from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import send_file

import os
import json
import pandas as pd
from datetime import datetime

from database import init_db
from database import get_connection

from drs_engine import generate_drs
from drs_engine import evaluate_sample
from drs_engine import generate_drs_from_parameters

app = Flask(__name__)

init_db()

UPLOAD_FOLDER = "project_data"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/")
def dashboard():

    conn = get_connection()

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        projects=projects
    )


# ==================================================
# CREATE PROJECT
# ==================================================

@app.route(
    "/create_project",
    methods=["POST"]
)
def create_project():

    name = request.form["project_name"]

    mode = request.form.get(
        "mode",
        "csv"
    )

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO projects
        (name,mode)
        VALUES (?,?)
        """,
        (
            name,
            mode
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ==================================================
# DELETE PROJECT
# ==================================================

@app.route(
    "/delete_project/<int:project_id>"
)
def delete_project(project_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM projects WHERE id=?",
        (project_id,)
    )

    conn.execute(
        "DELETE FROM drs_models WHERE project_id=?",
        (project_id,)
    )

    conn.execute(
        "DELETE FROM samples WHERE project_id=?",
        (project_id,)
    )

    conn.execute(
        "DELETE FROM parameters WHERE project_id=?",
        (project_id,)
    )

    conn.commit()
    conn.close()

    csv_path = (
        f"{UPLOAD_FOLDER}/project_{project_id}.csv"
    )

    if os.path.exists(csv_path):
        os.remove(csv_path)

    return redirect("/")


# ==================================================
# PROJECT PAGE
# ==================================================

@app.route(
    "/project/<int:project_id>"
)
def project(project_id):

    conn = get_connection()

    project = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE id=?
        """,
        (project_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "project.html",
        project=project
    )


# ==================================================
# PARAMETER MANAGEMENT
# ==================================================

@app.route(
    "/parameters/<int:project_id>"
)
def parameters(project_id):

    conn = get_connection()

    params = conn.execute(
        """
        SELECT *
        FROM parameters
        WHERE project_id=?
        ORDER BY id
        """,
        (project_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "parameters.html",
        params=params,
        project_id=project_id
    )


@app.route(
    "/add_parameter/<int:project_id>",
    methods=["POST"]
)
def add_parameter(project_id):

    name = request.form["name"]

    min_value = float(
        request.form["min"]
    )

    max_value = float(
        request.form["max"]
    )

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO parameters
        (
            project_id,
            name,
            min_value,
            max_value
        )
        VALUES (?,?,?,?)
        """,
        (
            project_id,
            name,
            min_value,
            max_value
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        f"/parameters/{project_id}"
    )


@app.route(
    "/delete_parameter/<int:param_id>/<int:project_id>"
)
def delete_parameter(
    param_id,
    project_id
):

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM parameters
        WHERE id=?
        """,
        (param_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        f"/parameters/{project_id}"
    )


@app.route(
    "/update_parameter/<int:param_id>/<int:project_id>",
    methods=["POST"]
)
def update_parameter(
    param_id,
    project_id
):

    name = request.form["name"]

    min_value = float(
        request.form["min"]
    )

    max_value = float(
        request.form["max"]
    )

    conn = get_connection()

    conn.execute(
        """
        UPDATE parameters
        SET
        name=?,
        min_value=?,
        max_value=?
        WHERE id=?
        """,
        (
            name,
            min_value,
            max_value,
            param_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        f"/parameters/{project_id}"
    )


# ==================================================
# CSV UPLOAD
# ==================================================

@app.route(
    "/upload/<int:project_id>",
    methods=["POST"]
)
def upload(project_id):

    file = request.files["csvfile"]

    try:

        df = pd.read_csv(
            file,
            sep=";"
        )

    except:

        file.seek(0)

        df = pd.read_csv(file)

    for col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    drs = generate_drs(df)

    csv_path = (
        f"{UPLOAD_FOLDER}/project_{project_id}.csv"
    )

    df.to_csv(
        csv_path,
        index=False
    )

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO drs_models
        (
            project_id,
            drs_json
        )
        VALUES (?,?)
        """,
        (
            project_id,
            json.dumps(drs)
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        f"/analyze/{project_id}"
    )


# ==================================================
# ANALYZE PAGE
# ==================================================

@app.route(
    "/analyze/<int:project_id>"
)
def analyze(project_id):

    conn = get_connection()

    project = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE id=?
        """,
        (project_id,)
    ).fetchone()

    if project["mode"] == "manual":

        params = conn.execute(
            """
            SELECT *
            FROM parameters
            WHERE project_id=?
            """
            ,
            (project_id,)
        ).fetchall()

        conn.close()

        return render_template(
            "analyze_manual.html",
            params=params,
            project_id=project_id
        )

    row = conn.execute(
        """
        SELECT drs_json
        FROM drs_models
        WHERE project_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (project_id,)
    ).fetchone()

    conn.close()

    if row is None:

        return redirect(
            f"/project/{project_id}"
        )

    drs = json.loads(
        row["drs_json"]
    )

    return render_template(
        "analyze.html",
        project_id=project_id,
        parameters=list(drs.keys()),
        drs=drs
    )


# ==================================================
# EVALUATE SAMPLE
# ==================================================

@app.route(
    "/evaluate/<int:project_id>",
    methods=["POST"]
)
def evaluate(project_id):

    conn = get_connection()

    project = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE id=?
        """,
        (project_id,)
    ).fetchone()

    sample = {}

    # ==================================
    # MANUAL MODE
    # ==================================

    if project["mode"] == "manual":

        params = conn.execute(
            """
            SELECT *
            FROM parameters
            WHERE project_id=?
            """,
            (project_id,)
        ).fetchall()

        for p in params:

            key = p["name"]

            sample[key] = float(request.form.get(key))

        drs = generate_drs_from_parameters(
            params
        )

    else:

        row = conn.execute(
            """
            SELECT drs_json
            FROM drs_models
            WHERE project_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (project_id,)
        ).fetchone()

        drs = json.loads(
            row["drs_json"]
        )
        file = request.files["file"]
        df = pd.read_csv(file)
        for param in drs.keys():
            value = request.form.get(param)
            if value is None:
                continue  # or raise error

            sample[param] = float(value)

    result = evaluate_sample(
        sample,
        drs
    )

    used_for_drs = 0

    if result["prediction"] == "PASS":
        used_for_drs = 1

    conn.execute(
        """
        INSERT INTO samples
        (
            project_id,
            sample_json,
            prediction,
            drs_score,
            used_for_drs,
            created_at
        )
        VALUES
        (?,?,?,?,?,?)
        """,
        (
            project_id,
            json.dumps(sample),
            result["prediction"],
            result["drs_score"],
            used_for_drs,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    conn.commit()

    # ==================================
    # UPDATE DRS ONLY FOR PASS
    # ==================================

    if result["prediction"] == "PASS":

        csv_path = (
            f"{UPLOAD_FOLDER}/project_{project_id}.csv"
        )

        sample_df = pd.DataFrame(
            [sample]
        )

        if os.path.exists(csv_path):

            sample_df.to_csv(
                csv_path,
                mode="a",
                header=False,
                index=False
            )

            full_df = pd.read_csv(
                csv_path
            )

        else:

            sample_df.to_csv(
                csv_path,
                index=False
            )

            full_df = sample_df

        new_drs = generate_drs(
            full_df
        )

        conn.execute(
            """
            INSERT INTO drs_models
            (
                project_id,
                drs_json
            )
            VALUES (?,?)
            """,
            (
                project_id,
                json.dumps(new_drs)
            )
        )

        conn.commit()

    conn.close()

    with open(
        "latest_result.json",
        "w"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )

    return render_template(
        "result.html",
        result=result,
        project_id=project_id
    )


# ==================================================
# HISTORY
# ==================================================

@app.route(
    "/history/<int:project_id>"
)
def history(project_id):

    conn = get_connection()

    samples = conn.execute(
        """
        SELECT *
        FROM samples
        WHERE project_id=?
        ORDER BY id DESC
        """,
        (project_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "history.html",
        samples=samples,
        project_id=project_id
    )


# ==================================================
# JSON EXPORT
# ==================================================

@app.route(
    "/download_json"
)
def download_json():

    return send_file(
        "latest_result.json",
        as_attachment=True
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
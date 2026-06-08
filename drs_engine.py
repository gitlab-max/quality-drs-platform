import pandas as pd
import numpy as np


# ==========================================
# CSV MODE
# Build DRS from accepted historical samples
# ==========================================

def generate_drs(df):

    drs = {}

    # convert everything possible to numeric

    for col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    numeric_cols = df.select_dtypes(
        include=np.number
    ).columns

    for col in numeric_cols:

        clean = df[col].dropna()

        if len(clean) == 0:
            continue

        mean = float(
            clean.mean()
        )

        std = float(
            clean.std()
        )

        if np.isnan(std):
            std = 0

        drs[col] = {

            "mean":
                mean,

            "std":
                std,

            "optimal_min":
                mean - std,

            "optimal_max":
                mean + std,

            "acceptable_min":
                mean - (2 * std),

            "acceptable_max":
                mean + (2 * std)
        }

    return drs


# ==========================================
# MANUAL MODE
# Build DRS from engineering limits
# ==========================================

def generate_drs_from_parameters(params):

    drs = {}

    for p in params:

        min_v = float(
            p["min_value"]
        )

        max_v = float(
            p["max_value"]
        )

        mean = (
            min_v + max_v
        ) / 2

        std = (
            max_v - min_v
        ) / 4

        drs[p["name"]] = {

            "mean":
                mean,

            "std":
                std,

            "optimal_min":
                min_v,

            "optimal_max":
                max_v,

            "acceptable_min":
                min_v - std,

            "acceptable_max":
                max_v + std
        }

    return drs


# ==========================================
# Evaluate New Sample
# ==========================================

def evaluate_sample(
    sample,
    drs
):

    scores = []

    assessment = {}

    for param, value in sample.items():

        if param not in drs:
            continue

        try:

            value = float(value)

        except:

            continue

        rule = drs[param]

        optimal_min = rule[
            "optimal_min"
        ]

        optimal_max = rule[
            "optimal_max"
        ]

        acceptable_min = rule[
            "acceptable_min"
        ]

        acceptable_max = rule[
            "acceptable_max"
        ]

        # ------------------------------
        # Optimal
        # ------------------------------

        if (
            optimal_min
            <= value
            <= optimal_max
        ):

            assessment[param] = {

                "status":
                    "OPTIMAL",

                "value":
                    value
            }

            scores.append(
                100
            )

        # ------------------------------
        # Acceptable
        # ------------------------------

        elif (
            acceptable_min
            <= value
            <= acceptable_max
        ):

            assessment[param] = {

                "status":
                    "ACCEPTABLE",

                "value":
                    value
            }

            scores.append(
                60
            )

        # ------------------------------
        # Alert
        # ------------------------------

        else:

            assessment[param] = {

                "status":
                    "ALERT",

                "value":
                    value
            }

            scores.append(
                0
            )

    # ==================================
    # Safety
    # ==================================

    if len(scores) == 0:

        return {

            "prediction":
                "ERROR",

            "drs_score":
                0,

            "assessment":
                {
                    "error":
                    "No valid parameters supplied"
                }
        }

    drs_score = round(
        sum(scores) / len(scores),
        2
    )

    # ==================================
    # Decision Logic
    # ==================================

    if drs_score >= 80:

        prediction = "PASS"

    elif drs_score >= 60:

        prediction = "WARNING"

    else:

        prediction = "REJECT"

    return {

        "prediction":
            prediction,

        "drs_score":
            drs_score,

        "assessment":
            assessment
    }


# ==========================================
# Rebuild DRS From Accepted Samples
# Future Use
# ==========================================

def rebuild_drs_from_history(df):

    if len(df) == 0:

        return {}

    return generate_drs(df)


# ==========================================
# Utility
# ==========================================

def get_parameter_status(
    value,
    drs_rule
):

    value = float(value)

    if (
        drs_rule["optimal_min"]
        <= value
        <= drs_rule["optimal_max"]
    ):

        return "OPTIMAL"

    elif (
        drs_rule["acceptable_min"]
        <= value
        <= drs_rule["acceptable_max"]
    ):

        return "ACCEPTABLE"

    else:

        return "ALERT"
function validateField(field){

    let min =
        parseFloat(
            field.dataset.min
        );

    let max =
        parseFloat(
            field.dataset.max
        );

    let value =
        parseFloat(
            field.value
        );

    if(isNaN(value))
        return;

    if(
        value < min ||
        value > max
    ){

        field.classList.remove(
            "good"
        );

        field.classList.add(
            "bad"
        );

    }else{

        field.classList.remove(
            "bad"
        );

        field.classList.add(
            "good"
        );
    }
}
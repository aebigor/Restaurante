function initFilters(){

    const input=document.getElementById("search");

    if(!input)return;

    input.addEventListener(

        "keyup",

        loadDishes

    );

}
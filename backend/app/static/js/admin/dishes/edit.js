document.addEventListener("DOMContentLoaded",()=>{

    loadCategories();

    loadStations();

    initPreview();

    loadDish();

    document

        .getElementById("dishForm")

        .addEventListener(

            "submit",

            updateDish

        );

});

async function loadDish(){

    const response=await fetch(

        API+DISH_ID

    );

    const dish=await response.json();

    document.getElementById("name").value=dish.name;

    document.getElementById("description").value=dish.description;

    document.getElementById("price").value=dish.price;

    document.getElementById("category").value=dish.category_id;

    document.getElementById("station").value=dish.station_id;

    document.getElementById("preparation_time").value=dish.preparation_time;

    document.getElementById("calories").value=dish.calories;

    document.getElementById("ingredients").value=dish.ingredients;

    document.getElementById("allergens").value=dish.allergens;

    document.getElementById("featured").checked=dish.featured;

    document.getElementById("available").checked=dish.available;

}

async function updateDish(e){

    e.preventDefault();

    /* misma estructura del create,
       cambiando POST por PUT */

}
document.addEventListener("DOMContentLoaded", () => {

    initFilters();

});

function initFilters(){

    const search = document.getElementById("search");

    if(search){

        search.addEventListener(

            "keyup",

            searchMenu

        );

    }

}

function searchMenu(){

    const value =
        document
            .getElementById("search")
            .value
            .toLowerCase();

    const rows =
        document.querySelectorAll(

            "#menuTable tr"

        );

    rows.forEach(row=>{

        const text =
            row.innerText.toLowerCase();

        row.style.display =

            text.includes(value)

            ?

            ""

            :

            "none";

    });

}
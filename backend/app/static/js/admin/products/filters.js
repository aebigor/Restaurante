document.addEventListener("DOMContentLoaded",()=>{

    const search=document.getElementById("searchProduct");

    if(search){

        search.addEventListener(

            "keyup",

            filterProducts

        );

    }

});

function filterProducts(){

    const text=document

        .getElementById("searchProduct")

        .value

        .toLowerCase();

    const filtered=products.filter(product=>{

        return(

            product.name

            .toLowerCase()

            .includes(text)

            ||

            product.category

            .toLowerCase()

            .includes(text)

        );

    });

    drawProducts(filtered);

}
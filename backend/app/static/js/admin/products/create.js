const API = "/api/products/";

document.addEventListener("DOMContentLoaded", () => {

    loadCategories();
    loadStations();
    initPreview();

    document
        .getElementById("productForm")
        .addEventListener("submit", saveProduct);

});

async function saveProduct(e){

    e.preventDefault();

    const data = {

    name: document.getElementById("name").value,

    code: document.getElementById("code").value,

    description: document.getElementById("description").value,

    price: Number(
        document.getElementById("price").value
    ),

    preparation_time: Number(
        document.getElementById("preparation_time").value
    ),

    stock: Number(
        document.getElementById("stock").value
    ),

    category_id:
        document.getElementById("category").value,

    station_id:
        document.getElementById("station").value

};

    console.log(data);

    try{

        const response=await fetch(

            API,

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify(data)

            }

        );

        const result=await response.json();

        if(!response.ok){

            console.log(result);

            alert(result.detail);

            return;

        }

        alert("Producto creado correctamente.");

        window.location="/admin/menu/products";

    }

    catch(error){

        console.error(error);

        alert("Error conectando con el servidor.");

    }

}
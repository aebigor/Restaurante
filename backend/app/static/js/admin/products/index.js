const API="/api/products/";

let products=[];

document.addEventListener("DOMContentLoaded",()=>{

    loadProducts();

});

async function loadProducts(){

    try{

        const response=await fetch(API);

        products=await response.json();

        drawProducts(products);

    }

    catch(error){

        console.error(error);

    }

}

function drawProducts(data){

    const container=document.getElementById("products-container");

    if(!container)return;

    container.innerHTML="";

    if(data.length===0){

        container.innerHTML=`

            <div class="empty">

                <h2>No existen productos.</h2>

            </div>

        `;

        return;

    }

    data.forEach(product=>{

        container.innerHTML+=`

        <div class="product-card">

            <img

                src="${product.image}"

                onerror="this.src='/static/img/no-image.png'"

            >

            <div class="product-body">

                <h3>${product.name}</h3>

                <p>${product.category}</p>

                <h2>$${product.price}</h2>

            </div>

            <div class="product-footer">

                <button

                    class="btn-edit"

                    onclick="editProduct('${product.id}')">

                    Editar

                </button>

                <button

                    class="btn-delete"

                    onclick="deleteProduct('${product.id}')">

                    Eliminar

                </button>

            </div>

        </div>

        `;

    });

}

function editProduct(id){

    window.location=

        "/admin/menu/products/edit?id="+id;

}
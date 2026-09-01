// =====================================================
// CONFIGURACIÓN
// =====================================================

const API = "/api/products/";

let productos = [];


// =====================================================
// INICIO
// =====================================================

document.addEventListener("DOMContentLoaded", () => {

    iniciar();

});

function iniciar(){

    cargarProductos();

    configurarBotones();

    configurarFiltros();

    configurarImagen();

}


// =====================================================
// BOTONES
// =====================================================

function configurarBotones(){

    const nuevo=document.getElementById("btnNuevoProducto");

    if(nuevo){

        nuevo.addEventListener("click",()=>{

            window.location="/admin/menu/products/create";

        });

    }

}


// =====================================================
// FILTROS
// =====================================================

function configurarFiltros(){

    const buscar=document.getElementById("searchProduct");

    if(buscar){

        buscar.addEventListener("keyup",filtrarProductos);

    }

    const categoria=document.getElementById("filterCategory");

    if(categoria){

        categoria.addEventListener("change",filtrarProductos);

    }

    const estado=document.getElementById("filterStatus");

    if(estado){

        estado.addEventListener("change",filtrarProductos);

    }

}


// =====================================================
// PREVIEW IMAGEN
// =====================================================

function configurarImagen(){

    const input=document.getElementById("image");

    if(!input){

        return;

    }

    input.addEventListener("change",function(){

        const archivo=this.files[0];

        if(!archivo){

            return;

        }

        const lector=new FileReader();

        lector.onload=function(e){

            document.getElementById("previewImage").src=e.target.result;

        }

        lector.readAsDataURL(archivo);

    });

}


// =====================================================
// CARGAR PRODUCTOS
// =====================================================

async function cargarProductos(){

    const contenedor=document.getElementById("productsContainer");

    if(!contenedor){

        return;

    }

    try{

        const respuesta=await fetch(API);

        if(!respuesta.ok){

            throw new Error();

        }

        productos=await respuesta.json();

        pintarProductos(productos);

    }

    catch{

        contenedor.innerHTML=`

            <div class="empty">

                <h2>

                    Aún no existen productos.

                </h2>

                <p>

                    Cree el primero.

                </p>

            </div>

        `;

    }

}


// =====================================================
// PINTAR PRODUCTOS
// =====================================================

function pintarProductos(lista){

    const contenedor=document.getElementById("productsContainer");

    if(!contenedor){

        return;

    }

    contenedor.innerHTML="";

    actualizarResumen(lista);

    lista.forEach(producto=>{

        contenedor.innerHTML+=`

        <div class="product-card">

            <div class="product-image">

                <img src="${
                    producto.image || "/static/img/no-image.png"
                }">

            </div>

            <div class="product-body">

                <div class="product-name">

                    ${producto.name}

                </div>

                <div class="product-category">

                    ${producto.category}

                </div>

                <div class="product-price">

                    $ ${Number(producto.price).toLocaleString()}

                </div>

                <div class="product-info">

                    <span>

                        ${producto.station}

                    </span>

                    <span>

                        Stock ${producto.stock}

                    </span>

                </div>

                <div class="product-actions">

                    <button
                        class="btn-edit"
                        onclick="editarProducto(${producto.id})">

                        Editar

                    </button>

                    <button
                        class="btn-delete"
                        onclick="eliminarProducto(${producto.id})">

                        Eliminar

                    </button>

                </div>

            </div>

        </div>

        `;

    });

}


// =====================================================
// RESUMEN
// =====================================================

function actualizarResumen(lista){

    const total=document.getElementById("totalProducts");

    if(total){

        total.innerHTML=lista.length;

    }

    const activos=document.getElementById("activeProducts");

    if(activos){

        activos.innerHTML=

            lista.filter(x=>x.status==="ACTIVE").length;

    }

    const agotados=document.getElementById("outProducts");

    if(agotados){

        agotados.innerHTML=

            lista.filter(x=>x.status==="OUT").length;

    }

    const ocultos=document.getElementById("hiddenProducts");

    if(ocultos){

        ocultos.innerHTML=

            lista.filter(x=>x.status==="HIDDEN").length;

    }

}


// =====================================================
// FILTRAR
// =====================================================

function filtrarProductos(){

    const texto=document
        .getElementById("searchProduct")
        ?.value
        .toLowerCase() || "";

    const categoria=document
        .getElementById("filterCategory")
        ?.value || "";

    const estado=document
        .getElementById("filterStatus")
        ?.value || "";

    const resultado=productos.filter(producto=>{

        let coincide=

            producto.name.toLowerCase().includes(texto)

            ||

            producto.code.toLowerCase().includes(texto);

        if(!coincide){

            return false;

        }

        if(categoria!=="" && producto.category!==categoria){

            return false;

        }

        if(estado!=="" && producto.status!==estado){

            return false;

        }

        return true;

    });

    pintarProductos(resultado);

}


// =====================================================
// EDITAR
// =====================================================

function editarProducto(id){

    window.location="/admin/menu/products/edit/"+id;

}


// =====================================================
// ELIMINAR
// =====================================================

async function eliminarProducto(id){

    const confirmar=confirm(

        "¿Eliminar este producto?"

    );

    if(!confirmar){

        return;

    }

    await fetch(API+id,{

        method:"DELETE"

    });

    cargarProductos();

}


// =====================================================
// GUARDAR PRODUCTO
// =====================================================

const formulario=document.getElementById("productForm");

if(formulario){

    formulario.addEventListener("submit",guardarProducto);

}

async function guardarProducto(e){

    e.preventDefault();

    alert(

        "En el siguiente bloque conectaremos este formulario con FastAPI."

    );

}

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadCategories();

    }
);
async function loadCategories(){

    const select =
        document.getElementById("category");


    try {


        const response = await fetch(
            "/api/categories/"
        );


        const categories =
            await response.json();



        select.innerHTML = `

            <option value="">
                Seleccione una categoría
            </option>

        `;



        categories.forEach(category => {


            if(category.active){


                select.innerHTML += `

                    <option value="${category.id}">

                        ${category.icon ?? ""}
                        ${category.name}

                    </option>

                `;


            }


        });



    }
    catch(error){

        console.error(
            "Error cargando categorías:",
            error
        );

    }

}
document
    .getElementById("productForm")
    .addEventListener(
        "submit",
        async function(event){

            event.preventDefault();


            const data = {

                name:
                    document.getElementById("name").value,


                code:
                    document.getElementById("code").value,


                category_id:
                    document.getElementById("category").value,


                price:
                    Number(
                        document.getElementById("price").value
                    ),


                preparation_time:
                    Number(
                        document.getElementById("time").value
                    ),


                station:
                    document.getElementById("station").value,


                stock:
                    Number(
                        document.getElementById("stock").value
                    ),


                status:
                    document.getElementById("status").value,


                description:
                    document.getElementById("description").value

            };



            try {


                const response = await fetch(
                    "/api/products/",
                    {

                        method:"POST",

                        headers:{
                            "Content-Type":"application/json"
                        },

                        body:
                            JSON.stringify(data)

                    }
                );



                if(!response.ok){

                    const error =
                        await response.json();

                    console.error(error);

                    throw new Error(
                        "Error creando producto"
                    );

                }



                alert(
                    "Producto creado correctamente"
                );



                window.location.href =
                    "/admin/menu/products";



            }
            catch(error){


                console.error(error);


                alert(
                    "No se pudo guardar el producto"
                );


            }


        }
    );
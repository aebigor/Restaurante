const API = "/api/categories/";

let categories = [];

// ==========================================
// INICIO
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    iniciar();

});

function iniciar(){

    cargarCategorias();

    configurarBotones();

    configurarFiltros();

}

// ==========================================
// BOTONES
// ==========================================

function configurarBotones(){

    const boton=document.getElementById("btnNuevaCategoria");

    if(boton){

        boton.addEventListener("click",()=>{

            window.location="/admin/menu/categories/create";

        });

    }

}

// ==========================================
// FILTROS
// ==========================================

function configurarFiltros(){

    const buscar=document.getElementById("searchCategory");

    if(buscar){

        buscar.addEventListener("keyup",filtrarCategorias);

    }

    const estado=document.getElementById("filterStatus");

    if(estado){

        estado.addEventListener("change",filtrarCategorias);

    }

}

// ==========================================
// CARGAR
// ==========================================

async function cargarCategorias(){

    try{

        const respuesta=await fetch(API);

        if(!respuesta.ok){

            throw new Error();

        }

        categories=await respuesta.json();

        pintarCategorias(categories);

    }

    catch(error){

        console.error(error);

    }

}

// ==========================================
// PINTAR
// ==========================================

function pintarCategorias(lista){

    const contenedor=document.getElementById("categoriesContainer");

    if(!contenedor){

        return;

    }

    contenedor.innerHTML="";

    actualizarResumen(lista);

    if(lista.length===0){

        contenedor.innerHTML=`

            <div class="empty">

                <h2>

                    No existen categorías.

                </h2>

                <p>

                    Cree la primera categoría.

                </p>

            </div>

        `;

        return;

    }

    lista.forEach(cat=>{

        contenedor.innerHTML+=`

        <div class="category-card">

            <div
                class="category-header"
                style="background:${cat.color};"
            >

                <h2>

                    ${cat.name}

                </h2>

                <div class="category-icon">

                    ${cat.icon}

                </div>

            </div>

            <div class="category-body">

                <p>

                    ${cat.description || ""}

                </p>

                <p>

                    <strong>Orden:</strong>

                    ${cat.display_order}

                </p>

                <p>

                    <span class="badge ${cat.active ? "badge-active":"badge-inactive"}">

                        ${cat.active ? "Activa":"Inactiva"}

                    </span>

                </p>

            </div>

            <div class="category-footer">

                <button
                    class="btn btn-edit"
                    onclick="editarCategoria('${cat.id}')">

                    Editar

                </button>

                <button
                    class="btn btn-delete"
                    onclick="eliminarCategoria('${cat.id}')">

                    Eliminar

                </button>

            </div>

        </div>

        `;

    });

}

// ==========================================
// RESUMEN
// ==========================================

function actualizarResumen(lista){

    document.getElementById("totalCategories").innerHTML=

        lista.length;

    document.getElementById("activeCategories").innerHTML=

        lista.filter(x=>x.active).length;

    document.getElementById("inactiveCategories").innerHTML=

        lista.filter(x=>!x.active).length;

}

// ==========================================
// FILTRAR
// ==========================================

function filtrarCategorias(){

    const texto=document
        .getElementById("searchCategory")
        .value
        .toLowerCase();

    const estado=document
        .getElementById("filterStatus")
        .value;

    const resultado=categories.filter(cat=>{

        let coincide=

            cat.name.toLowerCase().includes(texto);

        if(!coincide){

            return false;

        }

        if(estado==="ACTIVE"){

            return cat.active;

        }

        if(estado==="INACTIVE"){

            return !cat.active;

        }

        return true;

    });

    pintarCategorias(resultado);

}

// ==========================================
// EDITAR
// ==========================================

function editarCategoria(id){

    window.location="/admin/menu/categories/edit/"+id;

}

// ==========================================
// ELIMINAR
// ==========================================

async function eliminarCategoria(id){

    const confirmar=confirm(

        "¿Eliminar esta categoría?"

    );

    if(!confirmar){

        return;

    }

    try{

        const respuesta=await fetch(

            API+id,

            {

                method:"DELETE"

            }

        );

        if(!respuesta.ok){

            throw new Error();

        }

        cargarCategorias();

    }

    catch(error){

        console.error(error);

        alert(

            "No fue posible eliminar la categoría."

        );

    }

}

function editCategory(id){

    window.location.href =
        `/admin/menu/categories/edit/${id}`;

}
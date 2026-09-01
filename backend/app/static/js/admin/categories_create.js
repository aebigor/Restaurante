const API="/api/categories/";

document.addEventListener("DOMContentLoaded",()=>{

    iniciarPreview();
    cargarEstaciones();

    document

        .getElementById("categoryForm")

        .addEventListener("submit",guardarCategoria);

});

// ==========================================
// PREVIEW
// ==========================================

function iniciarPreview(){

    document.getElementById("name")

        .addEventListener("keyup",actualizarPreview);

    document.getElementById("description")

        .addEventListener("keyup",actualizarPreview);

    document.getElementById("icon")

        .addEventListener("keyup",actualizarPreview);

    document.getElementById("color")

        .addEventListener("change",actualizarPreview);

}

function actualizarPreview(){

    document.getElementById("previewName").innerHTML=

        document.getElementById("name").value || "Categoría";

    document.getElementById("previewDescription").innerHTML=

        document.getElementById("description").value || "Descripción...";

    document.getElementById("previewIcon").innerHTML=

        document.getElementById("icon").value || "🍔";

    document.getElementById("previewHeader").style.background=

        document.getElementById("color").value;

}

async function cargarEstaciones(){
    const r=await fetch("/api/stations/");
    const stations=await r.json();
    document.getElementById("station").innerHTML='<option value="">Selecciona una estación</option>'+stations.filter(x=>x.active).map(x=>`<option value="${x.id}">${x.name}</option>`).join("");
}

// ==========================================
// GUARDAR
// ==========================================

async function guardarCategoria(e){

    e.preventDefault();

    const data={

        name:document.getElementById("name").value,

        description:document.getElementById("description").value,

        color:document.getElementById("color").value,

        icon:document.getElementById("icon").value,

        display_order:parseInt(

            document.getElementById("display_order").value

        ),

        active:
            document.getElementById("active").value==="true",
        station_id:
            document.getElementById("station").value || null

    };

    if(!data.station_id){ alert("Selecciona una estación de cocina."); return; }

    try{

        const respuesta=await fetch(

            API,

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify(data)

            }

        );

        if(!respuesta.ok){

            const error=await respuesta.json();

            alert(error.detail || "Error guardando la categoría.");

            return;

        }

        alert("Categoría creada correctamente.");

        window.location="/admin/menu/categories";

    }

    catch(error){

        console.error(error);

        alert("Error de conexión con el servidor.");

    }

}
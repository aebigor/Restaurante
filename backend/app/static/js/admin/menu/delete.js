const API = "/api/menu/";

async function deleteMenu(id){

    const confirmDelete = confirm(

        "¿Desea eliminar este menú?"

    );

    if(!confirmDelete){

        return;

    }

    try{

        const response = await fetch(

            API + id,

            {

                method:"DELETE"

            }

        );

        const result = await response.json();

        if(!response.ok){

            alert(result.detail);

            return;

        }

        alert(result.message);

        loadMenus();

    }

    catch(error){

        console.error(error);

        alert("No fue posible eliminar el menú.");

    }

}
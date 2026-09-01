async function deleteDish(id){

    if(

        !confirm(

            "¿Eliminar plato?"

        )

    )return;

    await fetch(

        API+id,

        {

            method:"DELETE"

        }

    );

    loadDishes();

}
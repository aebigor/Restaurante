async function deleteProduct(id){

    const confirmDelete=confirm(

        "¿Desea eliminar este producto?"

    );

    if(!confirmDelete){

        return;

    }

    try{

        const response=await fetch(

            "/api/products/"+id,

            {

                method:"DELETE"

            }

        );

        if(!response.ok){

            const error=await response.json();

            alert(error.detail);

            return;

        }

        loadProducts();

    }

    catch(error){

        console.error(error);

        alert(

            "Error eliminando el producto."

        );

    }

}
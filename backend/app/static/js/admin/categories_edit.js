document.addEventListener(
    "DOMContentLoaded",
    async () => {

        await loadCategory();

    }
);



async function loadCategory(){

    try {

        const response = await fetch(
            `/api/categories/${categoryId}`
        );


        if(!response.ok){

            throw new Error(
                "No se pudo cargar la categoría"
            );

        }


        const category = await response.json();


        document.getElementById("name").value =
            category.name;


        document.getElementById("description").value =
            category.description ?? "";


        document.getElementById("display_order").value =
            category.display_order;


        document.getElementById("color").value =
            category.color;


        document.getElementById("icon").value =
            category.icon;


        document.getElementById("active").value =
            category.active;



        updatePreview();


    }
    catch(error){

        console.error(error);

    }

}



function updatePreview(){

    document.getElementById("previewName").innerText =
        document.getElementById("name").value;


    document.getElementById("previewDescription").innerText =
        document.getElementById("description").value;


    document.getElementById("previewIcon").innerText =
        document.getElementById("icon").value;


    document.getElementById("previewHeader").style.background =
        document.getElementById("color").value;

}
document
    .getElementById("categoryEditForm")
    .addEventListener(
        "submit",
        async function(event){

            event.preventDefault();


            const data = {

                name:
                    document.getElementById("name").value,


                description:
                    document.getElementById("description").value,


                color:
                    document.getElementById("color").value,


                icon:
                    document.getElementById("icon").value,


                display_order:
                    Number(
                        document.getElementById("display_order").value
                    ),


                active:
                    document.getElementById("active").value === "true"

            };



            try {


                const response = await fetch(
                    `/api/categories/${categoryId}`,
                    {

                        method: "PUT",

                        headers: {
                            "Content-Type": "application/json"
                        },

                        body: JSON.stringify(data)

                    }
                );



                if(!response.ok){

                    throw new Error(
                        "Error actualizando categoría"
                    );

                }



                alert(
                    "Categoría actualizada correctamente"
                );


                window.location.href =
                    "/admin/menu/categories";


            }
            catch(error){

                console.error(error);

                alert(
                    "No se pudo actualizar la categoría"
                );

            }


        }
    );
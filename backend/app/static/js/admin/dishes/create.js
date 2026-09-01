const API = "/api/dishes/";


document.addEventListener("DOMContentLoaded", () => {

    initPreview();

    const form =
        document.getElementById("dishForm");

    if (form) {

        form.addEventListener(
            "submit",
            saveDish
        );

    }

});


async function saveDish(event) {

    event.preventDefault();


    const button =
        document.getElementById("btnGuardar");


    try {

        button.disabled = true;

        button.textContent =
            "Guardando...";


        /* ==========================================
           CATEGORÍA
        ========================================== */

        const categoryId =
            document.getElementById(
                "category"
            ).value;


        if (!categoryId) {

            alert(
                "Selecciona una categoría."
            );

            return;

        }


        /* ==========================================
           ESTACIÓN
        ========================================== */

        const stationId =
            document.getElementById(
                "station"
            ).value;


        if (!stationId) {

            alert(
                "La categoría seleccionada no tiene una estación de cocina asignada."
            );

            return;

        }


        /* ==========================================
           IMAGEN
        ========================================== */

        let imageUrl = null;


        const imageInput =
            document.getElementById(
                "image"
            );


        const imageFile =
            imageInput.files[0];


        if (imageFile) {

            const uploadData =
                new FormData();


            uploadData.append(
                "file",
                imageFile
            );


            const uploadResponse =
                await fetch(
                    "/api/dishes/upload-image",
                    {
                        method: "POST",
                        body: uploadData
                    }
                );


            const uploadResult =
                await uploadResponse.json();


            if (!uploadResponse.ok) {

                throw new Error(
                    uploadResult.detail ||
                    "No fue posible subir la imagen."
                );

            }


            imageUrl =
                uploadResult.url;

        }


        /* ==========================================
           DATOS DEL PLATO
        ========================================== */

        const data = {

            name:
                document
                    .getElementById("name")
                    .value
                    .trim(),

            price:
                parseFloat(
                    document
                        .getElementById("price")
                        .value
                ),

            category_id:
                categoryId,

            station_id:
                stationId,

            preparation_time:
                parseInt(
                    document
                        .getElementById(
                            "preparation_time"
                        )
                        .value
                ) || 10,

            portion:
                document
                    .getElementById("portion")
                    .value
                    .trim() ||
                "1 porción",

            image:
                imageUrl,

            model_3d:
                null,

            video:
                null,

            featured:
                document
                    .getElementById(
                        "featured"
                    )
                    .checked,

            available:
                document
                    .getElementById(
                        "available"
                    )
                    .checked

        };


        /* ==========================================
           VALIDACIÓN
        ========================================== */

        if (!data.name) {

            alert(
                "Ingresa el nombre del plato."
            );

            return;

        }


        if (
            !data.price ||
            data.price < 0
        ) {

            alert(
                "Ingresa un precio válido."
            );

            return;

        }


        /* ==========================================
           CREAR PLATO
        ========================================== */

        const response =
            await fetch(
                API,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(data)
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            console.error(
                result
            );

            alert(
                result.detail ||
                "No fue posible guardar el plato."
            );

            return;

        }


        alert(
            "Plato creado correctamente."
        );


        window.location.href =
            "/admin/dishes";


    } catch (error) {

        console.error(
            "Error creando plato:",
            error
        );

        alert(
            error.message ||
            "Ocurrió un error al crear el plato."
        );


    } finally {

        button.disabled = false;

        button.textContent =
            "Guardar Plato";

    }

}
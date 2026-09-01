const API = "/api/menu/";


document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("menuForm");

    if (!form) {
        return;
    }

    form.addEventListener("submit", saveMenu);

});


async function saveMenu(event) {

    event.preventDefault();


    const button =
        document.getElementById("btnCreateMenu");


    const title =
        document
            .getElementById("title")
            .value
            .trim();


    const description =
        document
            .getElementById("description")
            .value
            .trim();


    const displayOrder =
        parseInt(
            document
                .getElementById("display_order")
                .value
        ) || 1;


    const active =
        document
            .getElementById("active")
            .value === "true";


    if (!title) {

        alert("Debes ingresar el nombre del menú.");

        return;

    }


    const data = {

        title: title,

        description: description || null,

        cover_image: null,

        display_order: displayOrder,

        active: active

    };


    try {

        button.disabled = true;

        button.textContent = "Creando menú...";


        const response = await fetch(

            API,

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify(data)

            }

        );


        const result =
            await response.json();


        if (!response.ok) {

            console.error(result);

            alert(
                result.detail ||
                "No fue posible crear el menú."
            );

            button.disabled = false;

            button.textContent = "Crear menú";

            return;

        }


        /*
         * IMPORTANTE:
         *
         * El menú ya fue creado.
         * Ahora pasamos directamente a
         * seleccionar los platos.
         */

        window.location =
            `/admin/menu/edit/${result.id}`;


    }

    catch (error) {

        console.error(error);

        alert(
            "No fue posible conectar con el servidor."
        );

        button.disabled = false;

        button.textContent = "Crear menú";

    }

}
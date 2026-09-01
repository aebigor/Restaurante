// ======================================================
// CREATE TABLE
// ======================================================

const form = document.getElementById("tableForm");

if (form) {

    form.addEventListener("submit", createTable);

}

// ======================================================
// CREAR MESA
// ======================================================

async function createTable(event) {

    event.preventDefault();

    const button = document.querySelector(".btn-save");

    button.disabled = true;

    button.innerHTML = "Guardando...";

    const data = {

        number: Number(

            document.getElementById("number").value

        ),

        name: document.getElementById("name").value.trim(),

        capacity: Number(

            document.getElementById("capacity").value

        ),

        zone: document.getElementById("zone").value,

        active: document.getElementById("active").checked

    };

    try {

        const response = await fetch(

            "/api/tables/",

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify(data)

            }

        );

        const result = await response.json();

        if (!response.ok) {

            throw new Error(

                result.detail ||

                result.message ||

                "No fue posible crear la mesa."

            );

        }

        alert("Mesa creada correctamente.");

        window.location.href = "/admin/tables";

    }

    catch (error) {

        alert(error.message);

    }

    finally {

        button.disabled = false;

        button.innerHTML = "Guardar Mesa";

    }

}
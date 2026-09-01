const API = "/api/tables/";

let tables = [];

document.addEventListener("DOMContentLoaded", () => {

    loadTables();

    document.getElementById("btnNuevaMesa")?.addEventListener("click", () => {

        window.location.href = "/admin/tables/create";

    });

    document.getElementById("searchTable")?.addEventListener("keyup", filterTables);

    document.getElementById("filterStatus")?.addEventListener("change", filterTables);

});

async function loadTables() {

    try {

        const response = await fetch(API);

        if (!response.ok) {

            throw new Error("Error obteniendo las mesas.");

        }

        tables = await response.json();

        renderTables(tables);

        updateCards(tables);

    }

    catch (e) {

        console.error(e);

    }

}

function renderTables(data) {

    const container = document.getElementById("tables-container");

    container.innerHTML = "";

    if (data.length === 0) {

        container.innerHTML = `

        <div class="empty">

            <h2>No existen mesas registradas</h2>

        </div>

        `;

        return;

    }

    data.forEach(table => {

        const status = table.active
            ? "Disponible"
            : "Fuera de servicio";

        const color = table.active
            ? "AVAILABLE"
            : "MAINTENANCE";

        container.innerHTML += `

        <div class="table-card estado-${color}">

            <div class="table-header">

                <h2>Mesa ${table.number}</h2>

                <span class="table-status">

                    ${status}

                </span>

            </div>

            <div class="table-body">

                <div class="table-info">

                    <strong>Nombre</strong>

                    <span>${table.name}</span>

                </div>

                <div class="table-info">

                    <strong>Capacidad</strong>

                    <span>${table.capacity} Personas</span>

                </div>

                <div class="table-info">

                    <strong>Zona</strong>

                    <span>${table.zone}</span>

                </div>

            </div>

            <div class="table-footer">

                <button

                    class="btn-edit"

                    onclick="editTable(${table.id})"

                >

                    ✏ Editar

                </button>

                <button

                    class="btn-delete"

                    onclick="deleteTable(${table.id})"

                >

                    🗑 Eliminar

                </button>

            </div>

        </div>

        `;

    });

}

function updateCards(data) {

    document.getElementById("totalTables").innerText = data.length;

    document.getElementById("freeTables").innerText =

        data.filter(x => x.active).length;

    document.getElementById("busyTables").innerText = 0;

    document.getElementById("reservedTables").innerText = 0;

}

function filterTables() {

    const search = document

        .getElementById("searchTable")

        .value

        .toLowerCase();

    const filter = document

        .getElementById("filterStatus")

        .value;

    const result = tables.filter(table => {

        const text = (

            table.name +

            table.number +

            table.zone

        ).toLowerCase();

        if (!text.includes(search)) {

            return false;

        }

        if (filter === "") {

            return true;

        }

        if (filter === "AVAILABLE") {

            return table.active;

        }

        if (filter === "MAINTENANCE") {

            return !table.active;

        }

        return true;

    });

    renderTables(result);

}

function editTable(id) {

    window.location.href = `/admin/tables/edit/${id}`;

}

async function deleteTable(id) {

    if (!confirm("¿Eliminar esta mesa?")) {

        return;

    }

    try {

        const response = await fetch(

            API + id,

            {

                method: "DELETE"

            }

        );

        if (!response.ok) {

            throw new Error();

        }

        loadTables();

    }

    catch {

        alert("No fue posible eliminar la mesa.");

    }

}
const stationApi = "/api/stations/";

const $ = (id) => document.getElementById(id);
let editingStationId = null;
let deletingStationId = null;


/* =========================================================
   MODAL
========================================================= */

function openStationModal() {
    const modal = $("stationModal");

    if (!modal) {
        console.error("No existe #stationModal");
        return;
    }

    modal.hidden = false;

    setTimeout(() => {
        const nameInput = $("stationName");
        if (nameInput) {
            nameInput.focus();
        }
    }, 50);
}


function closeStationModal() {
    const modal = $("stationModal");

    if (!modal) return;

    modal.hidden = true;

    const form = $("stationForm");

    if (form) {
        form.reset();
    }
    editingStationId = null;
    if ($("saveStationButton")) $("saveStationButton").textContent = "Crear estación";

    const color = $("stationColor");

    if (color) {
        color.value = "#3498db";
    }

    const error = $("stationError");

    if (error) {
        error.textContent = "";
    }
}


/* =========================================================
   TARJETA DE ESTACIÓN
========================================================= */

function stationCard(station) {

    const load = station.total_active || 0;

    const status =
        station.preparing > 0
            ? "En producción"
            : station.waiting > 0
                ? "En cola"
                : "Disponible";

    return `
        <article
            class="station-card"
            style="--station-color:${station.color || "#3498db"}"
        >

            <div class="station-card-top">

                <div class="station-icon">
                    👨‍🍳
                </div>

                <span class="station-status">
                    ● ${status}
                </span>

            </div>

            <h3>
                ${escapeHtml(station.name)}
            </h3>

            <p>
                ${station.dishes_count || 0} plato(s) asignado(s)
                ·
                ${escapeHtml(
                    station.printer_name || "Sin impresora configurada"
                )}
            </p>

            <div class="station-metrics">

                <div>
                    <strong>${station.waiting || 0}</strong>
                    <span>Esperando</span>
                </div>

                <div>
                    <strong>${station.preparing || 0}</strong>
                    <span>Preparando</span>
                </div>

                <div>
                    <strong>${station.ready || 0}</strong>
                    <span>Listos</span>
                </div>

            </div>

            <div class="station-progress">
                <span
                    style="width:${Math.min(load * 12, 100)}%"
                ></span>
            </div>

            <div class="station-actions">
                <button type="button" class="station-link" onclick="openKds('${station.id}')">🖥 Ver pantalla</button>
                <button type="button" class="station-action edit" onclick="editStation('${station.id}')">✎ Editar</button>
                <button type="button" class="station-action delete" onclick="askDeleteStation('${station.id}', '${escapeHtml(station.name)}')">🗑 Eliminar</button>
            </div>

        </article>
    `;
}


/* =========================================================
   SEGURIDAD HTML
========================================================= */

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================================
   CARGAR ESTACIONES
========================================================= */

async function loadStations() {

    const response = await fetch("/api/stations/dashboard", {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    });

    if (!response.ok) {
        throw new Error(
            `No se pudieron cargar las estaciones (${response.status})`
        );
    }

    const stations = await response.json();

    const totalStations = $("totalStations");
    const totalWaiting = $("totalWaiting");
    const totalPreparing = $("totalPreparing");
    const totalReady = $("totalReady");
    const lastUpdate = $("lastUpdate");
    const stationGrid = $("stationGrid");
    const emptyStations = $("emptyStations");

    if (totalStations) {
        totalStations.textContent = stations.length;
    }

    if (totalWaiting) {
        totalWaiting.textContent =
            stations.reduce(
                (total, station) =>
                    total + (station.waiting || 0),
                0
            );
    }

    if (totalPreparing) {
        totalPreparing.textContent =
            stations.reduce(
                (total, station) =>
                    total + (station.preparing || 0),
                0
            );
    }

    if (totalReady) {
        totalReady.textContent =
            stations.reduce(
                (total, station) =>
                    total + (station.ready || 0),
                0
            );
    }

    if (lastUpdate) {
        lastUpdate.textContent =
            `Actualizado ${new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit"
            })}`;
    }

    if (stationGrid) {

        stationGrid.innerHTML =
            stations.length
                ? stations.map(stationCard).join("")
                : "";
    }

    if (emptyStations) {
        emptyStations.hidden = stations.length !== 0;
    }
}


/* =========================================================
   CREAR ESTACIÓN
========================================================= */

async function createStation(event) {

    event.preventDefault();

    const errorElement = $("stationError");

    if (errorElement) {
        errorElement.textContent = "";
    }

    const nameElement = $("stationName");
    const printerElement = $("stationPrinter");
    const colorElement = $("stationColor");

    const name =
        nameElement
            ? nameElement.value.trim()
            : "";

    const printer =
        printerElement
            ? printerElement.value.trim()
            : "";

    const color =
        colorElement
            ? colorElement.value
            : "#3498db";


    /* -------------------------------
       Validación frontend
    -------------------------------- */

    if (!name) {

        if (errorElement) {
            errorElement.textContent =
                "Escribe el nombre de la estación.";
        }

        if (nameElement) {
            nameElement.focus();
        }

        return;
    }


    if (name.length < 2) {

        if (errorElement) {
            errorElement.textContent =
                "El nombre debe tener al menos 2 caracteres.";
        }

        return;
    }


    /* -------------------------------
       Datos enviados
    -------------------------------- */

    const data = {

        name: name,

        printer_name:
            printer || null,

        color: color,

        /*
         * priority NO se envía desde el frontend.
         *
         * El backend la calcula automáticamente:
         *
         * última prioridad + 1
         */
    };


    console.log(
        "Creando estación:",
        data
    );


    try {

        const response = await fetch(
            editingStationId ? `${stationApi}${editingStationId}` : stationApi,
            {
                method: editingStationId ? "PUT" : "POST",

                headers: {
                    "Content-Type":
                        "application/json",

                    "Accept":
                        "application/json"
                },

                body: JSON.stringify(data)
            }
        );


        let result = null;

        try {
            result = await response.json();
        }
        catch {
            result = null;
        }


        /* -------------------------------
           Error del backend
        -------------------------------- */

        if (!response.ok) {

            console.error(
                "Error creando estación:",
                result
            );

            let message =
                "No fue posible crear la estación.";


            if (result?.detail) {

                if (Array.isArray(result.detail)) {

                    message =
                        result.detail
                            .map(error =>
                                error.msg || "Dato inválido"
                            )
                            .join(", ");

                }
                else {

                    message =
                        String(result.detail);
                }
            }


            if (errorElement) {
                errorElement.textContent =
                    message;
            }

            return;
        }


        /* -------------------------------
           Éxito
        -------------------------------- */

        console.log(
            "Estación creada:",
            result
        );


        closeStationModal();
        editingStationId = null;
        if ($("saveStationButton")) $("saveStationButton").textContent = "Crear estación";
        await loadStations();

    }
    catch (error) {

        console.error(
            "Error de conexión:",
            error
        );

        if (errorElement) {

            errorElement.textContent =
                "No fue posible conectar con el servidor.";
        }
    }
}


async function editStation(stationId) {
    try {
        const response = await fetch(`${stationApi}${stationId}`, {headers:{Accept:"application/json"}});
        if (!response.ok) throw new Error("No se pudo cargar la estación.");
        const station = await response.json();
        editingStationId = station.id;
        $("stationName").value = station.name || "";
        $("stationPrinter").value = station.printer_name || "";
        $("stationColor").value = station.color || "#3498db";
        $("stationModal").hidden = false;
        $("saveStationButton").textContent = "Guardar cambios";
        $("stationError").textContent = "";
        $("stationName").focus();
    } catch(e) { alert(e.message); }
}
function askDeleteStation(stationId, stationName) {
    deletingStationId = stationId;
    $("deleteStationText").textContent = `¿Quieres eliminar "${stationName}"? Dejará de aparecer en las estaciones activas.`;
    $("deleteStationModal").hidden = false;
}
async function deleteStation() {
    if (!deletingStationId) return;
    try {
        const response = await fetch(`${stationApi}${deletingStationId}`, {method:"DELETE",headers:{Accept:"application/json"}});
        const data = await response.json().catch(()=>({}));
        if (!response.ok) throw new Error(data.detail || "No se pudo eliminar la estación.");
        $("deleteStationModal").hidden = true;
        deletingStationId = null;
        await loadStations();
    } catch(e) { alert(e.message); }
}

/* =========================================================
   KDS
========================================================= */

async function openKds(stationId) {

    try {

        const response = await fetch(
            `/api/screens/ensure/${stationId}`,
            {
                method: "POST",
                headers: {
                    "Accept": "application/json"
                }
            }
        );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail ||
                "No se pudo preparar la pantalla."
            );
        }


        const url =
            `/kitchen/${encodeURIComponent(result.code)}`;


        window.open(
            url,
            "_blank"
        );


        await loadStations();

    }
    catch (error) {

        console.error(
            "Error abriendo KDS:",
            error
        );

        alert(
            error.message ||
            "No se pudo abrir la pantalla de cocina."
        );
    }
}


/* =========================================================
   INICIALIZACIÓN
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "Kitchen Dashboard inicializado"
        );


        const openButton =
            $("openStationModal");

        const emptyButton =
            $("emptyCreateStation");

        const closeButton =
            $("closeStationModal");

        const cancelButton =
            $("cancelStation");

        const form =
            $("stationForm");

        const modal =
            $("stationModal");
        $("closeDeleteStation")?.addEventListener("click", () => $("deleteStationModal").hidden = true);
        $("cancelDeleteStation")?.addEventListener("click", () => $("deleteStationModal").hidden = true);
        $("confirmDeleteStation")?.addEventListener("click", deleteStation);


        /* -------------------------------
           Botón Nueva estación
        -------------------------------- */

        if (openButton) {

            openButton.addEventListener(
                "click",
                openStationModal
            );

        }
        else {

            console.error(
                "No se encontró #openStationModal"
            );
        }


        /* -------------------------------
           Primera estación
        -------------------------------- */

        if (emptyButton) {

            emptyButton.addEventListener(
                "click",
                openStationModal
            );

        }


        /* -------------------------------
           Cerrar
        -------------------------------- */

        if (closeButton) {

            closeButton.addEventListener(
                "click",
                closeStationModal
            );

        }


        if (cancelButton) {

            cancelButton.addEventListener(
                "click",
                closeStationModal
            );

        }


        /* -------------------------------
           Formulario
        -------------------------------- */

        if (form) {

            form.addEventListener(
                "submit",
                createStation
            );

        }
        else {

            console.error(
                "No se encontró #stationForm"
            );
        }


        /* -------------------------------
           Cerrar haciendo click fuera
        -------------------------------- */

        if (modal) {

            modal.addEventListener(
                "click",
                (event) => {

                    if (
                        event.target === modal
                    ) {
                        closeStationModal();
                    }

                }
            );

        }


        /* -------------------------------
           Cargar estaciones
        -------------------------------- */

        loadStations()
            .catch(error => {

                console.error(
                    error
                );

                const grid =
                    $("stationGrid");

                if (grid) {

                    grid.innerHTML = `
                        <div class="load-error">
                            ${escapeHtml(error.message)}
                        </div>
                    `;
                }

            });


        /* -------------------------------
           Actualización automática
        -------------------------------- */

        setInterval(
            () => {

                loadStations()
                    .catch(() => {});

            },
            10000
        );

    }
);
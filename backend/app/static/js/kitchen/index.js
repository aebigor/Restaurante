
const STORAGE_KEY = "kitchen_selected_station_id";

let items = [];
let historyItems = [];
let selectedStation = null;
let currentScreenCode = null;


// ==========================================================
// FECHAS
// ==========================================================

function parseBackendDate(value) {

    if (!value) return null;

    let text = String(value);

    // FastAPI está devolviendo fechas sin zona horaria.
    // Nuestro backend las guarda como UTC.
    if (
        !text.endsWith("Z") &&
        !text.includes("+")
    ) {
        text += "Z";
    }

    return new Date(text);
}


function elapsedFrom(start, end = Date.now()) {

    const date = parseBackendDate(start);

    if (!date || Number.isNaN(date.getTime())) {
        return 0;
    }

    return Math.max(
        0,
        Math.floor(
            (end - date.getTime()) / 1000
        )
    );
}


function elapsedBetween(start, end) {

    const a = parseBackendDate(start);
    const b = parseBackendDate(end);

    if (
        !a ||
        !b ||
        Number.isNaN(a.getTime()) ||
        Number.isNaN(b.getTime())
    ) {
        return 0;
    }

    return Math.max(
        0,
        Math.floor(
            (b.getTime() - a.getTime()) / 1000
        )
    );
}


function fmt(seconds) {

    seconds = Math.max(
        0,
        Number(seconds) || 0
    );

    const hours = Math.floor(seconds / 3600);

    const minutes = Math.floor(
        (seconds % 3600) / 60
    );

    const secs = seconds % 60;

    if (hours > 0) {

        return (
            String(hours).padStart(2, "0") +
            ":" +
            String(minutes).padStart(2, "0") +
            ":" +
            String(secs).padStart(2, "0")
        );
    }

    return (
        String(minutes).padStart(2, "0") +
        ":" +
        String(secs).padStart(2, "0")
    );
}


function formatClock(value) {

    const date = parseBackendDate(value);

    if (!date) return "—";

    return date.toLocaleTimeString(
        "es-CO",
        {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
    );
}


// ==========================================================
// UTILIDADES
// ==========================================================

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ==========================================================
// ESTACIONES
// ==========================================================

async function getStations() {

    const response =
        await fetch("/api/stations/");

    if (!response.ok) {
        throw new Error(
            "No se pudieron cargar las estaciones."
        );
    }

    return response.json();
}


async function getScreens() {

    const response =
        await fetch("/api/screens/");

    if (!response.ok) {
        return [];
    }

    return response.json();
}


function renderStations(stations, screens) {

    const root =
        document.getElementById("stations");

    const savedId =
        localStorage.getItem(STORAGE_KEY);

    const activeStations =
        stations.filter(
            station => station.active !== false
        );

    if (!activeStations.length) {

        root.innerHTML = `
            <div class="empty-panel">
                <strong>No hay estaciones registradas.</strong>
                <span>
                    Primero crea una estación desde
                    Administración → Cocina.
                </span>
            </div>
        `;

        return;
    }

    const screenByStation =
        new Map();

    screens
        .filter(screen => screen.active !== false)
        .forEach(screen => {

            if (
                !screenByStation.has(
                    String(screen.station_id)
                )
            ) {

                screenByStation.set(
                    String(screen.station_id),
                    screen
                );
            }
        });


    root.innerHTML =
        activeStations.map(
            (station, index) => {

                const id =
                    String(station.id);

                const screen =
                    screenByStation.get(id);

                const isSaved =
                    savedId === id;

                const isPrimary =
                    station.priority === 1 ||
                    index === 0;

                const color =
                    station.color ||
                    "#00d2ff";

                return `
                    <button
                        class="station-card ${isSaved ? "selected" : ""}"
                        data-station-id="${escapeHtml(id)}"
                        style="--station-color:${escapeHtml(color)}"
                    >

                        <div class="station-card-top">

                            <span class="station-icon">
                                ${isPrimary ? "★" : "▦"}
                            </span>

                            <div class="station-tags">

                                ${
                                    isPrimary
                                        ? '<span class="tag primary">PRINCIPAL</span>'
                                        : ""
                                }

                                ${
                                    isSaved
                                        ? '<span class="tag saved">SELECCIONADA</span>'
                                        : ""
                                }

                            </div>

                        </div>

                        <h3>
                            ${escapeHtml(station.name)}
                        </h3>

                        <p>
                            ${escapeHtml(
                                station.description ||
                                "Estación de preparación"
                            )}
                        </p>

                        <div class="station-card-bottom">

                            <span>
                                ${
                                    screen
                                        ? "Pantalla registrada"
                                        : "Pantalla se creará automáticamente"
                                }
                            </span>

                            <span class="arrow">
                                →
                            </span>

                        </div>

                    </button>
                `;
            }
        ).join("");


    root
        .querySelectorAll(".station-card")
        .forEach(card => {

            card.addEventListener(
                "click",
                () =>
                    selectStation(
                        card.dataset.stationId,
                        activeStations
                    )
            );
        });


    document
        .getElementById("selectedBadge")
        .classList
        .toggle(
            "hidden",
            !savedId
        );
}


// ==========================================================
// SELECCIONAR ESTACIÓN
// ==========================================================

async function selectStation(
    stationId,
    stations
) {

    const station =
        stations.find(
            item =>
                String(item.id) ===
                String(stationId)
        );

    if (!station) return;

    const buttons =
        document.querySelectorAll(
            ".station-card"
        );

    buttons.forEach(
        button =>
            button.disabled = true
    );

    try {

        const response =
            await fetch(
                `/api/screens/ensure/${encodeURIComponent(station.id)}`,
                {
                    method: "POST"
                }
            );

        if (!response.ok) {

            throw new Error(
                "No se pudo preparar la pantalla de esta estación."
            );
        }

        const screen =
            await response.json();

        localStorage.setItem(
            STORAGE_KEY,
            String(station.id)
        );

        localStorage.setItem(
            "kitchen_selected_station_name",
            station.name
        );

        localStorage.setItem(
            "kitchen_selected_screen_code",
            screen.code
        );

        window.location.href =
            `/kitchen/${encodeURIComponent(screen.code)}`;

    } catch (error) {

        alert(
            error.message ||
            "No se pudo seleccionar la estación."
        );

        buttons.forEach(
            button =>
                button.disabled = false
        );
    }
}


// ==========================================================
// SELECTOR
// ==========================================================

function showSelector() {

    document
        .getElementById("stationSelector")
        .classList
        .remove("hidden");

    document
        .getElementById("kitchenBoard")
        .classList
        .add("hidden");

    document
        .getElementById("changeStationBtn")
        .classList
        .add("hidden");

    document
        .getElementById("screenTitle")
        .textContent =
        "Seleccionar estación";

    document
        .getElementById("screenSubtitle")
        .textContent =
        "Selecciona manualmente la estación que atenderá esta pantalla.";

    loadStationSelector();
}


async function loadStationSelector() {

    const root =
        document.getElementById("stations");

    try {

        const [
            stations,
            screens
        ] = await Promise.all([
            getStations(),
            getScreens()
        ]);

        renderStations(
            stations,
            screens
        );

    } catch (error) {

        root.innerHTML = `
            <div class="empty-panel">

                <strong>
                    No se pudieron cargar las estaciones.
                </strong>

                <span>
                    Revisa que el servidor esté funcionando.
                </span>

            </div>
        `;
    }
}


// ==========================================================
// HEARTBEAT
// ==========================================================

async function heartbeat() {

    if (!currentScreenCode) return;

    fetch(
        `/api/screens/${encodeURIComponent(currentScreenCode)}/heartbeat`,
        {
            method: "POST"
        }
    ).catch(() => {});
}


// ==========================================================
// CARGAR COLA
// ==========================================================

async function loadBoard() {

    if (!currentScreenCode) return;

    const response =
        await fetch(
            `/api/screens/${encodeURIComponent(currentScreenCode)}/queue`
        );

    if (!response.ok) {

        showSelector();

        return;
    }

    const data =
        await response.json();

    selectedStation = data;

    document
        .getElementById("stationSelector")
        .classList
        .add("hidden");

    document
        .getElementById("kitchenBoard")
        .classList
        .remove("hidden");

    document
        .getElementById("changeStationBtn")
        .classList
        .remove("hidden");

    document
        .getElementById("screenTitle")
        .textContent =
        data.screen || "Cocina";

    document
        .getElementById("screenSubtitle")
        .textContent =
        "Pantalla asignada a esta estación · cola automática";

    document
        .getElementById("stationName")
        .textContent =
        data.screen || "Cocina";

    document
        .getElementById("stationDescription")
        .textContent =
        "Cola automática · orden de llegada";

    items =
        data.items || [];

    const queueCount =
        document.getElementById(
            "queueCount"
        );

    if (queueCount) {

        queueCount.textContent =
            items.length;
    }

    render();

    await loadHistory();
}


// ==========================================================
// RENDER COLA
// ==========================================================

function render() {

    const root =
        document.getElementById("queue");

    if (!items.length) {

        root.innerHTML = `
            <div class="empty-panel queue-empty">

                <div class="empty-icon">
                    ✓
                </div>

                <strong>
                    No hay comandas pendientes
                </strong>

                <span>
                    La estación está al día.
                    Los nuevos pedidos aparecerán automáticamente.
                </span>

            </div>
        `;

        return;
    }


    root.innerHTML =
        items.map(item => {

            const waiting =
                item.status === "WAITING";

            let waitingTime = 0;
            let preparationTime = 0;
            let totalTime = 0;

            if (waiting) {

                waitingTime =
                    elapsedFrom(
                        item.created_at
                    );

            } else {

                waitingTime =
                    item.waiting_seconds ||
                    elapsedBetween(
                        item.created_at,
                        item.started_at
                    );

                preparationTime =
                    elapsedFrom(
                        item.started_at
                    );

                totalTime =
                    waitingTime +
                    preparationTime;
            }


            return `
                <article
                    class="ticket ${String(item.status).toLowerCase()}"
                    data-item-id="${escapeHtml(item.id)}"
                >

                    <div class="ticket-head">

                        <small>
                            COMANDA
                            ${
                                item.order_id
                                    ? escapeHtml(
                                        item.order_id
                                            .slice(0, 8)
                                            .toUpperCase()
                                    )
                                    : "—"
                            }

                            · MESA
                            ${escapeHtml(
                                item.table || "—"
                            )}
                        </small>

                        <small>
                            ${
                                waiting
                                    ? "NUEVA"
                                    : "PREPARANDO"
                            }
                        </small>

                    </div>


                    <h2>
                        ${escapeHtml(item.quantity)}
                        ×
                        ${escapeHtml(item.name)}
                    </h2>


                    ${
                        waiting
                            ? `
                                <div class="time-main-label">
                                    ESPERA EN COCINA
                                </div>

                                <div
                                    class="timer"
                                    data-mode="waiting"
                                    data-created="${escapeHtml(item.created_at)}"
                                >
                                    ${fmt(waitingTime)}
                                </div>
                            `
                            : `
                                <div class="time-grid">

                                    <div>
                                        <span>
                                            ESPERA
                                        </span>

                                        <strong>
                                            ${fmt(waitingTime)}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            PREPARACIÓN
                                        </span>

                                        <strong
                                            class="preparation-timer"
                                            data-started="${escapeHtml(item.started_at)}"
                                        >
                                            ${fmt(preparationTime)}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            TOTAL
                                        </span>

                                        <strong
                                            class="total-timer"
                                            data-created="${escapeHtml(item.created_at)}"
                                        >
                                            ${fmt(totalTime)}
                                        </strong>
                                    </div>

                                </div>
                            `
                    }


                    <button
                        onclick="changeStatus(
                            '${escapeHtml(item.id)}',
                            '${escapeHtml(item.status)}'
                        )"
                    >
                        ${
                            waiting
                                ? "Tomar pedido"
                                : "Marcar listo"
                        }
                    </button>

                </article>
            `;

        }).join("");
}


// ==========================================================
// CAMBIAR ESTADO
// ==========================================================

async function changeStatus(
    id,
    status
) {

    const endpoint =
        status === "WAITING"
            ? "start"
            : "finish";

    const response =
        await fetch(
            `/api/kitchen-queue/${encodeURIComponent(id)}/${endpoint}`,
            {
                method: "PATCH"
            }
        );

    if (!response.ok) {

        alert(
            "No se pudo actualizar el estado de la comanda."
        );

        return;
    }

    await loadBoard();
}


// ==========================================================
// HISTORIAL
// ==========================================================

async function loadHistory() {

    if (!selectedStation?.station_id) {
        return;
    }

    const response =
        await fetch(
            `/api/kitchen-queue/station/${encodeURIComponent(selectedStation.station_id)}/history`
        );

    if (!response.ok) {
        return;
    }

    historyItems =
        await response.json();

    renderHistory();
}


function renderHistory() {

    const root =
        document.getElementById("history");

    if (!root) return;


    if (!historyItems.length) {

        root.innerHTML = `
            <div class="empty-panel">
                <strong>
                    Todavía no hay historial.
                </strong>

                <span>
                    Las comandas terminadas aparecerán aquí.
                </span>
            </div>
        `;

        return;
    }


    root.innerHTML =
        historyItems.map(item => {

            return `
                <article class="history-card">

                    <div class="history-main">

                        <strong>
                            ${escapeHtml(item.quantity)}
                            ×
                            ${escapeHtml(item.name)}
                        </strong>

                        <span>
                            Comanda
                            ${
                                item.order_id
                                    ? escapeHtml(
                                        item.order_id
                                            .slice(0, 8)
                                            .toUpperCase()
                                    )
                                    : "—"
                            }

                            · Mesa
                            ${escapeHtml(
                                item.table || "—"
                            )}
                        </span>

                    </div>


                    <div class="history-times">

                        <div>
                            <span>
                                ESPERA
                            </span>

                            <strong>
                                ${fmt(
                                    item.waiting_seconds
                                )}
                            </strong>
                        </div>


                        <div>
                            <span>
                                COCINA
                            </span>

                            <strong>
                                ${fmt(
                                    item.preparation_seconds
                                )}
                            </strong>
                        </div>


                        <div>
                            <span>
                                TOTAL
                            </span>

                            <strong>
                                ${fmt(
                                    item.total_seconds
                                )}
                            </strong>
                        </div>

                    </div>


                    <div class="history-finished">

                        <span>
                            LISTO
                        </span>

                        <strong>
                            ${formatClock(
                                item.finished_at
                            )}
                        </strong>

                    </div>

                </article>
            `;

        }).join("");
}


// ==========================================================
// ACTUALIZAR CRONÓMETROS
// ==========================================================

function tickTimers() {

    // Esperando
    document
        .querySelectorAll(
            ".timer[data-mode='waiting']"
        )
        .forEach(element => {

            element.textContent =
                fmt(
                    elapsedFrom(
                        element.dataset.created
                    )
                );
        });


    // Preparación
    document
        .querySelectorAll(
            ".preparation-timer"
        )
        .forEach(element => {

            element.textContent =
                fmt(
                    elapsedFrom(
                        element.dataset.started
                    )
                );
        });


    // Tiempo total
    document
        .querySelectorAll(
            ".total-timer"
        )
        .forEach(element => {

            element.textContent =
                fmt(
                    elapsedFrom(
                        element.dataset.created
                    )
                );
        });
}


// ==========================================================
// CAMBIAR ESTACIÓN
// ==========================================================

document
    .getElementById("changeStationBtn")
    .addEventListener(
        "click",
        () => {

            currentScreenCode = null;

            showSelector();
        }
    );


// ==========================================================
// HISTORIAL BOTÓN
// ==========================================================

const toggleHistoryBtn =
    document.getElementById(
        "toggleHistoryBtn"
    );

if (toggleHistoryBtn) {

    toggleHistoryBtn.addEventListener(
        "click",
        () => {

            const history =
                document.getElementById(
                    "history"
                );

            if (!history) return;

            const hidden =
                history.classList.toggle(
                    "hidden"
                );

            toggleHistoryBtn.textContent =
                hidden
                    ? "Ver historial"
                    : "Ocultar historial";
        }
    );
}


// ==========================================================
// RELOJ
// ==========================================================

function updateClock() {

    const clock =
        document.getElementById("clock");

    if (!clock) return;

    clock.textContent =
        new Date().toLocaleTimeString(
            "es-CO",
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );
}


// ==========================================================
// INICIO
// ==========================================================

async function boot() {

    const pathParts =
        window.location.pathname
            .split("/")
            .filter(Boolean);

    const screenFromUrl =
        pathParts[0] === "kitchen" &&
        pathParts[1]
            ? decodeURIComponent(
                pathParts[1]
            )
            : null;


    if (screenFromUrl) {

        currentScreenCode =
            screenFromUrl;

        await loadBoard();

        heartbeat();

        setInterval(
            loadBoard,
            5000
        );

        setInterval(
            heartbeat,
            15000
        );

        return;
    }


    showSelector();
}


// ==========================================================
// INTERVALOS
// ==========================================================

setInterval(
    tickTimers,
    1000
);

setInterval(
    updateClock,
    1000
);

updateClock();

boot();


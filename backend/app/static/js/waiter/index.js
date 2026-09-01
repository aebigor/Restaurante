// ==========================================================
// CONFIGURACIÓN
// ==========================================================

const API_BASE = "/api";


// ==========================================================
// ESTADO
// ==========================================================

let activeMenu = null;
let menuDishes = [];
let tablesData = [];
let selectedTable = null;
let selectedCategory = "all";
let cart = [];


// ==========================================================
// ELEMENTOS
// ==========================================================

const tablesContainer =
    document.getElementById("tables");

const callsContainer =
    document.getElementById("calls");

const activeMenuName =
    document.getElementById("activeMenuName");

const totalTablesElement =
    document.getElementById("totalTables");

const freeTablesElement =
    document.getElementById("freeTables");

const occupiedTablesElement =
    document.getElementById("occupiedTables");

const refreshTablesButton =
    document.getElementById("refreshTables");

const refreshCallsButton =
    document.getElementById("refreshCalls");

const refreshOrdersButton =
    document.getElementById("refreshOrders");

const activeOrdersContainer =
    document.getElementById("activeOrders");

const orderModal =
    document.getElementById("orderModal");

const closeOrderButton =
    document.getElementById("closeOrder");

const cancelOrderButton =
    document.getElementById("cancelOrder");

const sendOrderButton =
    document.getElementById("sendOrder");

const orderTitle =
    document.getElementById("orderTitle");

const orderMenuName =
    document.getElementById("orderMenuName");

const menuCategories =
    document.getElementById("menuCategories");

const dishList =
    document.getElementById("dishList");

const cartContainer =
    document.getElementById("cart");

const cartTotal =
    document.getElementById("cartTotal");

const cartTotalBottom =
    document.getElementById("cartTotalBottom");

const orderError =
    document.getElementById("orderError");


// ==========================================================
// API
// ==========================================================

async function api(url, options = {}) {

    const token =
        localStorage.getItem("token");

    const response = await fetch(
        url,
        {
            ...options,

            headers: {

                "Content-Type":
                    "application/json",

                ...(token
                    ? {
                        "Authorization":
                            `Bearer ${token}`
                    }
                    : {}),

                ...(options.headers || {})
            }
        }
    );

    let data = null;

    try {

        data = await response.json();

    } catch {

        data = null;

    }

    if (!response.ok) {

        throw new Error(
            data?.detail ||
            `Error ${response.status}`
        );
    }

    return data;
}


// ==========================================================
// FORMATO MONEDA
// ==========================================================

function formatCurrency(value) {

    return new Intl.NumberFormat(
        "es-CO",
        {
            style: "currency",
            currency: "COP",
            maximumFractionDigits: 0
        }
    ).format(value || 0);
}


// ==========================================================
// ESCAPAR HTML
// ==========================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ==========================================================
// FECHAS
// ==========================================================

function parseBackendDate(value) {

    if (!value) return null;

    const text = String(value);

    return new Date(
        text.endsWith("Z") ||
        text.includes("+")
            ? text
            : `${text}Z`
    );
}


function elapsedSince(value) {

    const date =
        parseBackendDate(value);

    if (
        !date ||
        Number.isNaN(date.getTime())
    ) {

        return 0;

    }

    return Math.max(
        0,
        Math.floor(
            (
                Date.now() -
                date.getTime()
            ) / 1000
        )
    );
}


function formatDuration(seconds) {

    const total =
        Math.max(
            0,
            Number(seconds) || 0
        );

    const h =
        Math.floor(
            total / 3600
        );

    const m =
        Math.floor(
            (total % 3600) / 60
        );

    const sec =
        total % 60;

    if (h > 0) {

        return (
            `${String(h).padStart(2, "0")}:` +
            `${String(m).padStart(2, "0")}:` +
            `${String(sec).padStart(2, "0")}`
        );

    }

    return (
        `${String(m).padStart(2, "0")}:` +
        `${String(sec).padStart(2, "0")}`
    );
}


function formatTime(value) {

    const date =
        parseBackendDate(value);

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


function updateWaiterTimers() {

    document
        .querySelectorAll(
            "[data-timer-start]"
        )
        .forEach(element => {

            const value =
                element.dataset.timerStart;

            if (value) {

                element.textContent =
                    formatDuration(
                        elapsedSince(value)
                    );

            }

        });
}


// ==========================================================
// MENÚ
// ==========================================================

async function loadMenu() {

    try {

        const data =
            await api(
                `${API_BASE}/waiter/menu`
            );

        if (
            !data.active ||
            !data.menu
        ) {

            activeMenu = null;
            menuDishes = [];

            activeMenuName.textContent =
                "Sin menú activo";

            return;
        }

        activeMenu =
            data.menu;

        menuDishes =
            data.dishes || [];

        activeMenuName.textContent =
            activeMenu.title;

    } catch (error) {

        console.error(
            "Error cargando menú:",
            error
        );

        activeMenuName.textContent =
            "Error al cargar";
    }
}


// ==========================================================
// MESAS
// ==========================================================

async function loadTables() {

    try {

        const data =
            await api(
                `${API_BASE}/waiter/tables`
            );

        tablesData =
            Array.isArray(data)
                ? data
                : data.tables || [];

        renderTables();

    } catch (error) {

        console.error(
            "Error cargando mesas:",
            error
        );

        tablesContainer.innerHTML = `
            <div class="error-state">
                No fue posible cargar las mesas.
            </div>
        `;
    }
}


// ==========================================================
// ESTADO MESA
// ==========================================================

function isTableOccupied(table) {

    return (
        table.status === "OCCUPIED" ||
        table.status === "occupied" ||
        table.occupied === true ||
        table.is_occupied === true ||
        table.session_active === true
    );
}


// ==========================================================
// RENDER MESAS
// ==========================================================

function renderTables() {

    const total =
        tablesData.length;

    const occupied =
        tablesData.filter(
            isTableOccupied
        ).length;

    const free =
        total - occupied;

    totalTablesElement.textContent =
        total;

    freeTablesElement.textContent =
        free;

    occupiedTablesElement.textContent =
        occupied;

    if (!total) {

        tablesContainer.innerHTML = `
            <div class="empty-state">
                No hay mesas registradas.
            </div>
        `;

        return;
    }

    tablesContainer.innerHTML =
        tablesData.map(table => {

            const occupied =
                isTableOccupied(table);

            const statusClass =
                occupied
                    ? "occupied"
                    : "free";

            const statusText =
                occupied
                    ? "Ocupada"
                    : "Libre";

            const tableName =
                table.name ||
                `Mesa ${table.number}`;

            const selectedClass =
                selectedTable &&
                String(
                    selectedTable.id
                ) ===
                String(table.id)
                    ? "selected"
                    : "";

            return `
                <button
                    type="button"
                    class="table-card ${statusClass} ${selectedClass}"
                    data-table-id="${escapeHtml(table.id)}"
                >

                    <div class="table-card-top">

                        <div class="table-number">
                            ${escapeHtml(
                                table.number || ""
                            )}
                        </div>

                        <span class="table-status">
                            <span></span>
                            ${statusText}
                        </span>

                    </div>

                    <div class="table-card-body">

                        <h3>
                            ${escapeHtml(
                                tableName
                            )}
                        </h3>

                        <p>
                            ${
                                table.zone
                                    ? escapeHtml(
                                        table.zone
                                    )
                                    : "Salón principal"
                            }
                        </p>

                        ${
                            occupied &&
                            table.session_opened_at
                                ? `
                                    <div class="table-live-time">

                                        <span>
                                            ⏱ Tiempo en mesa
                                        </span>

                                        <strong
                                            data-timer-start="${escapeHtml(
                                                table.session_opened_at
                                            )}"
                                        >
                                            ${formatDuration(
                                                elapsedSince(
                                                    table.session_opened_at
                                                )
                                            )}
                                        </strong>

                                    </div>
                                `
                                : ""
                        }

                    </div>

                    <div class="table-card-footer">

                        <span>
                            👥 ${table.capacity || 0} personas
                        </span>

                        <strong>
                            ${
                                occupied
                                    ? "+ Nuevo pedido"
                                    : "Tomar pedido"
                            }
                            →
                        </strong>

                    </div>

                </button>
            `;

        }).join("");

    document
        .querySelectorAll(
            ".table-card"
        )
        .forEach(card => {

            card.addEventListener(
                "click",
                () => {

                    const table =
                        tablesData.find(
                            item =>
                                String(item.id) ===
                                String(
                                    card.dataset.tableId
                                )
                        );

                    if (table) {

                        openOrder(table);

                    }

                }
            );

        });
}


// ==========================================================
// ABRIR PEDIDO
// ==========================================================

function openOrder(table) {

    if (!activeMenu) {

        alert(
            "No hay un menú activo para registrar pedidos."
        );

        return;
    }

    selectedTable =
        table;

    selectedCategory =
        "all";

    cart = [];

    orderError.textContent =
        "";

    orderTitle.textContent =
        table.name ||
        `Mesa ${table.number}`;

    orderMenuName.textContent =
        activeMenu.title;

    renderCategories();

    renderDishes();

    renderCart();

    orderModal.hidden =
        false;

    document.body.classList.add(
        "modal-open"
    );
}


// ==========================================================
// CERRAR MODAL
// ==========================================================

function closeOrder() {

    orderModal.hidden =
        true;

    document.body.classList.remove(
        "modal-open"
    );

    selectedTable =
        null;

    cart = [];

    selectedCategory =
        "all";

    orderError.textContent =
        "";
}


// ==========================================================
// CATEGORÍAS
// ==========================================================

function getCategories() {

    const categoriesMap =
        new Map();

    menuDishes.forEach(dish => {

        if (!dish.category_id) {

            return;
        }

        if (
            !categoriesMap.has(
                dish.category_id
            )
        ) {

            categoriesMap.set(
                dish.category_id,
                {
                    id: dish.category_id,
                    name:
                        dish.category ||
                        "Sin categoría"
                }
            );
        }

    });

    return Array.from(
        categoriesMap.values()
    );
}


function renderCategories() {

    const categories =
        getCategories();

    menuCategories.innerHTML = `

        <button
            type="button"
            class="category-filter ${
                selectedCategory === "all"
                    ? "active"
                    : ""
            }"
            data-category="all"
        >
            Todos
        </button>

        ${categories.map(category => `

            <button
                type="button"
                class="category-filter ${
                    String(
                        selectedCategory
                    ) ===
                    String(category.id)
                        ? "active"
                        : ""
                }"
                data-category="${escapeHtml(
                    category.id
                )}"
            >
                ${escapeHtml(
                    category.name
                )}
            </button>

        `).join("")}

    `;

    document
        .querySelectorAll(
            ".category-filter"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    selectedCategory =
                        button.dataset.category;

                    renderCategories();

                    renderDishes();
                }
            );

        });
}


// ==========================================================
// PLATOS
// ==========================================================

function renderDishes() {

    const dishes =
        menuDishes.filter(
            dish => {

                if (
                    selectedCategory ===
                    "all"
                ) {

                    return true;

                }

                return (
                    String(
                        dish.category_id
                    ) ===
                    String(
                        selectedCategory
                    )
                );

            }
        );

    if (!dishes.length) {

        dishList.innerHTML = `
            <div class="empty-state">
                No hay platos disponibles
                en esta categoría.
            </div>
        `;

        return;
    }

    dishList.innerHTML =
        dishes.map(dish => {

            const quantity =
                getCartQuantity(
                    dish.id
                );

            return `

                <article
                    class="order-dish-card"
                >

                    <div class="dish-info">

                        <div class="dish-category">
                            ${escapeHtml(
                                dish.category ||
                                "Sin categoría"
                            )}
                        </div>

                        <h4>
                            ${escapeHtml(
                                dish.name
                            )}
                        </h4>

                        ${
                            dish.description
                                ? `
                                    <p>
                                        ${escapeHtml(
                                            dish.description
                                        )}
                                    </p>
                                `
                                : ""
                        }

                        <strong>
                            ${formatCurrency(
                                dish.price
                            )}
                        </strong>

                    </div>

                    <div class="dish-actions">

                        ${
                            quantity > 0
                                ? `

                                    <div class="quantity-control">

                                        <button
                                            type="button"
                                            class="quantity-btn"
                                            data-action="remove"
                                            data-dish-id="${escapeHtml(
                                                dish.id
                                            )}"
                                        >
                                            −
                                        </button>

                                        <span>
                                            ${quantity}
                                        </span>

                                        <button
                                            type="button"
                                            class="quantity-btn"
                                            data-action="add"
                                            data-dish-id="${escapeHtml(
                                                dish.id
                                            )}"
                                        >
                                            +
                                        </button>

                                    </div>

                                `
                                : `

                                    <button
                                        type="button"
                                        class="add-dish"
                                        data-action="add"
                                        data-dish-id="${escapeHtml(
                                            dish.id
                                        )}"
                                    >
                                        + Agregar
                                    </button>

                                `
                        }

                    </div>

                </article>

            `;

        }).join("");

    document
        .querySelectorAll(
            "[data-dish-id]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const dishId =
                        button.dataset.dishId;

                    const action =
                        button.dataset.action;

                    const dish =
                        menuDishes.find(
                            item =>
                                String(
                                    item.id
                                ) ===
                                String(
                                    dishId
                                )
                        );

                    if (!dish) return;

                    if (
                        action === "add"
                    ) {

                        addToCart(dish);

                    }

                    if (
                        action === "remove"
                    ) {

                        removeFromCart(
                            dish.id
                        );

                    }

                }
            );

        });
}


// ==========================================================
// CARRITO
// ==========================================================

function getCartQuantity(dishId) {

    const item =
        cart.find(
            item =>
                String(item.id) ===
                String(dishId)
        );

    return item
        ? item.quantity
        : 0;
}


function addToCart(dish) {

    const item =
        cart.find(
            item =>
                String(item.id) ===
                String(dish.id)
        );

    if (item) {

        item.quantity += 1;

    } else {

        cart.push({

            id: dish.id,

            name: dish.name,

            price: Number(
                dish.price
            ),

            quantity: 1
        });
    }

    renderDishes();

    renderCart();
}


function removeFromCart(dishId) {

    const index =
        cart.findIndex(
            item =>
                String(item.id) ===
                String(dishId)
        );

    if (index === -1) return;

    if (
        cart[index].quantity > 1
    ) {

        cart[index].quantity -= 1;

    } else {

        cart.splice(
            index,
            1
        );
    }

    renderDishes();

    renderCart();
}


function renderCart() {

    if (!cart.length) {

        cartContainer.innerHTML = `

            <div class="cart-empty">

                <span>
                    🛒
                </span>

                <p>
                    Aún no hay productos agregados.
                </p>

            </div>

        `;

        cartTotal.textContent =
            formatCurrency(0);

        cartTotalBottom.textContent =
            formatCurrency(0);

        return;
    }

    cartContainer.innerHTML =
        cart.map(item => `

            <div class="cart-item">

                <div class="cart-item-info">

                    <h4>
                        ${escapeHtml(
                            item.name
                        )}
                    </h4>

                    <span>
                        ${formatCurrency(
                            item.price
                        )}
                    </span>

                </div>

                <div class="cart-item-actions">

                    <button
                        type="button"
                        data-cart-action="remove"
                        data-cart-id="${escapeHtml(
                            item.id
                        )}"
                    >
                        −
                    </button>

                    <strong>
                        ${item.quantity}
                    </strong>

                    <button
                        type="button"
                        data-cart-action="add"
                        data-cart-id="${escapeHtml(
                            item.id
                        )}"
                    >
                        +
                    </button>

                </div>

                <div class="cart-item-total">

                    ${formatCurrency(
                        item.price *
                        item.quantity
                    )}

                </div>

            </div>

        `).join("");

    document
        .querySelectorAll(
            "[data-cart-id]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const id =
                        button.dataset.cartId;

                    const action =
                        button.dataset.cartAction;

                    const dish =
                        menuDishes.find(
                            item =>
                                String(
                                    item.id
                                ) ===
                                String(id)
                        );

                    if (
                        action === "add" &&
                        dish
                    ) {

                        addToCart(dish);

                    }

                    if (
                        action === "remove"
                    ) {

                        removeFromCart(id);

                    }

                }
            );

        });

    const total =
        cart.reduce(
            (sum, item) =>
                sum +
                (
                    item.price *
                    item.quantity
                ),
            0
        );

    cartTotal.textContent =
        formatCurrency(total);

    cartTotalBottom.textContent =
        formatCurrency(total);
}


// ==========================================================
// ENVIAR PEDIDO
// ==========================================================

async function sendOrder() {

    orderError.textContent = "";

    // ======================================================
    // VALIDAR MESA
    // ======================================================

    if (!selectedTable) {

        orderError.textContent =
            "Debes seleccionar una mesa.";

        return;
    }

    // ======================================================
    // VALIDAR CARRITO
    // ======================================================

    if (!cart.length) {

        orderError.textContent =
            "Agrega al menos un producto al pedido.";

        return;
    }

    // ======================================================
    // EVITAR DOBLE CLICK
    // ======================================================

    if (sendOrderButton) {
        sendOrderButton.disabled = true;
    }

    try {

        // ==================================================
        // SESSION ID
        // ==================================================
        //
        // Si la mesa está libre:
        //     session_id = null
        //
        // Si la mesa ya está ocupada:
        //     usamos SU sesión existente.
        //
        // De esta manera el backend recuperará la misma
        // comanda.
        //

        const sessionId =
            selectedTable.session_id || null;

        // ==================================================
        // ENVIAR PEDIDO
        // ==================================================

        const data = await api(
            `${API_BASE}/waiter/orders`,
            {
                method: "POST",

                body: JSON.stringify({

                    /*
                     * IMPORTANTE:
                     *
                     * NO usamos Number() porque los IDs son UUID.
                     */

                    table_id:
                        selectedTable.id,

                    session_id:
                        sessionId,

                    people: 1,

                    items: cart.map(item => ({

                        dish_id:
                            item.id,

                        quantity:
                            item.quantity,

                        notes:
                            item.notes || null

                    }))

                })
            }
        );

        // ==================================================
        // ESTACIONES
        // ==================================================

        const stations =
            (data.stations || [])
                .map(
                    station => station.name
                )
                .join(", ");

        // ==================================================
        // MENSAJE
        // ==================================================

        if (sessionId) {

            alert(
                "Pedido agregado a la comanda existente." +
                (
                    stations
                        ? `\nEnviado a: ${stations}`
                        : ""
                )
            );

        } else {

            alert(
                "Pedido enviado correctamente." +
                (
                    stations
                        ? `\nEnviado a: ${stations}`
                        : ""
                )
            );
        }

        // ==================================================
        // CERRAR MODAL
        // ==================================================

        closeOrder();

        // ==================================================
        // ACTUALIZAR MESAS Y PEDIDOS
        // ==================================================

        await Promise.all([
            loadTables(),
            loadActiveOrders()
        ]);

    } catch (error) {

        console.error(
            "Error enviando pedido:",
            error
        );

        orderError.textContent =
            error.message ||
            "No fue posible enviar el pedido.";

    } finally {

        if (sendOrderButton) {
            sendOrderButton.disabled = false;
        }
    }
}


// ==========================================================
// SOLICITUDES
// ==========================================================

async function loadCalls() {

    try {

        const data =
            await api(
                `${API_BASE}/waiter-calls/pending`
            );

        const calls =
            Array.isArray(data)
                ? data
                : data.calls || [];

        renderCalls(calls);

    } catch (error) {

        console.error(
            "Error cargando solicitudes:",
            error
        );
    }
}


function renderCalls(calls) {

    if (!calls.length) {

        callsContainer.innerHTML = `
            <div class="empty-state">
                No hay solicitudes pendientes.
            </div>
        `;

        return;
    }

    callsContainer.innerHTML =
        calls.map(call => `

            <article class="call-card">

                <div>

                    <span>
                        MESA
                    </span>

                    <h3>
                        ${escapeHtml(
                            call.table_name ||
                            call.table_number ||
                            "Sin información"
                        )}
                    </h3>

                </div>

                <div>

                    <span class="call-status">
                        Solicita atención
                    </span>

                </div>

            </article>

        `).join("");
}


// ==========================================================
// ESTADOS PEDIDO
// ==========================================================

function orderStatusLabel(status) {

    const labels = {

        PENDING:
            "Pendiente",

        PREPARING:
            "Preparando",

        READY:
            "Listo",

        SERVED:
            "Entregado",

        CLOSED:
            "Cerrado",

        OPEN:
            "En cocina"

    };

    return (
        labels[status] ||
        status ||
        "Pendiente"
    );
}


function orderStatusClass(status) {

    return String(
        status || "PENDING"
    ).toLowerCase();
}


// ==========================================================
// PEDIDOS ACTIVOS
// ==========================================================

async function loadActiveOrders() {

    if (!activeOrdersContainer)
        return;

    try {

        const orders =
            await api(
                `${API_BASE}/waiter/orders/active`
            );

        renderActiveOrders(
            Array.isArray(orders)
                ? orders
                : []
        );

    } catch (error) {

        console.error(
            "Error cargando pedidos activos:",
            error
        );

        activeOrdersContainer.innerHTML = `
            <div class="error-state">
                No fue posible consultar los pedidos activos.
            </div>
        `;
    }
}


// ==========================================================
// RENDER PEDIDOS
// ==========================================================

function renderActiveOrders(
    orders
) {

    if (!orders.length) {

        activeOrdersContainer.innerHTML = `
            <div class="empty-state">
                No tienes pedidos activos.
            </div>
        `;

        return;
    }

    activeOrdersContainer.innerHTML =
        orders.map(order => {

            const allReady =
                order.status === "READY";

            const served =
                Boolean(
                    order.served_at
                ) ||
                order.status === "SERVED";

            const sessionTime =
                order.session_opened_at
                    ? elapsedSince(
                        order.session_opened_at
                    )
                    : 0;

            const orderAge =
                elapsedSince(
                    order.created_at
                );

            const eatingTime =
                served
                    ? elapsedSince(
                        order.served_at
                    )
                    : 0;

            return `

                <article
                    class="
                        active-order-card
                        ${allReady ? "order-ready" : ""}
                        ${served ? "order-served" : ""}
                    "
                >

                    <!-- ==================================
                         ENCABEZADO
                    =================================== -->

                    <div class="active-order-head">

                        <div>

                            <span class="section-label">
                                MESA
                                ${escapeHtml(
                                    order.table_number
                                )}
                            </span>

                            <h3>
                                Comanda #${escapeHtml(
                                    String(
                                        order.id
                                    )
                                        .slice(
                                            0,
                                            8
                                        )
                                        .toUpperCase()
                                )}
                            </h3>

                        </div>

                        <span
                            class="
                                order-status
                                ${orderStatusClass(
                                    order.status
                                )}
                            "
                        >

                            ${
                                served
                                    ? "🍽 ENTREGADO"
                                    : allReady
                                        ? "✓ TODO LISTO"
                                        : orderStatusLabel(
                                            order.status
                                        )
                            }

                        </span>

                    </div>


                    <!-- ==================================
                         TIEMPOS
                    =================================== -->

                    <div class="order-timing-grid">

                        <div class="timing-box">

                            <span>
                                TIEMPO EN MESA
                            </span>

                            <strong
                                data-timer-start="${escapeHtml(
                                    order.session_opened_at ||
                                    ""
                                )}"
                            >
                                ${formatDuration(
                                    sessionTime
                                )}
                            </strong>

                        </div>


                        <div class="timing-box">

                            <span>
                                PEDIDO HACE
                            </span>

                            <strong
                                data-timer-start="${escapeHtml(
                                    order.created_at ||
                                    ""
                                )}"
                            >
                                ${formatDuration(
                                    orderAge
                                )}
                            </strong>

                        </div>


                        <div class="timing-box">

                            <span>

                                ${
                                    served
                                        ? "COMIENDO"
                                        : "ESTADO"
                                }

                            </span>

                            ${
                                served
                                    ? `

                                        <strong
                                            data-timer-start="${escapeHtml(
                                                order.served_at
                                            )}"
                                        >
                                            ${formatDuration(
                                                eatingTime
                                            )}
                                        </strong>

                                    `
                                    : `

                                        <strong>
                                            ${orderStatusLabel(
                                                order.status
                                            )}
                                        </strong>

                                    `
                            }

                        </div>

                    </div>


                    <!-- ==================================
                         PRODUCTOS
                    =================================== -->

                    <div class="active-order-items">

                        ${
                            (order.items || [])
                                .map(
                                    item => `

                                        <div
                                            class="active-order-item"
                                        >

                                            <div>

                                                <strong>
                                                    ${escapeHtml(
                                                        item.quantity
                                                    )}
                                                    ×
                                                    ${escapeHtml(
                                                        item.name
                                                    )}
                                                </strong>

                                                ${
                                                    item.notes
                                                        ? `
                                                            <small>
                                                                ${escapeHtml(
                                                                    item.notes
                                                                )}
                                                            </small>
                                                        `
                                                        : ""
                                                }

                                            </div>

                                            <span
                                                class="
                                                    item-status
                                                    ${orderStatusClass(
                                                        item.status
                                                    )}
                                                "
                                            >

                                                ${
                                                    item.status ===
                                                    "READY"

                                                        ? "✓ Listo"

                                                        : item.status ===
                                                          "SERVED"

                                                            ? "✓ Entregado"

                                                            : orderStatusLabel(
                                                                item.status
                                                            )
                                                }

                                            </span>

                                        </div>

                                    `
                                )
                                .join("")
                        }

                    </div>


                    <!-- ==================================
                         INFORMACIÓN
                    =================================== -->

                    <div class="active-order-meta">

                        <span>
                            Pedido:
                            <strong>
                                ${formatTime(
                                    order.created_at
                                )}
                            </strong>
                        </span>

                        ${
                            order.served_at
                                ? `
                                    <span>
                                        Entregado:
                                        <strong>
                                            ${formatTime(
                                                order.served_at
                                            )}
                                        </strong>
                                    </span>
                                `
                                : ""
                        }

                        <strong>
                            Total
                            ${formatCurrency(
                                order.total
                            )}
                        </strong>

                    </div>


                    <!-- ==================================
                         ACCIONES
                    =================================== -->

                    <div class="active-order-actions">

                        ${
                            allReady &&
                            !served

                                ? `

                                    <button
                                        type="button"
                                        class="order-action primary-action"
                                        onclick="serveOrder('${escapeHtml(
                                            order.id
                                        )}')"
                                    >
                                        ✓ Entregar pedido
                                    </button>

                                `

                                : ""
                        }


                        ${
                            served

                                ? `

                                    <button
                                        type="button"
                                        class="order-action secondary-action"
                                        onclick="printOrder('${escapeHtml(
                                            order.id
                                        )}')"
                                    >
                                        🖨 Imprimir comanda
                                    </button>

                                    <span class="served-note">
                                        ✓ Pedido entregado ·
                                        el tiempo de comida está corriendo
                                    </span>

                                `

                                : `

                                    <span class="kitchen-note">

                                        ${
                                            allReady
                                                ? "Listo para entregar"
                                                : "La cocina está trabajando"
                                        }

                                    </span>

                                `
                        }

                    </div>


                    <!-- ==================================
                         PIE
                    =================================== -->

                    <div class="active-order-footer">

                        <strong>
                            Total
                            ${formatCurrency(
                                order.total
                            )}
                        </strong>

                        <div class="order-footer-actions">

                            <!-- NUEVO PEDIDO -->

                            <button
                                type="button"
                                class="new-order-inline"
                                onclick="newOrderForTable('${escapeHtml(
                                    order.table_id
                                )}')"
                            >
                                ＋ Nuevo pedido
                            </button>


                            <!-- LIBERAR MESA -->

                            ${
                                served

                                    ? `

                                        <button
                                            type="button"
                                            class="close-table-inline"
                                            onclick="closeTableSession('${escapeHtml(
                                                order.session_id
                                            )}')"
                                        >
                                            🔓 Liberar mesa
                                        </button>

                                    `

                                    : ""
                            }

                        </div>

                    </div>

                </article>

            `;

        }).join("");
}


// ==========================================================
// ENTREGAR PEDIDO
// ==========================================================

async function serveOrder(
    orderId
) {

    if (
        !confirm(
            "¿Confirmas que el pedido fue entregado al cliente?"
        )
    ) {

        return;
    }

    try {

        await api(
            `${API_BASE}/waiter/orders/${encodeURIComponent(
                orderId
            )}/serve`,
            {
                method: "PATCH"
            }
        );

        await loadActiveOrders();

    } catch (error) {

        alert(
            error.message ||
            "No se pudo marcar el pedido como entregado."
        );
    }
}


// ==========================================================
// IMPRIMIR COMANDA
// ==========================================================

async function printOrder(
    orderId
) {

    try {

        const orders =
            await api(
                `${API_BASE}/waiter/orders/active`
            );

        const order =
            orders.find(
                item =>
                    String(item.id) ===
                    String(orderId)
            );

        if (!order) {

            throw new Error(
                "No se encontró la comanda."
            );
        }

        const popup =
            window.open(
                "",
                "_blank",
                "width=420,height=700"
            );

        if (!popup) {

            throw new Error(
                "El navegador bloqueó la ventana de impresión."
            );
        }

        const items =
            (order.items || [])
                .map(
                    item => `

                        <tr>

                            <td>
                                ${escapeHtml(
                                    item.quantity
                                )}
                                ×
                                ${escapeHtml(
                                    item.name
                                )}
                            </td>

                            <td>
                                ${formatCurrency(
                                    item.total
                                )}
                            </td>

                        </tr>

                    `
                )
                .join("");

        popup.document.write(`

            <!doctype html>

            <html lang="es">

            <head>

                <meta charset="utf-8">

                <title>
                    Comanda
                </title>

                <style>

                    body {

                        font-family:
                            Arial,
                            sans-serif;

                        width:
                            320px;

                        margin:
                            20px auto;

                        color:
                            #111;

                    }

                    h1 {

                        text-align:
                            center;

                        font-size:
                            20px;

                        margin:
                            0 0 8px;

                    }

                    h2 {

                        text-align:
                            center;

                        font-size:
                            16px;

                        margin:
                            8px 0 18px;

                    }

                    p {

                        margin:
                            5px 0;

                        font-size:
                            12px;

                    }

                    table {

                        width:
                            100%;

                        border-collapse:
                            collapse;

                        margin-top:
                            15px;

                        font-size:
                            13px;

                    }

                    td {

                        padding:
                            7px 0;

                        border-bottom:
                            1px dashed #999;

                    }

                    td:last-child {

                        text-align:
                            right;

                        white-space:
                            nowrap;

                    }

                    .total {

                        font-size:
                            16px;

                        font-weight:
                            700;

                        text-align:
                            right;

                        margin-top:
                            15px;

                    }

                    @media print {

                        body {

                            margin:
                                0 auto;

                        }

                    }

                </style>

            </head>

            <body>

                <h1>
                    COMANDA
                </h1>

                <h2>
                    Mesa
                    ${escapeHtml(
                        order.table_number
                    )}
                </h2>

                <p>
                    Pedido #${escapeHtml(
                        String(
                            order.id
                        )
                            .slice(
                                0,
                                8
                            )
                            .toUpperCase()
                    )}
                </p>

                <p>
                    Hora:
                    ${formatTime(
                        order.created_at
                    )}
                </p>

                <table>

                    ${items}

                </table>

                <div class="total">

                    Total:
                    ${formatCurrency(
                        order.total
                    )}

                </div>

                <script>

                    window.onload =
                        function() {

                            window.print();

                        };

                </script>

            </body>

            </html>

        `);

        popup.document.close();

    } catch (error) {

        alert(
            error.message ||
            "No se pudo imprimir la comanda."
        );
    }
}


// ==========================================================
// NUEVO PEDIDO PARA LA MISMA MESA
// ==========================================================

async function newOrderForTable(
    tableId
) {

    let table =
        tablesData.find(
            item =>
                String(item.id) ===
                String(tableId)
        );

    if (!table) {

        await loadTables();

        table =
            tablesData.find(
                item =>
                    String(item.id) ===
                    String(tableId)
            );
    }

    if (table) {

        openOrder(table);

    }
}


// ==========================================================
// LIBERAR MESA
// ==========================================================

async function closeTableSession(
    sessionId
) {

    if (!sessionId) {

        return;
    }

    const confirmed =
        confirm(
            "¿Confirmas que la cuenta ya fue pagada y la mesa está limpia?\n\nLa mesa pasará a LIBRE."
        );

    if (!confirmed) {

        return;
    }

    try {

        await api(
            `${API_BASE}/waiter/sessions/${encodeURIComponent(
                sessionId
            )}/close`,
            {
                method: "PATCH"
            }
        );

        alert(
            "Mesa liberada correctamente."
        );

        await Promise.all([
            loadTables(),
            loadActiveOrders()
        ]);

    } catch (error) {

        alert(
            error.message ||
            "No se pudo liberar la mesa."
        );
    }
}


// ==========================================================
// EVENTOS
// ==========================================================

if (refreshTablesButton) {

    refreshTablesButton.addEventListener(
        "click",
        loadTables
    );

}


if (refreshCallsButton) {

    refreshCallsButton.addEventListener(
        "click",
        loadCalls
    );

}


if (refreshOrdersButton) {

    refreshOrdersButton.addEventListener(
        "click",
        loadActiveOrders
    );

}


if (closeOrderButton) {

    closeOrderButton.addEventListener(
        "click",
        closeOrder
    );

}


if (cancelOrderButton) {

    cancelOrderButton.addEventListener(
        "click",
        closeOrder
    );

}


if (sendOrderButton) {

    sendOrderButton.addEventListener(
        "click",
        sendOrder
    );

}


if (orderModal) {

    orderModal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                orderModal
            ) {

                closeOrder();

            }

        }
    );

}


document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape" &&
            orderModal &&
            !orderModal.hidden
        ) {

            closeOrder();

        }

    }
);


// ==========================================================
// INICIO
// ==========================================================

async function init() {

    await loadMenu();

    await loadTables();

    await loadCalls();

    await loadActiveOrders();

}


init();


// ==========================================================
// ACTUALIZACIÓN AUTOMÁTICA
// ==========================================================

setInterval(
    loadTables,
    10000
);

setInterval(
    loadCalls,
    5000
);

setInterval(
    loadActiveOrders,
    5000
);

setInterval(
    updateWaiterTimers,
    1000
);
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

const printComandaButton =
    document.getElementById("printComanda");

let lastComandaConfirmationCode = null;
let preopenedPrintWindow = null;

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


const mealNotificationState = new Map();

function showMealTimeNotification(table, minutes) {
    const tableName = table.name || `Mesa ${table.number}`;
    const message = `⚠️ ${tableName} lleva ${minutes} minutos. Revisa si el cliente necesita atención.`;

    let container = document.getElementById("waiterMealNotifications");
    if (!container) {
        container = document.createElement("div");
        container.id = "waiterMealNotifications";
        container.className = "waiter-meal-notifications";
        document.body.appendChild(container);
    }

    const alert = document.createElement("div");
    alert.className = "waiter-meal-alert";
    alert.innerHTML = `<strong>${escapeHtml(message)}</strong><button type="button" aria-label="Cerrar aviso">×</button>`;
    alert.querySelector("button").addEventListener("click", () => alert.remove());
    container.appendChild(alert);

    window.setTimeout(() => alert.remove(), 12000);

    // La notificación del navegador es opcional; el aviso visible del panel
    // siempre se muestra aunque el navegador no tenga permisos.
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Aviso de mesa", { body: message });
    }
}

function checkMealTimeNotifications() {
    tablesData.forEach(table => {
        if (!table.prepayment_required || !table.session_opened_at) return;
        if (table.status === "FREE" || table.status === "CLOSED") return;

        const elapsed = elapsedSince(table.session_opened_at);
        const milestone = Math.floor(elapsed / 1800);
        if (milestone < 1) return;

        const key = `${table.id}:${table.session_id || "session"}`;
        const previous = mealNotificationState.get(key) || 0;
        if (milestone > previous) {
            mealNotificationState.set(key, milestone);
            showMealTimeNotification(table, milestone * 30);
        }
    });
}

function updateMealTimeWarnings() {
    document.querySelectorAll("[data-meal-warning-start]").forEach(element => {
        const start = element.dataset.mealWarningStart;
        const elapsed = elapsedSince(start);
        const reached = elapsed >= 1800;
        element.hidden = !reached;
        if (reached) {
            element.innerHTML = "⚠️ Esta mesa lleva <strong>30 minutos o más comiendo.</strong><span>Revisa la mesa y verifica si el cliente necesita atención.</span>";
        }
    });
}


function updateWaiterTimers() {

    checkMealTimeNotifications();
    updateMealTimeWarnings();

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

        const dishes = data.dishes || [];
        const products = (data.products || []).map(product => ({
            ...product,
            is_product: true
        }));

        menuDishes = [...dishes, ...products];

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
        table.status === "PAID" ||
        table.status === "paid" ||
        table.status === "CLEAN" ||
        table.status === "clean" ||
        table.occupied === true ||
        table.is_occupied === true ||
        table.session_active === true
    );
}

function isTablePaid(table) {
    return table.status === "PAID" || table.status === "paid";
}

function isTableClean(table) {
    return table.status === "CLEAN" || table.status === "clean";
}


// ==========================================================
// RENDER MESAS
// ==========================================================

function renderTables() {

    const total = tablesData.length;

    const occupied = tablesData.filter(isTableOccupied).length;
    const free = total - occupied;
    const paid = tablesData.filter(isTablePaid).length;

    totalTablesElement.textContent = total;
    freeTablesElement.textContent = free;
    occupiedTablesElement.textContent = occupied;

    if (!total) {
        tablesContainer.innerHTML = `
            <div class="empty-state">No hay mesas registradas.</div>
        `;
        return;
    }

    tablesContainer.innerHTML = tablesData.map(table => {
        const occupiedTable = isTableOccupied(table);
        const paidTable = isTablePaid(table);
        const cleanTable = isTableClean(table);
        const statusClass = cleanTable ? "clean" : paidTable ? "paid" : occupiedTable ? "occupied" : "free";
        const statusText = cleanTable ? "Limpia · espera Caja" : paidTable ? "Pagada" : occupiedTable ? "Ocupada" : "Libre";
        const tableName = table.name || `Mesa ${table.number}`;
        const selectedClass = selectedTable && String(selectedTable.id) === String(table.id) ? "selected" : "";

        return `
            <article class="table-card ${statusClass} ${selectedClass}">
                <div class="table-card-top">
                    <div class="table-number">${escapeHtml(table.number || "")}</div>
                    <span class="table-status"><span></span>${statusText}</span>
                </div>

                <div class="table-card-body">
                    <h3>${escapeHtml(tableName)}</h3>
                    <p>${table.zone ? escapeHtml(table.zone) : "Salón principal"}</p>
                    <div class="table-operation-badges">
                        ${table.prepayment_required ? '<span class="table-badge prepay">💳 PAGA PRIMERO</span>' : ''}
                        ${table.comanda_print_priority === 1 ? '<span class="table-badge high">🔴 COMANDA PRIMERO</span>' : table.comanda_print_priority === 3 ? '<span class="table-badge low">⚪ COMANDA ÚLTIMA</span>' : ''}
                    </div>

                    ${
                        table.payment_pending
                            ? `
                                <div class="payment-waiting-box">
                                    <strong>💳 Esperando pago en Caja</strong>
                                    <span>El cliente debe acercarse con la comanda antes de enviar la preparación.</span>
                                    <div>⏱ Tiempo en espera <b data-timer-start="${escapeHtml(table.payment_pending_since || table.session_opened_at)}">${formatDuration(elapsedSince(table.payment_pending_since || table.session_opened_at))}</b></div>
                                </div>
                            `
                            : paidTable || cleanTable
                            ? `
                                <div class="table-paid-notice">
                                    <strong>${cleanTable ? "✓ Mesa marcada como limpia" : "✓ Pago autorizado por caja"}</strong>
                                    <span>${cleanTable ? "Caja debe realizar la liberación." : "Entrega todos los pedidos y marca la mesa como limpia."}</span>
                                </div>
                                ${table.last_served_at ? `
                                    <div class="table-live-time">
                                        <span>🍽 Último pedido entregado</span>
                                        <strong data-timer-start="${escapeHtml(table.last_served_at)}">
                                            ${formatDuration(elapsedSince(table.last_served_at))}
                                        </strong>
                                    </div>
                                ` : ""}
                                ${table.prepayment_required && table.session_opened_at ? `
                                    <div class="meal-time-warning"
                                         data-meal-warning-start="${escapeHtml(table.session_opened_at)}"
                                         hidden>
                                    </div>
                                ` : ""}
                            `
                            : occupiedTable && table.session_opened_at
                                ? `
                                    <div class="table-live-time">
                                        <span>⏱ Tiempo en mesa</span>
                                        <strong data-timer-start="${escapeHtml(table.session_opened_at)}">
                                            ${formatDuration(elapsedSince(table.session_opened_at))}
                                        </strong>
                                    </div>
                                    ${table.prepayment_required ? `
                                        <div class="meal-time-warning"
                                             data-meal-warning-start="${escapeHtml(table.session_opened_at)}"
                                             hidden>
                                        </div>
                                    ` : ""}
                                `
                                : ""
                    }
                </div>

                <div class="table-card-footer">
                    <span>👥 ${table.capacity || 0} personas</span>
                    ${
                        paidTable
                            ? table.can_mark_clean
                                ? table.prepayment_required
                                    ? `
                                        <button type="button" class="clean-table-button prepayment-release-button" onclick="event.stopPropagation(); markTableClean('${escapeHtml(table.session_id)}', true)">
                                            ✅ Confirmar salida y liberar mesa
                                        </button>
                                    `
                                    : `
                                        <button type="button" class="clean-table-button" onclick="event.stopPropagation(); markTableClean('${escapeHtml(table.session_id)}', false)">
                                            🧹 Marcar mesa limpia
                                        </button>
                                    `
                                : `<span class="waiting-cash-release">🍽️ Pendiente: ${table.pending_delivery || 0} pedido(s) por entregar</span>`
                            : cleanTable
                                ? `<span class="waiting-cash-release">🔒 Esperando liberación de Caja</span>`
                            : `
                                <button type="button" class="table-open-button">
                                    ${occupiedTable ? "+ Nuevo pedido" : "Tomar pedido"} →
                                </button>
                            `
                    }
                </div>
            </article>
        `;
    }).join("");

    document.querySelectorAll(".table-card").forEach(card => {
        card.addEventListener("click", () => {
            const table = tablesData.find(item => String(item.id) === String(card.dataset.tableId));
            if (!table || isTablePaid(table) || isTableClean(table)) return;
            openOrder(table);
        });
        card.dataset.tableId = card.querySelector(".table-number")?.textContent?.trim() || "";
    });

    // Corregimos el identificador real de cada tarjeta sin confiar en el texto visual.
    document.querySelectorAll(".table-card").forEach((card, index) => {
        card.dataset.tableId = String(tablesData[index].id);
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

            quantity: 1,

            is_product: Boolean(dish.is_product)
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
        if (printComandaButton) printComandaButton.disabled = true;
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
    if (printComandaButton) printComandaButton.disabled = false;
}


function renderComandaPrint(win, confirmationCode = null) {
    if (!win || win.closed || !selectedTable || !cart.length) return;

    const total = cart.reduce((sum, item) => sum + Number(item.price || 0) * Number(item.quantity || 0), 0);
    const tableName = selectedTable.name || `Mesa ${selectedTable.number}`;
    const rows = cart.map(item => `<tr><td>${escapeHtml(item.quantity)} × ${escapeHtml(item.name)}</td><td>${formatCurrency(Number(item.price || 0) * Number(item.quantity || 0))}</td></tr>`).join("");
    const isPrepayment = Boolean(selectedTable.prepayment_required);
    const mode = isPrepayment ? "PAGO ANTICIPADO · LLEVAR A CAJA" : "COMANDA DE MESA";
    const codeBlock = isPrepayment && confirmationCode ? `<div class="code"><small>CÓDIGO DE COMANDA</small><strong>${escapeHtml(confirmationCode)}</strong><span>Entrégalo en Caja para autorizar el paso a cocina.</span></div>` : "";

    win.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Comanda ${escapeHtml(tableName)}</title><style>body{font-family:Arial,sans-serif;padding:24px;color:#111}h1{font-size:22px;margin:0 0 6px}h2{font-size:13px;margin:0 0 18px}table{width:100%;border-collapse:collapse}td{padding:8px 0;border-bottom:1px dashed #bbb}td:last-child{text-align:right;font-weight:700}.total{display:flex;justify-content:space-between;margin-top:18px;font-size:18px;font-weight:800}.note{margin:16px 0;padding:10px;background:#f3f3f3;font-weight:800;font-size:12px;text-align:center}.code{margin:16px 0;padding:14px;border:2px solid #111;text-align:center}.code small{display:block;font-size:10px;font-weight:700}.code strong{display:block;font-size:30px;letter-spacing:6px;margin:7px 0}.code span{display:block;font-size:10px}</style></head><body><h1>CRIPTONIX</h1><h2>${escapeHtml(tableName)} · ${escapeHtml(selectedTable.zone || "Salón")}</h2><div class="note">${mode}</div>${codeBlock}<table>${rows}</table><div class="total"><span>TOTAL</span><span>${formatCurrency(total)}</span></div><p style="margin-top:24px;font-size:11px">Fecha: ${new Date().toLocaleString("es-CO")}</p><script>window.onload=()=>{window.print();setTimeout(()=>window.close(),500)}<\/script></body></html>`);
    win.document.close();
}

function printComanda(confirmationCode = lastComandaConfirmationCode) {
    if (!selectedTable || !cart.length) {
        alert("Agrega productos antes de imprimir la comanda.");
        return;
    }
    const win = window.open("", "_blank", "width=420,height=700");
    if (!win) { alert("El navegador bloqueó la ventana de impresión. Permite ventanas emergentes para este sitio."); return; }
    renderComandaPrint(win, confirmationCode);
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
        // PREABRIR IMPRESIÓN PARA MESAS DE PAGO ANTICIPADO
        // El popup se abre antes del await para que el navegador no lo bloquee.
        // ==================================================

        if (selectedTable.prepayment_required) {
            preopenedPrintWindow = window.open("", "_blank", "width=420,height=700");
        }

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

                        dish_id: item.is_product ? null : item.id,
                        product_id: item.is_product ? item.id : null,

                        quantity: item.quantity,

                        notes: item.notes || null

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

        if (data.payment_pending) {
            lastComandaConfirmationCode = data.confirmation_code || null;
            if (preopenedPrintWindow && !preopenedPrintWindow.closed) {
                renderComandaPrint(preopenedPrintWindow, lastComandaConfirmationCode);
            } else {
                alert(
                    "Comanda registrada. Esta mesa exige pago anticipado.\n\nImprime la comanda y entrega el código en Caja. Cocina la recibirá después del pago."
                );
            }
            preopenedPrintWindow = null;
            if (printComandaButton) printComandaButton.disabled = false;
        } else if (sessionId) {

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
        // ACTUALIZAR MESAS Y PEDIDOS
        // ==================================================
        // Para pago anticipado mantenemos la comanda abierta para que
        // el mesero pueda imprimirla. Para mesas normales cerramos.
        if (!data.payment_pending) {
            closeOrder();
        }
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
        calls.map(call => {

            // Buscar la mesa en las mesas que ya cargó el panel
            const table =
                tablesData.find(
                    t => String(t.id) === String(call.table_id)
                );

            const tableNumber =
                table?.number ??
                table?.table_number ??
                call.table_number ??
                call.table_id ??
                "Sin información";

            return `

                <article class="call-card">

                    <div class="call-info">

                        <span>
                            MESA
                        </span>

                        <h3>
                            ${escapeHtml(
                                String(tableNumber)
                            )}
                        </h3>

                    </div>


                    <div class="call-actions">

                        <span class="call-status">
                            Solicita atención
                        </span>

                        <button
                            type="button"
                            class="call-attended-btn"
                            data-call-id="${escapeHtml(
                                String(call.id)
                            )}"
                            onclick="attendCall('${escapeHtml(
                                String(call.id)
                            )}', this)"
                        >
                            ✓ Atendido
                        </button>

                    </div>

                </article>

            `;
        }).join("");
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
// MARCAR SOLICITUD COMO ATENDIDA
// ==========================================================

async function attendCall(callId, button) {

    if (!callId) {
        return;
    }


    const originalText =
        button.textContent;


    button.disabled = true;

    button.textContent =
        "Procesando...";


    try {

        await api(
            `${API_BASE}/waiter-calls/${encodeURIComponent(callId)}`,
            {
                method: "PATCH",

                body: JSON.stringify({
                    status: "ATTENDED"
                })
            }
        );


        // Recargar las solicitudes.
        // La solicitud atendida ya no aparecerá porque
        // /pending solamente devuelve REQUESTED y ACKNOWLEDGED.

        await loadCalls();


    } catch (error) {

        console.error(
            "Error atendiendo solicitud:",
            error
        );


        button.disabled = false;

        button.textContent =
            originalText;


        alert(
            error.message ||
            "No fue posible marcar la solicitud como atendida."
        );
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

            const readyItems = (order.items || []).filter(
                item => item.status === "READY"
            ).length;

            const totalItems = (order.items || []).filter(
                item => item.status !== "CANCELLED"
            ).length;

            const servedItems = (order.items || []).filter(
                item => item.status === "SERVED"
            ).length;

            const allReady =
                totalItems > 0 && readyItems + servedItems === totalItems;

            const allServed =
                totalItems > 0 && servedItems === totalItems;

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
                                    : allServed
                                        ? "✓ TODO ENTREGADO"
                                        : readyItems > 0
                                            ? `✓ ${readyItems + servedItems}/${totalItems} DISPONIBLE`
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
                                                    item.status === "READY"
                                                        ? `
                                                            <button
                                                                type="button"
                                                                class="item-deliver-button"
                                                                onclick="serveOrderItem('${escapeHtml(order.id)}','${escapeHtml(item.id)}')"
                                                            >
                                                                ✓ Entregar
                                                            </button>
                                                          `
                                                        : item.status === "SERVED"
                                                            ? "✓ Entregado"
                                                            : orderStatusLabel(item.status)
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
                            allServed && !served
                                ? `
                                    <button
                                        type="button"
                                        class="order-action primary-action"
                                        onclick="serveOrder('${escapeHtml(order.id)}')"
                                    >
                                        ✓ Confirmar entrega total
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
                                            allServed
                                                ? "Todos los productos fueron entregados. Confirma la entrega total."
                                                : readyItems > 0
                                                    ? `${readyItems + servedItems} de ${totalItems} producto(s) disponible(s) — entrega los que ya están listos`
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


                            <!-- La liberación de la mesa pertenece exclusivamente a Caja. -->

                        </div>

                    </div>

                </article>

            `;

        }).join("");
}


// ==========================================================
// ENTREGAR PRODUCTO INDIVIDUAL
// ==========================================================

async function serveOrderItem(orderId, itemId) {
    try {
        await api(
            `${API_BASE}/waiter/orders/${encodeURIComponent(orderId)}/items/${encodeURIComponent(itemId)}/serve`,
            { method: "PATCH" }
        );
        await loadActiveOrders();
    } catch (error) {
        alert(error.message || "No se pudo entregar el producto.");
    }
}


// ==========================================================
// CONFIRMAR COMANDA COMPLETA
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

                ${order.prepayment_required ? `
                    <p style="font-weight:800;text-align:center;border:2px solid #111;padding:8px;margin:12px 0;">
                        💳 PAGO ANTICIPADO — PASAR POR CAJA
                    </p>
                ` : ""}

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

async function markTableClean(sessionId, isPrepayment = false) {
    if (!sessionId) return;

    const message = isPrepayment
        ? "¿Confirmas que los clientes ya se retiraron y que la mesa está completamente limpia?\\n\\nLa mesa de pago anticipado quedará LIBRE inmediatamente."
        : "¿Confirmas que la mesa ya está completamente limpia?\\n\\nEl pago ya fue autorizado por Caja. La mesa quedará en estado LIMPIA y Caja será quien la libere.";

    const confirmed = confirm(message);
    if (!confirmed) return;

    try {
        const response = await api(
            `${API_BASE}/waiter/sessions/${encodeURIComponent(sessionId)}/clean`,
            { method: "PATCH" }
        );

        alert(response.message || (
            isPrepayment
                ? "Mesa liberada correctamente."
                : "Mesa marcada como limpia. Caja debe liberarla."
        ));

        await Promise.all([loadTables(), loadActiveOrders()]);
    } catch (error) {
        alert(error.message || "No se pudo actualizar el estado de la mesa.");
    }
}

// Compatibilidad: ningún botón del mesero debe llamar esta función para liberar.
async function closeTableSession() {
    alert("El mesero no puede liberar mesas. Marca la mesa como limpia y Caja realizará la liberación.");
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

if (printComandaButton) {
    printComandaButton.addEventListener("click", printComanda);
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

// Refresco rápido para que el estado de pago/limpieza y las mesas
// se reflejen casi en tiempo real sin depender de recargar la página.
setInterval(
    loadTables,
    1000
);

setInterval(
    loadCalls,
    5000
);

// La cocina puede marcar un solo producto como LISTO. El mesero debe
// verlo en la comanda aunque los demás productos todavía estén trabajando.
setInterval(
    loadActiveOrders,
    1000
);

setInterval(
    updateWaiterTimers,
    1000
);
document.getElementById("logoutWaiter")?.addEventListener("click",()=>{localStorage.removeItem("token");localStorage.removeItem("user");window.location.replace("/login");});

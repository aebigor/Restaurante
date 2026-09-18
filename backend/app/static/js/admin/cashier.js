const API = "/api/cashier";


let cashierData = null;

let selectedSession = null;

let selectedAccount = null;


// ==========================================================
// ELEMENTOS
// ==========================================================

const openRegisterPanel =
    document.getElementById(
        "openRegisterPanel"
    );

const registerSummary =
    document.getElementById(
        "registerSummary"
    );

const accountsPanel =
    document.getElementById(
        "accountsPanel"
    );

const accountPanel =
    document.getElementById(
        "accountPanel"
    );

const closeRegisterPanel =
    document.getElementById(
        "closeRegisterPanel"
    );

const registerStatus =
    document.getElementById(
        "registerStatus"
    );

const tablesContainer =
    document.getElementById(
        "tablesContainer"
    );

const accountTitle =
    document.getElementById(
        "accountTitle"
    );

const accountContent =
    document.getElementById(
        "accountContent"
    );

const paymentBox =
    document.getElementById(
        "paymentBox"
    );

const onlineOrdersPanel = document.getElementById("onlineOrdersPanel");
const onlineOrdersContainer = document.getElementById("onlineOrdersContainer");


// ==========================================================
// API
// ==========================================================

async function api(
    url,
    options = {}
) {

    const token =
        localStorage.getItem("token");


    const response =
        await fetch(
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

        data =
            await response.json();

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
// MONEDA
// ==========================================================

function money(value) {

    return new Intl.NumberFormat(
        "es-CO",
        {
            style: "currency",
            currency: "COP",
            maximumFractionDigits: 0
        }
    ).format(
        Number(value || 0)
    );

}


// ==========================================================
// ESCAPAR HTML
// ==========================================================

function escapeHtml(value) {

    return String(
        value ?? ""
    )
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

}


// ==========================================================
// CARGAR CAJA
// ==========================================================

async function loadCashier() {

    try {

        cashierData =
            await api(
                `${API}/summary`
            );


        if (
            !cashierData.register_open
        ) {

            showClosedRegister();

            return;

        }


        showOpenRegister();

        renderRegister(
            cashierData.register
        );

        renderTables(
            cashierData.tables
        );

        await loadOnlineOrders();

    } catch (error) {

        console.error(
            error
        );

        registerStatus.textContent =
            "Error";

        alert(
            error.message ||
            "No fue posible cargar Caja."
        );

    }

}


// ==========================================================
// CAJA CERRADA
// ==========================================================

function showClosedRegister() {

    openRegisterPanel.hidden =
        false;

    registerSummary.hidden =
        true;

    accountsPanel.hidden =
        true;

    accountPanel.hidden =
        true;

    closeRegisterPanel.hidden =
        true;


    registerStatus.textContent =
        "● CAJA CERRADA";

}


// ==========================================================
// CAJA ABIERTA
// ==========================================================

function showOpenRegister() {

    openRegisterPanel.hidden =
        true;

    registerSummary.hidden =
        false;

    accountsPanel.hidden =
        false;

    closeRegisterPanel.hidden =
        false;


    registerStatus.textContent =
        "● CAJA ABIERTA";

}


// ==========================================================
// RESUMEN
// ==========================================================

function renderRegister(
    register
) {

    document.getElementById(
        "openingValue"
    ).textContent =
        money(
            register.opening_amount
        );


    document.getElementById(
        "cashValue"
    ).textContent =
        money(
            register.cash_sales
        );


    document.getElementById(
        "cardValue"
    ).textContent =
        money(
            register.card_sales
        );


    document.getElementById(
        "transferValue"
    ).textContent =
        money(
            register.transfer_sales
        );


    document.getElementById(
        "salesValue"
    ).textContent =
        money(
            register.total_sales
        );


    document.getElementById(
        "expectedCash"
    ).textContent =
        money(
            register.expected_cash
        );

}


// ==========================================================
// MESAS
// ==========================================================

function renderTables(
    tables
) {

    if (!tables.length) {

        tablesContainer.innerHTML = `

            <div class="empty-state">

                No hay cuentas pendientes de pago.

            </div>

        `;

        return;

    }


    tablesContainer.innerHTML =
        tables.map(
            table => `

                <article
                    class="cash-table-card"
                >

                    <div>

                        <span>
                            MESA
                        </span>

                        <h3>
                            Mesa ${escapeHtml(
                                table.table_number
                            )}
                        </h3>

                        <p>
                            ${escapeHtml(
                                table.table_name
                            )}
                        </p>

                    </div>


                    <div class="cash-table-total">

                        <span>
                            Total
                        </span>

                        <strong>
                            ${money(
                                table.balance
                            )}
                        </strong>

                    </div>


                    <button
                        type="button"
                        onclick="openAccount('${table.session_id}')"
                    >
                        Ver cuenta
                    </button>

                    ${table.status === "CLEAN" ? `
                        <button type="button" class="cash-release-button" onclick="event.stopPropagation(); releaseTable('${table.session_id}')">
                            🔓 Liberar mesa
                        </button>
                    ` : table.status === "PAID" ? `
                        <span class="cash-wait-clean">⏳ Esperando que el mesero marque limpia</span>
                    ` : ""}

                </article>

            `
        ).join("");

}


// ==========================================================
// PEDIDOS ONLINE
// ==========================================================

async function loadOnlineOrders() {
    if (!onlineOrdersPanel) return;
    try {
        const orders = await api(`${API}/online-orders`);
        onlineOrdersPanel.hidden = false;
        if (!orders.length) {
            onlineOrdersContainer.innerHTML = '<div class="empty-state">No hay pedidos online pendientes.</div>';
            return;
        }
        onlineOrdersContainer.innerHTML = orders.map(order => {
            const delivery = order.order_type === "DOMICILIO";
            const items = order.items.map(item => `<div class="online-order-item"><span>${item.quantity} × ${escapeHtml(item.name)}</span><strong>${money(item.total)}</strong></div>`).join("");
            let actions = "";
            if (order.status === "PENDING_CASHIER") {
                actions = `<button class="btn-primary" type="button" onclick="confirmOnlineOrder('${order.id}')">✓ Confirmar y enviar a cocina</button>`;
            } else if (order.status === "READY" && delivery) {
                actions = `<span class="online-waiting-courier">🚚 Esperando que un domiciliario tome el pedido</span>`;
            } else if (order.status === "DELIVERED_PENDING_PAYMENT") {
                actions = `<button class="btn-pay" type="button" onclick="closeOnlinePayment('${order.id}')">💵 Registrar pago y cerrar</button>`;
            } else if (order.status === "OUT_FOR_DELIVERY") {
                actions = `<span>🛵 ${escapeHtml(order.courier_name || 'Domiciliario')} · entrega en curso</span>`;
            }
            return `<article class="online-order-card"><div class="online-order-head"><div><span>PEDIDO #${escapeHtml(order.short_id)}</span><h3>${escapeHtml(order.customer.name)}</h3><small>${delivery ? "Domicilio" : "Recoger"} · ${new Date(order.created_at).toLocaleString("es-CO")}</small></div><strong>${money(order.total)}</strong></div><div class="online-order-items">${items}</div>${delivery ? `<div class="online-delivery"><b>Dirección:</b> ${escapeHtml(order.delivery_address || "-")}<br><b>Teléfono:</b> ${escapeHtml(order.delivery_phone || "-")}</div>` : ""}${order.notes ? `<div class="online-delivery"><b>Nota:</b> ${escapeHtml(order.notes)}</div>` : ""}<div class="online-order-footer"><span class="status-pill">${escapeHtml(order.status)}</span>${actions}</div></article>`;
        }).join("");
    } catch (error) {
        console.error(error);
    }
}

async function confirmOnlineOrder(orderId) {
    if (!confirm("¿Confirmar este pedido y enviarlo a cocina?")) return;
    try { await api(`${API}/online-orders/${encodeURIComponent(orderId)}/confirm`, {method:"PATCH"}); await loadOnlineOrders(); }
    catch(error){ alert(error.message); }
}

async function dispatchOnlineOrder(orderId) {
    try { await api(`${API}/online-orders/${encodeURIComponent(orderId)}/dispatch`, {method:"PATCH"}); await loadOnlineOrders(); } catch(error){ alert(error.message); }
}

async function closeOnlinePayment(orderId) {
    const method = prompt("Método de pago: CASH (efectivo), TRANSFER (Nequi/transferencia) o CARD", "CASH");
    if (!method) return;
    const normalized = method.trim().toUpperCase();
    if (!["CASH","TRANSFER","CARD"].includes(normalized)) { alert("Método inválido."); return; }
    try { await api(`${API}/online-orders/${encodeURIComponent(orderId)}/close-payment`, {method:"PATCH", body:JSON.stringify({payment_method:normalized})}); await loadOnlineOrders(); } catch(error){ alert(error.message); }
}

async function deliverOnlineOrder(orderId) {
    alert("La entrega la confirma el domiciliario con el código del cliente. Luego Caja registra el pago y cierra el pedido.");
}

async function loadCourierLocations(){
    const box=document.getElementById('courierLocations'); if(!box) return;
    try{const rows=await api('/api/delivery/locations'); box.innerHTML=rows.length?rows.map(x=>`<article class="courier-location-card"><b>🚚 ${escapeHtml(x.name)}</b><span>${x.order_id?'Pedido activo #'+x.order_id.slice(0,8).toUpperCase():'Sin pedido activo'}</span><small>${x.latitude!=null?`📍 ${Number(x.latitude).toFixed(6)}, ${Number(x.longitude).toFixed(6)}`:'Sin ubicación reportada'}${x.recorded_at?' · '+new Date(x.recorded_at).toLocaleTimeString('es-CO'):''}</small></article>`).join(''):'No hay domiciliarios registrados.'}catch(e){box.textContent=e.message}}



// ==========================================================
// ABRIR CAJA
// ==========================================================

document
    .getElementById(
        "openRegisterButton"
    )
    ?.addEventListener(
        "click",
        async () => {

            const value =
                Number(
                    document.getElementById(
                        "openingAmount"
                    ).value || 0
                );


            if (value < 0) {

                alert(
                    "La base inicial no puede ser negativa."
                );

                return;

            }


            try {

                await api(
                    `${API}/register/open`,
                    {
                        method: "POST",

                        body: JSON.stringify({
                            opening_amount: value
                        })
                    }
                );


                await loadCashier();


            } catch (error) {

                alert(
                    error.message
                );

            }

        }
    );


// ==========================================================
// VER CUENTA
// ==========================================================

async function openAccount(
    sessionId
) {

    selectedSession =
        sessionId;


    try {

        selectedAccount =
            await api(
                `${API}/sessions/${sessionId}/account`
            );


        renderAccount(
            selectedAccount
        );


        accountPanel.hidden =
            false;


        accountPanel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        alert(
            error.message
        );

    }

}


// ==========================================================
// RENDER CUENTA
// ==========================================================

function renderAccount(
    account
) {

    accountTitle.textContent =
        `Mesa ${account.table.number}`;


    let html = "";


    for (
        const order of account.orders
    ) {

        html += `

            <div class="account-order">

                <div class="account-order-head">

                    <strong>
                        Pedido
                    </strong>

                    <span>
                        ${escapeHtml(
                            order.status
                        )}
                    </span>

                </div>

        `;


        for (
            const item of order.items
        ) {

            html += `

                <div class="account-item">

                    <div>

                        <strong>
                            ${escapeHtml(
                                item.name
                            )}
                        </strong>

                        <span>
                            ${item.quantity} ×
                            ${money(
                                item.unit_price
                            )}
                        </span>

                    </div>

                    <strong>
                        ${money(
                            item.total
                        )}
                    </strong>

                </div>

            `;

        }


        html += `
            </div>
        `;

    }


    html += `

        <div class="account-total">

            <span>
                TOTAL
            </span>

            <strong>
                ${money(
                    account.balance
                )}
            </strong>

        </div>

    `;


    accountContent.innerHTML =
        html;


    document.getElementById(
        "paymentTotal"
    ).textContent =
        money(
            account.balance
        );


    document.getElementById(
        "receivedAmount"
    ).value =
        account.balance;


    paymentBox.hidden =
        account.balance <= 0;


    updateChange();

}


// ==========================================================
// CALCULAR CAMBIO
// ==========================================================

function updateChange() {

    if (!selectedAccount) {
        return;
    }


    const method =
        document.getElementById(
            "paymentMethod"
        ).value;


    const received =
        Number(
            document.getElementById(
                "receivedAmount"
            ).value || 0
        );


    const total =
        Number(
            selectedAccount.balance || 0
        );


    let change = 0;


    if (
        method === "CASH"
    ) {

        change =
            Math.max(
                0,
                received - total
            );

    }


    document.getElementById(
        "changeValue"
    ).textContent =
        money(change);

}


// ==========================================================
// EVENTOS DE PAGO
// ==========================================================

document
    .getElementById(
        "paymentMethod"
    )
    ?.addEventListener(
        "change",
        updateChange
    );


document
    .getElementById(
        "receivedAmount"
    )
    ?.addEventListener(
        "input",
        updateChange
    );


// ==========================================================
// COBRAR
// ==========================================================

document
    .getElementById(
        "payButton"
    )
    ?.addEventListener(
        "click",
        async () => {

            if (!selectedAccount) {
                return;
            }


            const method =
                document.getElementById(
                    "paymentMethod"
                ).value;


            const received =
                Number(
                    document.getElementById(
                        "receivedAmount"
                    ).value || 0
                );


            const reference =
                document.getElementById(
                    "paymentReference"
                ).value.trim();


            const total =
                Number(
                    selectedAccount.balance
                );


            if (
                method === "CASH" &&
                received < total
            ) {

                alert(
                    "El efectivo recibido es menor al total."
                );

                return;

            }


            const button =
                document.getElementById(
                    "payButton"
                );


            button.disabled = true;


            try {

                const result =
                    await api(
                        `${API}/payments`,
                        {

                            method: "POST",

                            body:
                                JSON.stringify({

                                    session_id:
                                        selectedSession,

                                    method:

                                        method,

                                    received_amount:

                                        received,

                                    reference:

                                        reference ||
                                        null

                                })

                        }
                    );


                alert(
                    `Cuenta cobrada correctamente.\n\n` +
                    `Total: ${money(result.total)}\n` +
                    `Cambio: ${money(result.change_amount)}`
                );


                selectedAccount =
                    null;

                selectedSession =
                    null;


                accountPanel.hidden =
                    true;


                await loadCashier();


            } catch (error) {

                alert(
                    error.message
                );

            } finally {

                button.disabled =
                    false;

            }

        }
    );


// ==========================================================
// ACTUALIZAR
// ==========================================================

document
    .getElementById(
        "refreshCashier"
    )
    ?.addEventListener(
        "click",
        loadCashier
    );

document.getElementById("refreshOnlineOrders")?.addEventListener("click", loadOnlineOrders);
setInterval(loadCourierLocations, 5000);
setTimeout(loadCourierLocations, 1000);


// ==========================================================
// LIBERAR MESA - SOLO CAJA
// ==========================================================

async function releaseTable(sessionId) {
    if (!sessionId) return;

    if (!confirm("¿Confirmas que la mesa está limpia y deseas liberarla?")) return;

    try {
        await api(`${API}/sessions/${encodeURIComponent(sessionId)}/release`, { method: "PATCH" });
        selectedSession = null;
        selectedAccount = null;
        if (accountPanel) accountPanel.hidden = true;
        alert("Mesa liberada correctamente.");
        await loadCashier();
    } catch (error) {
        alert(error.message || "No se pudo liberar la mesa.");
    }
}


// ==========================================================
// CERRAR CAJA
// ==========================================================

document
    .getElementById(
        "closeRegisterButton"
    )
    ?.addEventListener(
        "click",
        async () => {

            const expected =
                Number(
                    cashierData
                    ?.register
                    ?.expected_cash || 0
                );


            const closing =
                Number(
                    document.getElementById(
                        "closingAmount"
                    ).value || 0
                );


            if (closing < 0) {

                alert(
                    "El efectivo contado no puede ser negativo."
                );

                return;

            }


            const confirmClose =
                confirm(
                    `Efectivo esperado: ${money(expected)}\n` +
                    `Efectivo contado: ${money(closing)}\n\n` +
                    `¿Deseas cerrar la caja?`
                );


            if (!confirmClose) {
                return;
            }


            try {

                const result =
                    await api(
                        `${API}/register/close`,
                        {

                            method: "POST",

                            body:
                                JSON.stringify({

                                    closing_amount:
                                        closing

                                })

                        }
                    );


                alert(
                    `Caja cerrada.\n\n` +
                    `Esperado: ${money(result.expected_cash)}\n` +
                    `Contado: ${money(result.closing_amount)}\n` +
                    `Diferencia: ${money(result.difference)}`
                );


                document.getElementById(
                    "closingAmount"
                ).value = "";


                await loadCashier();


            } catch (error) {

                alert(
                    error.message
                );

            }

        }
    );


// ==========================================================
// INICIO
// ==========================================================

loadCashier();


// ==========================================================
// ACTUALIZACIÓN AUTOMÁTICA DE CAJA
// ==========================================================

setInterval(
    loadCashier,
    30000
);
const API = "/api/cashier";


let cashierData = null;

let selectedSession = null;

let selectedAccount = null;
let prepaymentCodeVerified = false;


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

    const withdrawalsValue = document.getElementById("withdrawalsValue");
    if (withdrawalsValue) {
        withdrawalsValue.textContent = money(register.withdrawals || 0);
    }

}


function parseDate(value) {
    if (!value) return null;
    const text = String(value);
    const d = new Date(text.endsWith("Z") || text.includes("+") ? text : `${text}Z`);
    return Number.isNaN(d.getTime()) ? null : d;
}

function formatElapsed(value) {
    const d = parseDate(value);
    if (!d) return "00:00";
    const seconds = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

function updateCashTimers() {
    document.querySelectorAll("[data-cash-timer]").forEach(el => {
        el.textContent = formatElapsed(el.dataset.cashTimer);
    });
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
                        ${table.payment_pending ? `<div class="cash-pending-badge">💳 PAGO ANTICIPADO · <span data-cash-timer="${escapeHtml(table.payment_pending_since || table.opened_at || '')}">${formatElapsed(table.payment_pending_since || table.opened_at)}</span></div>` : ''}

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

                    ${["CLEAN", "PAID"].includes(table.status) ? `
                        <button type="button" class="cash-release-button" onclick="event.stopPropagation(); releaseTable('${table.session_id}')">
                            🔓 Liberar mesa
                        </button>
                        ${table.status === "PAID" ? '<span class="cash-wait-clean">✓ Pagada · Caja puede cerrar la mesa</span>' : ''}
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
                const proofHtml = (order.payment_proofs || []).map(p => `<a class="cash-proof-thumb ${p.status === 'APPROVED' ? 'approved' : p.status === 'REJECTED' ? 'rejected' : ''}" href="${escapeHtml(p.file_url)}" target="_blank" rel="noopener"><img src="${escapeHtml(p.file_url)}" alt="Comprobante"><span>${escapeHtml(p.payment_method || 'TRANSFER')} · ${escapeHtml(p.status)}</span></a>`).join("");
                const hasPending = (order.payment_proofs || []).some(p => p.status === 'PENDING');
                const proofActions = (order.payment_proofs || []).filter(p => p.status === 'PENDING').map(p => `<span class="proof-review-actions"><button type="button" class="proof-approve" onclick="reviewDeliveryProof('${p.id}','APPROVED')">✓ Aprobar</button><button type="button" class="proof-reject" onclick="reviewDeliveryProof('${p.id}','REJECTED')">Rechazar</button></span>`).join("");
                actions = `<div class="delivery-close-actions"><span>🛵 ${escapeHtml(order.courier_name || 'Domiciliario')} · entrega validada</span><div class="cash-delivery-payment-methods"><button type="button" onclick="setDeliveryPayment('${order.id}','CASH')">💵 Efectivo</button><button type="button" onclick="setDeliveryPayment('${order.id}','TRANSFER_NEQUI')">Nequi</button><button type="button" onclick="setDeliveryPayment('${order.id}','TRANSFER_BANCOLOMBIA')">Bancolombia</button><button type="button" onclick="setDeliveryPayment('${order.id}','TRANSFER_LLAVES')">Llaves</button><button type="button" onclick="setDeliveryPayment('${order.id}','CARD')">💳 Tarjeta</button></div>${proofHtml ? `<div class="cash-proofs">${proofHtml}</div>` : '<small class="proof-missing">Sin comprobante transferido todavía.</small>'}${hasPending ? `<div>${proofActions}</div>` : ''}<button class="btn-pay" type="button" onclick="closeOnlinePayment('${order.id}')">✅ Registrar pago y cerrar venta</button><button class="btn-chat-delivery" type="button" onclick="openDeliveryChat('${order.id}','${escapeHtml(order.courier_name || 'Domiciliario')}')">💬 Abrir chat con domiciliario</button></div>`;
            } else if (order.status === "OUT_FOR_DELIVERY") {
                actions = `<span>🛵 ${escapeHtml(order.courier_name || 'Domiciliario')} · entrega en curso</span><button class="btn-chat-delivery" type="button" onclick="openDeliveryChat('${order.id}','${escapeHtml(order.courier_name || 'Domiciliario')}')">💬 Chat</button>`;
            }
            return `<article class="online-order-card"><div class="online-order-head"><div><span>PEDIDO #${escapeHtml(order.short_id)}</span><h3>${escapeHtml(order.customer.name)}</h3><small>${delivery ? "Domicilio" : "Recoger"} · ${new Date(order.created_at).toLocaleString("es-CO")}</small></div><strong>${money(order.total)}</strong></div><div class="online-order-items">${items}</div>${delivery ? `<div class="online-delivery"><b>Dirección:</b> ${escapeHtml(order.delivery_address || "-")}<br><b>Teléfono:</b> ${escapeHtml(order.delivery_phone || "-")}<br><b>Domiciliario:</b> ${escapeHtml(order.courier_name || "Sin asignar")}</div>` : ""}${order.notes ? `<div class="online-delivery"><b>Nota:</b> ${escapeHtml(order.notes)}</div>` : ""}<div class="online-order-footer"><span class="status-pill">${escapeHtml(order.status)}</span>${actions}</div></article>`;
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

async function setDeliveryPayment(orderId, method) {
    try {
        const response = await api(`/api/delivery/orders/${encodeURIComponent(orderId)}/payment-method`, {method:"PATCH", body:JSON.stringify({payment_method:method})});
        await loadOnlineOrders();
        await openDeliveryChat(orderId, "Domiciliario", false);
    } catch(error) { alert(error.message); }
}

async function closeOnlinePayment(orderId) {
    const current = (await api(`${API}/online-orders`)).find(x => x.id === orderId);
    const suggested = current?.payment_method || "CASH";
    const method = prompt("Método: CASH, CARD, TRANSFER_NEQUI, TRANSFER_BANCOLOMBIA o TRANSFER_LLAVES", suggested);
    if (!method) return;
    const normalized = method.trim().toUpperCase().replace(/\s+/g,"_");
    const aliases = {NEQUI:"TRANSFER_NEQUI",BANCOLOMBIA:"TRANSFER_BANCOLOMBIA",LLAVES:"TRANSFER_LLAVES",LLAVE:"TRANSFER_LLAVES",TRANSFER:"TRANSFER"};
    const finalMethod = aliases[normalized] || normalized;
    if (!["CASH","TRANSFER","CARD","TRANSFER_NEQUI","TRANSFER_BANCOLOMBIA","TRANSFER_LLAVES"].includes(finalMethod)) { alert("Método inválido."); return; }
    try { await api(`${API}/online-orders/${encodeURIComponent(orderId)}/close-payment`, {method:"PATCH", body:JSON.stringify({payment_method:finalMethod})}); await loadOnlineOrders(); }
    catch(error){ alert(error.message); }
}

async function reviewDeliveryProof(proofId, status) {
    const note = status === 'REJECTED' ? (prompt('Motivo del rechazo (opcional):') || '') : '';
    try { await api(`/api/delivery/payment-proofs/${encodeURIComponent(proofId)}/review`, {method:'PATCH', body:JSON.stringify({status, note})}); await loadOnlineOrders(); } catch(error){ alert(error.message); }
}

let deliveryChatOrderId = null;
async function openDeliveryChat(orderId, courierName, refresh=true) {
    deliveryChatOrderId = orderId;
    const panel = document.getElementById('deliveryChatPanel');
    if(panel){ panel.hidden=false; const who=document.getElementById('deliveryChatTitle'); if(who)who.textContent=`Soporte · ${courierName||'Domiciliario'} · Pedido #${String(orderId).slice(0,8).toUpperCase()}`; }
    await loadDeliveryChat();
    if(refresh) document.getElementById('deliveryChatPanel')?.scrollIntoView({behavior:'smooth',block:'nearest'});
}
async function loadDeliveryChat(){
    if(!deliveryChatOrderId) return;
    const box=document.getElementById('deliveryChatMessages'); if(!box)return;
    try{const rows=await api(`/api/delivery/messages?order_id=${encodeURIComponent(deliveryChatOrderId)}`);box.innerHTML=rows.length?rows.map(m=>`<div class="cash-chat-message"><b>${escapeHtml(m.sender)}</b><small>${new Date(m.created_at).toLocaleString('es-CO')}</small><p>${escapeHtml(m.message)}</p></div>`).join(''):'<p>No hay mensajes todavía.</p>';box.scrollTop=box.scrollHeight;}catch(e){box.textContent=e.message;}
}

async function loadCourierLocations(){
    const box=document.getElementById('courierLocations'); if(!box) return;
    try{const rows=await api('/api/delivery/locations'); box.innerHTML=rows.length?rows.map(x=>`<article class="courier-location-card ${x.online?'is-online':'is-offline'}"><div><b>🚚 ${escapeHtml(x.name)}</b><span class="courier-presence">${x.online?'🟢 EN LÍNEA':'⚪ SIN CONEXIÓN'}</span></div><span>${x.order_id?`Pedido activo #${x.order_short_id||x.order_id.slice(0,8).toUpperCase()}`:'Sin pedido activo'}</span>${x.destination?`<small>📍 ${escapeHtml(x.destination)}</small>`:''}<small>${x.latitude!=null?`GPS ${Number(x.latitude).toFixed(6)}, ${Number(x.longitude).toFixed(6)}`:'Sin ubicación reportada'}${x.recorded_at?' · '+new Date(x.recorded_at).toLocaleTimeString('es-CO'):''}</small></article>`).join(''):'No hay domiciliarios registrados.'}catch(e){box.textContent=e.message}}

document.getElementById('deliveryChatForm')?.addEventListener('submit', async e=>{
    e.preventDefault(); const input=document.getElementById('deliveryChatInput'); const value=input?.value.trim(); if(!value||!deliveryChatOrderId)return;
    try{await api('/api/delivery/messages',{method:'POST',body:JSON.stringify({order_id:deliveryChatOrderId,message:value})});input.value='';await loadDeliveryChat();}catch(err){alert(err.message)}
});
document.getElementById('deliveryChatClose')?.addEventListener('click',()=>{deliveryChatOrderId=null;const p=document.getElementById('deliveryChatPanel');if(p)p.hidden=true;});

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

    prepaymentCodeVerified = !Boolean(account.table?.prepayment_required);
    const codeBox = document.getElementById("prepaymentCodeBox");
    const codeInput = document.getElementById("prepaymentCode");
    const codeStatus = document.getElementById("prepaymentCodeStatus");
    const payButton = document.getElementById("payButton");
    if (codeBox) codeBox.hidden = !Boolean(account.table?.prepayment_required);
    if (codeInput) codeInput.value = "";
    if (codeStatus) codeStatus.textContent = account.table?.prepayment_required ? "Pendiente de validar." : "";
    if (payButton) payButton.disabled = Boolean(account.table?.prepayment_required);


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


    const changeElement = document.getElementById("changeValue");
    const receivedElement = document.getElementById("receivedAmount");
    if (method === "CASH" && received < total) {
        changeElement.textContent = `Faltan ${money(total - received)}`;
        changeElement.closest(".change-box")?.classList.add("change-short");
    } else {
        changeElement.textContent = money(change);
        changeElement.closest(".change-box")?.classList.remove("change-short");
    }

}


// ==========================================================
// VALIDAR CÓDIGO DE COMANDA DE PAGO ANTICIPADO
// ==========================================================

document.getElementById("verifyPrepaymentCode")?.addEventListener("click", async () => {
    if (!selectedAccount || !selectedAccount.table?.prepayment_required) return;
    const input = document.getElementById("prepaymentCode");
    const status = document.getElementById("prepaymentCodeStatus");
    const button = document.getElementById("verifyPrepaymentCode");
    const code = String(input?.value || "").trim();

    if (!/^\d{6}$/.test(code)) {
        if (status) status.textContent = "El código debe tener 6 dígitos.";
        return;
    }

    button.disabled = true;
    if (status) status.textContent = "Validando…";
    try {
        const result = await api(`${API}/payments/prepayment/verify`, {
            method: "POST",
            body: JSON.stringify({ session_id: selectedSession, confirmation_code: code })
        });
        prepaymentCodeVerified = true;
        if (status) status.textContent = `✅ Código válido para Mesa ${result.table_number}. Ahora puedes cobrar.`;
        const payButton = document.getElementById("payButton");
        if (payButton) payButton.disabled = false;
    } catch (error) {
        prepaymentCodeVerified = false;
        if (status) status.textContent = `❌ ${error.message || "Código inválido."}`;
        const payButton = document.getElementById("payButton");
        if (payButton) payButton.disabled = true;
    } finally {
        button.disabled = false;
    }
});

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

            if (selectedAccount.table?.prepayment_required && !prepaymentCodeVerified) {
                alert("Primero debes validar el código de la comanda.");
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
                        `${API}/${selectedAccount?.table?.prepayment_required ? "payments/prepayment" : "payments"}`,
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
                                        null,

                                    confirmation_code:
                                        selectedAccount?.table?.prepayment_required
                                            ? document.getElementById("prepaymentCode")?.value.trim()
                                            : null

                                })

                        }
                    );


                alert(
                    `${selectedAccount?.table?.prepayment_required ? "Pago anticipado registrado. La comanda fue enviada a cocina." : "Cuenta cobrada correctamente."}\n\n` +
                    `Total: ${money(result.total)}\n` +
                    `Cambio: ${money(result.change_amount)}`
                );


                selectedAccount =
                    null;

                selectedSession =
                    null;
                prepaymentCodeVerified = false;


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
setInterval(() => loadCashier().catch(console.error), 3000);
setInterval(updateCashTimers, 1000);


// ==========================================================
// LIBERAR MESA - SOLO CAJA
// ==========================================================

async function releaseTable(sessionId) {
    if (!sessionId) return;

    if (!confirm("¿Confirmas que el cliente ya pagó y deseas liberar la mesa?\n\nAl liberar desde Caja, la mesa y sus comandas se cerrarán aunque el mesero haya olvidado marcar la entrega.")) return;

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
// RETIRO DE DINERO
// ==========================================================

const withdrawalModal = document.getElementById("withdrawalModal");
const withdrawalAvailable = document.getElementById("withdrawalAvailable");
const withdrawalAmount = document.getElementById("withdrawalAmount");
const withdrawalRecipientName = document.getElementById("withdrawalRecipientName");
const withdrawalRecipientDocument = document.getElementById("withdrawalRecipientDocument");
const withdrawalReason = document.getElementById("withdrawalReason");
const withdrawalError = document.getElementById("withdrawalError");

function openWithdrawalModal() {
    const available = Number(cashierData?.register?.expected_cash || 0);
    withdrawalAvailable.textContent = money(available);
    withdrawalAmount.value = "";
    withdrawalRecipientName.value = "";
    withdrawalRecipientDocument.value = "";
    withdrawalReason.value = "Retiro de efectivo";
    withdrawalError.hidden = true;
    withdrawalError.textContent = "";
    withdrawalModal.hidden = false;
    setTimeout(() => withdrawalAmount?.focus(), 50);
}

function closeWithdrawalModal() {
    withdrawalModal.hidden = true;
}

async function confirmWithdrawal() {
    const amount = Number(withdrawalAmount.value || 0);
    const recipientName = withdrawalRecipientName.value.trim();
    const recipientDocument = withdrawalRecipientDocument.value.trim();
    const reason = withdrawalReason.value.trim();
    const available = Number(cashierData?.register?.expected_cash || 0);

    if (amount <= 0) return showWithdrawalError("Ingresa un valor de retiro mayor que cero.");
    if (amount > available) return showWithdrawalError(`No puedes retirar ${money(amount)}. El efectivo disponible es ${money(available)}.`);
    if (recipientName.length < 2) return showWithdrawalError("Ingresa el nombre completo de quien recibe el dinero.");
    if (recipientDocument.length < 4) return showWithdrawalError("Ingresa la cédula o documento de quien recibe el dinero.");

    const button = document.getElementById("confirmWithdrawal");
    button.disabled = true;
    try {
        const result = await api(`${API}/register/withdrawal`, {
            method: "POST",
            body: JSON.stringify({
                amount,
                recipient_name: recipientName,
                recipient_document: recipientDocument,
                reason: reason || "Retiro de efectivo"
            })
        });
        closeWithdrawalModal();
        alert(`Retiro registrado correctamente.\n\nRetirado: ${money(result.amount)}\nEfectivo restante esperado: ${money(result.cash_available)}`);
        await loadCashier();
    } catch (error) {
        showWithdrawalError(error.message || "No se pudo registrar el retiro.");
    } finally {
        button.disabled = false;
    }
}

function showWithdrawalError(message) {
    withdrawalError.textContent = message;
    withdrawalError.hidden = false;
}

document.getElementById("withdrawRegisterButton")?.addEventListener("click", openWithdrawalModal);
document.getElementById("closeWithdrawalModal")?.addEventListener("click", closeWithdrawalModal);
document.getElementById("cancelWithdrawal")?.addEventListener("click", closeWithdrawalModal);
document.getElementById("confirmWithdrawal")?.addEventListener("click", confirmWithdrawal);
withdrawalModal?.addEventListener("click", event => {
    if (event.target === withdrawalModal) closeWithdrawalModal();
});

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
setInterval(loadDeliveryChat, 5000);
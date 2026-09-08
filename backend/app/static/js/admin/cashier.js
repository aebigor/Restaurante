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
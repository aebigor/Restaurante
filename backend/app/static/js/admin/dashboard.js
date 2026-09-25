const adminToken = localStorage.getItem("token");

function money(value) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0
    }).format(Number(value || 0));
}

function escapeAdmin(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString("es-CO", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit"
    });
}

function registerRow(register, index, closed = false) {
    const difference = Number(register.difference || 0);
    const differenceClass = difference === 0 ? "difference-ok" : difference > 0 ? "difference-positive" : "difference-negative";
    const differenceText = difference === 0 ? "Cuadra" : difference > 0 ? `Sobra ${money(difference)}` : `Falta ${money(Math.abs(difference))}`;

    if (!closed) {
        return `
            <div class="register-row">
                <div class="register-number">${index + 1}</div>
                <div class="register-info">
                    <strong>Caja ${index + 1}</strong>
                    <span>${escapeAdmin(register.opened_by)} · abierta ${formatDateTime(register.opened_at)}</span>
                </div>
                <div class="register-sales">${money(register.total_sales)}</div>
                <div class="register-opened"><span class="open-dot"></span> ABIERTA</div>
            </div>
        `;
    }

    return `
        <div class="closed-register-card">
            <div class="closed-register-head">
                <div>
                    <strong>Caja ${index + 1}</strong>
                    <span>${escapeAdmin(register.opened_by)}</span>
                </div>
                <span class="closed-badge">CERRADA</span>
            </div>
            <div class="closed-register-grid">
                <div><span>Inicio</span><strong>${money(register.opening_amount)}</strong></div>
                <div><span>Ventas</span><strong>${money(register.total_sales)}</strong></div>
                <div><span>Efectivo</span><strong>${money(register.cash_sales)}</strong></div>
                <div><span>Tarjeta</span><strong>${money(register.card_sales)}</strong></div>
                <div><span>Transferencias</span><strong>${money(register.transfer_sales)}</strong></div>
                <div><span>Efectivo esperado</span><strong>${money(register.expected_cash)}</strong></div>
                <div><span>Efectivo contado</span><strong>${money(register.closing_amount)}</strong></div>
                <div class="${differenceClass}"><span>Diferencia</span><strong>${differenceText}</strong></div>
            </div>
            <div class="closed-register-footer">
                <span>🧾 ${register.payment_count || 0} cobros</span>
                <span>Cierre: ${formatDateTime(register.closed_at)}</span>
            </div>
        </div>
    `;
}

function formatElapsed(value) {
    if (!value) return "00:00";
    const text = String(value);
    const d = new Date(text.endsWith("Z") || text.includes("+") ? text : `${text}Z`);
    if (Number.isNaN(d.getTime())) return "00:00";
    const seconds = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

function renderPendingPrepayments(rows) {
    const list = document.getElementById("pendingPrepaymentList");
    const badge = document.getElementById("pendingPrepaymentBadge");
    if (!list || !badge) return;
    badge.textContent = `${rows.length} pendientes`;
    if (!rows.length) {
        list.innerHTML = `<div class="empty-registers"><strong>No hay mesas esperando pago</strong><span>Cuando un mesero registre una mesa de pago anticipado aparecerá aquí.</span></div>`;
        return;
    }
    list.innerHTML = rows.map(row => `
        <article class="pending-payment-row">
            <div class="pending-payment-main"><div class="pending-table-number">${row.table_number}</div><div><strong>${escapeAdmin(row.table_name || `Mesa ${row.table_number}`)}</strong><span>${escapeAdmin(row.zone || "Salón")}</span></div></div>
            <div class="pending-payment-time">⏱ <b data-admin-pending-timer="${row.created_at}">${formatElapsed(row.created_at)}</b></div>
            <div class="pending-payment-total">${money(row.balance)}</div>
            <span class="pending-payment-badge">💳 PENDIENTE</span>
        </article>`).join("");
}

function updateAdminPendingTimers() {
    document.querySelectorAll("[data-admin-pending-timer]").forEach(el => el.textContent = formatElapsed(el.dataset.adminPendingTimer));
}

async function loadAdminDashboard() {
    const response = await fetch("/api/cashier/admin-summary", {
        headers: { Authorization: `Bearer ${adminToken}` }
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "No se pudo cargar el resumen administrativo.");
    }

    const data = await response.json();

    document.getElementById("salesToday").textContent = money(data.sales_today);
    document.getElementById("earningsTotal").textContent = money(data.sales_today);
    document.getElementById("ordersToday").textContent = data.orders_today || 0;
    document.getElementById("salesCountToday").textContent = data.payments_today || 0;
    document.getElementById("openRegisters").textContent = data.open_registers || 0;


    document.getElementById("cashToday").textContent = money(data.cash_today);
    document.getElementById("cardToday").textContent = money(data.card_today);
    document.getElementById("transferToday").textContent = money(data.transfer_today);

    const date = data.date ? new Date(`${data.date}T00:00:00`) : new Date();
    document.getElementById("adminDate").textContent = date.toLocaleDateString("es-CO", {
        day: "2-digit", month: "long", year: "numeric"
    });

    const activeList = document.getElementById("registerStatusList");
    if (!data.registers?.length) {
        activeList.innerHTML = `<div class="empty-registers"><strong>No hay cajas abiertas</strong><span>Cuando un cajero abra un turno aparecerá aquí.</span></div>`;
    } else {
        activeList.innerHTML = data.registers.map((r, i) => registerRow(r, i)).join("");
    }

    renderPendingPrepayments(data.pending_prepayments || []);

    const closedList = document.getElementById("closedRegisterList");
    document.getElementById("closedRegistersBadge").textContent = `${data.closed_registers_today || 0} cerradas`;
    if (!data.closed_registers?.length) {
        closedList.innerHTML = `<div class="empty-registers"><strong>Aún no hay cajas cerradas hoy</strong><span>Al cerrar una caja, aquí aparecerá su arqueo completo.</span></div>`;
    } else {
        closedList.innerHTML = data.closed_registers.map((r, i) => registerRow(r, i, true)).join("");
    }
}

loadAdminDashboard().catch(error => {
    console.error(error);
    document.getElementById("registerStatusList").innerHTML = `<div class="empty-registers">No fue posible consultar el estado de las cajas.</div>`;
    document.getElementById("closedRegisterList").innerHTML = `<div class="empty-registers">No fue posible consultar los cierres.</div>`;
});

setInterval(() => {
    loadAdminDashboard().catch(console.error);
}, 3000);
setInterval(updateAdminPendingTimers, 1000);

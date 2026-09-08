const token = localStorage.getItem("token");
const money = value => new Intl.NumberFormat("es-CO", {style:"currency", currency:"COP", maximumFractionDigits:0}).format(Number(value || 0));

const escapeHtml = value => String(value ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#039;");

const dateTime = value => {
    if (!value) return "—";
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString("es-CO", {day:"2-digit", month:"2-digit", year:"numeric", hour:"2-digit", minute:"2-digit"});
};

function renderOpen(register, index) {
    return `
        <div class="control-register">
            <div class="control-register-number">${index + 1}</div>
            <div class="control-register-info"><strong>Caja ${index + 1}</strong><span>Cajero: ${escapeHtml(register.opened_by)}</span><small>Abierta: ${dateTime(register.opened_at)}</small></div>
            <div class="control-register-sales">${money(register.total_sales)}</div>
            <div class="control-register-status">ABIERTA</div>
        </div>`;
}

function renderClosed(register, index) {
    const diff = Number(register.difference || 0);
    const diffText = diff === 0 ? "Cuadra" : diff > 0 ? `Sobra ${money(diff)}` : `Falta ${money(Math.abs(diff))}`;
    const diffClass = diff === 0 ? "ok" : diff > 0 ? "positive" : "negative";
    return `
        <div class="control-closed-register">
            <div class="control-closed-head"><div><strong>Caja ${index + 1}</strong><span>${escapeHtml(register.opened_by)}</span></div><b>CERRADA</b></div>
            <div class="control-closed-grid">
                <div><span>Base</span><strong>${money(register.opening_amount)}</strong></div>
                <div><span>Ventas</span><strong>${money(register.total_sales)}</strong></div>
                <div><span>Efectivo</span><strong>${money(register.cash_sales)}</strong></div>
                <div><span>Tarjeta</span><strong>${money(register.card_sales)}</strong></div>
                <div><span>Transferencias</span><strong>${money(register.transfer_sales)}</strong></div>
                <div><span>Esperado</span><strong>${money(register.expected_cash)}</strong></div>
                <div><span>Contado</span><strong>${money(register.closing_amount)}</strong></div>
                <div class="${diffClass}"><span>Diferencia</span><strong>${diffText}</strong></div>
            </div>
            <small class="control-closed-time">${register.payment_count || 0} cobros · cierre ${dateTime(register.closed_at)}</small>
        </div>`;
}

async function loadCashControl(){
    const response = await fetch("/api/cashier/admin-summary", {headers:{Authorization:`Bearer ${token}`}});
    const data = await response.json().catch(() => ({}));
    if(!response.ok) throw new Error(data.detail || "No se pudo cargar el control de cajas.");

    document.getElementById("controlOpenCount").textContent = data.open_registers || 0;
    document.getElementById("controlSales").textContent = money(data.sales_today);
    document.getElementById("controlClosedCount").textContent = data.closed_registers_today || 0;

    const list = document.getElementById("controlRegisterList");
    list.innerHTML = data.registers?.length
        ? data.registers.map(renderOpen).join("")
        : `<div class="control-empty"><strong>No hay cajas abiertas en este momento.</strong><br>Los turnos que abra un cajero aparecerán aquí.</div>`;

    const closedList = document.getElementById("controlClosedRegisterList");
    closedList.innerHTML = data.closed_registers?.length
        ? data.closed_registers.map(renderClosed).join("")
        : `<div class="control-empty"><strong>No hay cajas cerradas hoy.</strong><br>El arqueo aparecerá aquí cuando termine un turno.</div>`;
}

document.getElementById("refreshAdminCash")?.addEventListener("click", loadCashControl);
loadCashControl().catch(err=>{console.error(err);document.getElementById("controlRegisterList").textContent="No fue posible consultar las cajas.";document.getElementById("controlClosedRegisterList").textContent="No fue posible consultar los cierres.";});
setInterval(() => loadCashControl().catch(console.error), 15000);

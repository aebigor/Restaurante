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
            <div class="control-closed-footer">
                <div class="control-edit-status">${register.closing_amount_edit_count > 0
                    ? `✓ Corrección administrativa usada${register.closing_amount_edited_at ? ` · ${dateTime(register.closing_amount_edited_at)}` : ""}${register.closing_amount_edited_by ? ` · ${escapeHtml(register.closing_amount_edited_by)}` : ""}${register.closing_amount_edit_reason ? `<br><span>Motivo: ${escapeHtml(register.closing_amount_edit_reason)}</span>` : ""}`
                    : "✓ Sin correcciones administrativas"}</div>
                ${register.closing_amount_edit_allowed
                    ? `<button class="control-edit-button" type="button" data-edit-register="${escapeHtml(register.id)}" data-current-closing="${Number(register.closing_amount || 0)}">✏️ Corregir efectivo contado</button>`
                    : ""}
            </div>
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

    const movementList = document.getElementById("controlMovementList");
    const movements = data.movements_today || [];
    movementList.innerHTML = movements.length
        ? movements.map(m => `
            <div class="control-movement">
                <div><span class="movement-type">${escapeHtml(m.type === "WITHDRAWAL" ? "RETIRO" : m.type)}</span><strong>${money(m.amount)}</strong><span>${dateTime(m.created_at)}</span></div>
                <div><span>RECIBE</span><strong>${escapeHtml(m.recipient_name)}</strong><span>CC: ${escapeHtml(m.recipient_document)}</span></div>
                <div><span>CAJERO</span><strong>${escapeHtml(m.cashier_name)}</strong><span>Motivo: ${escapeHtml(m.reason || "—")}</span></div>
                <div><span>CAJA</span><strong>${escapeHtml(m.register_id.slice(0,8).toUpperCase())}</strong><span>Movimiento auditado</span></div>
            </div>`).join("")
        : `<div class="control-empty"><strong>No hay retiros registrados hoy.</strong><br>Los retiros de efectivo aparecerán aquí inmediatamente.</div>`;

    const rec = data.transfer_reconciliation || {};
    const providers = rec.providers || {};
    const transferSummary = document.getElementById('transferSummary');
    if (transferSummary) {
        const cards = Object.entries(providers).map(([key,p]) => `<div class="transfer-provider"><span>${escapeHtml(p.label || key)}</span><strong>${money(p.sales_total)}</strong><small>${p.sales_count || 0} ventas · ${p.proof_count || 0} comprobantes aprobados</small></div>`).join('');
        transferSummary.innerHTML = `<div class="transfer-kpis"><div><span>Ventas registradas por transferencia</span><strong>${rec.registered_count || 0}</strong><small>${money(rec.registered_total || 0)}</small></div><div><span>Comprobantes aprobados</span><strong>${rec.approved_proof_count || 0}</strong><small>Revisados por Caja</small></div></div><div class="transfer-providers">${cards || '<span>No hay transferencias hoy.</span>'}</div>`;
    }

    const transferAlerts = document.getElementById('transferAlerts');
    if (transferAlerts) {
        const pending = rec.pending_transfer_closures || [];
        const missing = rec.sales_without_approved_proof || [];
        transferAlerts.innerHTML = `${pending.length ? `<div class="transfer-alert warning"><b>⚠️ Comprobantes aprobados sin venta cerrada (${pending.length})</b>${pending.map(x=>`<span>Pedido #${escapeHtml(x.order_short_id)} · ${escapeHtml(x.method_label)} · ${escapeHtml(x.customer_name)}</span>`).join('')}</div>` : ''}${missing.length ? `<div class="transfer-alert danger"><b>🚨 Ventas por transferencia sin comprobante aprobado (${missing.length})</b>${missing.map(x=>`<span>Pedido #${escapeHtml(x.order_short_id)} · ${escapeHtml(x.method_label)} · ${money(x.amount)}</span>`).join('')}</div>` : ''}${!pending.length&&!missing.length ? `<div class="transfer-ok">✅ No hay diferencias de comprobantes por transferencia detectadas.</div>` : ''}`;
    }

    const evidenceList = document.getElementById('transferEvidenceList');
    const evidence = data.transfer_evidence_today || [];
    if (evidenceList) {
        evidenceList.innerHTML = evidence.length ? evidence.map(x=>`<article class="transfer-evidence-card"><a href="${escapeHtml(x.file_url)}" target="_blank" rel="noopener"><img src="${escapeHtml(x.file_url)}" alt="Comprobante ${escapeHtml(x.order_short_id)}"></a><div><b>Pedido #${escapeHtml(x.order_short_id)}</b><span>${escapeHtml(x.customer_name)} · ${escapeHtml(x.method_label)}</span><small>${x.status==='APPROVED'?'✅ Aprobado':x.status==='REJECTED'?'❌ Rechazado':'⏳ Pendiente'} · ${dateTime(x.created_at)}</small><small>${x.registered_in_cash?'✅ Venta registrada en Caja':'⚠️ Aún no registrada en Caja'}</small>${x.review_note?`<small>Nota: ${escapeHtml(x.review_note)}</small>`:''}</div></article>`).join('') : '<div class="control-empty"><strong>No hay comprobantes transferidos hoy.</strong><br>Cuando un domiciliario suba un comprobante aparecerá aquí.</div>';
    }
}

const editModal = document.getElementById("editClosingModal");
const editForm = document.getElementById("editClosingForm");
const editRegisterId = document.getElementById("editRegisterId");
const editClosingAmount = document.getElementById("editClosingAmount");
const editReason = document.getElementById("editClosingReason");
const editConfirm = document.getElementById("editClosingConfirm");

function closeEditModal(){
    if (!editModal) return;
    editModal.hidden = true;
    editForm?.reset();
    if (editConfirm) editConfirm.checked = false;
}

document.addEventListener("click", event => {
    const button = event.target.closest("[data-edit-register]");
    if (!button) return;
    editRegisterId.value = button.dataset.editRegister;
    editClosingAmount.value = Number(button.dataset.currentClosing || 0);
    editReason.value = "";
    editConfirm.checked = false;
    editModal.hidden = false;
    editClosingAmount.focus();
});

document.getElementById("closeEditClosingModal")?.addEventListener("click", closeEditModal);
document.getElementById("cancelEditClosing")?.addEventListener("click", closeEditModal);
editModal?.addEventListener("click", event => {
    if (event.target === editModal) closeEditModal();
});

editForm?.addEventListener("submit", async event => {
    event.preventDefault();
    if (!editConfirm.checked) {
        alert("Debes confirmar que entiendes que esta corrección solo puede hacerse una vez y únicamente hoy.");
        return;
    }
    const registerId = editRegisterId.value;
    const amount = Number(editClosingAmount.value);
    const reason = editReason.value.trim();
    if (!Number.isFinite(amount) || amount < 0) {
        alert("Ingresa un monto válido.");
        return;
    }
    if (reason.length < 5) {
        alert("Escribe un motivo de al menos 5 caracteres para dejar trazabilidad.");
        return;
    }
    const button = editForm.querySelector("button[type=submit]");
    button.disabled = true;
    try {
        const response = await fetch(`/api/cashier/admin/register/${encodeURIComponent(registerId)}/closing-amount`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({closing_amount: amount, reason})
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "No se pudo corregir el arqueo.");
        closeEditModal();
        await loadCashControl();
        alert("Corrección guardada. Esta caja ya no podrá volver a editarse.");
    } catch (error) {
        alert(error.message || "No se pudo corregir el arqueo.");
    } finally {
        button.disabled = false;
    }
});

document.getElementById("refreshAdminCash")?.addEventListener("click", loadCashControl);
loadCashControl().catch(err=>{console.error(err);document.getElementById("controlRegisterList").textContent="No fue posible consultar las cajas.";document.getElementById("controlClosedRegisterList").textContent="No fue posible consultar los cierres.";});
setInterval(() => loadCashControl().catch(console.error), 15000);

(() => {
    const grid = document.getElementById("supportAdminGrid");
    const refresh = document.getElementById("supportRefresh");
    const token = localStorage.getItem("token");
    const money = value => `$${Number(value || 0).toLocaleString("es-CO")}`;
    const esc = value => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));

    async function load() {
        grid.innerHTML = '<div class="support-loading">Cargando solicitudes…</div>';
        try {
            const r = await fetch("/api/chatbot/support?status=ALL", { headers: { Authorization: `Bearer ${token}` } });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || "No fue posible cargar soporte.");
            if (!data.items?.length) { grid.innerHTML = '<div class="support-empty">🎧 No hay solicitudes de soporte registradas.</div>'; return; }
            grid.innerHTML = data.items.map(item => `
                <article class="support-ticket ${item.status === 'RESOLVED' ? 'resolved' : ''}">
                    <div class="support-ticket-top"><span class="support-status">${item.status === 'RESOLVED' ? 'ATENDIDA' : 'PENDIENTE'}</span><time>${new Date(item.created_at).toLocaleString('es-CO')}</time></div>
                    <h3>${esc(item.customer_name)}</h3>
                    <small>${esc(item.customer_email || 'Sin correo')}</small>
                    <p>${esc(item.message)}</p>
                    ${item.status !== 'RESOLVED' ? `<button class="resolve-btn" data-id="${item.id}">✓ Marcar como atendida</button>` : '<span class="resolved-label">✓ Cerrada</span>'}
                </article>`).join('');
            grid.querySelectorAll('.resolve-btn').forEach(btn => btn.addEventListener('click', () => resolve(btn.dataset.id)));
        } catch (e) { grid.innerHTML = `<div class="support-error">${esc(e.message)}</div>`; }
    }
    async function resolve(id) {
        const r = await fetch(`/api/chatbot/support/${id}/close`, { method: 'PATCH', headers: { Authorization: `Bearer ${token}` } });
        if (!r.ok) { alert('No fue posible cerrar la solicitud.'); return; }
        load();
    }
    refresh?.addEventListener('click', load);
    load();
})();

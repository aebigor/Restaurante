(() => {
  const $ = id => document.getElementById(id);
  let items = [];
  const fields = ["name","sku","barcode","category","item_type","brand","presentation","unit","quantity","min_quantity","max_quantity","reorder_quantity","unit_cost","storage","location","purchase_date","opened_date","expiry_date","storage_temperature","supplier","allergen","notes"];
  const money = n => new Intl.NumberFormat("es-CO", {style:"currency", currency:"COP", maximumFractionDigits:0}).format(Number(n || 0));
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const dateTime = v => v ? new Date(v).toLocaleString("es-CO", {day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit"}) : "—";

  function getToken() {
    try {
      if (window.AppAuth && typeof window.AppAuth.getAuth === "function") {
        const auth = window.AppAuth.getAuth();
        if (auth?.token) return auth.token;
      }
    } catch (_) {}
    return localStorage.getItem("token") || localStorage.getItem("customer_token") || "";
  }

  async function req(url, opts = {}) {
    const token = getToken();
    const headers = {"Content-Type":"application/json", ...(opts.headers || {})};
    if (token) headers.Authorization = `Bearer ${token}`;
    const r = await fetch(url, {...opts, headers});
    if (!r.ok) {
      let m = "Error en la operación";
      try { m = (await r.json()).detail || m; } catch {}
      throw Error(m);
    }
    return r.json();
  }

  function stateClass(s) {
    if (s === "VENCIDO" || s === "SIN STOCK") return "bad";
    if (s === "REVISAR VENCIMIENTO") return "expiry";
    if (s === "POR AGOTARSE") return "low";
    return "ok";
  }

  function render() {
    const q = $("search").value.toLowerCase().trim();
    const filter = $("filter").value;
    const shown = items.filter(i => (!filter || i.status === filter) && [i.name,i.sku,i.barcode,i.category,i.supplier,i.location].join(" ").toLowerCase().includes(q));
    $("itemsBody").innerHTML = shown.length ? shown.map(i => `
      <tr>
        <td><b>${esc(i.name)}</b><br><small>${esc(i.brand || "Sin marca")} · ${esc(i.presentation || "")} · ${money(i.unit_cost)} / ${esc(i.unit)}</small></td>
        <td>${esc(i.category)}<br><small>${esc(i.item_type)}</small></td>
        <td><b>${i.quantity} ${esc(i.unit)}</b></td>
        <td>${i.min_quantity} / ${i.max_quantity || "—"}</td>
        <td>${esc(i.storage || "—")}<br><small>${esc(i.location || "Sin ubicación")}</small></td>
        <td>${esc(i.expiry_date || "Sin vencimiento")}</td>
        <td><span class="state ${stateClass(i.status)}">${esc(i.status)}</span><small class="recommendation">${esc(i.recommendation)}</small></td>
        <td><div class="action-row"><button class="mini-btn" data-edit="${i.id}">Editar</button><button class="mini-btn" data-move="${i.id}">Movimiento</button><button class="mini-btn" data-history="${i.id}">Historial</button><button class="mini-btn danger" data-del="${i.id}">Archivar</button></div></td>
      </tr>`).join("") : `<tr><td colspan="8">No hay productos que coincidan.</td></tr>`;

    const counts = {"OK":0,"POR AGOTARSE":0,"SIN STOCK":0,"REVISAR VENCIMIENTO":0,"VENCIDO":0};
    items.forEach(i => counts[i.status] = (counts[i.status] || 0) + 1);
    $("chartBars").innerHTML = Object.entries(counts).map(([status,n]) => {
      const width = items.length ? Math.max((n / items.length) * 100, n ? 3 : 0) : 0;
      return `<div class="bar-row"><span>${status}</span><div class="bar-track"><div class="bar-fill ${stateClass(status)}" style="width:${width}%"></div></div><b>${n}</b></div>`;
    }).join("");
    $("statTotal").textContent = items.length;
    $("statLow").textContent = counts["POR AGOTARSE"] + counts["SIN STOCK"];
    $("statExpiry").textContent = counts["VENCIDO"] + counts["REVISAR VENCIMIENTO"];
    $("statValue").textContent = money(items.reduce((a,i) => a + Number(i.value || 0), 0));
  }

  async function load() {
    try {
      const d = await req("/api/inventory");
      items = d.items || [];
      render();
    } catch (e) {
      $("itemsBody").innerHTML = `<tr><td colspan="8">${esc(e.message)}. Inicia sesión como administrador y vuelve a cargar.</td></tr>`;
    }
  }

  function openItem(item) {
    $("itemForm").reset();
    $("itemId").value = item?.id || "";
    $("modalTitle").textContent = item ? "Editar producto" : "Agregar producto";
    const defaults = {category:"Ingredientes", item_type:"INGREDIENTE", unit:"unidad", quantity:0, min_quantity:0, max_quantity:0, reorder_quantity:0, unit_cost:0};
    fields.forEach(k => { $(k).value = item?.[k] ?? defaults[k] ?? ""; });
    $("itemModal").hidden = false;
  }
  function closeItem() { $("itemModal").hidden = true; }
  function openMove(item) { $("movementForm").reset(); $("movementItemId").value = item.id; $("movementTitle").textContent = `${item.name} · ${item.quantity} ${item.unit}`; $("movementModal").hidden = false; }
  function closeMove() { $("movementModal").hidden = true; }

  async function showHistory(item) {
    $("historyTitle").textContent = `Historial · ${item.name}`;
    $("historyBody").innerHTML = "Cargando...";
    $("historyModal").hidden = false;
    try {
      const d = await req(`/api/inventory/${item.id}/movements`);
      $("historyBody").innerHTML = d.movements?.length ? d.movements.map(m => `<div class="history-row"><div><b>${esc(m.type)}</b><span>${dateTime(m.created_at)}</span></div><strong>${m.type === "SALIDA" || m.type === "MERMA" ? "-" : "+"}${m.quantity} ${esc(item.unit)}</strong><small>${esc(m.reason || "Sin motivo")}</small></div>`).join("") : `<div class="empty-history">No hay movimientos registrados.</div>`;
    } catch (e) { $("historyBody").textContent = e.message; }
  }
  function closeHistory() { $("historyModal").hidden = true; }

  $("newItem").onclick = () => openItem();

  $("downloadReport").onclick = async () => {
    try {
      const token = getToken();
      if (!token) throw Error("Tu sesión de administrador no está activa. Vuelve a iniciar sesión.");
      const r = await fetch("/api/inventory/report.xlsx", {headers:{Authorization:`Bearer ${token}`}});
      if (!r.ok) {
        let msg = `No se pudo descargar el informe (HTTP ${r.status})`;
        try { const d = await r.json(); msg = d.detail || msg; } catch (_) {}
        throw Error(msg);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "informe_inventario.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message || "No se pudo descargar el informe.");
    }
  };
  $("closeModal").onclick = $("cancelModal").onclick = closeItem;
  $("closeMovement").onclick = $("cancelMovement").onclick = closeMove;
  $("closeHistory").onclick = closeHistory;
  $("search").oninput = render;
  $("filter").onchange = render;

  $("itemForm").onsubmit = async e => {
    e.preventDefault();
    const id = $("itemId").value;
    const d = {};
    fields.forEach(k => d[k] = ["quantity","min_quantity","max_quantity","reorder_quantity","unit_cost"].includes(k) ? Number($(k).value || 0) : ($(k).value || null));
    try { await req(id ? `/api/inventory/${id}` : "/api/inventory", {method:id ? "PUT" : "POST", body:JSON.stringify(d)}); closeItem(); await load(); }
    catch (err) { alert(err.message); }
  };

  $("movementForm").onsubmit = async e => {
    e.preventDefault();
    try { await req(`/api/inventory/${$("movementItemId").value}/movement`, {method:"POST", body:JSON.stringify({movement_type:$("movementType").value, quantity:Number($("movementQty").value), reason:$("movementReason").value || null})}); closeMove(); await load(); }
    catch (err) { alert(err.message); }
  };

  $("itemsBody").onclick = async e => {
    const b = e.target.closest("button");
    if (!b) return;
    const id = b.dataset.edit || b.dataset.move || b.dataset.history || b.dataset.del;
    const item = items.find(x => x.id === id);
    if (!item) return;
    if (b.dataset.edit) openItem(item);
    else if (b.dataset.move) openMove(item);
    else if (b.dataset.history) showHistory(item);
    else if (b.dataset.del && confirm(`¿Archivar ${item.name}? Se conserva su historial.`)) { try { await req(`/api/inventory/${item.id}`, {method:"DELETE"}); await load(); } catch (err) { alert(err.message); } }
  };

  load();
})();

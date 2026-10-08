(()=>{
const token=AppAuth.getAuth().token;let user=null;try{user=AppAuth.getAuth().user}catch(_){ }
if(!token||user?.role!=='Administrador'){location.replace('/admin/login');return;}
const $=id=>document.getElementById(id), grid=$('ordersGrid'), detail=$('orderDetail');
const money=v=>new Intl.NumberFormat('es-CO',{style:'currency',currency:'COP',maximumFractionDigits:0}).format(Number(v||0));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const fmt=v=>v?new Date(v).toLocaleString('es-CO'):'—';
const labels={PENDING_CASHIER:'Esperando Caja',OPEN:'Confirmado',PREPARING:'En preparación',READY:'Listo',OUT_FOR_DELIVERY:'En camino',DELIVERED_PENDING_PAYMENT:'Entregado · pendiente de cierre',DELIVERED:'Entregado',CLOSED:'Cerrado',CANCELLED:'Cancelado'};
async function api(url,opt={}){const r=await fetch(url,{...opt,headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`,...(opt.headers||{})}});const t=await r.text();let d={};try{d=JSON.parse(t)}catch{}if(!r.ok)throw Error(d.detail||`HTTP ${r.status}`);return d;}
let orders=[], selected=null, map=null, marker=null, courierMap=null, courierMarkers={};
async function loadCourierMonitor(){
  const list=document.getElementById('adminCourierList'), state=document.getElementById('courierMonitorState');
  if(!list)return;
  try{
    const rows=await api('/api/delivery/admin/couriers');
    if(!courierMap){courierMap=L.map('adminCourierMap').setView([4.711,-74.072],12);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(courierMap);}
    const nextMarkers={}; const valid=[];
    list.innerHTML=rows.length?rows.map(x=>{
      if(x.latitude!=null&&x.longitude!=null)valid.push([x.latitude,x.longitude]);
      if(x.latitude!=null&&x.longitude!=null){
        const pos=[x.latitude,x.longitude];let m=courierMarkers[x.courier_id];
        const popup=`<b>🚚 ${esc(x.name)}</b><br>${x.online?'🟢 En línea':'⚪ Sin conexión'}${x.destination?`<br>📍 ${esc(x.destination)}`:''}`;
        if(!m)m=L.marker(pos).addTo(courierMap);else m.setLatLng(pos);m.bindPopup(popup);nextMarkers[x.courier_id]=m;
      }
      return `<article class="admin-courier-row ${x.online?'online':'offline'}"><div class="courier-row-head"><b>🚚 ${esc(x.name)}</b><span>${x.online?'🟢 EN LÍNEA':'⚪ SIN CONEXIÓN'}</span></div><div>${x.order_id?`<strong>Pedido #${esc(x.order_short_id)}</strong> · ${esc(x.order_status||'')}`:'Sin pedido activo'}</div>${x.destination?`<small>📍 ${esc(x.destination)}</small>`:'<small>Sin destino asignado</small>'}<small>${x.recorded_at?`GPS ${fmt(x.recorded_at)}`:'Sin ubicación registrada'}${x.last_seen?` · última conexión ${fmt(x.last_seen)}`:''}</small></article>`;
    }).join(''):'<div class="empty">No hay domiciliarios contratados activos.</div>';
    Object.values(courierMarkers).forEach(m=>{if(!nextMarkers[m._courier_id]){/* handled below */}});
    Object.entries(courierMarkers).forEach(([id,m])=>{if(!nextMarkers[id])courierMap.removeLayer(m);});
    Object.entries(nextMarkers).forEach(([id,m])=>m._courier_id=id);courierMarkers=nextMarkers;
    if(valid.length===1)courierMap.setView(valid[0],15); else if(valid.length>1)courierMap.fitBounds(valid,{padding:[30,30],maxZoom:14});
    if(state)state.textContent=`${rows.filter(x=>x.online).length} en línea · ${rows.length} domiciliarios`;
  }catch(e){if(list)list.innerHTML=`<div class="empty">${esc(e.message)}</div>`;if(state)state.textContent='Error de conexión';}
}

async function load(){try{await loadCourierMonitor();const data=await api('/api/delivery/admin/orders');orders=data;renderList();if(selected){const fresh=orders.find(x=>x.id===selected.id);if(fresh)await openDetail(fresh.id,false)}$('ordersMessage').textContent='';}catch(e){$('ordersMessage').textContent=e.message;}}
function renderList(){if(!orders.length){grid.innerHTML='<div class="empty">No hay pedidos online o domicilios.</div>';return;}grid.innerHTML=orders.map(o=>`<article class="order-card" data-order="${o.id}"><div class="head"><div><h3>Pedido #${esc(o.short_id)}</h3><small>${fmt(o.created_at)}</small></div><span class="status">${esc(labels[o.status]||o.status)}</span></div><p>👤 ${esc(o.customer?.name||'Cliente')}</p><p>📍 ${esc(o.address||'Sin dirección')}</p><p>🛵 ${o.courier_name?esc(o.courier_name):'Sin repartidor'}</p><div class="mini-row"><strong>${money(o.total)}</strong><span>${o.location?'📍 GPS activo':'📍 Sin GPS'}</span></div></article>`).join('');}
function timeline(o){return [['Creado',o.created_at],['Caja confirmó',o.cashier_confirmed_at],['Cocina inició',o.kitchen_started_at],['Pedido listo',o.ready_at],['Repartidor asignado',o.courier_assigned_at],['Salida a domicilio',o.dispatched_at],['Entrega validada',o.courier_delivered_at],['Pago/cierre',o.closed_at]].map(x=>`<div><span>${x[0]}</span><b>${fmt(x[1])}</b></div>`).join('');}
async function openDetail(id,scroll=true){const o=await api(`/api/delivery/admin/orders/${id}`);selected=o;detail.classList.remove('hidden');$('detailTitle').textContent=`Pedido #${o.short_id}`;$('detailBody').innerHTML=`<div class="detail-layout"><div><div class="panel"><h3>Información</h3><div class="facts"><div class="fact"><small>Cliente</small><b>${esc(o.customer?.name||'Cliente')}</b></div><div class="fact"><small>Teléfono</small><b>${esc(o.customer?.phone||'—')}</b></div><div class="fact"><small>Dirección</small><b>${esc(o.address||'—')}</b></div><div class="fact"><small>Repartidor</small><b>${esc(o.courier_name||'Sin asignar')}</b></div><div class="fact"><small>Estado</small><b>${esc(labels[o.status]||o.status)}</b></div><div class="fact"><small>Total</small><b>${money(o.total)}</b></div></div>${o.delivery_code?`<div class="code-box"><small>CÓDIGO DE ENTREGA VIGENTE</small><br><strong>${esc(o.delivery_code)}</strong></div>`:''}<div class="timeline">${timeline(o)}</div></div><div class="panel" style="margin-top:20px"><h3>💬 Chat</h3><div id="chatMessages" class="messages">Cargando...</div><form id="chatForm" class="chat-form"><input id="chatInput" maxlength="1000" placeholder="Mensaje para Caja o repartidor..." required><button class="btn" type="submit">Enviar</button></form></div></div><div><div class="panel"><h3>📍 Ubicación del repartidor</h3><div id="orderMap" class="map"></div><div id="mapState" class="map-state">Actualizando ubicación...</div></div><div class="panel" style="margin-top:20px"><h3>Acciones</h3>${!['CLOSED','CANCELLED','DELIVERED_PENDING_PAYMENT'].includes(o.status)?`<button id="cancelOrder" data-id="${o.id}" class="btn danger">✕ Cancelar pedido</button>`:'<p>Este pedido ya no admite cancelación desde Administración.</p>'}</div></div></div>`;
initMap(o);await loadChat();if(scroll)detail.scrollIntoView({behavior:'smooth',block:'start'});
}
function initMap(o){if(map){map.remove();map=null;marker=null}map=L.map('orderMap').setView([4.711,-74.072],12);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);if(o.location)updateMarker(o.location);else $('mapState').textContent='El repartidor todavía no ha enviado ubicación.';}
function updateMarker(loc){if(!map||!loc)return;const pos=[loc.latitude,loc.longitude];if(!marker)marker=L.marker(pos).addTo(map).bindPopup(`🛵 ${esc(selected?.courier_name||'Repartidor')}`);else marker.setLatLng(pos);map.setView(pos,15);$('mapState').textContent=`Última ubicación: ${fmt(loc.recorded_at)} · precisión ${loc.accuracy?Math.round(loc.accuracy)+' m':'—'}`;}
async function refreshLocation(){if(!selected)return;try{const l=await api(`/api/delivery/admin/orders/${selected.id}/location`);if(l.available)updateMarker(l);else $('mapState').textContent='El repartidor todavía no ha enviado ubicación.';}catch(e){console.error(e)}}
async function loadChat(){if(!selected)return;try{const data=await api(`/api/delivery/messages?order_id=${encodeURIComponent(selected.id)}`);const box=$('chatMessages');box.innerHTML=data.length?data.map(m=>`<div class="bubble"><b>${esc(m.sender)}</b><small>${fmt(m.created_at)}</small><p>${esc(m.message)}</p></div>`).join(''):'<p>No hay mensajes todavía.</p>';box.scrollTop=box.scrollHeight;}catch(e){$('chatMessages').textContent=e.message}}
$('ordersGrid').addEventListener('click',e=>{const card=e.target.closest('[data-order]');if(card)openDetail(card.dataset.order)});
$('closeDetail').onclick=()=>{detail.classList.add('hidden');selected=null;if(map){map.remove();map=null}};
$('refreshOrders').onclick=load;
document.addEventListener('click',async e=>{const b=e.target.closest('#cancelOrder');if(!b)return;const reason=prompt('Motivo de cancelación:');if(!reason?.trim())return;try{await api(`/api/delivery/admin/orders/${b.dataset.id}/cancel`,{method:'PATCH',body:JSON.stringify({reason:reason.trim()})});await load()}catch(x){alert(x.message)}});
document.addEventListener('submit',async e=>{if(e.target.id!=='chatForm')return;e.preventDefault();const input=$('chatInput'),v=input.value.trim();if(!v||!selected)return;try{await api('/api/delivery/messages',{method:'POST',body:JSON.stringify({order_id:selected.id,message:v})});input.value='';await loadChat()}catch(x){alert(x.message)}});
load();setInterval(load,5000);setInterval(loadCourierMonitor,5000);setInterval(refreshLocation,3000);setInterval(loadChat,5000);
})();

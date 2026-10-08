(()=>{
const token=localStorage.getItem('token');
let user=null;try{user=JSON.parse(localStorage.getItem('user')||'null')}catch(_){}
if(!token||user?.role!=='Domiciliario'){location.replace('/login');return;}
const $=id=>document.getElementById(id);
const money=v=>new Intl.NumberFormat('es-CO',{style:'currency',currency:'COP',maximumFractionDigits:0}).format(Number(v||0));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const methodLabel=m=>({CASH:'Efectivo',CARD:'Tarjeta',TRANSFER:'Transferencia',TRANSFER_NEQUI:'Nequi',TRANSFER_BANCOLOMBIA:'Bancolombia',TRANSFER_LLAVES:'Llaves'})[m]||m||'Sin definir';
const proofLabel=s=>({PENDING:'⏳ Pendiente de revisión',APPROVED:'✅ Aprobado',REJECTED:'❌ Rechazado'})[s]||s;
async function api(url,opt={}){
  const headers={Authorization:`Bearer ${token}`,...(opt.headers||{})};
  if(!(opt.body instanceof FormData)) headers['Content-Type']='application/json';
  const r=await fetch(url,{...opt,headers});
  const t=await r.text();let d={};try{d=JSON.parse(t)}catch{}
  if(!r.ok)throw Error(d.detail||`HTTP ${r.status}`);return d;
}
function proofHtml(o){
  const proofs=o.payment_proofs||[];
  if(!proofs.length)return '<div class="proof-empty">No hay comprobante cargado todavía.</div>';
  return proofs.map(p=>`<div class="proof-row"><a href="${esc(p.file_url)}" target="_blank" rel="noopener"><img src="${esc(p.file_url)}" alt="Comprobante"></a><div><b>${esc(methodLabel(p.payment_method))}</b><span>${esc(proofLabel(p.status))}</span><small>${p.review_note?esc(p.review_note):'Enviado '+new Date(p.created_at).toLocaleString('es-CO')}</small></div></div>`).join('');
}
function paymentBox(o){
  const method=o.payment_method||'CASH';
  return `<div class="delivery-payment-box">
    <div class="payment-title"><div><b>💰 Cierre de la venta</b><small>Selecciona cómo recibió el pago y avisa a Caja.</small></div><strong>${money(o.total)}</strong></div>
    <label>Método recibido
      <select data-payment-method="${esc(o.id)}">
        <option value="CASH" ${method==='CASH'?'selected':''}>Efectivo</option>
        <option value="CARD" ${method==='CARD'?'selected':''}>Tarjeta</option>
        <option value="TRANSFER_NEQUI" ${method==='TRANSFER_NEQUI'?'selected':''}>Nequi</option>
        <option value="TRANSFER_BANCOLOMBIA" ${method==='TRANSFER_BANCOLOMBIA'?'selected':''}>Bancolombia</option>
        <option value="TRANSFER_LLAVES" ${method==='TRANSFER_LLAVES'?'selected':''}>Llaves</option>
      </select>
    </label>
    <button class="payment-report" data-report-payment="${esc(o.id)}">📨 Informar pago a Caja</button>
    <div class="proof-upload-row">
      <input type="file" accept="image/jpeg,image/png,image/webp" data-proof-file="${esc(o.id)}">
      <button class="payment-proof" type="button" data-upload-proof="${esc(o.id)}">📷 Subir comprobante</button>
    </div>
    <small class="payment-help">Para efectivo no necesitas foto. Para Nequi, Bancolombia o Llaves toma una foto legible del comprobante.</small>
    <div class="proofs"><b>Comprobantes enviados</b>${proofHtml(o)}</div>
  </div>`;
}
function card(o,active=false){
  let actions='';
  if(active && o.status==='OUT_FOR_DELIVERY') actions=`<div class="actions"><button data-deliver="${o.id}">🔐 Confirmar entrega</button><button data-cancel="${o.id}" class="danger">Cancelar orden</button></div>`;
  else if(active && o.status==='DELIVERED_PENDING_PAYMENT') actions=paymentBox(o);
  else if(!active) actions=`<button data-claim="${o.id}">🚚 Tomar pedido</button>`;
  return `<article class="delivery-card"><div class="top"><b>#${esc(o.short_id)}</b><strong>${money(o.total)}</strong></div><p>👤 ${esc(o.customer?.name||'Cliente')} · ${esc(o.customer?.phone||'')}</p><p class="address">📍 ${esc(o.address||'Sin dirección')}</p><p>🍳 Cocina: <b>${o.prep_seconds!=null?Math.round(o.prep_seconds/60)+' min':'calculando'}</b></p>${o.dispatched_at?`<p>🛵 En ruta: <b>${Math.max(0,Math.floor((Date.now()-new Date(o.dispatched_at))/60000))} min</b></p>`:''}${o.payment_method?`<p>💳 Pago reportado: <b>${esc(methodLabel(o.payment_method))}</b></p>`:''}${actions}</article>`;
}
async function loadMessages(){
  try{
    const qs=window.activeDeliveryOrderId?`?order_id=${encodeURIComponent(window.activeDeliveryOrderId)}`:'';
    const data=await api(`/api/delivery/messages${qs}`);
    $('messages').innerHTML=data.length?data.map(x=>`<div><b>${esc(x.sender)}</b><small>${new Date(x.created_at).toLocaleTimeString('es-CO')}</small><p>${esc(x.message)}</p></div>`).join(''):'<p>No hay mensajes.</p>';
  }catch(e){console.error(e)}
}
async function load(){
  try{
    const [a,m]=await Promise.all([api('/api/delivery/available-orders'),api('/api/delivery/my-orders')]);
    $('available').innerHTML=a.length?a.map(o=>card(o)).join(''):'<p>No hay pedidos listos esperando repartidor.</p>';
    const active=m.find(o=>o.status==='OUT_FOR_DELIVERY'||o.status==='DELIVERED_PENDING_PAYMENT');
    window.activeDeliveryOrderId=active?.id||null;
    $('active').innerHTML=active?card(active,true):'<p>No tienes una entrega activa.</p>';
    await loadMessages();
  }catch(e){console.error(e)}
}
async function reportPayment(orderId){
  const select=document.querySelector(`[data-payment-method="${CSS.escape(orderId)}"]`);const method=select?.value||'CASH';
  try{await api(`/api/delivery/orders/${orderId}/payment-method`,{method:'PATCH',body:JSON.stringify({payment_method:method})});alert(`Pago informado a Caja: ${methodLabel(method)}.`);await load();}
  catch(e){alert(e.message)}
}
async function uploadProof(orderId){
  const fileInput=document.querySelector(`[data-proof-file="${CSS.escape(orderId)}"]`);const select=document.querySelector(`[data-payment-method="${CSS.escape(orderId)}"]`);const file=fileInput?.files?.[0];const method=select?.value||'TRANSFER';
  if(!file){alert('Selecciona primero la foto del comprobante.');return;}
  if(!method.startsWith('TRANSFER')){alert('La foto solo se usa para pagos por transferencia.');return;}
  const fd=new FormData();fd.append('payment_method',method);fd.append('file',file);
  try{await api(`/api/delivery/orders/${orderId}/payment-proof`,{method:'POST',body:fd});alert('Comprobante enviado a Caja para revisión.');await load();}
  catch(e){alert(e.message)}
}
document.addEventListener('click',async e=>{
  const claim=e.target.closest('[data-claim]');
  if(claim){try{await api(`/api/delivery/orders/${claim.dataset.claim}/claim`,{method:'PATCH'});await load()}catch(x){alert(x.message)}return;}
  const del=e.target.closest('[data-deliver]');
  if(del){const code=prompt('Ingresa el código de 6 dígitos del cliente:');if(!code)return;try{await api(`/api/delivery/orders/${del.dataset.deliver}/delivered`,{method:'POST',body:JSON.stringify({code})});alert('Entrega confirmada. Ahora reporta el pago a Caja.');await load()}catch(x){alert(x.message)}return;}
  const cancel=e.target.closest('[data-cancel]');
  if(cancel){const reason=prompt('Motivo de cancelación:');if(!reason)return;try{await api(`/api/delivery/orders/${cancel.dataset.cancel}/cancel`,{method:'PATCH',body:JSON.stringify({reason})});await load()}catch(x){alert(x.message)}return;}
  const report=e.target.closest('[data-report-payment]');
  if(report){await reportPayment(report.dataset.reportPayment);return;}
  const upload=e.target.closest('[data-upload-proof]');
  if(upload){await uploadProof(upload.dataset.uploadProof);return;}
});
$('messageForm').addEventListener('submit',async e=>{
  e.preventDefault();const v=$('messageInput').value.trim();if(!v)return;
  try{await api('/api/delivery/messages',{method:'POST',body:JSON.stringify({message:v,order_id:window.activeDeliveryOrderId||null})});$('messageInput').value='';await loadMessages();}
  catch(x){alert(x.message)}
});
$('logout').onclick=async()=>{try{await api('/api/delivery/presence/offline',{method:'POST'})}catch(_){}localStorage.removeItem('token');localStorage.removeItem('user');location.replace('/login')};
function track(){
  if(!navigator.geolocation){$('locationState').textContent='⚠️ Este navegador no permite ubicación.';return;}
  navigator.geolocation.watchPosition(async p=>{try{await api('/api/delivery/location',{method:'POST',body:JSON.stringify({latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy})});$('locationState').textContent=`📍 Ubicación activa · precisión aprox. ${Math.round(p.coords.accuracy)} m`;}catch(e){console.error(e)}},e=>{$('locationState').textContent='⚠️ Debes permitir la ubicación para que Caja y Administración puedan ver al domiciliario.'},{enableHighAccuracy:true,maximumAge:2000,timeout:10000});
}
async function heartbeat(){try{await api('/api/delivery/presence',{method:'POST'})}catch(e){console.error(e)}}
track();heartbeat();load();setInterval(load,5000);setInterval(heartbeat,15000);
})();

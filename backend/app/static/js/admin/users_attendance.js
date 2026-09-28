const token = localStorage.getItem("token");
const headers = () => ({"Content-Type":"application/json", Authorization:`Bearer ${token}`});
let roles = [];
let editingUserId = null;
let scheduleUserId = null;

const $ = id => document.getElementById(id);
const esc = v => String(v ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#039;",'"':"&quot;"}[c]));

function openModal(id){ $(id).classList.add("open"); }
function closeModal(id){ $(id).classList.remove("open"); }
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>closeModal(b.dataset.close)));

async function loadRoles(){
  const r=await fetch("/api/admin/roles",{headers:headers()});
  if(!r.ok) throw new Error("No se pudieron cargar los roles");
  roles=await r.json();
  $("roleId").innerHTML=roles.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join("");
}

async function loadUsers(){
  const r=await fetch("/api/admin/users",{headers:headers()});
  if(!r.ok) throw new Error("No se pudieron cargar los usuarios");
  const users=await r.json();
  $("usersCount").textContent=users.length;
  const box=$("usersTable");
  if(!users.length){box.innerHTML='<div class="empty-state">No hay usuarios registrados.</div>';return;}
  box.innerHTML=users.map(u=>`<article class="user-row">
    <div class="avatar">${esc((u.full_name||"U").split(/\s+/).slice(0,2).map(x=>x[0]).join("").toUpperCase())}</div>
    <div class="user-main"><strong>${esc(u.full_name)}</strong><span>${esc(u.email)} · ${esc(u.role||"Sin rol")}</span></div>
    <span class="status-pill ${u.active?'ok':'off'}">${u.active?'ACTIVO':'INACTIVO'}</span>
    <span class="attendance-pill ${u.attendance_enabled?'on':'off'}">${u.attendance_enabled?'🕐 Asistencia activa':'Sin asistencia'}</span>
    <div class="row-actions"><button data-action="schedule" data-id="${u.id}">Horario</button>${u.attendance_enabled?`<button data-action="qr" data-id="${u.id}">QR</button>`:''}<button data-action="edit" data-id="${u.id}">Editar</button></div>
  </article>`).join("");
  box.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>handleAction(b.dataset.action,b.dataset.id,users)));
}

async function handleAction(action,id,users){
  const u=users.find(x=>x.id===id);
  if(action==='edit'){
    editingUserId=id; $("userModalTitle").textContent="Editar usuario"; $("userId").value=id;
    $("fullName").value=u.full_name; $("email").value=u.email; $("password").required=false; $("password").value="";
    const role=roles.find(r=>r.name===u.role); if(role) $("roleId").value=role.id;
    $("attendanceEnabled").checked=u.attendance_enabled; $("attendancePin").value=""; openModal("userModal"); return;
  }
  if(action==='schedule'){
    scheduleUserId=id; $("scheduleTitle").textContent=`Horario de ${u.full_name}`; await loadSchedule(id); openModal("scheduleModal"); return;
  }
  if(action==='qr'){
    $("qrName").textContent=u.full_name; $("qrImage").src=`/api/attendance/qr/user/${id}.svg?ts=${Date.now()}`; $("qrPinText").textContent="Código personal: por seguridad se muestra solo si acabas de crearlo o cambiarlo."; $("printQr").onclick=()=>printCard(u.full_name); openModal("qrModal");
  }
}

async function loadSchedule(id){
  const r=await fetch(`/api/admin/attendance/users/${id}/schedule`,{headers:headers()});
  const rows=await r.json();
  $("scheduleGrid").innerHTML=rows.map(x=>`<div class="schedule-row" data-day="${x.weekday}"><strong>${x.name}</strong><label><input class="day-enabled" type="checkbox" ${x.enabled?'checked':''}> Trabaja</label><input class="day-start" type="time" value="${x.start_time||''}" ${x.enabled?'':'disabled'}><span>→</span><input class="day-end" type="time" value="${x.end_time||''}" ${x.enabled?'':'disabled'}><input class="day-tolerance" type="number" min="0" max="120" value="${x.tolerance_minutes??5}" title="Tolerancia en minutos"><span>min tolerancia</span></div>`).join("");
  document.querySelectorAll(".schedule-row .day-enabled").forEach(c=>c.addEventListener("change",e=>{const row=e.target.closest(".schedule-row");row.querySelector(".day-start").disabled=!e.target.checked;row.querySelector(".day-end").disabled=!e.target.checked;}));
}

$("saveSchedule").addEventListener("click",async()=>{
  const schedules=[...document.querySelectorAll(".schedule-row")].map(row=>({weekday:Number(row.dataset.day),enabled:row.querySelector(".day-enabled").checked,start_time:row.querySelector(".day-start").value||null,end_time:row.querySelector(".day-end").value||null,tolerance_minutes:Number(row.querySelector(".day-tolerance").value||5)}));
  const r=await fetch(`/api/admin/attendance/users/${scheduleUserId}/schedule`,{method:"PUT",headers:headers(),body:JSON.stringify({schedules})});
  const d=await r.json().catch(()=>({})); if(!r.ok){alert(d.detail||"No se pudo guardar el horario");return;} closeModal("scheduleModal"); alert("Horario guardado correctamente.");
});

$("newUserBtn").addEventListener("click",()=>{editingUserId=null;$("userModalTitle").textContent="Crear usuario";$("userForm").reset();$("password").required=true;$("attendanceEnabled").checked=true;openModal("userModal");});

$("userForm").addEventListener("submit",async e=>{
  e.preventDefault();
  const payload={full_name:$("fullName").value.trim(),email:$("email").value.trim(),role_id:$("roleId").value,active:true,attendance_enabled:$("attendanceEnabled").checked};
  if($("password").value) payload.password=$("password").value;
  if($("attendancePin").value) payload.attendance_pin=$("attendancePin").value;
  let r;
  if(editingUserId) r=await fetch(`/api/admin/users/${editingUserId}`,{method:"PATCH",headers:headers(),body:JSON.stringify(payload)});
  else r=await fetch("/api/admin/users",{method:"POST",headers:headers(),body:JSON.stringify(payload)});
  const d=await r.json().catch(()=>({}));
  if(!r.ok){alert(d.detail||"No se pudo guardar el usuario");return;}
  closeModal("userModal"); await loadUsers();
  if(!editingUserId && d.qr_token){ $("qrName").textContent=payload.full_name;$("qrImage").src=`/api/admin/users/${d.user.id}/qr.svg?ts=${Date.now()}`;$("qrPinText").textContent=d.attendance_pin?`Código personal: ${d.attendance_pin}`:"Código personal configurado anteriormente. Por seguridad no se muestra aquí.";openModal("qrModal"); }
  else alert("Usuario actualizado correctamente.");
});

function printCard(name){
  const src=$("qrImage").src; const pin=$("qrPinText").textContent;
  const w=window.open("","_blank","width=500,height=650");
  w.document.write(`<html><head><title>Tarjeta de asistencia</title><style>body{font-family:Arial;text-align:center;padding:30px}img{width:300px;height:300px}h1{font-size:24px}p{font-size:18px}</style></head><body><h1>🔥 EL IMPERIO DEL BARRIL</h1><h2>${esc(name)}</h2><img src="${src}"><p>${esc(pin)}</p><p>Presentar esta tarjeta en la terminal de asistencia.</p><script>window.onload=()=>{window.print();}</script></body></html>`);w.document.close();
}

loadRoles().then(loadUsers).catch(e=>alert(e.message));

const KIOSK_KEY='imperio_attendance_device';
const $=id=>document.getElementById(id);
let device={}; let stream=null; let scannerTimer=null;
function save(){localStorage.setItem(KIOSK_KEY,JSON.stringify(device));}
function setState(text,ok=false){$('deviceStateText').textContent=text;document.querySelector('.state-dot').classList.toggle('ok',ok);}
async function registerOrRestore(){
  const saved=JSON.parse(localStorage.getItem(KIOSK_KEY)||'null');
  if(saved?.device_uuid && saved?.device_secret){device=saved; await checkStatus(); return;}
  device.device_uuid=crypto.randomUUID();
  const r=await fetch('/api/attendance/devices/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_uuid:device.device_uuid,name:'Terminal de asistencia'})});
  const d=await r.json(); if(!r.ok)throw new Error(d.detail||'No se pudo registrar la terminal');
  device.device_id=d.device_id; device.device_secret=d.pairing_secret||d.device_token; device.pairing_code=d.pairing_code; save();
  if(d.status==='ACTIVE'&&d.device_token){device.device_token=d.device_token;save();activate();return;}
  showPairing(d.pairing_code); pollStatus();
}
function showPairing(code){$('pairingCode').textContent=code||'------';$('pairingOverlay').classList.add('show');setState('Esperando autorización del administrador');}
async function checkStatus(){
  const r=await fetch('/api/attendance/devices/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_uuid:device.device_uuid,device_secret:device.device_secret})});
  const d=await r.json(); if(!r.ok){localStorage.removeItem(KIOSK_KEY);location.reload();return;}
  if(d.status==='ACTIVE'&&d.device_token){device.device_token=d.device_token;save();activate();return true;}
  if(d.status==='REVOKED'){setState('Terminal revocada');$('pairingOverlay').classList.add('show');$('pairingStatus').textContent='Esta terminal fue revocada. Registra nuevamente el dispositivo.';return false;}
  showPairing(d.pairing_code||device.pairing_code);return false;
}
function pollStatus(){clearInterval(scannerTimer);scannerTimer=setInterval(async()=>{const active=await checkStatus();if(active)clearInterval(scannerTimer)},3000);}
function activate(){$('pairingOverlay').classList.remove('show');setState('Terminal autorizada · lista para fichar',true);$('checkBtn').disabled=false;}
function parseQR(raw){raw=String(raw||'').trim();if(raw.startsWith('ELIMPERIO|EMP|'))return raw.split('|')[2];return raw;}
async function checkAttendance(){
  if(!device.device_token){setState('Terminal no autorizada');return;}
  const qr=parseQR($('qrInput').value);const pin=$('pinInput').value.trim();if(!qr||!pin){showResult('Escribe/escanea tu QR y luego tu código personal.','error');return;}
  $('checkBtn').disabled=true;showResult('Verificando...','info');
  const r=await fetch('/api/attendance/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device_token:device.device_token,qr_token:qr,pin})});
  const d=await r.json().catch(()=>({}));$('checkBtn').disabled=false;
  if(!r.ok){showResult(d.detail||'No se pudo registrar la asistencia.','error');$('pinInput').select();return;}
  const label=d.action==='ENTRADA'?'ENTRADA REGISTRADA':'SALIDA REGISTRADA';let extra='';if(d.late_minutes)extra+=`<br>Llegaste ${d.late_minutes} minutos tarde.`;if(d.early_leave_minutes)extra+=`<br>Saliste ${d.early_leave_minutes} minutos antes.`;if(d.overtime_minutes)extra+=`<br>Horas extra: ${Math.floor(d.overtime_minutes/60)}h ${d.overtime_minutes%60}m.`;showResult(`✅ <strong>${label}</strong><br>${d.employee}<br>${d.time}${extra}`,'success');$('pinInput').value='';$('qrInput').value='';}
function showResult(html,type){const el=$('result');el.className=`result-box ${type}`;el.innerHTML=html;setTimeout(()=>{if(type==='success')el.innerHTML='';},8000);}
async function startCamera(){
  if(!('BarcodeDetector' in window)){showResult('Este navegador no tiene lector QR nativo. Puedes escribir el token del QR debajo.','info');return;}
  try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}});$('camera').srcObject=stream;const detector=new BarcodeDetector({formats:['qr_code']});
    const scan=async()=>{if(!stream)return;try{const codes=await detector.detect($('camera'));if(codes.length){$('qrInput').value=parseQR(codes[0].rawValue);showResult('QR detectado. Ahora ingresa tu código personal.','info');$('pinInput').focus();}}catch(_){}requestAnimationFrame(scan)};scan();
  }catch(e){showResult('No se pudo acceder a la cámara. Revisa los permisos del navegador.','error');}
}
$('cameraBtn').onclick=startCamera;$('checkBtn').onclick=checkAttendance;$('pinInput').addEventListener('keydown',e=>{if(e.key==='Enter')checkAttendance()});
function clock(){const d=new Date();$('clock').textContent=d.toLocaleTimeString('es-CO',{hour12:false});}setInterval(clock,1000);clock();registerOrRestore().catch(e=>{setState('Error preparando terminal');showResult(e.message,'error');});

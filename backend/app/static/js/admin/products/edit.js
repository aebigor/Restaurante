const API = "/api/products/";
let inventoryOptions = [];
let productData = null;
const productId = window.location.pathname.split("/").filter(Boolean).pop();

document.addEventListener("DOMContentLoaded", async () => {
    if (!document.getElementById("productForm")) return;
    loadCategories(); loadStations(); initPreview();
    await loadInventoryOptions();
    await loadProduct();
    document.getElementById("addInventoryIngredient")?.addEventListener("click", () => addInventoryRow());
    document.getElementById("productForm").addEventListener("submit", saveProduct);
});
async function loadInventoryOptions(){ const r=await fetch("/api/products/inventory-options"); if(r.ok) inventoryOptions=await r.json(); }
function escapeHtml(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function addInventoryRow(selectedId="",quantity=1){
 const c=document.getElementById("inventoryRecipeRows"); const row=document.createElement("div"); row.className="inventory-recipe-row";
 row.innerHTML=`<select class="recipe-item" required><option value="">Selecciona un insumo del inventario...</option>${inventoryOptions.map(i=>`<option value="${i.id}" ${String(i.id)===String(selectedId)?"selected":""}>${escapeHtml(i.name)} · ${escapeHtml(i.category)} · ${i.quantity} ${escapeHtml(i.unit)} ${i.status!=="OK"?"· ⚠️ "+i.status:""}</option>`).join("")}</select><input class="recipe-qty" type="number" min="0.001" step="0.001" value="${quantity}" required><span class="recipe-unit">unidad</span><button type="button" class="mini-remove">✕</button>`;
 row.querySelector(".mini-remove").onclick=()=>row.remove(); const sel=row.querySelector(".recipe-item"); const unit=row.querySelector(".recipe-unit"); sel.onchange=()=>{const i=inventoryOptions.find(x=>String(x.id)===String(sel.value));unit.textContent=i?.unit||"unidad";}; sel.dispatchEvent(new Event("change")); c.appendChild(row);
}
async function loadProduct(){
 try{
  const r=await fetch(`${API}${productId}`); const d=await r.json(); if(!r.ok) throw Error(d.detail||"No se pudo cargar el producto."); productData=d;
  document.getElementById("name").value=d.name||""; document.getElementById("code").value=d.code||""; document.getElementById("description").value=d.description||""; document.getElementById("price").value=d.price||""; document.getElementById("preparation_time").value=d.preparation_time||0; document.getElementById("category").value=d.category_id; document.getElementById("station").value=d.station_id; document.getElementById("status").value=d.active?"ACTIVE":"HIDDEN";
  (d.inventory_recipe||[]).forEach(r=>addInventoryRow(r.inventory_item_id,r.quantity_per_sale));
 }catch(e){alert(e.message);}
}
function collectRecipe(){return [...document.querySelectorAll(".inventory-recipe-row")].map(r=>({inventory_item_id:r.querySelector(".recipe-item").value,quantity_per_sale:Number(r.querySelector(".recipe-qty").value)})).filter(x=>x.inventory_item_id);}
async function saveProduct(e){
 e.preventDefault(); const categoryId=document.getElementById("category").value, stationId=document.getElementById("station").value; if(!categoryId||!stationId)return alert("Selecciona categoría y estación.");
 const data={name:document.getElementById("name").value.trim(),code:document.getElementById("code").value.trim()||null,description:document.getElementById("description").value.trim()||null,price:Number(document.getElementById("price").value),preparation_time:Number(document.getElementById("preparation_time").value||0),stock:0,category_id:categoryId,station_id:stationId,active:document.getElementById("status").value==="ACTIVE",inventory_recipe:collectRecipe()};
 try{const token=localStorage.getItem("token");const r=await fetch(`${API}${productId}`,{method:"PUT",headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{})},body:JSON.stringify(data)});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.detail||"No se pudo actualizar.");alert("Producto actualizado correctamente.");location.href="/admin/menu/products";}catch(e){alert(e.message);}
}

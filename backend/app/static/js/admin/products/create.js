const API = "/api/products/";
let inventoryOptions = [];

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("productForm");
    if (!form) return;
    loadCategories();
    loadStations();
    loadInventoryOptions();
    initPreview();
    document.getElementById("addInventoryIngredient")?.addEventListener("click", () => addInventoryRow());
    form.addEventListener("submit", saveProduct);
});

async function loadInventoryOptions() {
    try {
        const r = await fetch("/api/products/inventory-options");
        if (!r.ok) throw new Error("No se pudo cargar el inventario.");
        inventoryOptions = await r.json();
    } catch (e) { console.error(e); }
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}

function addInventoryRow(selectedId = "", quantity = 1) {
    const container = document.getElementById("inventoryRecipeRows");
    if (!container) return;
    const row = document.createElement("div");
    row.className = "inventory-recipe-row";
    row.innerHTML = `
        <select class="recipe-item" required>
            <option value="">Selecciona un insumo del inventario...</option>
            ${inventoryOptions.map(i => `<option value="${i.id}" ${String(i.id) === String(selectedId) ? "selected" : ""}>${escapeHtml(i.name)} · ${escapeHtml(i.category)} · ${escapeHtml(i.quantity)} ${escapeHtml(i.unit)} ${i.status !== "OK" ? "· ⚠️ " + i.status : ""}</option>`).join("")}
        </select>
        <input class="recipe-qty" type="number" min="0.001" step="0.001" value="${quantity}" required title="Cantidad que se descuenta por cada venta">
        <span class="recipe-unit">unidad</span>
        <button type="button" class="mini-remove" title="Quitar">✕</button>`;
    row.querySelector(".mini-remove").onclick = () => row.remove();
    const select = row.querySelector(".recipe-item");
    const unit = row.querySelector(".recipe-unit");
    select.onchange = () => {
        const item = inventoryOptions.find(x => String(x.id) === String(select.value));
        unit.textContent = item?.unit || "unidad";
    };
    container.appendChild(row);
    select.dispatchEvent(new Event("change"));
}

function collectRecipe() {
    return [...document.querySelectorAll(".inventory-recipe-row")].map(row => ({
        inventory_item_id: row.querySelector(".recipe-item").value,
        quantity_per_sale: Number(row.querySelector(".recipe-qty").value)
    })).filter(x => x.inventory_item_id);
}

async function saveProduct(e) {
    e.preventDefault();
    const button = document.querySelector('#productForm button[type="submit"]');
    const categoryId = document.getElementById("category").value;
    const stationId = document.getElementById("station").value;
    if (!categoryId) return alert("Selecciona una categoría para el producto.");
    if (!stationId) return alert("Selecciona la estación que atenderá este producto.");

    const data = {
        name: document.getElementById("name").value.trim(),
        code: document.getElementById("code").value.trim() || null,
        description: document.getElementById("description").value.trim() || null,
        price: Number(document.getElementById("price").value),
        preparation_time: Number(document.getElementById("preparation_time").value || 0),
        stock: 0,
        category_id: categoryId,
        station_id: stationId,
        active: document.getElementById("status").value === "ACTIVE",
        inventory_recipe: collectRecipe()
    };
    if (!data.name || data.price <= 0) return alert("Ingresa un nombre y un precio válido.");
    if (data.inventory_recipe.some(x => x.quantity_per_sale <= 0)) return alert("Las cantidades de descuento deben ser mayores que cero.");

    try {
        if (button) { button.disabled = true; button.textContent = "Guardando..."; }
        const token = localStorage.getItem("token");
        const response = await fetch(API, {method:"POST", headers:{"Content-Type":"application/json", ...(token ? {Authorization:`Bearer ${token}`} : {})}, body:JSON.stringify(data)});
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.detail || "No fue posible guardar el producto.");
        alert(data.inventory_recipe.length ? "Producto guardado. El inventario se descontará automáticamente al venderlo." : "Producto guardado correctamente.");
        window.location = "/admin/menu/products";
    } catch (error) {
        console.error(error); alert(error.message || "Error conectando con el servidor.");
        if (button) { button.disabled = false; button.textContent = "Guardar Producto"; }
    }
}

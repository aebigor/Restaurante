const API = "/api/products/";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("productForm");
    if (!form) return;

    loadCategories();
    loadStations();
    initPreview();
    form.addEventListener("submit", saveProduct);
});

async function saveProduct(e) {
    e.preventDefault();

    const button = document.querySelector('#productForm button[type="submit"]');
    const categoryId = document.getElementById("category").value;
    const stationId = document.getElementById("station").value;

    if (!categoryId) {
        alert("Selecciona una categoría para el producto.");
        return;
    }
    if (!stationId) {
        alert("Selecciona la estación que atenderá este producto.");
        return;
    }

    const data = {
        name: document.getElementById("name").value.trim(),
        code: document.getElementById("code").value.trim() || null,
        description: document.getElementById("description").value.trim() || null,
        price: Number(document.getElementById("price").value),
        preparation_time: Number(document.getElementById("preparation_time").value || 0),
        stock: Number(document.getElementById("stock").value || 0),
        category_id: categoryId,
        station_id: stationId,
        active: document.getElementById("status").value === "ACTIVE"
    };

    if (!data.name || data.price <= 0) {
        alert("Ingresa un nombre y un precio válido.");
        return;
    }

    try {
        if (button) {
            button.disabled = true;
            button.textContent = "Guardando...";
        }

        const token = localStorage.getItem("token");
        const response = await fetch(API, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {})
            },
            body: JSON.stringify(data)
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(result.detail || "No fue posible guardar el producto.");
        }

        alert("Producto guardado correctamente.");
        window.location = "/admin/menu/products";
    } catch (error) {
        console.error(error);
        alert(error.message || "Error conectando con el servidor.");
        if (button) {
            button.disabled = false;
            button.textContent = "Guardar Producto";
        }
    }
}

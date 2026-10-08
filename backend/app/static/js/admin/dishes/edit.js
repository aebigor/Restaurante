const API = "/api/dishes/";

function setValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value ?? "";
}

async function apiJson(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    let data = null;
    try { data = await response.json(); } catch (_) {}

    if (!response.ok) {
        throw new Error(data?.detail || `Error ${response.status}`);
    }
    return data;
}

async function loadCategories(selectedId) {
    const select = document.getElementById("category");
    if (!select) return;

    const response = await fetch("/api/categories/active");
    const categories = await response.json();
    if (!response.ok) throw new Error(categories?.detail || "No se pudieron cargar las categorías.");

    select.innerHTML = '<option value="">Seleccione una categoría</option>';
    categories.forEach(category => {
        const option = document.createElement("option");
        option.value = category.id;
        option.textContent = category.name;
        option.selected = String(category.id) === String(selectedId);
        select.appendChild(option);
    });
}

async function loadStations(selectedId) {
    const select = document.getElementById("station");
    if (!select) return;

    const response = await fetch("/api/stations/");
    const stations = await response.json();
    if (!response.ok) throw new Error(stations?.detail || "No se pudieron cargar las estaciones.");

    select.innerHTML = '<option value="">Seleccione una estación</option>';
    (Array.isArray(stations) ? stations : []).forEach(station => {
        const option = document.createElement("option");
        option.value = station.id;
        option.textContent = station.name;
        option.selected = String(station.id) === String(selectedId);
        select.appendChild(option);
    });
}

async function loadDish() {
    const dish = await apiJson(`${API}${encodeURIComponent(DISH_ID)}`);

    setValue("name", dish.name);
    setValue("price", dish.price);
    setValue("portion", dish.portion);
    setValue("preparation_time", dish.preparation_time);
    setValue("category", dish.category_id);
    setValue("station", dish.station_id);

    document.getElementById("available").checked = dish.available !== false;
    document.getElementById("featured").checked = dish.featured === true;

    const preview = document.getElementById("previewImage");
    if (preview && dish.image) preview.src = dish.image;

    // Cargar primero los catálogos y después dejar seleccionado el valor real del plato.
    await Promise.all([
        loadCategories(dish.category_id),
        loadStations(dish.station_id)
    ]);
}

function initPreview() {
    const input = document.getElementById("image");
    const preview = document.getElementById("previewImage");
    if (!input || !preview) return;
    input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (file) preview.src = URL.createObjectURL(file);
    });
}

async function updateDish(event) {
    event.preventDefault();

    const button = document.getElementById("btnGuardar");
    const categoryId = document.getElementById("category").value;
    const stationId = document.getElementById("station").value;

    if (!categoryId) { alert("Selecciona una categoría."); return; }
    if (!stationId) { alert("Selecciona la estación donde realmente se prepara este plato."); return; }

    try {
        button.disabled = true;
        button.textContent = "Guardando...";

        let imageUrl = null;
        const imageFile = document.getElementById("image").files?.[0];

        if (imageFile) {
            const formData = new FormData();
            formData.append("file", imageFile);
            const uploadResponse = await fetch("/api/dishes/upload-image", { method: "POST", body: formData });
            const uploadResult = await uploadResponse.json();
            if (!uploadResponse.ok) throw new Error(uploadResult.detail || "No fue posible subir la imagen.");
            imageUrl = uploadResult.url;
        } else {
            const current = await apiJson(`${API}${encodeURIComponent(DISH_ID)}`);
            imageUrl = current.image || null;
        }

        const data = {
            name: document.getElementById("name").value.trim(),
            price: parseFloat(document.getElementById("price").value),
            category_id: categoryId,
            station_id: stationId,
            preparation_time: parseInt(document.getElementById("preparation_time").value, 10) || 10,
            portion: document.getElementById("portion").value.trim() || "1 porción",
            image: imageUrl,
            featured: document.getElementById("featured").checked,
            available: document.getElementById("available").checked
        };

        if (!data.name) throw new Error("Ingresa el nombre del plato.");
        if (Number.isNaN(data.price) || data.price < 0) throw new Error("Ingresa un precio válido.");

        await apiJson(`${API}${encodeURIComponent(DISH_ID)}`, {
            method: "PUT",
            body: JSON.stringify(data)
        });

        alert("Plato actualizado correctamente.");
        window.location.href = "/admin/dishes";
    } catch (error) {
        console.error("Error actualizando plato:", error);
        alert(error.message || "No fue posible actualizar el plato.");
    } finally {
        button.disabled = false;
        button.textContent = "Guardar cambios";
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    initPreview();
    try {
        await loadDish();
    } catch (error) {
        console.error("Error cargando plato:", error);
        alert(error.message || "No fue posible cargar el plato.");
    }

    document.getElementById("dishForm")?.addEventListener("submit", updateDish);
});

document.addEventListener("DOMContentLoaded", () => {

    loadCategories();
    loadDishes();
    initFilters();

});


// ==========================================================
// VARIABLES
// ==========================================================

let allDishes = [];


// ==========================================================
// CARGAR CATEGORÍAS
// ==========================================================

async function loadCategories() {

    const select = document.getElementById("categoryFilter");

    if (!select) {
        return;
    }

    try {

        const response = await fetch("/api/categories/active");

        if (!response.ok) {
            throw new Error("No se pudieron cargar las categorías.");
        }

        const categories = await response.json();

        categories.forEach(category => {

            const option = document.createElement("option");

            option.value = category.id;
            option.textContent = category.name;

            select.appendChild(option);

        });

    } catch (error) {

        console.error("Error cargando categorías:", error);

    }

}


// ==========================================================
// CARGAR PLATOS
// ==========================================================

async function loadDishes() {

    const grid = document.getElementById("dishGrid");

    if (!grid) {
        return;
    }

    try {

        grid.innerHTML = `
            <div class="loading">
                Cargando platos...
            </div>
        `;

        const response = await fetch("/api/dishes/");

        if (!response.ok) {
            throw new Error("No se pudieron cargar los platos.");
        }

        allDishes = await response.json();

        updateCounters(allDishes);

        renderDishes(allDishes);

    } catch (error) {

        console.error("Error cargando platos:", error);

        grid.innerHTML = `
            <div class="empty-state">
                <h3>No se pudieron cargar los platos</h3>
                <p>Verifique que el servidor esté funcionando correctamente.</p>
            </div>
        `;

    }

}


// ==========================================================
// CONTADORES
// ==========================================================

function updateCounters(dishes) {

    const total = dishes.length;

    const featured = dishes.filter(
        dish => dish.featured === true
    ).length;

    const available = dishes.filter(
        dish => dish.available === true && dish.active !== false
    ).length;


    const totalElement = document.getElementById("totalDishes");

    const featuredElement = document.getElementById("featuredDishes");

    const availableElement = document.getElementById("availableDishes");


    if (totalElement) {
        totalElement.textContent = total;
    }

    if (featuredElement) {
        featuredElement.textContent = featured;
    }

    if (availableElement) {
        availableElement.textContent = available;
    }

}


// ==========================================================
// MOSTRAR PLATOS
// ==========================================================

function renderDishes(dishes) {

    const grid = document.getElementById("dishGrid");

    if (!grid) {
        return;
    }


    if (!dishes.length) {

        grid.innerHTML = `
            <div class="empty-state">

                <h3>No hay platos registrados</h3>

                <p>
                    Cree su primer plato para comenzar a construir la carta.
                </p>

                <a
                    href="/admin/dishes/create"
                    class="btn-primary"
                >
                    + Nuevo Plato
                </a>

            </div>
        `;

        return;
    }


    grid.innerHTML = dishes.map(dish => {

        const image = dish.image
            ? dish.image
            : "/static/img/no-image.png";


        const price = formatPrice(dish.price);


        const portion = dish.portion
            ? dish.portion
            : "Sin especificar";


        const categoryName =
            dish.category_name ||
            dish.category?.name ||
            "Sin categoría";


        const stationName =
            dish.station_name ||
            dish.station?.name ||
            "Sin estación";


        return `

            <article class="dish-card">

                <div class="dish-image-container">

                    <img
                        src="${image}"
                        alt="${escapeHtml(dish.name)}"
                        class="dish-image"
                        onerror="this.onerror=null;this.src='/static/img/no-image.png';"
                    >

                </div>


                <div class="dish-card-content">

                    <div class="dish-card-header">

                        <h3>
                            ${escapeHtml(dish.name)}
                        </h3>

                        ${
                            dish.featured
                            ? `<span class="dish-badge">Destacado</span>`
                            : ""
                        }

                    </div>


                    <div class="dish-category">

                        ${escapeHtml(categoryName)}

                    </div>


                    <div class="dish-price">

                        ${price}

                    </div>


                    <div class="dish-info">

                        <div>
                            <strong>Porción:</strong>
                            ${escapeHtml(portion)}
                        </div>

                        <div>
                            <strong>Estación:</strong>
                            ${escapeHtml(stationName)}
                        </div>

                    </div>


                    <div class="dish-status">

                        ${
                            dish.available
                            ? `<span class="status available">Disponible</span>`
                            : `<span class="status unavailable">No disponible</span>`
                        }

                    </div>


                    <div class="dish-actions">

                        ${
                            dish.model_3d
                            ? `
                                <button
                                    type="button"
                                    class="btn-secondary btn-3d"
                                    onclick="viewDish3D('${dish.id}')"
                                >
                                    Ver en 3D
                                </button>
                            `
                            : `
                                <button
                                    type="button"
                                    class="btn-secondary btn-3d disabled"
                                    disabled
                                    title="El modelo 3D se agregará posteriormente"
                                >
                                    Ver en 3D
                                </button>
                            `
                        }


                        <a
                            href="/admin/dishes/${dish.id}/edit"
                            class="btn-secondary"
                        >
                            Editar
                        </a>


                        <button
                            type="button"
                            class="btn-danger"
                            onclick="deleteDish('${dish.id}')"
                        >
                            Eliminar
                        </button>

                    </div>

                </div>

            </article>

        `;

    }).join("");

}


// ==========================================================
// FILTROS
// ==========================================================

function initFilters() {

    const search = document.getElementById("search");

    const categoryFilter =
        document.getElementById("categoryFilter");


    if (search) {

        search.addEventListener("input", applyFilters);

    }


    if (categoryFilter) {

        categoryFilter.addEventListener("change", applyFilters);

    }

}


// ==========================================================
// APLICAR FILTROS
// ==========================================================

function applyFilters() {

    const searchInput =
        document.getElementById("search");

    const categoryInput =
        document.getElementById("categoryFilter");


    const search =
        searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";


    const category =
        categoryInput
            ? categoryInput.value
            : "";


    const filtered = allDishes.filter(dish => {

        const name =
            (dish.name || "").toLowerCase();


        const matchesSearch =
            !search ||
            name.includes(search);


        const matchesCategory =
            !category ||
            dish.category_id === category;


        return matchesSearch && matchesCategory;

    });


    renderDishes(filtered);

}


// ==========================================================
// VER EN 3D
// ==========================================================

function viewDish3D(dishId) {

    const dish = allDishes.find(
        item => item.id === dishId
    );


    if (!dish) {

        alert("No se encontró el plato.");

        return;

    }


    if (!dish.model_3d) {

        alert(
            "Este plato todavía no tiene un modelo 3D."
        );

        return;

    }


    // ------------------------------------------------------
    // PREPARADO PARA EL FUTURO VISOR 3D
    // ------------------------------------------------------

    alert(
        "El visor 3D se implementará próximamente."
    );

}


// ==========================================================
// ELIMINAR PLATO
// ==========================================================

async function deleteDish(dishId) {

    const confirmed = confirm(
        "¿Está seguro de que desea eliminar este plato?"
    );


    if (!confirmed) {
        return;
    }


    try {

        const response = await fetch(
            `/api/dishes/${dishId}`,
            {
                method: "DELETE"
            }
        );


        if (!response.ok) {

            const errorData =
                await response.json().catch(() => null);

            throw new Error(
                errorData?.detail ||
                "No se pudo eliminar el plato."
            );

        }


        await loadDishes();


    } catch (error) {

        console.error(
            "Error eliminando plato:",
            error
        );


        alert(
            error.message ||
            "No se pudo eliminar el plato."
        );

    }

}


// ==========================================================
// FORMATEAR PRECIO
// ==========================================================

function formatPrice(value) {

    const number = Number(value || 0);

    return number.toLocaleString(
        "es-CO",
        {
            style: "currency",
            currency: "COP",
            maximumFractionDigits: 0
        }
    );

}


// ==========================================================
// SEGURIDAD HTML
// ==========================================================

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }


    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}
const MENU_API = "/api/menu/";
const DISH_API = "/api/dishes/";

let menuId = null;
let menuItems = [];
let dishes = [];


/* ==========================================================
   INICIO
========================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const parts =
            window.location.pathname
                .split("/")
                .filter(Boolean);

        menuId =
            parts[parts.length - 1];


        document
            .getElementById("menu_id")
            .value = menuId;


        document
            .getElementById("saveMenu")
            .addEventListener(
                "click",
                updateMenu
            );


        document
            .getElementById("openDishModal")
            .addEventListener(
                "click",
                openDishModal
            );


        document
            .getElementById("openDishModalEmpty")
            .addEventListener(
                "click",
                openDishModal
            );


        document
            .getElementById("closeDishModal")
            .addEventListener(
                "click",
                closeDishModal
            );


        document
            .querySelector(".menu-modal-overlay")
            .addEventListener(
                "click",
                closeDishModal
            );


        document
            .getElementById("dishSearch")
            .addEventListener(
                "input",
                filterDishes
            );


        loadMenu();

        loadMenuItems();

    }
);


/* ==========================================================
   CARGAR MENÚ
========================================================== */

async function loadMenu() {

    try {

        const response =
            await fetch(
                MENU_API + menuId
            );


        if (!response.ok) {

            throw new Error(
                "No fue posible cargar el menú."
            );

        }


        const menu =
            await response.json();


        document
            .getElementById("title")
            .value =
            menu.title || "";


        document
            .getElementById("description")
            .value =
            menu.description || "";


        document
            .getElementById("display_order")
            .value =
            menu.display_order || 1;


        document
            .getElementById("active")
            .value =
            menu.active
                ? "true"
                : "false";


        document
            .getElementById("menuTitle")
            .textContent =
            menu.title;


        document
            .getElementById("menuDescription")
            .textContent =
            menu.description ||
            "Organiza los platos que estarán disponibles.";

    }
    catch (error) {

        console.error(error);

        alert(
            "No fue posible cargar el menú."
        );

    }

}


/* ==========================================================
   CARGAR PLATOS DEL MENÚ
========================================================== */

async function loadMenuItems() {

    const container =
        document.getElementById(
            "menuItems"
        );


    container.innerHTML = `
        <div class="menu-loading">
            <span class="loading-icon">⏳</span>
            Cargando platos...
        </div>
    `;


    try {

        const response =
            await fetch(
                MENU_API +
                menuId +
                "/items"
            );


        if (!response.ok) {

            throw new Error(
                "No fue posible cargar los platos."
            );

        }


        menuItems =
            await response.json();


        renderMenuItems();

    }
    catch (error) {

        console.error(error);

        container.innerHTML = `
            <div class="menu-error">
                <strong>No fue posible cargar los platos.</strong>
                <span>Verifica la conexión con el servidor.</span>
            </div>
        `;

    }

}


/* ==========================================================
   MOSTRAR PLATOS
========================================================== */

function renderMenuItems() {

    const container =
        document.getElementById(
            "menuItems"
        );


    const empty =
        document.getElementById(
            "emptyItems"
        );


    container.innerHTML = "";


    if (!menuItems.length) {

        empty.style.display =
            "flex";

        return;

    }


    empty.style.display =
        "none";


    menuItems.forEach(
        (item, index) => {

            const dish =
                item.dish;


            container.innerHTML += `

                <article class="menu-item-row">

                    <div class="menu-item-order">

                        ${index + 1}

                    </div>


                    <div class="menu-item-image">

                        <img
                            src="${
                                dish.image ||
                                "/static/img/no-image.png"
                            }"
                            alt="${escapeHtml(
                                dish.name
                            )}"
                        >

                    </div>


                    <div class="menu-item-info">

                        <span class="menu-item-category">

                            ${
                                dish.category_name ||
                                "Plato"
                            }

                        </span>

                        <h3>

                            ${escapeHtml(
                                dish.name
                            )}

                        </h3>

                        <span class="menu-item-portion">

                            ${
                                dish.portion ||
                                "Porción estándar"
                            }

                        </span>

                    </div>


                    <div class="menu-item-price">

                        $${formatPrice(
                            dish.price
                        )}

                    </div>


                    <div class="menu-item-actions">

                        <button
                            type="button"
                            class="item-move"
                            onclick="moveItem(${index}, -1)"
                            title="Subir"
                        >
                            ↑
                        </button>


                        <button
                            type="button"
                            class="item-move"
                            onclick="moveItem(${index}, 1)"
                            title="Bajar"
                        >
                            ↓
                        </button>


                        <button
                            type="button"
                            class="item-remove"
                            onclick="removeItem('${item.id}')"
                        >
                            Quitar
                        </button>

                    </div>

                </article>

            `;

        }
    );

}


/* ==========================================================
   ABRIR MODAL
========================================================== */

async function openDishModal() {

    const modal =
        document.getElementById(
            "dishModal"
        );


    modal.style.display =
        "flex";


    await loadAvailableDishes();

}


/* ==========================================================
   CERRAR MODAL
========================================================== */

function closeDishModal() {

    document
        .getElementById("dishModal")
        .style.display =
        "none";

}


/* ==========================================================
   CARGAR PLATOS DISPONIBLES
========================================================== */

async function loadAvailableDishes() {

    const container =
        document.getElementById(
            "availableDishes"
        );


    container.innerHTML = `
        <div class="menu-loading">
            <span class="loading-icon">⏳</span>
            Cargando platos...
        </div>
    `;


    try {

        const response =
            await fetch(
                DISH_API
            );


        if (!response.ok) {

            throw new Error(
                "No fue posible cargar los platos."
            );

        }


        const allDishes =
            await response.json();


        const usedIds =
            menuItems.map(
                item => item.dish_id
            );


        dishes =
            allDishes.filter(
                dish =>

                    !usedIds.includes(
                        dish.id
                    )

                    &&

                    dish.active !== false

                    &&

                    dish.available !== false

            );


        renderAvailableDishes(
            dishes
        );

    }
    catch (error) {

        console.error(error);

        container.innerHTML = `
            <div class="menu-error">
                No fue posible cargar los platos.
            </div>
        `;

    }

}


/* ==========================================================
   MOSTRAR DISPONIBLES
========================================================== */

function renderAvailableDishes(list) {

    const container =
        document.getElementById(
            "availableDishes"
        );


    container.innerHTML = "";


    if (!list.length) {

        container.innerHTML = `

            <div class="menu-items-empty">

                <div class="empty-icon">
                    🍽
                </div>

                <h3>
                    No hay platos disponibles
                </h3>

                <p>
                    Crea un plato o verifica
                    que esté disponible.
                </p>

            </div>

        `;

        return;

    }


    list.forEach(
        dish => {

            container.innerHTML += `

                <article class="available-dish">

                    <img
                        src="${
                            dish.image ||
                            "/static/img/no-image.png"
                        }"
                        alt="${escapeHtml(
                            dish.name
                        )}"
                    >


                    <div class="available-dish-info">

                        <span class="available-dish-category">

                            ${
                                dish.category_name ||
                                "Plato"
                            }

                        </span>

                        <h3>

                            ${escapeHtml(
                                dish.name
                            )}

                        </h3>

                        <span>

                            ${
                                dish.portion ||
                                "Porción estándar"
                            }

                        </span>

                        <strong>

                            $${formatPrice(
                                dish.price
                            )}

                        </strong>

                    </div>


                    <button
                        type="button"
                        class="btn-add-dish"
                        onclick="addDish('${dish.id}')"
                    >
                        Agregar
                    </button>

                </article>

            `;

        }
    );

}


/* ==========================================================
   AGREGAR PLATO
========================================================== */

async function addDish(dishId) {

    const nextOrder =
        menuItems.length + 1;


    try {

        const response =
            await fetch(
                MENU_API +
                menuId +
                "/items",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        dish_id:
                            dishId,

                        display_order:
                            nextOrder

                    })

                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.detail ||
                "No fue posible agregar el plato."
            );

            return;

        }


        menuItems.push(
            result
        );


        closeDishModal();

        renderMenuItems();

    }
    catch (error) {

        console.error(error);

        alert(
            "No fue posible conectar con el servidor."
        );

    }

}


/* ==========================================================
   QUITAR
========================================================== */

async function removeItem(itemId) {

    const confirmed =
        confirm(
            "¿Quieres quitar este plato del menú?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                MENU_API +
                menuId +
                "/items/" +
                itemId,
                {
                    method: "DELETE"
                }
            );


        const result =
            response.ok
                ? null
                : await response.json();


        if (!response.ok) {

            alert(
                result.detail ||
                "No fue posible quitar el plato."
            );

            return;

        }


        menuItems =
            menuItems.filter(
                item =>
                    item.id !== itemId
            );


        renderMenuItems();

    }
    catch (error) {

        console.error(error);

        alert(
            "No fue posible conectar con el servidor."
        );

    }

}


/* ==========================================================
   MOVER PLATO
========================================================== */

function moveItem(
    index,
    direction
) {

    const newIndex =
        index + direction;


    if (
        newIndex < 0 ||
        newIndex >= menuItems.length
    ) {

        return;

    }


    const temp =
        menuItems[index];


    menuItems[index] =
        menuItems[newIndex];


    menuItems[newIndex] =
        temp;


    menuItems.forEach(
        (item, position) => {

            item.display_order =
                position + 1;

        }
    );


    renderMenuItems();

}


/* ==========================================================
   ACTUALIZAR MENÚ
========================================================== */

async function updateMenu() {

    const button =
        document.getElementById(
            "saveMenu"
        );


    const title =
        document
            .getElementById("title")
            .value
            .trim();


    const description =
        document
            .getElementById("description")
            .value
            .trim();


    const displayOrder =
        parseInt(
            document
                .getElementById(
                    "display_order"
                )
                .value
        ) || 1;


    const active =
        document
            .getElementById(
                "active"
            )
            .value === "true";


    if (!title) {

        alert(
            "El menú necesita un nombre."
        );

        return;

    }


    const data = {

        title: title,

        description:
            description || null,

        /*
         * El menú ya no maneja imágenes.
         * Se mantiene null para conservar
         * compatibilidad con el backend actual.
         */
        cover_image: null,

        display_order:
            displayOrder,

        active:
            active

    };


    try {

        button.disabled = true;

        button.textContent =
            "Guardando...";


        const response =
            await fetch(
                MENU_API +
                menuId,
                {

                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(data)

                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.detail ||
                "No fue posible actualizar el menú."
            );

            return;

        }


        document
            .getElementById("menuTitle")
            .textContent =
            result.title;


        document
            .getElementById("menuDescription")
            .textContent =
            result.description ||
            "Organiza los platos que estarán disponibles.";


        alert(
            "Menú actualizado correctamente."
        );

    }
    catch (error) {

        console.error(error);

        alert(
            "No fue posible conectar con el servidor."
        );

    }
    finally {

        button.disabled = false;

        button.textContent =
            "Guardar cambios";

    }

}


/* ==========================================================
   BUSCAR PLATOS
========================================================== */

function filterDishes() {

    const value =
        document
            .getElementById(
                "dishSearch"
            )
            .value
            .toLowerCase()
            .trim();


    const filtered =
        dishes.filter(
            dish =>

                dish.name
                    .toLowerCase()
                    .includes(value)

        );


    renderAvailableDishes(
        filtered
    );

}


/* ==========================================================
   PRECIO
========================================================== */

function formatPrice(value) {

    return Number(value || 0)
        .toLocaleString(
            "es-CO"
        );

}


/* ==========================================================
   ESCAPE
========================================================== */

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}
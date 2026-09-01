const API = "/api/menu/";
const ITEMS_API = "/api/menu/";

let menus = [];


/* ==========================================================
   INICIO
========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    loadMenus();

    const search =
        document.getElementById("search");

    if (search) {

        search.addEventListener(
            "input",
            filterMenus
        );

    }

});


/* ==========================================================
   CARGAR MENÚS
========================================================== */

async function loadMenus() {

    const grid =
        document.getElementById("menuGrid");

    const empty =
        document.getElementById("emptyMenus");

    grid.innerHTML = `
        <div class="menu-loading">
            <span class="loading-icon">⏳</span>
            Cargando menús...
        </div>
    `;

    try {

        const response =
            await fetch(API);

        if (!response.ok) {

            throw new Error(
                "No fue posible cargar los menús."
            );

        }

        menus =
            await response.json();

        await renderMenus(menus);

    }
    catch (error) {

        console.error(error);

        grid.innerHTML = `
            <div class="menu-error">
                <strong>No fue posible cargar los menús.</strong>
                <span>Verifica la conexión con el servidor.</span>
            </div>
        `;

    }

}


/* ==========================================================
   RENDERIZAR
========================================================== */

async function renderMenus(list) {

    const grid =
        document.getElementById("menuGrid");

    const empty =
        document.getElementById("emptyMenus");

    grid.innerHTML = "";

    if (!list.length) {

        empty.style.display = "flex";

        updateSummary([]);

        return;

    }

    empty.style.display = "none";


    const menusWithItems =
        await Promise.all(

            list.map(async menu => {

                try {

                    const response =
                        await fetch(
                            ITEMS_API +
                            menu.id +
                            "/items"
                        );

                    if (!response.ok) {

                        return {
                            ...menu,
                            itemCount: 0
                        };

                    }

                    const items =
                        await response.json();

                    return {
                        ...menu,
                        itemCount: items.length
                    };

                }
                catch {

                    return {
                        ...menu,
                        itemCount: 0
                    };

                }

            })

        );


    menusWithItems.forEach(menu => {

        grid.innerHTML +=
            createMenuCard(menu);

    });


    updateSummary(
        menusWithItems
    );

}


/* ==========================================================
   TARJETA DEL MENÚ
========================================================== */

function createMenuCard(menu) {

    const statusClass =
        menu.active
            ? "menu-active"
            : "menu-inactive";

    const statusText =
        menu.active
            ? "Activo"
            : "Inactivo";


    return `

        <article class="menu-card">

            <div class="menu-card-top">

                <div class="menu-card-icon">
                    🍽
                </div>

                <span class="menu-status ${statusClass}">
                    ${statusText}
                </span>

            </div>


            <div class="menu-card-body">

                <span class="menu-card-label">
                    MENÚ
                </span>

                <h3>
                    ${escapeHtml(menu.title)}
                </h3>


                <p class="menu-description">

                    ${
                        escapeHtml(
                            menu.description ||
                            "Sin descripción."
                        )
                    }

                </p>


                <div class="menu-card-meta">

                    <div class="menu-meta-item">

                        <span class="meta-icon">
                            🍴
                        </span>

                        <div>

                            <strong>
                                ${menu.itemCount}
                            </strong>

                            <small>
                                ${
                                    menu.itemCount === 1
                                        ? "plato"
                                        : "platos"
                                }
                            </small>

                        </div>

                    </div>


                    <div class="menu-meta-item">

                        <span class="meta-icon">
                            #
                        </span>

                        <div>

                            <strong>
                                ${menu.display_order}
                            </strong>

                            <small>
                                orden
                            </small>

                        </div>

                    </div>

                </div>


                <div class="menu-card-actions">

                    <button
                        type="button"
                        class="btn-manage"
                        onclick="manageMenu('${menu.id}')"
                    >
                        Gestionar platos
                    </button>
                    
                    ${
                        menu.active
                        ? `
                            <button
                                type="button"
                                class="btn-qr"
                                onclick="viewMenuQRs('${menu.id}')"
                            >
                                📱 Ver QRs
                            </button>
                        `
                        : ""
                    }


                    <button
                        type="button"
                        class="btn-edit"
                        onclick="editMenu('${menu.id}')"
                    >
                        Editar
                    </button>

                    <button
                        type="button"
                        class="btn-delete"
                        onclick="deleteMenu('${menu.id}')"
                    >
                        Eliminar
                    </button>

                </div>

            </div>

        </article>

    `;

}


/* ==========================================================
   RESUMEN
========================================================== */

function updateSummary(list) {

    const total =
        document.getElementById("totalMenus");

    const active =
        document.getElementById("activeMenus");

    const published =
        document.getElementById("publishedMenu");


    total.textContent =
        list.length;


    const activeList =
        list.filter(
            menu => menu.active
        );


    active.textContent =
        activeList.length;


    if (activeList.length) {

        published.textContent =
            activeList[0].title;

    }
    else {

        published.textContent =
            "—";

    }

}


/* ==========================================================
   BUSCAR
========================================================== */

function filterMenus() {

    const value =
        document
            .getElementById("search")
            .value
            .toLowerCase()
            .trim();


    const filtered =
        menus.filter(menu => {

            return (

                menu.title
                    .toLowerCase()
                    .includes(value)

                ||

                (menu.description || "")
                    .toLowerCase()
                    .includes(value)

            );

        });


    renderMenus(filtered);

}


/* ==========================================================
   GESTIONAR
========================================================== */

function manageMenu(id) {

    window.location =
        `/admin/menu/edit/${id}`;

}


/* ==========================================================
   EDITAR
========================================================== */

function editMenu(id) {

    window.location =
        `/admin/menu/edit/${id}`;

}


/* ==========================================================
   ELIMINAR
========================================================== */

async function deleteMenu(id) {

    const menu =
        menus.find(
            item => item.id === id
        );


    if (!menu) {
        return;
    }


    const confirmed =
        confirm(
            `¿Deseas eliminar el menú "${menu.title}"?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                API + id,
                {
                    method: "DELETE"
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.detail ||
                "No fue posible eliminar el menú."
            );

            return;

        }


        await loadMenus();

    }
    catch (error) {

        console.error(error);

        alert(
            "No fue posible conectar con el servidor."
        );

    }

}


/* ==========================================================
   ESCAPE HTML
========================================================== */

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}

/* ==========================================================
   VER QRS
========================================================== */

function viewMenuQRs(id) {

    window.location =
        `/admin/menu/${id}/qrs`;

}
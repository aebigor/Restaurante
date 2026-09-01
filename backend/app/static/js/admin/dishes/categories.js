let dishCategories = [];


document.addEventListener("DOMContentLoaded", () => {
    loadCategories();
});


async function loadCategories() {

    const select = document.getElementById("category");

    if (!select) {
        return;
    }

    try {

        const response = await fetch("/api/categories/active");

        if (!response.ok) {
            throw new Error("No fue posible cargar las categorías.");
        }

        dishCategories = await response.json();

        select.innerHTML = `
            <option value="">
                Seleccione una categoría
            </option>
        `;

        dishCategories.forEach(category => {

            const option = document.createElement("option");

            option.value = category.id;

            option.textContent = category.name;

            select.appendChild(option);

        });


        select.addEventListener(
            "change",
            syncCategoryStation
        );


    } catch (error) {

        console.error(
            "Error cargando categorías:",
            error
        );

        select.innerHTML = `
            <option value="">
                Error cargando categorías
            </option>
        `;

    }

}


function syncCategoryStation() {

    const categorySelect =
        document.getElementById("category");

    const stationSelect =
        document.getElementById("station");


    if (!categorySelect || !stationSelect) {
        return;
    }


    const category =
        dishCategories.find(
            category =>
                String(category.id) ===
                String(categorySelect.value)
        );


    if (!category) {

        stationSelect.value = "";

        return;

    }


    if (!category.station_id) {

        stationSelect.value = "";

        alert(
            "Esta categoría no tiene una estación de cocina asignada."
        );

        return;

    }


    stationSelect.value =
        String(category.station_id);

}
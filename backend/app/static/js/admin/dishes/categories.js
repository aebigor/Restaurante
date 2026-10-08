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



// La categoría NO decide la estación del plato.
// La estación se selecciona de forma independiente en el formulario.

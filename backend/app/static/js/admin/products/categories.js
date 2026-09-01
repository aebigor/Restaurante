async function loadCategories() {

    try {

        const response = await fetch("/api/categories/");

        if (!response.ok) {
            throw new Error("No fue posible cargar las categorías.");
        }

        const categories = await response.json();

        const select = document.getElementById("category");

        select.innerHTML = "";

        categories.forEach(category => {

            select.innerHTML += `

                <option value="${category.id}">

                    ${category.icon} ${category.name}

                </option>

            `;

        });

    }

    catch (error) {

        console.error(error);

    }

}
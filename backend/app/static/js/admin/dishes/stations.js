document.addEventListener("DOMContentLoaded", async () => {

    const stationSelect = document.getElementById("station");

    if (!stationSelect) {
        console.error("No existe el selector #station");
        return;
    }

    stationSelect.innerHTML = `
        <option value="">Cargando estaciones...</option>
    `;

    try {

        const response = await fetch("/api/stations/");

        if (!response.ok) {
            throw new Error(
                `Error cargando estaciones: ${response.status}`
            );
        }

        const stations = await response.json();

        stationSelect.innerHTML = `
            <option value="">Seleccione una estación</option>
        `;

        if (!Array.isArray(stations) || stations.length === 0) {

            stationSelect.innerHTML = `
                <option value="">No hay estaciones creadas</option>
            `;

            return;
        }

        stations.forEach(station => {

            const option = document.createElement("option");

            option.value = station.id;

            option.textContent = station.name;

            stationSelect.appendChild(option);

        });

    } catch (error) {

        console.error("Error cargando estaciones:", error);

        stationSelect.innerHTML = `
            <option value="">
                Error al cargar estaciones
            </option>
        `;
    }

});
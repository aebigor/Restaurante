async function loadStations(){

    try{

        const response = await fetch(

            "/api/stations/"

        );

        if(!response.ok){

            throw new Error(

                "No fue posible cargar las estaciones."

            );

        }

        const stations = await response.json();

        const select = document.getElementById(

            "station"

        );

        select.innerHTML = "";

        stations.forEach(station=>{

            select.innerHTML += `

                <option value="${station.id}">

                    ${station.name}

                </option>

            `;

        });

    }

    catch(error){

        console.error(error);

    }

}
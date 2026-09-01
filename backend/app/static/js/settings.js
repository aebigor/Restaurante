const form=document.getElementById("formMesa");

form.addEventListener("submit",async(e)=>{

    e.preventDefault();

    const body={

        name:document.getElementById("name").value,

        capacity:Number(document.getElementById("capacity").value)

    };

    await fetch("/api/tables",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify(body)

    });

    cargarMesas();

});

async function cargarMesas(){

    const r=await fetch("/api/tables");

    const data=await r.json();

    let html="";

    data.forEach(m=>{

        html+=`

        <tr>

            <td>${m.id}</td>

            <td>${m.name}</td>

            <td>${m.capacity}</td>

            <td>${m.status}</td>

        </tr>

        `;

    });

    document.getElementById("tablaMesas").innerHTML=html;

}

cargarMesas();
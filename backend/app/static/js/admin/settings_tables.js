const form = document.getElementById("tableForm");

form.addEventListener("submit", async (e)=>{

    e.preventDefault();

    const data={

        number:Number(document.getElementById("number").value),

        name:document.getElementById("name").value,

        capacity:Number(document.getElementById("capacity").value),

        zone:document.getElementById("zone").value

    };

    const response=await fetch("/tables/",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify(data)

    });

    const result=await response.json();

    alert(result.message);

    form.reset();

});
const form = document.getElementById("loginForm");

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const response = await fetch("/auth/login", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            email: document.getElementById("email").value,

            password: document.getElementById("password").value

        })

    });

    if (!response.ok) {

        alert("Correo o contraseña incorrectos.");

        return;

    }

    const data = await response.json();

    // ==============================
    // Guardar sesión
    // ==============================

    localStorage.setItem(

        "token",

        data.access_token

    );

    localStorage.setItem(

        "user",

        JSON.stringify(data.user)

    );

    // ==============================
    // Redirección por rol
    // ==============================

    switch (data.user.role) {

        case "Administrador":

            window.location.href = "/admin";

            break;

        case "Mesero":

            window.location.href = "/waiter";

            break;

        case "Cocina":

            window.location.href = "/kitchen";

            break;

        case "Caja":

            window.location.href = "/cashier";

            break;

        default:

            alert("El usuario no tiene un rol válido.");

    }

});
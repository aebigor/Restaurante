const form = document.getElementById("loginForm");

if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const message = document.getElementById("mensaje");
        const mode = form.dataset.mode || "customer";

        message.textContent = "Verificando...";

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: document.getElementById("email").value.trim(),
                    password: document.getElementById("password").value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Correo o contraseña incorrectos."
                );
            }

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));

            // Cada cliente conserva su propia sesión, aunque en este mismo
            // navegador también haya pestañas de Caja/Admin/Domiciliario.
            if (data.user.role === "Cliente") {
                localStorage.setItem("customer_token", data.access_token);
                localStorage.setItem("customer_user", JSON.stringify(data.user));
            }

            console.log("USUARIO LOGIN:", data.user);
            console.log("ROL LOGIN:", data.user.role);

            const redirects = {
                Administrador: "/admin",
                Caja: "/cashier",
                Mesero: "/waiter",
                Cocina: "/kitchen",
                Parrilla: "/kitchen",
                Sopas: "/kitchen",
                Domiciliario: "/domiciliario",
                Cliente: "/"
            };

            const personalRoles = [
                "Administrador",
                "Caja",
                "Mesero",
                "Cocina",
                "Parrilla",
                "Sopas",
                "Domiciliario"
            ];

            // Login administrativo
            if (mode === "admin" && !personalRoles.includes(data.user.role)) {
                localStorage.removeItem("token");
                localStorage.removeItem("user");

                throw new Error(
                    `Esta cuenta no tiene un rol de personal autorizado. Rol recibido: ${data.user.role}`
                );
            }

            const next = new URLSearchParams(
                window.location.search
            ).get("next");

            // Cliente normal
            if (
                mode === "customer" &&
                data.user.role === "Cliente" &&
                next === "checkout"
            ) {
                window.location.replace("/checkout");
                return;
            }

            // Todos los demás roles van directamente a su panel
            const destino = redirects[data.user.role];

            if (destino) {
                window.location.replace(destino);
                return;
            }

            throw new Error(
                `No existe un panel configurado para el rol: ${data.user.role}`
            );

        } catch (error) {
            console.error("LOGIN ERROR:", error);
            message.textContent = error.message;
        }
    });
}
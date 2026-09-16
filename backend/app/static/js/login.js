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
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: document.getElementById("email").value.trim(),
                    password: document.getElementById("password").value
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Correo o contraseña incorrectos.");
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            const redirects = {
                Administrador: "/admin", Caja: "/cashier", Mesero: "/waiter",
                Cocina: "/kitchen", Parrilla: "/kitchen", Sopas: "/kitchen", Cliente: "/"
            };
            if (mode === "admin" && !["Administrador","Caja","Mesero","Cocina","Parrilla","Sopas"].includes(data.user.role)) {
                localStorage.removeItem("token"); localStorage.removeItem("user");
                throw new Error("Esta cuenta no tiene un rol de personal autorizado.");
            }
            window.location.href = redirects[data.user.role] || "/";
        } catch (error) {
            message.textContent = error.message;
        }
    });
}

const registerForm = document.getElementById("registerForm");
if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = document.getElementById("mensaje");
        message.textContent = "Creando cuenta...";
        try {
            const response = await fetch("/auth/register", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    full_name: document.getElementById("fullName").value.trim(),
                    email: document.getElementById("email").value.trim(),
                    password: document.getElementById("password").value
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "No fue posible crear la cuenta.");
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            window.location.href = "/";
        } catch (error) { message.textContent = error.message; }
    });
}

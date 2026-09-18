const registerForm = document.getElementById("registerForm");

if (registerForm) {
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    const loginLink = document.getElementById("loginLink");
    if (loginLink && next) loginLink.href = `/login?next=${encodeURIComponent(next)}`;

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = document.getElementById("mensaje");
        const termsAccepted = document.getElementById("termsAccepted").checked;

        if (!termsAccepted) {
            message.textContent = "Debes aceptar los términos y condiciones para crear tu cuenta.";
            return;
        }

        message.textContent = "Creando tu cuenta...";
        message.className = "message";

        try {
            const response = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    full_name: document.getElementById("fullName").value.trim(),
                    email: document.getElementById("email").value.trim(),
                    password: document.getElementById("password").value,
                    terms_accepted: true,
                    marketing_opt_in: document.getElementById("marketingOptIn").checked
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "No fue posible crear la cuenta.");

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            localStorage.setItem("customer_token", data.access_token);
            localStorage.setItem("customer_user", JSON.stringify(data.user));

            const destination = next === "checkout" ? "/checkout" : "/";
            window.location.replace(destination);
        } catch (error) {
            message.textContent = error.message;
            message.className = "message error";
        }
    });
}

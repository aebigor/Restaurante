(function () {
    const user = JSON.parse(localStorage.getItem("user") || "null");
    const token = localStorage.getItem("token");

    if (!token || !user) {
        window.location.href = "/";
        return;
    }

    if (user.role !== "Caja") {
        const routes = {
            Administrador: "/admin",
            Mesero: "/waiter",
            Cocina: "/kitchen",
            Parrilla: "/kitchen",
            Sopas: "/kitchen"
        };
        window.location.href = routes[user.role] || "/";
        return;
    }

    const sidebar = document.getElementById("cashierSidebar");
    const content = document.querySelector(".cashier-content");
    const toggle = document.getElementById("toggleCashierSidebar");
    const menuButton = document.getElementById("cashierMenuButton");
    const logout = document.getElementById("logoutBtn");
    const userName = document.getElementById("cashierUserName");

    if (userName) userName.textContent = user.full_name || "Cajero";

    function toggleSidebar() {
        sidebar?.classList.toggle("collapsed");
        content?.classList.toggle("sidebar-collapsed");
    }

    toggle?.addEventListener("click", toggleSidebar);
    menuButton?.addEventListener("click", toggleSidebar);

    document.querySelectorAll(".cashier-nav-item[href^='#']").forEach((link) => {
        link.addEventListener("click", () => {
            const target = document.querySelector(link.getAttribute("href"));
            target?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    logout?.addEventListener("click", (event) => {
        event.preventDefault();
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.replace("/admin/login");
    });
})();

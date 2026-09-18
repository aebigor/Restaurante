/* ============================================================
   AUTENTICACIÓN MULTISESIÓN
   Cada rol tiene su propio token persistente en localStorage.
   Esto permite tener Admin, Caja, Mesero, Cocina, Domiciliario
   y Cliente abiertos simultáneamente en pestañas del mismo PC.
   ============================================================ */
(function () {
    const ROLE_KEYS = {
        Administrador: "admin",
        Caja: "cashier",
        Mesero: "waiter",
        Cocina: "kitchen_cocina",
        Parrilla: "kitchen_parrilla",
        Sopas: "kitchen_sopas",
        Domiciliario: "delivery",
        Cliente: "customer"
    };

    function keyForRole(role) {
        return ROLE_KEYS[role] || String(role || "guest").toLowerCase().replace(/[^a-z0-9_-]/g, "_");
    }

    // Migra una sesión antigua de sessionStorage una sola vez.
    // Evita que los usuarios tengan que volver a iniciar sesión después
    // de instalar esta versión.
    (function migrateLegacySession() {
        const oldToken = sessionStorage.getItem("token");
        const oldUserRaw = sessionStorage.getItem("user");
        if (!oldToken || !oldUserRaw) return;
        try {
            const oldUser = JSON.parse(oldUserRaw);
            if (oldUser?.role) {
                saveAuth(oldUser, oldToken);
                sessionStorage.removeItem("token");
                sessionStorage.removeItem("user");
            }
        } catch (_) {}
    })();

    function roleCandidates() {
        const path = window.location.pathname;
        if (path.startsWith("/admin")) return ["Administrador"];
        if (path.startsWith("/cashier")) return ["Caja"];
        if (path.startsWith("/waiter")) return ["Mesero"];
        if (path.startsWith("/domiciliario")) return ["Domiciliario"];
        if (path.startsWith("/kitchen")) return ["Cocina", "Parrilla", "Sopas"];
        return ["Cliente"];
    }

    function getAuth(role) {
        const roles = role ? [role] : roleCandidates();
        for (const candidate of roles) {
            const key = keyForRole(candidate);
            const token = localStorage.getItem(`auth_token_${key}`);
            const rawUser = localStorage.getItem(`auth_user_${key}`);
            if (!token || !rawUser) continue;
            try {
                return { token, user: JSON.parse(rawUser), role: candidate, key };
            } catch (_) {}
        }
        return { token: null, user: null, role: null, key: null };
    }

    function saveAuth(user, token) {
        const role = user?.role || "Cliente";
        const key = keyForRole(role);
        localStorage.setItem(`auth_token_${key}`, token);
        localStorage.setItem(`auth_user_${key}`, JSON.stringify(user));
        localStorage.setItem("auth_last_role", role);
    }

    function updateUser(user) {
        const role = user?.role || getAuth().role;
        if (!role) return;
        localStorage.setItem(`auth_user_${keyForRole(role)}`, JSON.stringify(user));
    }

    function clearAuth(role) {
        const auth = getAuth(role);
        if (auth.key) {
            localStorage.removeItem(`auth_token_${auth.key}`);
            localStorage.removeItem(`auth_user_${auth.key}`);
        }
    }

    window.AppAuth = { keyForRole, roleCandidates, getAuth, saveAuth, updateUser, clearAuth };
})();

(() => {
    const root = document.getElementById("imperioChat");
    if (!root) return;

    const launcher = document.getElementById("chatLauncher");
    const panel = document.getElementById("chatPanel");
    const close = document.getElementById("chatClose");
    const messages = document.getElementById("chatMessages");
    const suggestions = document.getElementById("chatSuggestions");
    const form = document.getElementById("chatForm");
    const input = document.getElementById("chatInput");
    const typing = document.getElementById("chatTyping");
    const supportModal = document.getElementById("supportModal");
    const supportMessage = document.getElementById("supportMessage");
    const supportSubmit = document.getElementById("supportSubmit");
    const supportStatus = document.getElementById("supportStatus");

    let greeted = false;
    const history = [];

    const money = value => `$${Number(value).toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;

    function currentToken() {
        return localStorage.getItem("customer_token") || localStorage.getItem("token");
    }

    function openChat() {
        root.classList.add("open");
        panel.setAttribute("aria-hidden", "false");
        launcher.setAttribute("aria-expanded", "true");
        if (!greeted) {
            greeted = true;
            const greeting = "¡Hola! 🔥 Soy el asistente de El Imperio del Barril.\n\nPuedo ayudarte a escoger tu comida, recomendarte platos y orientarte con tu pedido. ¿Qué te provoca hoy?";
            addBot(greeting);
            history.push({ role: "bot", content: greeting });
            renderSuggestions(["Quiero una recomendación", "Algo económico", "Algo para compartir", "Ver destacados"]);
        }
        setTimeout(() => input?.focus(), 100);
    }

    function closeChat() {
        root.classList.remove("open");
        panel.setAttribute("aria-hidden", "true");
        launcher.setAttribute("aria-expanded", "false");
    }

    function addMessage(text, type = "bot") {
        const bubble = document.createElement("div");
        bubble.className = `chat-message ${type}`;
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
    }

    function addBot(text) { addMessage(text, "bot"); }
    function addUser(text) { addMessage(text, "user"); history.push({ role: "user", content: text }); }

    function renderSuggestions(items = []) {
        suggestions.innerHTML = "";
        items.filter(Boolean).slice(0, 5).forEach(label => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = label;
            btn.addEventListener("click", () => {
                if (label === "Solicitar atención humana") {
                    openSupport();
                    return;
                }
                sendMessage(label);
            });
            suggestions.appendChild(btn);
        });
    }

    function addProducts(products = []) {
        products.forEach(product => {
            const card = document.createElement("div");
            card.className = "chat-product";
            card.innerHTML = `
                <img src="${escapeHtml(product.image)}" alt="${escapeHtml(product.name)}" onerror="this.src='/static/img/no-image.png'">
                <div class="chat-product-main">
                    <strong>${escapeHtml(product.name)}</strong>
                    <p>${escapeHtml(product.description || "Una preparación de la casa.")}</p>
                    <span class="chat-product-price">${money(product.price)}</span>
                </div>
                <button class="chat-add" type="button">+ Agregar</button>
            `;
            card.querySelector(".chat-add").addEventListener("click", () => addToCart(product));
            messages.appendChild(card);
        });
        messages.scrollTop = messages.scrollHeight;
    }

    function addToCart(product) {
        const key = "imperio_cart";
        let cart = [];
        try { cart = JSON.parse(localStorage.getItem(key) || "[]"); } catch (_) { cart = []; }
        const existing = cart.find(item => String(item.id) === String(product.id));
        if (existing) existing.qty += 1;
        else cart.push({ id: product.id, name: product.name, price: Number(product.price), image: product.image, qty: 1 });
        localStorage.setItem(key, JSON.stringify(cart));

        const count = document.getElementById("cartCount");
        if (count) count.textContent = cart.reduce((sum, item) => sum + Number(item.qty || 0), 0);
        addBot(`🔥 ¡${product.name} quedó agregado al carrito!`);
        const openCart = document.getElementById("openCart");
        if (openCart) {
            setTimeout(() => openCart.click(), 250);
        }
    }

    async function sendMessage(raw) {
        const text = String(raw || "").trim();
        if (!text) return;
        addUser(text);
        input.value = "";
        renderSuggestions([]);
        typing.hidden = false;
        messages.scrollTop = messages.scrollHeight;

        try {
            const response = await fetch("/api/chatbot/message", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, history: history.slice(-10) })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "No fue posible responder.");
            await delay(300);
            const reply = data.reply || "Estoy aquí para ayudarte.";
            addBot(reply);
            history.push({ role: "bot", content: reply });
            if (Array.isArray(data.products) && data.products.length) addProducts(data.products);
            renderSuggestions(data.suggestions || []);
        } catch (error) {
            addBot("Tuve un pequeño problema para consultar el menú. Puedes intentarlo otra vez o solicitar atención humana.");
            renderSuggestions(["Solicitar atención humana", "Quiero una recomendación"]);
        } finally {
            typing.hidden = true;
            messages.scrollTop = messages.scrollHeight;
        }
    }

    function openSupport() {
        const token = currentToken();
        if (!token) {
            addBot("Para solicitar atención personalizada primero debes ingresar a tu cuenta.");
            setTimeout(() => { window.location.href = "/login?next=/"; }, 900);
            return;
        }
        supportStatus.textContent = "";
        supportStatus.className = "";
        supportMessage.value = "";
        supportModal.hidden = false;
        setTimeout(() => supportMessage.focus(), 50);
    }

    async function submitSupport() {
        const token = currentToken();
        const message = supportMessage.value.trim() || "Necesito hablar con una persona.";
        supportSubmit.disabled = true;
        supportStatus.textContent = "Enviando solicitud…";
        supportStatus.className = "";
        try {
            const response = await fetch("/api/chatbot/support", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ message })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "No se pudo registrar la solicitud.");
            supportStatus.textContent = data.message || "Solicitud registrada.";
            supportStatus.className = "ok";
            addBot(data.message || "✅ Listo. En breve te atenderá uno de nuestros agentes.");
            setTimeout(() => { supportModal.hidden = true; }, 1600);
        } catch (error) {
            supportStatus.textContent = error.message || "No fue posible registrar la solicitud.";
            supportStatus.className = "error";
        } finally {
            supportSubmit.disabled = false;
        }
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>'"]/g, char => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
        }[char]));
    }

    function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

    launcher.addEventListener("click", () => root.classList.contains("open") ? closeChat() : openChat());
    close.addEventListener("click", closeChat);
    form.addEventListener("submit", event => { event.preventDefault(); sendMessage(input.value); });
    supportSubmit.addEventListener("click", submitSupport);
    supportModal.querySelectorAll("[data-close-support]").forEach(el => el.addEventListener("click", () => { supportModal.hidden = true; }));
    document.addEventListener("keydown", event => { if (event.key === "Escape") { closeChat(); supportModal.hidden = true; } });
})();

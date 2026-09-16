(() => {
    const storageKey = "imperio_cart";
    let cart = JSON.parse(localStorage.getItem(storageKey) || "[]");
    const money = value => `$${Number(value).toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;
    const save = () => localStorage.setItem(storageKey, JSON.stringify(cart));

    const count = document.getElementById("cartCount");
    const total = document.getElementById("cartTotal");
    const itemsBox = document.getElementById("cartItems");
    const empty = document.getElementById("cartEmpty");
    const drawer = document.getElementById("cartDrawer");
    const backdrop = document.getElementById("drawerBackdrop");

    function renderCart() {
        const units = cart.reduce((sum, item) => sum + item.qty, 0);
        const totalValue = cart.reduce((sum, item) => sum + Number(item.price) * item.qty, 0);
        count.textContent = units;
        total.textContent = money(totalValue);
        empty.style.display = cart.length ? "none" : "flex";
        itemsBox.style.display = cart.length ? "block" : "none";
        itemsBox.innerHTML = cart.map(item => `
            <div class="cart-row">
                <img src="${item.image}" alt="${item.name}" onerror="this.src='/static/img/no-image.png'">
                <div><h4>${item.name}</h4><small>${money(item.price)} c/u</small><div class="qty"><button data-minus="${item.id}">−</button><strong>${item.qty}</strong><button data-plus="${item.id}">+</button></div></div>
                <strong>${money(Number(item.price) * item.qty)}</strong>
            </div>`).join("");
        save();
    }

    function openCart() { drawer.classList.add("open"); backdrop.classList.add("open"); drawer.setAttribute("aria-hidden", "false"); }
    function closeCart() { drawer.classList.remove("open"); backdrop.classList.remove("open"); drawer.setAttribute("aria-hidden", "true"); }

    document.getElementById("openCart")?.addEventListener("click", openCart);
    document.getElementById("closeCart")?.addEventListener("click", closeCart);
    backdrop?.addEventListener("click", closeCart);

    document.querySelectorAll("[data-add]").forEach(button => {
        button.addEventListener("click", () => {
            const card = button.closest(".dish-card");
            const id = card.dataset.id;
            const existing = cart.find(item => item.id === id);
            if (existing) existing.qty += 1;
            else cart.push({ id, name: card.dataset.name, price: Number(card.dataset.price), image: card.dataset.image, qty: 1 });
            renderCart();
            openCart();
        });
    });

    itemsBox?.addEventListener("click", event => {
        const plus = event.target.closest("[data-plus]");
        const minus = event.target.closest("[data-minus]");
        const id = (plus || minus)?.dataset.plus || (plus || minus)?.dataset.minus;
        if (!id) return;
        const item = cart.find(row => row.id === id);
        if (!item) return;
        if (plus) item.qty += 1;
        if (minus) item.qty -= 1;
        cart = cart.filter(row => row.qty > 0);
        renderCart();
    });

    document.getElementById("checkoutBtn")?.addEventListener("click", () => {
        if (!cart.length) return alert("Agrega al menos un producto al pedido.");
        localStorage.setItem("imperio_pending_order", JSON.stringify(cart));
        window.location.href = "/login?next=checkout";
    });

    document.querySelectorAll(".category-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".category-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const category = tab.dataset.category;
            document.querySelectorAll(".dish-card").forEach(card => {
                card.style.display = category === "all" || card.dataset.category === category ? "block" : "none";
            });
        });
    });

    renderCart();
})();

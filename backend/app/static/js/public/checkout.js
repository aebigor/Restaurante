(() => {
    const token = localStorage.getItem("customer_token") || localStorage.getItem("token");
    let user = null;
    try { user = JSON.parse(localStorage.getItem("customer_user") || localStorage.getItem("user") || "null"); } catch (_) {}

    if (!token || user?.role !== "Cliente") {
        window.location.replace("/login?next=checkout");
        return;
    }

    const cart = JSON.parse(localStorage.getItem("imperio_cart") || "[]");
    const itemsBox = document.getElementById("checkoutItems");
    const totalBox = document.getElementById("checkoutTotal");
    const deliveryFeeBox = document.getElementById("deliveryFee");
    const message = document.getElementById("checkoutMessage");
    const customerBox = document.getElementById("customerBox");
    const money = value => `$${Number(value).toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;

    customerBox.innerHTML = `<strong>${user.full_name}</strong><span>${user.email}</span><small>Cliente registrado</small>`;

    if (!cart.length) {
        itemsBox.innerHTML = `<div class="empty-checkout">Tu carrito está vacío. <a href="/">Volver al menú</a></div>`;
        document.getElementById("placeOrder").disabled = true;
        return;
    }

    itemsBox.innerHTML = cart.map(item => `
        <div class="checkout-item">
            <img src="${item.image || "/static/img/no-image.png"}" alt="${item.name}" onerror="this.src='/static/img/no-image.png'">
            <div><strong>${item.name}</strong><span>${item.qty} × ${money(item.price)}</span></div>
            <b>${money(Number(item.price) * item.qty)}</b>
        </div>`).join("");

    const subtotal = cart.reduce((sum, item) => sum + Number(item.price) * item.qty, 0);
    const subtotalBox=document.getElementById('checkoutSubtotal'); if(subtotalBox) subtotalBox.textContent=money(subtotal);
    const orderType = document.getElementById("orderType");
    function updateTotals(){ const fee=orderType.value==='DOMICILIO'?7000:0; if(deliveryFeeBox) deliveryFeeBox.textContent=money(fee); totalBox.textContent=money(subtotal+fee); }
    updateTotals();

    const deliveryFields = document.getElementById("deliveryFields");
    const deliveryAddress = document.getElementById("deliveryAddress");
    const deliveryPhone = document.getElementById("deliveryPhone");

    function toggleDelivery() {
        const delivery = orderType.value === "DOMICILIO";
        deliveryFields.hidden = !delivery;
        deliveryAddress.required = delivery;
        deliveryPhone.required = delivery;
        updateTotals();
    }
    orderType.addEventListener("change", toggleDelivery);
    toggleDelivery();

    document.getElementById("placeOrder").addEventListener("click", async () => {
        const button = document.getElementById("placeOrder");
        button.disabled = true;
        button.textContent = "ENVIANDO...";
        message.textContent = "";

        try {
            const response = await fetch("/orders/customer", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    order_type: orderType.value,
                    notes: document.getElementById("orderNotes").value.trim() || null,
                    delivery_address: deliveryAddress.value.trim() || null,
                    delivery_phone: deliveryPhone.value.trim() || null,
                    items: cart.map(item => ({ dish_id: item.id, quantity: item.qty }))
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "No fue posible enviar el pedido.");

            localStorage.removeItem("imperio_cart");
            localStorage.removeItem("imperio_pending_order");
            document.querySelector(".checkout-card").innerHTML = `
                <div class="success-icon">✓</div>
                <span class="eyebrow">PEDIDO RECIBIDO</span>
                <h1>¡Gracias, ${user.full_name.split(" ")[0]}!</h1>
                <p>Tu pedido quedó recibido y ahora pasa a Caja para confirmación antes de entrar a cocina.</p>
                <div class="order-number">Pedido<br><strong>#${data.order_id.slice(0, 8).toUpperCase()}</strong></div>
                <p>Subtotal: <strong>${money(data.subtotal)}</strong></p><p>Domicilio: <strong>${money(data.delivery_fee)}</strong></p><p>Total: <strong>${money(data.total)}</strong></p>${data.delivery_code ? `<div class="delivery-code"><b>🔐 Código de entrega</b><strong>${data.delivery_code}</strong><small>Entrégaselo al domiciliario. Lo necesitará para confirmar la entrega.</small></div>` : ''}
                <a class="place-order success-link" href="/mis-pedidos">VER SEGUIMIENTO</a>`;
        } catch (error) {
            message.textContent = error.message;
            button.disabled = false;
            button.textContent = "CONFIRMAR PEDIDO";
        }
    });
})();

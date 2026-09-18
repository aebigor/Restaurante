(() => {
  const token = localStorage.getItem('customer_token') || localStorage.getItem('token');
  let user = null;
  try {
    user = JSON.parse(localStorage.getItem('customer_user') || localStorage.getItem('user') || 'null');
  } catch (_) {}

  if (!token || user?.role !== 'Cliente') {
    location.replace('/login');
    return;
  }

  const list = document.getElementById('ordersList');
  const msg = document.getElementById('ordersMessage');
  const modal = document.getElementById('trackingModal');
  const mapElement = document.getElementById('courierMap');
  const trackingTitle = document.getElementById('trackingTitle');
  const trackingStatus = document.getElementById('trackingStatus');
  const trackingUpdated = document.getElementById('trackingUpdated');

  const money = v => new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0
  }).format(Number(v || 0));

  const esc = v => String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

  const mins = s => s == null ? '—' : `${Math.max(0, Math.round(s / 60))} min`;

  function elapsed(start, end = null) {
    if (!start) return null;
    return Math.max(0, Math.floor(((end ? new Date(end) : new Date()) - new Date(start)) / 1000));
  }

  function logout() {
    localStorage.removeItem('customer_token');
    localStorage.removeItem('customer_user');
    try {
      if (JSON.parse(localStorage.getItem('user') || 'null')?.role === 'Cliente') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    } catch (_) {}
    location.replace('/');
  }

  document.getElementById('logoutCustomer')?.addEventListener('click', logout);

  // ============================================================
  // MAPA DEL DOMICILIARIO
  // ============================================================
  let map = null;
  let courierMarker = null;
  let accuracyCircle = null;
  let selectedOrderId = null;
  let trackingTimer = null;
  let lastLocation = null;

  function initMap() {
    if (map || !window.L || !mapElement) return;

    map = L.map(mapElement, {
      zoomControl: true,
      attributionControl: true
    }).setView([4.7110, -74.0721], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
  }

  function updateMap(location) {
    if (!location || location.latitude == null || location.longitude == null) {
      trackingStatus.textContent = 'El domiciliario aún no ha enviado su ubicación.';
      trackingUpdated.textContent = 'Sin ubicación disponible';
      return;
    }

    initMap();
    if (!map) return;

    const lat = Number(location.latitude);
    const lng = Number(location.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    lastLocation = [lat, lng];
    const point = [lat, lng];

    if (!courierMarker) {
      courierMarker = L.marker(point).addTo(map).bindPopup('🛵 Domiciliario');
      courierMarker.openPopup();
    } else {
      courierMarker.setLatLng(point);
    }

    if (accuracyCircle) {
      accuracyCircle.setLatLng(point);
      if (location.accuracy != null) accuracyCircle.setRadius(Number(location.accuracy));
    } else {
      accuracyCircle = L.circle(point, {
        radius: Number(location.accuracy || 50)
      }).addTo(map);
    }

    map.setView(point, Math.max(map.getZoom(), 15), { animate: true });

    trackingStatus.textContent = '🟢 Ubicación del domiciliario actualizada';
    trackingUpdated.textContent = location.recorded_at
      ? `Última actualización: ${new Date(location.recorded_at).toLocaleTimeString('es-CO')}`
      : 'Ubicación recibida';
  }

  async function loadTracking(orderId, firstOpen = false) {
    try {
      const response = await fetch(`/orders/customer/${encodeURIComponent(orderId)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (_) {
        throw new Error(`HTTP ${response.status}: respuesta no válida del servidor.`);
      }

      if (!response.ok) throw new Error(data.detail || 'No fue posible consultar la ubicación.');

      if (data.order_type !== 'DOMICILIO') {
        trackingStatus.textContent = 'Este pedido no es un domicilio.';
        return;
      }

      if (!data.courier_id) {
        trackingStatus.textContent = data.status === 'READY'
          ? 'Tu pedido está listo y está esperando que un domiciliario lo tome.'
          : 'Todavía no hay un domiciliario asignado.';
        trackingUpdated.textContent = 'Esperando asignación';
        return;
      }

      updateMap(data.courier_location);

      if (firstOpen && data.courier_location) {
        setTimeout(() => map?.invalidateSize(), 100);
      }
    } catch (error) {
      trackingStatus.textContent = error.message || 'No fue posible actualizar el mapa.';
    }
  }

  function openTracking(order) {
    if (order.order_type !== 'DOMICILIO') return;

    selectedOrderId = order.id;
    trackingTitle.textContent = `Pedido #${order.short_id}`;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');

    initMap();
    setTimeout(() => map?.invalidateSize(), 100);

    loadTracking(selectedOrderId, true);

    clearInterval(trackingTimer);
    trackingTimer = setInterval(() => {
      if (selectedOrderId) loadTracking(selectedOrderId);
    }, 5000);
  }

  function closeTracking() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    selectedOrderId = null;
    clearInterval(trackingTimer);
    trackingTimer = null;
  }

  document.getElementById('closeTracking')?.addEventListener('click', closeTracking);
  document.getElementById('centerCourier')?.addEventListener('click', () => {
    if (map && lastLocation) map.setView(lastLocation, 17, { animate: true });
  });

  modal?.addEventListener('click', event => {
    if (event.target === modal) closeTracking();
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && modal?.classList.contains('open')) closeTracking();
  });

  // ============================================================
  // PEDIDOS DEL CLIENTE
  // ============================================================
  async function load() {
    try {
      msg.textContent = 'Actualizando…';

      const response = await fetch('/orders/customer', {
        headers: { Authorization: `Bearer ${token}` }
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (_) {
        throw new Error(`HTTP ${response.status}: respuesta no válida del servidor.`);
      }

      if (!response.ok) throw new Error(data.detail || 'No fue posible consultar tus pedidos.');

      msg.textContent = '';
      render(data);
    } catch (error) {
      msg.textContent = error.message;
    }
  }

  function render(orders) {
    if (!orders.length) {
      list.innerHTML = '<div class="empty-orders">Aún no tienes pedidos.<br><a href="/">Ir al menú</a></div>';
      return;
    }

    const steps = ['PENDING_CASHIER', 'OPEN', 'PREPARING', 'READY', 'OUT_FOR_DELIVERY'];

    list.innerHTML = orders.map(order => {
      let idx = steps.indexOf(order.status);
      if (['DELIVERED_PENDING_PAYMENT', 'DELIVERED', 'CLOSED'].includes(order.status)) idx = 4;
      if (order.status === 'CANCELLED') idx = -1;

      const delivery = order.order_type === 'DOMICILIO';
      const prep = mins(order.prep_seconds);
      const ride = delivery && order.dispatched_at
        ? (order.delivery_seconds != null ? mins(order.delivery_seconds) : mins(elapsed(order.dispatched_at)))
        : null;

      let eta = '';
      if (delivery && !['DELIVERED', 'CLOSED', 'CANCELLED'].includes(order.status)) {
        if (order.status === 'OUT_FOR_DELIVERY') {
          eta = ride
            ? `🛵 Tiempo en manos del repartidor: <b>${ride}</b>`
            : '🛵 Repartidor en camino';
        } else {
          eta = '🕐 Llegada estimada: <b>15–25 min</b>';
        }
      }

      if (order.status === 'DELIVERED_PENDING_PAYMENT') {
        eta = '📦 Entregado al cliente · pendiente de cierre en Caja';
      }

      if (order.status === 'CLOSED') {
        eta = `✅ Cerrado por Caja${order.payment_method ? ` · ${esc(order.payment_method)}` : ''}`;
      }

      const codeBox = delivery && order.delivery_code
        ? `<div class="delivery-code-box">
             <div>
               <span class="code-label">🔐 CÓDIGO DE ENTREGA</span>
               <strong class="delivery-code">${esc(order.delivery_code)}</strong>
               <small>Muéstrale este código al domiciliario cuando llegue tu pedido.</small>
             </div>
             <button type="button" class="copy-code" data-copy-code="${esc(order.delivery_code)}">Copiar</button>
           </div>`
        : '';

      const trackingButton = delivery && order.courier_id && !['DELIVERED', 'CLOSED', 'CANCELLED'].includes(order.status)
        ? `<button type="button" class="tracking-button" data-track-order="${esc(order.id)}">🗺️ Ver ubicación del domiciliario</button>`
        : '';

      return `<article class="order-card ${delivery ? 'is-delivery' : ''}" data-order-id="${esc(order.id)}">
        <div class="order-head">
          <div>
            <h2>Pedido #${esc(order.short_id)}</h2>
            <div class="order-meta">${delivery ? 'Domicilio' : 'Para recoger'} · ${new Date(order.created_at).toLocaleString('es-CO')}</div>
          </div>
          <span class="status-pill">${esc(order.status_label)}</span>
        </div>

        <div class="progress">
          ${[0, 1, 2, 3, 4].map(i => `<span class="step ${i <= idx ? 'active' : ''}"></span>`).join('')}
        </div>

        <div class="items">
          ${order.items.map(item => `<div class="item"><span>${item.quantity} × ${esc(item.name)}</span><strong>${money(item.total)}</strong></div>`).join('')}
        </div>

        ${delivery ? `<div class="delivery-box">
          <strong>Entrega:</strong> ${esc(order.delivery_address || 'Sin dirección')}<br>
          <strong>Teléfono:</strong> ${esc(order.delivery_phone || 'Sin teléfono')}<br>
          <strong>Domicilio:</strong> ${money(order.delivery_fee)}
        </div>` : ''}

        ${codeBox}
        ${trackingButton}

        <div class="timing-box">
          <span>⏱️ Cocina: <b>${prep}</b></span>
          ${eta ? `<span>${eta}</span>` : ''}
          ${order.status === 'OUT_FOR_DELIVERY' && order.dispatched_at
            ? `<span>⏱️ En ruta: <b>${mins(elapsed(order.dispatched_at, order.courier_delivered_at))}</b></span>`
            : ''}
        </div>

        <div class="order-bottom">
          <div><span>Total</span><div class="order-total">${money(order.total)}</div></div>
          <div>${
            order.status === 'READY' && delivery
              ? 'Esperando repartidor'
              : order.status === 'OUT_FOR_DELIVERY'
                ? '🚚 En camino'
                : order.status === 'DELIVERED_PENDING_PAYMENT'
                  ? '✓ Entregado'
                  : 'Seguimiento activo'
          }</div>
        </div>
      </article>`;
    }).join('');

    list.querySelectorAll('[data-track-order]').forEach(button => {
      button.addEventListener('click', () => {
        const order = orders.find(x => String(x.id) === String(button.dataset.trackOrder));
        if (order) openTracking(order);
      });
    });

    list.querySelectorAll('[data-copy-code]').forEach(button => {
      button.addEventListener('click', async () => {
        const code = button.dataset.copyCode;
        try {
          await navigator.clipboard.writeText(code);
          const original = button.textContent;
          button.textContent = '✓ Copiado';
          setTimeout(() => { button.textContent = original; }, 1500);
        } catch (_) {
          alert(`Código de entrega: ${code}`);
        }
      });
    });
  }

  document.getElementById('refreshOrders')?.addEventListener('click', load);
  load();
  setInterval(load, 5000);
})();

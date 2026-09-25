const form = document.getElementById("tableEditForm");

async function loadTable() {
    const response = await fetch(`/api/tables/${window.TABLE_ID}`);
    const table = await response.json();
    if (!response.ok) throw new Error(table.detail || "No se pudo cargar la mesa.");
    document.getElementById("number").value = table.number;
    document.getElementById("name").value = table.name || "";
    document.getElementById("capacity").value = table.capacity;
    document.getElementById("zone").value = table.zone || "Salón";
    document.getElementById("prepayment_required").value = String(Boolean(table.prepayment_required));
    document.getElementById("comanda_print_priority").value = String(table.comanda_print_priority || 2);
    document.getElementById("active").checked = Boolean(table.active);
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector(".btn-save");
    button.disabled = true;
    try {
        const response = await fetch(`/api/tables/${window.TABLE_ID}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                number: Number(document.getElementById("number").value),
                name: document.getElementById("name").value.trim(),
                capacity: Number(document.getElementById("capacity").value),
                zone: document.getElementById("zone").value,
                active: document.getElementById("active").checked,
                prepayment_required: document.getElementById("prepayment_required").value === "true",
                comanda_print_priority: Number(document.getElementById("comanda_print_priority").value)
            })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || result.message || "No se pudo actualizar la mesa.");
        alert("Mesa actualizada correctamente.");
        window.location.href = "/admin/tables";
    } catch (error) {
        alert(error.message);
    } finally {
        button.disabled = false;
    }
});

loadTable().catch(error => alert(error.message));

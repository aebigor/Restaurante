from __future__ import annotations

import base64
import os
import re
import urllib.parse
import urllib.request
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.chatbot.model import SupportRequest
from app.modules.chatbot.schemas import ChatMessage, SupportRequestCreate
from app.modules.dishes.model import Dish
from app.modules.menu.model import Menu
from app.modules.menu_items.model import MenuItem

# IMPORTANTE: este módulo se publica bajo /api/chatbot.
router = APIRouter(prefix="/api/chatbot", tags=["Asistente del Imperio"])


STOPWORDS = {
    "quiero", "quieres", "para", "algo", "una", "unos", "unas", "con", "que",
    "del", "los", "las", "por", "favor", "dame", "busco", "tengo", "me", "mi",
    "hoy", "ver", "dime", "puedes", "puede", "como", "ser", "somos", "personas",
}


def _money(value) -> str:
    return f"${float(value):,.0f}".replace(",", ".")


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    return re.sub(r"[^a-z0-9 ]", " ", text)


def _active_dishes(db: Session):
    menu = (
        db.query(Menu)
        .filter(Menu.active.is_(True))
        .order_by(Menu.display_order.asc(), Menu.created_at.desc())
        .first()
    )
    if not menu:
        return []
    return (
        db.query(Dish)
        .join(MenuItem, MenuItem.dish_id == Dish.id)
        .filter(
            MenuItem.menu_id == menu.id,
            MenuItem.active.is_(True),
            Dish.active.is_(True),
            Dish.available.is_(True),
        )
        .order_by(MenuItem.display_order.asc(), MenuItem.id.asc())
        .all()
    )


def _dish_payload(dish: Dish) -> dict:
    return {
        "id": str(dish.id),
        "name": dish.name,
        "price": float(dish.price),
        "description": dish.description or "Una preparación de la casa.",
        "category": dish.category.name if dish.category else "Menú",
        "image": dish.image or "/static/img/no-image.png",
        "featured": bool(dish.featured),
    }


def _haystack(dish: Dish) -> str:
    return _normalize(" ".join([
        dish.name or "",
        dish.description or "",
        dish.ingredients or "",
        dish.portion or "",
        dish.category.name if dish.category else "",
    ]))


def _find_matches(message: str, dishes: list[Dish]) -> list[Dish]:
    text = _normalize(message)
    tokens = {t for t in text.split() if len(t) >= 3 and t not in STOPWORDS}
    scored = []
    for dish in dishes:
        haystack = _haystack(dish)
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, dish))
    scored.sort(key=lambda item: (-item[0], -int(item[1].featured), float(item[1].price)))
    return [dish for _, dish in scored[:4]]


def _extract_people(text: str) -> int | None:
    normalized = _normalize(text)
    patterns = [
        r"(?:somos|para|seremos|vamos a ser)\s+(\d+)",
        r"(\d+)\s+(?:personas|personas somos|personas seremos)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return max(1, min(int(match.group(1)), 20))
    return None


def _extract_budget(text: str) -> int | None:
    normalized = _normalize(text).replace(".", "")
    match = re.search(r"(?:\$\s*)?(\d{2,3}(?:\s*000)?|\d{4,7})\s*(?:pesos|cop)?", normalized)
    if not match:
        return None
    raw = match.group(1).replace(" ", "")
    try:
        value = int(raw)
        if value < 1000 and len(raw) <= 3:
            value *= 1000
        return value
    except ValueError:
        return None


def _recommend(dishes: list[Dish], intent: str, people: int | None = None, budget: int | None = None) -> list[Dish]:
    if not dishes:
        return []

    if intent == "featured":
        return [d for d in dishes if d.featured][:4] or dishes[:4]

    if intent == "cheap":
        candidates = sorted(dishes, key=lambda d: Decimal(str(d.price)))
        if budget:
            inside = [d for d in candidates if float(d.price) <= budget]
            if inside:
                return inside[:4]
        return candidates[:4]

    if intent == "spicy":
        candidates = [d for d in dishes if (d.spicy_level or 0) > 0 or "picante" in _haystack(d)]
        return candidates[:4] or dishes[:3]

    if intent == "share":
        candidates = [d for d in dishes if d.portion and any(x in _normalize(d.portion) for x in ["2", "3", "4", "familiar", "grande", "compartir"])]
        candidates += [d for d in dishes if "picada" in _haystack(d) or "combo" in _haystack(d)]
        unique = []
        seen = set()
        for d in candidates:
            if d.id not in seen:
                seen.add(d.id)
                unique.append(d)
        return unique[:4] or dishes[:4]

    return [d for d in dishes if d.featured][:3] or dishes[:3]


def _intent(text: str) -> str:
    t = _normalize(text)
    if any(x in t for x in ["hablar con una persona", "hablar con alguien", "asesor", "humano", "soporte", "persona real", "agente"]):
        return "human"
    if any(x in t for x in ["hola", "buenas", "hey", "buenos dias", "buenas tardes", "buenas noches"]):
        return "greeting"
    if any(x in t for x in ["gracias", "muchas gracias", "perfecto", "listo"]):
        return "thanks"
    if any(x in t for x in ["picante", "aji", "fuerte", "picoso"]):
        return "spicy"
    if any(x in t for x in ["compartir", "familia", "para todos", "varias personas", "somos "]):
        return "share"
    if any(x in t for x in ["economico", "barato", "barata", "poco dinero", "presupuesto", "plata", "ahorrar"]):
        return "cheap"
    if any(x in t for x in ["destacado", "favorito", "popular", "recomendacion", "recomienda", "sugiere", "mejor"]):
        return "featured"
    if any(x in t for x in ["bebida", "gaseosa", "jugo", "cerveza", "tomar"]):
        return "drink"
    if any(x in t for x in ["pedido", "orden", "carrito", "comprar", "agregar"]):
        return "order"
    return "search"


def _gemini_reply(history: list[dict], message: str, dishes: list[Dish]) -> str | None:
    """Respuesta conversacional opcional usando Gemini API sin instalar SDK.
    Si no hay API key o falla el servicio, el bot usa su motor local de respaldo.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    menu_lines = []
    for dish in dishes[:80]:
        category = dish.category.name if dish.category else "Menú"
        menu_lines.append(f"- {dish.name} | ${float(dish.price):,.0f} COP | {category} | {dish.description or ''}")
    menu_text = "\n".join(menu_lines)
    history_lines = []
    for item in (history or [])[-8:]:
        role = "Cliente" if item.get("role") == "user" else "Asistente"
        history_lines.append(f"{role}: {item.get('content', '')}")
    history_text = "\n".join(history_lines)

    system = """Eres el vendedor virtual de El Imperio del Barril, un restaurante en Bogotá.
Habla en español colombiano, natural, amable, breve y con personalidad. Tu objetivo es ayudar al cliente a elegir y comprar.
NUNCA inventes platos, precios, ingredientes, promociones ni disponibilidad: usa exclusivamente el menú proporcionado.
Si faltan datos para recomendar, haz UNA pregunta útil (personas, presupuesto o gusto).
Si el cliente pide hablar con una persona, indícale que puede solicitar atención humana.
No digas que eres una IA salvo que te lo pregunten. No uses markdown pesado.
"""
    prompt = f"""{system}

MENÚ ACTIVO:
{menu_text}

CONVERSACIÓN RECIENTE:
{history_text}

MENSAJE ACTUAL DEL CLIENTE:
{message}

Responde como un pequeño vendedor humano del restaurante. Si puedes recomendar, menciona máximo 3 opciones del menú y termina con una pregunta que ayude a continuar la venta."""

    import json
    payload = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.65, "maxOutputTokens": 300},
    }).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(str(part.get("text", "")) for part in parts).strip()
        return text or None
    except Exception:
        return None


def _reply_for_history(history: list[dict], message: str, dishes: list[Dish]):
    current = _intent(message)
    people = _extract_people(message)
    budget = _extract_budget(message)
    recent = " ".join(str(item.get("content", "")) for item in history[-6:] if isinstance(item, dict))
    context = _normalize(recent + " " + message)

    # Conversación guiada: si el cliente dio número de personas, úsalo en la recomendación.
    if people is not None and current in {"search", "share", "featured"}:
        current = "share"

    if budget is not None and current == "search":
        current = "cheap"

    if current == "greeting":
        return (
            "¡Hola! 🔥 Soy el asistente del Imperio del Barril. Estoy aquí para ayudarte a elegir y comprar. "
            "Cuéntame qué te provoca, cuántas personas son o cuánto quieres gastar.",
            ["Quiero una recomendación", "Algo económico", "Algo para compartir", "Algo picante"],
            [],
        )

    if current == "thanks":
        return ("¡Con gusto! ❤️ Cuando quieras seguimos. ¿Quieres que te recomiende algo más o hablamos con un asesor?", ["Quiero otra recomendación", "Hablar con una persona"], [])

    if current == "human":
        return (
            "Claro. Voy a pasar tu solicitud a una persona de nuestro equipo. Escríbeme en el siguiente formulario qué necesitas y te avisaremos cuando esté registrada.",
            ["Solicitar atención humana"], [],
        )

    if current == "drink":
        matches = [d for d in dishes if any(x in _haystack(d) for x in ["bebida", "gaseosa", "jugo", "refresco", "limonada"])]
        return ("🥤 Claro. Estas son las bebidas que encontré disponibles en la carta actual:", ["Quiero una recomendación", "Algo económico"], [_dish_payload(d) for d in (matches[:4] or dishes[:4])])

    if current == "order":
        return ("¡De una! Puedes agregar los platos que quieras al carrito desde aquí. Si me dices cuántas personas son, también puedo ayudarte a calcular una combinación.", ["Somos 2 personas", "Somos 4 personas", "Quiero una recomendación"], [])

    if current == "featured":
        matches = _recommend(dishes, "featured")
        return ("🔥 Te muestro algunas opciones destacadas del menú activo. Si me dices cuántas personas son, te ayudo a escoger mejor:", ["Somos 2 personas", "Somos 4 personas", "Algo económico"], [_dish_payload(d) for d in matches])

    if current == "cheap":
        matches = _recommend(dishes, "cheap", budget=budget)
        suffix = f" dentro de unos ${budget:,.0f}".replace(",", ".") if budget else ""
        return (f"💰 Si quieres cuidar el presupuesto{suffix}, estas opciones encajan con lo que me dijiste:", ["Algo para compartir", "Ver destacados", "Hablar con una persona"], [_dish_payload(d) for d in matches])

    if current == "share":
        matches = _recommend(dishes, "share", people=people)
        if people:
            return (f"🍗 Perfecto, son {people} personas. Te propongo estas opciones para compartir. Si me dices tu presupuesto, puedo afinar la recomendación:", ["Mi presupuesto es 50000", "Algo económico", "Ver destacados"], [_dish_payload(d) for d in matches])
        return ("🍗 Para compartir te puedo ayudar mejor si me dices cuántas personas son. ¿Son 2, 4 o más?", ["Somos 2 personas", "Somos 4 personas", "Somos más de 4"], [_dish_payload(d) for d in matches])

    if current == "spicy":
        matches = _recommend(dishes, "spicy")
        return ("🌶️ Si buscas algo con picante, estas son las opciones que la carta marca como picantes:", ["Algo suave", "Algo económico", "Ver destacados"], [_dish_payload(d) for d in matches])

    matches = _find_matches(message, dishes)
    if matches:
        return (f"Entendí que buscas algo relacionado con «{message.strip()}». Encontré estas opciones en el menú actual. ¿Quieres que te ayude a escoger según personas o presupuesto?", ["Somos 2 personas", "Somos 4 personas", "Algo económico", "Hablar con una persona"], [_dish_payload(d) for d in matches])

    return (
        "Quiero ayudarte a encontrar exactamente lo que buscas 😊. Puedes decirme, por ejemplo, «somos 4», «algo económico», «quiero algo picante», «una picada» o el nombre de un plato.",
        ["Quiero una recomendación", "Algo económico", "Algo para compartir", "Algo picante"],
        [],
    )


@router.post("/message")
def chat_message(data: ChatMessage, db: Session = Depends(get_db)):
    message = data.message.strip()
    dishes = _active_dishes(db)
    if not dishes:
        return {"reply": "En este momento no tengo un menú activo para recomendarte. Si quieres, puedo ayudarte con soporte.", "suggestions": ["Hablar con una persona"], "products": []}

    reply, suggestions, products = _reply_for_history(data.history or [], message, dishes)
    ai_reply = _gemini_reply(data.history or [], message, dishes)
    if ai_reply:
        reply = ai_reply
    return {"reply": reply, "suggestions": suggestions, "products": products}


def _send_whatsapp(text: str) -> tuple[bool, str | None]:
    """Envía el aviso a soporte mediante Twilio sin exponer credenciales al navegador."""
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    sender = os.getenv("TWILIO_WHATSAPP_FROM")
    recipient = os.getenv("SUPPORT_WHATSAPP_TO", "whatsapp:+573174875518")
    if not sid or not token or not sender:
        return False, "TWILIO_NOT_CONFIGURED"

    if not sender.startswith("whatsapp:"):
        sender = f"whatsapp:{sender}"
    if not recipient.startswith("whatsapp:"):
        recipient = f"whatsapp:{recipient}"

    payload = urllib.parse.urlencode({"From": sender, "To": recipient, "Body": text}).encode()
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    request = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=payload,
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            return True, body
    except Exception as exc:
        return False, str(exc)


@router.post("/support")
def create_support_request(
    data: SupportRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user or not getattr(current_user, "is_active", True):
        raise HTTPException(status_code=401, detail="Tu sesión no está activa.")

    message = data.message.strip() or "Necesito hablar con una persona."
    request = SupportRequest(
        customer_id=current_user.id,
        customer_name=current_user.full_name,
        customer_email=current_user.email,
        message=message,
        status="PENDING",
        handled=False,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    whatsapp_text = (
        "🔥 NUEVA SOLICITUD DE SOPORTE — EL IMPERIO DEL BARRIL\n\n"
        f"Cliente: {current_user.full_name}\n"
        f"Correo: {current_user.email or 'No registrado'}\n"
        f"Solicitud: {message}\n"
        f"ID: {request.id}\n\n"
        "El cliente está esperando atención humana."
    )
    sent, detail = _send_whatsapp(whatsapp_text)

    if sent:
        response_message = "✅ Listo. Tu mensaje fue enviado a nuestro equipo. En breve te atenderá uno de nuestros agentes."
    else:
        response_message = "✅ Tu solicitud quedó registrada. En breve te atenderá uno de nuestros agentes."

    return {
        "ok": True,
        "message": response_message,
        "request_id": str(request.id),
        "whatsapp_sent": sent,
        "whatsapp_detail": None if sent else detail,
    }


def _require_admin(current_user):
    role = current_user.role.name if getattr(current_user, "role", None) else None
    if role != "Administrador":
        raise HTTPException(status_code=403, detail="Solo Administración puede gestionar soporte.")


@router.get("/support")
def list_support_requests(status: str = "PENDING", db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin(current_user)
    query = db.query(SupportRequest)
    if status != "ALL":
        query = query.filter(SupportRequest.status == status)
    rows = query.order_by(SupportRequest.created_at.desc()).limit(100).all()
    return {"items": [{
        "id": str(row.id), "customer_id": str(row.customer_id) if row.customer_id else None,
        "customer_name": row.customer_name, "customer_email": row.customer_email,
        "message": row.message, "status": row.status, "handled": row.handled,
        "created_at": row.created_at,
    } for row in rows]}


@router.patch("/support/{request_id}/close")
def close_support_request(request_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin(current_user)
    row = db.query(SupportRequest).filter(SupportRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    row.status = "RESOLVED"
    row.handled = True
    db.commit()
    return {"ok": True, "message": "Solicitud marcada como atendida."}

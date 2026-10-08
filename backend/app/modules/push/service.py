import base64
from app.core.config import settings

def _private_key_pem():
    raw=(settings.WEB_PUSH_VAPID_PRIVATE_KEY or "").strip()
    if not raw:return None
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        b=base64.urlsafe_b64decode(raw+"="*(-len(raw)%4)); key=ec.derive_private_key(int.from_bytes(b,"big"),ec.SECP256R1())
        return key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    except Exception:return None

def vapid_public_key():
    raw=(settings.WEB_PUSH_VAPID_PRIVATE_KEY or "").strip()
    if not raw:return None
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        b=base64.urlsafe_b64decode(raw+"="*(-len(raw)%4)); key=ec.derive_private_key(int.from_bytes(b,"big"),ec.SECP256R1())
        public=key.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)
        return base64.urlsafe_b64encode(public).rstrip(b"=").decode()
    except Exception:return None

def send_push(subscription,payload):
    if not settings.WEB_PUSH_VAPID_PRIVATE_KEY or not settings.WEB_PUSH_VAPID_EMAIL:return False
    try:
        from pywebpush import webpush
        webpush({"endpoint":subscription.endpoint,"keys":{"p256dh":subscription.p256dh,"auth":subscription.auth}},data=payload,vapid_private_key=_private_key_pem(),vapid_claims={"sub":settings.WEB_PUSH_VAPID_EMAIL})
        return True
    except Exception as exc:
        print(f"[WEB PUSH] no enviado: {exc}")
        return False

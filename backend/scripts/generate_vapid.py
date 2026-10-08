import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

key=ec.generate_private_key(ec.SECP256R1())
private=key.private_numbers().private_value.to_bytes(32,"big")
public=key.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)
enc=lambda b:base64.urlsafe_b64encode(b).rstrip(b"=").decode()
print("WEB_PUSH_VAPID_PRIVATE_KEY="+enc(private))
print("WEB_PUSH_VAPID_PUBLIC_KEY="+enc(public))

from uuid import UUID

from decimal import Decimal

from datetime import datetime

from pydantic import BaseModel, Field


# ==========================================================
# ABRIR CAJA
# ==========================================================

class CashRegisterOpen(BaseModel):

    opening_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )


# ==========================================================
# CERRAR CAJA
# ==========================================================

class CashRegisterClose(BaseModel):

    closing_amount: Decimal = Field(
        ge=0
    )


# ==========================================================
# COBRO
# ==========================================================



# ==========================================================
# CORRECCIÓN ADMINISTRATIVA DEL ARQUEO
# ==========================================================

class CashRegisterClosingEdit(BaseModel):

    closing_amount: Decimal = Field(
        ge=0
    )

    reason: str = Field(
        min_length=5,
        max_length=255
    )


class CashPaymentCreate(BaseModel):

    session_id: UUID

    method: str

    received_amount: Decimal = Field(
        ge=0
    )

    reference: str | None = None

    # Obligatorio para mesas con pago anticipado.
    confirmation_code: str | None = None


# ==========================================================
# RESPUESTA DE PAGO
# ==========================================================

class PrepaymentCodeVerify(BaseModel):

    session_id: UUID
    confirmation_code: str = Field(min_length=6, max_length=6)


# ==========================================================
# RESPUESTA DE PAGO
# ==========================================================

class CashPaymentResponse(BaseModel):

    id: UUID

    session_id: UUID

    method: str

    amount: Decimal

    received_amount: Decimal

    change_amount: Decimal

    reference: str | None

    paid_at: datetime

    class Config:

        from_attributes = True

# ==========================================================
# RETIRO DE DINERO
# ==========================================================

class CashRegisterWithdrawalCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    recipient_name: str = Field(min_length=2, max_length=150)
    recipient_document: str = Field(min_length=4, max_length=50)
    reason: str | None = Field(default=None, max_length=255)

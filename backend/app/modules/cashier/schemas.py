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

class CashPaymentCreate(BaseModel):

    session_id: UUID

    method: str

    received_amount: Decimal = Field(
        ge=0
    )

    reference: str | None = None


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
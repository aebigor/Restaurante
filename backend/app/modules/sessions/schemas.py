from pydantic import BaseModel


class SessionCreate(BaseModel):

    table_number: int

    people: int


class SessionResponse(BaseModel):

    id: int

    table_id: int

    people: int

    status: str

    class Config:

        from_attributes = True
        
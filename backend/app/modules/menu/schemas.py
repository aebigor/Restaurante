from uuid import UUID

from pydantic import BaseModel


class MenuBase(BaseModel):

    title: str

    description: str | None = None

    cover_image: str | None = None

    display_order: int = 1

    active: bool = True


class MenuCreate(MenuBase):

    pass


class MenuUpdate(MenuBase):

    pass


class MenuResponse(MenuBase):

    id: UUID

    slug: str

    class Config:

        from_attributes = True
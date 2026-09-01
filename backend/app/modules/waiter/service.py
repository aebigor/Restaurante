from sqlalchemy.orm import Session, joinedload

from app.modules.menu.model import Menu
from app.modules.menu_items.model import MenuItem


class WaiterService:

    def get_active_menu(
        self,
        db: Session
    ):

        menu = (
            db.query(Menu)
            .options(
                joinedload(Menu.items)
                .joinedload(MenuItem.dish)
                .joinedload("category")
            )
            .filter(
                Menu.active == True
            )
            .order_by(
                Menu.display_order.asc()
            )
            .first()
        )

        if not menu:
            return None

        categories = {}

        for item in menu.items:

            if not item.active:
                continue

            dish = item.dish

            if not dish:
                continue

            category = dish.category

            if not category:
                continue

            category_id = str(category.id)

            if category_id not in categories:

                categories[category_id] = {
                    "id": category_id,
                    "name": category.name,
                    "dishes": []
                }

            categories[category_id]["dishes"].append({
                "id": str(dish.id),
                "name": dish.name,
                "description": getattr(
                    dish,
                    "description",
                    None
                ),
                "price": float(dish.price),
                "portion": getattr(
                    dish,
                    "portion",
                    None
                ),
                "calories": getattr(
                    dish,
                    "calories",
                    None
                ),
                "image": getattr(
                    dish,
                    "image",
                    None
                ),
                "preparation_time": getattr(
                    dish,
                    "preparation_time",
                    None
                ),
                "spicy_level": getattr(
                    dish,
                    "spicy_level",
                    None
                ),
                "featured": getattr(
                    dish,
                    "featured",
                    False
                ),
                "available": getattr(
                    dish,
                    "available",
                    True
                ),
                "menu_item_id": str(item.id),
                "display_order": item.display_order
            })

        return {
            "id": str(menu.id),
            "title": menu.title,
            "slug": menu.slug,
            "description": menu.description,
            "categories": list(categories.values())
        }
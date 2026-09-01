"""
=========================================================
Seed de Estaciones

Se ejecuta una sola vez.

Crea automáticamente las estaciones
principales del restaurante.
=========================================================
"""

from app.core.database import SessionLocal

from app.modules.stations.model import Station
# Registrar modelos relacionados
import app.modules.products.model
import app.modules.categories.model


def run():

    db = SessionLocal()

    stations = [

        {

            "name": "Parrilla",

            "printer_name": "PRINTER_PARRILLA",

            "color": "#e74c3c"

        },

        {

            "name": "Cocina",

            "printer_name": "PRINTER_COCINA",

            "color": "#3498db"

        },

        {

            "name": "Bar",

            "printer_name": "PRINTER_BAR",

            "color": "#2ecc71"

        },

        {

            "name": "Postres",

            "printer_name": "PRINTER_POSTRES",

            "color": "#f1c40f"

        }

    ]

    for item in stations:

        exists = (

            db.query(Station)

            .filter(

                Station.name == item["name"]

            )

            .first()

        )

        if exists:

            continue

        db.add(

            Station(

                name=item["name"],

                printer_name=item["printer_name"],

                color=item["color"]

            )

        )

    db.commit()

    db.close()

    print("✔ Estaciones creadas correctamente.")


if __name__ == "__main__":

    run()
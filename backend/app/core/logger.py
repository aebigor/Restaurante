"""
=========================================================
Logger Global

Centraliza todos los registros del sistema.

Toda la aplicación utilizará este logger.

Nunca utilizar print() para depuración.

=========================================================
"""

import logging

logger = logging.getLogger("CriptonixERP")

logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

console = logging.StreamHandler()

console.setFormatter(formatter)

logger.addHandler(console)
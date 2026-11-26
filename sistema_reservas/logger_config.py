"""Configuración centralizada de logging con archivo rotativo."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DIRECTORIO_LOGS = Path(__file__).resolve().parent.parent / "logs"
ARCHIVO_LOG = DIRECTORIO_LOGS / "sistema_reservas.log"
FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """Configura el logger del paquete una sola vez, con archivo y consola."""
    logger = logging.getLogger("sistema_reservas")
    if logger.handlers:
        return logger

    DIRECTORIO_LOGS.mkdir(parents=True, exist_ok=True)
    logger.setLevel(nivel)
    logger.propagate = False

    formato = logging.Formatter(FORMATO, datefmt=FORMATO_FECHA)

    archivo = RotatingFileHandler(
        ARCHIVO_LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    archivo.setFormatter(formato)
    archivo.setLevel(nivel)

    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    consola.setLevel(logging.WARNING)

    logger.addHandler(archivo)
    logger.addHandler(consola)
    logger.info("Sistema de logging inicializado en %s", ARCHIVO_LOG)
    return logger

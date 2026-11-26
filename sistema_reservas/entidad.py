"""Entidad base del dominio: identidad y contrato común."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sistema_reservas.excepciones import DatosInvalidosError


class Entidad(ABC):
    """Clase abstracta para todas las entidades del sistema."""

    def __init__(self, identificador: str) -> None:
        self._identificador = self._validar_identificador(identificador)
        self._creado_en = datetime.now()

    @staticmethod
    def _validar_identificador(identificador: str) -> str:
        if not isinstance(identificador, str):
            raise DatosInvalidosError("El identificador debe ser una cadena de texto.")
        limpio = identificador.strip()
        if not limpio:
            raise DatosInvalidosError("El identificador no puede estar vacío.")
        if len(limpio) > 40:
            raise DatosInvalidosError("El identificador no puede superar los 40 caracteres.")
        return limpio

    @property
    def identificador(self) -> str:
        """Identificador único de la entidad."""
        return self._identificador

    @property
    def creado_en(self) -> datetime:
        """Fecha y hora de creación de la entidad."""
        return self._creado_en

    @abstractmethod
    def descripcion(self) -> str:
        """Devuelve una descripción legible de la entidad."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a un diccionario."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(identificador={self._identificador!r})"

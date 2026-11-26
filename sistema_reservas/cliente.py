"""Cliente del sistema con validaciones y encapsulación."""

from __future__ import annotations

import re
from typing import Any

from sistema_reservas.entidad import Entidad
from sistema_reservas.excepciones import ClienteInvalidoError

_PATRON_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_PATRON_DOCUMENTO = re.compile(r"^\d{6,10}$")
_PATRON_TELEFONO = re.compile(r"^\+?\d{7,15}$")
_PATRON_NOMBRE = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$"
)


class Cliente(Entidad):
    """Persona que contrata servicios; valida sus datos antes de asignarlos."""

    def __init__(self, nombre: str, email: str, documento: str, telefono: str) -> None:
        documento_normalizado = self._validar_documento(documento)
        super().__init__(f"CLI-{documento_normalizado}")
        self._nombre = self._validar_nombre(nombre)
        self._email = self._validar_email(email)
        self._telefono = self._validar_telefono(telefono)
        self._documento = documento_normalizado

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_nombre(valor)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        self._email = self._validar_email(valor)

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = self._validar_telefono(valor)

    @property
    def documento(self) -> str:
        return self._documento

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        if not isinstance(nombre, str):
            raise ClienteInvalidoError("El nombre debe ser una cadena de texto.")
        limpio = " ".join(nombre.split())
        if not 3 <= len(limpio) <= 60:
            raise ClienteInvalidoError(
                "El nombre debe tener entre 3 y 60 caracteres.", detalle=repr(nombre)
            )
        if not _PATRON_NOMBRE.fullmatch(limpio):
            raise ClienteInvalidoError(
                "El nombre solo admite letras, espacios, apóstrofos y guiones.",
                detalle=repr(nombre),
            )
        return limpio

    @staticmethod
    def _validar_email(email: str) -> str:
        if not isinstance(email, str):
            raise ClienteInvalidoError("El correo debe ser una cadena de texto.")
        limpio = email.strip().lower()
        if len(limpio) > 80 or not _PATRON_EMAIL.fullmatch(limpio):
            raise ClienteInvalidoError(
                "El correo electrónico no tiene un formato válido.", detalle=repr(email)
            )
        return limpio

    @staticmethod
    def _validar_documento(documento: str) -> str:
        if not isinstance(documento, str):
            raise ClienteInvalidoError("El documento debe ser una cadena de texto.")
        limpio = documento.strip()
        if not _PATRON_DOCUMENTO.fullmatch(limpio):
            raise ClienteInvalidoError(
                "El documento debe contener entre 6 y 10 dígitos.", detalle=repr(documento)
            )
        return limpio

    @staticmethod
    def _validar_telefono(telefono: str) -> str:
        if not isinstance(telefono, str):
            raise ClienteInvalidoError("El teléfono debe ser una cadena de texto.")
        limpio = re.sub(r"[\s()-]", "", telefono)
        if not _PATRON_TELEFONO.fullmatch(limpio):
            raise ClienteInvalidoError(
                "El teléfono debe tener entre 7 y 15 dígitos, con prefijo + opcional.",
                detalle=repr(telefono),
            )
        return limpio

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> "Cliente":
        """Construye un cliente a partir de un diccionario, encadenando errores de datos."""
        if not isinstance(datos, dict):
            raise ClienteInvalidoError("Los datos del cliente deben ser un diccionario.")
        try:
            return cls(
                nombre=datos["nombre"],
                email=datos["email"],
                documento=datos["documento"],
                telefono=datos["telefono"],
            )
        except KeyError as exc:
            raise ClienteInvalidoError(
                "Faltan datos obligatorios del cliente.",
                detalle=f"campo ausente: {exc.args[0]}",
            ) from exc

    def descripcion(self) -> str:
        return f"Cliente {self._nombre} (documento {self._documento}, correo {self._email})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": type(self).__name__,
            "identificador": self._identificador,
            "nombre": self._nombre,
            "email": self._email,
            "documento": self._documento,
            "telefono": self._telefono,
            "creado_en": self._creado_en.isoformat(timespec="seconds"),
        }

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Cliente):
            return NotImplemented
        return self._identificador == otro._identificador

    def __hash__(self) -> int:
        return hash(self._identificador)

    def __str__(self) -> str:
        return f"{self._nombre} <{self._email}>"

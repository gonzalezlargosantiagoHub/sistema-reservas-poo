"""Servicios ofrecidos: reserva de salas, alquiler de equipos y asesorías."""

from __future__ import annotations

import logging
from abc import abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Any

from sistema_reservas.entidad import Entidad
from sistema_reservas.excepciones import (
    CapacidadExcedidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
    StockInsuficienteError,
)

LOGGER = logging.getLogger(__name__)
_CENTAVOS = Decimal("0.01")


class Servicio(Entidad):
    """Servicio contratable; define el contrato polimórfico de cálculo de costos."""

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa_base: Decimal | str | int | float,
        *,
        activo: bool = True,
    ) -> None:
        super().__init__(identificador)
        self._nombre = self._validar_texto(nombre, "nombre")
        self._tarifa_base = self._validar_tarifa(tarifa_base)
        if not isinstance(activo, bool):
            raise ServicioInvalidoError("El estado del servicio debe ser booleano.")
        self._activo = activo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> Decimal:
        return self._tarifa_base

    @property
    def activo(self) -> bool:
        return self._activo

    def activar(self) -> None:
        self._activo = True
        LOGGER.info("Servicio %s activado", self._identificador)

    def desactivar(self) -> None:
        self._activo = False
        LOGGER.warning("Servicio %s desactivado", self._identificador)

    @staticmethod
    def _validar_texto(valor: str, campo: str, *, minimo: int = 3, maximo: int = 60) -> str:
        if not isinstance(valor, str):
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser una cadena de texto.")
        limpio = " ".join(valor.split())
        if not minimo <= len(limpio) <= maximo:
            raise ServicioInvalidoError(
                f"El campo '{campo}' debe tener entre {minimo} y {maximo} caracteres.",
                detalle=repr(valor),
            )
        return limpio

    @staticmethod
    def _validar_tarifa(tarifa: Decimal | str | int | float) -> Decimal:
        try:
            valor = Decimal(str(tarifa))
        except (InvalidOperation, ValueError) as exc:
            raise ServicioInvalidoError(
                "La tarifa debe ser un número válido.", detalle=repr(tarifa)
            ) from exc
        if not valor.is_finite() or valor <= 0:
            raise ServicioInvalidoError("La tarifa debe ser un número positivo.")
        return valor.quantize(_CENTAVOS)

    @staticmethod
    def _validar_entero(valor: Any, campo: str, *, maximo: int | None = None) -> int:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser un entero.")
        if valor < 1:
            raise ServicioInvalidoError(f"El campo '{campo}' debe ser mayor o igual a 1.")
        if maximo is not None and valor > maximo:
            raise ServicioInvalidoError(
                f"El campo '{campo}' no puede superar {maximo}.", detalle=f"valor={valor}"
            )
        return valor

    def _verificar_disponibilidad(self) -> None:
        if not self._activo:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._nombre}' está desactivado.",
                detalle=self._identificador,
            )

    @abstractmethod
    def calcular_costo(self, **parametros: Any) -> Decimal:
        """Calcula el costo del servicio según los parámetros de la reserva."""

    def descripcion(self) -> str:
        estado = "activo" if self._activo else "inactivo"
        return f"{self._nombre} (tarifa base S/ {self._tarifa_base}, {estado})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": type(self).__name__,
            "identificador": self._identificador,
            "nombre": self._nombre,
            "tarifa_base": str(self._tarifa_base),
            "activo": self._activo,
            "creado_en": self._creado_en.isoformat(timespec="seconds"),
        }


class ReservaSala(Servicio):
    """Sala física con capacidad máxima y recargo por ocupación alta."""

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa_hora: Decimal | str | int | float,
        capacidad: int,
    ) -> None:
        super().__init__(identificador, nombre, tarifa_hora)
        self._capacidad = self._validar_entero(capacidad, "capacidad", maximo=200)

    @property
    def capacidad(self) -> int:
        return self._capacidad

    def calcular_costo(self, *, horas: int, asistentes: int) -> Decimal:
        self._verificar_disponibilidad()
        horas = self._validar_entero(horas, "horas", maximo=12)
        asistentes = self._validar_entero(asistentes, "asistentes")
        if asistentes > self._capacidad:
            raise CapacidadExcedidaError(
                f"La sala '{self._nombre}' admite hasta {self._capacidad} asistentes.",
                detalle=f"solicitados={asistentes}",
            )
        costo = self._tarifa_base * horas
        if asistentes > self._capacidad * Decimal("0.8"):
            costo *= Decimal("1.10")
        return costo.quantize(_CENTAVOS)

    def descripcion(self) -> str:
        return f"Sala '{self._nombre}' para {self._capacidad} personas (S/ {self._tarifa_base}/hora)"

    def to_dict(self) -> dict[str, Any]:
        datos = super().to_dict()
        datos["capacidad"] = self._capacidad
        return datos


class AlquilerEquipo(Servicio):
    """Equipo con stock limitado y descuento por alquiler de tres o más unidades."""

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa_diaria: Decimal | str | int | float,
        stock: int,
    ) -> None:
        super().__init__(identificador, nombre, tarifa_diaria)
        self._stock = self._validar_entero(stock, "stock", maximo=500)

    @property
    def stock(self) -> int:
        return self._stock

    def calcular_costo(self, *, dias: int, cantidad: int) -> Decimal:
        self._verificar_disponibilidad()
        dias = self._validar_entero(dias, "días", maximo=365)
        cantidad = self._validar_entero(cantidad, "cantidad")
        if cantidad > self._stock:
            raise StockInsuficienteError(
                f"El equipo '{self._nombre}' solo tiene {self._stock} unidades disponibles.",
                detalle=f"solicitadas={cantidad}",
            )
        costo = self._tarifa_base * dias * cantidad
        if cantidad >= 3:
            costo *= Decimal("0.95")
        return costo.quantize(_CENTAVOS)

    def descripcion(self) -> str:
        return f"Equipo '{self._nombre}' con {self._stock} unidades (S/ {self._tarifa_base}/día)"

    def to_dict(self) -> dict[str, Any]:
        datos = super().to_dict()
        datos["stock"] = self._stock
        return datos


class AsesoriaEspecializada(Servicio):
    """Asesoría que puede exigir certificación y recarga las sesiones extensas."""

    def __init__(
        self,
        identificador: str,
        nombre: str,
        tarifa_hora: Decimal | str | int | float,
        especialidad: str,
        *,
        requiere_certificacion: bool = True,
    ) -> None:
        super().__init__(identificador, nombre, tarifa_hora)
        self._especialidad = self._validar_texto(especialidad, "especialidad")
        if not isinstance(requiere_certificacion, bool):
            raise ServicioInvalidoError("'requiere_certificacion' debe ser booleano.")
        self._requiere_certificacion = requiere_certificacion

    @property
    def especialidad(self) -> str:
        return self._especialidad

    @property
    def requiere_certificacion(self) -> bool:
        return self._requiere_certificacion

    def calcular_costo(self, *, horas: int, certificado: bool = False) -> Decimal:
        self._verificar_disponibilidad()
        horas = self._validar_entero(horas, "horas", maximo=8)
        if not isinstance(certificado, bool):
            raise ServicioInvalidoError("'certificado' debe ser booleano.")
        if self._requiere_certificacion and not certificado:
            raise ServicioNoDisponibleError(
                f"La asesoría '{self._nombre}' exige un asesor certificado.",
                detalle=f"especialidad={self._especialidad}",
            )
        costo = self._tarifa_base * horas
        if horas >= 4:
            costo *= Decimal("1.15")
        return costo.quantize(_CENTAVOS)

    def descripcion(self) -> str:
        exigencia = "con certificación" if self._requiere_certificacion else "sin certificación"
        return (
            f"Asesoría '{self._nombre}' de {self._especialidad} "
            f"({exigencia}, S/ {self._tarifa_base}/hora)"
        )

    def to_dict(self) -> dict[str, Any]:
        datos = super().to_dict()
        datos["especialidad"] = self._especialidad
        datos["requiere_certificacion"] = self._requiere_certificacion
        return datos

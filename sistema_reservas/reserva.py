"""Reserva de servicios con ciclo de vida controlado."""

from __future__ import annotations

import itertools
import logging
import threading
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from sistema_reservas.cliente import Cliente
from sistema_reservas.entidad import Entidad
from sistema_reservas.excepciones import (
    PagoRechazadoError,
    ReservaInvalidaError,
    SistemaReservasError,
    TransicionEstadoError,
)
from sistema_reservas.servicio import Servicio

LOGGER = logging.getLogger(__name__)


class EstadoReserva(str, Enum):
    """Estados posibles de una reserva."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    PROCESADA = "PROCESADA"


class Reserva(Entidad):
    """Reserva que evita transiciones de estado inválidas y audita cada cambio."""

    LIMITE_PAGO = Decimal("5000.00")
    _secuencia = itertools.count(1)
    _candado = threading.Lock()

    def __init__(
        self,
        cliente: Cliente,
        servicio: Servicio,
        fecha: datetime,
        **parametros: Any,
    ) -> None:
        with Reserva._candado:
            numero = next(Reserva._secuencia)
        super().__init__(f"RES-{numero:04d}")
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        self._cliente = cliente
        self._servicio = servicio
        self._fecha = self._validar_fecha(fecha)
        self._parametros = dict(parametros)
        self._estado = EstadoReserva.PENDIENTE
        self._total = Decimal("0.00")
        self._historial: list[dict[str, str]] = []
        self._registrar("CREADA", f"{servicio.identificador} para {cliente.identificador}")
        LOGGER.info(
            "Reserva %s creada: cliente=%s servicio=%s fecha=%s",
            self._identificador,
            cliente.identificador,
            servicio.identificador,
            self._fecha.isoformat(timespec="minutes"),
        )

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def fecha(self) -> datetime:
        return self._fecha

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def total(self) -> Decimal:
        return self._total

    @property
    def parametros(self) -> dict[str, Any]:
        return dict(self._parametros)

    @property
    def historial(self) -> tuple[dict[str, str], ...]:
        return tuple(dict(evento) for evento in self._historial)

    @staticmethod
    def _validar_fecha(fecha: datetime) -> datetime:
        if not isinstance(fecha, datetime):
            raise ReservaInvalidaError("La fecha de la reserva debe ser un datetime.")
        ahora = datetime.now()
        if fecha <= ahora:
            raise ReservaInvalidaError(
                "La fecha de la reserva debe ser futura.",
                detalle=fecha.isoformat(timespec="minutes"),
            )
        if fecha > ahora + timedelta(days=365):
            raise ReservaInvalidaError(
                "La reserva no puede exceder los 365 días de anticipación."
            )
        return fecha

    def _exigir_estado(self, esperado: EstadoReserva, accion: str) -> None:
        if self._estado is not esperado:
            raise TransicionEstadoError(
                f"No se puede {accion} una reserva en estado {self._estado.value}.",
                detalle=f"requerido={esperado.value}",
            )

    def _registrar(self, evento: str, detalle: str) -> None:
        self._historial.append(
            {
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "evento": evento,
                "detalle": detalle,
            }
        )

    def _cambiar_estado(self, nuevo: EstadoReserva, detalle: str) -> None:
        anterior = self._estado
        self._estado = nuevo
        self._registrar(f"ESTADO_{nuevo.value}", detalle)
        LOGGER.info(
            "Reserva %s: %s -> %s (%s)",
            self._identificador,
            anterior.value,
            nuevo.value,
            detalle,
        )

    def confirmar(self) -> Decimal:
        """Confirma la reserva y calcula su costo total."""
        self._exigir_estado(EstadoReserva.PENDIENTE, "confirmar")
        try:
            total = self._servicio.calcular_costo(**self._parametros)
        except SistemaReservasError:
            self._registrar("CONFIRMACION_FALLIDA", "error en el cálculo del costo")
            LOGGER.warning(
                "Falló la confirmación de %s por parámetros inválidos", self._identificador
            )
            raise
        if total <= 0:
            raise ReservaInvalidaError("El costo calculado debe ser positivo.")
        self._total = total
        self._cambiar_estado(EstadoReserva.CONFIRMADA, f"total=S/ {total}")
        return total

    def cancelar(self, motivo: str) -> None:
        """Cancela la reserva si su estado lo permite."""
        if self._estado not in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA):
            raise TransicionEstadoError(
                f"No se puede cancelar una reserva en estado {self._estado.value}.",
                detalle="estados permitidos: PENDIENTE o CONFIRMADA",
            )
        if not isinstance(motivo, str) or len(motivo.strip()) < 5:
            raise ReservaInvalidaError(
                "El motivo de cancelación debe tener al menos 5 caracteres."
            )
        self._cambiar_estado(EstadoReserva.CANCELADA, f"motivo={motivo.strip()}")

    def procesar(self) -> Decimal:
        """Procesa el pago de una reserva confirmada dentro del límite permitido."""
        self._exigir_estado(EstadoReserva.CONFIRMADA, "procesar")
        if self._total > self.LIMITE_PAGO:
            raise PagoRechazadoError(
                "El total excede el límite de pago automático.",
                detalle=f"total=S/ {self._total}; límite=S/ {self.LIMITE_PAGO}",
            )
        self._cambiar_estado(EstadoReserva.PROCESADA, "pago aprobado")
        return self._total

    def descripcion(self) -> str:
        return (
            f"Reserva {self._identificador}: {self._servicio.descripcion()} "
            f"para {self._cliente.nombre} el {self._fecha:%Y-%m-%d %H:%M} "
            f"[{self._estado.value}]"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": type(self).__name__,
            "identificador": self._identificador,
            "cliente": self._cliente.identificador,
            "servicio": self._servicio.identificador,
            "fecha": self._fecha.isoformat(timespec="minutes"),
            "parametros": dict(self._parametros),
            "estado": self._estado.value,
            "total": str(self._total),
            "creado_en": self._creado_en.isoformat(timespec="seconds"),
            "historial": list(self._historial),
        }

    def __str__(self) -> str:
        return self.descripcion()

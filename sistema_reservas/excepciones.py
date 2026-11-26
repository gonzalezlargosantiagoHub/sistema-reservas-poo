"""Jerarquía de excepciones personalizadas del sistema."""

from __future__ import annotations


class SistemaReservasError(Exception):
    """Error base de la aplicación; todas las excepciones heredan de aquí."""

    codigo = "SR-000"

    def __init__(self, mensaje: str, *, detalle: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle

    def __str__(self) -> str:
        base = f"[{self.codigo}] {self.mensaje}"
        return f"{base} ({self.detalle})" if self.detalle else base


class DatosInvalidosError(SistemaReservasError, ValueError):
    """Datos de entrada que no cumplen las reglas del dominio."""

    codigo = "SR-100"


class ClienteInvalidoError(DatosInvalidosError):
    """Datos de un cliente inválidos."""

    codigo = "SR-101"


class ServicioInvalidoError(DatosInvalidosError):
    """Configuración o parámetros inválidos de un servicio."""

    codigo = "SR-102"


class ReservaInvalidaError(DatosInvalidosError):
    """Datos de una reserva inválidos."""

    codigo = "SR-103"


class OperacionNoPermitidaError(SistemaReservasError):
    """Operación no permitida para el estado actual de la entidad."""

    codigo = "SR-200"


class TransicionEstadoError(OperacionNoPermitidaError):
    """Cambio de estado inválido en una reserva."""

    codigo = "SR-201"


class ServicioNoDisponibleError(SistemaReservasError):
    """El servicio no puede ofrecerse en las condiciones solicitadas."""

    codigo = "SR-300"


class CapacidadExcedidaError(ServicioNoDisponibleError):
    """La cantidad de asistentes supera la capacidad de la sala."""

    codigo = "SR-301"


class StockInsuficienteError(ServicioNoDisponibleError):
    """No hay unidades suficientes del equipo solicitado."""

    codigo = "SR-302"


class PagoRechazadoError(SistemaReservasError):
    """El procesamiento del pago fue rechazado."""

    codigo = "SR-400"

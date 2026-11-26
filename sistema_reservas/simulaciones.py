"""Simulaciones válidas e inválidas que ejercitan el sistema completo."""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Callable

from sistema_reservas.cliente import Cliente
from sistema_reservas.excepciones import (
    CapacidadExcedidaError,
    ClienteInvalidoError,
    PagoRechazadoError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SistemaReservasError,
    StockInsuficienteError,
    TransicionEstadoError,
)
from sistema_reservas.logger_config import ARCHIVO_LOG, configurar_logging
from sistema_reservas.reserva import EstadoReserva, Reserva
from sistema_reservas.servicio import (
    AlquilerEquipo,
    AsesoriaEspecializada,
    ReservaSala,
    Servicio,
)

LOGGER = logging.getLogger(__name__)
Escenario = Callable[[], tuple[bool, str]]


@dataclass(frozen=True)
class ResultadoSimulacion:
    """Resultado de un escenario ejecutado."""

    numero: int
    nombre: str
    tipo: str
    exitoso: bool
    detalle: str


def _cliente(
    nombre: str = "Ana Torres",
    email: str = "ana.torres@correo.com",
    documento: str = "12345678",
    telefono: str = "+51987654321",
) -> Cliente:
    return Cliente(nombre, email, documento, telefono)


def _en_dias(dias: int) -> datetime:
    return datetime.now() + timedelta(days=dias)


def _escenario_01() -> tuple[bool, str]:
    cliente = _cliente()
    sala = ReservaSala("SAL-001", "Sala Ejecutiva", "120.00", 10)
    reserva = Reserva(cliente, sala, _en_dias(2), horas=3, asistentes=8)
    try:
        total = reserva.confirmar()
    except SistemaReservasError as exc:
        return False, f"error inesperado en la confirmación: {exc}"
    else:
        reserva.procesar()
        correcto = reserva.estado is EstadoReserva.PROCESADA and total == Decimal("360.00")
        return correcto, f"total=S/ {total}, estado={reserva.estado.value}"


def _escenario_02() -> tuple[bool, str]:
    try:
        Cliente("Ana Torres", "ana.torres@correo", "12345678", "987654321")
    except ClienteInvalidoError as exc:
        return True, f"correo inválido rechazado: {exc}"
    return False, "el correo inválido fue aceptado"


def _escenario_03() -> tuple[bool, str]:
    sala = ReservaSala("SAL-002", "Sala Pequeña", "80.00", 5)
    reserva = Reserva(_cliente(), sala, _en_dias(1), horas=2, asistentes=9)
    try:
        reserva.confirmar()
    except CapacidadExcedidaError as exc:
        correcto = reserva.estado is EstadoReserva.PENDIENTE
        return correcto, f"capacidad controlada ({exc}); estado={reserva.estado.value}"
    return False, "la capacidad excedida no fue detectada"


def _escenario_04() -> tuple[bool, str]:
    equipo = AlquilerEquipo("EQP-001", "Proyector 4K", "45.00", 3)
    reserva = Reserva(_cliente(), equipo, _en_dias(2), dias=2, cantidad=5)
    try:
        reserva.confirmar()
    except StockInsuficienteError as exc:
        correcto = reserva.estado is EstadoReserva.PENDIENTE
        return correcto, f"stock controlado ({exc}); estado={reserva.estado.value}"
    return False, "el stock insuficiente no fue detectado"


def _escenario_05() -> tuple[bool, str]:
    equipo = AlquilerEquipo("EQP-002", "Laptop de alto rendimiento", "45.00", 6)
    reserva = Reserva(_cliente(), equipo, _en_dias(3), dias=4, cantidad=3)
    total = reserva.confirmar()
    correcto = total == Decimal("513.00")
    return correcto, f"descuento por volumen aplicado, total=S/ {total}"


def _escenario_06() -> tuple[bool, str]:
    asesoria = AsesoriaEspecializada(
        "ASE-001", "Asesoría de ciberseguridad", "200.00", "Ciberseguridad"
    )
    reserva = Reserva(_cliente(), asesoria, _en_dias(4), horas=4, certificado=True)
    total = reserva.confirmar()
    correcto = total == Decimal("920.00")
    return correcto, f"recargo por sesión extensa aplicado, total=S/ {total}"


def _escenario_07() -> tuple[bool, str]:
    asesoria = AsesoriaEspecializada(
        "ASE-002", "Asesoría financiera", "150.00", "Finanzas corporativas"
    )
    reserva = Reserva(_cliente(), asesoria, _en_dias(5), horas=2, certificado=False)
    try:
        reserva.confirmar()
    except ServicioNoDisponibleError as exc:
        return True, f"asesoría sin certificación rechazada: {exc}"
    return False, "la asesoría sin certificación fue aceptada"


def _escenario_08() -> tuple[bool, str]:
    sala = ReservaSala("SAL-003", "Sala de reuniones", "120.00", 10)
    reserva = Reserva(_cliente(), sala, _en_dias(1), horas=2, asistentes=5)
    reserva.confirmar()
    reserva.procesar()
    try:
        reserva.cancelar("El cliente ya no requiere el servicio")
    except TransicionEstadoError as exc:
        correcto = reserva.estado is EstadoReserva.PROCESADA
        return correcto, f"cancelación de reserva procesada rechazada: {exc}"
    return False, "se permitió cancelar una reserva procesada"


def _escenario_09() -> tuple[bool, str]:
    sala = ReservaSala("SAL-004", "Sala de capacitación", "100.00", 20)
    reserva = Reserva(_cliente(), sala, _en_dias(2), horas=2, asistentes=4)
    reserva.cancelar("Reserva duplicada por error del sistema")
    try:
        reserva.confirmar()
    except TransicionEstadoError as exc:
        correcto = reserva.estado is EstadoReserva.CANCELADA
        return correcto, f"confirmación de reserva cancelada rechazada: {exc}"
    return False, "se permitió confirmar una reserva cancelada"


def _escenario_10() -> tuple[bool, str]:
    sala = ReservaSala("SAL-005", "Sala directiva", "150.00", 12)
    reserva = Reserva(_cliente(), sala, _en_dias(1), horas=1, asistentes=3)
    try:
        reserva.cancelar("no")
    except ReservaInvalidaError as exc:
        correcto = reserva.estado is EstadoReserva.PENDIENTE
        return correcto, f"motivo inválido rechazado ({exc}); estado={reserva.estado.value}"
    return False, "se aceptó un motivo de cancelación inválido"


def _escenario_11() -> tuple[bool, str]:
    sala = ReservaSala("SAL-006", "Sala de innovación", "90.00", 8)
    reserva = Reserva(_cliente(), sala, _en_dias(3), horas=2, asistentes=4)
    reserva.confirmar()
    reserva.cancelar("Cambio de fecha solicitado por el cliente")
    correcto = reserva.estado is EstadoReserva.CANCELADA
    return correcto, f"cancelación válida, estado={reserva.estado.value}"


def _escenario_12() -> tuple[bool, str]:
    sala = ReservaSala("SAL-007", "Auditorio principal", "1500.00", 100)
    reserva = Reserva(_cliente(), sala, _en_dias(10), horas=6, asistentes=2)
    total = reserva.confirmar()
    try:
        reserva.procesar()
    except PagoRechazadoError as exc:
        correcto = reserva.estado is EstadoReserva.CONFIRMADA and total == Decimal("9000.00")
        return correcto, f"pago rechazado por límite ({exc}); estado={reserva.estado.value}"
    return False, "el pago que excede el límite fue aprobado"


def _escenario_13() -> tuple[bool, str]:
    servicios: list[tuple[Servicio, dict[str, object]]] = [
        (ReservaSala("SAL-008", "Auditorio", "300.00", 100), {"horas": 2, "asistentes": 50}),
        (AlquilerEquipo("EQP-003", "Laptop", "35.00", 10), {"dias": 5, "cantidad": 2}),
        (
            AsesoriaEspecializada(
                "ASE-003",
                "Asesoría legal",
                "180.00",
                "Derecho corporativo",
                requiere_certificacion=False,
            ),
            {"horas": 2},
        ),
    ]
    totales = [servicio.calcular_costo(**parametros) for servicio, parametros in servicios]
    total = sum(totales, Decimal("0.00"))
    correcto = total == Decimal("1310.00") and len({type(servicio) for servicio, _ in servicios}) == 3
    return correcto, f"polimorfismo verificado, total=S/ {total}"


def _escenario_14() -> tuple[bool, str]:
    datos = {"nombre": "Luis Prado", "documento": "87654321", "telefono": "987654321"}
    try:
        try:
            _ = datos["email"]
        except KeyError as exc:
            raise ReservaInvalidaError(
                "No se puede registrar la reserva: faltan datos del cliente."
            ) from exc
    except ReservaInvalidaError as exc:
        encadenada = isinstance(exc.__cause__, KeyError)
        return encadenada, f"cadena: KeyError -> ReservaInvalidaError ({exc})"
    return False, "no se produjo la excepción encadenada esperada"


def _escenario_15() -> tuple[bool, str]:
    ruta = Path(tempfile.gettempdir()) / "reporte_reservas_simulacion.txt"
    liberado = False
    try:
        with ruta.open("w", encoding="utf-8") as archivo:
            archivo.write("Reporte temporal de simulación\n")
        raise ReservaInvalidaError("Fallo simulado al enviar el reporte.")
    except ReservaInvalidaError as exc:
        LOGGER.warning("Escenario de limpieza controlado: %s", exc)
    finally:
        ruta.unlink(missing_ok=True)
        liberado = not ruta.exists()
    return liberado, "recurso temporal liberado en el bloque finally"


def _escenario_16() -> tuple[bool, str]:
    cliente = _cliente()
    cliente.email = "NUEVO.Correo@Dominio.COM"
    cliente.telefono = "+51 999-888-777"
    correcto = cliente.email == "nuevo.correo@dominio.com" and cliente.telefono == "+51999888777"
    return correcto, f"datos normalizados: email={cliente.email}, teléfono={cliente.telefono}"


def _escenario_17() -> tuple[bool, str]:
    sala = ReservaSala("SAL-009", "Sala de posgrado", "110.00", 15)
    try:
        Reserva(_cliente(), sala, datetime.now() - timedelta(days=1), horas=1)
    except ReservaInvalidaError as exc:
        return True, f"fecha pasada rechazada: {exc}"
    return False, "se aceptó una reserva con fecha pasada"


def _escenario_18() -> tuple[bool, str]:
    sala = ReservaSala("SAL-010", "Sala temporal", "70.00", 6)
    sala.desactivar()
    reserva = Reserva(_cliente(), sala, _en_dias(2), horas=1, asistentes=2)
    try:
        reserva.confirmar()
    except ServicioNoDisponibleError as exc:
        return True, f"servicio desactivado rechazado: {exc}"
    return False, "se permitió reservar un servicio desactivado"


SIMULACIONES: tuple[tuple[str, str, Escenario], ...] = (
    ("Flujo completo de reserva de sala", "válida", _escenario_01),
    ("Cliente con correo inválido", "inválida", _escenario_02),
    ("Asistentes por encima de la capacidad", "inválida", _escenario_03),
    ("Alquiler de equipo sin stock suficiente", "inválida", _escenario_04),
    ("Alquiler de equipo con descuento por volumen", "válida", _escenario_05),
    ("Asesoría con certificación y recargo", "válida", _escenario_06),
    ("Asesoría sin la certificación exigida", "inválida", _escenario_07),
    ("Cancelación de una reserva procesada", "inválida", _escenario_08),
    ("Confirmación de una reserva cancelada", "inválida", _escenario_09),
    ("Cancelación con motivo demasiado corto", "inválida", _escenario_10),
    ("Cancelación válida de una reserva confirmada", "válida", _escenario_11),
    ("Pago rechazado por superar el límite", "inválida", _escenario_12),
    ("Cálculo polimórfico de varios servicios", "válida", _escenario_13),
    ("Excepción encadenada por datos incompletos", "inválida", _escenario_14),
    ("Liberación de recursos con try/finally", "válida", _escenario_15),
    ("Actualización encapsulada de contacto", "válida", _escenario_16),
    ("Reserva con fecha en el pasado", "inválida", _escenario_17),
    ("Reserva sobre un servicio desactivado", "inválida", _escenario_18),
)


def ejecutar_todas() -> list[ResultadoSimulacion]:
    """Ejecuta todos los escenarios y devuelve sus resultados."""
    configurar_logging()
    resultados: list[ResultadoSimulacion] = []
    LOGGER.info("Inicio de simulación: %s escenarios", len(SIMULACIONES))
    for numero, (nombre, tipo, escenario) in enumerate(SIMULACIONES, start=1):
        try:
            exitoso, detalle = escenario()
        except Exception as exc:  # una simulación no debe detener el resto
            LOGGER.exception("Escenario %02d no controlado", numero)
            exitoso, detalle = False, f"error no controlado: {type(exc).__name__}: {exc}"
        resultado = ResultadoSimulacion(numero, nombre, tipo, exitoso, detalle)
        resultados.append(resultado)
        LOGGER.info(
            "Escenario %02d (%s) %s: %s",
            numero,
            tipo,
            "OK" if exitoso else "FALLO",
            detalle,
        )
    LOGGER.info("Fin de simulación: %s/%s escenarios correctos", sum(r.exitoso for r in resultados), len(resultados))
    return resultados


def main() -> int:
    resultados = ejecutar_todas()
    print("=" * 78)
    print("SISTEMA DE RESERVAS Y SERVICIOS - SIMULACIONES")
    print("=" * 78)
    for resultado in resultados:
        estado = "OK   " if resultado.exitoso else "FALLO"
        print(f"[{resultado.numero:02d}] {estado} | {resultado.tipo:<9} | {resultado.nombre}")
        print(f"     {resultado.detalle}")
    total = len(resultados)
    correctos = sum(resultado.exitoso for resultado in resultados)
    validas = sum(1 for resultado in resultados if resultado.tipo == "válida")
    print("-" * 78)
    print(f"Escenarios: {total} | válidos: {validas} | inválidos: {total - validas}")
    print(f"Resultado: {correctos}/{total} escenarios se comportaron como se esperaba")
    print(f"Log: {ARCHIVO_LOG}")
    return 0 if correctos == total else 1

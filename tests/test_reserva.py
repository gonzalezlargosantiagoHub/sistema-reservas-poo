"""Pruebas del ciclo de vida de las reservas."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from sistema_reservas.cliente import Cliente
from sistema_reservas.excepciones import (
    CapacidadExcedidaError,
    PagoRechazadoError,
    ReservaInvalidaError,
    TransicionEstadoError,
)
from sistema_reservas.reserva import EstadoReserva, Reserva
from sistema_reservas.servicio import ReservaSala


class TestReserva(unittest.TestCase):
    def setUp(self) -> None:
        self.cliente = Cliente("Ana Torres", "ana@correo.com", "12345678", "987654321")
        self.sala = ReservaSala("SAL-100", "Sala de pruebas", "100.00", 10)
        self.fecha = datetime.now() + timedelta(days=5)

    def crear_reserva(self, **parametros: object) -> Reserva:
        parametros.setdefault("horas", 2)
        parametros.setdefault("asistentes", 4)
        return Reserva(self.cliente, self.sala, self.fecha, **parametros)

    def test_estado_inicial_y_total(self) -> None:
        reserva = self.crear_reserva()
        self.assertIs(reserva.estado, EstadoReserva.PENDIENTE)
        self.assertEqual(reserva.total, Decimal("0.00"))
        self.assertTrue(reserva.identificador.startswith("RES-"))

    def test_confirmar_calcula_total_y_cambia_estado(self) -> None:
        reserva = self.crear_reserva()
        total = reserva.confirmar()
        self.assertEqual(total, Decimal("200.00"))
        self.assertEqual(reserva.total, Decimal("200.00"))
        self.assertIs(reserva.estado, EstadoReserva.CONFIRMADA)

    def test_confirmar_dos_veces_es_invalido(self) -> None:
        reserva = self.crear_reserva()
        reserva.confirmar()
        with self.assertRaises(TransicionEstadoError):
            reserva.confirmar()

    def test_cancelar_reserva_pendiente(self) -> None:
        reserva = self.crear_reserva()
        reserva.cancelar("El cliente cambió de planes")
        self.assertIs(reserva.estado, EstadoReserva.CANCELADA)

    def test_cancelar_con_motivo_corto_es_invalido(self) -> None:
        reserva = self.crear_reserva()
        with self.assertRaises(ReservaInvalidaError):
            reserva.cancelar("no")
        self.assertIs(reserva.estado, EstadoReserva.PENDIENTE)

    def test_no_se_puede_cancelar_una_reserva_procesada(self) -> None:
        reserva = self.crear_reserva()
        reserva.confirmar()
        reserva.procesar()
        with self.assertRaises(TransicionEstadoError):
            reserva.cancelar("Solicitud tardía del cliente")
        self.assertIs(reserva.estado, EstadoReserva.PROCESADA)

    def test_procesar_requiere_confirmacion(self) -> None:
        reserva = self.crear_reserva()
        with self.assertRaises(TransicionEstadoError):
            reserva.procesar()

    def test_pago_en_el_limite_es_permitido(self) -> None:
        sala = ReservaSala("SAL-101", "Auditorio", "1000.00", 50)
        reserva = Reserva(self.cliente, sala, self.fecha, horas=5, asistentes=2)
        reserva.confirmar()
        self.assertEqual(reserva.procesar(), Decimal("5000.00"))
        self.assertIs(reserva.estado, EstadoReserva.PROCESADA)

    def test_pago_sobre_el_limite_es_rechazado(self) -> None:
        sala = ReservaSala("SAL-102", "Auditorio grande", "1500.00", 50)
        reserva = Reserva(self.cliente, sala, self.fecha, horas=6, asistentes=2)
        reserva.confirmar()
        with self.assertRaises(PagoRechazadoError):
            reserva.procesar()
        self.assertIs(reserva.estado, EstadoReserva.CONFIRMADA)

    def test_fecha_pasada_es_rechazada(self) -> None:
        with self.assertRaises(ReservaInvalidaError):
            Reserva(self.cliente, self.sala, datetime.now() - timedelta(days=1), horas=1)

    def test_fecha_demasiado_lejana_es_rechazada(self) -> None:
        with self.assertRaises(ReservaInvalidaError):
            Reserva(self.cliente, self.sala, datetime.now() + timedelta(days=400), horas=1)

    def test_confirmacion_fallida_conserva_estado_y_audita(self) -> None:
        reserva = self.crear_reserva(asistentes=11)
        with self.assertRaises(CapacidadExcedidaError):
            reserva.confirmar()
        self.assertIs(reserva.estado, EstadoReserva.PENDIENTE)
        eventos = [evento["evento"] for evento in reserva.historial]
        self.assertIn("CONFIRMACION_FALLIDA", eventos)

    def test_to_dict_refleja_el_estado(self) -> None:
        reserva = self.crear_reserva()
        reserva.confirmar()
        datos = reserva.to_dict()
        self.assertEqual(datos["estado"], "CONFIRMADA")
        self.assertEqual(datos["cliente"], "CLI-12345678")
        self.assertEqual(datos["servicio"], "SAL-100")
        self.assertEqual(datos["total"], "200.00")

    def test_identificadores_son_unicos(self) -> None:
        primera = self.crear_reserva()
        segunda = self.crear_reserva()
        self.assertNotEqual(primera.identificador, segunda.identificador)

    def test_reserva_requiere_entidades_validas(self) -> None:
        with self.assertRaises(ReservaInvalidaError):
            Reserva("no-es-cliente", self.sala, self.fecha, horas=1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

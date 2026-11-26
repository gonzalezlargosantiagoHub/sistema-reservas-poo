"""Pruebas de los servicios y del polimorfismo de costos."""

from __future__ import annotations

import unittest
from decimal import Decimal, InvalidOperation

from sistema_reservas.excepciones import (
    CapacidadExcedidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
    StockInsuficienteError,
)
from sistema_reservas.servicio import (
    AlquilerEquipo,
    AsesoriaEspecializada,
    ReservaSala,
    Servicio,
)


class TestReservaSala(unittest.TestCase):
    def setUp(self) -> None:
        self.sala = ReservaSala("SAL-001", "Sala Ejecutiva", "120.00", 10)

    def test_costo_sin_recargo(self) -> None:
        self.assertEqual(self.sala.calcular_costo(horas=3, asistentes=8), Decimal("360.00"))

    def test_recargo_por_ocupacion_alta(self) -> None:
        self.assertEqual(self.sala.calcular_costo(horas=2, asistentes=9), Decimal("264.00"))

    def test_capacidad_excedida(self) -> None:
        with self.assertRaises(CapacidadExcedidaError):
            self.sala.calcular_costo(horas=2, asistentes=11)

    def test_horas_fuera_de_rango(self) -> None:
        for horas in (0, 13):
            with self.subTest(horas=horas), self.assertRaises(ServicioInvalidoError):
                self.sala.calcular_costo(horas=horas, asistentes=2)

    def test_asistentes_booleanos_rechazados(self) -> None:
        with self.assertRaises(ServicioInvalidoError):
            self.sala.calcular_costo(horas=1, asistentes=True)  # type: ignore[arg-type]

    def test_servicio_desactivado(self) -> None:
        self.sala.desactivar()
        with self.assertRaises(ServicioNoDisponibleError):
            self.sala.calcular_costo(horas=1, asistentes=1)

    def test_tarifa_invalida_encadena_invalidoperation(self) -> None:
        with self.assertRaises(ServicioInvalidoError) as contexto:
            ReservaSala("SAL-002", "Sala X", "no-es-numero", 5)
        self.assertIsInstance(contexto.exception.__cause__, InvalidOperation)

    def test_tarifa_negativa_rechazada(self) -> None:
        with self.assertRaises(ServicioInvalidoError):
            ReservaSala("SAL-003", "Sala Y", "-10.00", 5)


class TestAlquilerEquipo(unittest.TestCase):
    def setUp(self) -> None:
        self.equipo = AlquilerEquipo("EQP-001", "Proyector 4K", "45.00", 6)

    def test_costo_con_descuento_por_volumen(self) -> None:
        self.assertEqual(self.equipo.calcular_costo(dias=4, cantidad=3), Decimal("513.00"))

    def test_costo_sin_descuento(self) -> None:
        self.assertEqual(self.equipo.calcular_costo(dias=2, cantidad=2), Decimal("180.00"))

    def test_stock_insuficiente(self) -> None:
        with self.assertRaises(StockInsuficienteError):
            self.equipo.calcular_costo(dias=1, cantidad=7)

    def test_dias_fuera_de_rango(self) -> None:
        with self.assertRaises(ServicioInvalidoError):
            self.equipo.calcular_costo(dias=366, cantidad=1)


class TestAsesoriaEspecializada(unittest.TestCase):
    def setUp(self) -> None:
        self.asesoria = AsesoriaEspecializada(
            "ASE-001", "Asesoría de ciberseguridad", "200.00", "Ciberseguridad"
        )

    def test_exige_certificacion(self) -> None:
        with self.assertRaises(ServicioNoDisponibleError):
            self.asesoria.calcular_costo(horas=2, certificado=False)

    def test_costo_con_recargo_por_sesion_extensa(self) -> None:
        self.assertEqual(
            self.asesoria.calcular_costo(horas=4, certificado=True), Decimal("920.00")
        )

    def test_costo_sin_recargo(self) -> None:
        self.assertEqual(
            self.asesoria.calcular_costo(horas=2, certificado=True), Decimal("400.00")
        )

    def test_asesoria_sin_certificacion_obligatoria(self) -> None:
        libre = AsesoriaEspecializada(
            "ASE-002", "Asesoría legal", "180.00", "Derecho corporativo",
            requiere_certificacion=False,
        )
        self.assertEqual(libre.calcular_costo(horas=2), Decimal("360.00"))


class TestPolimorfismo(unittest.TestCase):
    def test_todos_los_servicios_comparten_el_contrato(self) -> None:
        servicios: list[Servicio] = [
            ReservaSala("SAL-010", "Auditorio", "300.00", 100),
            AlquilerEquipo("EQP-010", "Laptop", "35.00", 10),
            AsesoriaEspecializada(
                "ASE-010", "Asesoría legal", "180.00", "Derecho corporativo",
                requiere_certificacion=False,
            ),
        ]
        for servicio in servicios:
            self.assertIsInstance(servicio, Servicio)
            self.assertTrue(servicio.descripcion())
            self.assertIn("tipo", servicio.to_dict())


if __name__ == "__main__":
    unittest.main()

"""Pruebas de integración de los escenarios y del archivo de logs."""

from __future__ import annotations

import unittest

from sistema_reservas.logger_config import ARCHIVO_LOG
from sistema_reservas.simulaciones import ejecutar_todas


class TestSimulaciones(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resultados = ejecutar_todas()

    def test_cantidad_minima_de_escenarios(self) -> None:
        self.assertGreaterEqual(len(self.resultados), 10)

    def test_todos_los_escenarios_son_correctos(self) -> None:
        fallidos = [resultado for resultado in self.resultados if not resultado.exitoso]
        self.assertFalse(fallidos, f"escenarios fallidos: {fallidos}")

    def test_incluye_escenarios_validos_e_invalidos(self) -> None:
        tipos = {resultado.tipo for resultado in self.resultados}
        self.assertEqual(tipos, {"válida", "inválida"})

    def test_cada_escenario_tiene_detalle(self) -> None:
        for resultado in self.resultados:
            with self.subTest(numero=resultado.numero):
                self.assertTrue(resultado.detalle.strip())

    def test_archivo_de_log_generado(self) -> None:
        self.assertTrue(ARCHIVO_LOG.exists())
        self.assertGreater(ARCHIVO_LOG.stat().st_size, 0)
        contenido = ARCHIVO_LOG.read_text(encoding="utf-8")
        self.assertIn("Inicio de simulación", contenido)
        self.assertIn("Escenario 01", contenido)
        self.assertIn("Reserva RES-", contenido)


if __name__ == "__main__":
    unittest.main()

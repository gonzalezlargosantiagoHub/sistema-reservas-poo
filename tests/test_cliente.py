"""Pruebas de la entidad abstracta y del cliente."""

from __future__ import annotations

import unittest

from sistema_reservas.cliente import Cliente
from sistema_reservas.entidad import Entidad
from sistema_reservas.excepciones import ClienteInvalidoError, DatosInvalidosError


class TestEntidad(unittest.TestCase):
    def test_no_se_puede_instanciar_clase_abstracta(self) -> None:
        with self.assertRaises(TypeError):
            Entidad("ENT-001")  # type: ignore[abstract]

    def test_identificador_vacio_es_rechazado(self) -> None:
        with self.assertRaises(DatosInvalidosError):
            Cliente("Ana Torres", "ana@correo.com", "  ", "987654321")


class ClienteValidoMixin:
    @staticmethod
    def crear_cliente() -> Cliente:
        return Cliente("Ana Torres", "Ana.Torres@Correo.COM", "12345678", "+51 987-654-321")


class TestCliente(ClienteValidoMixin, unittest.TestCase):
    def test_creacion_valida_y_normalizacion(self) -> None:
        cliente = self.crear_cliente()
        self.assertEqual(cliente.identificador, "CLI-12345678")
        self.assertEqual(cliente.email, "ana.torres@correo.com")
        self.assertEqual(cliente.telefono, "+51987654321")
        self.assertEqual(cliente.documento, "12345678")
        self.assertEqual(cliente.nombre, "Ana Torres")

    def test_correo_invalido(self) -> None:
        for correo in ("ana@correo", "ana.correo.com", "@correo.com", "ana@.com"):
            with self.subTest(correo=correo), self.assertRaises(ClienteInvalidoError):
                Cliente("Ana Torres", correo, "12345678", "987654321")

    def test_documento_invalido(self) -> None:
        for documento in ("123", "12345678901", "12A45678", ""):
            with self.subTest(documento=documento), self.assertRaises(ClienteInvalidoError):
                Cliente("Ana Torres", "ana@correo.com", documento, "987654321")

    def test_telefono_invalido(self) -> None:
        for telefono in ("123", "teléfono", "+51-abc-123", ""):
            with self.subTest(telefono=telefono), self.assertRaises(ClienteInvalidoError):
                Cliente("Ana Torres", "ana@correo.com", "12345678", telefono)

    def test_nombre_invalido(self) -> None:
        for nombre in ("Al", "Ana 123", "   ", 42):
            with self.subTest(nombre=nombre), self.assertRaises(ClienteInvalidoError):
                Cliente(nombre, "ana@correo.com", "12345678", "987654321")  # type: ignore[arg-type]

    def test_setter_invalido_conserva_el_valor_anterior(self) -> None:
        cliente = self.crear_cliente()
        with self.assertRaises(ClienteInvalidoError):
            cliente.email = "correo-invalido"
        self.assertEqual(cliente.email, "ana.torres@correo.com")

    def test_setter_valido_actualiza_el_dato(self) -> None:
        cliente = self.crear_cliente()
        cliente.telefono = "+51 999-888-777"
        self.assertEqual(cliente.telefono, "+51999888777")

    def test_desde_dict_encadena_keyerror(self) -> None:
        datos = {"nombre": "Luis Prado", "documento": "87654321", "telefono": "987654321"}
        with self.assertRaises(ClienteInvalidoError) as contexto:
            Cliente.desde_dict(datos)
        self.assertIsInstance(contexto.exception.__cause__, KeyError)
        self.assertIsInstance(contexto.exception, ValueError)

    def test_igualdad_por_identificador(self) -> None:
        primero = self.crear_cliente()
        segundo = Cliente("Otra Persona", "otra@correo.com", "12345678", "912345678")
        self.assertEqual(primero, segundo)
        self.assertEqual(len({primero, segundo}), 1)

    def test_to_dict_contiene_datos_clave(self) -> None:
        datos = self.crear_cliente().to_dict()
        self.assertEqual(datos["tipo"], "Cliente")
        self.assertEqual(datos["identificador"], "CLI-12345678")
        self.assertIn("creado_en", datos)


if __name__ == "__main__":
    unittest.main()

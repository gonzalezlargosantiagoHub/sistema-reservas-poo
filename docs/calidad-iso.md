# Cumplimiento de calidad: ISO 9001, ISO/IEC 9126 e ISO/IEC 12207

Este documento relaciona las prácticas implementadas en el proyecto con las normas
solicitadas. Cada afirmación se vincula con evidencia verificable dentro del repositorio.

## 1. ISO 9001 — Sistemas de gestión de la calidad

| Principio / requisito              | Implementación en el proyecto                                             | Evidencia                                                    |
|------------------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------|
| Enfoque al cliente                | Reglas de negocio explícitas: capacidad, stock, certificación, límite de pago | `sistema_reservas/servicio.py`, `sistema_reservas/reserva.py` |
| Liderazgo y responsabilidad        | Flujo de trabajo con issue, rama y pull request por módulo                 | Pestañas Issues y Pull requests del repositorio               |
| Competencia y documentación        | README, diagrama UML, tabla de escenarios y esta matriz de trazabilidad    | `README.md`, `docs/calidad-iso.md`                            |
| Control de la información documentada | Código versionado con commits descriptivos por módulo                   | Historial de Git (`git log`)                                  |
| Mejora continua (PDCA)             | Ciclo detección → corrección → verificación aplicado a cada PR             | Commits de corrección y suite de pruebas                      |
| Seguimiento y medición             | 18 escenarios y 49 pruebas con resultado verificable                       | `py -m unittest discover -s tests -v`                         |
| Trazabilidad                       | Registro cronológico de cada reserva y de cada ejecución                   | `logs/sistema_reservas.log`, historial interno de `Reserva`   |

## 2. ISO/IEC 9126 — Calidad del producto de software

| Característica      | Subcaracterística        | Implementación                                                               |
|---------------------|--------------------------|------------------------------------------------------------------------------|
| Funcionalidad       | Adecuación               | Tres tipos de servicio con reglas propias y polimorfismo de costos           |
|                     | Exactitud                | Cálculo monetario con `Decimal` y cuantización a dos decimales                |
|                     | Interoperabilidad        | Serialización `to_dict` y construcción desde diccionario (`Cliente.desde_dict`) |
|                     | Seguridad                | Validación de todos los datos de entrada y transiciones de estado controladas |
| Fiabilidad          | Madurez                  | 49 pruebas automatizadas y 18 escenarios de regresión                         |
|                     | Tolerancia a fallos      | Excepciones personalizadas con códigos y estados consistentes tras el error   |
|                     | Recuperabilidad          | La reserva conserva su estado y registra el fallo en el historial             |
| Usabilidad          | Comprensión              | Mensajes de error en español con código, contexto y detalle                   |
|                     | Operabilidad             | Un comando ejecuta todas las simulaciones y genera el log                     |
| Eficiencia          | Comportamiento temporal  | Operaciones en memoria sin dependencias externas                              |
|                     | Utilización de recursos  | Log rotativo con límite de 1 MB y 3 respaldos                                 |
| Mantenibilidad      | Analizabilidad           | Arquitectura por módulos y jerarquía de excepciones clara                     |
|                     | Modificabilidad          | Servicios extensibles mediante la clase abstracta `Servicio`                  |
|                     | Estabilidad              | Pruebas unitarias por módulo y pruebas de integración                         |
|                     | Facilidad de prueba      | Suite estándar `unittest` sin configuración adicional                         |
| Portabilidad        | Adaptabilidad            | Solo biblioteca estándar, sin dependencias de terceros                        |
|                     | Instalabilidad           | Ejecutable con Python 3.10+ sin instalación de paquetes                       |
|                     | Coexistencia             | Paquete aislado `sistema_reservas` sin colisiones de nombres                  |

## 3. ISO/IEC 12207 — Procesos del ciclo de vida del software

| Proceso                              | Actividad realizada                                                  | Artefacto                                              |
|--------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------|
| Especificación de requisitos         | Definición de entidades, servicios, estados y reglas de negocio      | `README.md`, issues por módulo                         |
| Diseño arquitectónico                | Diagrama de clases, jerarquías abstractas y separación por capas     | Diagrama Mermaid del README, `entidad.py`, `servicio.py` |
| Construcción                         | Implementación con tipado estático, `Decimal` y docstrings           | `sistema_reservas/*.py`                                |
| Integración                          | Ensamblaje de servicios, reservas, logging y simulaciones            | `simulaciones.py`                                      |
| Verificación                         | Pruebas unitarias y de integración automatizadas                     | `tests/`                                               |
| Validación                           | Escenarios válidos e inválidos con resultado esperado                | 18 escenarios de `simulaciones.py`                     |
| Operación                            | Ejecución mediante `main.py` o `python -m sistema_reservas`           | `main.py`, `__main__.py`                               |
| Mantenimiento                        | Correcciones y mejoras mediante issues, ramas y pull requests         | Historial de Git                                       |
| Gestión de configuración             | Repositorio público, una rama por módulo y commits atómicos           | GitHub                                                 |
| Aseguramiento de la calidad          | Revisión por PR, evidencias de pruebas y logs                        | Pull requests, `logs/sistema_reservas.log`             |

## 4. Matriz de trazabilidad requisito → módulo → prueba

| Requisito                                        | Módulo                          | Prueba principal                                                        |
|--------------------------------------------------|---------------------------------|-------------------------------------------------------------------------|
| Entidad abstracta con contrato común             | `entidad.py`                    | `test_cliente.TestEntidad.test_no_se_puede_instanciar_clase_abstracta`  |
| Validación y encapsulación del cliente           | `cliente.py`                    | `test_cliente.TestCliente.*`                                            |
| Excepciones personalizadas y encadenamiento      | `excepciones.py`                | `test_cliente.TestCliente.test_desde_dict_encadena_keyerror`            |
| Cálculo de costos por tipo de servicio           | `servicio.py`                   | `test_servicios.*`                                                      |
| Control de capacidad y stock                     | `servicio.py`                   | `test_servicios.TestReservaSala.test_capacidad_excedida`                |
| Confirmación, cancelación y procesamiento        | `reserva.py`                    | `test_reserva.TestReserva.*`                                            |
| Límite de pago automático                        | `reserva.py`                    | `test_reserva.TestReserva.test_pago_sobre_el_limite_es_rechazado`       |
| Traceabilidad por archivo de logs                | `logger_config.py`              | `test_simulaciones.TestSimulaciones.test_archivo_de_log_generado`       |
| Diez o más simulaciones válidas e inválidas      | `simulaciones.py`               | `test_simulaciones.TestSimulaciones.test_cantidad_minima_de_escenarios` |

## 5. Gestión de la configuración y evidencias

- Repositorio público con `main` protegida por convención: toda integración pasa por PR.
- Una rama `feature/*` por módulo, con commits que describen el cambio y su justificación.
- Un issue por módulo con contexto, alcance y criterios de aceptación.
- Cada PR referencia su issue mediante `Closes #N` y resume cambios, riesgos y verificación.
- El archivo `logs/sistema_reservas.log` se versiona como evidencia de ejecución.

## 6. Métricas de calidad del entregable

| Métrica                              | Valor                     |
|--------------------------------------|---------------------------|
| Escenarios de simulación             | 18 (7 válidos, 11 inválidos) |
| Pruebas automatizadas                | 49                        |
| Resultado de la suite                | 100 % correctas           |
| Dependencias externas                | 0                         |
| Cobertura funcional de módulos       | 7/7 módulos con pruebas   |
| Excepciones personalizadas           | 11 tipos con código único |

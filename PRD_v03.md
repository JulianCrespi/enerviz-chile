# EnerViz Chile – PRD de Resiliencia Basada en InfoTécnica

*Versión 0.3 • 2025-05-03*

---

## 1. Visión del Producto

Crear un **gemelo digital 3-D** interactivo del SEN en CesiumJS, construído **exclusivamente** sobre el inventario técnico oficial de InfoTécnica (`instalaciones_activos.xlsx`). EnerViz permitirá a ingenieros, reguladores y analistas:

* **Visualizar** la topología completa de transmisión (líneas, circuitos, tramos) y nodos (subestaciones, barras).
* **Explorar** relaciones espaciales y temporales para detectar vulnerabilidades (N‑1, redundancia, cuellos de botella).
* **Simular** fallas críticas (blackouts pasados y futuros) y ver su impacto geográfico instantáneo.

---

## 2. Motivación y Oportunidad

* **Datos maestros dispersos**: InfoTécnica concentra toda la *información técnica* (líneas, subestaciones, transformadores, empresas, etc.) en 67 hojas de un solo Excel.
* **Falta de contexto espacial**: Aunque los shapefiles IDE dan geometría, no hay plataforma que una lógica con geografía y tiempo.
* **Demanda de resiliencia**: Después de blackouts nacionales e internacionales, hay urgencia de herramientas que cuantifiquen y comuniquen riesgos en forma clara.

**Oportunidad**: Consolidar y normalizar `instalaciones_activos.xlsx` como *fuente única de verdad* y combinarlo con geometrías para crear un gemelo dinámico de resiliencia.

---

## 3. Inventario Técnico: Estructura de `instalaciones_activos.xlsx`

| Hoja                                                        | Filas aprox.      | Campos clave                                              | Relaciones (FK)                                        |
| ----------------------------------------------------------- | ----------------- | --------------------------------------------------------- | ------------------------------------------------------ |
| **Empresa**                                                 | 1 090             | `id`, `name`, `grupo_id`                                  | `empresa.propietario_id` en Subestación, Línea         |
| **Subestaciones**                                           | 1 243             | `id`, `name`, `lat`, `lon`, `propietario_id`              | `Patio.subestacion_id`, `transformador.subestacion_id` |
| **Barras**                                                  | 17 328            | `id`, `name`, `tension_kV`, `patio_subestacion_id`        | `barra.id` enlaza a demanda/precios                    |
| **Linea**                                                   | 1 194             | `id`, `name`, `voltaje_kV`, `length_km`, `propietario_id` | `circuito.linea_id`                                    |
| **Circuito**                                                | 3 492             | `id`, `name`, `linea_id`                                  | `tramo.circuito_id`                                    |
| **Tramo**                                                   | 9 364             | `id`, `circuito_id`, `nodo1_id`, `nodo2_id`, `length_km`  | Grafo de transmisión                                   |
| **Nodo**                                                    | 116 564           | `id`, `name`                                              | Claves origen/destino en Tramo                         |
| **Transformadores**, **Reactores**, **Compensadores**, etc. | 15 000–20 000 c/u | `id`, `subestacion_id`, `barra_id`, `capacidad`           | Para futura capa de carga dinámica                     |

**Claves primarias**: columna `id`.  **Foreign keys**: siempre terminan en `_id`.

---

## 4. Relaciones Espaciales y Temporales

1. **Grafo topológico**: nodos = Subestaciones/Barras, aristas = Tramos → permite rutas de redundancia, cálculos N‑1/N‑2.
2. **Geometría**: cada `Tramo.id` se vincula a `ID_LIN_TRA` en shapefile IDE → `LINESTRING` para trazado 3-D.
3. **Atributos temporales**: más adelante enlazaremos tablas de **Potencia Transitada** y **Demanda Real** a `Tramo.id` y `Barra.id` para colorear carga por hora.
4. **Empresa/Propietario**: filtrar y agrupar por dueños para análisis de riesgos corporativos.

---

## 5. Funcionalidades MVP

| Módulo                           | Descripción                                                          | Criterio de aceptación                                                                                      |
| -------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **ETL de Inventario**            | Importar `instalaciones_activos.xlsx` y shapefiles a DuckDB.         | Tablas `linea`, `circuito`, `tramo`, `subestacion`, `barra`, `empresa`, `tramo_geom` creadas correctamente. |
| **Grafo de Transmisión**         | Construir `networkx` a partir de `tramo` y `nodo`.                   | Grafo con 9 364 aristas, 116 564 nodos instanciado.                                                         |
| **Visualización Estática**       | Renderizar líneas y subestaciones en Cesium, coloreadas por tensión. | Líneas ≥ 66 kV visibles y coloreadas: amarillo (66), cian (220), rojo (500).                                |
| **Cálculo de Redundancia (N-1)** | Calcular paths alternativos ante falla de un tramo.                  | Para cada arco, `redundant_paths` ≥ 1 o marcar como crítico.                                                |
| **Semáforo de Carga**            | Colorear aristas según carga pasada (verde/ámbar/rojo).              | Integración con CSV manual de `potencia_transitada.csv`.                                                    |
| **Simulación de Outage**         | UI para click en tramo y recalcular grafo sin ese tramo.             | Afectados destacados y panel de impacto actualizado.                                                        |

---

## 6. Beneficio Clave: Poder del Inventario Estructurado en CesiumJS

* **Visión de extremo a extremo**: desde generadoras, subestaciones, barras, circuitos y tramos, todo conectado y espacializado.
* **Insights inmediatos**: un clic revela redundancias, cuellos de botella y propietarios involucrados.
* **Simulaciones geográficas**: remover un `Tramo.id` → recalcular rutas y ver zonas aisladas en segundos.
* **Temporalidad integrada**: con extensiones para enlazar carga real (MW) por hora, evoluciones diarias o históricas.
* **Escalabilidad**: el Excel maestro impulsa la base de datos relacional en DuckDB y permite consultas ad-hoc antes de invertir en APIs.

---

## 7. Roadmap de Sprints

| Sprint | Entregable                                                      | Duración |
| ------ | --------------------------------------------------------------- | -------- |
| 0      | ETL completo: DuckDB con inventario + Parquet exportados        | 2 días   |
| 1      | CesiumJS: render estático de líneas y subestaciones             | 3 días   |
| 2      | Algoritmo N-1: redundancy y flujo simulado                      | 4 días   |
| 3      | Semáforo de carga diario (CSV manual) + panel de vulnerabilidad | 4 días   |
| 4      | UI Simulación de Outage + export de vistazo (`screenshot`)      | 3 días   |

---

## 8. Métricas de Éxito (90 días)

* **Inventario cubierto**: 100 % de `instalaciones_activos.xlsx` integrado.
* **Velocidad de consulta**: < 2 s para simulación N-1 en laptop estándar.
* **Demostraciones**: 3 pilotos con Transelec, CNE, SEC.
* **Adopción**: ≥ 20 usuarios diarios en exploración de vulnerabilidades.

---

*Última actualización: 3 May 2025 por Julian Crespi*


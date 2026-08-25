# Fraime

Contexto completo del producto en [idea.md](idea.md). Resumen:

Plataforma open source de generación de video con IA que detecta automáticamente
la capacidad de hardware disponible y selecciona el mejor modelo posible para
generar video, evitando los paywalls de las plataformas cerradas y la fricción
de implementar modelos open source por cuenta propia.

## Productos / Componentes

El repositorio está organizado en un directorio por componente, en la raíz:

- `api/` — Motor de generación de video, motor de detección de modelos,
  autenticación/autorización, seguridad de datos sensibles, integración cloud.
- `sdk/` — Acceso programático a la API para integrar generación de video en
  workflows (versionado en paralelo a la API, auth, soporte multi-lenguaje).
- `mcp/` — Servidor MCP para acceso agéntico a la API desde workflows de IA
  (contexto generalizado, customización de endpoints).

Cada componente es autocontenido: sus dependencias, configuración, tests y
documentación viven dentro de su propia carpeta, no en la raíz ni mezcladas
con otro componente.

## Regla de aislamiento entre componentes

**Un cambio solicitado para un componente no debe tocar archivos de otro
componente.**

- Si la tarea es sobre `api/`, no se modifica nada dentro de `sdk/` ni `mcp/`,
  y viceversa.
- Si un cambio en un componente requiere ajustar otro (p. ej. el SDK necesita
  reflejar un cambio de contrato en la API), eso se trata como una tarea
  aparte: se señala explícitamente al usuario en vez de hacerlo de forma
  implícita en el mismo cambio.
- Archivos verdaderamente compartidos por todo el repo (este `CLAUDE.md`,
  `idea.md`, configuración de CI/repo a nivel raíz) son la única excepción, y
  solo se tocan cuando el cambio pedido es explícitamente a nivel de
  repositorio, no de un componente.
- Ante ambigüedad sobre a qué componente pertenece un cambio, se pregunta
  antes de tocar código en más de una carpeta.

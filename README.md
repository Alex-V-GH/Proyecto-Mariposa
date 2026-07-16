# 🦋 Proyecto Mariposa

Simulación de agentes autónomos ("beings") que aprenden a sobrevivir en un mundo 2D mediante **Q-learning**, cada uno con su propia tabla de aprendizaje y su propia experiencia dentro de un entorno compartido.

## Estado actual: 🚧 WIP temprano / no funcional

Este proyecto está en una etapa muy inicial. El código está roto en varios lugares a propósito (o por descuido) y todavía no corre de punta a punta. Se sube igual como forma de llevar registro de la evolución del proyecto desde el principio.

## Idea general

- **`World`**: un mapa (por ahora 100x100) con paredes, recursos y peligros ("damages"), que contiene y gestiona a los `beings` que lo habitan.
- **`Being`**: un agente con posición, HP, y una Q-table propia. Se mueve por el mundo, gana o pierde HP según pise recursos o daño, y elige sus acciones con una política epsilon-greedy (explorar vs. explotar).

La idea de fondo es que, a diferencia de un único agente resolviendo un laberinto fijo, acá conviven múltiples seres aprendiendo simultáneamente su propia estrategia de supervivencia dentro del mismo entorno.

## Por qué "Mariposa"

*(completar si tenés una razón/historia para el nombre — si no, se puede borrar esta sección)*

## Roadmap / cosas pendientes

- [ ] Corregir el uso incorrecto de `super.algo()` (debería ser `self.algo()`)
- [ ] Revisar la lógica de `move()` (el `while` actual no tiene sentido tal como está)
- [ ] Repensar el dimensionamiento de la Q-table respecto a `translate_coor_to_index`
- [ ] Implementar `add_wall`, `add_resources`, `get_target`, `fucking_die` (por ahora son placeholders)
- [ ] Sistema de visualización del mundo
- [ ] Loop de entrenamiento real (episodios, métricas, gráficas de progreso)
- [ ] Definir condiciones de muerte/reinicio de un being
- [ ] Multi-agente: manejo de colisiones y espacios ocupados entre beings

## Requisitos

- Python 3.x
- numpy

## Licencia

*(a definir)*

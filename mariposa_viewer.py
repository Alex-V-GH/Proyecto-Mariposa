"""
Proyecto Mariposa - módulo de visualización (pygame).

Este archivo es INDEPENDIENTE de mariposa_dqn.py -- solo lo importa,
no lo modifica. La idea es mantener separada la simulación (mundo,
beings, redes) de cómo se dibuja, tal como pediste.

Tiene dos partes en una sola ventana:

  1. IZQUIERDA: la cuadrícula del mundo, mostrando en tiempo real
     paredes, recursos, daños y beings (cada paso de simulación se
     dibuja apenas ocurre).
  2. DERECHA: un panel que, cuando hacés click sobre un being en la
     cuadrícula, muestra su red neuronal -- capas, neuronas y
     conexiones -- y algunos datos básicos (hp, arquitectura, epsilon).

Controles:
  - Click sobre un being en la cuadrícula: lo selecciona.
  - Barra espaciadora: pausa/reanuda la simulación (útil para mirar
    con calma la red de un being sin que la posición cambie).
  - Cerrar la ventana: termina el programa.

Cómo correrlo:
    python mariposa_viewer.py
(requiere `pip install pygame`)
"""

import sys
import pygame

from mariposa_dqn import World


# ------------------------------------------------------------------
# Configuración visual. Todo lo que es "número mágico de diseño"
# vive acá arriba, para que sea fácil de tocar sin buscar en el resto
# del código.
# ------------------------------------------------------------------
CELL_SIZE = 6                      # píxeles por celda del mundo
GRID_W, GRID_H = 100, 100          # coincide con world.dimensions
GRID_PIXEL_W = GRID_W * CELL_SIZE
GRID_PIXEL_H = GRID_H * CELL_SIZE

PANEL_WIDTH = 420                  # ancho del panel de la red neuronal
WINDOW_WIDTH = GRID_PIXEL_W + PANEL_WIDTH
WINDOW_HEIGHT = max(GRID_PIXEL_H, 560)

FPS = 20
STEPS_PER_FRAME = 1                # cuántos world.step por frame (velocidad de sim)

COLORS = {
    "grid_bg": (245, 245, 245),
    "wall": (45, 45, 45),
    "resource": (60, 170, 90),
    "damage": (200, 60, 60),
    "being": (60, 110, 220),
    "being_selected": (255, 165, 0),
    "panel_bg": (24, 24, 32),
    "text": (225, 225, 225),
    "text_dim": (150, 150, 160),
    "conn_pos": (90, 180, 255),
    "conn_neg": (255, 100, 100),
    "node": (235, 235, 235),
    "node_border": (10, 10, 10),
}


class Viewer:
    """
    Encapsula la ventana, el loop principal, y el dibujo. No sabe nada
    de Q-learning ni de cómo funciona una red -- solo lee los atributos
    públicos que ya tenés en World/Being/DynamicQNetwork
    (`world.beings`, `being.pos`, `being.q_network.layer_sizes`,
    `being.q_network.weights`, etc).
    """

    def __init__(self, world, steps_per_frame=STEPS_PER_FRAME, fps=FPS):
        pygame.init()
        pygame.display.set_caption("Proyecto Mariposa - Visor")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 12)

        self.world = world
        self.steps_per_frame = steps_per_frame
        self.fps = fps

        self.selected_being = None
        self.paused = False

    # ---------------- dibujo de la cuadrícula (parte 1) ----------------

    def _cell_rect(self, pos):
        # Convención: pos = (fila, columna), igual que ya usás en
        # World (walls/resources/damages son tuplas (x, y)).
        fila, col = pos
        return pygame.Rect(col * CELL_SIZE, fila * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def draw_grid(self):
        pygame.draw.rect(self.screen, COLORS["grid_bg"], (0, 0, GRID_PIXEL_W, GRID_PIXEL_H))

        for pos in self.world.walls:
            pygame.draw.rect(self.screen, COLORS["wall"], self._cell_rect(pos))
        for pos in self.world.resources:
            pygame.draw.rect(self.screen, COLORS["resource"], self._cell_rect(pos))
        for pos in self.world.damages:
            pygame.draw.rect(self.screen, COLORS["damage"], self._cell_rect(pos))

        for being in self.world.beings:
            color = COLORS["being_selected"] if being is self.selected_being else being.color
            rect = self._cell_rect(being.pos)
            pygame.draw.circle(self.screen, color, rect.center, max(2, CELL_SIZE // 2))

        # separador entre la cuadrícula y el panel
        pygame.draw.line(
            self.screen, (0, 0, 0),
            (GRID_PIXEL_W, 0), (GRID_PIXEL_W, WINDOW_HEIGHT), 2,
        )

    def pick_being_at(self, mouse_pos):
        """
        Busca el being más cercano a donde se hizo click, con algo de
        tolerancia (por si el click no cae justo en el pixel exacto
        del centro de la celda).
        """
        mx, my = mouse_pos
        if mx > GRID_PIXEL_W:
            return None  # el click fue en el panel, no en la cuadrícula

        col = mx // CELL_SIZE
        fila = my // CELL_SIZE

        mejor = None
        mejor_dist = None
        for being in self.world.beings:
            bx, by = being.pos
            dist = (bx - fila) ** 2 + (by - col) ** 2
            if mejor_dist is None or dist < mejor_dist:
                mejor_dist = dist
                mejor = being

        # tolerancia: si ni el más cercano está a menos de ~2 celdas,
        # consideramos que no se clickeó ningún being.
        if mejor is not None and mejor_dist is not None and mejor_dist <= 4:
            return mejor
        return None

    # ---------------- dibujo del panel de red (parte 2) ----------------

    def draw_panel(self):
        panel_rect = pygame.Rect(GRID_PIXEL_W, 0, PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, COLORS["panel_bg"], panel_rect)

        being = self.selected_being
        if being is None:
            msg = self.font.render("Click en un being para ver su red", True, COLORS["text_dim"])
            self.screen.blit(msg, (GRID_PIXEL_W + 20, 20))
            return

        # --- datos básicos del being seleccionado ---
        info_lines = [
            f"Posición: {being.pos}",
            f"HP: {being.hp} / {being.maxhp}",
            f"Arquitectura: {being.q_network.layer_sizes}",
            f"Epsilon (exploración): {being.epsilon:.2f}",
            f"Experiencias guardadas: {len(being.replay_buffer)}",
        ]
        y = 15
        for line in info_lines:
            text = self.font_small.render(line, True, COLORS["text"])
            self.screen.blit(text, (GRID_PIXEL_W + 15, y))
            y += 20

        pygame.draw.line(
            self.screen, COLORS["text_dim"],
            (GRID_PIXEL_W + 15, y + 5), (GRID_PIXEL_W + PANEL_WIDTH - 15, y + 5), 1,
        )

        self.draw_network(being.q_network, top=y + 20)

    def draw_network(self, network, top):
        """
        Dibuja la red como un grafo de capas: un punto por neurona,
        una línea por conexión (peso). Grosor de línea ~ magnitud del
        peso; color indica signo (celeste = positivo, rojo = negativo)
        -- así de un vistazo se nota qué conexiones "pesan más" y en
        qué sentido empujan.
        """
        layer_sizes = network.layer_sizes
        n_layers = len(layer_sizes)

        area_left = GRID_PIXEL_W + 25
        area_right = GRID_PIXEL_W + PANEL_WIDTH - 25
        area_top = top
        area_bottom = WINDOW_HEIGHT - 20
        area_height = max(area_bottom - area_top, 10)

        # posición X de cada capa, distribuidas uniformemente
        if n_layers > 1:
            layer_x = [
                area_left + i * (area_right - area_left) / (n_layers - 1)
                for i in range(n_layers)
            ]
        else:
            layer_x = [area_left]

        # posición Y de cada neurona dentro de su capa (centradas)
        positions = []
        for size in layer_sizes:
            spacing = area_height / (size + 1)
            ys = [area_top + spacing * (i + 1) for i in range(size)]
            positions.append(ys)

        # --- conexiones (se dibujan antes que los nodos, para que
        # los nodos queden "encima") ---
        max_abs_weight = 1e-6
        for W in network.weights:
            local_max = float(abs(W).max()) if W.size else 0.0
            max_abs_weight = max(max_abs_weight, local_max)

        for li, W in enumerate(network.weights):
            x1 = layer_x[li]
            x2 = layer_x[li + 1]
            for i in range(W.shape[0]):
                y1 = positions[li][i]
                for j in range(W.shape[1]):
                    y2 = positions[li + 1][j]
                    w = float(W[i, j])
                    color = COLORS["conn_pos"] if w >= 0 else COLORS["conn_neg"]
                    # grosor proporcional al peso relativo (1 a 4 px)
                    thickness = 1 + int(3 * (abs(w) / max_abs_weight))
                    pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), thickness)

        # --- nodos (neuronas) ---
        for li, size in enumerate(layer_sizes):
            x = layer_x[li]
            for i in range(size):
                y = positions[li][i]
                pygame.draw.circle(self.screen, COLORS["node"], (int(x), int(y)), 6)
                pygame.draw.circle(self.screen, COLORS["node_border"], (int(x), int(y)), 6, 1)

        # etiquetas de capa (input / oculta N / output)
        for li in range(n_layers):
            if li == 0:
                label = "input"
            elif li == n_layers - 1:
                label = "output"
            else:
                label = f"oculta {li}"
            text = self.font_small.render(label, True, COLORS["text_dim"])
            text_rect = text.get_rect(center=(layer_x[li], area_bottom + 8))
            self.screen.blit(text, text_rect)

    # ---------------- loop principal ----------------

    def run(self, max_frames=None):
        """
        max_frames: si se pasa un número, el loop corre esa cantidad
        de frames y termina solo (pensado para pruebas automatizadas
        sin ventana interactiva). En uso normal se deja en None y el
        loop corre hasta que cierres la ventana.
        """
        running = True
        frame_count = 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    clicked = self.pick_being_at(event.pos)
                    if clicked is not None:
                        self.selected_being = clicked
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused

            if not self.paused:
                for _ in range(self.steps_per_frame):
                    # copia de la lista: si en el futuro un being
                    # "muere" y se remueve de world.beings a mitad de
                    # loop, esto evita problemas de iterar una lista
                    # que cambia de tamaño mientras la recorremos.
                    for being in list(self.world.beings):
                        being.step(self.world)

            self.screen.fill(COLORS["grid_bg"])
            self.draw_grid()
            self.draw_panel()
            pygame.display.flip()
            self.clock.tick(self.fps)

            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                running = False

        pygame.quit()


if __name__ == "__main__":
    world = World()
    # un par de beings extra para tener algo interesante que mirar
    world.spawn_being((5, 5),(20, 20, 20))
    world.spawn_being((10, 4),(255, 255, 180))
    world.spawn_being((55, 88),(200, 200, 0))
    world.spawn_being((43, 64),(60, 0, 0))
    world.spawn_being((93, 56),(0, 0, 255))

    viewer = Viewer(world)
    viewer.run()
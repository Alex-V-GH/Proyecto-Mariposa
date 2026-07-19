"""
Proyecto Mariposa - versión con red neuronal (DQN) en reemplazo de la Q-table.

Este archivo parte del código que compartiste y aplica los cambios que
hablamos:

  1. El estado ya no es un índice de tabla: es un vector de features.
  2. La Q-table se reemplaza por una red neuronal chica, implementada a
     mano con numpy (sin PyTorch/TensorFlow, para no meter una dependencia
     pesada todavía -- lo podemos migrar después si querés).
  3. Se separa el "vivir un paso" en fases bien claras:
     observar -> elegir acción -> ejecutar -> observar resultado ->
     guardar transición -> aprender (con experience replay).
  4. Cada Being tiene SU PROPIA red y su propio buffer de experiencia,
     como pediste (nada compartido entre beings).

Cada cambio importante está marcado con  >>> CAMBIO:  para que puedas
rastrear qué se tocó y por qué, sin perder el hilo de tu código original.
"""

import numpy as np
import random
from collections import deque
import time


class World:
    def __init__(self) -> None:
        self.dimensions = (100, 100)
        self.walls = []
        for x in range(100):
            for y in range (100):
                if x > 0 and x < 99 and y > 0 and y < 99:
                    pass
                else:
                    self.walls.append((x,y))
        print(self.walls)
        self.resources = []
        for c in range(50):
            tup = (random.randint(2,98), random.randint(2,98))
            if tup not in self.resources:
                self.resources.append(tup)
        self.damages = []
        for c in range(3500):
            tup = (random.randint(2,98), random.randint(2,98))
            if tup not in self.resources and tup not in self.damages:
                self.damages.append(tup)
        self.beings_positions = []
        self.beings = []
        self.spawn_being((1, 1),(0, 255, 255))

    def add_wall(self):
        1

    def add_resources(self):
        1

    def translate_coor_to_index(self, pos):
        # >>> CAMBIO: esta función ya NO se usa para armar el estado de
        # la red (la red no necesita un índice de tabla). La dejamos
        # por si te sirve para debug o para otra cosa más adelante.
        return pos[0] * self.dimensions[1] + pos[1]

    def spawn_being(self, pos, color):
        self.beings_positions.append(pos)
        self.beings.append(Being(pos, color))

    def is_spot_valid(self, pos):
        if pos in self.walls or pos in self.beings_positions:
            return False
        else:
            return True

    def is_spot_damage(self, pos):
        if pos in self.damages:
            return 1
        else:
            return 0

    def is_spot_resource(self, pos):
        if pos in self.resources:
            return 1
        else:
            return 0

    def is_spot_others(self, pos):
        # >>> CAMBIO (bugfix, no relacionado a la red): decía
        # `self.beings.positions`, que no existe (`beings` es una lista
        # de objetos Being, no tiene atributo `.positions`). Lo que ya
        # tenías armado para esto es `self.beings_positions`.
        if pos in self.beings_positions:
            return 1  # más adelante podrías devolver un id en vez de 1
        else:
            return 0  # >>> CAMBIO: antes devolvía None; para meterlo en
            # un vector numérico de estado conviene 0 en vez de None.

    def get_neighbors(self, pos):
        """
        >>> CAMBIO (nuevo): no existía. Lo necesitamos para armar el
        vector de estado que le damos a la red: qué hay arriba, abajo,
        izquierda y derecha del being. Devuelve las 4 posiciones vecinas
        en el mismo orden que Being.movements (sin contar "quedarse quieto").
        """
        x, y = pos
        return [
            (x - 1, y),  # arriba
            (x + 1, y),  # abajo
            (x, y - 1),  # izquierda
            (x, y + 1),  # derecha
            (x - 1, y -1),  # arriba izquierda
            (x + 1, y -1),  # abajo izquierda
            (x - 1, y + 1),  # arriba derecha
            (x + 1, y + 1),  # abajo derecha
        ]


class DynamicQNetwork:
    """
    >>> CAMBIO (Parte 1 - red de N capas dinámicas): esta clase
    reemplaza a `SimpleQNetwork`, que tenía la arquitectura (2 capas)
    escrita a mano y fija.

    Acá la arquitectura se define con una lista `layer_sizes`, por
    ejemplo [7, 16, 5] (una capa oculta) o [7, 12, 8, 5] (dos capas
    ocultas) o incluso [7, 5] (sin capas ocultas, directo input->output).
    Esto es justamente lo que necesitás para que la reproducción pueda
    mutar cantidad de neuronas y de capas: cada being puede tener una
    lista distinta, y el forward/backward se adaptan solos, sin tener
    que reescribir código por cada arquitectura posible.

    Convención: ReLU en todas las capas ocultas, sin activación (lineal)
    en la capa de salida -- así los Q-values pueden ser negativos o
    positivos libremente, sin el techo/piso que impondría una ReLU o
    una sigmoid ahí.
    """

    def __init__(self, layer_sizes, lr=0.01):
        # layer_sizes = [tamaño_input, tamaño_capa1, ..., tamaño_output]
        assert len(layer_sizes) >= 2, "hace falta al menos input y output"
        self.layer_sizes = list(layer_sizes)
        self.lr = lr

        self.weights = []
        self.biases = []
        for i in range(len(layer_sizes) - 1):
            in_size, out_size = layer_sizes[i], layer_sizes[i + 1]
            self.weights.append(np.random.randn(in_size, out_size) * 0.1)
            self.biases.append(np.zeros(out_size))

    @property
    def num_layers(self):
        return len(self.weights)

    def forward(self, state):
        """
        Igual que antes conceptualmente: dado un estado, devuelve los
        Q-values (uno por acción) y un cache con lo necesario para el
        backward. La diferencia es que ahora recorremos un LOOP sobre
        todas las capas, en vez de tener z1/a1/z2 hardcodeados.
        """
        activations = [state]  # activations[i] = entrada de la capa i
        zs = []  # zs[i] = salida sin activar (pre-activación) de la capa i

        a = state
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            z = a @ W + b
            zs.append(z)
            is_output_layer = (i == self.num_layers - 1)
            a = z if is_output_layer else np.maximum(0, z)  # lineal en output, ReLU en ocultas
            activations.append(a)

        q_values = activations[-1]
        cache = (activations, zs)
        return q_values, cache

    def train_step(self, state, action, target_q):
        """
        Backward genérico: en vez de escribir a mano dW1/dW2 para una
        arquitectura fija, recorremos las capas DE ATRÁS PARA ADELANTE
        (por eso `reversed`), aplicando la regla de la cadena capa por
        capa. Esto funciona sin importar cuántas capas tenga la red.
        """
        q_values, (activations, zs) = self.forward(state)
        predicted = q_values[action]
        error = predicted - target_q  # derivada de 0.5*(pred-target)^2

        # Gradiente en la salida: solo la acción tomada tiene error;
        # el resto de las acciones no participó en esta predicción.
        delta = np.zeros_like(q_values)
        delta[action] = error

        grads_w = [None] * self.num_layers
        grads_b = [None] * self.num_layers

        for i in reversed(range(self.num_layers)):
            a_prev = activations[i]  # entrada que recibió esta capa
            grads_w[i] = np.outer(a_prev, delta)
            grads_b[i] = delta

            if i > 0:
                # Propagamos el gradiente hacia la capa anterior.
                d_a_prev = delta @ self.weights[i].T
                z_prev = zs[i - 1]
                delta = d_a_prev * (z_prev > 0)  # derivada de ReLU

        for i in range(self.num_layers):
            self.weights[i] -= self.lr * grads_w[i]
            self.biases[i] -= self.lr * grads_b[i]

        return error ** 2  # "loss", por si querés loguearlo


class Being:
    def __init__(self, location=(1, 1), color = (255, 0, 255), hidden_layers=None) -> None:
        self.movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        self.num_movements = len(self.movements)
        self.pos = location
        self.pos_target = None
        self.color = color
        self.dead = False

        self.hp = 10
        self.maxhp = 10

        # >>> CAMBIO: se borraron max_states, stat_combinations y
        # self.q_table. Ya no armamos una tabla con todas las
        # combinaciones posibles de vecinos x hp; en su lugar el estado
        # es un vector de tamaño fijo, sin importar cuántas
        # combinaciones puedan darse.

        # Vector de estado: [x_norm, y_norm, hp_norm,
        #                    vecino_arriba, vecino_abajo,
        #                    vecino_izq,    vecino_der]
        # cada "vecino_X" es (es_recurso - es_daño), igual que hp_delta.
        self.state_size = 11 #casillas vecinas(8), hp marker (1) x(1) y(1) vecinos(1)

        # >>> CAMBIO (Parte 1): en vez de una arquitectura fija, la red
        # se arma a partir de `hidden_layers` -- una lista con la
        # cantidad de neuronas de cada capa oculta. Por default usamos
        # una sola capa de 16 (igual que antes), pero cualquier being
        # (o su descendencia mutada) puede recibir otra lista distinta,
        # ej: [] (sin capas ocultas), [8, 8], [24, 12, 6], etc.
        if hidden_layers is None:
            hidden_layers = [16]
        self.hidden_layers = hidden_layers

        layer_sizes = [self.state_size, *hidden_layers, self.num_movements]

        # >>> CAMBIO: la Q-table se reemplaza por esta red, propia de
        # este being (nada compartido con otros beings).
        self.q_network = DynamicQNetwork(layer_sizes=layer_sizes)

        # >>> CAMBIO (nuevo): memoria de experiencias para entrenar en
        # lotes en vez de aprender de a un solo paso ("experience
        # replay" -- estabiliza mucho el entrenamiento con redes).
        self.replay_buffer = deque(maxlen=2000)

        self.lr = 0.1  # ya no se usa para la red (tiene su lr propio
        # adentro); lo dejamos por si lo usás en otro lado.
        self.gamma = 0.94  # sigue siendo relevante: cuánto le importa el futuro
        self.epsilon = 0.2  # explorar vs explotar, se mantiene igual

    def get_state_vector(self, world):
        """
        >>> CAMBIO (nuevo): reemplaza a
        `translate_coor_to_index` + `q_table[indice, hp]`.
        Arma el vector numérico que la red recibe como entrada.
        """
        x, y = self.pos
        vecinos = world.get_neighbors(self.pos)
        vecinos_valor = [
            world.is_spot_resource(v) - world.is_spot_damage(v)
            for v in vecinos
        ]
        return np.array(
            [
                x / world.dimensions[0],
                y / world.dimensions[1],
                self.hp / self.maxhp,
                *vecinos_valor,
            ],
            dtype=np.float32,
        )

    def chose_action(self, state_vector):
        """
        >>> CAMBIO: misma lógica epsilon-greedy de siempre; el "exploit"
        ahora consulta a la red (forward pass) en vez de leer una fila
        de tabla.
        """
        if random.random() < self.epsilon:
            return random.randint(0, self.num_movements - 1)
        q_values, _ = self.q_network.forward(state_vector)
        return int(np.argmax(q_values))

    def calculate_stats(self, pos, world):
        hp_delta = world.is_spot_resource(pos) - world.is_spot_damage(pos)
        self.hp += hp_delta
        if self.hp > self.maxhp:
            self.hp = self.maxhp
        return hp_delta

    def calculate_reward(self, delta):
        reward = (self.maxhp + 1 - self.hp) / self.maxhp * delta
        return reward

    def fucking_die(self, world):
        self.dead = True
        self.color =(0,0,0)


    def step(self, world):
        """
        >>> CAMBIO (nuevo): reemplaza al `move()` viejo.

        El `move()` original tenía `while world.is_spot_valid(new_pos)`
        arrancando con new_pos=(-1,-1). Como (-1,-1) probablemente
        cuenta como "válido" para is_spot_valid (no está en walls ni en
        beings_positions), el while podía no ejecutarse nunca, o si
        ejecutaba, movía al being repetidamente en el mismo `action`
        dentro de un solo llamado a move() -- no era el comportamiento
        de "un paso" que buscabas.

        Acá separamos las fases de un paso de vida del being:
        1. Observar el estado actual.
        2. Elegir una acción.
        3. Ejecutar el movimiento (si el destino es válido).
        4. Observar el nuevo estado y calcular el reward.
        5. Guardar la transición en el replay buffer.
        6. Aprender de un lote de experiencias pasadas.
        """
        if not self.dead:
            # 1. Observar estado actual
            state = self.get_state_vector(world)

            # 2. Elegir acción
            action = self.chose_action(state)
            movement = self.movements[action]
            new_pos = (self.pos[0] + movement[0], self.pos[1] + movement[1])

            # 3. Ejecutar (si no es válido, se queda en el lugar, como
            # "chocar contra pared": mismo pos, sin bonus/penalidad extra
            # por el choque en sí)
            if world.is_spot_valid(new_pos):
                if self.pos in world.beings_positions:
                    world.beings_positions.remove(self.pos)
                self.pos = new_pos
                world.beings_positions.append(self.pos)

            # 4. Observar resultado y calcular reward
            hp_delta = self.calculate_stats(self.pos, world)
            reward = self.calculate_reward(hp_delta)
            next_state = self.get_state_vector(world)

            # 5. Guardar transición
            self.replay_buffer.append((state, action, reward, next_state))

            # 6. Aprender (si ya hay suficiente experiencia acumulada)
            self.learn()

            #7. chequear si se murio, y correr dicha secuencia si se amerita.
            if self.hp <= 0:
                self.fucking_die(world)

            return reward

    def learn(self, batch_size=16):
        """
        >>> CAMBIO (nuevo): reemplaza al update directo de la Q-table
        (`Q[s,a] = Q[s,a] + lr*(...)`). Con red neuronal no alcanza con
        tocar un solo valor por paso: se entrena en mini-lotes de
        experiencias pasadas para que la red no "olvide" lo aprendido
        antes ni se desestabilice de un paso a otro.
        """
        if len(self.replay_buffer) < batch_size:
            return  # todavía no hay suficiente experiencia acumulada

        batch = random.sample(self.replay_buffer, batch_size)
        for state, action, reward, next_state, in batch:
            next_q_values, _ = self.q_network.forward(next_state)
            target_q = reward + self.gamma * np.max(next_q_values)

            self.q_network.train_step(state, action, target_q)


if __name__ == "__main__":
    # >>> CAMBIO (nuevo): mini loop de ejemplo, solo para confirmar que
    # el being puede dar pasos, acumular experiencia y aprender sin
    # explotar en errores. NO es un entrenamiento serio (eso -- episodios,
    # métricas, gráficas de progreso -- es el próximo paso del roadmap).
    world = World()
    being = world.beings[0]

    for paso in range(500):
        reward = being.step(world)
        print(f"Paso {paso}: pos={being.pos} hp={being.hp} reward={reward:.2f}")
        time.sleep(0.2)

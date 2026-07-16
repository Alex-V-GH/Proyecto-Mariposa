import numpy as np
import random

class World ():
    def __init__(self) -> None:
        self.dimensions = (100, 100)
        self.walls = [(0, 0), (1, 0), (2, 0), (3, 0)]
        #hacer cuadrado grande exterior
        self.resources = [(4, 3), (5, 6), (3, 2), (1, 3)]
        self.damages = [(5, 7), (8, 2), (1, 6), (3, 3)]
        self.beings_positions = []
        self.beings = []
        self.spawn_being((1,1))
    def add_wall(self):
        1
    def add_resources(self):
        1
    def translate_coor_to_index(self, pos):
        return pos[0] * self.dimensions[1] + pos[1]

    #beings spawns
    def spawn_being(self,pos):
        self.beings_positions.append(pos)
        self.beings.append(Being(pos))

    #calculations for beings
    def is_spot_valid(self, pos):
        if pos in self.walls or pos in self.beings_positions:
            return False
        else:
            return True
    def is_spot_damage(self,pos):
        if pos in self.damages:
            return 1
        else:
            return 0
    def is_spot_resource(self,pos):
        if pos in self.resources:
            return 1
        else:
            return 0
    def is_spot_others(self,pos):
        if pos in self.beings.positions:
            return 1 #index de being, u otro identificador (color, maybe?)
        else:
            return None

class Being ():
    def __init__(self, location = [1,1]) -> None:
        self.movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        self.num_movements = len(self.movements)
        print(f"Possible movements: {self.num_movements}")
        self.pos = location
        self.pos_target = None

        max_states = 9 * 5
        # places around | props_variety (wall, resource, others, damage, empty) | hp

        stat_combinations = 10 # * x * x
        #only hp by now | 
        self.hp = 10
        self.maxhp = 10

        print(f"total situational combinations: {max_states * stat_combinations}")

        self.q_table = np.zeros((max_states, stat_combinations, self.num_movements))
        print("Q_TABLE\n\n", self.q_table)

        self.lr = 0.1 #learning rate. 0 - 1
        self.gamma = 0.94 #anxiety (thinks about future) 0 - 1
        self.epsilon = 0.2 #explore (1) vs exploit (0)

    def get_target():
        1

    def move(self, action):
        new_pos = (-1,-1)
        while super.is_spot_valid(new_pos):
            movement = self.movements[action]
            new_pos = (self.pos[0] + movement[0], self.pos[1] + movement[1])
            self.calculate_reward(self.calculate_stats(new_pos))
            self.pos = new_pos
    
    def calculate_stats(self,pos):
        hp_delta = super.is_spot_resource(pos) - super.is_spot_damage(pos)
        self.hp += hp_delta
        if self.hp > self.maxhp:
            self.hp = self.maxhp
        if self.hp <= 0:
            self.fucking_die()
        return hp_delta
        
    def fucking_die(self):
        1
 
    def calculate_reward(self,delta):
        reward = (self.maxhp + 1 - self.hp) / self.maxhp * delta
        #by now only calculates on hp. the less hp it has, the more important it is.
        return reward

    def chose_action(self):
        randomness = random.random()
        if randomness < self.epsilon:   #explore
            action = random.randint(0, self.num_movements - 1)
        else: #exploit
            state_index = super.translate_coor_to_index(self.pos)
            action = np.argmax(self.q_table[state_index, :])
        return action





# ============================================
# PASO 11: VER EL MAPA (para entenderlo mejor)
# ============================================
print("\n=== MAPA DEL MUNDO ===")
print(" C0 C1 C2 C3 C4")
for fila in range(5):
 linea = f"F{fila} "
 for columna in range(5):
 if (fila, columna) == estado_inicial:
 linea += " " 🚀 # Inicio
 elif (fila, columna) == estado_objetivo:
 linea += " " 🏆 # Meta
 elif (fila, columna) in obstaculos:
 linea += " " 🧱 # Obstáculo
 else:
 linea += " " ⬜ # Camino libre
 print(linea)
# ============================================
# PASO 12: ¡ENTRENAMIENTO! (EL ROBOT APRENDE)
# ============================================
print("\n=== COMIENZA EL ENTRENAMIENTO ===\n" 🧠 )
# Lista para guardar las recompensas de cada partida
recompensas_por_episodio = []
# Jugar el número de episodios (partidas) especificado
for episodio in range(episodios):

 # Cada episodio empieza en la casilla inicial
 estado = estado_inicial
 recompensa_total = 0
 terminado = False
 pasos = 0

 # El robot juega hasta llegar a la meta (o máximo 100 pasos)
 while not terminado and pasos < 100:

 # 1. El robot ELIGE qué hacer (explorar o explotar)
 accion = elegir_accion(estado, epsilon)

 # 2. El robot EJECUTA la acción
 nuevo_estado = tomar_accion(estado, accion)

 # 3. Calcular la RECOMPENSA
 recompensa = calcular_recompensa(nuevo_estado)

 # 4. Convertir estados a índices para usar la tabla Q
 indice_estado = estado_a_indice(estado)
 indice_nuevo_estado = estado_a_indice(nuevo_estado)

 # 5. APRENDER: Actualizar la tabla Q (¡LO MÁS IMPORTANTE!)
 # Fórmula: Q(s,a) = Q(s,a) + α × [r + γ × max(Q(s')) - Q(s,a)]
 mejor_valor_futuro = np.max(Q[indice_nuevo_estado, :])
 valor_actual = Q[indice_estado, accion]
 nuevo_valor = valor_actual + alpha * (recompensa + gamma * mejor_valor_futuro - valor_actual)
 Q[indice_estado, accion] = nuevo_valor

 # 6. Actualizar para el siguiente paso
 recompensa_total += recompensa
 estado = nuevo_estado
 pasos += 1

 # Si llegó a la meta, termina el episodio
 if estado == estado_objetivo:
 terminado = True

 # Guardar la recompensa de este episodio
 recompensas_por_episodio.append(recompensa_total)

 # Mostrar progreso cada 10 episodios
 if (episodio + 1) % 10 == 0:
 print(f" Episodio 📊 {episodio+1}/{episodios} - Recompensa: {recompensa_total}")
print("\n=== ENTRENAMIENTO COMPLETADO ===\n" ✅ )
# ============================================
# PASO 13: VER LA TABLA Q FINAL
# ============================================
print("=== TABLA Q (LO QUE APRENDIÓ EL ROBOT) ===\n")
print("Cada fila es una casilla, cada columna una acción:")
print("Acciones: 0= , 1= , 2= , 3= \n" ↑ ↓ ← → )
for i in range(num_estados):
 valores = Q[i, :]
 print(f"Casilla {i:2d}: [{valores[0]:6.1f} {valores[1]:6.1f} {valores[2]:6.1f} {valores[3]:6.1f}]")
# ============================================
# PASO 14: VER LA POLÍTICA (lo que aprendió el robot)
# ============================================
print("\n=== POLÍTICA APRENDIDA (hacia dónde ir en cada casilla) ===\n")
simbolos_acciones = [" " ↑ , " " ↓ , " " ← , " " → ]
print(" C0 C1 C2 C3 C4")
for fila in range(5):
 linea = f"F{fila} "
 for columna in range(5):
 estado = (fila, columna)

 # Si es obstáculo
 if estado in obstaculos:
 linea += " " 🧱
 # Si es la meta
 elif estado == estado_objetivo:
 linea += " " 🏆
 else:
 indice = estado_a_indice(estado)
 mejor_accion = np.argmax(Q[indice, :])
 linea += f"{simbolos_acciones[mejor_accion]} "
 print(linea)
# ============================================
# PASO 15: DEMOSTRACIÓN DE UNA PARTIDA
# ============================================
print("\n=== DEMOSTRACIÓN: EL ROBOT USA LO QUE APRENDIÓ ===\n")
# Jugar una partida sin exploración (epsilon = 0)
estado = estado_inicial
camino = [estado]
terminado = False
pasos = 0
print(f" Empieza en: 🚀 {estado}")
while not terminado and pasos < 50:

 # Elegir la mejor acción según la tabla Q (sin exploración)
 indice = estado_a_indice(estado)
 mejor_accion = np.argmax(Q[indice, :])
 accion = mejor_accion

 # Ejecutar acción
 nuevo_estado = tomar_accion(estado, accion)
 simbolo = simbolos_acciones[accion]

 estado = nuevo_estado
 camino.append(estado)
 pasos += 1

 print(f" Paso {pasos}: {simbolo} → {estado}")

 if estado == estado_objetivo:
 print("\n ¡EL ROBOT LLEGÓ A LA META! " 🎉🎉🎉 🎉🎉🎉 )
 terminado = True
if not terminado:
 print("\n No llegó a la meta en 50 pasos" ❌ )
# ============================================
# PASO 16: GRÁFICA DE PROGRESO
# ============================================
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 5))
plt.plot(recompensas_por_episodio)
plt.xlabel("Número de partida (episodio)")
plt.ylabel("Recompensa total")
plt.title(" Progreso del aprendizaje del robot" 📈 )
plt.grid(True, alpha=0.3)
plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
# Calcular promedio cada 10 partidas
if len(recompensas_por_episodio) >= 10:
 promedios = []
 for i in range(0, len(recompensas_por_episodio), 10):
 grupo = recompensas_por_episodio[i:i+10]
 promedios.append(sum(grupo)/len(grupo))
 plt.plot(range(0, len(recompensas_por_episodio), 10)[:len(promedios)],
 promedios, 'r', linewidth=2, label='Promedio cada 10 partidas')
 plt.legend()
plt.show()
import random  


# Lista de acciones posibles en cada estado.
ACTIONS = ["up", "down", "left", "right", "stay"]


# -----------------------------------------------------------------------------
# Generación del entorno y "fuerza del río"
# -----------------------------------------------------------------------------

def river_strength_for_cols(rows, cols):
    """
    Crea una lista strengths con un número por cada columna del tablero.

    strengths[j] = probabilidad de que el río te empuje hacia ABAJO
    cuando intentas hacer una acción que NO sea "down".
    """
    strengths = []

    # Recorremos cada columna 
    for j in range(cols):
        # en la primera y última columna no hay corriente (0.0)
        if j == 0 or j == cols - 1:
            strengths.append(0.0)

        # En el resto, elegimos una corriente aleatoria (ej: 0.3, 0.6, 0.9...)
        else:
            strengths.append(round(random.uniform(0.06, 0.94), 1))

    return strengths


def create_river_grid(rows, cols, nislas):
    """
    Crea el tablero (grid) como lista de listas (matriz).

    - 'R' = río (se puede estar aquí)
    - 'I' = isla (obstáculo: NO se puede entrar)
    - 'E' = salida (objetivo final)

    También coloca:
    - nislas islas aleatorias
    - una salida en la última columna
    """
    # Creamos una matriz llena de "R" (todo río inicialmente)
    grid = [["R" for _ in range(cols)] for _ in range(rows)]

    # Vamos a colocar islas sin repetir posición
    placed = set()  # guardamos coordenadas ya usadas para no duplicar islas

    # Mientras falten islas por colocar:
    while len(placed) < nislas:

        # Elegimos una fila al azar (evitamos fila 0 y última por comodidad)
        i = random.randint(1, rows - 2)

        # Elegimos una columna al azar
        j = random.randint(0, cols - 1)

        # Si esa isla no estaba ya colocada, la colocamos
        if (i, j) not in placed:
            placed.add((i, j))
            grid[i][j] = "I"  # marcamos la celda como isla

    # Ahora colocamos la salida en la ÚLTIMA columna (col = cols-1)
    exit_i = random.randint(0, rows - 1)

    # Si por casualidad cayó sobre una isla, buscamos otra fila
    while grid[exit_i][cols - 1] == "I":
        exit_i = random.randint(0, rows - 1)

    # Colocamos la salida
    grid[exit_i][cols - 1] = "E"

    return grid


# -----------------------------------------------------------------------------
# Utilidades para movimientos y límites
# -----------------------------------------------------------------------------

def in_bounds(rows, cols, pos):
    """
    Devuelve True si pos=(i,j) está dentro del tablero.
    """
    i, j = pos
    return 0 <= i < rows and 0 <= j < cols


def intended_move(pos, action):
    """
    Devuelve a qué celda irías si el mundo fuese determinista y NO hubiese corriente.

    Esto es solo el "deseo" del agente.
    La corriente se aplica luego en transition_probs.
    """
    i, j = pos

    if action == "up":
        return (i - 1, j)

    if action == "down":
        return (i + 1, j)

    if action == "left":
        return (i, j - 1)

    if action == "right":
        return (i, j + 1)

    # Si action == "stay"
    return (i, j)


# -----------------------------------------------------------------------------
# Transiciones P(s' | s, a) 
# -----------------------------------------------------------------------------

def transition_probs(grid, strengths, state, action):
    """
    Devuelve un diccionario con probabilidades de transición.

    Si estamos en state=(i,j) y elegimos action:
      - devuelve algo como:
          { (i1,j1): 0.7, (i2,j2): 0.3 }
        que significa:
          70% acabas en (i1,j1)
          30% acabas en (i2,j2)

    - Si action == "down": NO hay aleatoriedad (es determinista).
    - Si action != "down":
        p_down = strengths[columna]
        con prob p_down: el río te empuja hacia abajo
        con prob 1-p_down: haces la acción que querías
    """
    rows, cols = len(grid), len(grid[0])
    i, j = state

    def valid_or_stay(dest):
        """
        Si dest es inválido (fuera del tablero o isla),
        entonces devolvemos state (te quedas donde estabas).
        """
        if not in_bounds(rows, cols, dest):
            return state
        di, dj = dest
        if grid[di][dj] == "I":
            return state
        return dest

    # Caso 1: acción "down" determinista
    if action == "down":
        dest = valid_or_stay(intended_move(state, "down"))
        return {dest: 1.0}

    # Caso 2: acción estocástica por corriente
    p_down = strengths[j]     # probabilidad de arrastre depende de la columna j
    p_dir = 1 - p_down        # probabilidad de que ocurra el movimiento deseado

    # Destino si sale bien la acción deseada
    dest_dir = valid_or_stay(intended_move(state, action))

    # Destino si te arrastra hacia abajo
    dest_down = valid_or_stay(intended_move(state, "down"))

    # Guardamos probabilidades en un diccionario
    probs = {}
    probs[dest_dir] = probs.get(dest_dir, 0) + p_dir
    probs[dest_down] = probs.get(dest_down, 0) + p_down

    return probs


# -----------------------------------------------------------------------------
# Estados del problema y salida
# -----------------------------------------------------------------------------

def all_states(grid):
    """
    Devuelve una lista con todos los estados válidos.
    Aquí, un estado es una coordenada (i,j) donde NO hay isla.
    """
    states = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] != "I":
                states.append((i, j))
    return states


def find_exit(grid):
    """
    Busca la celda marcada como 'E' y devuelve su posición.
    """
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == "E":
                return (i, j)
    raise ValueError("Salida no encontrada")


# -----------------------------------------------------------------------------
# Recompensas 
# -----------------------------------------------------------------------------

def reward(grid, s, a, sp, exit_pos):
    """
    Función de recompensa.

    - Cada paso cuesta -1 (así el agente intenta tardar poco).
    - Llegar a la salida da +100 extra (así el agente quiere llegar sí o sí).
    """
    r = -1  # coste por mover / actuar

    # Si el estado siguiente sp es la salida, damos premio
    if sp == exit_pos:
        r += 100

    return r


# -----------------------------------------------------------------------------
# Value Iteration (cómo calculamos la mejor estrategia)
# -----------------------------------------------------------------------------

def value_iteration(grid, strengths, gamma=0.99, theta=1e-6):
    """
    Resuelve el MDP usando Value Iteration.
    """
    states = all_states(grid)
    exit_pos = find_exit(grid)

    # Inicializamos V(s)=0 para todos los estados
    V = {s: 0.0 for s in states}

    # Repetimos hasta convergencia
    while True:
        delta = 0  # máximo cambio de valor en esta iteración

        for s in states:

            # Si estamos en la salida, no actualizamos (estado terminal)
            if s == exit_pos:
                continue

            # Calculamos el mejor valor posible desde este estado s
            best = float("-inf")

            # Probamos cada acción posible
            for a in ACTIONS:

                # Probabilidades de ir a cada estado siguiente sp
                probs = transition_probs(grid, strengths, s, a)

                # q = valor esperado de elegir acción a en s
                q = 0

                for sp, p in probs.items():
                    q += p * (reward(grid, s, a, sp, exit_pos) + gamma * V[sp])

                # Nos quedamos con la mejor acción (máximo q)
                best = max(best, q)

            # Guardamos cuánto cambia V(s)
            delta = max(delta, abs(V[s] - best))

            # Actualizamos V(s)
            V[s] = best

        # Si ya casi no cambia nada, paramos
        if delta < theta:
            break

    # Con V ya calculado, sacamos la política óptima
    policy = {}

    for s in states:
        if s == exit_pos:
            policy[s] = "stay"
            continue

        best_a = "stay"
        best_q = float("-inf")

        # Probamos acciones para elegir la que mejor valor esperado da
        for a in ACTIONS:
            probs = transition_probs(grid, strengths, s, a)
            q = 0
            for sp, p in probs.items():
                q += p * (reward(grid, s, a, sp, exit_pos) + gamma * V[sp])

            if q > best_q:
                best_q = q
                best_a = a

        policy[s] = best_a

    return V, policy


# -----------------------------------------------------------------------------
# Impresión del tablero y de la política 
# -----------------------------------------------------------------------------

def print_grid(grid, start):
    """
    Imprime el tablero del río.
    Marcamos el inicio con 'S'.
    """
    for i in range(len(grid)):
        row = []
        for j in range(len(grid[0])):
            if (i, j) == start:
                row.append("S")
            else:
                row.append(grid[i][j])
        print(" ".join(row))


def print_policy(grid, policy, start):
    """
    Imprime la política óptima como flechas.

    - ↑ ↓ ← → indican la acción recomendada en cada celda.
    - █ representa islas (obstáculo).
    - E es la salida.
    """
    arrows = {"up": "↑", "down": "↓", "left": "←", "right": "→", "stay": "·"}

    for i in range(len(grid)):
        row = []
        for j in range(len(grid[0])):
            if (i, j) == start:
                row.append("S")
            elif grid[i][j] == "I":
                row.append("█")
            elif grid[i][j] == "E":
                row.append("E")
            else:
                row.append(arrows[policy[(i, j)]])
        print(" ".join(row))


# -----------------------------------------------------------------------------
# Simulación: seguimos la política óptima y vemos qué pasa (con azar)
# -----------------------------------------------------------------------------

def simulate(grid, strengths, policy, start, max_steps=100):
    """
    Simula una partida siguiendo la política óptima.

    Importante:
    - Aunque la política sea óptima "en promedio", en una simulación concreta
      puede haber mala suerte (arrastre hacia abajo varias veces).
    """
    exit_pos = find_exit(grid)
    s = start

    total = 0  # recompensa acumulada

    for t in range(max_steps):

        # Si llegamos a la salida, terminamos
        if s == exit_pos:
            break

        # Elegimos acción recomendada por la política
        a = policy[s]

        # Miramos posibles estados siguientes y sus probabilidades
        probs = transition_probs(grid, strengths, s, a)

        # Elegimos al azar sp según las probabilidades (muestreo)
        r = random.random()  # número aleatorio entre 0 y 1
        acc = 0

        for sp, p in probs.items():
            acc += p
            if r <= acc:
                break

        # Calculamos recompensa de esta transición y acumulamos
        total += reward(grid, s, a, sp, exit_pos)

        # Mostramos el paso por pantalla (sirve para capturas en la memoria)
        print(f"t={t}  s={s}  a={a}  -> {sp}")

        # Avanzamos al siguiente estado
        s = sp

    print("Recompensa total:", total)


if __name__ == "__main__": 
    rows, cols = 7, 6

    # Crea el tablero y la corriente
    grid = create_river_grid(rows, cols, nislas=2)
    strengths = river_strength_for_cols(rows, cols)

    # Inicio fijo
    start = (0, 0)

    print("\nGrid del río:")
    print_grid(grid, start)

    print("\nFuerza del río por columna:", strengths)

    # Resolvemos el MDP
    V, policy = value_iteration(grid, strengths)

    print("\nPolítica óptima (flechas):")
    print_policy(grid, policy, start)

    print("\nSimulación siguiendo la política:")
    simulate(grid, strengths, policy, start)


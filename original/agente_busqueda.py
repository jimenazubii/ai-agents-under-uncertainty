from collections import deque

from mapa_conocido import crear_tablero_conocido, mostrar_tablero
from perceptos_willard import (
    percept,
    crear_KB,
    deducir_desde_perceptos,
    actualizar_tablero_conocido_desde_KB,
)


def bfs_plan(tablero: list[list[str]]) -> list[str] | None:
    """
    Busca (con BFS) un plan seguro desde (0,0) hasta la salida 'S',
    cumpliendo que el capitán ha recogido antes al coronel 'CW'.
    """
    n = len(tablero)

    start = (0, 0, False)  # (x, y, lleva_cw)
    cola = deque([start])
    visitados = {start}

    # Para reconstrucción del camino
    padre = {start: None}
    accion_desde_padre = {start: None}

    movimientos = {
        "U": (-1, 0),
        "D": (1, 0),
        "L": (0, -1),
        "R": (0, 1),
    }

    while cola:
        x, y, lleva_cw = cola.popleft()

        # Objetivo: estar en 'S' habiendo recogido 'CW'
        if tablero[x][y] == "S" and lleva_cw:
            plan: list[str] = []
            estado = (x, y, lleva_cw)
            while padre[estado] is not None:
                plan.append(accion_desde_padre[estado])
                estado = padre[estado]
            plan.reverse()
            return plan

        # Expandimos vecinos (acciones)
        for a, (dx, dy) in movimientos.items():
            nx, ny = x + dx, y + dy

            # Fuera del tablero
            if not (0 <= nx < n and 0 <= ny < n):
                continue

            celda = tablero[nx][ny]

            # Nunca entramos en precipicio ni en enemigo vivo
            if celda == "P" or celda == "E":
                continue

            nuevo_lleva_cw = lleva_cw or (celda == "CW")
            nuevo_estado = (nx, ny, nuevo_lleva_cw)

            if nuevo_estado not in visitados:
                visitados.add(nuevo_estado)
                padre[nuevo_estado] = (x, y, lleva_cw)
                accion_desde_padre[nuevo_estado] = a
                cola.append(nuevo_estado)

    # No se ha encontrado plan seguro
    return None


def ejecutar_plan_automatico(tablero: list[list[str]]) -> None:
    """
    Ejecuta el modo automático:
    """
    n = len(tablero)
    plan = bfs_plan(tablero)

    if plan is None:
        print("No se ha encontrado ningún plan seguro (sin pisar P ni E).")
        return

    print("Plan encontrado por BFS (modo búsqueda):", plan)

    # Estado inicial
    posicion = (0, 0)
    estado = {"granada": 1, "lleva_cw": False, "vivo": True}

    # Tablero conocido y KB (reutilizamos la lógica del modo interactivo)
    tablero_conocido = crear_tablero_conocido(n)
    tablero_conocido[0][0] = "·"
    KB = crear_KB(n)

    # Percepto inicial + KB
    p0 = percept(posicion, tablero)
    deducir_desde_perceptos(posicion, p0, KB, n)
    actualizar_tablero_conocido_desde_KB(tablero_conocido, KB, tablero)

    print("\nEstado inicial (modo búsqueda):")
    mostrar_tablero(tablero_conocido, posicion)
    print(
        f"Percepción inicial: Brisa={int(p0[0])}, Ronquidos={int(p0[1])}, Resplandor={int(p0[2])}, "
        f"Par↑={int(p0[3])}, Par↓={int(p0[4])}, Par←={int(p0[5])}, Par→={int(p0[6])}, Gri={int(p0[7])}]"
    )

    # Ejecutamos cada acción del plan
    for paso, a in enumerate(plan, start=1):
        x, y = posicion

        if a == "U":
            x -= 1
        elif a == "D":
            x += 1
        elif a == "L":
            y -= 1
        elif a == "R":
            y += 1

        posicion = (x, y)
        celda = tablero[x][y]

        # Actualizamos estado/representación al pisar la celda
        if celda == "CW":
            estado["lleva_cw"] = True
            tablero_conocido[x][y] = "CW"
        elif celda == "S":
            tablero_conocido[x][y] = "S"
        elif celda in ("·", "I"):
            tablero_conocido[x][y] = "·"

        # Perceptos + KB
        p = percept(posicion, tablero)
        deducir_desde_perceptos(posicion, p, KB, n)
        actualizar_tablero_conocido_desde_KB(tablero_conocido, KB, tablero)

        print(f"\nPaso {paso}: acción {a}, nueva posición {posicion}")
        mostrar_tablero(tablero_conocido, posicion)
        print(
            f"Percepción: Brisa={int(p[0])}, Ronquidos={int(p[1])}, Resplandor={int(p[2])}, "
            f"Par↑={int(p[3])}, Par↓={int(p[4])}, Par←={int(p[5])}, Par→={int(p[6])}, Gri={int(p[7])}]"
        )
        if estado["lleva_cw"]:
            print("Estado: ¡CW a bordo!")

    # Comprobamos objetivo al final
    if tablero[posicion[0]][posicion[1]] == "S" and estado["lleva_cw"]:
        print("\n¡Objetivo alcanzado: has llegado a la salida con CW!")
    elif tablero[posicion[0]][posicion[1]] == "S":
        print("\nHas llegado a la salida, pero sin CW (el plan no lo recogió).")
    else:
        print("\nEl plan ha terminado en una celda que no es la salida.")

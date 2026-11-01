from palacio_kurtz import vecinos_ortogonales

def percept(posicion: tuple[int, int],
            tablero: list[list[str]],
            grito: bool = False) -> list[bool]:
    """
    Calcula el percepto del capitán en la celda actual.

    El percepto sigue el formato del enunciado:
        [Brisa?, Ronquido?, Resplandor?, Pared↑?, Pared↓?, Pared←?, Pared→?, Grito?]

    Donde:
        - Brisa: True si hay un precipicio 'P' en una celda ortogonalmente adyacente.
        - Ronquido: True si hay un enemigo 'E' adyacente.
        - Resplandor: True si la salida 'S' está en la celda actual o en una adyacente.
        - Pared: True si en esa dirección hay pared (salirse del tablero).
        - Grito: True si en este turno se eliminó al enemigo con la granada.
    """
    x, y = posicion
    n = len(tablero)
    m = len(tablero[0])

    arriba = (x - 1, y)
    abajo = (x + 1, y)
    izquierda = (x, y - 1)
    derecha = (x, y + 1)

    def dentro(i: int, j: int) -> bool:
        """Devuelve True si (i,j) está dentro de los límites del tablero."""
        return 0 <= i < n and 0 <= j < m

    brisa = (
        (dentro(*arriba) and tablero[arriba[0]][arriba[1]] == "P") or
        (dentro(*abajo) and tablero[abajo[0]][abajo[1]] == "P") or
        (dentro(*izquierda) and tablero[izquierda[0]][izquierda[1]] == "P") or
        (dentro(*derecha) and tablero[derecha[0]][derecha[1]] == "P")
    )

    ronquido = (
        (dentro(*arriba) and tablero[arriba[0]][arriba[1]] == "E") or
        (dentro(*abajo) and tablero[abajo[0]][abajo[1]] == "E") or
        (dentro(*izquierda) and tablero[izquierda[0]][izquierda[1]] == "E") or
        (dentro(*derecha) and tablero[derecha[0]][derecha[1]] == "E")
    )

    # Resplandor si estoy en S o si S está en una celda adyacente
    resplandor = (
        tablero[x][y] == "S" or
        (dentro(*arriba) and tablero[arriba[0]][arriba[1]] == "S") or
        (dentro(*abajo) and tablero[abajo[0]][abajo[1]] == "S") or
        (dentro(*izquierda) and tablero[izquierda[0]][izquierda[1]] == "S") or
        (dentro(*derecha) and tablero[derecha[0]][derecha[1]] == "S")
    )

    pared_up = not dentro(x - 1, y)
    pared_down = not dentro(x + 1, y)
    pared_left = not dentro(x, y - 1)
    pared_right = not dentro(x, y + 1)

    return [brisa, ronquido, resplandor,
            pared_up, pared_down, pared_left, pared_right,
            grito]


def crear_KB(n: int) -> dict[tuple[int, int], dict]:
    """
    Crea una base de conocimiento (KB).

    Para cada celda (i,j) se guarda:
        - seguro: True si el agente considera la celda segura (por ahora: visitada).
        - posible_P: True si podría haber precipicio 
        - posible_E: True si podría haber enemigo 
    """
    KB = {}
    for i in range(n):
        for j in range(n):
            KB[(i, j)] = {
                "seguro": False,
                "posible_P": False,
                "posible_E": False,
            }
    return KB


def deducir_desde_perceptos(posicion: tuple[int, int],
                            p: list[bool],
                            KB: dict,
                            n: int) -> None:
    """
    Actualiza la KB aplicando reglas locales muy simples a partir del percepto actual.
    """
    x, y = posicion
    brisa, ronq, _, _, _, _, _, _ = p

    # La casilla donde está CK es segura
    KB[(x, y)]["seguro"] = True
    KB[(x, y)]["posible_P"] = False
    KB[(x, y)]["posible_E"] = False

    vecinos = vecinos_ortogonales(posicion, n)

    # Sin brisa: ningún vecino tiene precipicio
    if not brisa:
        for v in vecinos:
            KB[v]["posible_P"] = False
            # Nota: se podría marcar "seguro respecto a P", pero mantenemos tu modelo simple.

    # Con brisa: al menos un vecino tiene P → marcamos vecinos como "posibles"
    else:
        for v in vecinos:
            if not KB[v]["seguro"]:
                KB[v]["posible_P"] = True

    # Sin ronquido: ningún vecino tiene enemigo
    if not ronq:
        for v in vecinos:
            KB[v]["posible_E"] = False
    else:
        for v in vecinos:
            if not KB[v]["seguro"]:
                KB[v]["posible_E"] = True


def actualizar_tablero_conocido_desde_KB(tablero_conocido: list[list[str]],
                                         KB: dict,
                                         tablero_real: list[list[str]]) -> None:
    """
    Proyecta el estado de la KB sobre el tablero conocido (lo que ve el jugador).

    Convención:
        - Si la celda es "segura" se pone como '·'
        - Si puede haber precipicio se pone como 'P?'
        - Si puede haber enemigo se pone como 'E?'
    """
    n = len(tablero_conocido)
    for i in range(n):
        for j in range(n):
            celda_vista = tablero_conocido[i][j]
            info = KB[(i, j)]

            # No pisamos símbolos ya vistos
            if celda_vista in ("S", "CW"):
                continue

            if info["seguro"]:
                tablero_conocido[i][j] = "·"
            else:
                # prioridad a avisar de P antes que de E
                if info["posible_P"]:
                    tablero_conocido[i][j] = "P?"
                elif info["posible_E"]:
                    tablero_conocido[i][j] = "E?"
                # si no sabemos nada, dejamos lo que hubiera

from palacio_core import (
    vecinos_ortogonales, riesgo_celda, percept, actualizar_todas_las_creencias,
    lanzar_granada, anular_belief
)

def mejor_direccion_a_vecino(pos: tuple[int,int], v: tuple[int,int]) -> str:
    x, y = pos
    vx, vy = v
    if (vx, vy) == (x-1, y): return "U"
    if (vx, vy) == (x+1, y): return "D"
    if (vx, vy) == (x, y-1): return "L"
    if (vx, vy) == (x, y+1): return "R"
    return "?"

def elegir_accion_busqueda( posicion: tuple[int,int], beliefs: dict[str, list[list[float]]],
    n: int, visitadas: set[tuple[int,int]], umbral: float, estado) -> tuple[str, str]:
    """
    Devuelve ("m", direc) o ("g", direc).
    Política greedy informada:
      score(vecino) = riesgo(vecino) - 2*P(S en vecino) + 0.05*(penalización si ya visitada)
    Además, si hay granada y algún vecino tiene P(M) alta, lanza granada.
    """
    vecinos = vecinos_ortogonales(posicion, n)
    if not vecinos:
        return ("m", None)

    # 1) Granada si merece la pena (M muy probable en una celda adyacente)
    if estado.get("granada", 0) > 0:
        mejor_v = max(vecinos, key=lambda v: beliefs["M"][v[0]][v[1]])
        if beliefs["M"][mejor_v[0]][mejor_v[1]] >= 0.35:  # umbral simple
            return ("g", mejor_direccion_a_vecino(posicion, mejor_v))

    # 2) Movimiento greedy con evaluación
    def score(v):
        r = riesgo_celda(beliefs, v)
        rep = 1.0 if v in visitadas else 0.0

        # 1) Antes de CK: NO usar P(S) como atracción
        if not estado.get("lleva_ck", False):
            ps_term = 0.0
        else:
            ps = beliefs["S"][v[0]][v[1]]
            ps_term = -2.0 * ps   # después de CK, sí atrae fuerte

        # 2) Si ya conoces la salida y aún NO tienes CK, penaliza volver a ella
        penaliza_salida = 0.0
        if (not estado.get("lleva_ck", False)) and (estado.get("salida_pos") is not None):
            if v == estado["salida_pos"]:
                penaliza_salida = 1.0  # grande para que no vuelva

        return r + 0.05*rep + penaliza_salida + ps_term


    # Preferimos vecinos bajo umbral; si ninguno, cogemos el menor score igualmente
    candidatos = [v for v in vecinos if riesgo_celda(beliefs, v) < umbral]
    if not candidatos:
        candidatos = vecinos

    mejor = min(candidatos, key=score)
    return ("m", mejor_direccion_a_vecino(posicion, mejor))
def ejecutar_paso_busqueda( posicion: tuple[int,int], tablero: list[list[set[str]]], estado: dict,
    tablero_conocido: list[list[str]], beliefs: dict[str, list[list[float]]], accion: str, direc: str | None,
    umbral: float = 0.2 ) -> tuple[tuple[int,int], dict, bool]:
    """
    Ejecuta un turno automático. Devuelve (nueva_pos, estado, grito_para_siguiente_turno)
    """
    n = len(tablero)

    # -------- GRANADA --------
    if accion == "g" and direc is not None:
        if estado.get("granada", 0) <= 0:
            return posicion, estado, False

        estado["granada"] -= 1
        grito = lanzar_granada(tablero, posicion, direc)

        if grito:
            anular_belief(beliefs["M"])

        p = percept(posicion, tablero, grito=grito)
        actualizar_todas_las_creencias(beliefs, p, posicion, n)

        return posicion, estado, False  # el grito SOLO vale este turno

    # -------- MOVERSE --------
    if accion == "m" and direc is not None:
        x, y = posicion
        new_x, new_y = x, y
        if direc == "U": new_x -= 1
        elif direc == "D": new_x += 1
        elif direc == "L": new_y -= 1
        elif direc == "R": new_y += 1

        if not (0 <= new_x < n and 0 <= new_y < n):
            return posicion, estado, False

        celda = tablero[new_x][new_y]

        if ("F" in celda) or ("P" in celda) or ("D" in celda) or ("M" in celda):
            estado["vivo"] = False
            tablero_conocido[new_x][new_y] = "X"
            return (new_x, new_y), estado, False

        if "CK" in celda:
            estado["lleva_ck"] = True

        if "S" in celda:
            tablero_conocido[new_x][new_y] = "S"
            if estado.get("salida_pos") is None:
                estado["salida_pos"] = (new_x, new_y)
        else:
            tablero_conocido[new_x][new_y] = "·"


        posicion = (new_x, new_y)

        p = percept(posicion, tablero, grito=False)
        actualizar_todas_las_creencias(beliefs, p, posicion, n)

        return posicion, estado, False

    return posicion, estado, False
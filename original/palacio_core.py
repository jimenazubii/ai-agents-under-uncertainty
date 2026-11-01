import random
import matplotlib.pyplot as plt


def crear_tablero(n: int) -> list[list[set]]:
    """
    Crea un tablero n x n relleno de sets.
    Utilizamos sets para que una celda pueda contener varios elementos simultáneamente y evita duplicados.
    """
    return [[set() for _ in range(n)] for _ in range(n)]
  
def coord_aleatorias(n: int) -> tuple[int, int]:
    """Devuelve una coordenada uniforme (x,y) dentro del tablero."""
    x_coord = random.randint(0, n - 1)
    y_coord = random.randint(0, n - 1)
    return x_coord, y_coord



def colocar_elementos(tablero: list[list[set[str]]]) -> None:
    """
    Coloca elementos en el tablero según restricciones del enunciado.
    Restricciones clave:
    - (0,0) es la casilla inicial .
    - Trampas F,P,D:
        - pueden coincidir entre sí y repetirse en la misma celda.
    - Elementos M, S, CK:
        - NO pueden estar en celdas con trampas pero pueden coincidir entre ellos.
    """

    n = len(tablero)

    # Marca explícitamente el inicio con "I" 
    tablero[0][0].add("I")

    # Celdas prohibidas: por ahora solo el inicio.
    prohibidas = {(0, 0)}

    # Trampas (se permiten en la misma celda entre ellas).
    trampas = ["F", "P", "D"]

    # Elementos “no-trampa”: enemigo M, salida S, Kurtz CK.
    elems = ["M", "S", "CK"]

    # Guardamos dónde hay trampas para impedir M/S/CK ahí.
    celdas_con_trampas = set()

    for trampa in trampas:
        x, y = coord_aleatorias(n)
        while (x, y) in prohibidas:
            x, y = coord_aleatorias(n)
        tablero[x][y].add(trampa)
        celdas_con_trampas.add((x, y))

    # Prohibidas para M/S/CK: inicio + cualquier celda con trampa.
    prohibidas_msk = celdas_con_trampas | prohibidas

    for elem in elems:
        x, y = coord_aleatorias(n)
        while (x, y) in prohibidas_msk:
            x, y = coord_aleatorias(n)
        tablero[x][y].add(elem)

def es_objetivo(posicion: tuple[int, int], tablero: list[list[set[str]]]) -> bool:
    """Devuelve True si la celda actual contiene 'S' (salida)."""
    x, y = posicion
    return "S" in tablero[x][y]

def percept(posicion: tuple[int, int], tablero: list[list[set[str]]], grito: bool = False) -> list[bool]:
    """
    Percepto con el formato del enunciado:
    [eF, eP, eD, eM, eS, pared_up, pared_down, pared_left, pared_right, grito]

    Interpretación:
    - eX es True si X aparece en la celda actual o en alguna adyacente (distancia Manhattan = 1)
    - paredes indican si en esa dirección te sales del tablero.
    - grito True solo justo después de lanzar granada y matar a M.
    """

    x, y = posicion
    n = len(tablero)
    m = len(tablero[0])

    def dentro(i: int, j: int) -> bool:
        return 0 <= i < n and 0 <= j < m

    # Celdas relevantes: la actual + adyacentes válidas
    candidatos = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    vecinos = [(i, j) for (i, j) in candidatos if dentro(i, j)]

    # Estímulos: True si el símbolo aparece en alguna celda de vecinos
    eF = any("F" in tablero[i][j] for (i, j) in vecinos)
    eP = any("P" in tablero[i][j] for (i, j) in vecinos)
    eD = any("D" in tablero[i][j] for (i, j) in vecinos)
    eM = any("M" in tablero[i][j] for (i, j) in vecinos)
    eS = any("S" in tablero[i][j] for (i, j) in vecinos)

    pared_up = not dentro(x - 1, y)
    pared_down = not dentro(x + 1, y)
    pared_left = not dentro(x, y - 1)
    pared_right = not dentro(x, y + 1)

    return [eF, eP, eD, eM, eS,
            pared_up, pared_down, pared_left, pared_right,
            grito]

def crear_tablero_conocido(n: int) -> list[list[str]]:
    """Tablero de conocimiento: '?' desconocido, '·' visitado, 'S' salida, 'X' muerte, etc."""
    return [["?" for _ in range(n)] for _ in range(n)]

def mostrar_tablero(tablero_conocido: list[list[str]], posicion: tuple[int, int]) -> None:
    """
    Imprime el tablero conocido y superpone la posición del agente como 'CW'.
    Así evitamos confundir al agente con CK (Kurtz).
    """
    x, y = posicion
    for i, fila in enumerate(tablero_conocido):
        fila_a_mostrar = []
        for j, celda in enumerate(fila):
            if (i, j) == (x, y):
                fila_a_mostrar.append("CW")
            else:
                fila_a_mostrar.append(celda)
        print(" ".join(fila_a_mostrar))


def crear_beliefs(n: int, inicio: tuple[int,int]=(0,0)) -> dict[str, list[list[float]]]:
    """
    Inicializa creencias como distribuciones uniformes:
      p0 = 1/(N-1) para todas las casillas excepto la inicial, que es 0.

    Se crea una matriz para cada elemento:
      F, P, D, M, S, CK
    """
    N = n*n 
    p0 = 1/(N-1)
    beliefs = {}
    elementos = ["F","P","D","M","S","CK"]
    for elemento in elementos: 
        matriz = [[p0 for _ in range(n)] for _ in range(n)]  
        matriz[inicio[0]][inicio[1]] = 0 
        beliefs[elemento] = matriz 
    return beliefs

def vecinos_ortogonales(pos: tuple[int, int], n: int) -> list[tuple[int, int]]:
    """Devuelve vecinos válidos (arriba, abajo, izquierda, derecha)."""
    x, y = pos
    vecinos = []
    if x > 0:
        vecinos.append((x - 1, y))
    if x < n - 1:
        vecinos.append((x + 1, y))
    if y > 0:
        vecinos.append((x, y - 1))
    if y < n - 1:
        vecinos.append((x, y + 1))
    return vecinos

def zona_perceptible(pos: tuple[int, int], n: int) -> set[tuple[int, int]]:
    """Zona donde puede estar una amenaza/objetivo si el estímulo es True."""
    vecinos = vecinos_ortogonales(pos, n)
    return {pos} | set(vecinos)


def renormalizar(matriz: list[list[float]]) -> None:
    """Renormaliza una matriz de probabilidades para que sume 1 (in-place)."""
    Z = 0.0
    for fila in matriz:
        Z += sum(fila)

    if Z == 0.0:
        raise ValueError("Renormalización imposible: la suma total es 0 (evidencia inconsistente o bug).")

    for i in range(len(matriz)):
        for j in range(len(matriz[0])):
            matriz[i][j] /= Z

def actualizar_belief_por_estimulo(belief_tau, pos, e_tau, n):
    """
    Likelihood simplificado:
      - Si hay estímulo: el objeto debe estar en zona_perceptible
      - Si no hay estímulo: el objeto no puede estar en zona_perceptible
    Implementación:
      - Pone a 0 las celdas imposibles
      - Renormaliza para que vuelva a sumar 1
    """

    zona = zona_perceptible(pos, n)  # debe devolver set[tuple[int,int]]

    for i in range(n):
        for j in range(n):
            dentro_zona = (i, j) in zona

            if e_tau:
                # Estímulo presente => fuera de zona es imposible
                if not dentro_zona:
                    belief_tau[i][j] = 0.0
            else:
                # Estímulo ausente => dentro de zona es imposible
                if dentro_zona:
                    belief_tau[i][j] = 0.0

    renormalizar(belief_tau)

def actualizar_todas_las_creencias(beliefs, percepto, pos, n):
    """
    Aplica actualizar_belief_por_estimulo a F,P,D,M,S.

    Nota:
    - CK no se actualiza porque no hay estímulo de CK.
      (Solo se detecta al entrar en su celda real del tablero.)
    """

    eF, eP, eD, eM, eS = percepto[0], percepto[1], percepto[2], percepto[3], percepto[4]

    actualizar_belief_por_estimulo(beliefs["F"], pos, eF, n)
    actualizar_belief_por_estimulo(beliefs["P"], pos, eP, n)
    actualizar_belief_por_estimulo(beliefs["D"], pos, eD, n)
    # Solo actualizamos M si aún existe (belief no anulada)
    if sum(sum(fila) for fila in beliefs["M"]) > 0.0:
        actualizar_belief_por_estimulo(beliefs["M"], pos, eM, n)
    actualizar_belief_por_estimulo(beliefs["S"], pos, eS, n)

    # CK (Kurtz) no tiene un estímulo directo en el percepto, así que NO se actualiza aquí.
    # Se puede actualizar aparte cuando se encuentre (si decides colapsar su belief al hallarlo).

def mostrar_heatmaps(matriz, titulo, posicion, vmax:float):
    """
    Dibuja un heatmap de una matriz.
    vmin=0, vmax parametrizable para comparar escalas.
    Marca posición actual con una X.
    """
    plt.figure(figsize=(4,4))
    plt.imshow(matriz, vmin=0.0, vmax=vmax)
    plt.title(titulo)
    plt.colorbar()

    if posicion is not None:
        x, y = posicion
        plt.scatter([y], [x], marker="x")  # (col=y, fila=x)

    plt.tight_layout()
    plt.show()


def riesgo_celda(beliefs, celda):
    """
    Define riesgo como suma de probabilidades de morir:
      F+P+D+M
    """
    i, j = celda
    return beliefs["F"][i][j] + beliefs["P"][i][j] + beliefs["D"][i][j] + beliefs["M"][i][j]

def recomendar_movimientos_bayes(posicion, beliefs, n, umbral=0.2):
    """
    Clasifica vecinos en:
      - recomendados: riesgo < umbral
      - arriesgados: riesgo >= umbral

    Además traduce cada vecino a dirección U/D/L/R.
    """
    x, y = posicion
    vecinos = vecinos_ortogonales(posicion, n)

    recomendados = []
    arriesgados = []

    for v in vecinos:
        r = riesgo_celda(beliefs, v)
        if r < umbral:
            recomendados.append((v, r))
        else:
            arriesgados.append((v, r))

    def dir_de(a: int, b: int) -> str:
        if a == x - 1 and b == y: return "U"
        if a == x + 1 and b == y: return "D"
        if a == x and b == y - 1: return "L"
        if a == x and b == y + 1: return "R"
        return "?"

    recomendados.sort(key=lambda t: t[1])
    arriesgados.sort(key=lambda t: t[1])

    if recomendados:
        print(f"Movimientos recomendados (riesgo < {umbral}):")
        print([(pos, dir_de(*pos), round(r, 3)) for (pos, r) in recomendados])
    if arriesgados:
        print(f"Movimientos arriesgados (riesgo >= {umbral}):")
        print([(pos, dir_de(*pos), round(r, 3)) for (pos, r) in arriesgados])

def lanzar_granada(tablero, origen, direc):
    """
    Lanza granada a una celda adyacente.
    - Si fuera del tablero: no hace nada (False).
    - Si hay M: lo elimina del set de la celda y devuelve True (grito).
    """

    x, y = origen
    gx, gy = x, y
    if direc == "U": gx -= 1
    elif direc == "D": gx += 1
    elif direc == "L": gy -= 1
    elif direc == "R": gy += 1

    n = len(tablero)
    if not (0 <= gx < n and 0 <= gy < n):
        return False

    if "M" in tablero[gx][gy]:
        tablero[gx][gy].discard("M")
        return True

    return False

def anular_belief(matriz):
    """Pone la matriz a 0 si el enemigo ya no existe."""
    for i in range(len(matriz)):
        for j in range(len(matriz[0])):
            matriz[i][j] = 0.0
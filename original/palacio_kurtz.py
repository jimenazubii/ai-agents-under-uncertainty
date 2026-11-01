import random
def crear_tablero(n: int) -> list[list[str]]:
    """
    Crea un tablero cuadrado n x n con todas las celdas vacías.
    """
    return [["·" for _ in range(n)] for _ in range(n)]


def coord_aleatorias(n: int) -> tuple[int, int]:
    """
    Genera una coordenada aleatoria válida dentro de un tablero n x n.
    """
    x_coord = random.randint(0, n - 1)
    y_coord = random.randint(0, n - 1)
    return x_coord, y_coord


def colocar_elementos(tablero: list[list[str]]) -> None:
    """
    Coloca los elementos del entorno en posiciones distintas.

    Elementos colocados:
        - 'I' en (0,0): inicio.
        - 3 precipicios: 'P'
        - 1 enemigo: 'E'
        - 1 Coronel Kurtz: 'CW'
        - 1 salida: 'S'

    Restricciones:
        - Todos los elementos se colocan en celdas distintas 
    """
    n = len(tablero)
    tablero[0][0] = "I"
    ocupadas = {(0, 0)}

    # Colocamos exactamente 6 elementos adicionales:
    # 3P, 1E, 1CW, 1S
    for i in range(6):
        x, y = coord_aleatorias(n)
        while (x, y) in ocupadas:
            x, y = coord_aleatorias(n)
        ocupadas.add((x, y))

        if i < 3:
            tablero[x][y] = "P"
        elif i == 3:
            tablero[x][y] = "E"
        elif i == 4:
            tablero[x][y] = "CW"
        else:
            tablero[x][y] = "S"


def es_objetivo(posicion: tuple[int, int], tablero: list[list[str]]) -> bool:
    """
    Comprueba si una posición es la casilla de salida.
    """
    x, y = posicion
    return tablero[x][y] == "S"


def vecinos_ortogonales(pos: tuple[int, int], n: int) -> list[tuple[int, int]]:
    """
    Devuelve las celdas adyacentes ortogonales dentro del tablero.
    """
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

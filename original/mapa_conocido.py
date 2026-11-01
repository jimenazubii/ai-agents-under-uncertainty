def crear_tablero_conocido(n: int) -> list[list[str]]:
    """
    Crea el tablero conocido inicial del capitán:
        - '?' indica una celda no explorada ni deducida.
        - A medida que el juego avanza, las celdas se actualizan con información del KB.
    """
    return [["?" for _ in range(n)] for _ in range(n)]


def mostrar_tablero(tablero_conocido: list[list[str]],
                    posicion: tuple[int, int]) -> None:
    """
    Muestra por consola el tablero conocido por el capitán
    """
    x, y = posicion

    for i, fila in enumerate(tablero_conocido):
        fila_a_mostrar = []
        for j, celda in enumerate(fila):
            if (i, j) == (x, y):
                fila_a_mostrar.append("CK")
            else:
                fila_a_mostrar.append(celda)
        print(" ".join(fila_a_mostrar))

if __name__ == "__main__": 
    a = crear_tablero_conocido(6)
    mostrar_tablero(a)
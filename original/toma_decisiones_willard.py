from palacio_kurtz import vecinos_ortogonales, es_objetivo
from perceptos_willard import percept, deducir_desde_perceptos, actualizar_tablero_conocido_desde_KB
from mapa_conocido import mostrar_tablero


def recomendar_movimientos(posicion: tuple[int, int],
                           KB: dict,
                           n: int) -> None:
    """
    Imprime recomendaciones de movimiento a partir del KB.

    Clasifica los vecinos ortogonales de la posición actual en:
        - seguras: KB indica "seguro"
        - riesgosas: KB marca "posible_P" o "posible_E"
        - desconocidas: KB no indica ni seguro ni posible peligro

    Además, imprime cada vecino junto con la dirección (U/D/L/R) necesaria
    para moverse a esa celda.
    """
    x, y = posicion
    vecinos = vecinos_ortogonales(posicion, n)

    seguras = []
    riesgosas = []
    desconocidas = []

    for vx, vy in vecinos:
        info = KB[(vx, vy)]
        if info["seguro"]:
            seguras.append((vx, vy))
        elif info["posible_P"] or info["posible_E"]:
            riesgosas.append((vx, vy))
        else:
            desconocidas.append((vx, vy))

    def dir_de(a: int, b: int) -> str:
        """
        Devuelve la dirección (U/D/L/R) para ir desde (x,y) a (a,b),
        asumiendo que (a,b) es vecino ortogonal.
        """
        if a == x - 1 and b == y:
            return "U"
        if a == x + 1 and b == y:
            return "D"
        if a == x and b == y - 1:
            return "L"
        if a == x and b == y + 1:
            return "R"
        return "?"

    if seguras:
        print("Movimientos recomendados (seguros):",
              [(pos, dir_de(*pos)) for pos in seguras])
    if riesgosas:
        print("Movimientos con posible peligro:",
              [(pos, dir_de(*pos)) for pos in riesgosas])
    if desconocidas:
        print("Movimientos sin información:",
              [(pos, dir_de(*pos)) for pos in desconocidas])


def acciones_posibles(posicion: tuple[int, int],
                      tablero: list[list[str]],
                      estado: dict,
                      tablero_conocido: list[list[str]],
                      KB: dict) -> tuple[tuple[int, int], dict]:
    """
    Bucle interactivo de un turno: pide al usuario una acción válida y la ejecuta.

    Acciones disponibles:
        - 'm': moverse (U/D/L/R) una celda ortogonal
        - 'g': tirar granada a una celda contigua (U/D/L/R)
        - 's': salir (solo tiene efecto si está en la salida)

    Efectos importantes:
        - Si CK entra en 'P' o 'E' con enemigo vivo: muere y estado["vivo"]=False
        - Si CK pisa 'CW': lo rescata (estado["lleva_cw"]=True)
        - Si CK llega a 'S': puede intentar salir
    """
    n = len(tablero)

    while True:
        x, y = posicion
        print()
        recomendar_movimientos(posicion, KB, n)

        accion = input(
            "\nIntroduce la acción que deseas realizar:\n"
            "1. Moverse (m)\n"
            "2. Arrojar granada (g)\n"
            "3. Salir (s)\n> "
        ).lower()

        # ------------------ MOVERSE ------------------
        if accion == "m":
            direc = input(
                "Introduce la dirección (Up (U), Down (D), Left (L), Right (R)): "
            ).upper()
            while direc not in ["U", "D", "L", "R"]:
                print("Dirección inválida. Intenta de nuevo.")
                direc = input(
                    "Introduce la dirección (Up (U), Down (D), Left (L), Right (R)): "
                ).upper()

            new_x, new_y = x, y
            if direc == "U":
                new_x -= 1
            elif direc == "D":
                new_x += 1
            elif direc == "L":
                new_y -= 1
            elif direc == "R":
                new_y += 1

            # Fuera del tablero: no se mueve
            if not (0 <= new_x < n and 0 <= new_y < n):
                print("No puedes salirte del tablero.")
                continue

            celda = tablero[new_x][new_y]

            # Precipicio -> muerte
            if celda == "P":
                print("¡Has caído por un precipicio! CK ha muerto.")
                estado["vivo"] = False
                tablero_conocido[new_x][new_y] = "P"
                posicion = (new_x, new_y)
                mostrar_tablero(tablero_conocido, posicion)
                return posicion, estado

            # Enemigo -> muerte si lo pisa
            if celda == "E":
                print("Has pisado al enemigo… ¡CK ha muerto!")
                estado["vivo"] = False
                tablero_conocido[new_x][new_y] = "E"
                posicion = (new_x, new_y)
                mostrar_tablero(tablero_conocido, posicion)
                return posicion, estado

            # CW -> lo rescata
            if celda == "CW":
                estado["lleva_cw"] = True
                print("Has encontrado al Capitán CW. Ahora te acompaña.")
                tablero_conocido[new_x][new_y] = "CW"

            # Salida
            elif celda == "S":
                print("Has llegado a la sala de la salida.")
                tablero_conocido[new_x][new_y] = "S"

            # Casilla normal (o inicio I)
            elif celda in ("·", "I"):
                tablero_conocido[new_x][new_y] = "·"

            # Actualizamos posición
            posicion = (new_x, new_y)
            print(f"\nTe has movido a la posición {posicion}")

            # Perceptos y deducción
            p = percept(posicion, tablero)
            deducir_desde_perceptos(posicion, p, KB, n)
            actualizar_tablero_conocido_desde_KB(tablero_conocido, KB, tablero)

            mostrar_tablero(tablero_conocido, posicion)
            print(
                f"Percepción: Brisa={int(p[0])}, Ronquidos={int(p[1])}, Resplandor={int(p[2])}, "
                f"Par↑={int(p[3])}, Par↓={int(p[4])}, Par←={int(p[5])}, Par→={int(p[6])}, Gri={int(p[7])}]"
            )
            if estado.get("lleva_cw"):
                print("Estado: ¡CW a bordo!")

            return posicion, estado

        # ------------------ GRANADA ------------------
        elif accion == "g":
            if estado["granada"] <= 0:
                print("No te quedan granadas.")
                continue

            direc = input("¿Hacia qué dirección lanzas la granada? (U/D/L/R): ").upper()
            while direc not in ["U", "D", "L", "R"]:
                print("Dirección inválida.")
                direc = input("¿Hacia qué dirección lanzas la granada? (U/D/L/R): ").upper()

            gx, gy = x, y
            if direc == "U":
                gx -= 1
            elif direc == "D":
                gx += 1
            elif direc == "L":
                gy -= 1
            elif direc == "R":
                gy += 1

            # Si choca contra pared, no la gasta
            if not (0 <= gx < n and 0 <= gy < n):
                print("La granada choca contra la pared y no hace nada.")
                continue

            # Consume la granada al llegar a una celda válida
            estado["granada"] -= 1

            # Si hay enemigo, se elimina y se oye grito
            if tablero[gx][gy] == "E":
                tablero[gx][gy] = "·"
                print("AAAAAAHHHH!!! Enemigo eliminado. La celda ahora es transitable.")
                p = percept(posicion, tablero, grito=True)
            else:
                print("La granada explota, pero no había enemigo allí.")
                p = percept(posicion, tablero, grito=False)

            deducir_desde_perceptos(posicion, p, KB, n)
            actualizar_tablero_conocido_desde_KB(tablero_conocido, KB, tablero)

            mostrar_tablero(tablero_conocido, posicion)
            print(
                f"Percepción: Brisa={int(p[0])}, Ronquidos={int(p[1])}, Resplandor={int(p[2])}, "
                f"Par↑={int(p[3])}, Par↓={int(p[4])}, Par←={int(p[5])}, Par→={int(p[6])}, Gri={int(p[7])}]"
            )

            continue  # sigue pidiendo acción en el mismo turno

        # ------------------ SALIR ------------------
        elif accion == "s":
            if es_objetivo(posicion, tablero):
                # En la salida: permitimos finalizar
                if estado.get("lleva_cw"):
                    print("¡Has escapado del palacio con el Capitán CW! Misión cumplida.")
                else:
                    print("Has llegado a la salida, pero no has rescatado a CW...")
                estado["vivo"] = False
                return posicion, estado
            else:
                print("No estás en la salida: el comando 'Salir' no tiene efecto.")
                continue

        # ------------------ OPCIÓN INVÁLIDA ------------------
        else:
            print("Opción no válida. Intenta de nuevo.")

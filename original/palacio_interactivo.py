from palacio_core import (
    recomendar_movimientos_bayes,   # imprime vecinos recomendados vs arriesgados según beliefs y umbral
    percept,                        # calcula percepto [eF,eP,eD,eM,eS, paredes..., grito]
    actualizar_todas_las_creencias, # aplica update Bayes (likelihood 0/1 + renormalización) a F,P,D,M,S
    mostrar_tablero,                # muestra el tablero conocido con la posición actual del agente
    mostrar_heatmaps,               # dibuja heatmaps de probabilidad (trampas agregadas, M, S)
    lanzar_granada,                 # intenta eliminar al enemigo M en celda adyacente
    anular_belief,                  # pone a 0 toda la matriz de belief (para “M ya no existe”)
    es_objetivo                     # True si la celda actual contiene la salida S
)

def acciones_posibles_bayes(
    posicion: tuple[int, int],
    tablero: list[list[set[str]]],
    estado: dict,
    tablero_conocido: list[list[str]],
    beliefs: dict[str, list[list[float]]],
    umbral: float = 0.2,
    grito_prev: bool = False
) -> tuple[tuple[int, int], dict, bool]:
    """
    Ejecuta *una interacción* (un turno) del modo Bayes interactivo.

    Parámetros:
    - posicion: (x,y) actual de CW.
    - tablero: tablero real (ground truth) con sets por celda.
    - estado: dict con 'vivo', 'granada', 'lleva_ck', etc.
    - tablero_conocido: visión parcial del jugador ('?', '·', 'S', 'X'...)
    - beliefs: dict de matrices de prob. para F,P,D,M,S,(CK opcional)
    - umbral: riesgo máximo para considerar una casilla “recomendada”
    - grito_prev: se deja por compatibilidad, pero NO se usa (el grito solo afecta al turno de granada)

    Devuelve:
    - nueva posicion
    - nuevo estado
    - salio: bool -> True si el jugador salió (acción 's' exitosa en la salida), False en otro caso
    """
    # n es el tamaño del tablero (NxN)
    n = len(tablero)

    # Bucle hasta que el usuario realice una acción válida.
    # Importante: tras ejecutar una acción válida (mover/granada/salir),
    # hacemos return y el “turno” termina (granada consume turno).
    while True:
        x, y = posicion
        print()

        # Antes de pedir acción, damos recomendaciones bayesianas:
        # - calcula el riesgo agregado por celda (F+P+D+M)
        # - separa vecinos en recomendados/arriesgados según umbral
        recomendar_movimientos_bayes(posicion, beliefs, n, umbral=umbral)

        # Pedimos la acción del turno
        accion = input(
            "\nIntroduce la acción que deseas realizar:\n"
            "1. Moverse (m)\n"
            "2. Arrojar granada (g)\n"
            "3. Salir (s)\n> "
        ).lower()

        # ------------------------------------------------------
        # 1) MOVERSE
        # ------------------------------------------------------
        if accion == "m":
            # Pedimos dirección y validamos input.
            direc = input("Dirección (U/D/L/R): ").upper()
            while direc not in ["U", "D", "L", "R"]:
                print("Dirección inválida.")
                direc = input("Dirección (U/D/L/R): ").upper()

            # Calculamos nueva posición candidata.
            new_x, new_y = x, y
            if direc == "U":
                new_x -= 1
            elif direc == "D":
                new_x += 1
            elif direc == "L":
                new_y -= 1
            elif direc == "R":
                new_y += 1

            # Si te sales del tablero, el movimiento es inválido y se repite el turno.
            if not (0 <= new_x < n and 0 <= new_y < n):
                print("No puedes salirte del tablero.")
                continue

            # Celda real (ground truth). Es un set[str] con los elementos que haya.
            celda = tablero[new_x][new_y]

            # ------------------ Condiciones de MUERTE ------------------
            # Si entras en trampa: muere CW.
            if ("F" in celda) or ("P" in celda) or ("D" in celda):
                print("¡Has caído en una trampa! CW ha muerto.")
                estado["vivo"] = False
                posicion = (new_x, new_y)

                # Marcamos en el tablero conocido que esa celda es mortal/fin.
                tablero_conocido[new_x][new_y] = "X"
                mostrar_tablero(tablero_conocido, posicion)

                # salio=False porque esto no es “salir”, es muerte.
                return posicion, estado, False

            # Si pisas enemigo: muere CW.
            if "M" in celda:
                print("Has pisado al enemigo… ¡CW ha muerto!")
                estado["vivo"] = False
                posicion = (new_x, new_y)
                tablero_conocido[new_x][new_y] = "X"
                mostrar_tablero(tablero_conocido, posicion)
                return posicion, estado, False

            # ------------------ Eventos (CK / Salida) ------------------
            # Si encuentras a CK, lo “recoges”.
            if "CK" in celda:
                estado["lleva_ck"] = True
                print("Has encontrado al Coronel Kurtz (CK).")

            # Si llegas a salida, la marcamos como S en el tablero conocido.
            if "S" in celda:
                print("Has llegado a la salida.")
                tablero_conocido[new_x][new_y] = "S"
            else:
                # Si no es salida: simplemente queda como visitada/explorada.
                tablero_conocido[new_x][new_y] = "·"

            # Actualizamos posición real del agente.
            posicion = (new_x, new_y)
            print(f"\nTe has movido a la posición {posicion}")

            # ------------------ Percepto + Bayes ------------------
            # MEJORA: el grito NO se arrastra al movimiento.
            # El grito solo existe en el turno de la granada, y ya lo incorporamos allí.
            p = percept(posicion, tablero, grito=False)

            # Actualiza beliefs para F,P,D,M,S (CK no se actualiza porque no hay estímulo).
            actualizar_todas_las_creencias(beliefs, p, posicion, n)

            # Mostramos tablero conocido tras el movimiento
            mostrar_tablero(tablero_conocido, posicion)

            # Heatmaps: construimos mapa agregado de trampas + M + S
            N = len(beliefs["F"])
            mapa_trampas = [
                [beliefs["F"][i][j] + beliefs["P"][i][j] + beliefs["D"][i][j] for j in range(N)]
                for i in range(N)
            ]

            mostrar_heatmaps(mapa_trampas, "P(trampa)=F+P+D", posicion, vmax=0.2)
            mostrar_heatmaps(beliefs["M"], "P(M)", posicion, vmax=1.0)
            mostrar_heatmaps(beliefs["S"], "P(S)", posicion, vmax=1.0)

            # Debug/visual: imprimimos percepto desglosado
            print(
                f"Percepción: eF={int(p[0])}, eP={int(p[1])}, eD={int(p[2])}, eM={int(p[3])}, eS={int(p[4])}, "
                f"Par↑={int(p[5])}, Par↓={int(p[6])}, Par←={int(p[7])}, Par→={int(p[8])}, Grito={int(p[9])}"
            )

            # Acción válida: termina el turno
            return posicion, estado, False

        # ------------------------------------------------------
        # 2) GRANADA
        # ------------------------------------------------------
        elif accion == "g":
            # Si no quedan granadas, elijo otra acción.
            if estado.get("granada", 0) <= 0:
                print("No te quedan granadas.")
                continue

            # Dirección de lanzamiento con validación.
            direc = input("¿Dirección de la granada? (U/D/L/R): ").upper()
            while direc not in ["U", "D", "L", "R"]:
                print("Dirección inválida.")
                direc = input("¿Dirección de la granada? (U/D/L/R): ").upper()

            # ------------------ Comprobación “si es pared no se gasta” ------------------
            gx, gy = x, y
            if direc == "U":
                gx -= 1
            elif direc == "D":
                gx += 1
            elif direc == "L":
                gy -= 1
            elif direc == "R":
                gy += 1

            # Si el objetivo está fuera, choca con pared y no consume granada.
            if not (0 <= gx < n and 0 <= gy < n):
                print("La granada choca contra la pared y no hace nada.")
                continue

            # Ahora sí: consume granada (porque el lanzamiento es válido)
            estado["granada"] -= 1

            # Lanzamos granada en el entorno real.
            # Devuelve True si había M en esa celda y lo elimina => “grito”.
            grito = lanzar_granada(tablero, posicion, direc)

            # Si grito: enemigo eliminado + belief de M anulada.
            if grito:
                print("AAAAAAHHHH!!! Enemigo eliminado (grito).")
                anular_belief(beliefs["M"])
            else:
                print("La granada explota, pero no había enemigo allí.")

            # ------------------ Percepto + Bayes tras granada ------------------
            # Importante: la granada no mueve al agente; el percepto se toma en la misma posición,
            # pero con el indicador grito (True/False) incorporado.
            p = percept(posicion, tablero, grito=grito)
            actualizar_todas_las_creencias(beliefs, p, posicion, n)

            mostrar_tablero(tablero_conocido, posicion)

            N = len(beliefs["F"])
            mapa_trampas = [
                [beliefs["F"][i][j] + beliefs["P"][i][j] + beliefs["D"][i][j] for j in range(N)]
                for i in range(N)
            ]
            mostrar_heatmaps(mapa_trampas, "P(trampa)=F+P+D", posicion, vmax=0.2)
            mostrar_heatmaps(beliefs["M"], "P(M)", posicion, vmax=1.0)
            mostrar_heatmaps(beliefs["S"], "P(S)", posicion, vmax=1.0)

            print(
                f"Percepción: eF={int(p[0])}, eP={int(p[1])}, eD={int(p[2])}, eM={int(p[3])}, eS={int(p[4])}, "
                f"Par↑={int(p[5])}, Par↓={int(p[6])}, Par←={int(p[7])}, Par→={int(p[8])}, Grito={int(p[9])}"
            )

            # MEJORA: la granada consume turno -> terminamos el turno aquí.
            return posicion, estado, False

        # ------------------------------------------------------
        # 3) SALIR
        # ------------------------------------------------------
        elif accion == "s":
            # Solo tiene efecto si realmente estás en la salida.
            if es_objetivo(posicion, tablero):
                if estado.get("lleva_ck"):
                    print("¡Has escapado del palacio con CK! Misión cumplida.")
                else:
                    print("Has llegado a la salida, pero no has encontrado a CK...")

                # Terminamos juego: marcamos no vivo para cortar bucle externo.
                estado["vivo"] = False

                # salio=True porque el usuario ha elegido salir estando en la salida.
                return posicion, estado, True

            else:
                print("No estás en la salida: 'Salir' no tiene efecto.")
                continue

        # ------------------------------------------------------
        # 4) Opción inválida
        # ------------------------------------------------------
        else:
            print("Opción no válida.")

from palacio_kurtz import crear_tablero, colocar_elementos, es_objetivo
from perceptos_willard import (
    percept,
    crear_KB,
    deducir_desde_perceptos,
    actualizar_tablero_conocido_desde_KB,
)
from mapa_conocido import crear_tablero_conocido, mostrar_tablero
from agente_busqueda import ejecutar_plan_automatico
from toma_decisiones_willard import acciones_posibles


if __name__ == "__main__":
    # -------------------------------------------------------------
    #  Inicialización del entorno real (palacio)
    # -------------------------------------------------------------
    n = 6
    tablero = crear_tablero(n)
    colocar_elementos(tablero)

    # -------------------------------------------------------------
    #  Selección de modo de juego
    # -------------------------------------------------------------
    modo = input(
        "Elige modo de juego:\n"
        "1. Modo interactivo (guiado por el usuario)\n"
        "2. Modo búsqueda (agente automático)\n> "
    ).strip()

    # -------------------------------------------------------------
    #  MODO 1: Interactivo ( guía al Capitán Willard)
    # -------------------------------------------------------------
    if modo == "1":
        # Estado del capitán
        posicion = (0, 0)
        estado = {"granada": 1, "lleva_cw": False, "vivo": True}

        # Mapa conocido y KB
        tablero_conocido = crear_tablero_conocido(n)
        tablero_conocido[0][0] = "·"  # la celda inicial se considera conocida
        KB = crear_KB(n)

        # Percepto inicial y deducción inicial
        p0 = percept(posicion, tablero)
        deducir_desde_perceptos(posicion, p0, KB, n)
        actualizar_tablero_conocido_desde_KB(tablero_conocido, KB, tablero)

        # Mostrar estado inicial
        mostrar_tablero(tablero_conocido, posicion)
        print(
            f"Percepción inicial: Brisa={int(p0[0])}, Ronquidos={int(p0[1])}, Resplandor={int(p0[2])}, "
            f"Par↑={int(p0[3])}, Par↓={int(p0[4])}, Par←={int(p0[5])}, Par→={int(p0[6])}, Gri={int(p0[7])}]"
        )

        # Bucle principal del modo interactivo:
        # - en cada iteración, el usuario elige una acción
        # - la acción actualiza posición/estado/KB/tablero conocido
        while estado["vivo"]:
            posicion, estado = acciones_posibles(
                posicion, tablero, estado, tablero_conocido, KB
            )

            # Si ha muerto, se termina
            if not estado["vivo"]:
                break

            # Comprobación de objetivo (salida + CW rescatado)
            if es_objetivo(posicion, tablero) and estado.get("lleva_cw"):
                print("¡Objetivo alcanzado: salida + CW rescatado!")
                break

            # Si está en salida sin CW, se informa (el usuario puede seguir)
            elif es_objetivo(posicion, tablero) and not estado.get("lleva_cw"):
                print("Estás en la salida, pero aún no has rescatado a CW.")

    # -------------------------------------------------------------
    #  MODO 2: Búsqueda automática (BFS)
    # -------------------------------------------------------------
    else:
        ejecutar_plan_automatico(tablero)

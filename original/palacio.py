
from palacio_core import (
    crear_tablero,               # Crea una matriz NxN de sets (cada celda puede tener varios elementos)
    colocar_elementos,           # Coloca F/P/D (trampas), M (enemigo), S (salida), CK (Kurtz)
    crear_tablero_conocido,      # Tablero "visible" por el jugador (lo que sabe hasta el momento)
    crear_beliefs,               # Inicializa distribuciones P(F),P(P),P(D),P(M),P(S)
    percept,                     # Calcula el percepto actual (estímulos + paredes + grito)
    actualizar_todas_las_creencias,  # Actualiza beliefs con Bayes según el percepto
    mostrar_tablero,             # Imprime tablero conocido en consola (sin enseñar trampas reales)
    mostrar_heatmaps,            # Dibuja mapas de calor para visualizar creencias
    es_objetivo                  # Comprueba si la celda actual es la salida S
)

from palacio_interactivo import acciones_posibles_bayes


# --------------------
# Programa principal 
# --------------------

if __name__ == "__main__":

    # Tamaño del tablero. 
    n = 6

    # Construcción del tablero real (oculto para el usuario):
    #    - utilizamos set porque pueden coexistir varios elementos en una misma celda, por ejemplo, varias trampas en la misma casilla
    tablero = crear_tablero(n)
    colocar_elementos(tablero)

    # Estado inicial del agente (Capitán Willard):
    #    - posicion arranca siempre en la esquina (0,0) siguiendo el enunciado.
    posicion = (0, 0)

    # Estado:
    #    - 1 granada inicial.
    #    - si ya has encontrado a Kurtz (CK) y lo llevas contigo.
    #    - si sigues vivo 
    estado = {"granada": 1, "lleva_ck": False, "vivo": True}

    # Tablero conocido:
    #    - Representa lo que el jugador sabe del mundo.
    #    - No contiene información perfecta: solo marca celdas visitadas, muerte, salida...
    tablero_conocido = crear_tablero_conocido(n)

    # Marcamos la celda inicial como explorada (·).
    tablero_conocido[0][0] = "·"

    # Inicialización de creencias Bayes:
    #    beliefs es un diccionario con matrices de probabilidad:
    beliefs = crear_beliefs(n, inicio=(0, 0))

    # p0 es el percepto inicial:
    p0 = percept(posicion, tablero, grito=False)

    # Actualizamos todas las creencias según Bayes y se renormaliza para que la distribución sume 1.
    actualizar_todas_las_creencias(beliefs, p0, posicion, n)

    # --------------------------------------------------------
    # Visualización del estado inicial
    # --------------------------------------------------------
    print("\nEstado inicial (Bayes):")

    # Muestra el tablero conocido (lo visto hasta ahora).
    mostrar_tablero(tablero_conocido, posicion)

    N = len(beliefs["F"])

    # Construimos un mapa de “probabilidad de trampa” como suma de: P(trampa) = P(F) + P(P) + P(D)
    mapa_trampas = [
        [beliefs["F"][i][j] + beliefs["P"][i][j] + beliefs["D"][i][j] for j in range(n)]
        for i in range(N)
    ]

    # Mostramos 3 heatmaps como pide el enunciado
    # Ajustamos vmax para mejorar lectura:
    mostrar_heatmaps(mapa_trampas, "P(trampa)=F+P+D", posicion, vmax=0.2)
    mostrar_heatmaps(beliefs["M"], "P(M)", posicion, vmax=1.0)
    mostrar_heatmaps(beliefs["S"], "P(S)", posicion, vmax=1.0)

    # --------------------------------------------------------
    # Bucle principal del juego (modo interactivo)
    #   - Mientras el agente esté vivo:
    #       * pide acción al usuario (mover, granada, etc.)
    #       * actualiza tablero_conocido y beliefs
    #       * comprueba condiciones de fin
    # --------------------------------------------------------
    while estado["vivo"]:
        posicion, estado, _ = acciones_posibles_bayes(
            posicion, tablero, estado, tablero_conocido, beliefs,
            umbral=0.2,
            grito_prev=False
        )

        # Si el usuario murió (trampa o enemigo), salimos del bucle.
        if not estado["vivo"]:
            break

        # Condición de victoria: estar en la salida (S) Y haber encontrado a Kurtz (CK).
        if es_objetivo(posicion, tablero) and estado.get("lleva_ck"):
            print("¡Objetivo alcanzado: salida + CK encontrado!")
            break

        # Caso: llegas a la salida pero aún no tienes a CK.
        # En este caso, el juego continúa (tienes que seguir buscando).
        elif es_objetivo(posicion, tablero) and not estado.get("lleva_ck"):
            print("Estás en la salida, pero aún no has encontrado a CK.")

"""Simulaciones de Martingala, colas e inventarios."""

from __future__ import annotations


def simular_volados(
    valores_r: list[float], capital: float, apuesta_inicial: float, meta: float
) -> dict:
    if capital <= 0 or apuesta_inicial <= 0 or meta <= capital:
        raise ValueError("R, capital, apuesta inicial y meta deben ser válidos.")
    saldo = capital
    apuesta = apuesta_inicial
    jugadas = []
    for i, r in enumerate(valores_r, start=1):
        if not 0 <= r <= 1:
            raise ValueError("Cada R debe estar en el intervalo [0, 1].")
        if saldo >= meta or saldo <= 0:
            break
        apostado = min(apuesta, saldo)
        gana = r < 0.5
        saldo = saldo + apostado if gana else saldo - apostado
        jugadas.append(
            {"juego": i, "R": r, "apuesta": apostado, "resultado": "Gana" if gana else "Pierde",
             "saldo": saldo}
        )
        if not gana:
            apuesta *= 2
    return {
        "jugadas": jugadas,
        "saldo_final": saldo,
        "exito": saldo >= meta,
        "quiebra": saldo <= 0,
        "completa": saldo >= meta or saldo <= 0,
    }


def simular_martingala(
    corridas_r: list[list[float]], capital: float, apuesta_inicial: float, meta: float
) -> dict:
    corridas = [
        simular_volados(valores, capital, apuesta_inicial, meta) for valores in corridas_r
    ]
    exitos = sum(corrida["exito"] for corrida in corridas)
    completas = sum(corrida["completa"] for corrida in corridas)
    return {
        "corridas": corridas,
        "exitos": exitos,
        "total": len(corridas),
        "corridas_completas": completas,
        "corridas_inconclusas": len(corridas) - completas,
        "probabilidad": exitos / completas if completas else 0.0,
        "probabilidad_sobre_total": exitos / len(corridas) if corridas else 0.0,
    }


def simular_cola(
    valores_llegada: list[float], valores_servicio: list[float],
    a1: float, b1: float, a2: float, b2: float,
) -> dict:
    if not valores_llegada or len(valores_llegada) != len(valores_servicio):
        raise ValueError("Se requiere el mismo número no nulo de R de llegada y servicio.")
    if b1 < a1 or b2 < a2 or a1 < 0 or a2 < 0:
        raise ValueError("Los intervalos deben ser no negativos y estar ordenados.")
    filas = []
    hora_llegada = hora_fin_anterior = 0.0
    total_sistema = total_inactivo = 0.0
    for i, (r_llegada, r_servicio) in enumerate(zip(valores_llegada, valores_servicio), 1):
        if not 0 <= r_llegada <= 1 or not 0 <= r_servicio <= 1:
            raise ValueError("Cada R debe estar en el intervalo [0, 1].")
        entre_llegadas = a1 + (b1 - a1) * r_llegada
        servicio = a2 + (b2 - a2) * r_servicio
        hora_llegada += entre_llegadas
        inicio = max(hora_llegada, hora_fin_anterior)
        inactivo = max(0.0, hora_llegada - hora_fin_anterior)
        hora_fin = inicio + servicio
        permanencia = hora_fin - hora_llegada
        filas.append(
            {"No.": i, "Tiempo llegada": entre_llegadas, "Hora llegada": hora_llegada,
             "Hora inicio servicio": inicio, "Tiempo servicio": servicio,
             "Hora fin servicio": hora_fin, "Tiempo espera en sistema": permanencia,
             "Tiempo servidor inactivo": inactivo}
        )
        total_sistema += permanencia
        total_inactivo += inactivo
        hora_fin_anterior = hora_fin
    return {
        "filas": filas,
        "promedio_sistema": total_sistema / len(filas),
        "tiempo_inactivo": total_inactivo,
        "hora_fin_ultimo": hora_fin_anterior,
        "porcentaje_inactivo": total_inactivo / hora_fin_anterior * 100 if hora_fin_anterior else 0,
    }


def simular_cola_tiempos(
    tiempos_llegada: list[float], tiempos_servicio: list[float]
) -> dict:
    """Calcula la cola a partir de tiempos de llegada y servicio conocidos."""
    if not tiempos_llegada or len(tiempos_llegada) != len(tiempos_servicio):
        raise ValueError("Se requiere igual cantidad no nula de tiempos.")
    if any(tiempo < 0 for tiempo in tiempos_llegada + tiempos_servicio):
        raise ValueError("Los tiempos no pueden ser negativos.")
    filas = []
    hora_llegada = hora_fin_anterior = 0.0
    tiempo_inactivo_total = tiempo_sistema_total = 0.0
    for numero, (entre_llegadas, servicio) in enumerate(
        zip(tiempos_llegada, tiempos_servicio), 1
    ):
        hora_llegada += entre_llegadas
        inicio = max(hora_llegada, hora_fin_anterior)
        inactivo = max(0.0, hora_llegada - hora_fin_anterior)
        hora_fin = inicio + servicio
        permanencia = hora_fin - hora_llegada
        filas.append({
            "No.": numero, "Tiempo llegada": entre_llegadas,
            "Hora llegada": hora_llegada, "Hora inicio servicio": inicio,
            "Tiempo servicio": servicio, "Hora fin servicio": hora_fin,
            "Tiempo espera en sistema": permanencia,
            "Tiempo servidor inactivo": inactivo,
        })
        tiempo_sistema_total += permanencia
        tiempo_inactivo_total += inactivo
        hora_fin_anterior = hora_fin
    return {
        "filas": filas,
        "promedio_sistema": tiempo_sistema_total / len(filas),
        "tiempo_inactivo": tiempo_inactivo_total,
        "hora_fin_ultimo": hora_fin_anterior,
        "porcentaje_inactivo": (
            tiempo_inactivo_total / hora_fin_anterior * 100 if hora_fin_anterior else 0
        ),
    }


def simular_inventario(
    valores_r: list[float],
    demandas: list[int],
    tiempos_entrega: list[int],
    inventario_inicial: int = 150,
    cantidad_pedido: int = 200,
    punto_reorden: int = 100,
) -> dict:
    if not valores_r or len(valores_r) != len(demandas):
        raise ValueError("Se necesita un R y una demanda para cada mes.")
    if len(tiempos_entrega) != len(demandas):
        raise ValueError("Se necesita un tiempo de entrega para cada mes.")
    if inventario_inicial < 0 or cantidad_pedido <= 0 or punto_reorden < 0:
        raise ValueError("Los parámetros de inventario deben ser válidos.")
    if any(demanda < 0 for demanda in demandas):
        raise ValueError("La demanda no puede ser negativa.")
    if any(tiempo not in (1, 2, 3) for tiempo in tiempos_entrega):
        raise ValueError("El tiempo de entrega debe ser de uno, dos o tres meses.")
    if any(not 0 <= valor <= 1 for valor in valores_r):
        raise ValueError("Cada R debe estar en el intervalo [0, 1].")

    filas = []
    entregas: dict[int, int] = {}
    ordenes_en_transito = 0
    siguiente_orden = 1
    inventario_final_anterior = inventario_inicial
    faltante_pendiente = 0

    for indice, (valor_r, demanda, tiempo_entrega) in enumerate(
        zip(valores_r, demandas, tiempos_entrega), 1
    ):
        recibido = entregas.pop(indice, 0)
        if recibido:
            ordenes_en_transito -= 1
            disponible = inventario_final_anterior + recibido
            backorder_surtido = min(disponible, faltante_pendiente)
            inventario_inicial_mes = disponible - backorder_surtido
            faltante_pendiente -= backorder_surtido
        else:
            inventario_inicial_mes = inventario_final_anterior

        if inventario_inicial_mes >= demanda:
            inventario_final = inventario_inicial_mes - demanda
            faltante = 0
            promedio = round((inventario_inicial_mes + inventario_final) / 2)
        else:
            inventario_final = 0
            faltante = demanda - inventario_inicial_mes
            faltante_pendiente += faltante
            promedio = round(inventario_inicial_mes ** 2 / (2 * demanda)) if demanda else 0

        orden = 0
        if inventario_final <= punto_reorden and ordenes_en_transito == 0:
            orden = siguiente_orden
            siguiente_orden += 1
            ordenes_en_transito += 1
            mes_entrega = indice + tiempo_entrega
            if mes_entrega <= len(demandas):
                entregas[mes_entrega] = entregas.get(mes_entrega, 0) + cantidad_pedido
            else:
                ordenes_en_transito -= 1

        filas.append({
            "Mes": indice,
            "Inventario inicial": inventario_inicial_mes,
            "R demanda": valor_r,
            "Demanda": demanda,
            "Inventario final": inventario_final,
            "Faltante": faltante,
            "Orden": orden,
            "Inventario mensual promedio": promedio,
            "Recibo": recibido,
            "Tiempo de entrega": tiempo_entrega if orden else None,
        })
        inventario_final_anterior = inventario_final

    total_ordenes = siguiente_orden - 1
    costo_ordenar = total_ordenes * 100
    costo_inventario = sum(
        fila["Inventario mensual promedio"] for fila in filas
    ) * (20 / 12)
    costo_faltante = sum(fila["Faltante"] for fila in filas) * 50
    return {
        "filas": filas,
        "total_ordenes": total_ordenes,
        "costo_ordenar": costo_ordenar,
        "costo_inventario": costo_inventario,
        "costo_faltante": costo_faltante,
        "costo_total": costo_ordenar + costo_inventario + costo_faltante,
    }

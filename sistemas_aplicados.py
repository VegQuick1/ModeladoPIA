"""Simulaciones de Martingala y de una cola de un solo canal."""

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
    """Simula la cola con tiempos entre llegadas y servicios ya especificados."""
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

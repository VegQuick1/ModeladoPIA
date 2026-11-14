"""Transformada inversa y distribuciones no uniformes."""

from __future__ import annotations

from math import exp, factorial, log, sqrt


def uniforme(valores_r: list[float], a: float, b: float) -> list[float]:
    _validar_r(valores_r)
    if b < a:
        raise ValueError("El límite superior debe ser mayor o igual al inferior.")
    return [a + (b - a) * r for r in valores_r]


def exponencial(valores_r: list[float], lam: float) -> dict:
    _validar_r(valores_r, incluir_cero=False)
    if lam <= 0:
        raise ValueError("lambda debe ser positiva.")
    tiempos = [-log(r) / lam for r in valores_r]
    total = sum(tiempos)
    return {"tiempos": tiempos, "total": total, "promedio": total / len(tiempos)}


def empirica(valores_r: list[float]) -> list[float]:
    _validar_r(valores_r)
    return [sqrt(2 * r) if r <= 0.5 else 2 * r for r in valores_r]


def tabla_poisson(lam: float, limite: float = 0.9999) -> list[dict]:
    if lam <= 0 or not 0 < limite < 1:
        raise ValueError("lambda debe ser positiva y el límite estar entre 0 y 1.")
    filas = []
    acumulada = 0.0
    x = 0
    while x < 10000:
        probabilidad = exp(-lam) * lam**x / factorial(x)
        acumulada += probabilidad
        filas.append({"x": x, "f": probabilidad, "F": min(acumulada, 1.0)})
        if acumulada >= limite:
            return filas
        x += 1
    raise RuntimeError("La acumulación de Poisson no convergió.")


def poisson_inversa(valores_r: list[float], lam: float) -> dict:
    _validar_r(valores_r)
    tabla = tabla_poisson(lam)
    resultados = []
    for r in valores_r:
        if r == 0:
            resultados.append(0)
            continue
        anterior = 0.0
        asignado = tabla[-1]["x"]
        for fila in tabla:
            if anterior < r <= fila["F"]:
                asignado = fila["x"]
                break
            anterior = fila["F"]
        resultados.append(asignado)
    return {"tabla": tabla, "valores": resultados}


def _validar_r(valores_r: list[float], incluir_cero: bool = True) -> None:
    if not valores_r:
        raise ValueError("Se requiere al menos un número R.")
    if any(r < 0 or r > 1 or (not incluir_cero and r == 0) for r in valores_r):
        raise ValueError("Cada R debe estar en el intervalo [0, 1].")

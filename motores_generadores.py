"""Generadores congruenciales y utilidades de periodo."""

from __future__ import annotations

from collections.abc import Callable
from math import gcd, isqrt


def factores_primos(n: int) -> set[int]:
    """Devuelve los factores primos distintos de un entero positivo."""
    factores: set[int] = set()
    divisor = 2
    while divisor <= isqrt(n):
        while n % divisor == 0:
            factores.add(divisor)
            n //= divisor
        divisor += 1
    if n > 1:
        factores.add(n)
    return factores


def periodo_completo_mixto(a: int, c: int, m: int) -> bool:
    """Comprueba las condiciones de Hull-Dobell para periodo m."""
    if m <= 0 or gcd(c, m) != 1:
        return False
    if any((a - 1) % p != 0 for p in factores_primos(m)):
        return False
    return m % 4 != 0 or (a - 1) % 4 == 0


def periodo_completo_multiplicativo(a: int, m: int) -> bool:
    """Comprueba periodo completo para el caso común m=2**k."""
    if m < 2 or a % m == 0:
        return False
    if m & (m - 1) == 0:
        if m == 2:
            return a % 2 == 1
        if m == 4:
            return a % 4 == 3
        return a % 8 in (3, 5)
    return False


def periodo_observado_mixto(
    semilla: int, a: int, c: int, m: int
) -> int | None:
    """Devuelve el primer retorno a la semilla o None si esta es transitoria."""
    return _periodo_observado(semilla, m, lambda x: (a * x + c) % m)


def periodo_observado_multiplicativo(
    semilla: int, a: int, m: int
) -> int | None:
    """Devuelve el primer retorno a la semilla o None si esta es transitoria."""
    return _periodo_observado(semilla, m, lambda x: (a * x) % m)


def _periodo_observado(
    semilla: int, m: int, siguiente: Callable[[int], int]
) -> int | None:
    vistos = {semilla}
    x = semilla
    for periodo in range(1, m + 1):
        x = siguiente(x)
        if x == semilla:
            return periodo
        if x in vistos:
            return None
        vistos.add(x)
    return None


def congruencial_mixto(
    semilla: int, a: int, c: int, m: int, cantidad: int
) -> list[dict[str, int | str]]:
    """Genera Xn y Rn=Xn/m para un congruencial mixto."""
    _validar_parametros(semilla, a, m, cantidad)
    if c < 0:
        raise ValueError("La constante c debe ser no negativa.")
    x = semilla
    filas = []
    for i in range(1, cantidad + 1):
        x_anterior = x
        x = (a * x + c) % m
        filas.append({
            "i": i, "n": i, "Xn": x_anterior, "Xnext": x,
            "X": x, "R": f"{x}/{m}",
        })
    return filas


def congruencial_multiplicativo(
    semilla: int, a: int, m: int, cantidad: int, normalizacion: str = "m"
) -> list[dict[str, int | str]]:
    """Genera un congruencial multiplicativo; normaliza por m o m-1."""
    _validar_parametros(semilla, a, m, cantidad)
    if normalizacion not in {"m", "m-1"}:
        raise ValueError("La normalización debe ser 'm' o 'm-1'.")
    denominador = m if normalizacion == "m" else m - 1
    if denominador <= 0:
        raise ValueError("El módulo no permite la normalización solicitada.")
    x = semilla
    filas = []
    for i in range(1, cantidad + 1):
        x_anterior = x
        x = (a * x) % m
        filas.append({
            "i": i, "n": i, "Xn": x_anterior, "Xnext": x,
            "X": x, "R": f"{x}/{denominador}",
        })
    return filas


def congruencial_mixto_hasta_paro(
    semilla: int, a: int, c: int, m: int, maximo: int = 64
) -> list[dict[str, int | str]]:
    """Genera iteraciones hasta repetir X0 o alcanzar una repetición consecutiva."""
    _validar_parametros(semilla, a, m, maximo)
    if c < 0:
        raise ValueError("La constante c debe ser no negativa.")
    filas = []
    x = semilla
    for i in range(1, maximo + 1):
        x_siguiente = (a * x + c) % m
        filas.append({
            "i": i, "n": i, "Xn": x, "Xnext": x_siguiente,
            "X": x_siguiente, "R": f"{x_siguiente}/{m}",
        })
        if x_siguiente == semilla or x_siguiente == x:
            return filas
        x = x_siguiente
    raise RuntimeError(f"No se alcanzó el criterio de paro en {maximo} iteraciones.")


def congruencial_multiplicativo_hasta_paro(
    semilla: int, a: int, m: int, maximo: int | None = None
) -> list[dict[str, int | str]]:
    """Genera iteraciones hasta regresar a X0 o alcanzar el límite indicado."""
    _validar_parametros(semilla, a, m, maximo if maximo is not None else m)
    cantidad_maxima = maximo if maximo is not None else m
    if cantidad_maxima < 1:
        raise ValueError("El máximo de iteraciones debe ser positivo.")
    x = semilla
    filas = []
    for i in range(1, cantidad_maxima + 1):
        x_siguiente = (a * x) % m
        filas.append({
            "i": i, "n": i, "Xn": x, "Xnext": x_siguiente,
            "X": x_siguiente, "R": f"{x_siguiente}/{m}",
        })
        if x_siguiente == semilla:
            return filas
        x = x_siguiente
    raise RuntimeError(
        f"No se regresó a X0={semilla} en {cantidad_maxima} iteraciones."
    )


def _validar_parametros(semilla: int, a: int, m: int, cantidad: int) -> None:
    if m <= 1:
        raise ValueError("El módulo m debe ser mayor que 1.")
    if not 0 <= semilla < m:
        raise ValueError("La semilla debe pertenecer al intervalo [0, m).")
    if a < 0 or cantidad < 0:
        raise ValueError("El multiplicador y la cantidad deben ser no negativos.")

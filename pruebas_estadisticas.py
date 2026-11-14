"""Pruebas estadísticas para secuencias de números rectangulares."""

from __future__ import annotations

from math import sqrt

CHI_CUADRADO_CRITICOS_005 = {
    1: 3.84, 2: 5.99, 3: 7.81, 4: 9.49, 5: 11.07,
    6: 12.592, 7: 14.067, 8: 15.507, 9: 16.919, 10: 18.307,
    11: 19.675, 12: 21.026, 13: 22.362, 14: 23.685, 15: 24.996,
    16: 26.296, 17: 27.587, 18: 28.869, 19: 30.144, 20: 31.410,
}
KS_CRITICOS_005 = {
    1: 0.975, 2: 0.842, 3: 0.708, 4: 0.624, 5: 0.565,
    6: 0.521, 7: 0.486, 8: 0.457, 9: 0.430, 10: 0.409,
}


def prueba_promedios(valores: list[float], alpha: float = 0.05) -> dict:
    _validar_muestra(valores)
    n = len(valores)
    media = sum(valores) / n
    z0 = abs((media - 0.5) * sqrt(n) / sqrt(1 / 12))
    z_critico = 1.96
    return {
        "n": n,
        "media": media,
        "z0": z0,
        "z_critico": z_critico,
        "acepta": z0 <= z_critico,
        "alpha": alpha,
    }


def prueba_ks(valores: list[float], alpha: float = 0.05) -> dict:
    _validar_muestra(valores)
    ordenados = sorted(valores)
    n = len(ordenados)
    filas = [
        {"i": i, "R_ordenado": r, "F_esperada": i / n, "diferencia": abs(i / n - r)}
        for i, r in enumerate(ordenados, start=1)
    ]
    dn = max(fila["diferencia"] for fila in filas)
    critico = KS_CRITICOS_005.get(n, 1.36 / sqrt(n))
    return {
        "n": n,
        "filas": filas,
        "dn": dn,
        "critico": critico,
        "acepta": dn <= critico,
        "alpha": alpha,
    }


def agrupar_frecuencias(
    observadas: list[int], esperadas: list[float], etiquetas: list[str] | None = None
) -> list[dict]:
    """Agrupa categorías contiguas para que toda FE agrupada sea >= 5."""
    if len(observadas) != len(esperadas) or not observadas:
        raise ValueError("Las listas de frecuencias deben tener igual tamaño no nulo.")
    if any(fe < 0 for fe in esperadas):
        raise ValueError("Las frecuencias esperadas no pueden ser negativas.")
    nombres = etiquetas or [str(i) for i in range(len(observadas))]
    grupos: list[dict] = []
    fo_acum = fe_acum = 0.0
    inicio = 0
    for i, (fo, fe) in enumerate(zip(observadas, esperadas)):
        if fo < 0:
            raise ValueError("Las frecuencias observadas no pueden ser negativas.")
        if fe_acum == 0:
            inicio = i
        fo_acum += fo
        fe_acum += fe
        if fe_acum >= 5:
            grupos.append(
                {"categoria": f"{nombres[inicio]}-{nombres[i]}", "FO": fo_acum, "FE": fe_acum}
            )
            fo_acum = fe_acum = 0.0
    if fe_acum:
        if not grupos:
            raise ValueError("No hay suficientes observaciones para una prueba chi-cuadrado.")
        grupos[-1]["categoria"] += f"-{nombres[-1]}"
        grupos[-1]["FO"] += fo_acum
        grupos[-1]["FE"] += fe_acum
    return grupos


def agrupar_categorias(
    observadas: list[int], esperadas: list[float], etiquetas: list[str] | None = None,
    minimo_esperado: float = 5,
) -> list[dict]:
    """Agrupa categorías contiguas desde la izquierda y consolida la cola."""
    if minimo_esperado <= 0:
        raise ValueError("El mínimo de frecuencia esperada debe ser positivo.")
    if not esperadas or len(observadas) != len(esperadas):
        raise ValueError("Se requiere igual cantidad de frecuencias observadas y esperadas.")
    nombres = etiquetas or [str(i) for i in range(len(observadas))]
    grupos: list[dict] = []
    fo_acum = fe_acum = 0.0
    inicio = 0
    for indice, (fo, fe) in enumerate(zip(observadas, esperadas)):
        if fo < 0 or fe < 0:
            raise ValueError("Las frecuencias no pueden ser negativas.")
        if fe_acum == 0:
            inicio = indice
        fo_acum += fo
        fe_acum += fe
        if fe_acum >= minimo_esperado:
            grupos.append({
                "categoria": f"{nombres[inicio]}-{nombres[indice]}",
                "FO": fo_acum, "FE": fe_acum,
            })
            fo_acum = fe_acum = 0.0
    if fe_acum:
        if not grupos:
            raise ValueError("La muestra es insuficiente para agrupar categorías.")
        grupos[-1]["categoria"] += f"-{nombres[-1]}"
        grupos[-1]["FO"] += fo_acum
        grupos[-1]["FE"] += fe_acum
    return grupos


def resultado_chi_cuadrado(grupos: list[dict], alpha: float = 0.05) -> dict:
    if not grupos or any(grupo["FE"] <= 0 for grupo in grupos):
        raise ValueError("Las categorías deben tener frecuencias esperadas positivas.")
    chi0 = sum((g["FO"] - g["FE"]) ** 2 / g["FE"] for g in grupos)
    gl = len(grupos) - 1
    critico = CHI_CUADRADO_CRITICOS_005.get(gl, float("inf"))
    return {
        "grupos": grupos, "chi0": chi0, "gl": gl, "critico": critico,
        "acepta": gl > 0 and chi0 <= critico, "alpha": alpha,
    }


def prueba_frecuencias(
    valores: list[float], categorias: int = 10, agrupar: bool = True
) -> dict:
    _validar_muestra(valores)
    if categorias < 2:
        raise ValueError("Se requieren al menos dos categorías.")
    observadas = [0] * categorias
    for valor in valores:
        indice = min(int(valor * categorias), categorias - 1)
        observadas[indice] += 1
    esperadas = [len(valores) / categorias] * categorias
    grupos = (
        agrupar_categorias(
            observadas, esperadas, [f"{i / categorias:.1f}" for i in range(categorias)]
        )
        if agrupar else [
            {"categoria": str(i), "FO": fo, "FE": fe}
            for i, (fo, fe) in enumerate(zip(observadas, esperadas))
        ]
    )
    return {
        "n": len(valores),
        "observadas": observadas,
        "esperadas": esperadas,
        **resultado_chi_cuadrado(grupos),
    }


def prueba_poker(valores: list[float], decimales: int = 3) -> dict:
    """Evalúa patrones de tres o cinco dígitos decimales."""
    _validar_muestra(valores)
    if decimales not in (3, 5):
        raise ValueError("La prueba de Póker admite tres o cinco decimales.")
    if decimales == 3:
        categorias = ["Tercia", "Un par", "Todos distintos"]
        probabilidades = [0.01, 0.27, 0.72]
        patrones = {(3,): 0, (2, 1): 1, (1, 1, 1): 2}
    else:
        categorias = [
            "Todos distintos", "Un par", "Dos pares", "Tercia",
            "Full", "Póker", "Quintilla",
        ]
        probabilidades = [0.3024, 0.5040, 0.1080, 0.0720, 0.0090, 0.0045, 0.0001]
        patrones = {
            (1, 1, 1, 1, 1): 0, (2, 1, 1, 1): 1, (2, 2, 1): 2,
            (3, 1, 1): 3, (3, 2): 4, (4, 1): 5, (5,): 6,
        }
    observadas = [0] * len(categorias)
    for valor in valores:
        digitos = (
            f"{min(int(valor * 10**decimales), 10**decimales - 1):0{decimales}d}"
            if decimales == 3 else f"{valor:.5f}".split(".")[1]
        )
        patron = tuple(sorted(
            (digitos.count(digito) for digito in set(digitos)), reverse=True,
        ))
        observadas[patrones[patron]] += 1
    esperadas = [len(valores) * probabilidad for probabilidad in probabilidades]
    if decimales == 5:
        pares_indice = categorias.index("Un par")
        resto_fo = sum(
            fo for indice, fo in enumerate(observadas) if indice != pares_indice
        )
        resto_fe = sum(
            fe for indice, fe in enumerate(esperadas)
            if indice != pares_indice and observadas[indice] > 0
        )
        omitidas = [
            categorias[indice] for indice, fo in enumerate(observadas)
            if indice != pares_indice and fo == 0
        ]
        grupos = [
            {"categoria": "Un par", "FO": observadas[pares_indice],
             "FE": esperadas[pares_indice]},
            {"categoria": "Resto de patrones", "FO": resto_fo, "FE": resto_fe},
        ]
    else:
        grupos = agrupar_categorias(observadas, esperadas, categorias)
    return {
        "n": len(valores), "decimales": decimales,
        "categorias": categorias, "probabilidades": probabilidades,
        "observadas": observadas, "categorias_omitidas": omitidas if decimales == 5 else [],
        "esperadas": esperadas,
        **resultado_chi_cuadrado(grupos),
    }


def prueba_distancias_decimales(
    valores: list[float], minimo_esperado: float = 5
) -> dict:
    """Clasifica el primer dígito repetido dentro de cada R de cinco decimales."""
    _validar_muestra(valores)
    if any(not 0 <= valor < 1 for valor in valores):
        raise ValueError("Cada R debe estar en el intervalo [0, 1).")
    if minimo_esperado <= 0:
        raise ValueError("El mínimo esperado debe ser positivo.")
    digitos_por_numero = [
        f"{valor:.5f}".split(".")[1] for valor in valores
    ]
    huecos: list[int] = []
    for digitos in digitos_por_numero:
        primera_posicion: dict[str, int] = {}
        hueco = 3
        for posicion, digito in enumerate(digitos):
            if digito in primera_posicion:
                hueco = min(posicion - primera_posicion[digito] - 1, 3)
                break
            primera_posicion[digito] = posicion
        huecos.append(hueco)
    observadas = [sum(hueco == indice for hueco in huecos) for indice in range(3)]
    observadas.append(sum(hueco >= 3 for hueco in huecos))
    esperadas = [
        len(valores) * 0.1 * (0.9**indice) for indice in range(3)
    ] + [len(valores) * (0.9**3)]
    grupos = [
        {
            "categoria": "0-2", "FO": sum(observadas[:3]),
            "FE": sum(esperadas[:3]),
        },
        {"categoria": ">=3", "FO": observadas[3], "FE": esperadas[3]},
    ]
    return {
        "n_digitos": len(valores), "digitos_evaluados": 5 * len(valores),
        "digitos_por_numero": digitos_por_numero, "n_huecos": len(huecos),
        "huecos": huecos, "observadas": observadas, "esperadas": esperadas,
        "grupos": grupos, **resultado_chi_cuadrado(grupos),
    }


def prueba_distancias(
    digitos: list[int], minimo_esperado: float = 5
) -> dict:
    """Prueba chi-cuadrado para huecos entre repeticiones de cada dígito."""
    if len(digitos) < 2 or any(digito not in range(10) for digito in digitos):
        raise ValueError("Se requieren al menos dos dígitos en [0, 9].")
    ultima_posicion: dict[int, int] = {}
    huecos: list[int] = []
    for posicion, digito in enumerate(digitos):
        if digito in ultima_posicion:
            huecos.append(posicion - ultima_posicion[digito] - 1)
        ultima_posicion[digito] = posicion
    if len(huecos) < 5:
        raise ValueError("La muestra no produce suficientes huecos para la prueba.")
    max_categoria = 0
    while len(huecos) * (0.9**(max_categoria + 1)) >= minimo_esperado:
        max_categoria += 1
    observadas = [sum(h == i for h in huecos) for i in range(max_categoria + 1)]
    observadas.append(sum(h >= max_categoria + 1 for h in huecos))
    esperadas = [len(huecos) * 0.1 * (0.9**i) for i in range(max_categoria + 1)]
    esperadas.append(len(huecos) * (0.9**(max_categoria + 1)))
    etiquetas = [str(i) for i in range(max_categoria + 1)] + [f">={max_categoria + 1}"]
    grupos = agrupar_categorias(observadas, esperadas, etiquetas, minimo_esperado)
    return {
        "n_digitos": len(digitos), "n_huecos": len(huecos), "huecos": huecos,
        "observadas": observadas, "esperadas": esperadas,
        **resultado_chi_cuadrado(grupos),
    }


def prueba_series(
    valores: list[float], divisiones: int = 3, agrupar: bool = True
) -> dict:
    _validar_muestra(valores)
    if divisiones < 2 or len(valores) < 2:
        raise ValueError("Se requieren dos divisiones y al menos dos números.")
    n_celdas = divisiones * divisiones
    parejas = list(zip(valores, valores[1:]))
    esperada = len(parejas) / n_celdas
    observadas = [[0 for _ in range(divisiones)] for _ in range(divisiones)]
    for primero, segundo in parejas:
        fila = min(int(primero * divisiones), divisiones - 1)
        columna = min(int(segundo * divisiones), divisiones - 1)
        observadas[fila][columna] += 1
    conteos = [cuenta for fila in observadas for cuenta in fila]
    grupos = (
        agrupar_categorias(
            conteos, [esperada] * n_celdas,
            [f"({i // divisiones + 1},{i % divisiones + 1})"
             for i in range(n_celdas)],
        )
        if agrupar else [
            {"categoria": f"({i // divisiones + 1},{i % divisiones + 1})",
             "FO": fo, "FE": esperada}
            for i, fo in enumerate(conteos)
        ]
    )
    return {
        "n_parejas": len(parejas), "divisiones": divisiones,
        "observadas_matriz": observadas, "FE_por_celda": esperada,
        **resultado_chi_cuadrado(grupos),
    }


def prueba_corridas(valores: list[float], alpha: float = 0.05) -> dict:
    """Prueba de independencia por corridas ascendentes y descendentes."""
    _validar_muestra(valores)
    signos = [
        1 if siguiente > anterior else -1
        for anterior, siguiente in zip(valores, valores[1:])
        if siguiente != anterior
    ]
    n1 = signos.count(1)
    n2 = signos.count(-1)
    total = n1 + n2
    corridas = 1 + sum(a != b for a, b in zip(signos, signos[1:])) if total else 0
    n_muestra = total + 1
    if total < 2 or n1 == 0 or n2 == 0:
        return {"n1": n1, "n2": n2, "corridas": corridas, "z0": float("inf"),
                "z_critico": 1.96, "acepta": False, "alpha": alpha}
    media = (2 * n_muestra - 1) / 3
    varianza = (16 * n_muestra - 29) / 90
    z0 = abs((corridas - media) / sqrt(varianza)) if varianza > 0 else float("inf")
    return {
        "n1": n1, "n2": n2, "corridas": corridas, "media_esperada": media,
        "varianza": varianza, "z0": z0, "z_critico": 1.96,
        "acepta": z0 <= 1.96, "alpha": alpha,
    }


def auditar_flujo(valores: list[float]) -> dict:
    return {
        "promedios": prueba_promedios(valores),
        "ks": prueba_ks(valores),
        "frecuencias": prueba_frecuencias(valores),
        "poker": prueba_poker(valores),
        "corridas": prueba_corridas(valores),
    }


def flujo_aceptado(resultados: list[dict]) -> int | None:
    """Retorna índice base cero del primer flujo que pasa las tres pruebas."""
    for i, resultado in enumerate(resultados):
        if all(resultado[nombre]["acepta"]
               for nombre in ("promedios", "ks", "frecuencias", "poker", "corridas")):
            return i
    return None


def _validar_muestra(valores: list[float]) -> None:
    if not valores:
        raise ValueError("La muestra no puede estar vacía.")
    if any(not 0 <= valor <= 1 for valor in valores):
        raise ValueError("Todos los R deben estar en el intervalo [0, 1].")

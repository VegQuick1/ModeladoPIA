"""Catorce retos estocásticos generados dinámicamente por semilla."""

from __future__ import annotations

import random
from fractions import Fraction
from math import isclose

import motores_generadores as generadores
import pruebas_estadisticas as estadisticas
import sistemas_aplicados as sistemas
import variables_no_uniformes as variables


DURACION_CAPITULO = 600
TITULOS = [
    "Generador Congruencial Mixto",
    "Generador Congruencial Multiplicativo",
    "Prueba de Promedios",
    "Prueba de Kolmogorov-Smirnov",
    "Prueba de Frecuencias",
    "Prueba de Distancias: Huecos",
    "Prueba de Series",
    "Prueba de Póker",
    "Distribución Exponencial",
    "Distribución Uniforme",
    "Distribución Empírica",
    "Distribución de Poisson",
    "Colas de un Canal",
    "Juego de Volados: Martingala",
]

_R_PRUEBAS_MEDIOCURSO = [
    0.03991, 0.38555, 0.17546, 0.32643, 0.69572,
    0.24122, 0.61196, 0.30532, 0.03788, 0.48228,
]
_R_DISTANCIAS_MEDIOCURSO = [
    0.03315, 0.01422, 0.43031, 0.05452, 0.71407,
    0.01189, 0.33096, 0.90593, 0.86316, 0.50452,
]
_R_POKER_MEDIOCURSO = [
    0.69910, 0.85385, 0.89889, 0.00024, 0.73827,
    0.33468, 0.11970, 0.96178, 0.63121, 0.62167,
]
_R_VOLADOS_LIBRETA = [
    0.03991, 0.38555, 0.17546, 0.32843, 0.69572,
    0.24122, 0.61196, 0.88722, 0.65961, 0.03788,
]
_R_CAJA = [
    9, 2, 6, 8, 6, 9, 4, 3, 5, 5, 5, 10, 2, 2, 4, 8, 8, 3, 6, 3,
]
_SERVICIO_CAJA = [
    3, 2, 4, 6, 4, 4, 3, 3, 4, 4, 6, 3, 1, 4, 3, 2, 2, 3, 5, 2,
]
_R_DISTRIBUCIONES = [0.76971, 0.82534, 0.63249, 0.11073]
CASOS_OFICIALES_PDF = {
    1: {
        "X0": 13, "a": 50, "c": 17, "m": 64,
        "iteraciones": 6, "periodo_esperado": 64,
    },
    2: {
        "X0": 7, "a": 5, "m": 64,
        "iteraciones": 16, "periodo_esperado": 16,
    },
    3: {"valores_R": _R_PRUEBAS_MEDIOCURSO.copy(), "alpha": 0.05},
    4: {
        "valores_R": [
            0.03991, 0.17546, 0.69572, 0.61196, 0.03788,
            0.38555, 0.32643, 0.24122, 0.30532, 0.48228,
        ],
        "D_critico": 0.409, "alpha": 0.05,
    },
    5: {
        "valores_R": _R_PRUEBAS_MEDIOCURSO.copy(),
        "categorias": 4, "agrupar": False, "alpha": 0.05,
    },
    6: {"valores_R": _R_DISTANCIAS_MEDIOCURSO.copy(), "alpha": 0.05},
    7: {
        "valores_R": _R_PRUEBAS_MEDIOCURSO.copy(),
        "divisiones": 2, "agrupar": False, "alpha": 0.05,
    },
    8: {
        "valores_R": _R_POKER_MEDIOCURSO.copy(),
        "decimales": 5, "alpha": 0.05,
    },
    9: {"valores_R": _R_DISTRIBUCIONES.copy(), "lambda": 3},
    10: {"valores_R": _R_DISTRIBUCIONES.copy(), "a": 2, "b": 4},
    11: {"valores_R": _R_DISTRIBUCIONES.copy()},
    12: {"valores_R": _R_DISTRIBUCIONES.copy(), "lambda": 5},
    13: {
        "tiempos_llegada": _R_CAJA.copy(),
        "tiempos_servicio": _SERVICIO_CAJA.copy(),
        "a1": 1, "b1": 10, "a2": 1, "b2": 6,
    },
    14: {
        "valores_R": _R_VOLADOS_LIBRETA.copy(),
        "corridas_R": [
            _R_VOLADOS_LIBRETA[0:2], _R_VOLADOS_LIBRETA[2:4],
            _R_VOLADOS_LIBRETA[4:8], _R_VOLADOS_LIBRETA[8:10],
        ],
        "capital": 30, "apuesta_inicial": 10, "meta": 50,
    },
}
ORIGEN_OFICIAL_PDF = {
    1: "Libreta de apuntes, cap. 01: generador mixto, X0=13, a=50, c=17, m=64.",
    2: "Libreta de apuntes, cap. 02: generador multiplicativo, X0=7, a=5, m=64.",
    3: "MedioCurso.pdf, capítulo 3: prueba de promedios, muestra oficial N=10.",
    4: "MedioCurso.pdf, capítulo 4: prueba Kolmogorov-Smirnov, muestra oficial N=10.",
    5: "MedioCurso.pdf, capítulo 5: prueba de frecuencias, muestra oficial N=10.",
    6: "MedioCurso.pdf, capítulo 6: prueba de distancias dentro de cinco decimales, N=10.",
    7: "MedioCurso.pdf, capítulo 7: prueba de series, nueve parejas en cuadrícula 2x2.",
    8: "MedioCurso.pdf, capítulo 8: prueba de Póker con cinco decimales, N=10.",
    9: "Ordinario.pdf, capítulo 9: cajero automático, exponencial con lambda=3.",
    10: "Ordinario.pdf, capítulo 10: envasado de refrescos, uniforme U(2,4).",
    11: "Ordinario.pdf, capítulo 11: transmisión de mensajes, distribución empírica.",
    12: "Ordinario.pdf, capítulo 12: demanda semanal, Poisson con lambda=5.",
    13: "Ordinario.pdf, capítulo 13: caja de supermercado, 20 clientes.",
    14: "Libreta de apuntes, cap. 14: capital 30, apuesta 10, meta 50 y secuencia indicada.",
}


def crear_caso(
    numero: int, semilla: int | None = None, modo_ejecucion: str = "DINAMICO"
) -> dict:
    if numero not in range(1, 15):
        raise ValueError("El capítulo debe estar entre 1 y 14.")
    if modo_ejecucion not in {"DINAMICO", "OFICIAL_PDF"}:
        raise ValueError("El modo debe ser DINAMICO u OFICIAL_PDF.")
    semilla = semilla if semilla is not None else random.SystemRandom().randrange(1, 2**31)
    rng = random.Random(semilla)
    datos_oficiales = CASOS_OFICIALES_PDF.get(numero) if modo_ejecucion == "OFICIAL_PDF" else None
    caso = {
        "numero": numero, "titulo": TITULOS[numero - 1], "semilla": semilla,
        "duracion": 720 if numero == 12 else DURACION_CAPITULO,
        "narrativa": "", "tabla": [], "formula": "",
        "formato": "", "campos": [], "esperado": {}, "auditoria": {},
        "respuestas": [], "modo_ejecucion": modo_ejecucion,
        "origen_problema": (
            ORIGEN_OFICIAL_PDF[numero] if datos_oficiales is not None
            else f"Generación dinámica con semilla {semilla}."
        ),
    }

    if numero in (1, 2):
        _caso_generador(caso, rng, numero, datos_oficiales)
    elif numero == 3:
        _caso_promedios(caso, rng, datos_oficiales)
    elif numero == 4:
        _caso_ks(caso, rng, datos_oficiales)
    elif numero == 5:
        _caso_frecuencias(caso, rng, datos_oficiales)
    elif numero == 6:
        _caso_distancias(caso, rng, datos_oficiales)
    elif numero == 7:
        _caso_series(caso, rng, datos_oficiales)
    elif numero == 8:
        _caso_poker(caso, rng, datos_oficiales)
    elif numero == 9:
        _caso_exponencial(caso, rng, datos_oficiales)
    elif numero == 10:
        _caso_uniforme(caso, rng, datos_oficiales)
    elif numero == 11:
        _caso_empirica(caso, rng, datos_oficiales)
    elif numero == 12:
        _caso_poisson(caso, rng, datos_oficiales)
    elif numero == 13:
        _caso_cola(caso, rng, datos_oficiales)
    else:
        _caso_volados(caso, rng, datos_oficiales)
    _configurar_tabla_interactiva(caso)
    return caso


def _caso_generador(
    caso: dict, rng: random.Random, numero: int, oficial: dict | None = None
) -> None:
    if oficial:
        m, a, x0 = oficial["m"], oficial["a"], oficial["X0"]
        c = oficial.get("c", 0)
        cantidad = oficial["iteraciones"]
    elif numero == 1:
        m = rng.choice((8, 10, 12, 16, 20, 32))
        for _ in range(1000):
            a, c, x0 = rng.randrange(m), rng.randrange(1, m), rng.randrange(m)
            try:
                filas = generadores.congruencial_mixto_hasta_paro(
                    x0, a, c, m, min(16, m),
                )
                if len(filas) >= 4:
                    break
            except RuntimeError:
                continue
        else:
            raise RuntimeError("No se pudo generar un caso mixto con paro manejable.")
        cantidad = len(filas)
    else:
        m = rng.choice((16, 32, 64))
        a = rng.choice((5, 11)) if m >= 16 else 5
        x0 = rng.randrange(1, m, 2)
        c = 0
        filas = generadores.congruencial_multiplicativo_hasta_paro(
            x0, a, m, m // 4,
        )
        cantidad = len(filas)
    periodo_esperado = (
        oficial["periodo_esperado"] if oficial
        else m if numero == 1 else m // 4
    )
    if numero == 1:
        if oficial:
            filas = generadores.congruencial_mixto(x0, a, c, m, cantidad)
        else:
            filas = generadores.congruencial_mixto_hasta_paro(
                x0, a, c, m, min(16, m),
            )
        periodo_observado = len(filas)
        ciclo_completo = (
            periodo_observado == periodo_esperado
            and filas[-1]["Xnext"] == x0
        )
        parametros = {"X0": x0, "a": a, "c": c, "m": m}
        caso["narrativa"] = (
            f"Calcula Xₙ₊₁=(aXₙ+c) mod m con X₀={x0}, a={a}, c={c}, m={m}. "
            "Detén la tabla al regresar a X₀ o al repetirse Xₙ₊₁=Xₙ."
        )
        caso["auditoria"] = {
            "parametros": {"tipo": "mixto", **parametros,
                           "periodo_completo": ciclo_completo,
                           "periodo_esperado": periodo_esperado,
                           "periodo_observado": periodo_observado},
            "tabla_generada": filas,
        }
    else:
        if oficial:
            filas = generadores.congruencial_multiplicativo(x0, a, m, cantidad)
        periodo_observado = generadores.periodo_observado_multiplicativo(x0, a, m)
        ciclo_completo = (
            periodo_observado == periodo_esperado
            and filas[-1]["Xnext"] == x0
        )
        parametros = {"X0": x0, "a": a, "m": m}
        caso["narrativa"] = (
            f"Calcula Xₙ₊₁=aXₙ mod m con X₀={x0}, a={a}, m={m} y "
            f"PE=m/4={periodo_esperado}. Detén la tabla cuando vuelva a X₀."
        )
        caso["auditoria"] = {
            "parametros": {"tipo": "multiplicativo", **parametros,
                           "periodo_completo": ciclo_completo,
                           "periodo_esperado": periodo_esperado,
                           "periodo_observado": periodo_observado},
            "tabla_generada": filas,
        }
    filas_calculo = list(filas)
    if numero == 1:
        x = filas[-1]["Xnext"]
        fila_extra = {
            "i": len(filas) + 1, "n": len(filas) + 1, "Xn": x,
            "Xnext": (a * x + c) % m, "X": (a * x + c) % m,
            "R": f"{(a * x + c) % m}/{m}",
        }
        filas_calculo.append(fila_extra)
    else:
        x = filas[-1]["Xnext"]
        filas_calculo.append({
            "i": len(filas) + 1, "n": len(filas) + 1, "Xn": x,
            "Xnext": (a * x) % m, "X": (a * x) % m,
            "R": f"{(a * x) % m}/{m}",
        })
    for fila in filas_calculo:
        producto = a * fila["Xn"] + c if numero == 1 else a * fila["Xn"]
        cociente, residuo = divmod(producto, m)
        fila["operacion"] = (
            f"{cociente}+{residuo}/{m}" if cociente else f"{residuo}/{m}"
        )
    caso["auditoria"]["tabla_interactiva"] = filas_calculo
    caso["auditoria"]["tabla_generada"] = filas_calculo
    caso["esperado"] = {
        f"{nombre}{i}": fila[clave]
        for i, fila in enumerate(filas_calculo, 1)
        for nombre, clave in (
            ("n", "n"), ("Xn", "Xn"), ("Xnext", "Xnext"), ("R", "R"),
        )
    }
    caso["esperado"]["periodo"] = "Aceptados" if ciclo_completo else "Rechazados"
    caso["auditoria"]["periodo_veredicto"] = caso["esperado"]["periodo"]
    caso["auditoria"]["iteraciones_hasta_paro"] = len(filas)
    caso["auditoria"]["criterio_paro"] = (
        "Xn+1 == X0 o Xn+1 == Xn" if numero == 1 else "Xn+1 == X0"
    )
    caso["tabla"] = [
        ["n", "Xn", "Xn+1", "# Rectangular"],
        *[
            [fila["n"], fila["Xn"], fila["Xnext"], fila["R"]]
            for fila in filas_calculo
        ],
    ]
    caso["formula"] = (
        f"Xₙ₊₁ = ({a}Xₙ + {c}) mod {m}"
        if numero == 1 else f"Xₙ₊₁ = {a}Xₙ mod {m}\nPE = m / 4 = {periodo_esperado}"
    )
    caso["formato"] = "Completa las filas hasta que se cumpla la condición de paro."


def _caso_promedios(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = oficial["valores_R"].copy() if oficial else _muestra_uniforme_balanceada(rng, 20)
    resultado = estadisticas.prueba_promedios(valores)
    caso["narrativa"] = (
        f"Analiza N={len(valores)} números rectangulares. Calcula la media y "
        "Z₀=|(media−0.5)√N / √(1/12)|. Con α=0.05, Z crítico=1.96."
    )
    caso["tabla"] = [["i", "Rᵢ"]] + [
        [i + 1, f"{valor:.5f}" if oficial else f"{valor:.4f}"]
        for i, valor in enumerate(valores)
    ]
    caso["formato"] = "Ingresa la media, Z₀ y el veredicto de H₀."
    caso["campos"] = [
        _campo("media", "Media", "decimal"),
        _campo("z0", "Z₀", "decimal"),
        _campo("zcrit", "Z de tabla", "decimal"),
        _campo("veredicto", "Decisión H₀", "selector", ["Acepta H₀", "Rechaza H₀"]),
    ]
    caso["esperado"] = {
        "media": resultado["media"], "z0": resultado["z0"],
        "zcrit": 1.96,
        "veredicto": "Acepta H₀" if resultado["acepta"] else "Rechaza H₀",
    }
    caso["auditoria"] = {
        "valores_R": valores,
        "alpha": oficial.get("alpha", 0.05) if oficial else 0.05,
        **resultado,
    }


def _caso_ks(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = oficial["valores_R"].copy() if oficial else _muestra_uniforme_balanceada(rng, 10)
    resultado = estadisticas.prueba_ks(valores)
    if oficial and "D_critico" in oficial:
        resultado["critico"] = oficial["D_critico"]
        resultado["acepta"] = resultado["dn"] <= resultado["critico"]
    tabla = [["i", "R ordenado", "F(i)=i/N", "Dᵢ"]] + [
        [fila["i"], f'{fila["R_ordenado"]:.5f}' if oficial else f'{fila["R_ordenado"]:.4f}',
         f'{fila["F_esperada"]:.4f}', "?"]
        for fila in resultado["filas"]
    ]
    caso["narrativa"] = (
        f"Ordena la muestra de N={len(valores)} y calcula Dₙ=max|i/N−Rᵢ|. "
        f"Valor crítico D₀.₀₅,{len(valores)}={resultado['critico']:.4f}."
    )
    caso["tabla"] = tabla
    caso["formato"] = "Ingresa Dₙ y el veredicto de H₀ (Dₙ ≤ D crítico)."
    caso["campos"] = [
        _campo("dn", "Dₙ", "decimal"),
        _campo("critico_tabla", "d₀.₀₅,N de tabla", "decimal"),
        _campo("veredicto", "Decisión H₀", "selector", ["Acepta H₀", "Rechaza H₀"]),
    ]
    caso["esperado"] = {
        "dn": resultado["dn"],
        "critico_tabla": resultado["critico"],
        "veredicto": "Acepta H₀" if resultado["acepta"] else "Rechaza H₀",
    }
    caso["auditoria"] = {
        "valores_R": valores,
        "alpha": oficial.get("alpha", 0.05) if oficial else 0.05,
        **resultado,
    }


def _caso_frecuencias(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = (
        oficial["valores_R"].copy() if oficial
        else _muestra_uniforme_balanceada(rng, 200)
    )
    categorias = oficial.get("categorias", 4) if oficial else 4
    resultado = estadisticas.prueba_frecuencias(
        valores, categorias, agrupar=oficial.get("agrupar", True) if oficial else True,
    )
    tabla = [["Intervalo", "FO", "FE", "Término χ²"]] + [
        [f"[{i / categorias:.2f}, {(i + 1) / categorias:.2f})",
         resultado["observadas"][i], resultado["esperadas"][i], "?"]
        for i in range(categorias)
    ]
    caso["narrativa"] = (
        f"Divide [0,1) en {categorias} subintervalos con N={len(valores)}. "
        f"Calcula χ₀² y contrasta con χ² crítico={resultado['critico']:.3f}, "
        f"gl={resultado['gl']}, α=0.05."
    )
    caso["tabla"] = tabla
    caso["formato"] = "Ingresa χ₀² y el veredicto de H₀."
    caso["campos"] = [
        _campo("chi0", "χ₀²", "decimal"),
        _campo("critico_tabla", "χ² crítico de tabla", "decimal"),
        _campo("veredicto", "Decisión H₀", "selector", ["Acepta H₀", "Rechaza H₀"]),
    ]
    caso["esperado"] = {
        "chi0": resultado["chi0"],
        "critico_tabla": resultado["critico"],
        "veredicto": "Acepta H₀" if resultado["acepta"] else "Rechaza H₀",
    }
    caso["auditoria"] = {
        "valores_R": valores,
        "alpha": oficial.get("alpha", 0.05) if oficial else 0.05,
        **resultado,
    }


def _caso_distancias(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores_r = oficial["valores_R"].copy() if oficial else None
    if valores_r is not None:
        resultado = estadisticas.prueba_distancias_decimales(valores_r)
        digitos = resultado["digitos_por_numero"]
        tabla = [["Hueco i", "FO", "FE", "Agrupación"]] + [
            [str(indice) if indice < 3 else "≥3", resultado["observadas"][indice],
             round(resultado["esperadas"][indice], 3),
             "0-2" if indice < 3 else "≥3"]
            for indice in range(4)
        ] + [
            [f"Grupo {grupo['categoria']}", grupo["FO"], round(grupo["FE"], 3), ""]
            for grupo in resultado["grupos"]
        ]
    else:
        digitos = [rng.randrange(10) for _ in range(500)]
        resultado = estadisticas.prueba_distancias(digitos)
        tabla = [["Hueco i", "FO", "FE", "FO−FE"]] + [
            [g["categoria"], g["FO"], round(g["FE"], 3), "?"]
            for g in resultado["grupos"]
        ]
    caso["narrativa"] = (
        f"Para cada uno de los {len(valores_r)} números, busca la primera repetición "
        "dentro de sus cinco decimales. Clasifica i=0, 1, 2 y la cola i≥3; "
        "agrupa las categorías indicadas para calcular χ₀²."
        if valores_r is not None else
        f"Secuencia de {len(digitos)} primeros dígitos decimales. Mide los huecos "
        f"entre repeticiones; hay {resultado['n_huecos']} huecos. FEᵢ=N_huecos·0.1·0.9ⁱ "
        "y la cola usa 0.9ᵏ. Las categorías adyacentes se agrupan hasta FE≥5."
    )
    caso["tabla"] = tabla
    caso["formato"] = "Calcula el χ₀² de las categorías agrupadas y decide sobre H₀."
    caso["campos"] = [
        *[
            _campo(f"FO{indice}", f"FO{indice}", "entero")
            for indice in range(4)
        ],
        *[
            _campo(f"FE{indice}", f"FE{indice}", "decimal")
            for indice in range(4)
        ],
        _campo("chi0", "χ₀² agrupado", "decimal"),
        _campo("critico_tabla", "χ² crítico de tabla", "decimal"),
        _campo("veredicto", "Decisión H₀", "selector", ["Acepta H₀", "Rechaza H₀"]),
    ]
    caso["esperado"] = {
        **{
            f"FO{indice}": resultado["observadas"][indice]
            for indice in range(4)
        },
        **{
            f"FE{indice}": resultado["esperadas"][indice]
            for indice in range(4)
        },
        "chi0": resultado["chi0"],
        "critico_tabla": resultado["critico"],
        "veredicto": "Acepta H₀" if resultado["acepta"] else "Rechaza H₀",
    }
    caso["auditoria"] = {
        "digitos" if valores_r is None else "digitos_por_numero": digitos,
        "alpha": oficial.get("alpha", 0.05) if oficial else 0.05,
        **resultado,
    }
    if valores_r is not None:
        caso["auditoria"]["valores_R"] = valores_r


def _caso_series(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = (
        oficial["valores_R"].copy() if oficial
        else _muestra_uniforme_balanceada(rng, 200)
    )
    divisiones = oficial.get("divisiones", 2) if oficial else 2
    resultado = estadisticas.prueba_series(
        valores, divisiones=divisiones,
        agrupar=oficial.get("agrupar", True) if oficial else True,
    )
    tabla = [["Celda (Rᵢ,Rᵢ₊₁)", "FO", "FE"]] + [
        [f"({i + 1},{j + 1})", resultado["observadas_matriz"][i][j],
         round(resultado["FE_por_celda"], 3)]
        for i in range(divisiones) for j in range(divisiones)
    ]
    caso["narrativa"] = (
        f"Forma {resultado['n_parejas']} parejas consecutivas y distribúyelas en "
        f"2×2 celdas. gl=3, α=0.05, χ² crítico={resultado['critico']:.3f}."
    )
    caso["tabla"] = tabla
    caso["formato"] = "Calcula χ₀² y selecciona el veredicto de independencia H₀."
    caso["campos"] = [
        _campo("FE_pareja", "Frecuencia esperada por celda", "decimal"),
        _campo("chi0", "χ₀²", "decimal"),
        _campo("critico_tabla", "χ² crítico de tabla", "decimal"),
        _campo("veredicto", "Decisión H₀", "selector", ["Acepta H₀", "Rechaza H₀"]),
    ]
    caso["esperado"] = {
        "FE_pareja": resultado["FE_por_celda"],
        "chi0": resultado["chi0"],
        "critico_tabla": resultado["critico"],
        "veredicto": "Acepta H₀" if resultado["acepta"] else "Rechaza H₀",
    }
    caso["auditoria"] = {
        "valores_R": valores,
        "alpha": oficial.get("alpha", 0.05) if oficial else 0.05,
        **resultado,
    }


def _caso_poker(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = (
        oficial["valores_R"].copy() if oficial
        else _muestra_uniforme_balanceada(rng, 200)
    )
    decimales = oficial.get("decimales", 3) if oficial else 3
    resultado = estadisticas.prueba_poker(valores, decimales=decimales)
    if decimales == 5:
        indice_par = resultado["categorias"].index("Un par")
        tabla = [["Patrón (5 dígitos)", "FO", "Probabilidad", "FE", "Agrupación"]] + [
            [
                categoria, resultado["observadas"][indice],
                f'{resultado["probabilidades"][indice]:.5f}',
                f'{resultado["esperadas"][indice]:.4f}',
                "Un par" if indice == indice_par else "Resto",
            ]
            for indice, categoria in enumerate(resultado["categorias"])
        ] + [
            [grupo["categoria"], grupo["FO"], "", f'{grupo["FE"]:.4f}', "Total"]
            for grupo in resultado["grupos"]
        ]
    else:
        tabla = [["Patrón (3 dígitos)", "FO", "Probabilidad", "FE", "Contribución"]] + [
            [grupo["categoria"], grupo["FO"], f'{grupo["FE"] / len(valores):.5f}',
             f'{grupo["FE"]:.4f}', "?"]
            for grupo in resultado["grupos"]
        ]
    probabilidades_texto = ", ".join(
        f"{nombre}={probabilidad:.5f}"
        for nombre, probabilidad in zip(
            resultado["categorias"], resultado["probabilidades"],
        )
    )
    caso["narrativa"] = (
        f"Evalúa {len(valores)} R con {decimales} dígitos decimales. "
        f"Probabilidades por patrón: {probabilidades_texto}. "
        f"Calcula χ² agrupado (gl={resultado['gl']}, crítico={resultado['critico']:.3f})."
    )
    caso["tabla"] = tabla
    caso["formato"] = "Calcula χ₀² agrupado y selecciona si la secuencia pasa Póker."
    caso["campos"] = [
        *[
            _campo(f"FO{indice}", f"FO {categoria}", "entero")
            for indice, categoria in enumerate(resultado["categorias"])
        ],
        *[
            _campo(f"FEp{indice}", f"FE {categoria}", "decimal")
            for indice, categoria in enumerate(resultado["categorias"])
        ],
        _campo("chi0", "χ₀² agrupado", "decimal"),
        _campo("critico_tabla", "χ² crítico de tabla", "decimal"),
        _campo("veredicto", "Prueba de Póker", "selector", ["Acepta H₀", "Rechaza H₀"]),
    ]
    caso["esperado"] = {
        **{
            f"FO{indice}": valor
            for indice, valor in enumerate(resultado["observadas"])
        },
        **{
            f"FEp{indice}": valor
            for indice, valor in enumerate(resultado["esperadas"])
        },
        "chi0": resultado["chi0"],
        "critico_tabla": resultado["critico"],
        "veredicto": "Acepta H₀" if resultado["acepta"] else "Rechaza H₀",
    }
    caso["auditoria"] = {
        "valores_R": valores,
        "alpha": oficial.get("alpha", 0.05) if oficial else 0.05,
        **resultado,
    }


def _caso_exponencial(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = (
        oficial["valores_R"].copy() if oficial
        else [0.1 + 0.89 * rng.random() for _ in range(5)]
    )
    lam = oficial["lambda"] if oficial else round(rng.uniform(0.35, 1.2), 2)
    resultado = variables.exponencial(valores, lam)
    caso["narrativa"] = (
        f"En el cajero automático, λ={lam} clientes/min. Aplica T_A=−ln(R)/λ "
        "a los cuatro números R. Calcula T_A1…T_A4, T_TC y T_PA."
        if oficial else
        f"Con λ={lam}, aplica X=−ln(R)/λ a los cinco números R. "
        "Calcula cada T_Ai, T_TC=ΣT_Ai y T_PA=T_TC/N."
    )
    caso["tabla"] = [["i", "Rᵢ", "T_Ai"]] + [
        [i + 1, f"{r:.5f}" if oficial else f"{r:.4f}", "?"]
        for i, r in enumerate(valores)
    ]
    caso["formato"] = f"Completa los {len(valores)} tiempos y los dos estadísticos."
    caso["campos"] = [
        _campo(f"T{i}", f"T_A{i}", "decimal") for i in range(1, len(valores) + 1)
    ] + [
        _campo("total", "T_TC", "decimal"), _campo("promedio", "T_PA", "decimal"),
    ]
    caso["esperado"] = {
        **{f"T{i}": value for i, value in enumerate(resultado["tiempos"], 1)},
        "total": resultado["total"], "promedio": resultado["promedio"],
    }
    caso["auditoria"] = {
        "valores_R": valores, "lambda": lam, "formula": "−ln(R)/lambda", **resultado,
    }


def _caso_uniforme(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = oficial["valores_R"].copy() if oficial else [rng.random() for _ in range(4)]
    minimo = oficial["a"] if oficial else rng.randint(2, 8)
    maximo = oficial["b"] if oficial else minimo + rng.randint(5, 12)
    resultados = variables.uniforme(valores, minimo, maximo)
    caso["narrativa"] = (
        f"Los tiempos de envasado de refrescos siguen U({minimo},{maximo}) minutos. "
        "Calcula T_E1…T_E4 con X=a+(b−a)R."
        if oficial else
        f"Transforma cuatro R con X=a+(b−a)R, a={minimo}, b={maximo}."
    )
    caso["tabla"] = [["i", "Rᵢ", "Xᵢ"]] + [
        [i + 1, f"{r:.5f}" if oficial else f"{r:.4f}", "?"]
        for i, r in enumerate(valores)
    ]
    caso["formato"] = "Calcula X₁, X₂, X₃ y X₄."
    caso["campos"] = [_campo(f"X{i}", f"X{i}", "decimal") for i in range(1, 5)]
    caso["esperado"] = {f"X{i}": value for i, value in enumerate(resultados, 1)}
    caso["auditoria"] = {
        "valores_R": valores, "a": minimo, "b": maximo,
        "formula": "a+(b-a)R", "resultados": resultados,
    }


def _caso_empirica(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    valores = (
        oficial["valores_R"].copy() if oficial else
        [rng.uniform(0.1, 0.49), rng.uniform(0.51, 0.95),
         rng.uniform(0.1, 0.49), rng.uniform(0.51, 0.95)]
    )
    resultados = variables.empirica(valores)
    caso["narrativa"] = (
        "Calcula los tiempos de transmisión de cuatro mensajes. Aplica X=√(2R) "
        "si R≤0.5 y X=2R si R>0.5."
    )
    caso["tabla"] = [["i", "Rᵢ", "Tramo", "Xᵢ"]] + [
        [i + 1, f"{r:.5f}" if oficial else f"{r:.4f}",
         "√(2R)" if r <= 0.5 else "2R", "?"]
        for i, r in enumerate(valores)
    ]
    caso["formato"] = "Calcula X₁, X₂, X₃ y X₄."
    caso["campos"] = [_campo(f"X{i}", f"X{i}", "decimal") for i in range(1, 5)]
    caso["esperado"] = {f"X{i}": value for i, value in enumerate(resultados, 1)}
    caso["auditoria"] = {
        "valores_R": valores, "formula": "√(2R), R≤0.5; 2R, R>0.5",
        "resultados": resultados,
    }


def _caso_poisson(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    lam = oficial["lambda"] if oficial else round(rng.uniform(2.2, 4.5), 2)
    valores = (
        oficial["valores_R"].copy() if oficial
        else [rng.uniform(0.1, 0.98) for _ in range(4)]
    )
    resultado = variables.poisson_inversa(valores, lam)
    filas_poisson = (
        resultado["tabla"] if oficial
        else resultado["tabla"][:min(10, len(resultado["tabla"]))]
    )
    tabla = [["x", "f(x)", "F(x)"]] + [
        [fila["x"], f'{fila["f"]:.5f}', f'{fila["F"]:.5f}']
        for fila in filas_poisson
    ]
    caso["narrativa"] = (
        f"La demanda semanal trabaja 5 de 7 días, con λ={lam}. Acumula Poisson "
        f"desde x=0 hasta F(x)≥0.9999 y asigna X mediante F(x−1)<R≤F(x). "
        f"R={valores}."
        if oficial else
        f"Con λ={lam}, acumula Poisson hasta F(x)≥0.9999. "
        "Asigna cada R mediante F(x−1)<R≤F(x)."
    )
    caso["tabla"] = tabla
    caso["formato"] = f"Ingresa los {len(valores)} enteros asignados a cada Rᵢ."
    caso["campos"] = [
        _campo(f"X{i}", f"X{i} entero", "entero")
        for i in range(1, len(valores) + 1)
    ]
    caso["esperado"] = {
        f"X{i}": value for i, value in enumerate(resultado["valores"], 1)
    }
    caso["auditoria"] = {
        "lambda": lam, "valores_R": valores, "tabla_completa": resultado["tabla"],
        "mapeo": resultado["valores"], "criterio_paro": 0.9999,
    }


def _caso_cola(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    if oficial:
        tiempos_llegada = oficial["tiempos_llegada"].copy()
        tiempos_servicio = oficial["tiempos_servicio"].copy()
        parametros = {clave: oficial[clave] for clave in ("a1", "b1", "a2", "b2")}
        resultado = sistemas.simular_cola_tiempos(tiempos_llegada, tiempos_servicio)
    else:
        n = 12
        r_llegada = [rng.random() for _ in range(n)]
        r_servicio = [rng.random() for _ in range(n)]
        parametros = {"a1": 2, "b1": 5, "a2": 1, "b2": 4}
        resultado = sistemas.simular_cola(r_llegada, r_servicio, **parametros)
        tiempos_llegada = r_llegada
        tiempos_servicio = r_servicio
    n = len(tiempos_llegada)
    tabla = [list(resultado["filas"][0].keys())]
    for indice, fila in enumerate(resultado["filas"]):
        ultima_seccion = indice >= n - 3
        tabla.append([
            "?" if ultima_seccion and clave in {
                "Hora inicio servicio", "Hora fin servicio", "Tiempo espera en sistema",
                "Tiempo servidor inactivo",
            } else round(valor, 3) if isinstance(valor, float) else valor
            for clave, valor in fila.items()
        ])
    caso["narrativa"] = (
        "Sección de caja de supermercado: 20 clientes, llegadas U(1,10) min "
        "y atención U(1,6) min. Completa las tres últimas filas y calcula el "
        "tiempo promedio en el sistema y el porcentaje de inactividad."
        if oficial else
        "Simula 12 clientes: llegadas U(2,5) y servicio U(1,4). "
        "Completa las últimas filas y calcula permanencia promedio e inactividad del servidor."
    )
    caso["tabla"] = tabla
    caso["formato"] = "Ingresa el tiempo promedio en el sistema (min) y el % inactivo."
    caso["campos"] = [
        _campo("promedio", "Permanencia promedio (min)", "decimal"),
        _campo("inactividad", "Servidor inactivo (%)", "porcentaje"),
    ]
    caso["esperado"] = {
        "promedio": resultado["promedio_sistema"],
        "inactividad": resultado["porcentaje_inactivo"],
    }
    caso["auditoria"] = {
        "parametros": parametros,
        "tiempos_llegada": tiempos_llegada if oficial else None,
        "tiempos_servicio": tiempos_servicio if oficial else None,
        "R_llegada": None if oficial else r_llegada,
        "R_servicio": None if oficial else r_servicio,
        **resultado,
    }


def _caso_volados(caso: dict, rng: random.Random, oficial: dict | None = None) -> None:
    capital = oficial["capital"] if oficial else 40
    apuesta_inicial = oficial["apuesta_inicial"] if oficial else 10
    meta = oficial["meta"] if oficial else 70
    corridas_r: list[list[float]] = []
    if oficial:
        corridas_r = [corrida.copy() for corrida in oficial["corridas_R"]]
    else:
        for _ in range(10):
            valores: list[float] = []
            corrida = sistemas.simular_volados([], capital, apuesta_inicial, meta)
            while not (corrida["exito"] or corrida["quiebra"]):
                valores.extend(rng.random() for _ in range(100))
                corrida = sistemas.simular_volados(valores, capital, apuesta_inicial, meta)
            corridas_r.append(valores)
    resultado = sistemas.simular_martingala(corridas_r, capital, apuesta_inicial, meta)
    tabla = [[
        "Corrida", "R disponibles" if oficial else "R utilizados",
        "Saldo final", "Estado",
    ]]
    for i, corrida in enumerate(resultado["corridas"], 1):
        valores_mostrados = (
            corridas_r[i - 1] if oficial
            else [tirada["R"] for tirada in corrida["jugadas"]]
        )
        estado = (
            "Éxito (finalizada)" if corrida["exito"] else
            "Quiebra (finalizada)" if corrida["completa"] else
            "Inconclusa"
        )
        tabla.append([
            i, ", ".join(f"{valor:.5f}" for valor in valores_mostrados),
            "?", estado,
        ])
    caso["narrativa"] = (
        f"Capital=${capital:.2f}, apuesta=${apuesta_inicial:.2f}, meta=${meta:.2f}. "
        "R<0.5 gana; R>0.5 pierde y dobla la siguiente apuesta, limitada al saldo. "
        "Identifica éxitos, quiebras y corridas inconclusas. Calcula P como éxitos "
        "entre corridas finalizadas; las inconclusas no entran al denominador. "
        "La clave final codifica latitud N=(19+P/2)° y longitud O=(99+(1−P)/2)°."
    )
    if oficial:
        caso["narrativa"] += (
            " El vector oficial se consume en orden y se distribuye entre las corridas "
            "hasta que cada una alcanza la meta o se agotan sus números."
        )
    caso["tabla"] = tabla
    caso["formato"] = "Ingresa la probabilidad de éxito como decimal o porcentaje."
    caso["campos"] = [_campo("probabilidad", "Éxitos / corridas (%)", "probabilidad")]
    caso["esperado"] = {"probabilidad": resultado["probabilidad"]}
    latitud = round(19 + resultado["probabilidad"] / 2, 4)
    longitud = round(99 + (1 - resultado["probabilidad"]) / 2, 4)
    caso["coordenadas"] = f"N {latitud:.4f}°, O {longitud:.4f}°"
    caso["auditoria"] = {
        "capital": capital, "apuesta_inicial": apuesta_inicial, "meta": meta,
        "corridas_R": corridas_r, "R_suministrados": oficial["valores_R"] if oficial else corridas_r[0],
        "tiradas_utilizadas_por_corrida": [
            len(corrida["jugadas"]) for corrida in resultado["corridas"]
        ],
        "numeros_no_utilizados": (
            sum(len(valores) for valores in corridas_r)
            - sum(len(corrida["jugadas"]) for corrida in resultado["corridas"])
        ),
        "criterio_corridas": (
            "Probabilidad calculada sobre corridas completas; cualquier corrida "
            "inconclusa queda identificada por separado."
        ),
        **resultado,
        "coordenadas_decodificadas": caso["coordenadas"],
        "tiradas_utilizadas": len(resultado["corridas"][0]["jugadas"]),
    }


def validar_respuesta(
    caso: dict, entrada: dict[str, str], tolerancia: float = 0.01,
    filas_dinamicas: dict[str, int] | None = None,
) -> dict:
    errores: list[str] = []
    correctos: list[str] = []
    formatos_invalidos: list[str] = []
    for campo in caso["campos"]:
        clave = campo["id"]
        if clave not in entrada:
            continue
        texto = entrada.get(clave, "").strip()
        esperado = caso["esperado"][clave]
        if campo["tipo"] == "selector":
            if texto != esperado:
                errores.append(clave)
            else:
                correctos.append(clave)
            continue
        if campo["tipo"].startswith("fracción"):
            try:
                valor_fraccion = Fraction(texto)
            except (ValueError, ZeroDivisionError):
                formatos_invalidos.append(clave)
                errores.append(clave)
                continue
            try:
                esperado_fraccion = Fraction(str(esperado))
            except (ValueError, ZeroDivisionError):
                raise ValueError(f"Valor esperado inválido para {clave}: {esperado!r}")
            if valor_fraccion == esperado_fraccion:
                correctos.append(clave)
                continue
            try:
                valor_decimal = float(texto)
            except ValueError:
                errores.append(clave)
                continue
            if not isclose(
                valor_decimal, float(esperado_fraccion), rel_tol=0,
                abs_tol=tolerancia,
            ):
                errores.append(clave)
            else:
                correctos.append(clave)
            continue
        try:
            valor = float(texto.removesuffix("%").strip().replace(",", "."))
        except ValueError:
            errores.append(clave)
            continue
        if campo["tipo"] == "probabilidad" and "%" in texto:
            valor /= 100
        elif campo["tipo"] == "probabilidad" and valor > 1:
            valor /= 100
        elif campo["tipo"] == "porcentaje" and 0 <= valor <= 1:
            valor *= 100
        if campo["tipo"] == "entero" and not valor.is_integer():
            errores.append(clave)
        elif not isclose(valor, float(esperado), rel_tol=0, abs_tol=tolerancia):
            errores.append(clave)
        else:
            correctos.append(clave)
    longitud_invalida = ""
    if filas_dinamicas is not None:
        for seccion in caso.get("tabla_interactiva", {}).get("secciones", []):
            if not seccion["dinamica"]:
                continue
            filas_actuales = filas_dinamicas.get(seccion["id"], 0)
            filas_objetivo = seccion["filas_paro"]
            if filas_actuales < filas_objetivo:
                longitud_invalida = seccion["mensaje_faltan"]
                break
            if filas_actuales > filas_objetivo:
                longitud_invalida = (
                    f"Debiste detenerte en la fila {filas_objetivo}; "
                    "hay filas adicionales después de cumplir el criterio de paro"
                )
                break
    return {
        "correcto": not errores and not formatos_invalidos and not longitud_invalida,
        "campos_incorrectos": errores,
        "campos_correctos": correctos,
        "formatos_invalidos": formatos_invalidos,
        "longitud_invalida": longitud_invalida,
        "diagnostico": (
            "Solución confirmada."
            if not errores and not formatos_invalidos and not longitud_invalida else
            longitud_invalida if longitud_invalida else
            "Formato de fracción inválido. Usa una barra, por ejemplo 27/64; "
            "también puedes ingresar el decimal equivalente."
            if formatos_invalidos else
            "Revisa las fórmulas, el redondeo y las unidades de los campos señalados."
        ),
    }


def _campo(
    identificador: str, etiqueta: str, tipo: str, opciones: list[str] | None = None
) -> dict:
    return {"id": identificador, "etiqueta": etiqueta, "tipo": tipo, "opciones": opciones or []}


def _configurar_tabla_interactiva(caso: dict) -> None:
    numero = caso["numero"]
    esperado_original = caso["esperado"].copy()
    campos_originales = {campo["id"]: campo for campo in caso["campos"]}
    campos: list[dict] = []
    secciones: list[dict] = []
    pie: list[str] = []

    def crear_campo(
        identificador: str, etiqueta: str, tipo: str, valor: object,
        opciones: list[str] | None = None,
    ) -> dict:
        caso["esperado"][identificador] = valor
        existente = next(
            (campo for campo in campos if campo["id"] == identificador), None,
        )
        if existente is not None:
            return existente
        campo = _campo(identificador, etiqueta, tipo, opciones)
        campos.append(campo)
        return campo

    def celda_dada(valor: object) -> dict:
        return {"valor": valor}

    def celda_editable(
        identificador: str, etiqueta: str, valor: object, tipo: str = "decimal",
        opciones: list[str] | None = None,
    ) -> dict:
        crear_campo(identificador, etiqueta, tipo, valor, opciones)
        return {"campo": identificador}

    def agregar_pie(identificador: str) -> None:
        original = campos_originales[identificador]
        campos.append(original)
        caso["esperado"][identificador] = esperado_original[identificador]
        pie.append(identificador)

    def agregar_seccion(
        clave: str, titulo: str, columnas: list[str], filas: list[list[dict]],
        dinamica: bool = False, iniciales: int = 3, paro: int | None = None,
        mensaje_faltan: str | None = None,
        scrollable: bool = True,
        visual: str | None = None,
        maximo: int | None = None,
    ) -> None:
        secciones.append({
            "id": clave, "titulo": titulo, "columnas": columnas, "filas": filas,
            "dinamica": dinamica, "filas_iniciales": iniciales,
            "filas_paro": paro if paro is not None else len(filas),
            "max_filas": maximo if maximo is not None else len(filas),
            "mensaje_faltan": mensaje_faltan or (
                "Aún no se detecta el cierre del ciclo ni se alcanza el criterio "
                "de paro; agrega más filas"
            ),
            "scrollable": scrollable,
            "visual": visual,
        })

    if numero in (1, 2):
        datos = caso["auditoria"]["tabla_interactiva"]
        parar_en = caso["auditoria"]["iteraciones_hasta_paro"]
        filas = []
        for indice, fila in enumerate(datos, 1):
            filas.append([
                celda_editable(f"n{indice}", f"n fila {indice}", fila["n"], "entero"),
                celda_editable(f"Xn{indice}", f"Xn fila {indice}", fila["Xn"], "entero"),
                celda_editable(f"Xnext{indice}", f"Xn+1 fila {indice}", fila["Xnext"], "entero"),
                celda_editable(
                    f"R{indice}", f"R{indice} (ej. 27/64)", fila["R"],
                    "fracción (ej. 27/64)",
                ),
            ])
        agregar_seccion(
            "iteraciones", "Iteraciones del generador",
            ["n", "Xn", "Xn+1", "# Rectangular"],
            filas, dinamica=True, iniciales=min(3, parar_en), paro=parar_en,
            maximo=(
                len(filas) if caso["modo_ejecucion"] == "OFICIAL_PDF"
                else min(len(filas), 16)
            ),
        )
        crear_campo(
            "periodo", "Los números rectangulares son:", "selector",
            esperado_original["periodo"], ["Aceptados", "Rechazados"],
        )
        pie.append("periodo")
    elif numero == 3:
        valores = caso["auditoria"]["valores_R"]
        filas = []
        for inicio in range(0, len(valores), 5):
            filas.append([
                celda_dada(f"{valor:.5f}") for valor in valores[inicio:inicio + 5]
            ])
        agregar_seccion(
            "muestra", "Muestra de números rectangulares",
            ["R₁", "R₂", "R₃", "R₄", "R₅"], filas, scrollable=False,
        )
        for clave in ("media", "z0", "zcrit", "veredicto"):
            agregar_pie(clave)
    elif numero == 4:
        filas = []
        for indice, registro in enumerate(caso["auditoria"]["filas"], 1):
            clave = f"D{indice}"
            valor_r = registro["R_ordenado"]
            f_esperada = registro["F_esperada"]
            filas.append([
                celda_dada(indice), celda_dada(f"{valor_r:.5f}"),
                celda_dada(f"{f_esperada:.2f}"),
                celda_editable(clave, f"D{indice}", registro["diferencia"]),
            ])
        agregar_seccion("ks", "Prueba Kolmogorov-Smirnov",
                        ["i", "Xi ordenado", "F(xi)=i/N", "Dn"], filas,
                        scrollable=False)
        for clave in ("dn", "critico_tabla", "veredicto"):
            agregar_pie(clave)
    elif numero == 5:
        valores = caso["auditoria"]["valores_R"]
        categorias = len(caso["auditoria"]["observadas"])
        filas = []
        for indice in range(categorias):
            inferior = f"{indice}/{categorias}"
            superior = f"{indice + 1}/{categorias}"
            cierre = "]" if indice == categorias - 1 else ")"
            filas.append([
                celda_dada(f"[{inferior}, {superior}{cierre}"),
                celda_dada(caso["auditoria"]["esperadas"][indice]),
                celda_editable(
                    f"FO{indice}", f"FO{indice}",
                    caso["auditoria"]["observadas"][indice], "entero",
                ),
            ])
        agregar_seccion("frecuencias", "Frecuencias por intervalo",
                        ["Intervalo", "FEᵢ", "FOᵢ"], filas)
        for clave in ("chi0", "critico_tabla", "veredicto"):
            agregar_pie(clave)
    elif numero == 6:
        resultado = caso["auditoria"]
        filas = []
        for indice in range(4):
            filas.append([
                celda_dada("≥3" if indice == 3 else indice),
                celda_editable(
                    f"FO{indice}", f"FO{indice}",
                    resultado["observadas"][indice], "entero",
                ),
                celda_editable(
                    f"FE{indice}", f"FE{indice}",
                    resultado["esperadas"][indice],
                ),
            ])
        agregar_seccion("distancias", "Distancias entre dígitos repetidos",
                        ["i", "FOi", "FEi"], filas)
        if "valores_R" in caso["auditoria"]:
            grupos_valores = {
                hueco: [f"{valor:.5f}" for valor, distancia in zip(
                    caso["auditoria"]["valores_R"], resultado["huecos"]
                ) if distancia == hueco]
                for hueco in range(4)
            }
            valores_filas = [
                [celda_dada(f"Distancia {hueco}"), celda_dada(", ".join(valores))]
                for hueco, valores in grupos_valores.items()
            ]
            titulo_muestra = "Números agrupados por primera repetición"
            encabezados_muestra = ["Distancia", "Números"]
        else:
            valores_filas = [[
                celda_dada(", ".join(map(str, caso["auditoria"]["digitos"]))),
            ]]
            titulo_muestra = "Secuencia de dígitos"
            encabezados_muestra = ["Dígitos"]
        agregar_seccion(
            "muestra_distancias", titulo_muestra, encabezados_muestra, valores_filas,
        )
        for clave in ("chi0", "critico_tabla", "veredicto"):
            agregar_pie(clave)
    elif numero == 7:
        matriz = caso["auditoria"]["observadas_matriz"]
        filas = []
        etiquetas = ["Inf-Izq", "Sup-Izq", "Inf-Der", "Sup-Der"]
        for indice, etiqueta in enumerate(etiquetas):
            fila, columna = divmod(indice, 2)
            filas.append([
                celda_dada(etiqueta),
                celda_editable(
                    f"FO{indice}", f"FO {etiqueta}", matriz[fila][columna], "entero",
                ),
                celda_dada(caso["auditoria"]["FE_por_celda"]),
            ])
        agregar_seccion("series", "Conteos de parejas por cuadrante",
                        ["Cuadrante", "FO", "FE"], filas, visual="cuadrantes")
        for clave in ("FE_pareja", "chi0", "critico_tabla", "veredicto"):
            agregar_pie(clave)
    elif numero == 8:
        auditoria = caso["auditoria"]
        filas = []
        for indice, categoria in enumerate(auditoria["categorias"]):
            filas.append([
                celda_dada({
                    "Todos distintos": "TD", "Un par": "1P", "Dos pares": "2P",
                    "Tercia": "T", "Full": "F", "Póker": "P", "Quintilla": "Q",
                }.get(categoria, categoria)),
                celda_editable(
                    f"FO{indice}", f"FO {categoria}", auditoria["observadas"][indice],
                    "entero",
                ),
                celda_editable(
                    f"FEp{indice}", f"FE {categoria}",
                    auditoria["esperadas"][indice],
                ),
            ])
        agregar_seccion("poker", "Clasificación de manos de Póker",
                        ["Mano", "FO", "FE"], filas)
        agregar_seccion(
            "poker_agrupacion", "Agrupación para χ² (gl = 1)",
            ["Grupo", "FO", "FE"],
            [
                [celda_dada(grupo["categoria"]), celda_dada(grupo["FO"]),
                 celda_dada(f'{grupo["FE"]:.4f}')]
                for grupo in auditoria["grupos"]
            ],
        )
        for clave in ("chi0", "critico_tabla", "veredicto"):
            agregar_pie(clave)
    elif numero in (9, 10, 11):
        valores = caso["auditoria"]["valores_R"]
        if numero == 9:
            id_col, etiqueta_col = "T", "T_Aᵢ"
            resultados = caso["auditoria"]["tiempos"]
            resumen = ("total", "promedio")
        else:
            id_col, etiqueta_col = "X", "Xᵢ"
            resultados = [caso["esperado"][f"X{i}"] for i in range(1, 5)]
            resumen = ()
        filas = []
        for indice, valor in enumerate(valores, 1):
            celdas = [
                celda_dada(indice), celda_dada(f"{valor:.5f}"),
            ]
            if numero == 11:
                celdas.append(celda_dada("√(2R)" if valor <= 0.5 else "2R"))
            celdas.append(celda_editable(
                f"{id_col}{indice}", f"{etiqueta_col}{indice}",
                resultados[indice - 1],
            ))
            filas.append(celdas)
        columnas = ["Cliente" if numero == 9 else "Elemento",
                    "Rᵢ"] + (["Regla aplicada"] if numero == 11 else []) + [etiqueta_col]
        agregar_seccion("transformacion", "Transformada inversa", columnas, filas)
        if numero == 9:
            for clave in resumen:
                agregar_pie(clave)
    elif numero == 12:
        auditoria = caso["auditoria"]
        poisson = list(auditoria["tabla_completa"])
        fila_final = poisson[-1]
        x_siguiente = fila_final["x"] + 1
        f_siguiente = fila_final["f"] * auditoria["lambda"] / x_siguiente
        poisson.append({
            "x": x_siguiente, "f": f_siguiente,
            "F": fila_final["F"] + f_siguiente,
        })
        filas_poisson = []
        for indice, fila in enumerate(poisson):
            filas_poisson.append([
                celda_dada(fila["x"]),
                celda_editable(f"pois_f{indice}", f"f({indice})", fila["f"]),
                celda_editable(f"pois_F{indice}", f"F({indice})", fila["F"]),
            ])
        agregar_seccion(
            "poisson", "Tabla de probabilidad acumulada",
            ["x", "f(x)", "F(x)"], filas_poisson,
            dinamica=True, iniciales=3, paro=len(auditoria["tabla_completa"]),
            mensaje_faltan=(
                "La tabla de Poisson aún no alcanza F(x)≥0.9999; agrega más filas"
            ),
            maximo=(
                len(filas_poisson) if caso["modo_ejecucion"] == "OFICIAL_PDF"
                else min(len(filas_poisson), 16)
            ),
        )
        valores = auditoria["valores_R"]
        filas_mapeo = [
            [
                celda_dada(indice + 1), celda_dada(f"{valor:.5f}"),
                celda_editable(
                    f"X{indice + 1}", f"X{indice + 1}", auditoria["mapeo"][indice],
                    "entero",
                ),
            ]
            for indice, valor in enumerate(valores)
        ]
        agregar_seccion("mapeo", "Transformada inversa discreta",
                        ["i", "Rᵢ", "Xᵢ"], filas_mapeo)
    elif numero == 13:
        filas = []
        for indice, fila in enumerate(caso["auditoria"]["filas"], 1):
            valores = list(fila.values())
            if indice >= len(caso["auditoria"]["filas"]) - 2:
                editables = {
                    "Hora inicio servicio", "Hora fin servicio",
                    "Tiempo espera en sistema", "Tiempo servidor inactivo",
                }
                celdas = []
                for columna, (clave, valor) in enumerate(fila.items()):
                    if clave in editables:
                        campo = f"c13_{indice}_{columna}"
                        celdas.append(celda_editable(campo, clave, valor))
                    else:
                        celdas.append(celda_dada(round(valor, 3) if isinstance(valor, float) else valor))
            else:
                celdas = [
                    celda_dada(round(valor, 3) if isinstance(valor, float) else valor)
                    for valor in valores
                ]
            filas.append(celdas)
        agregar_seccion(
            "cola", "Eventos de la cola de un canal",
            list(caso["auditoria"]["filas"][0].keys()), filas,
        )
        for clave in ("promedio", "inactividad"):
            agregar_pie(clave)
    else:
        filas = []
        corrida_indice = 0
        for numero_corrida, corrida in enumerate(caso["auditoria"]["corridas"], 1):
            for jugada in corrida["jugadas"]:
                corrida_indice += 1
                ganada = jugada["resultado"] == "Gana"
                estado = (
                    "Meta" if jugada["saldo"] >= caso["auditoria"]["meta"]
                    else "Quiebra" if jugada["saldo"] <= 0 else "Continúa"
                )
                filas.append([
                    celda_dada(numero_corrida),
                    celda_editable(f"antes{corrida_indice}", "Cant. antes",
                                   jugada["saldo"] - jugada["apuesta"] if ganada
                                   else jugada["saldo"] + jugada["apuesta"]),
                    celda_editable(f"apuesta{corrida_indice}", "Apuesta", jugada["apuesta"]),
                    celda_dada(f'{jugada["R"]:.5f}'),
                    celda_editable(
                        f"gana{corrida_indice}", "¿Se ganó?", "Sí" if ganada else "No",
                        "selector", ["Sí", "No"],
                    ),
                    celda_editable(f"despues{corrida_indice}", "Cant. después", jugada["saldo"]),
                    celda_editable(
                        f"estado{corrida_indice}", "Estado", estado, "selector",
                        ["Meta", "Quiebra", "Continúa"],
                    ),
                ])
        agregar_seccion(
            "volados", "Jugadas de las corridas",
            ["# Corrida", "Cant. antes", "Apuesta", "# Aleatorio",
             "¿Se ganó?", "Cant. después", "Estado"], filas,
            dinamica=True, iniciales=min(3, len(filas)), paro=len(filas),
            mensaje_faltan="Aún quedan jugadas por completar; agrega más filas",
        )
        agregar_pie("probabilidad")

    caso["campos"] = campos
    caso["tabla_interactiva"] = {
        "secciones": secciones, "pie": pie, "campos": campos,
    }


def _muestra_uniforme_balanceada(rng: random.Random, n: int) -> list[float]:
    valores = [(indice + rng.random()) / n for indice in range(n)]
    rng.shuffle(valores)
    return valores

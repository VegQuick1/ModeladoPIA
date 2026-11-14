import unittest
import json
from fractions import Fraction

import casos_narrativa
import motores_generadores as generadores
import pruebas_estadisticas as estadisticas
import sistemas_aplicados as sistemas
import variables_no_uniformes as variables
from main import (
    PENALIZACION_SEGUNDOS,
    ajustar_cantidad_filas,
    _analisis_transitorio_estable,
    _extraer_resultados_pruebas,
    construir_documento_auditoria,
    estado_reloj,
)


class TemporizadorTests(unittest.TestCase):
    def test_todos_los_capitulos_tienen_600_segundos(self):
        self.assertEqual(casos_narrativa.DURACION_CAPITULO, 600)
        for numero in range(1, 15):
            with self.subTest(capitulo=numero):
                self.assertEqual(casos_narrativa.crear_caso(numero, numero)["duracion"], 600)

    def test_colores_y_penalizacion_en_los_limites(self):
        self.assertEqual(estado_reloj(181), "verde")
        self.assertEqual(estado_reloj(180), "amarillo")
        self.assertEqual(estado_reloj(61), "amarillo")
        self.assertEqual(estado_reloj(60), "rojo")
        self.assertEqual(estado_reloj(0), "rojo")
        self.assertEqual(PENALIZACION_SEGUNDOS, 25)


class GeneradoresTests(unittest.TestCase):
    def test_periodo_completo_mixto_y_secuencia(self):
        self.assertTrue(generadores.periodo_completo_mixto(601, 137, 1000))
        filas = generadores.congruencial_mixto(7, 21, 13, 100, 2)
        self.assertEqual([fila["X"] for fila in filas], [60, 73])
        self.assertEqual([fila["R"] for fila in filas], ["60/100", "73/100"])
        self.assertEqual(generadores.periodo_observado_mixto(7, 7, 7, 10), 4)
        self.assertEqual(generadores.periodo_observado_multiplicativo(5, 5, 32), 8)
        self.assertTrue(generadores.periodo_completo_multiplicativo(5, 32))

    def test_generador_multiplicativo(self):
        filas = generadores.congruencial_multiplicativo(1, 999, 1009, 5)
        self.assertEqual(len(filas), 5)
        self.assertTrue(all(
            Fraction(fila["R"]) == Fraction(fila["X"], 1009) for fila in filas
        ))
        self.assertTrue(all(
            fila["R"] == f'{fila["X"]}/1009' for fila in filas
        ))


class PruebasEstadisticasTests(unittest.TestCase):
    def test_promedios_y_ks(self):
        valores = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
        self.assertAlmostEqual(estadisticas.prueba_promedios(valores)["media"], 0.5)
        ks = estadisticas.prueba_ks(valores)
        self.assertAlmostEqual(ks["dn"], 0.05)
        self.assertLessEqual(ks["dn"], ks["critico"])
        self.assertAlmostEqual(estadisticas.prueba_ks([0.1] * 10)["critico"], 0.409)

    def test_agrupa_categorias_con_fe_minima(self):
        grupos = estadisticas.agrupar_categorias(
            [1, 1, 1, 1], [2, 2, 2, 2], ["a", "b", "c", "d"],
        )
        self.assertTrue(all(grupo["FE"] >= 5 for grupo in grupos))
        self.assertEqual(sum(grupo["FO"] for grupo in grupos), 4)

    def test_distancias_agrupa_y_calcula_gl(self):
        resultado = estadisticas.prueba_distancias([1, 2, 1, 3, 1, 2, 3] * 30)
        self.assertGreaterEqual(resultado["n_huecos"], 5)
        self.assertTrue(all(grupo["FE"] >= 5 for grupo in resultado["grupos"]))
        self.assertEqual(resultado["gl"], len(resultado["grupos"]) - 1)

    def test_series_y_poker(self):
        valores = [((i * 37) % 1000) / 1000 for i in range(200)]
        series = estadisticas.prueba_series(valores, 2)
        self.assertEqual(sum(map(sum, series["observadas_matriz"])), 199)
        poker = estadisticas.prueba_poker([(i + 0.5) / 1000 for i in range(1000)])
        self.assertEqual(poker["observadas"], [10, 270, 720])

    def test_pruebas_oficiales_de_distancias_series_y_poker(self):
        serie = [
            0.03991, 0.38555, 0.17546, 0.32643, 0.69572,
            0.24122, 0.61196, 0.30532, 0.03788, 0.48228,
        ]
        distancias = estadisticas.prueba_distancias_decimales([
            0.03315, 0.01422, 0.43031, 0.05452, 0.71407,
            0.01189, 0.33096, 0.90593, 0.86316, 0.50452,
        ])
        self.assertEqual(distancias["observadas"], [4, 2, 3, 1])
        self.assertEqual(
            [(grupo["FO"], round(grupo["FE"], 2)) for grupo in distancias["grupos"]],
            [(9, 2.71), (1, 7.29)],
        )
        self.assertAlmostEqual(distancias["chi0"], 20.026473, places=6)

        prueba_series = estadisticas.prueba_series(serie, 2, agrupar=False)
        self.assertEqual(prueba_series["observadas_matriz"], [[5, 2], [2, 0]])
        self.assertAlmostEqual(prueba_series["chi0"], 5.666667, places=6)

        poker = estadisticas.prueba_poker([
            0.69910, 0.85385, 0.89889, 0.00024, 0.73827,
            0.33468, 0.11970, 0.96178, 0.63121, 0.62167,
        ], decimales=5)
        self.assertEqual(poker["observadas"], [1, 6, 1, 1, 1, 0, 0])
        self.assertEqual(poker["probabilidades"], [
            0.30240, 0.50400, 0.10800, 0.07200, 0.00900, 0.00450, 0.00010,
        ])
        self.assertAlmostEqual(poker["chi0"], 0.3528604, places=6)
        self.assertAlmostEqual(poker["grupos"][1]["FE"], 4.914)


class TransformacionesYSistemasTests(unittest.TestCase):
    def test_exponencial_uniforme_empirica_y_poisson(self):
        expo = variables.exponencial([0.5, 0.25], 0.5)
        self.assertAlmostEqual(expo["tiempos"][0], 2 * 0.69314718056)
        self.assertAlmostEqual(expo["total"], sum(expo["tiempos"]))
        self.assertEqual(variables.uniforme([0, 0.5, 1], 2, 6), [2, 4, 6])
        self.assertEqual(variables.empirica([0.5, 0.75]), [1, 1.5])
        tabla = variables.tabla_poisson(3.2)
        self.assertGreaterEqual(tabla[-1]["F"], 0.9999)
        self.assertEqual(variables.poisson_inversa([0.2], 3.2)["valores"], [2])

    def test_transformaciones_oficiales_del_ordinario(self):
        valores = [0.76971, 0.82534, 0.63249, 0.11073]
        exponencial = variables.exponencial(valores, 3)
        for calculado, esperado in zip(
            exponencial["tiempos"], [0.08724715, 0.06398662, 0.15269696, 0.73355349],
        ):
            self.assertAlmostEqual(calculado, esperado, places=7)
        self.assertAlmostEqual(exponencial["total"], 1.03748422, places=7)
        self.assertAlmostEqual(exponencial["promedio"], 0.25937105, places=7)
        self.assertEqual(
            variables.uniforme(valores, 2, 4),
            [3.53942, 3.65068, 3.26498, 2.22146],
        )
        self.assertEqual(
            variables.empirica(valores),
            [1.53942, 1.65068, 1.26498, 0.4705953675930098],
        )
        poisson = variables.poisson_inversa(valores, 5)
        self.assertEqual(poisson["valores"], [7, 7, 6, 2])
        self.assertEqual(poisson["tabla"][-1]["x"], 15)
        self.assertAlmostEqual(poisson["tabla"][-1]["F"], 0.999931, places=6)

    def test_martingala_y_cola(self):
        corrida = sistemas.simular_volados([0.9, 0.9], 30, 20, 50)
        self.assertEqual(corrida["jugadas"][-1]["apuesta"], 10)
        self.assertTrue(corrida["quiebra"])
        self.assertTrue(corrida["completa"])
        parcial = sistemas.simular_volados([0.9], 40, 20, 90)
        self.assertFalse(parcial["completa"])
        cola = sistemas.simular_cola([0, 0], [0, 0], 2, 5, 1, 4)
        self.assertEqual(cola["filas"][0]["Hora llegada"], 2)
        self.assertEqual(cola["porcentaje_inactivo"], 60)
        oficial = sistemas.simular_cola_tiempos(
            casos_narrativa.CASOS_OFICIALES_PDF[13]["tiempos_llegada"],
            casos_narrativa.CASOS_OFICIALES_PDF[13]["tiempos_servicio"],
        )
        self.assertAlmostEqual(oficial["promedio_sistema"], 3.6)
        self.assertAlmostEqual(oficial["porcentaje_inactivo"], 39.2857142857)


class CasosTests(unittest.TestCase):
    def test_catorce_capitulos_generan_y_validan_campos_individuales(self):
        for numero in range(1, 15):
            with self.subTest(capitulo=numero):
                caso = casos_narrativa.crear_caso(numero, semilla=8100 + numero)
                self.assertEqual(caso["numero"], numero)
                self.assertTrue(caso["tabla"])
                self.assertTrue(caso["campos"])
                entrada = {}
                for campo in caso["campos"]:
                    esperado = caso["esperado"][campo["id"]]
                    entrada[campo["id"]] = str(esperado)
                self.assertTrue(
                    casos_narrativa.validar_respuesta(caso, entrada)["correcto"],
                )

    def test_dinamico_y_oficial_cargan_los_catorce_capitulos(self):
        for modo in ("DINAMICO", "OFICIAL_PDF"):
            for numero in range(1, 15):
                with self.subTest(modo=modo, capitulo=numero):
                    caso = casos_narrativa.crear_caso(
                        numero, semilla=9000 + numero, modo_ejecucion=modo,
                    )
                    self.assertEqual(caso["modo_ejecucion"], modo)
                    self.assertTrue(caso["tabla"])
                    self.assertEqual(caso["duracion"], 600)
                    respuestas = {
                        campo["id"]: str(caso["esperado"][campo["id"]])
                        for campo in caso["campos"]
                    }
                    self.assertTrue(
                        casos_narrativa.validar_respuesta(caso, respuestas)["correcto"],
                    )
                    for seccion in caso["tabla_interactiva"]["secciones"]:
                        if seccion["dinamica"] and numero in (1, 2, 12):
                            self.assertGreaterEqual(seccion["filas_paro"], 4)
                            self.assertLessEqual(seccion["filas_paro"], 16)

    def test_tablas_interactivas_y_condiciones_de_paro(self):
        for numero, filas_paro in ((1, 6), (2, 16)):
            caso = casos_narrativa.crear_caso(numero, 77, "OFICIAL_PDF")
            seccion = caso["tabla_interactiva"]["secciones"][0]
            self.assertTrue(seccion["dinamica"])
            self.assertEqual(seccion["filas_iniciales"], 3)
            self.assertEqual(seccion["filas_paro"], filas_paro)
            self.assertEqual(seccion["max_filas"], filas_paro + 1)
            self.assertEqual(
                [len(fila) for fila in seccion["filas"]], [4] * (filas_paro + 1),
            )
            self.assertTrue(all(
                "campo" in celda for fila in seccion["filas"] for celda in fila
            ))
        cola = casos_narrativa.crear_caso(13, 77, "OFICIAL_PDF")
        filas_cola = cola["tabla_interactiva"]["secciones"][0]["filas"]
        self.assertEqual(sum("campo" in celda for celda in filas_cola[-1]), 4)
        poisson = casos_narrativa.crear_caso(12, 77, "OFICIAL_PDF")
        self.assertTrue(poisson["tabla_interactiva"]["secciones"][0]["dinamica"])
        volados = casos_narrativa.crear_caso(14, 77, "OFICIAL_PDF")
        seccion_volados = volados["tabla_interactiva"]["secciones"][0]
        self.assertTrue(seccion_volados["dinamica"])
        self.assertEqual(seccion_volados["filas_iniciales"], 3)
        self.assertEqual(seccion_volados["filas_paro"], 10)
        self.assertEqual(ajustar_cantidad_filas(3, 1, 10), 4)
        self.assertEqual(ajustar_cantidad_filas(3, -1, 10), 2)
        self.assertEqual(ajustar_cantidad_filas(10, 1, 10), 10)
        self.assertEqual(ajustar_cantidad_filas(1, -1, 10), 1)

        caso = casos_narrativa.crear_caso(1, 77, "OFICIAL_PDF")
        respuesta = {
            campo["id"]: str(caso["esperado"][campo["id"]])
            for campo in caso["campos"]
        }
        incompleto = casos_narrativa.validar_respuesta(
            caso, respuesta, filas_dinamicas={"iteraciones": 3},
        )
        self.assertFalse(incompleto["correcto"])
        self.assertIn("agrega más filas", incompleto["diagnostico"])
        excedido = casos_narrativa.validar_respuesta(
            caso, respuesta, filas_dinamicas={"iteraciones": 7},
        )
        self.assertFalse(excedido["correcto"])
        self.assertIn("fila 6", excedido["diagnostico"])

    def test_preset_oficial_calcula_respuestas_de_los_pdf(self):
        casos = {
            numero: casos_narrativa.crear_caso(numero, 77, "OFICIAL_PDF")
            for numero in range(1, 15)
        }
        self.assertEqual(
            [casos[1]["esperado"][f"Xnext{i}"] for i in range(1, 7)],
            [27, 23, 15, 63, 31, 31],
        )
        self.assertEqual(
            [casos[1]["esperado"][f"R{i}"] for i in range(1, 7)],
            ["27/64", "23/64", "15/64", "63/64", "31/64", "31/64"],
        )
        self.assertEqual(casos[1]["esperado"]["periodo"], "Rechazados")
        self.assertEqual(casos[1]["auditoria"]["iteraciones_hasta_paro"], 6)
        self.assertEqual(
            [casos[2]["esperado"][f"Xnext{i}"] for i in range(1, 17)],
            [35, 47, 43, 23, 51, 63, 59, 39, 3, 15, 11, 55, 19, 31, 27, 7],
        )
        self.assertEqual(
            [casos[2]["esperado"][f"R{i}"] for i in range(1, 17)],
            ["35/64", "47/64", "43/64", "23/64", "51/64", "63/64",
             "59/64", "39/64", "3/64", "15/64", "11/64", "55/64",
             "19/64", "31/64", "27/64", "7/64"],
        )
        self.assertEqual(casos[2]["esperado"]["periodo"], "Aceptados")
        self.assertEqual(casos[2]["auditoria"]["iteraciones_hasta_paro"], 16)

        base_medio = [
            0.03991, 0.38555, 0.17546, 0.32643, 0.69572,
            0.24122, 0.61196, 0.30532, 0.03788, 0.48228,
        ]
        self.assertEqual(casos[3]["auditoria"]["valores_R"], base_medio)
        self.assertEqual(casos[5]["auditoria"]["valores_R"], base_medio)
        self.assertEqual(casos[7]["auditoria"]["valores_R"], base_medio)
        self.assertEqual(casos[4]["auditoria"]["valores_R"], [
            0.03991, 0.17546, 0.69572, 0.61196, 0.03788,
            0.38555, 0.32643, 0.24122, 0.30532, 0.48228,
        ])
        self.assertEqual(casos[6]["auditoria"]["valores_R"], [
            0.03315, 0.01422, 0.43031, 0.05452, 0.71407,
            0.01189, 0.33096, 0.90593, 0.86316, 0.50452,
        ])
        self.assertEqual(casos[8]["auditoria"]["valores_R"], [
            0.69910, 0.85385, 0.89889, 0.00024, 0.73827,
            0.33468, 0.11970, 0.96178, 0.63121, 0.62167,
        ])
        self.assertAlmostEqual(casos[3]["esperado"]["media"], 0.330173)
        self.assertAlmostEqual(casos[3]["esperado"]["z0"], 1.860362, places=6)
        self.assertEqual(casos[3]["esperado"]["veredicto"], "Acepta H₀")
        self.assertAlmostEqual(casos[4]["esperado"]["dn"], 0.31772)
        self.assertEqual(casos[4]["auditoria"]["critico"], 0.409)
        self.assertEqual(casos[4]["esperado"]["veredicto"], "Acepta H₀")
        self.assertEqual(casos[5]["auditoria"]["observadas"], [4, 4, 2, 0])
        self.assertEqual(casos[5]["auditoria"]["esperadas"], [2.5] * 4)
        self.assertAlmostEqual(casos[5]["esperado"]["chi0"], 4.4)
        self.assertEqual(casos[5]["auditoria"]["gl"], 3)
        self.assertEqual(casos[5]["esperado"]["veredicto"], "Acepta H₀")
        self.assertEqual(casos[6]["auditoria"]["observadas"], [4, 2, 3, 1])
        self.assertAlmostEqual(casos[6]["esperado"]["chi0"], 20.026473, places=6)
        self.assertEqual(casos[6]["auditoria"]["gl"], 1)
        self.assertEqual(casos[6]["esperado"]["veredicto"], "Rechaza H₀")
        self.assertEqual(casos[7]["auditoria"]["observadas_matriz"], [[5, 2], [2, 0]])
        self.assertAlmostEqual(casos[7]["esperado"]["chi0"], 5.666667, places=6)
        self.assertEqual(casos[7]["esperado"]["veredicto"], "Acepta H₀")
        self.assertEqual(casos[8]["auditoria"]["observadas"], [1, 6, 1, 1, 1, 0, 0])
        self.assertEqual(casos[8]["auditoria"]["grupos"][0]["FO"], 6)
        self.assertAlmostEqual(casos[8]["auditoria"]["grupos"][1]["FE"], 4.914)
        self.assertAlmostEqual(casos[8]["esperado"]["chi0"], 0.3528604, places=6)
        self.assertEqual(casos[8]["esperado"]["veredicto"], "Acepta H₀")

        cajero = casos[9]["esperado"]
        self.assertEqual(casos[9]["auditoria"]["valores_R"], [
            0.76971, 0.82534, 0.63249, 0.11073,
        ])
        self.assertEqual(casos[10]["auditoria"]["valores_R"], casos[9]["auditoria"]["valores_R"])
        self.assertEqual(casos[11]["auditoria"]["valores_R"], casos[9]["auditoria"]["valores_R"])
        self.assertEqual(casos[12]["auditoria"]["valores_R"], casos[9]["auditoria"]["valores_R"])
        self.assertEqual(casos[9]["tabla"][1][1], "0.76971")
        self.assertEqual(casos[10]["tabla"][1][1], "0.76971")
        self.assertEqual(casos[11]["tabla"][1][1], "0.76971")
        self.assertIn("0.76971", casos[12]["narrativa"])
        self.assertAlmostEqual(cajero["total"], 1.037484217, places=8)
        self.assertAlmostEqual(cajero["promedio"], 0.259371054, places=8)
        self.assertAlmostEqual(casos[9]["esperado"]["T1"], 0.0872471528, places=8)
        self.assertEqual(
            [casos[10]["esperado"][f"X{i}"] for i in range(1, 5)],
            [3.53942, 3.65068, 3.26498, 2.22146],
        )
        self.assertAlmostEqual(casos[11]["esperado"]["X4"], 0.4705953676)
        self.assertEqual(
            [casos[12]["esperado"][f"X{i}"] for i in range(1, 5)],
            [7, 7, 6, 2],
        )
        self.assertEqual(casos[12]["auditoria"]["tabla_completa"][-1]["x"], 15)
        self.assertAlmostEqual(casos[12]["auditoria"]["tabla_completa"][-1]["F"], 0.999931, places=6)
        self.assertAlmostEqual(casos[13]["esperado"]["promedio"], 3.60)
        self.assertAlmostEqual(casos[13]["esperado"]["inactividad"], 39.2857142857)
        self.assertEqual(
            casos[13]["auditoria"]["tiempos_llegada"],
            [9, 2, 6, 8, 6, 9, 4, 3, 5, 5, 5, 10, 2, 2, 4, 8, 8, 3, 6, 3],
        )
        self.assertEqual(
            casos[13]["auditoria"]["tiempos_servicio"],
            [3, 2, 4, 6, 4, 4, 3, 3, 4, 4, 6, 3, 1, 4, 3, 2, 2, 3, 5, 2],
        )
        self.assertEqual(casos[14]["auditoria"]["R_suministrados"], [
            0.03991, 0.38555, 0.17546, 0.32843, 0.69572,
            0.24122, 0.61196, 0.88722, 0.65961, 0.03788,
        ])
        self.assertAlmostEqual(casos[14]["esperado"]["probabilidad"], 2 / 3)
        self.assertEqual(len(casos[14]["auditoria"]["corridas"]), 4)
        self.assertEqual(casos[14]["auditoria"]["exitos"], 2)
        self.assertEqual(casos[14]["auditoria"]["corridas_completas"], 3)
        self.assertEqual(casos[14]["auditoria"]["corridas_inconclusas"], 1)
        self.assertEqual(casos[14]["auditoria"]["numeros_no_utilizados"], 0)
        self.assertEqual(casos[14]["auditoria"]["tiradas_utilizadas"], 2)
        self.assertEqual(
            casos[14]["auditoria"]["tiradas_utilizadas_por_corrida"], [2, 2, 4, 2],
        )
        self.assertEqual(len(casos[12]["tabla"]), 17)

    def test_auditoria_incluye_modo_y_origen_en_ambos_modos(self):
        for modo in ("DINAMICO", "OFICIAL_PDF"):
            caso = casos_narrativa.crear_caso(10, 123, modo)
            informe = construir_documento_auditoria(caso)
            self.assertEqual(informe["modo_ejecucion"], modo)
            self.assertTrue(informe["origen_problema"])
            self.assertEqual(informe["solucion"], caso["esperado"])

    def test_semillas_reproducibles_y_auditorias_exportables(self):
        for numero in range(1, 15):
            caso = casos_narrativa.crear_caso(numero, semilla=4500 + numero)
            repetido = casos_narrativa.crear_caso(numero, semilla=4500 + numero)
            self.assertEqual(caso["tabla"], repetido["tabla"])
            informe = {
                "capitulo": numero,
                "auditoria": caso["auditoria"],
                "transitorio_vs_estable": _analisis_transitorio_estable(caso),
                "resultados_pruebas": _extraer_resultados_pruebas(caso["auditoria"]),
            }
            json.dumps(informe, ensure_ascii=False)

    def test_tablas_estadisticas_no_revelan_veredicto(self):
        for numero in range(3, 9):
            caso = casos_narrativa.crear_caso(numero, semilla=1900 + numero)
            encabezados = [str(valor).lower() for valor in caso["tabla"][0]]
            self.assertFalse(any("h0" in valor or "acepta" in valor or "rechaza" in valor
                                 for valor in encabezados))
            self.assertNotIn(caso["esperado"]["veredicto"], str(caso["tabla"]))

    def test_poker_muestra_agrupacion_de_tercia_con_fe_baja(self):
        caso = casos_narrativa.crear_caso(8, semilla=28)
        auditoria = caso["auditoria"]
        self.assertLess(auditoria["esperadas"][0], 5)
        self.assertTrue(all(grupo["FE"] >= 5 for grupo in auditoria["grupos"]))
        self.assertEqual(auditoria["gl"], len(auditoria["grupos"]) - 1)

    def test_generadores_muestran_fracciones_y_condicion_de_paro(self):
        for numero in (1, 2):
            caso = casos_narrativa.crear_caso(numero, semilla=22, modo_ejecucion="OFICIAL_PDF")
            self.assertEqual(caso["tabla"][0], [
                "n", "Xₙ", "Xₙ₊₁", "# Rect (fracción con /)",
            ])
            filas = caso["auditoria"]["tabla_generada"]
            for indice, fila in enumerate(filas, 1):
                self.assertEqual(
                    fila["R"], f'{fila["Xnext"]}/{caso["auditoria"]["parametros"]["m"]}',
                )
                self.assertEqual(caso["esperado"][f"R{indice}"], fila["R"])
                self.assertIn("ej. 27/64", next(
                    campo["etiqueta"] for campo in caso["campos"]
                    if campo["id"] == f"R{indice}"
                ))
            entrada_correcta = {
                clave: str(valor) for clave, valor in caso["esperado"].items()
            }
            self.assertTrue(casos_narrativa.validar_respuesta(
                caso, entrada_correcta,
            )["correcto"])
            entrada_simplificada = entrada_correcta.copy()
            entrada_simplificada["R1"] = str(Fraction(filas[0]["R"]))
            self.assertTrue(casos_narrativa.validar_respuesta(
                caso, entrada_simplificada,
            )["correcto"])
            auditoria = construir_documento_auditoria(caso)
            self.assertEqual(auditoria["solucion"]["R1"], filas[0]["R"])
            self.assertEqual(
                auditoria["motor_y_resultados"]["tabla_generada"][0]["R"],
                filas[0]["R"],
            )
            self.assertIn(
                f'"R": "{filas[0]["R"]}"',
                json.dumps(auditoria, ensure_ascii=False),
            )

    def test_formato_fraccion_invalido_no_se_confunde_con_respuesta_numerica(self):
        caso = casos_narrativa.crear_caso(1, semilla=22)
        entrada = {clave: str(valor) for clave, valor in caso["esperado"].items()}
        entrada["R1"] = "27,64"
        resultado = casos_narrativa.validar_respuesta(caso, entrada)
        self.assertFalse(resultado["correcto"])
        self.assertEqual(resultado["formatos_invalidos"], ["R1"])
        self.assertIn("27/64", resultado["diagnostico"])

    def test_porcentaje_y_probabilidad_admiten_fracciones_o_porcentajes(self):
        probabilidad = casos_narrativa.crear_caso(14, semilla=314)
        p = probabilidad["esperado"]["probabilidad"]
        self.assertTrue(casos_narrativa.validar_respuesta(
            probabilidad, {"probabilidad": f"{p * 100:.2f}%"},
        )["correcto"])
        self.assertTrue(casos_narrativa.validar_respuesta(
            probabilidad, {"probabilidad": str(p)},
        )["correcto"])
        cola = casos_narrativa.crear_caso(13, semilla=313)
        inactividad = cola["esperado"]["inactividad"]
        self.assertTrue(casos_narrativa.validar_respuesta(
            cola, {"promedio": str(cola["esperado"]["promedio"]),
                   "inactividad": str(inactividad / 100)},
        )["correcto"])

    def test_decimal_con_coma(self):
        caso = casos_narrativa.crear_caso(3, semilla=3)
        entrada = {
            "media": f'{caso["esperado"]["media"]:.4f}'.replace(".", ","),
            "z0": f'{caso["esperado"]["z0"]:.4f}'.replace(".", ","),
            "veredicto": caso["esperado"]["veredicto"],
        }
        self.assertTrue(casos_narrativa.validar_respuesta(caso, entrada)["correcto"])


if __name__ == "__main__":
    unittest.main()

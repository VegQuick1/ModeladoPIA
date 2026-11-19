import inspect
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import casos_narrativa
import motores_generadores as generadores
import pruebas_estadisticas as estadisticas
import main as modulo_main
import revision as modulo_revision
import sistemas_aplicados as sistemas
import variables_no_uniformes as variables
from revision import (
    _analisis_transitorio_estable,
    _extraer_resultados_pruebas,
    construir_documento_auditoria,
    construir_respuestas_exactas,
)
from main import (
    ExpedienteMontecarlo,
    PENALIZACION_SEGUNDOS,
    ajustar_cantidad_filas,
    crear_savegame,
    encabezado_transicion,
    estado_reloj,
    estado_nodo,
    hay_partida_guardada,
    leer_valores_entrada,
    minimo_segundos_humanos,
    modo_ejecucion_desde_juego,
    modo_juego_normalizado,
    narrativa_transicion,
    normalizar_savegame,
    resultado_final,
)


class TemporizadorTests(unittest.TestCase):
    def test_duracion_dinamica_de_capitulos(self):
        for numero in range(1, 15):
            with self.subTest(capitulo=numero):
                caso = casos_narrativa.crear_caso(numero, numero)
                self.assertEqual(
                    caso["duracion"], casos_narrativa.calcular_tiempo_capitulo(caso),
                )
                self.assertGreaterEqual(caso["duracion"], 240)
                self.assertLessEqual(caso["duracion"], 1080)

        corto = casos_narrativa.crear_caso(10, 10)
        extenso = casos_narrativa.crear_caso(2, 10, "OFICIAL_PDF")
        poisson = casos_narrativa.crear_caso(12, 10, "OFICIAL_PDF")
        inventario = casos_narrativa.crear_caso(13, 10, "OFICIAL_PDF")
        self.assertEqual(corto["duracion"], 328)
        self.assertGreater(extenso["duracion"], corto["duracion"])
        self.assertEqual(extenso["duracion"], 1080)
        self.assertGreater(poisson["duracion"], corto["duracion"])
        self.assertEqual(inventario["duracion"], 792)

    def test_colores_y_penalizacion_en_los_limites(self):
        self.assertEqual(estado_reloj(351, 1000), "verde")
        self.assertEqual(estado_reloj(350, 1000), "amarillo")
        self.assertEqual(estado_reloj(151, 1000), "amarillo")
        self.assertEqual(estado_reloj(150, 1000), "rojo")
        self.assertEqual(estado_reloj(0, 1000), "rojo")
        self.assertEqual(PENALIZACION_SEGUNDOS, 25)


class VerificacionEntornoTests(unittest.TestCase):
    class TkFalso:
        def withdraw(self):
            pass

        def update_idletasks(self):
            pass

        def winfo_screenwidth(self):
            return 1920

        def winfo_screenheight(self):
            return 1080

        def destroy(self):
            pass

    def test_preflight_carga_tk_assets_y_ruta_de_guardado_escribible(self):
        with patch("tkinter.Tk", return_value=self.TkFalso()):
            modulo_main.verificar_entorno_ejecucion()
        self.assertEqual(
            modulo_main.ARCHIVO_SAVEGAME,
            Path(modulo_main.__file__).resolve().with_name("savegame.json"),
        )

    def test_preflight_redirige_guardado_a_la_ruta_de_usuario_si_no_hay_permiso(self):
        guardado_original = modulo_main.ARCHIVO_SAVEGAME
        with tempfile.TemporaryDirectory() as directorio:
            with (
                patch.dict("os.environ", {"LOCALAPPDATA": directorio}),
                patch("tkinter.Tk", return_value=self.TkFalso()),
                patch("main._probar_escritura", side_effect=(False, True)),
                patch.object(modulo_main, "ARCHIVO_SAVEGAME", guardado_original),
            ):
                modulo_main.verificar_entorno_ejecucion()
                ruta_guardada = modulo_main.ARCHIVO_SAVEGAME
                if modulo_main.sys.platform == "darwin":
                    ruta_esperada = (
                        Path.home()
                        / "Library"
                        / "Application Support"
                        / "ExpedienteMontecarlo"
                        / "savegame.json"
                    )
                else:
                    ruta_esperada = (
                        Path(directorio) / "ExpedienteMontecarlo" / "savegame.json"
                    )
                self.assertEqual(
                    ruta_guardada,
                    ruta_esperada,
                )
                self.assertTrue(ruta_guardada.is_file())

    def test_savegame_progreso_y_umbral_antitrampa(self):
        guardado = crear_savegame("OFICIAL_PDF", "Detective Vance")
        self.assertEqual(guardado["modo"], "OFICIAL_PDF")
        self.assertEqual(guardado["alias"], "Detective Vance")
        self.assertEqual(guardado["capitulo_actual"], 1)
        self.assertEqual(estado_nodo(1, guardado), "○")
        self.assertEqual(estado_nodo(2, guardado), "🔒")

        guardado["estrellas"] = [1, 2]
        guardado["fallidos"] = [3]
        self.assertEqual(estado_nodo(3, guardado), "⚠")
        self.assertEqual(estado_nodo(4, guardado), "○")
        self.assertEqual(resultado_final(guardado), "incompleto")
        self.assertEqual(
            resultado_final({**guardado, "estrellas": list(range(1, 15))}),
            "bueno",
        )

        normalizado = normalizar_savegame({
            "modo": "modo-desconocido", "alias": "  Forense  ",
            "capitulo": 99, "estrellas": [1, 99, "2", True],
            "fallidos": [2, 2, 0],
        })
        self.assertEqual(normalizado["modo"], "DINAMICO")
        self.assertEqual(normalizado["alias"], "Forense")
        self.assertEqual(normalizado["capitulo"], 14)
        self.assertEqual(normalizado["capitulo_actual"], 14)
        self.assertEqual(normalizado["estrellas"], [1])
        self.assertEqual(normalizado["fallidos"], [2])
        self.assertEqual(
            normalizar_savegame({
                "capitulo": 3, "capitulo_actual": 8, "alias": "Detective",
            })["capitulo"],
            8,
        )

        caso_pequeno = casos_narrativa.crear_caso(3, 10)
        caso_grande = casos_narrativa.crear_caso(2, 10, "OFICIAL_PDF")
        self.assertEqual(
            minimo_segundos_humanos(caso_pequeno),
            max(12, len(caso_pequeno["campos"]) * 2),
        )
        self.assertEqual(
            minimo_segundos_humanos(caso_grande),
            max(12, len(caso_grande["campos"]) * 2),
        )


class TransicionesTests(unittest.TestCase):
    def test_pantalla_de_transicion_muestra_resultado_y_guarda(self):
        class WidgetFalso:
            def __init__(self):
                self.configuracion = {}
                self.mostrado = False

            def configure(self, **valores):
                self.configuracion.update(valores)

            def grid(self):
                self.mostrado = True

            def actualizar(self, *_argumentos):
                pass

        class AplicacionFalsa:
            def _ocultar_pantallas(self):
                pass

            def _guardar_progreso(self):
                self.guardados += 1
                self.capitulo_guardado = self.savegame.get("capitulo_actual")

            def _mostrar_menu(self):
                self.menu_mostrado = True

        app = AplicacionFalsa()
        app.investigacion_iniciada = True
        app.capitulo = 1
        app.completados = {1}
        app.savegame = {
            "resultado_actual": "limpio",
            "alias": "Detective Vance",
            "viaje_tiempo": False,
            "pendientes_rehacer": [],
        }
        app.guardados = 0
        app.boton_descanso_continuar = WidgetFalso()
        app.descanso_titulo = WidgetFalso()
        app.descanso_texto = WidgetFalso()
        app.descanso_frame = WidgetFalso()
        app.descanso_visual = WidgetFalso()

        ExpedienteMontecarlo._mostrar_descanso(app, "Nodo asegurado.")

        self.assertEqual(app.guardados, 1)
        self.assertEqual(app.capitulo_guardado, 2)
        self.assertEqual(app.savegame["capitulo"], 2)
        self.assertEqual(
            app.descanso_titulo.configuracion["text"],
            f"{encabezado_transicion('limpio')}\nESTRELLAS: 1 / 14",
        )
        self.assertEqual(
            app.boton_descanso_continuar.configuracion["text"],
            "Continuar al Capítulo 2",
        )
        self.assertTrue(app.descanso_frame.mostrado)
        self.assertIn("El primer cuaderno", app.descanso_texto.configuracion["text"])

        ExpedienteMontecarlo._guardar_y_volver_menu(app)
        self.assertEqual(app.guardados, 2)
        self.assertTrue(app.menu_mostrado)

        app.capitulo = 14
        app.savegame["resultado_actual"] = "tiempo_agotado"
        ExpedienteMontecarlo._mostrar_descanso(app, "Último nodo.")
        self.assertEqual(
            app.boton_descanso_continuar.configuracion["text"],
            "Evaluar estrellas",
        )
        self.assertIn(
            encabezado_transicion("tiempo_agotado"),
            app.descanso_titulo.configuracion["text"],
        )

    def test_narrativas_reaccionan_al_resultado_y_al_capitulo(self):
        self.assertNotEqual(
            narrativa_transicion(1, "limpio"),
            narrativa_transicion(2, "limpio"),
        )
        self.assertNotEqual(
            narrativa_transicion(1, "tiempo_agotado"),
            narrativa_transicion(2, "tiempo_agotado"),
        )
        self.assertIn("cadena de custodia", narrativa_transicion(1, "anti_trampa"))
        self.assertIn("REGISTRO COMPROMETIDO", encabezado_transicion("anti_trampa"))
        self.assertIn("TIEMPO AGOTADO", encabezado_transicion("tiempo_agotado"))

    def test_continuar_tras_agotar_tiempo_guarda_el_siguiente_capitulo(self):
        class AplicacionFalsa:
            def _cargar_caso_actual(self):
                self.savegame["capitulo"] = self.capitulo
                self._guardar_progreso()

            def _guardar_progreso(self):
                self.guardado = self.savegame["capitulo"]

            def _mostrar_interludio(self):
                self.interludio_mostrado = True

        app = AplicacionFalsa()
        app.capitulo = 1
        app.savegame = {
            "pendientes_rehacer": [],
            "viaje_tiempo": False,
            "resultado_actual": "tiempo_agotado",
        }

        ExpedienteMontecarlo._continuar_desde_descanso(app)

        self.assertEqual(app.capitulo, 2)
        self.assertEqual(app.guardado, 2)
        self.assertEqual(app.savegame["resultado_actual"], "")
        self.assertTrue(app.interludio_mostrado)

    def test_capitulo_14_continua_a_la_evaluacion_final(self):
        class AplicacionFalsa:
            def _guardar_progreso(self):
                self.guardado = dict(self.savegame)

            def _mostrar_final(self):
                self.final_mostrado = True

        app = AplicacionFalsa()
        app.capitulo = 14
        app.savegame = {
            "capitulo": 14,
            "pendientes_rehacer": [],
            "viaje_tiempo": False,
            "resultado_actual": "limpio",
        }

        ExpedienteMontecarlo._continuar_desde_descanso(app)

        self.assertEqual(app.guardado["capitulo"], 14)
        self.assertEqual(app.guardado["resultado_actual"], "")
        self.assertTrue(app.final_mostrado)

    def test_boton_de_tabla_completa_ausente(self):
        codigo = inspect.getsource(ExpedienteMontecarlo._crear_pestana_expediente)
        self.assertNotIn("Ver tabla completa / auditoría", codigo)

    def test_continuar_partida_guardada_omite_archivo_de_ingreso(self):
        class AplicacionFalsa:
            def _mostrar_interludio(self):
                self.briefing = True

            def _nuevo_juego(self, modo):
                self.archivo_ingreso = True

            def _continuar_investigacion(self):
                self.continuada = True

        app = AplicacionFalsa()
        app.savegame = {
            "alias": "Detective Vance",
            "activo": True,
            "modo": "OFICIAL_PDF",
            "modo_juego": "OFICIAL",
            "capitulo": 5,
            "capitulo_actual": 5,
            "estrellas": [1, 2, 3, 4],
            "fallidos": [],
        }

        self.assertTrue(hay_partida_guardada(app.savegame))
        ExpedienteMontecarlo._continuar_investigacion(app)
        self.assertEqual(app.capitulo, 5)
        self.assertEqual(app.caso["numero"], 5)
        self.assertTrue(app.briefing)
        self.assertFalse(hasattr(app, "archivo_ingreso"))

        ExpedienteMontecarlo._nuevo_juego(app, "DINAMICO")
        self.assertTrue(app.continuada)
        self.assertFalse(hasattr(app, "archivo_ingreso"))

    def test_capitulo_actual_avanza_para_cada_resultado_final(self):
        class WidgetFalso:
            def configure(self, **_valores):
                pass

            def grid(self):
                pass

            def actualizar(self, *_argumentos):
                pass

        class AplicacionFalsa:
            def _ocultar_pantallas(self):
                pass

            def _guardar_progreso(self):
                self.capitulo_guardado = self.savegame["capitulo_actual"]

        for resultado in ("limpio", "tiempo_agotado", "anti_trampa"):
            with self.subTest(resultado=resultado):
                app = AplicacionFalsa()
                app.capitulo = 7
                app.completados = {1, 2}
                app.investigacion_iniciada = True
                app.savegame = {
                    "resultado_actual": resultado,
                    "alias": "Detective Vance",
                    "viaje_tiempo": False,
                    "pendientes_rehacer": [],
                    "estrellas": [1, 2],
                }
                app.boton_descanso_continuar = WidgetFalso()
                app.descanso_titulo = WidgetFalso()
                app.descanso_texto = WidgetFalso()
                app.descanso_frame = WidgetFalso()
                app.descanso_visual = WidgetFalso()

                ExpedienteMontecarlo._mostrar_descanso(app, "Fin del nodo.")

                self.assertEqual(app.savegame["capitulo_actual"], 8)
                self.assertEqual(app.capitulo_guardado, 8)

    def test_guardar_progreso_persiste_el_capitulo_actual_canonico(self):
        class AplicacionFalsa:
            def _guardar_progreso(self):
                ExpedienteMontecarlo._guardar_progreso(self)

        app = AplicacionFalsa()
        app.capitulo = 7
        app.modo_ejecucion = "DINAMICO"
        app.completados = {7}
        app.capitulos_fallidos = set()
        app.savegame = {
            "capitulo": 7,
            "capitulo_actual": 8,
            "estrellas": [7],
            "fallidos": [],
        }
        with tempfile.TemporaryDirectory() as directorio:
            archivo = Path(directorio) / "savegame.json"
            with patch("main.ARCHIVO_SAVEGAME", archivo):
                app._guardar_progreso()
            guardado = json.loads(archivo.read_text(encoding="utf-8"))

        self.assertEqual(guardado["capitulo"], 8)
        self.assertEqual(guardado["capitulo_actual"], 8)

    def test_controles_de_navegacion_y_auditoria_solo_viven_en_revision(self):
        interfaz = inspect.getsource(ExpedienteMontecarlo._construir_interfaz)
        expediente = inspect.getsource(ExpedienteMontecarlo._crear_pestana_expediente)
        revision = inspect.getsource(modulo_revision._mostrar_respuestas_exactas)
        self.assertNotIn("CTkTabview", interfaz)
        self.assertNotIn("_crear_pestana_auditoria", interfaz)
        self.assertNotIn("← Anterior", expediente)
        self.assertNotIn("Siguiente →", expediente)
        self.assertNotIn("selector_capitulo", expediente)
        self.assertIn("Auditoría V&V", revision)
        self.assertIn("selector_revision", revision)


class ModoPartidaTests(unittest.TestCase):
    class WidgetFalso:
        def __init__(self):
            self.visible = True
            self.configuracion = {}

        def grid(self):
            self.visible = True

        def grid_remove(self):
            self.visible = False

        def configure(self, **valores):
            self.configuracion.update(valores)

    def test_modo_se_guarda_bloqueado_y_se_conserva_al_continuar(self):
        for modo in ("OFICIAL", "DINAMICO"):
            with self.subTest(modo=modo):
                guardado = crear_savegame(modo, "Detective Vance")
                guardado.update({"activo": True, "capitulo_actual": 6})
                guardado = normalizar_savegame(guardado)

                class AplicacionFalsa:
                    def _mostrar_interludio(self):
                        self.briefing = True

                    def _continuar_investigacion(self):
                        ExpedienteMontecarlo._continuar_investigacion(self)

                app = AplicacionFalsa()
                app.savegame = guardado
                ExpedienteMontecarlo._continuar_investigacion(app)

                self.assertEqual(app.savegame["modo_juego"], modo)
                self.assertEqual(
                    app.modo_ejecucion, modo_ejecucion_desde_juego(modo),
                )
                self.assertEqual(modo_juego_normalizado(app.modo_ejecucion), modo)
                self.assertEqual(app.capitulo, 6)
                self.assertTrue(app.briefing)
                otro_modo = "DINAMICO" if modo == "OFICIAL" else "OFICIAL"
                ExpedienteMontecarlo._nuevo_juego(app, otro_modo)
                self.assertEqual(app.modo_juego, modo)
                self.assertEqual(app.modo_ejecucion, modo_ejecucion_desde_juego(modo))

                app.botones_modo = self.WidgetFalso()
                app.modo_bloqueado_label = self.WidgetFalso()
                app.boton_continuar = self.WidgetFalso()
                ExpedienteMontecarlo._actualizar_estado_menu(app)
                self.assertFalse(app.botones_modo.visible)
                self.assertTrue(app.modo_bloqueado_label.visible)
                self.assertIn(
                    "MODO APUNTES" if modo == "OFICIAL" else "MODO DINÁMICO",
                    app.modo_bloqueado_label.configuracion["text"],
                )
                self.assertEqual(
                    app.boton_continuar.configuracion["text"],
                    "Continuar Investigación (Capítulo 06)",
                )

    def test_elegir_modo_nuevo_lo_guarda_y_abre_el_archivo_de_ingreso(self):
        class WidgetFalso:
            def __init__(self):
                self.visible = False
                self.valor = ""

            def set(self, valor):
                self.valor = valor

            def delete(self, *_argumentos):
                self.valor = ""

            def grid(self):
                self.visible = True

        class AplicacionFalsa:
            def _guardar_progreso(self):
                self.guardado = dict(self.savegame)

            def _ocultar_pantallas(self):
                pass

        app = AplicacionFalsa()
        app.savegame = crear_savegame()
        app.completados = set()
        app.capitulos_fallidos = set()
        app.alias_seleccionado = WidgetFalso()
        app.alias_personalizado = WidgetFalso()
        app.dialogo_frame = WidgetFalso()

        ExpedienteMontecarlo._nuevo_juego(app, "OFICIAL")

        self.assertEqual(app.guardado["modo_juego"], "OFICIAL")
        self.assertEqual(app.modo_ejecucion, "OFICIAL_PDF")
        self.assertFalse(app.guardado["activo"])
        self.assertTrue(app.dialogo_frame.visible)

    def test_sin_partida_se_muestran_las_dos_opciones_de_modo(self):
        app = type("AplicacionFalsa", (), {})()
        app.savegame = crear_savegame()
        app.botones_modo = self.WidgetFalso()
        app.modo_bloqueado_label = self.WidgetFalso()
        app.boton_continuar = self.WidgetFalso()

        ExpedienteMontecarlo._actualizar_estado_menu(app)

        self.assertTrue(app.botones_modo.visible)
        self.assertFalse(app.modo_bloqueado_label.visible)
        self.assertEqual(app.boton_continuar.configuracion["state"], "disabled")
        codigo = inspect.getsource(ExpedienteMontecarlo._construir_interfaz)
        self.assertIn("Nueva Investigación: Modo Apuntes (Oficial)", codigo)
        self.assertIn(
            "Nueva Investigación: Modo Dinámico (Semillas Aleatorias)", codigo,
        )

    def test_restablecer_elimina_el_guardado_y_desbloquea_modos(self):
        class AplicacionFalsa:
            def _renderizar_caso(self, reiniciar_reloj):
                self.reinicio_sin_reloj = not reiniciar_reloj

            def _actualizar_estado_menu(self):
                ExpedienteMontecarlo._actualizar_estado_menu(self)

            def _mostrar_menu(self):
                self.menu_mostrado = True
                self._actualizar_estado_menu()

        app = AplicacionFalsa()
        app.savegame = crear_savegame("OFICIAL", "Detective Vance")
        app.savegame["activo"] = True
        app.modo_ejecucion = "OFICIAL_PDF"
        app.modo_juego = "OFICIAL"
        app.capitulo = 4
        app.completados = {1, 2}
        app.capitulos_fallidos = {3}
        app.botones_modo = self.WidgetFalso()
        app.modo_bloqueado_label = self.WidgetFalso()
        app.boton_continuar = self.WidgetFalso()

        with tempfile.TemporaryDirectory() as directorio:
            archivo = Path(directorio) / "savegame.json"
            archivo.write_text('{"activo": true}', encoding="utf-8")
            with (
                patch("main.ARCHIVO_SAVEGAME", archivo),
                patch("main.messagebox.askyesno", return_value=True),
            ):
                ExpedienteMontecarlo._restablecer_progreso(app)

            self.assertFalse(archivo.exists())
            self.assertFalse(hay_partida_guardada(app.savegame))
            self.assertEqual(app.modo_juego, "DINAMICO")
            self.assertTrue(app.botones_modo.visible)
            self.assertFalse(app.modo_bloqueado_label.visible)
            self.assertEqual(app.boton_continuar.configuracion["state"], "disabled")
            self.assertTrue(app.menu_mostrado)


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
        oficial = sistemas.simular_cola_tiempos([2, 1], [1, 2])
        self.assertEqual(len(oficial["filas"]), 2)

    def test_inventario_calcula_recibos_faltantes_y_costos(self):
        resultado = sistemas.simular_inventario(
            [0.1, 0.2, 0.3, 0.4],
            [100, 120, 80, 90],
            [2, 1, 3, 1],
            inventario_inicial=150,
        )
        self.assertEqual(len(resultado["filas"]), 4)
        self.assertEqual(resultado["filas"][0]["Inventario final"], 50)
        self.assertEqual(resultado["filas"][1]["Faltante"], 70)
        self.assertEqual(
            resultado["costo_ordenar"], resultado["total_ordenes"] * 100,
        )
        self.assertEqual(
            resultado["costo_faltante"],
            sum(fila["Faltante"] for fila in resultado["filas"]) * 50,
        )


class CasosTests(unittest.TestCase):
    def test_introducciones_indican_metodo_y_tienen_dos_parrafos_detallados(self):
        for numero, metodo in casos_narrativa.METODOS_CAPITULO.items():
            with self.subTest(capitulo=numero):
                intro = casos_narrativa.crear_caso(numero, semilla=3200 + numero)[
                    "intro_narrativa"
                ]
                parrafos = [parrafo for parrafo in intro.split("\n\n") if parrafo]
                palabras = len(intro.split())
                self.assertIn(metodo, intro)
                self.assertEqual(len(parrafos), 2)
                self.assertGreaterEqual(palabras, 90)
                self.assertLessEqual(palabras, 140)

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
                    self.assertEqual(
                        caso["duracion"], casos_narrativa.calcular_tiempo_capitulo(caso),
                    )
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
                            if modo == "DINAMICO":
                                self.assertLessEqual(seccion["max_filas"], 16)

    def test_tablas_interactivas_y_condiciones_de_paro(self):
        for numero, filas_paro in ((1, 6), (2, 16)):
            caso = casos_narrativa.crear_caso(numero, 77, "OFICIAL_PDF")
            seccion = caso["tabla_interactiva"]["secciones"][0]
            self.assertTrue(seccion["dinamica"])
            self.assertEqual(seccion["filas_iniciales"], 3)
            self.assertEqual(seccion["filas_paro"], filas_paro)
            self.assertEqual(seccion["max_filas"], filas_paro + 1)
            self.assertEqual([len(fila) for fila in seccion["filas"]], [5] * (filas_paro + 1))
            self.assertTrue(all("campo" in celda for fila in seccion["filas"] for celda in fila))
        inventario = casos_narrativa.crear_caso(13, 77, "OFICIAL_PDF")
        filas_inventario = inventario["tabla_interactiva"]["secciones"][0]["filas"]
        self.assertEqual(sum("campo" in celda for celda in filas_inventario[-1]), 4)
        self.assertEqual(inventario["esperado"]["costo_ordenar"], 300)
        self.assertEqual(inventario["esperado"]["costo_inventario"], 1915)
        self.assertEqual(inventario["esperado"]["costo_faltante"], 2950)
        self.assertEqual(inventario["esperado"]["costo_total"], 5165)
        self.assertTrue(casos_narrativa.validar_respuesta(
            inventario,
            {
                **{
                    clave: str(valor)
                    for clave, valor in inventario["esperado"].items()
                },
                "costo_inventario": "1918",
                "costo_total": "5168",
            },
        )["correcto"])
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
        inventario = casos[13]
        self.assertEqual(inventario["esperado"]["costo_ordenar"], 300)
        self.assertEqual(inventario["esperado"]["costo_inventario"], 1915)
        self.assertEqual(inventario["esperado"]["costo_faltante"], 2950)
        self.assertEqual(inventario["esperado"]["costo_total"], 5165)
        self.assertEqual(len(inventario["auditoria"]["filas"]), 12)
        self.assertEqual(sum(
            fila["Faltante"] for fila in inventario["auditoria"]["filas"]
        ), 59)
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

    def test_auditoria_bloquea_respuestas_mientras_el_capitulo_sigue_abierto(self):
        caso = casos_narrativa.crear_caso(13, 123, "OFICIAL_PDF")
        informe = construir_documento_auditoria(caso, mostrar_solucion=False)
        self.assertEqual(informe["solucion"], "Bloqueado hasta resolver el capítulo.")
        self.assertEqual(informe["motor_y_resultados"], informe["solucion"])
        self.assertEqual(informe["hipotesis"]["resultados_pruebas"], informe["solucion"])
        self.assertEqual(informe["transitorio_vs_estable"], informe["solucion"])
        self.assertTrue(any(
            valor == "Por resolver"
            for seccion in informe["tabla_reto"]
            for fila in seccion["filas"]
            for valor in fila
        ))

    def test_placeholders_no_muestran_ejemplos(self):
        for numero in range(1, 15):
            caso = casos_narrativa.crear_caso(numero, semilla=7000 + numero)
            entradas = [
                campo for campo in caso["campos"]
                if campo["tipo"] != "selector"
            ]
            self.assertTrue(entradas)
            self.assertTrue(all(
                not campo.get("placeholder_text", "").lower().startswith("ej.")
                for campo in entradas
            ))
        caso = casos_narrativa.crear_caso(1, 77, "OFICIAL_PDF")
        fila = caso["tabla_interactiva"]["secciones"][0]["filas"][0]
        self.assertTrue(all(
            not caso["tabla_interactiva"]["campos"][next(
                i for i, item in enumerate(caso["tabla_interactiva"]["campos"])
                if item["id"] == celda["campo"]
            )]["placeholder_text"].lower().startswith("ej.")
            for celda in fila
        ))
        self.assertEqual(
            construir_respuestas_exactas(caso)["tabla_interactiva_resuelta"][0]["filas"][0][2],
            caso["esperado"]["operacion1"],
        )

    def test_placeholder_no_se_toma_como_respuesta(self):
        class CampoVacio:
            placeholder_text = ""

            def get(self):
                return ""

        self.assertEqual(leer_valores_entrada({"media": CampoVacio()}), {"media": ""})

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
                "n", "Xn",
                "(aXn+C) ÷ m" if numero == 1 else "aXn ÷ m",
                "Xn+1", "# Rectangular",
            ])
            filas = caso["auditoria"]["tabla_generada"]
            for indice, fila in enumerate(filas, 1):
                self.assertEqual(
                    fila["R"], f'{fila["Xnext"]}/{caso["auditoria"]["parametros"]["m"]}',
                )
                self.assertEqual(caso["esperado"][f"R{indice}"], fila["R"])
                self.assertNotIn("ej.", next(
                    campo["etiqueta"] for campo in caso["campos"]
                    if campo["id"] == f"R{indice}"
                ))
            columnas = caso["tabla_interactiva"]["secciones"][0]["columnas"]
            self.assertEqual(len(columnas), 5)
            ids_fila_1 = {
                celda.get("campo")
                for celda in caso["tabla_interactiva"]["secciones"][0]["filas"][0]
            }
            self.assertEqual(
                ids_fila_1,
                {"n1", "Xn1", "operacion1", "Xnext1", "R1"},
            )
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

    def test_tablas_estadisticas_contienen_respuestas_interactivas_y_criticos(self):
        casos = {
            numero: casos_narrativa.crear_caso(numero, 77, "OFICIAL_PDF")
            for numero in range(3, 9)
        }
        self.assertIn("zcrit", casos[3]["tabla_interactiva"]["pie"])
        self.assertTrue(all(
            campo["campo"].startswith("D")
            for campo in casos[4]["tabla_interactiva"]["secciones"][0]["filas"][0]
            if "campo" in campo
        ))
        self.assertEqual(
            [casos[5]["esperado"][f"FO{i}"] for i in range(4)], [4, 4, 2, 0],
        )
        self.assertTrue(
            casos[7]["tabla_interactiva"]["secciones"][0]["visual"] == "cuadrantes",
        )
        manos = casos[8]["tabla_interactiva"]["secciones"][0]["filas"]
        self.assertEqual(len(manos), 7)
        self.assertEqual(
            [celda["valor"] for fila in manos for celda in fila[:1]],
            ["TD", "1P", "2P", "T", "F", "P", "Q"],
        )
        self.assertAlmostEqual(casos[8]["esperado"]["chi0"], 0.3528604, places=6)

    def test_porcentaje_y_probabilidad_admiten_fracciones_o_porcentajes(self):
        probabilidad = casos_narrativa.crear_caso(14, semilla=314)
        p = probabilidad["esperado"]["probabilidad"]
        self.assertTrue(casos_narrativa.validar_respuesta(
            probabilidad, {"probabilidad": f"{p * 100:.2f}%"},
        )["correcto"])
        self.assertTrue(casos_narrativa.validar_respuesta(
            probabilidad, {"probabilidad": str(p)},
        )["correcto"])
        inventario = casos_narrativa.crear_caso(13, semilla=313)
        self.assertTrue(casos_narrativa.validar_respuesta(
            inventario, {
                "costo_ordenar": str(inventario["esperado"]["costo_ordenar"]),
                "costo_inventario": str(inventario["esperado"]["costo_inventario"]),
                "costo_faltante": str(inventario["esperado"]["costo_faltante"]),
                "costo_total": str(inventario["esperado"]["costo_total"]),
            },
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

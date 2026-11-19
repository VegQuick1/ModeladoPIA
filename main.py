"""Interfaz gráfica y flujo de juego de EXPEDIENTE MONTECARLO."""

from __future__ import annotations

import ctypes
import importlib
import json
import os
import shutil
import sys
import tempfile
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageTk


ARCHIVO_SAVEGAME = Path(__file__).resolve().with_name("savegame.json")
HABILITAR_ATAJO_REVISION = True


def _mostrar_alerta_entorno(mensaje: str) -> None:
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(
                None, mensaje, "EXPEDIENTE MONTECARLO · Verificación de entorno", 0x10,
            )
            return
        except (AttributeError, OSError):
            pass
    print(mensaje, file=sys.stderr)


def _probar_escritura(directorio: Path) -> bool:
    if not directorio.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".expediente_", suffix=".tmp",
            dir=directorio, delete=True,
        ) as prueba:
            prueba.write("ok")
            prueba.flush()
        return True
    except OSError:
        return False


def verificar_entorno_ejecucion() -> None:
    global ARCHIVO_SAVEGAME

    errores: list[str] = []
    try:
        import tkinter
    except ImportError as error:
        errores.append(f"No se pudo cargar tkinter: {error}")
    else:
        ventana_prueba = None
        try:
            ventana_prueba = tkinter.Tk()
            ventana_prueba.withdraw()
            ventana_prueba.update_idletasks()
            ancho = ventana_prueba.winfo_screenwidth()
            alto = ventana_prueba.winfo_screenheight()
            if ancho <= 0 or alto <= 0:
                errores.append(f"Resolución de pantalla no válida: {ancho} × {alto}.")
        except (AttributeError, OSError, tkinter.TclError) as error:
            errores.append(f"El subsistema gráfico Tcl/Tk no está disponible: {error}")
        finally:
            if ventana_prueba is not None:
                try:
                    ventana_prueba.destroy()
                except tkinter.TclError:
                    pass

    try:
        customtkinter = importlib.import_module("customtkinter")
        carpeta_assets_ctk = Path(customtkinter.__file__).resolve().parent / "assets"
        carpeta_temas = carpeta_assets_ctk / "themes"
        carpeta_fuentes = carpeta_assets_ctk / "fonts"
        if not carpeta_temas.is_dir() or not any(carpeta_temas.glob("*.json")):
            errores.append(
                "Faltan los temas de CustomTkinter dentro del paquete."
            )
        if not carpeta_fuentes.is_dir() or not any(carpeta_fuentes.rglob("*.ttf")):
            errores.append("Faltan las fuentes de CustomTkinter dentro del paquete.")
    except (ImportError, OSError, AttributeError) as error:
        errores.append(f"CustomTkinter no está disponible o está incompleto: {error}")

    try:
        importlib.import_module("PIL.Image")
        importlib.import_module("PIL.ImageTk")
    except ImportError as error:
        errores.append(f"Falta Pillow (PIL), necesario para cargar imágenes: {error}")

    base_recursos = (
        Path(sys._MEIPASS) if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent
    )
    try:
        importlib.import_module("escenas_visuales")
    except ImportError as error:
        errores.append(f"No se cargaron las ilustraciones de la aplicación: {error}")
    carpeta_assets = base_recursos / "assets"
    if carpeta_assets.exists() and not carpeta_assets.is_dir():
        errores.append(f"La ruta de recursos visuales no es una carpeta: {carpeta_assets}")

    carpeta_aplicacion = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent
    )
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        carpeta_aplicacion = (
            Path.home() / "Library" / "Application Support" / "ExpedienteMontecarlo"
        )
        try:
            carpeta_aplicacion.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            errores.append(
                f"No se pudo crear la carpeta de datos de macOS: {error}"
            )

    ARCHIVO_SAVEGAME = carpeta_aplicacion / "savegame.json"
    guardado_escribible = _probar_escritura(carpeta_aplicacion)
    if ARCHIVO_SAVEGAME.exists():
        try:
            with ARCHIVO_SAVEGAME.open("r+b"):
                pass
        except OSError:
            guardado_escribible = False

    if not guardado_escribible:
        ruta_guardado_anterior = ARCHIVO_SAVEGAME
        if sys.platform == "darwin":
            local_appdata = (
                Path.home()
                / "Library"
                / "Application Support"
                / "ExpedienteMontecarlo"
            )
        else:
            local_appdata = Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    str(Path.home() / "AppData" / "Local"),
                ),
            ) / "ExpedienteMontecarlo"
        try:
            local_appdata.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            errores.append(
                "No se puede escribir junto al ejecutable y tampoco se pudo crear "
                f"{local_appdata}: {error}"
            )
        else:
            if _probar_escritura(local_appdata):
                ARCHIVO_SAVEGAME = local_appdata / "savegame.json"
                if ruta_guardado_anterior.is_file() and not ARCHIVO_SAVEGAME.exists():
                    try:
                        shutil.copy2(ruta_guardado_anterior, ARCHIVO_SAVEGAME)
                    except OSError as error:
                        errores.append(
                            "No se pudo copiar el progreso existente a la carpeta "
                            f"escribible {local_appdata}: {error}"
                        )
            else:
                errores.append(
                    "No hay permiso de escritura junto al ejecutable ni en "
                    f"{local_appdata}; se necesita una carpeta escribible para guardar."
                )

    if errores:
        _mostrar_alerta_entorno(
            "La aplicación no puede iniciarse correctamente:\n\n"
            + "\n".join(f"• {error}" for error in errores)
        )
        raise SystemExit(1)


def _revision_habilitada() -> bool:
    if getattr(sys, "frozen", False):
        return (Path(sys._MEIPASS) / "revision.enabled").is_file()
    return (
        HABILITAR_ATAJO_REVISION
        or os.environ.get("HABILITAR_ATAJO_REVISION") == "1"
    )


if __name__ == "__main__":
    verificar_entorno_ejecucion()

from tkinter import messagebox

import customtkinter as ctk

import casos_narrativa
import pruebas_estadisticas as estadisticas
from escenas_visuales import EscenaVisual


ARCHIVO_PROGRESO_ANTERIOR = Path(__file__).with_name("progreso.json")
TOTAL_CAPITULOS = 14
PENALIZACION_SEGUNDOS = 25
MODOS_EJECUCION = ("DINAMICO", "OFICIAL_PDF")
MODOS_JUEGO = ("OFICIAL", "DINAMICO")
COLOR_CORRECTO = "#4E9A67"
COLOR_INCORRECTO = "#B83B3B"
UMBRAL_ANTITRAMPAS = 12
ALIAS_PREDEFINIDOS = ("Detective Vance", "Inspectora Mercer", "Agente K.")
COLOR_MESA = "#12100E"
COLOR_SUPERFICIE = "#181512"
COLOR_CARPETA = "#241F1A"
COLOR_NOTA = "#241F1A"
COLOR_ENTRADA = "#181512"
COLOR_BORDE_ENTRADA = "#8C6D3F"
COLOR_TEXTO_ENTRADA = "#FAF6F0"
COLOR_LATON = "#A67C46"
COLOR_AMBAR = "#F5B942"
COLOR_VERIFICADO = "#4E9A67"
COLOR_ALERTA = "#B83B3B"
COLOR_TINTA = "#F5EFE6"
NARRATIVAS_TRANSICION = {
    1: (
        "El primer cuaderno cae en tus manos. La secuencia apunta a un generador que El Arquitecto dejó activo en otra terminal.",
        "El cuaderno se queda a medias y la señal se enfría. El Arquitecto ya cambió de frecuencia; la siguiente terminal puede guardar el patrón.",
    ),
    2: (
        "La segunda señal confirma que alguien repitió el mismo pulso. Un informe estadístico en el archivo municipal podría revelar quién lo oyó.",
        "La señal se corta antes de confirmar el patrón. En el archivo municipal queda otro informe, aunque El Arquitecto ya pudo borrar sus huellas.",
    ),
    3: (
        "Los promedios encajan con la muestra intervenida. La distribución deja una marca que el siguiente análisis tendrá que poner a prueba.",
        "La muestra no ofrece una conclusión firme. La distribución sigue siendo una pista, pero El Arquitecto gana tiempo para mover sus piezas.",
    ),
    4: (
        "La prueba de ajuste encuentra una desviación útil. El rastro lleva ahora a una tabla de frecuencias alterada.",
        "La prueba no alcanza a fijar la desviación. La tabla de frecuencias es la única pista que queda antes de que cambien los registros.",
    ),
    5: (
        "Las frecuencias no fueron obra del azar. Alguien dejó una distancia marcada entre dos puntos del registro.",
        "Las frecuencias no bastan para sostener la acusación. La próxima medición puede recuperar la pista antes de que desaparezca.",
    ),
    6: (
        "La distancia calculada conduce a una cuadrícula de movimientos. El Arquitecto está dejando coordenadas, no mensajes.",
        "La distancia queda sin confirmar y las coordenadas pierden precisión. Una cuadrícula de movimientos aún podría señalar su ruta.",
    ),
    7: (
        "Los cuadrantes dibujan un recorrido deliberado. En el siguiente archivo, varias manos han repartido las mismas cartas.",
        "Los movimientos no forman un patrón concluyente. Las cartas del archivo siguiente podrían revelar quién alteró la secuencia.",
    ),
    8: (
        "La combinación de cartas confirma una firma repetida. El rastro sale del archivo y llega al libro de caja de un mensajero.",
        "Las cartas no confirman la firma. El libro de caja todavía puede mostrar por dónde escapó el mensajero.",
    ),
    9: (
        "Los tiempos de servicio coinciden con la ruta del mensajero. Sus intervalos conducen a una oficina con turnos irregulares.",
        "El cálculo de los tiempos queda inconcluso. La oficina de turnos sigue siendo el siguiente lugar donde buscar.",
    ),
    10: (
        "La oficina confirma que las llegadas no son uniformes. Un registro empírico conserva los datos que alguien intentó corregir.",
        "Las llegadas no quedan clasificadas y la oficina cierra sus libros. El registro empírico es ahora la pista más cercana.",
    ),
    11: (
        "La distribución empírica coincide con varios movimientos de la investigación. Una tabla de conteos puede cerrar esa conexión.",
        "Los datos empíricos no alcanzan para confirmar la conexión. La tabla de conteos conserva una segunda oportunidad.",
    ),
    12: (
        "La tabla de Poisson reproduce la señal hasta su último valor. El patrón apunta al almacén donde El Arquitecto guarda sus recursos.",
        "La señal de Poisson queda incompleta. El almacén sigue siendo el destino probable, pero el inventario podría haber sido cambiado.",
    ),
    13: (
        "El inventario revela qué recursos fueron movidos y cuándo. Solo queda enfrentar al Arquitecto en la última jugada.",
        "El inventario no permite reconstruir todos los movimientos. La última jugada aún puede exponer al Arquitecto.",
    ),
    14: (
        "La última señal queda fijada en el expediente. Ahora toca decidir si las estrellas reunidas bastan para cerrar el caso.",
        "La última señal se pierde entre los registros. El tablero conserva los nodos pendientes; todavía puedes volver sobre ellos.",
    ),
}


def encabezado_transicion(resultado: str) -> str:
    return {
        "limpio": "★ NODO DESCIFRADO — ESTRELLA OBTENIDA",
        "tiempo_agotado": "✖ TIEMPO AGOTADO — NODO SIN ESTRELLA",
        "anti_trampa": "⚠ REGISTRO COMPROMETIDO — SIN ESTRELLA",
    }.get(resultado, "✖ NODO SIN ESTRELLA")


def narrativa_transicion(capitulo: int, resultado: str) -> str:
    if capitulo not in NARRATIVAS_TRANSICION:
        raise ValueError(f"Capítulo de transición inválido: {capitulo}")
    recuperado, perdido = NARRATIVAS_TRANSICION[capitulo]
    texto = recuperado if resultado == "limpio" else perdido
    if resultado == "anti_trampa":
        texto += " El registro muestra una alteración; la cadena de custodia quedó comprometida."
    return texto


def modo_juego_normalizado(modo: str) -> str:
    return "OFICIAL" if modo in ("OFICIAL", "OFICIAL_PDF") else "DINAMICO"


def modo_ejecucion_desde_juego(modo_juego: str) -> str:
    return "OFICIAL_PDF" if modo_juego == "OFICIAL" else "DINAMICO"


def crear_savegame(modo: str = "DINAMICO", alias: str = "") -> dict:
    if modo not in MODOS_JUEGO + MODOS_EJECUCION:
        raise ValueError(f"Modo de ejecución desconocido: {modo}")
    modo_juego = modo_juego_normalizado(modo)
    modo_ejecucion = modo_ejecucion_desde_juego(modo_juego)
    return {
        "version": 1,
        "alias": alias,
        "modo": modo_ejecucion,
        "modo_juego": modo_juego,
        "capitulo": 1,
        "capitulo_actual": 1,
        "estrellas": [],
        "fallidos": [],
        "activo": False,
        "viaje_tiempo": False,
        "pendientes_rehacer": [],
    }


def hay_partida_guardada(savegame: dict) -> bool:
    alias = savegame.get("alias", "")
    return isinstance(alias, str) and bool(alias.strip()) and (
        bool(savegame.get("activo"))
        or bool(savegame.get("estrellas"))
        or bool(savegame.get("fallidos"))
    )


def estado_nodo(numero: int, savegame: dict) -> str:
    if numero in savegame["estrellas"]:
        return "★"
    if numero in savegame["fallidos"]:
        return "⚠"
    if numero <= max(savegame["estrellas"] + savegame["fallidos"], default=0) + 1:
        return "○"
    return "🔒"


def minimo_segundos_humanos(caso: dict) -> int:
    celdas = len(caso["campos"])
    return max(UMBRAL_ANTITRAMPAS, celdas * 2)


def resultado_final(savegame: dict) -> str:
    return "bueno" if len(savegame["estrellas"]) == TOTAL_CAPITULOS else "incompleto"


def normalizar_savegame(datos: dict) -> dict:
    modo_juego = modo_juego_normalizado(
        datos.get("modo_juego", datos.get("modo", "DINAMICO")),
    )

    def capitulos(clave: str) -> list[int]:
        valores = datos.get(clave, [])
        if not isinstance(valores, list):
            return []
        return sorted({
            valor for valor in valores
            if isinstance(valor, int) and not isinstance(valor, bool)
            and 1 <= valor <= TOTAL_CAPITULOS
        })

    resultado = crear_savegame(modo_juego, str(datos.get("alias", "")).strip())
    capitulo_actual = min(
        TOTAL_CAPITULOS,
        max(1, int(datos.get("capitulo_actual", datos.get("capitulo", 1)))),
    )
    resultado.update({
        "capitulo": capitulo_actual,
        "capitulo_actual": capitulo_actual,
        "estrellas": capitulos("estrellas"),
        "fallidos": capitulos("fallidos"),
        "activo": bool(datos.get("activo", False)),
        "viaje_tiempo": bool(datos.get("viaje_tiempo", False)),
        "pendientes_rehacer": capitulos("pendientes_rehacer"),
        "alertas_antitrampa": (
            datos.get("alertas_antitrampa", [])
            if isinstance(datos.get("alertas_antitrampa", []), list) else []
        ),
        "resultado_actual": str(datos.get("resultado_actual", "")),
    })
    return resultado


def estado_reloj(segundos: int, tiempo_total: int) -> str:
    if tiempo_total <= 0:
        raise ValueError("El tiempo total del capítulo debe ser positivo.")
    proporcion = segundos / tiempo_total
    if proporcion <= 0.15:
        return "rojo"
    if proporcion <= 0.35:
        return "amarillo"
    return "verde"


def ajustar_cantidad_filas(actual: int, cambio: int, maxima: int, minimo: int = 1) -> int:
    if minimo < 0 or maxima < minimo:
        raise ValueError("Los límites de filas no son válidos.")
    return min(max(actual + cambio, minimo), maxima)


def cambiar_musica_si_disponible(aplicacion: object, pista: str) -> None:
    reproductor = getattr(aplicacion, "musica", None)
    if reproductor is not None:
        reproductor.cambiar_pista(pista)


class TableroClasificacion(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, configuracion: dict) -> None:
        super().__init__(master, fg_color=COLOR_CARPETA, corner_radius=8)
        self.configuracion = configuracion
        self.fichas_config = {
            ficha["id"]: ficha for ficha in configuracion["fichas"]
        }
        self.asignaciones: dict[str, str] = {}
        self.botones_ficha: dict[str, ctk.CTkButton] = {}
        self.fichas_por_categoria: dict[str, dict[str, ctk.CTkButton]] = {}
        self.zonas: dict[str, dict] = {}
        self.seleccionada: str | None = None
        self._arrastrando: str | None = None
        self._posicion_inicial: tuple[int, int] | None = None
        self._fantasma: ctk.CTkLabel | None = None
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text=configuracion["titulo"], anchor="w",
            text_color=COLOR_AMBAR, font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 2))
        ctk.CTkLabel(
            self, text="Arrastra una ficha a una categoría o selecciónala y pulsa su zona.",
            anchor="w", text_color=COLOR_TINTA, font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 5))

        self.zonas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.zonas_frame.grid(row=2, column=0, sticky="ew", padx=6)
        self.fichas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fichas_frame.grid(row=3, column=0, sticky="ew", padx=6, pady=(6, 8))
        columnas_zonas = configuracion.get(
            "columnas_zonas", min(4, max(1, len(configuracion["categorias"]))),
        )
        columnas_fichas = configuracion.get("columnas_fichas", 5)
        for columna in range(columnas_zonas):
            self.zonas_frame.grid_columnconfigure(columna, weight=1, uniform="zonas")
        for indice, categoria in enumerate(configuracion["categorias"]):
            zona = ctk.CTkFrame(
                self.zonas_frame, fg_color=COLOR_NOTA, corner_radius=6,
                border_width=1, border_color=COLOR_LATON,
            )
            zona.configure(height=92)
            zona.grid_propagate(False)
            zona.grid(
                row=indice // columnas_zonas, column=indice % columnas_zonas,
                sticky="nsew", padx=3, pady=3,
            )
            cabecera = ctk.CTkButton(
                zona, text=f"{categoria} · 0 asignadas", anchor="w",
                fg_color="transparent", hover_color=COLOR_SUPERFICIE,
                text_color=COLOR_TINTA, font=ctk.CTkFont(size=11, weight="bold"),
                height=24,
                command=lambda nombre=categoria: self._asignar_seleccionada(nombre),
            )
            cabecera.pack(fill="x", padx=2, pady=(2, 0))
            contenedor = ctk.CTkFrame(zona, fg_color="transparent")
            contenedor.pack(fill="both", expand=True, padx=2, pady=(0, 2))
            for columna in range(columnas_fichas):
                contenedor.grid_columnconfigure(columna, weight=1, uniform="fichas_asignadas")
            self.zonas[categoria] = {
                "frame": zona, "cabecera": cabecera, "contenedor": contenedor,
                "columnas_fichas": columnas_fichas,
            }
            self.fichas_por_categoria[categoria] = {}

        for indice, ficha in enumerate(configuracion["fichas"]):
            boton = ctk.CTkButton(
                self.fichas_frame, text=ficha["texto"], width=230, height=32,
                fg_color=COLOR_NOTA, hover_color=COLOR_SUPERFICIE,
                text_color=COLOR_TINTA, border_width=1,
                border_color=COLOR_LATON, font=ctk.CTkFont(size=12),
            )
            boton.grid(row=indice // 4, column=indice % 4, sticky="ew", padx=3, pady=2)
            self.botones_ficha[ficha["id"]] = boton
            self._vincular_arrastre(boton, ficha["id"])
        for columna in range(4):
            self.fichas_frame.grid_columnconfigure(columna, weight=1, uniform="fichas")

    def _vincular_arrastre(self, boton: ctk.CTkButton, identificador: str) -> None:
        boton.bind(
            "<ButtonPress-1>",
            lambda evento: self._iniciar_arrastre(evento, identificador),
        )
        boton.bind(
            "<B1-Motion>",
            lambda evento: self._mover_ficha(evento, identificador),
        )
        boton.bind(
            "<ButtonRelease-1>",
            lambda evento: self._soltar_ficha(evento, identificador),
        )

    def _iniciar_arrastre(self, evento: tk.Event, identificador: str) -> None:
        self._arrastrando = identificador
        self._posicion_inicial = (evento.x_root, evento.y_root)
        self.seleccionada = identificador
        self._actualizar_estilo_fichas()

    def _mover_ficha(self, evento: tk.Event, identificador: str) -> None:
        if self._arrastrando != identificador or self._posicion_inicial is None:
            return
        x_inicial, y_inicial = self._posicion_inicial
        if self._fantasma is None and (
            abs(evento.x_root - x_inicial) + abs(evento.y_root - y_inicial) >= 8
        ):
            texto = self.fichas_config[identificador]["texto"]
            self._fantasma = ctk.CTkLabel(
                self, text=texto, fg_color=COLOR_LATON,
                text_color=COLOR_TINTA, corner_radius=5,
                font=ctk.CTkFont(size=12),
            )
        if self._fantasma is not None:
            self._fantasma.place(
                x=evento.x_root - self.winfo_rootx() + 10,
                y=evento.y_root - self.winfo_rooty() + 10,
            )
            self._fantasma.lift()

    def _soltar_ficha(self, evento: tk.Event, identificador: str) -> None:
        if self._fantasma is not None:
            self._fantasma.destroy()
            self._fantasma = None
            categoria = self._categoria_en(evento.x_root, evento.y_root)
            if categoria is not None:
                self._asignar(identificador, categoria)
        else:
            if identificador in self.asignaciones:
                self._devolver(identificador)
            else:
                self.seleccionada = identificador
                self._actualizar_estilo_fichas()
        self._arrastrando = None
        self._posicion_inicial = None

    def _categoria_en(self, x: int, y: int) -> str | None:
        for categoria, zona in self.zonas.items():
            marco = zona["frame"]
            if (
                marco.winfo_rootx() <= x <= marco.winfo_rootx() + marco.winfo_width()
                and marco.winfo_rooty() <= y <= marco.winfo_rooty() + marco.winfo_height()
            ):
                return categoria
        return None

    def _asignar_seleccionada(self, categoria: str) -> None:
        if self.seleccionada is not None:
            self._asignar(self.seleccionada, categoria)

    def _asignar(self, identificador: str, categoria: str) -> None:
        anterior = self.asignaciones.get(identificador)
        if anterior == categoria:
            return
        if anterior is not None:
            boton_anterior = self.fichas_por_categoria[anterior].pop(identificador)
            boton_anterior.destroy()
            self._reorganizar_fichas(anterior)
        self.botones_ficha[identificador].grid_remove()
        boton_zona = ctk.CTkButton(
            self.zonas[categoria]["contenedor"],
            text=self.fichas_config[identificador]["texto"],
            width=100 if ", " in self.fichas_config[identificador]["texto"] else 42,
            height=16, fg_color=COLOR_NOTA, hover_color=COLOR_SUPERFICIE,
            text_color=COLOR_TINTA, border_width=1, border_color=COLOR_LATON,
            font=ctk.CTkFont(size=9),
        )
        self.fichas_por_categoria[categoria][identificador] = boton_zona
        self._vincular_arrastre(boton_zona, identificador)
        self._reorganizar_fichas(categoria)
        self.asignaciones[identificador] = categoria
        self.seleccionada = None
        self._actualizar_zonas()
        self._actualizar_estilo_fichas()

    def _devolver(self, identificador: str) -> None:
        categoria = self.asignaciones.pop(identificador, None)
        if categoria is None:
            return
        self.fichas_por_categoria[categoria].pop(identificador).destroy()
        self.botones_ficha[identificador].grid()
        self.seleccionada = identificador
        self._reorganizar_fichas(categoria)
        self._actualizar_zonas()
        self._actualizar_estilo_fichas()

    def _reorganizar_fichas(self, categoria: str) -> None:
        zona = self.zonas[categoria]
        columnas = zona["columnas_fichas"]
        for indice, boton in enumerate(self.fichas_por_categoria[categoria].values()):
            boton.grid(
                row=indice // columnas, column=indice % columnas,
                sticky="ew", padx=1, pady=0,
            )

    def completar(self) -> None:
        for identificador, ficha in self.fichas_config.items():
            self._asignar(identificador, ficha["categoria_correcta"])

    def validar(self) -> dict[str, list[str]]:
        pendientes = [
            identificador for identificador in self.fichas_config
            if identificador not in self.asignaciones
        ]
        incorrectas = [
            identificador for identificador, categoria in self.asignaciones.items()
            if categoria != self.fichas_config[identificador]["categoria_correcta"]
        ]
        return {"pendientes": pendientes, "incorrectas": incorrectas}

    def _actualizar_zonas(self) -> None:
        for categoria, zona in self.zonas.items():
            asignadas = self.fichas_por_categoria[categoria]
            zona["cabecera"].configure(
                text=f"{categoria} · {len(asignadas)} asignadas",
            )

    def _actualizar_estilo_fichas(self) -> None:
        for identificador, boton in self.botones_ficha.items():
            boton.configure(
                fg_color=(
                    COLOR_LATON if identificador in self.asignaciones else COLOR_NOTA
                ),
                border_color=(
                    COLOR_AMBAR if identificador == self.seleccionada else COLOR_LATON
                ),
            )


class TablaInteractiva(ctk.CTkFrame):
    def __init__(
        self, master: ctk.CTkBaseClass | ctk.CTkScrollableFrame,
        configuracion: dict,
        entradas: dict[str, ctk.CTkEntry | ctk.CTkComboBox | ctk.CTkOptionMenu],
        scrollable: bool = True,
    ) -> None:
        super().__init__(master, fg_color=COLOR_CARPETA, corner_radius=8)
        self.configuracion = configuracion
        self.entradas = entradas
        self.scrollable = scrollable
        self.filas_visibles: dict[str, int] = {}
        self.entradas_tabla: set[str] = set()
        self.etiquetas_corrida: dict[int, ctk.CTkLabel] = {}
        self.grid_columnconfigure(0, weight=1)
        if scrollable:
            self.grid_rowconfigure(0, weight=1)
            self.area_contenido: ctk.CTkFrame | ctk.CTkScrollableFrame = (
                ctk.CTkScrollableFrame(
                    self, fg_color=COLOR_CARPETA, corner_radius=8,
                    scrollbar_button_color=COLOR_LATON,
                    scrollbar_button_hover_color=COLOR_AMBAR,
                )
            )
            self.area_contenido._scrollbar.grid_remove()
            self.area_contenido.bind(
                "<Configure>", self._programar_ajuste_scrollbar, add="+",
            )
            self.area_contenido._parent_canvas.bind(
                "<Configure>", self._programar_ajuste_scrollbar, add="+",
            )
            self.area_contenido.grid(row=0, column=0, sticky="nsew")
        else:
            self.area_contenido = ctk.CTkFrame(
                self, fg_color=COLOR_CARPETA, corner_radius=8,
            )
            self.area_contenido.grid(row=0, column=0, sticky="ew")
        self._renderizar()
        if scrollable:
            self.after_idle(self._ajustar_scrollbar)

    def _programar_ajuste_scrollbar(self, _evento: tk.Event) -> None:
        if self.scrollable:
            self.after_idle(self._ajustar_scrollbar)

    def _ajustar_scrollbar(self) -> None:
        if not self.scrollable or not self.winfo_exists():
            return
        area = self.area_contenido
        if not isinstance(area, ctk.CTkScrollableFrame):
            return
        alto_contenido = area.winfo_reqheight()
        alto_visible = area._parent_canvas.winfo_height()
        if alto_contenido > alto_visible > 1:
            area._scrollbar.grid()
        else:
            area._scrollbar.grid_remove()
            area._parent_canvas.yview_moveto(0)

    def _renderizar(self) -> None:
        contenido = self.area_contenido
        self.etiquetas_corrida.clear()
        valores_entrada = {
            clave: self.entradas[clave].get()
            for clave in self.entradas_tabla if clave in self.entradas
        }
        for widget in contenido.winfo_children():
            widget.destroy()
        for clave in self.entradas_tabla:
            self.entradas.pop(clave, None)
        self.entradas_tabla.clear()
        fila_grid = 0
        for seccion in self.configuracion["secciones"]:
            ctk.CTkLabel(
                contenido, text=seccion["titulo"], anchor="w",
                text_color=COLOR_AMBAR, font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=fila_grid, column=0, sticky="ew", padx=8, pady=(10, 4))
            fila_grid += 1
            tabla_seccion = ctk.CTkFrame(contenido, fg_color="transparent")
            tabla_seccion.grid(row=fila_grid, column=0, sticky="ew", padx=6)
            fila_grid += 1
            cantidad_columnas = 2 if seccion.get("visual") == "cuadrantes" else len(
                seccion["columnas"],
            )
            for columna in range(cantidad_columnas):
                tabla_seccion.grid_columnconfigure(
                    columna, weight=1, uniform=seccion["id"],
                )
            if seccion.get("visual") != "cuadrantes":
                encabezado = ctk.CTkFrame(tabla_seccion, fg_color=COLOR_NOTA)
                encabezado.grid(
                    row=0, column=0, columnspan=cantidad_columnas, sticky="ew",
                )
                for columna, nombre in enumerate(seccion["columnas"]):
                    encabezado.grid_columnconfigure(
                        columna, weight=1, uniform=seccion["id"],
                    )
                    ctk.CTkLabel(
                        encabezado, text=nombre, text_color=COLOR_TINTA,
                        font=ctk.CTkFont(size=13, weight="bold"),
                    ).grid(row=0, column=columna, sticky="ew", padx=3, pady=5)
            visible = self.filas_visibles.setdefault(
                seccion["id"],
                seccion["filas_iniciales"] if seccion["dinamica"] else len(seccion["filas"]),
            )
            visible = min(visible, len(seccion["filas"]))
            self.filas_visibles[seccion["id"]] = visible
            cuerpo = ctk.CTkFrame(
                tabla_seccion, fg_color="transparent",
            )
            cuerpo.grid(
                row=1 if seccion.get("visual") != "cuadrantes" else 0,
                column=0, columnspan=cantidad_columnas, sticky="ew",
            )
            for columna in range(cantidad_columnas):
                cuerpo.grid_columnconfigure(columna, weight=1, uniform=seccion["id"])
            if seccion.get("visual") == "cuadrantes":
                posiciones = [
                    ("Sup-Izq", 1, 0, 0), ("Sup-Der", 3, 0, 1),
                    ("Inf-Izq", 0, 1, 0), ("Inf-Der", 2, 1, 1),
                ]
                por_indice = seccion["filas"]
                for etiqueta, indice, fila, columna in posiciones:
                    bloque = ctk.CTkFrame(
                        cuerpo, fg_color=COLOR_NOTA, corner_radius=6,
                        border_color=COLOR_LATON, border_width=1,
                    )
                    bloque.grid(
                        row=fila, column=columna, sticky="nsew",
                        padx=5, pady=5,
                    )
                    ctk.CTkLabel(
                        bloque, text=etiqueta, text_color=COLOR_TINTA,
                    ).pack(pady=(5, 2))
                    fo_celda = por_indice[indice][1]
                    campo = next(
                        item for item in self.configuracion["campos"]
                        if item["id"] == fo_celda["campo"]
                    )
                    entrada = ctk.CTkEntry(
                        bloque,
                        placeholder_text=campo.get("placeholder_text", campo["etiqueta"]),
                        fg_color=COLOR_ENTRADA, text_color=COLOR_TEXTO_ENTRADA,
                        placeholder_text_color="#9E9384",
                        border_color=COLOR_BORDE_ENTRADA,
                        font=ctk.CTkFont(size=14),
                        justify="center",
                    )
                    if campo["id"] in valores_entrada:
                        entrada.insert(0, valores_entrada[campo["id"]])
                    entrada.pack(fill="x", padx=8, pady=(0, 5))
                    self.entradas[campo["id"]] = entrada
                    self.entradas_tabla.add(campo["id"])
                    ctk.CTkLabel(
                        bloque, text=f'FE = {por_indice[indice][2]["valor"]}',
                        text_color=COLOR_TINTA, font=ctk.CTkFont(size=13),
                    ).pack(pady=(0, 5))
            else:
                for indice, celdas in enumerate(seccion["filas"][:visible]):
                    for columna, celda in enumerate(celdas):
                        if "campo" in celda:
                            campo = next(
                                item for item in self.configuracion["campos"]
                                if item["id"] == celda["campo"]
                            )
                            if campo["tipo"] == "selector":
                                entrada = ctk.CTkComboBox(
                                    cuerpo, values=campo["opciones"], state="readonly",
                                    fg_color=COLOR_ENTRADA, text_color=COLOR_TEXTO_ENTRADA,
                                    border_color=COLOR_BORDE_ENTRADA, button_color=COLOR_LATON,
                                    button_hover_color="#A57C44",
                                    font=ctk.CTkFont(size=14),
                                    command=(
                                        self.recalcular_corridas_volados
                                        if seccion["id"] == "volados"
                                        and campo["id"].startswith("estado")
                                        else None
                                    ),
                                )
                                entrada.set("")
                            elif campo["tipo"] == "option_menu":
                                entrada = ctk.CTkOptionMenu(
                                    cuerpo, values=campo["opciones"],
                                    fg_color=COLOR_ENTRADA, text_color=COLOR_TEXTO_ENTRADA,
                                    button_color=COLOR_LATON,
                                    button_hover_color="#A57C44",
                                    dropdown_fg_color=COLOR_CARPETA,
                                    dropdown_text_color=COLOR_TINTA,
                                    font=ctk.CTkFont(size=14),
                                )
                                entrada.set("")
                            else:
                                entrada = ctk.CTkEntry(
                                    cuerpo,
                                    placeholder_text=campo.get(
                                        "placeholder_text", campo["tipo"],
                                    ),
                                    fg_color=COLOR_ENTRADA, text_color=COLOR_TEXTO_ENTRADA,
                                    placeholder_text_color="#9E9384",
                                    border_color=COLOR_BORDE_ENTRADA,
                                    font=ctk.CTkFont(size=14),
                                )
                            if campo["id"] in valores_entrada:
                                valor_anterior = valores_entrada[campo["id"]]
                                if campo["tipo"] in {"selector", "option_menu"}:
                                    entrada.set(valor_anterior)
                                else:
                                    entrada.insert(0, valor_anterior)
                            entrada.grid(
                                row=indice, column=columna, sticky="ew", padx=3, pady=2,
                            )
                            self.entradas[campo["id"]] = entrada
                            self.entradas_tabla.add(campo["id"])
                            if seccion["dinamica"] and columna == len(celdas) - 1:
                                entrada.bind(
                                    "<Return>",
                                    lambda _, clave=seccion["id"]: self.agregar_fila(clave),
                                )
                        else:
                            etiqueta = ctk.CTkLabel(
                                cuerpo, text=str(celda["valor"]), anchor="center",
                                fg_color=COLOR_CARPETA, corner_radius=4,
                                text_color=COLOR_TINTA,
                                font=ctk.CTkFont(size=14),
                            )
                            etiqueta.grid(
                                row=indice, column=columna, sticky="ew", padx=3, pady=2,
                            )
                            if seccion["id"] == "volados" and columna == 0:
                                self.etiquetas_corrida[indice + 1] = etiqueta
            fila_grid += 1
            if seccion["dinamica"]:
                controles = ctk.CTkFrame(contenido, fg_color="transparent")
                controles.grid(row=fila_grid, column=0, sticky="w", padx=6, pady=(3, 8))
                ctk.CTkButton(
                    controles, text="+ Agregar fila", width=120,
                    command=lambda clave=seccion["id"]: self.agregar_fila(clave),
                    fg_color=COLOR_LATON, hover_color="#A57C44",
                    font=ctk.CTkFont(size=13, weight="bold"),
                ).pack(side="left", padx=3)
                ctk.CTkButton(
                    controles, text="− Quitar fila", width=120,
                    command=lambda clave=seccion["id"]: self.quitar_fila(clave),
                    fg_color="#6A3029", hover_color="#8A3B34",
                    font=ctk.CTkFont(size=13, weight="bold"),
                ).pack(side="left", padx=3)
                fila_grid += 1
        if any(seccion["id"] == "volados" for seccion in self.configuracion["secciones"]):
            self.recalcular_corridas_volados()

    def recalcular_corridas_volados(self, _valor: str | None = None) -> None:
        if _valor is not None and _valor not in {"Meta", "Quiebra", "Continúa"}:
            return
        corrida = 1
        for indice, fila in enumerate(self._seccion("volados")["filas"], 1):
            fila[0]["valor"] = corrida
            etiqueta = self.etiquetas_corrida.get(indice)
            if etiqueta is not None:
                etiqueta.configure(text=str(corrida))
            estado = self.entradas.get(f"estado{indice}")
            if estado is not None and estado.get() in {"Meta", "Quiebra"}:
                corrida += 1

    def agregar_fila(self, clave: str) -> None:
        seccion = self._seccion(clave)
        cantidad = self.filas_visibles[clave]
        nueva_cantidad = ajustar_cantidad_filas(
            cantidad, 1, seccion["max_filas"],
        )
        if nueva_cantidad != cantidad:
            self.filas_visibles[clave] = nueva_cantidad
            self._renderizar()

    def quitar_fila(self, clave: str) -> None:
        cantidad = self.filas_visibles[clave]
        nueva_cantidad = ajustar_cantidad_filas(
            cantidad, -1, self._seccion(clave)["max_filas"],
        )
        if nueva_cantidad != cantidad:
            self.filas_visibles[clave] = nueva_cantidad
            self._renderizar()

    def cantidad_filas(self) -> dict[str, int]:
        return self.filas_visibles.copy()

    def colorear(self, correctos: list[str], incorrectos: list[str]) -> None:
        for clave in correctos:
            self._colorear_entrada(clave, COLOR_CORRECTO)
        for clave in incorrectos:
            self._colorear_entrada(clave, COLOR_INCORRECTO)

    def _colorear_entrada(self, clave: str, color: str) -> None:
        entrada = self.entradas.get(clave)
        if entrada is not None:
            if isinstance(entrada, ctk.CTkOptionMenu):
                entrada.configure(fg_color=color)
            else:
                entrada.configure(border_color=color)

    def _seccion(self, clave: str) -> dict:
        return next(seccion for seccion in self.configuracion["secciones"]
                    if seccion["id"] == clave)


class ReproductorAmbiental:
    def __init__(self, ventana: ctk.CTk, carpeta_assets: Path) -> None:
        self.ventana = ventana
        self.carpeta_audio = carpeta_assets / "audio"
        self._pygame = None
        self._silenciado = False
        self._pista_actual: str | None = None
        self._pista_pendiente: str | None = None
        try:
            pygame = importlib.import_module("pygame")
        except ImportError:
            return
        try:
            pygame.mixer.init()
        except pygame.error as error:
            print(f"Audio ambiental desactivado: {error}", file=sys.stderr)
            return
        self._pygame = pygame

    @property
    def silenciado(self) -> bool:
        return self._silenciado

    @property
    def disponible(self) -> bool:
        return self._pygame is not None

    def cambiar_pista(self, nombre: str) -> None:
        self._pista_pendiente = nombre
        if self._silenciado or self._pygame is None or nombre == self._pista_actual:
            return
        if self._pista_actual is None:
            self._iniciar_pista(nombre)
            return
        self._pygame.mixer.music.fadeout(850)
        self.ventana.after(900, self._iniciar_pista_pendiente)

    def alternar(self) -> bool:
        self._silenciado = not self._silenciado
        if self._silenciado:
            if self._pygame is not None:
                self._pygame.mixer.music.stop()
        elif self._pista_pendiente is not None:
            self._pista_actual = None
            self._iniciar_pista(self._pista_pendiente)
        return self._silenciado

    def cerrar(self) -> None:
        if self._pygame is not None:
            self._pygame.mixer.music.stop()
            self._pygame.mixer.quit()

    def _iniciar_pista_pendiente(self) -> None:
        if self._pista_pendiente is not None:
            self._iniciar_pista(self._pista_pendiente)

    def _iniciar_pista(self, nombre: str) -> None:
        if self._silenciado or self._pygame is None:
            return
        ruta = next(
            (
                self.carpeta_audio / f"{nombre}.{extension}"
                for extension in ("mp3", "wav")
                if (self.carpeta_audio / f"{nombre}.{extension}").is_file()
            ),
            None,
        )
        if ruta is None:
            print(
                f"No se encontró la pista {nombre} en {self.carpeta_audio}.",
                file=sys.stderr,
            )
            return
        try:
            self._pygame.mixer.music.load(str(ruta))
            self._pygame.mixer.music.set_volume(0.35)
            self._pygame.mixer.music.play(-1, fade_ms=650)
        except self._pygame.error as error:
            print(f"No se pudo reproducir {ruta}: {error}", file=sys.stderr)
            return
        self._pista_actual = nombre


class ExpedienteMontecarlo(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("EXPEDIENTE MONTECARLO | El Rastro del Fantasma")
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        ancho_ventana = min(
            ancho_pantalla, max(680, min(1600, int(ancho_pantalla * 0.88))),
        )
        alto_ventana = min(
            alto_pantalla, max(560, min(1100, int(alto_pantalla * 0.86))),
        )
        self._altura_escena = max(130, min(200, int(alto_ventana * 0.18)))
        self._ancho_lateral = max(220, min(278, int(ancho_ventana * 0.21)))
        self.geometry(
            f"{ancho_ventana}x{alto_ventana}"
            f"+{max(0, (ancho_pantalla - ancho_ventana) // 2)}"
            f"+{max(0, (alto_pantalla - alto_ventana) // 2)}",
        )
        self.minsize(
            min(ancho_ventana, max(700, int(ancho_pantalla * 0.72))),
            min(alto_ventana, max(560, int(alto_pantalla * 0.72))),
        )
        self.configure(fg_color=COLOR_MESA)
        carpeta_assets = (
            Path(sys._MEIPASS) / "assets"
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().with_name("assets")
        )
        self.musica = ReproductorAmbiental(self, carpeta_assets)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        self.savegame = self._cargar_savegame()
        self.modo_ejecucion = self.savegame["modo"]
        self.modo_juego = self.savegame["modo_juego"]
        self.capitulo = self.savegame["capitulo_actual"]
        self.completados = set(self.savegame["estrellas"])
        self.capitulos_fallidos = set(self.savegame["fallidos"])
        self.caso = casos_narrativa.crear_caso(self.capitulo, modo_ejecucion=self.modo_ejecucion)
        self.fin = 0.0
        self.inicio_capitulo = 0.0
        self.investigacion_iniciada = False
        self.resuelto = False
        self.revision_activa = False
        self.entradas: dict[
            str, ctk.CTkEntry | ctk.CTkComboBox | ctk.CTkOptionMenu
        ] = {}
        self._modo_nuevo = self.modo_juego

        self._construir_interfaz()
        if _revision_habilitada():
            revision = importlib.import_module("revision")
            revision.instalar_revision(self)
        self._renderizar_caso(reiniciar_reloj=False)
        self._mostrar_menu()

    def _cerrar(self) -> None:
        self.musica.cerrar()
        self.destroy()

    def _alternar_sonido(self) -> None:
        silenciado = self.musica.alternar()
        self.boton_sonido.configure(text="🔇" if silenciado else "🔊")

    def _construir_interfaz(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        encabezado = ctk.CTkFrame(self, fg_color=COLOR_CARPETA, corner_radius=0, height=58)
        encabezado.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(
            encabezado, text="◈ EXPEDIENTE MONTECARLO",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_AMBAR,
        ).pack(side="left", padx=22, pady=14)
        ctk.CTkLabel(
            encabezado, text="UNIDAD DE ANÁLISIS FORENSE  /  CLASIFICADO",
            font=ctk.CTkFont(size=13), text_color=COLOR_TINTA,
        ).pack(side="right", padx=(12, 16))
        self.boton_sonido = ctk.CTkButton(
            encabezado, text="🔊" if self.musica.disponible else "🔇",
            width=42, height=36,
            command=self._alternar_sonido, fg_color="#3A3023",
            hover_color=COLOR_LATON, font=ctk.CTkFont(size=16),
            state="normal" if self.musica.disponible else "disabled",
        )
        self.boton_sonido.pack(side="right", padx=(6, 2), pady=8)

        self.lateral = ctk.CTkFrame(
            self, width=self._ancho_lateral, fg_color=COLOR_SUPERFICIE,
            corner_radius=0,
        )
        self.lateral.grid(row=1, column=0, sticky="nsew")
        self.lateral.grid_propagate(False)
        self.ficha_expediente = ctk.CTkFrame(
            self.lateral, fg_color=COLOR_CARPETA, border_color=COLOR_LATON,
            border_width=1, corner_radius=8,
        )
        self.ficha_expediente.pack(fill="x", padx=12, pady=18)
        ctk.CTkLabel(
            self.ficha_expediente, text="EXPEDIENTE ACTIVO", text_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(14, 4))
        ctk.CTkLabel(
            self.ficha_expediente, text="◉", font=ctk.CTkFont(size=58), text_color=COLOR_ALERTA,
        ).pack(pady=(8, 0))
        ctk.CTkLabel(
            self.ficha_expediente, text='SOSPECHOSO: "EL ARQUITECTO"',
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=8)
        self.estado = ctk.CTkLabel(
            self.ficha_expediente, text="INVESTIGACIÓN NO INICIADA",
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=13),
        )
        self.estado.pack(pady=3)
        self.etiqueta_caso = ctk.CTkLabel(
            self.ficha_expediente, text="", wraplength=238,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.etiqueta_caso.pack(pady=(14, 8), padx=14)
        ctk.CTkLabel(
            self.ficha_expediente, text="CRONÓMETRO FORENSE",
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=13),
        ).pack(pady=(10, 2))
        self.reloj = ctk.CTkLabel(
            self.ficha_expediente, text="10:00", font=ctk.CTkFont(size=48, weight="bold"),
            text_color=COLOR_AMBAR, fg_color=COLOR_NOTA, corner_radius=6,
        )
        self.reloj.pack(pady=4, padx=14, fill="x")
        self.progreso_label = ctk.CTkLabel(
            self.ficha_expediente, text="", text_color=COLOR_TINTA,
            font=ctk.CTkFont(size=13),
        )
        self.progreso_label.pack(pady=10)
        self.modo_insignia = ctk.CTkLabel(
            self.ficha_expediente, text="", text_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.modo_insignia.pack(pady=(4, 14))
        self.tabs = ctk.CTkFrame(self, fg_color=COLOR_SUPERFICIE)
        self.tabs.grid(row=1, column=1, sticky="nsew", padx=(8, 18), pady=12)
        self.expediente_tab = ctk.CTkFrame(self.tabs, fg_color="transparent")
        self.expediente_tab.grid(row=0, column=0, sticky="nsew")
        self.tabs.grid_columnconfigure(0, weight=1)
        self.tabs.grid_rowconfigure(0, weight=1)
        self._crear_pestana_expediente()

        self.menu_frame = ctk.CTkFrame(self, fg_color=COLOR_MESA, corner_radius=0)
        self.menu_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=45, pady=25)
        self.menu_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.menu_frame, text="EXPEDIENTE MONTECARLO",
            text_color=COLOR_AMBAR, font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, pady=(6, 2))
        ctk.CTkLabel(
            self.menu_frame, text="EL RASTRO DEL FANTASMA",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TINTA,
        ).grid(row=1, column=0, pady=(0, 4))
        ctk.CTkLabel(
            self.menu_frame,
            text="La lluvia no borra los datos. Elige un expediente y conserva la cadena de custodia.",
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=14),
        ).grid(row=2, column=0, pady=(0, 12))
        self.mapa_progreso = ctk.CTkFrame(self.menu_frame, fg_color=COLOR_SUPERFICIE)
        self.mapa_progreso.grid(row=3, column=0, padx=20, pady=8)
        self.botones_modo = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        self.botones_modo.grid(row=4, column=0, pady=8)
        ctk.CTkButton(
            self.botones_modo, text="Nueva Investigación: Modo Apuntes (Oficial)",
            command=lambda: self._nuevo_juego("OFICIAL"), width=350,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        ).pack(side="left", padx=7)
        ctk.CTkButton(
            self.botones_modo, text="Nueva Investigación: Modo Dinámico (Semillas Aleatorias)",
            command=lambda: self._nuevo_juego("DINAMICO"), width=390,
            fg_color=COLOR_VERIFICADO, hover_color="#3D7A52",
        ).pack(side="left", padx=7)
        self.modo_bloqueado_label = ctk.CTkLabel(
            self.menu_frame, text="", text_color="#e0a952",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.modo_bloqueado_label.grid(row=4, column=0, pady=8)
        self.modo_bloqueado_label.grid_remove()
        self.boton_continuar = ctk.CTkButton(
            self.menu_frame, text="Continuar Investigación",
            command=self._continuar_investigacion, width=300, height=40,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        )
        self.boton_continuar.grid(row=5, column=0, pady=(5, 3))
        ctk.CTkButton(
            self.menu_frame, text="Restablecer Progreso",
            command=self._restablecer_progreso, width=220,
            fg_color="#6A3029", hover_color="#8A3B34",
        ).grid(row=6, column=0, pady=(3, 5))

        self.dialogo_frame = ctk.CTkFrame(self, fg_color=COLOR_MESA)
        self.dialogo_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.dialogo_frame.grid_columnconfigure(0, weight=1)
        self.alias_seleccionado = ctk.StringVar(value=ALIAS_PREDEFINIDOS[0])
        self.ingreso_visual = EscenaVisual(
            self.dialogo_frame, "ingreso", height=self._altura_escena,
        )
        self.ingreso_visual.grid(row=0, column=0, sticky="ew", padx=45, pady=(12, 4))
        ctk.CTkLabel(
            self.dialogo_frame, text="ARCHIVO DE INGRESO · 02:13 A. M.",
            text_color=COLOR_AMBAR, font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=1, column=0, pady=(10, 12))
        ctk.CTkLabel(
            self.dialogo_frame,
            text="— La ciudad está bajo lluvia, detective. El expediente no espera.\nElija el nombre que quedará en la cadena de custodia.",
            justify="center", text_color=COLOR_TINTA, font=ctk.CTkFont(size=15),
        ).grid(row=2, column=0, pady=8)
        self.alias_menu = ctk.CTkComboBox(
            self.dialogo_frame, values=list(ALIAS_PREDEFINIDOS) + ["Alias personalizado"],
            variable=self.alias_seleccionado, width=310, command=self._cambio_alias,
            fg_color=COLOR_ENTRADA, text_color=COLOR_TINTA,
            border_color=COLOR_BORDE_ENTRADA, button_color=COLOR_LATON,
            button_hover_color="#A57C44",
            font=ctk.CTkFont(size=14),
        )
        self.alias_menu.grid(row=3, column=0, pady=6)
        self.alias_personalizado = ctk.CTkEntry(
            self.dialogo_frame, placeholder_text="Escriba su alias",
            width=310, fg_color=COLOR_ENTRADA, text_color=COLOR_TEXTO_ENTRADA,
            placeholder_text_color="#9E9384", border_color=COLOR_BORDE_ENTRADA,
            font=ctk.CTkFont(size=14),
        )
        self.alias_personalizado.grid(row=4, column=0, pady=6)
        self.alias_personalizado.grid_remove()
        ctk.CTkButton(
            self.dialogo_frame, text="Entrar al expediente",
            command=self._confirmar_nuevo_juego, width=260,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        ).grid(row=5, column=0, pady=(14, 6))
        ctk.CTkButton(
            self.dialogo_frame, text="Volver al menú",
            command=self._mostrar_menu, width=180, fg_color="#55452F",
        ).grid(row=6, column=0, pady=4)

        self.transicion_frame = ctk.CTkFrame(self, fg_color=COLOR_MESA)
        self.transicion_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.transicion_frame.grid_columnconfigure(0, weight=1)
        self.transicion_visual = EscenaVisual(
            self.transicion_frame, "capitulo_01", height=self._altura_escena,
        )
        self.transicion_visual.grid(row=0, column=0, sticky="ew", padx=25, pady=(10, 2))
        self.transicion_titulo = ctk.CTkLabel(
            self.transicion_frame, text="", text_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=19, weight="bold"),
        )
        self.transicion_titulo.grid(row=1, column=0, pady=(8, 10))
        self.transicion_texto = ctk.CTkLabel(
            self.transicion_frame, text="", justify="center", wraplength=760,
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=15),
        )
        self.transicion_texto.grid(row=2, column=0, padx=30, pady=8)
        self.boton_iniciar_nodo = ctk.CTkButton(
            self.transicion_frame, text="Iniciar Nodo",
            command=self._iniciar_nodo, width=240,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        )
        self.boton_iniciar_nodo.grid(row=3, column=0, pady=(12, 6))
        ctk.CTkButton(
            self.transicion_frame, text="Volver al Menú Principal",
            command=self._mostrar_menu, width=240, fg_color="#55452F",
        ).grid(row=4, column=0, pady=5)

        self.descanso_frame = ctk.CTkFrame(self, fg_color=COLOR_MESA)
        self.descanso_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.descanso_frame.grid_columnconfigure(0, weight=1)
        self.descanso_visual = EscenaVisual(
            self.descanso_frame, "transicion", height=self._altura_escena,
        )
        self.descanso_visual.grid(row=0, column=0, sticky="ew", padx=25, pady=(10, 2))
        self.descanso_titulo = ctk.CTkLabel(
            self.descanso_frame, text="", text_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.descanso_titulo.grid(row=1, column=0, pady=(8, 10))
        self.descanso_texto = ctk.CTkLabel(
            self.descanso_frame, text="", wraplength=760, justify="center",
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=15),
        )
        self.descanso_texto.grid(row=2, column=0, padx=30, pady=8)
        self.boton_descanso_continuar = ctk.CTkButton(
            self.descanso_frame, text="Continuar",
            command=self._continuar_desde_descanso, width=310,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        )
        self.boton_descanso_continuar.grid(row=3, column=0, pady=(12, 6))
        ctk.CTkButton(
            self.descanso_frame, text="Guardar progreso y volver al Menú Principal",
            command=self._guardar_y_volver_menu, width=380, fg_color="#55452F",
        ).grid(row=4, column=0, pady=5)

        self.final_frame = ctk.CTkFrame(self, fg_color=COLOR_MESA)
        self.final_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.final_frame.grid_columnconfigure(0, weight=1)
        self.final_visual = EscenaVisual(
            self.final_frame, "final_bueno", height=self._altura_escena,
        )
        self.final_visual.grid(row=0, column=0, sticky="ew", padx=25, pady=(8, 2))
        self.final_titulo = ctk.CTkLabel(
            self.final_frame, text="", text_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.final_titulo.grid(row=1, column=0, pady=(8, 10))
        self.final_texto = ctk.CTkLabel(
            self.final_frame, text="", wraplength=800, justify="center",
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=15),
        )
        self.final_texto.grid(row=2, column=0, padx=30, pady=8)
        self.boton_viaje = ctk.CTkButton(
            self.final_frame, text="Volver en el tiempo: reconstruir nodos sin estrella",
            command=self._iniciar_viaje_tiempo, width=440,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        )
        self.boton_viaje.grid(row=3, column=0, pady=(12, 6))
        self.boton_final_no = ctk.CTkButton(
            self.final_frame, text="No. Cerrar el expediente",
            command=self._final_malo, width=300, fg_color="#6A3029",
        )
        self.boton_final_no.grid(row=4, column=0, pady=5)
        ctk.CTkButton(
            self.final_frame, text="Volver al Menú Principal",
            command=self._mostrar_menu, width=220, fg_color="#55452F",
        ).grid(row=5, column=0, pady=8)

        for pantalla in (self.dialogo_frame, self.transicion_frame, self.descanso_frame, self.final_frame):
            pantalla.grid_remove()

    def _crear_pestana_expediente(self) -> None:
        tab = self.expediente_tab
        tab.grid_columnconfigure(0, weight=4)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        self.cabecera_caso = ctk.CTkLabel(
            tab, text="TRANSMISIÓN INTERCEPTADA",
            text_color=COLOR_AMBAR, font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.cabecera_caso.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 2))
        self.narrativa = ctk.CTkLabel(
            tab, text="", justify="left", anchor="nw", wraplength=920,
            font=ctk.CTkFont(size=15), text_color=COLOR_TINTA,
        )
        self.narrativa.grid(row=1, column=0, sticky="ew", padx=14, pady=10)
        self.formula_label = ctk.CTkLabel(
            tab, text="", justify="left", anchor="w", wraplength=250,
            fg_color=COLOR_CARPETA, corner_radius=8, text_color=COLOR_AMBAR,
            font=ctk.CTkFont(family="Consolas", size=15),
        )
        self.formula_label.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=10)
        self.formula_label.grid_remove()
        self.tabla_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.tabla_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=12, pady=8)
        self.tabla_frame.grid_columnconfigure(0, weight=1)
        self.tabla_frame.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            tab, fg_color=COLOR_CARPETA, border_color=COLOR_LATON, border_width=1,
        )
        panel.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=10)
        panel.grid_columnconfigure(0, weight=1)
        self.formato = ctk.CTkLabel(
            panel, text="", anchor="w", wraplength=900,
            text_color=COLOR_TINTA, font=ctk.CTkFont(size=14),
        )
        self.formato.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self.campos_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.campos_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        for columna in range(4):
            self.campos_frame.grid_columnconfigure(columna, weight=1)
        controles = ctk.CTkFrame(panel, fg_color="transparent")
        controles.grid(row=2, column=0, sticky="ew", padx=8, pady=4)
        self.verificar = ctk.CTkButton(
            controles, text="Verificar solución", command=self._verificar,
            fg_color=COLOR_LATON, hover_color="#A57C44",
        )
        self.verificar.pack(side="left", padx=4)
        self.tablas_boton = ctk.CTkButton(
            controles, text="Tablas Estadísticas",
            command=self._mostrar_tablas_estadisticas,
            fg_color="#55452F", hover_color="#705A38",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.mensaje = ctk.CTkLabel(
            panel, text="", anchor="w", wraplength=900,
        )
        self.mensaje.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 6))

        self.victoria = ctk.CTkFrame(tab, fg_color=COLOR_CARPETA, corner_radius=18)
        self.victoria.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=35, pady=35)
        self.victoria.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.victoria, text="INVESTIGACIÓN COMPLETADA",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_AMBAR,
        ).grid(row=0, column=0, pady=(90, 24))
        ctk.CTkLabel(
            self.victoria, text="EL ARQUITECTO HA SIDO LOCALIZADO",
            font=ctk.CTkFont(size=18), text_color=COLOR_TINTA,
        ).grid(row=1, column=0, pady=12)
        self.coordenadas_label = ctk.CTkLabel(
            self.victoria, text="", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_AMBAR,
        )
        self.coordenadas_label.grid(row=2, column=0, pady=24)
        ctk.CTkLabel(
            self.victoria, text="14 NODOS DESCIFRADOS · EVIDENCIA GUARDADA",
            text_color=COLOR_TINTA,
        ).grid(row=3, column=0, pady=12)
        self.victoria.grid_remove()

    def _ocultar_pantallas(self) -> None:
        for pantalla in (
            self.menu_frame, self.dialogo_frame, self.transicion_frame,
            self.descanso_frame, self.final_frame,
        ):
            pantalla.grid_remove()
        self.lateral.grid_remove()
        self.tabs.grid_remove()

    def _mostrar_menu(self) -> None:
        self.investigacion_iniciada = False
        cambiar_musica_si_disponible(self, "menu_noir")
        self._ocultar_pantallas()
        self._actualizar_mapa_progreso()
        self._actualizar_estado_menu()
        self.menu_frame.grid()

    def _actualizar_estado_menu(self) -> None:
        hay_partida = hay_partida_guardada(self.savegame)
        if hay_partida:
            self.botones_modo.grid_remove()
            etiqueta_modo = (
                "MODO APUNTES" if self.savegame["modo_juego"] == "OFICIAL"
                else "MODO DINÁMICO"
            )
            self.modo_bloqueado_label.configure(
                text=f"EXPEDIENTE EN CURSO · {etiqueta_modo} (BLOQUEADO)",
            )
            self.modo_bloqueado_label.grid()
        else:
            self.modo_bloqueado_label.grid_remove()
            self.botones_modo.grid()
        self.boton_continuar.configure(
            state="normal" if hay_partida else "disabled",
            text=(
                f"Continuar Investigación (Capítulo "
                f"{self.savegame['capitulo_actual']:02d})"
                if hay_partida else "Continuar Investigación"
            ),
        )

    def _actualizar_mapa_progreso(self) -> None:
        for widget in self.mapa_progreso.winfo_children():
            widget.destroy()
        self.mapa_progreso.grid_columnconfigure(0, weight=1)
        capitulo_actual = self.savegame["capitulo_actual"]
        ctk.CTkLabel(
            self.mapa_progreso, text=f"INVESTIGADOR: {self.savegame['alias'] or 'SIN IDENTIFICAR'}",
            text_color=COLOR_AMBAR, font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            self.mapa_progreso,
            text=f"CAPÍTULO ACTUAL: {capitulo_actual:02d} · {casos_narrativa.TITULOS[capitulo_actual - 1]}",
            text_color=COLOR_AMBAR, font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=1, column=0, columnspan=4, sticky="w", padx=12, pady=(2, 6))
        for numero in range(1, TOTAL_CAPITULOS + 1):
            estado = estado_nodo(numero, self.savegame)
            actual = numero == capitulo_actual
            texto = f"{'▶ ' if actual else ''}{estado} NODO {numero:02d}"
            color = (
                "#3C684A" if actual else
                "#314B38" if estado == "★" else
                "#5A2A27" if estado == "⚠" else COLOR_CARPETA
            )
            boton = ctk.CTkButton(
                self.mapa_progreso, text=texto, width=170, height=34,
                fg_color=color, hover_color="#705A38", state="disabled",
            )
            boton.grid(
                row=2 + (numero - 1) // 4, column=(numero - 1) % 4,
                padx=6, pady=5,
            )

    def _nuevo_juego(self, modo_ejecucion: str) -> None:
        if modo_ejecucion not in MODOS_JUEGO + MODOS_EJECUCION:
            raise ValueError(f"Modo de ejecución desconocido: {modo_ejecucion}")
        if hay_partida_guardada(self.savegame):
            self._continuar_investigacion()
            return
        self._modo_nuevo = modo_juego_normalizado(modo_ejecucion)
        self.modo_juego = self._modo_nuevo
        self.modo_ejecucion = modo_ejecucion_desde_juego(self.modo_juego)
        self.savegame = crear_savegame(self.modo_juego)
        self.completados.clear()
        self.capitulos_fallidos.clear()
        self.capitulo = 1
        self.caso = casos_narrativa.crear_caso(
            1, modo_ejecucion=self.modo_ejecucion,
        )
        self._guardar_progreso()
        self.alias_seleccionado.set(ALIAS_PREDEFINIDOS[0])
        self.alias_personalizado.delete(0, "end")
        self._ocultar_pantallas()
        self.dialogo_frame.grid()

    def _cambio_alias(self, seleccion: str) -> None:
        if seleccion == "Alias personalizado":
            self.alias_personalizado.grid()
        else:
            self.alias_personalizado.grid_remove()

    def _confirmar_nuevo_juego(self) -> None:
        alias = (
            self.alias_personalizado.get().strip()
            if self.alias_seleccionado.get() == "Alias personalizado"
            else self.alias_seleccionado.get()
        )
        if not alias:
            messagebox.showwarning("Alias requerido", "Escriba un alias para la cadena de custodia.")
            return
        self.modo_juego = self._modo_nuevo
        self.modo_ejecucion = modo_ejecucion_desde_juego(self.modo_juego)
        self.savegame = crear_savegame(self.modo_juego, alias)
        self.completados.clear()
        self.capitulos_fallidos.clear()
        self.capitulo = 1
        self.savegame["activo"] = True
        self.caso = casos_narrativa.crear_caso(1, modo_ejecucion=self.modo_ejecucion)
        self._guardar_progreso()
        self._mostrar_interludio()

    def _continuar_investigacion(self) -> None:
        self.modo_juego = self.savegame["modo_juego"]
        self.modo_ejecucion = modo_ejecucion_desde_juego(self.modo_juego)
        self.capitulo = self.savegame["capitulo_actual"]
        self.completados = set(self.savegame["estrellas"])
        self.capitulos_fallidos = set(self.savegame["fallidos"])
        self.caso = casos_narrativa.crear_caso(
            self.capitulo, modo_ejecucion=self.modo_ejecucion,
        )
        if not hay_partida_guardada(self.savegame):
            self._nuevo_juego(self.modo_ejecucion)
            return
        self._mostrar_interludio()

    def _mostrar_interludio(self) -> None:
        self.investigacion_iniciada = False
        cambiar_musica_si_disponible(self, "menu_noir")
        self._ocultar_pantallas()
        alias = self.savegame["alias"] or "Investigador"
        self.transicion_visual.actualizar(
            f"capitulo_{self.capitulo:02d}", len(self.completados),
        )
        self.transicion_titulo.configure(
            text=f"{alias} · NODO {self.capitulo:02d} / {TOTAL_CAPITULOS}",
        )
        self.transicion_texto.configure(text=self.caso["intro_narrativa"])
        self.transicion_frame.grid()

    def _iniciar_nodo(self) -> None:
        self._ocultar_pantallas()
        cambiar_musica_si_disponible(self, "investigacion_noir")
        self.lateral.grid()
        self.tabs.grid()
        self.investigacion_iniciada = True
        self.estado.configure(
            text=f"RASTRO ACTIVO · {self.savegame['alias']}",
            text_color=COLOR_AMBAR,
        )
        self._renderizar_caso(reiniciar_reloj=True)
        self.inicio_capitulo = time.monotonic()
        self.after(250, self._tick)

    def _mostrar_descanso(self, mensaje: str) -> None:
        self.investigacion_iniciada = False
        cambiar_musica_si_disponible(self, "menu_noir")
        capitulo_siguiente = min(TOTAL_CAPITULOS, self.capitulo + 1)
        self.savegame["capitulo_actual"] = capitulo_siguiente
        self.savegame["capitulo"] = capitulo_siguiente
        self._guardar_progreso()
        self._ocultar_pantallas()
        self.descanso_visual.actualizar("transicion", len(self.completados))
        if self.capitulo >= TOTAL_CAPITULOS:
            texto_boton = "Evaluar estrellas"
        elif self.savegame.get("viaje_tiempo"):
            pendientes = self.savegame["pendientes_rehacer"]
            if self.capitulo not in self.savegame["estrellas"] and self.capitulo not in pendientes:
                pendientes = [*pendientes, self.capitulo]
            texto_boton = (
                f"Continuar al Capítulo {pendientes[0]}"
                if pendientes else "Evaluar estrellas"
            )
        else:
            texto_boton = f"Continuar al Capítulo {self.capitulo + 1}"
        self.boton_descanso_continuar.configure(text=texto_boton)
        resultado = self.savegame.get("resultado_actual", "")
        self.descanso_titulo.configure(
            text=(
                f"{encabezado_transicion(resultado)}\n"
                f"ESTRELLAS: {len(self.completados)} / {TOTAL_CAPITULOS}"
            ),
            text_color=COLOR_AMBAR if resultado == "limpio" else "#B83B3B",
        )
        self.descanso_texto.configure(
            text=(
                f"{narrativa_transicion(self.capitulo, resultado)}\n\n"
                f"{self.savegame['alias']}: {mensaje}"
            ),
        )
        self.descanso_frame.grid()

    def _continuar_desde_descanso(self) -> None:
        queue = self.savegame["pendientes_rehacer"]
        if self.savegame["viaje_tiempo"]:
            if self.capitulo not in self.savegame["estrellas"] and self.capitulo not in queue:
                queue.append(self.capitulo)
            if queue:
                self.capitulo = queue.pop(0)
                self.savegame["resultado_actual"] = ""
                self._cargar_caso_actual()
                self._mostrar_interludio()
                return
            self.savegame["viaje_tiempo"] = False
            self.savegame["resultado_actual"] = ""
            self._guardar_progreso()
            self._mostrar_final()
            return
        if self.capitulo >= TOTAL_CAPITULOS:
            self.savegame["resultado_actual"] = ""
            self._guardar_progreso()
            self._mostrar_final()
            return
        self.capitulo += 1
        self.savegame["resultado_actual"] = ""
        self._cargar_caso_actual()
        self._mostrar_interludio()

    def _guardar_y_volver_menu(self) -> None:
        self._guardar_progreso()
        self._mostrar_menu()

    def _cargar_caso_actual(self) -> None:
        self.savegame["capitulo"] = self.capitulo
        self.savegame["capitulo_actual"] = self.capitulo
        self.savegame["activo"] = True
        self.caso = casos_narrativa.crear_caso(
            self.capitulo, modo_ejecucion=self.modo_ejecucion,
        )
        self._guardar_progreso()

    def _mostrar_final(self) -> None:
        cambiar_musica_si_disponible(self, "menu_noir")
        self.investigacion_iniciada = False
        self._ocultar_pantallas()
        limpio = resultado_final(self.savegame) == "bueno"
        self.final_visual.actualizar(
            "final_bueno" if limpio else "final_malo",
            len(self.completados),
        )
        self.final_titulo.configure(
            text="EXPEDIENTE CERRADO · PRUEBA IRREFUTABLE" if limpio
            else "EXPEDIENTE INCOMPLETO · EL RASTRO SE PIERDE",
            text_color=COLOR_AMBAR if limpio else "#B83B3B",
        )
        if limpio:
            texto = (
                "Las catorce estrellas sostienen la cadena de custodia. "
                "El Arquitecto queda bajo custodia; ninguna cifra depende de una conjetura."
            )
            self.boton_viaje.grid_remove()
            self.boton_final_no.grid_remove()
            self.savegame["activo"] = False
        else:
            faltantes = sorted(set(range(1, TOTAL_CAPITULOS + 1)) - set(self.savegame["estrellas"]))
            texto = (
                f"Faltan pruebas en los nodos {', '.join(f'{n:02d}' for n in faltantes)}. "
                "La lluvia cubre el rastro. ¿Reconstruirá la evidencia o cerrará el expediente?"
            )
            self.boton_viaje.grid()
            self.boton_final_no.grid()
        self.final_texto.configure(text=texto)
        self.final_frame.grid()
        self._guardar_progreso()

    def _iniciar_viaje_tiempo(self) -> None:
        self.savegame["viaje_tiempo"] = True
        self.savegame["pendientes_rehacer"] = sorted(
            set(range(1, TOTAL_CAPITULOS + 1)) - set(self.savegame["estrellas"])
        )
        self.capitulo = self.savegame["pendientes_rehacer"].pop(0)
        self._cargar_caso_actual()
        self._mostrar_interludio()

    def _final_malo(self) -> None:
        self.final_visual.actualizar("final_malo", len(self.completados))
        self.final_titulo.configure(text="FINAL MALO · PRUEBAS INSUFICIENTES", text_color="#B83B3B")
        self.final_texto.configure(
            text="El Arquitecto abandona la ciudad antes del amanecer. "
                 "La cadena de custodia conserva huecos que ningún informe puede cubrir."
        )
        self.boton_viaje.grid_remove()
        self.boton_final_no.grid_remove()
        self.savegame["activo"] = False
        self.savegame["viaje_tiempo"] = False
        self._guardar_progreso()
        self.final_frame.grid()

    def _restablecer_progreso(self) -> None:
        if not messagebox.askyesno(
            "Restablecer progreso",
            "Se borrarán las estrellas y el expediente guardado. ¿Continuar?",
        ):
            return
        try:
            ARCHIVO_SAVEGAME.unlink(missing_ok=True)
        except OSError as error:
            messagebox.showerror("No se pudo restablecer", str(error))
            return
        self.savegame = crear_savegame()
        self.modo_ejecucion = "DINAMICO"
        self.modo_juego = "DINAMICO"
        self.capitulo = 1
        self.completados.clear()
        self.capitulos_fallidos.clear()
        self.caso = casos_narrativa.crear_caso(1, modo_ejecucion="DINAMICO")
        self._renderizar_caso(reiniciar_reloj=False)
        self._mostrar_menu()

    def _actualizar_insignia_modo(self) -> None:
        if not hasattr(self, "modo_insignia"):
            return
        texto = (
            "MODO APUNTES (BLOQUEADO)"
            if self.modo_juego == "OFICIAL" else "MODO DINÁMICO (BLOQUEADO)"
        )
        self.modo_insignia.configure(text=texto)

    def _renderizar_caso(self, reiniciar_reloj: bool) -> None:
        self.resuelto = self.capitulo in self.completados
        if reiniciar_reloj:
            self.fin = time.monotonic() + self.caso["duracion"]
            self.reloj.configure(
                text=f"{self.caso['duracion'] // 60:02d}:{self.caso['duracion'] % 60:02d}",
            )
        self.etiqueta_caso.configure(
            text=f"CAPÍTULO {self.capitulo:02d}\n{self.caso['titulo'].upper()}",
        )
        self.progreso_label.configure(
            text=f"ESTRELLAS: {len(self.completados)} / {TOTAL_CAPITULOS}",
        )
        self._actualizar_insignia_modo()
        self.cabecera_caso.configure(
            text=f"NODO ENCRIPTADO {self.capitulo:02d} / {TOTAL_CAPITULOS}",
        )
        self.narrativa.configure(text=self.caso["narrativa"])
        self.formato.configure(text=self.caso["formato"])
        formula = self.caso.get("formula", "")
        self.formula_label.configure(text=formula)
        if formula:
            self.formula_label.grid()
        else:
            self.formula_label.grid_remove()
        if 3 <= self.capitulo <= 8:
            self.tablas_boton.pack(side="left", padx=4)
        else:
            self.tablas_boton.pack_forget()
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()
        self.entradas.clear()
        self.caso["tabla_interactiva"]["campos"] = self.caso["campos"]
        configuracion_tablero = self.caso.get("tablero_clasificacion")
        self.tablero_clasificacion: TableroClasificacion | None = None
        self.tabla_frame.grid_rowconfigure(0, weight=1)
        self.tabla_frame.grid_rowconfigure(1, weight=0)
        if configuracion_tablero:
            self.area_trabajo = ctk.CTkScrollableFrame(
                self.tabla_frame, fg_color="transparent",
                scrollbar_button_color=COLOR_LATON,
                scrollbar_button_hover_color=COLOR_AMBAR,
            )
            self.area_trabajo.grid(row=0, column=0, sticky="nsew")
            self.area_trabajo.grid_columnconfigure(0, weight=1)
            self.tablero_clasificacion = TableroClasificacion(
                self.area_trabajo, configuracion_tablero,
            )
            self.tablero_clasificacion.grid(
                row=0, column=0, sticky="ew", padx=4, pady=(0, 6),
            )
            self.tabla = TablaInteractiva(
                self.area_trabajo, self.caso["tabla_interactiva"],
                self.entradas, scrollable=False,
            )
            self.tabla.grid(row=1, column=0, sticky="ew")
        else:
            self.area_trabajo = None
            self.tabla = TablaInteractiva(
                self.tabla_frame, self.caso["tabla_interactiva"], self.entradas,
                scrollable=True,
            )
            self.tabla.grid(row=0, column=0, sticky="nsew")
        self._renderizar_campos()
        self.mensaje.configure(text="")
        self.verificar.configure(state="disabled" if self.resuelto else "normal")
        self.victoria.grid_remove()
        actualizar_auditoria = getattr(self, "_actualizar_auditoria", None)
        if actualizar_auditoria is not None:
            actualizar_auditoria()
        if self.investigacion_iniciada:
            self._guardar_progreso()

    def _renderizar_campos(self) -> None:
        for widget in self.campos_frame.winfo_children():
            widget.destroy()
        pie = set(self.caso["tabla_interactiva"]["pie"])
        campos_pie = [
            campo for campo in self.caso["campos"] if campo["id"] in pie
        ]
        for indice, campo in enumerate(campos_pie):
            celda = ctk.CTkFrame(self.campos_frame, fg_color="transparent")
            celda.grid(
                row=indice // 4, column=indice % 4, sticky="ew", padx=5, pady=5,
            )
            ctk.CTkLabel(
                celda, text=campo["etiqueta"], anchor="w",
                text_color=COLOR_TINTA, font=ctk.CTkFont(size=13),
            ).pack(fill="x", pady=(1, 3))
            if campo["tipo"] == "selector":
                entrada = ctk.CTkComboBox(
                    celda, values=campo["opciones"], state="readonly",
                )
                entrada.set("")
            elif campo["tipo"] == "option_menu":
                entrada = ctk.CTkOptionMenu(
                    celda, values=campo["opciones"], fg_color=COLOR_ENTRADA,
                    text_color=COLOR_TEXTO_ENTRADA, button_color=COLOR_LATON,
                    button_hover_color="#A57C44",
                    dropdown_fg_color=COLOR_CARPETA,
                    dropdown_text_color=COLOR_TINTA,
                    font=ctk.CTkFont(size=14),
                )
                entrada.set("")
            else:
                entrada = ctk.CTkEntry(
                    celda,
                    placeholder_text=campo.get("placeholder_text", campo["tipo"]),
                    fg_color=COLOR_ENTRADA, text_color=COLOR_TEXTO_ENTRADA,
                    placeholder_text_color="#9E9384",
                    border_color=COLOR_BORDE_ENTRADA,
                    font=ctk.CTkFont(size=14),
                )
            entrada.pack(fill="x")
            self.entradas[campo["id"]] = entrada

    def _verificar(self) -> None:
        if self.resuelto:
            return
        respuesta = leer_valores_entrada(self.entradas)
        caso_activo = dict(self.caso)
        caso_activo["campos"] = [
            campo for campo in self.caso["campos"] if campo["id"] in respuesta
        ]
        resultado = casos_narrativa.validar_respuesta(
            caso_activo, respuesta, filas_dinamicas=self.tabla.cantidad_filas(),
        )
        if self.tablero_clasificacion is not None:
            estado_clasificacion = self.tablero_clasificacion.validar()
            if (
                estado_clasificacion["pendientes"]
                or estado_clasificacion["incorrectas"]
            ):
                resultado["correcto"] = False
                mensajes = []
                if estado_clasificacion["pendientes"]:
                    mensajes.append(
                        f"Quedan {len(estado_clasificacion['pendientes'])} fichas "
                        "en la bandeja."
                    )
                if estado_clasificacion["incorrectas"]:
                    mensajes.append(
                        f"{len(estado_clasificacion['incorrectas'])} fichas están "
                        "en una zona incorrecta."
                    )
                resultado["clasificacion_diagnostico"] = " ".join(mensajes)
        self.tabla.colorear(resultado["campos_correctos"], resultado["campos_incorrectos"])
        self.caso["respuestas"].append({
            "hora": datetime.now().isoformat(timespec="seconds"),
            "entrada": respuesta, "correcto": resultado["correcto"],
            "campos_incorrectos": resultado["campos_incorrectos"],
            "clasificacion": (
                self.tablero_clasificacion.asignaciones.copy()
                if self.tablero_clasificacion is not None else None
            ),
        })
        transcurrido = time.monotonic() - self.inicio_capitulo
        minimo = minimo_segundos_humanos(self.caso)
        if (
            resultado["correcto"] and not self.revision_activa
            and transcurrido < minimo
        ):
            alerta = {
                "capitulo": self.capitulo,
                "segundos": round(transcurrido, 2),
                "minimo": minimo,
                "fecha": datetime.now().isoformat(timespec="seconds"),
            }
            self.savegame.setdefault("alertas_antitrampa", []).append(alerta)
            self.capitulos_fallidos.add(self.capitulo)
            self.savegame["fallidos"] = sorted(self.capitulos_fallidos)
            self.savegame["resultado_actual"] = "anti_trampa"
            self._mostrar_descanso(
                f"La resolución tomó {transcurrido:.1f} s; el mínimo forense es {minimo} s. "
                "La cadena de custodia quedó bajo sospecha y no se concedió estrella.",
            )
            return
        if resultado["correcto"]:
            self.resuelto = True
            self.completados.add(self.capitulo)
            self.capitulos_fallidos.discard(self.capitulo)
            self.savegame["estrellas"] = sorted(self.completados)
            self.savegame["fallidos"] = sorted(self.capitulos_fallidos)
            self.savegame["resultado_actual"] = "limpio"
            self.fin = time.monotonic()
            self.estado.configure(text="NODO DESCIFRADO", text_color=COLOR_AMBAR)
            self.mensaje.configure(
                text="SOLUCIÓN CONFIRMADA. El rastro continúa…", text_color=COLOR_AMBAR,
            )
            self.verificar.configure(state="disabled")
            self._mostrar_descanso(
                "Las cifras coinciden. El registro queda sellado en la cadena de custodia."
            )
        elif resultado.get("clasificacion_diagnostico"):
            self.fin -= PENALIZACION_SEGUNDOS
            self.mensaje.configure(
                text=f"{resultado['clasificacion_diagnostico']} · Penalización: −25 s",
                text_color=COLOR_AMBAR,
            )
        elif resultado["formatos_invalidos"]:
            etiquetas = {
                campo["id"]: campo["etiqueta"] for campo in self.caso["campos"]
            }
            campos_invalidos = ", ".join(
                etiquetas[clave] for clave in resultado["formatos_invalidos"]
            )
            self.mensaje.configure(
                text=f"FORMATO INVÁLIDO: {campos_invalidos}. "
                f"{resultado['diagnostico']} Sin penalización de tiempo.",
                text_color=COLOR_AMBAR,
            )
        elif resultado.get("longitud_invalida"):
            self.fin -= PENALIZACION_SEGUNDOS
            self.mensaje.configure(
                text=f"{resultado['diagnostico']} · Penalización: −25 s",
                text_color=COLOR_AMBAR,
            )
        else:
            self.fin -= PENALIZACION_SEGUNDOS
            etiquetas = {
                campo["id"]: campo["etiqueta"] for campo in self.caso["campos"]
            }
            campos_erroneos = ", ".join(
                etiquetas[clave] for clave in resultado["campos_incorrectos"]
            )
            self.mensaje.configure(
                text=f"DIAGNÓSTICO: {campos_erroneos}. {resultado['diagnostico']}  "
                "·  Penalización: −25 s",
                text_color=COLOR_AMBAR,
            )
        actualizar_auditoria = getattr(self, "_actualizar_auditoria", None)
        if actualizar_auditoria is not None:
            actualizar_auditoria()
        self._guardar_progreso()

    def _mostrar_victoria(self) -> None:
        self._mostrar_final()

    def _cambiar_capitulo(self, numero: int) -> None:
        if not 1 <= numero <= TOTAL_CAPITULOS:
            return
        if numero == self.capitulo:
            return
        self.capitulo = numero
        self.savegame["capitulo_actual"] = numero
        self.savegame["capitulo"] = numero
        self.caso = casos_narrativa.crear_caso(numero, modo_ejecucion=self.modo_ejecucion)
        self.estado.configure(text="RASTRO ACTIVO")
        self._renderizar_caso(reiniciar_reloj=self.investigacion_iniciada)
        if not self.investigacion_iniciada:
            self._guardar_progreso()
            self._mostrar_interludio()
        actualizar_panel = getattr(self, "_actualizar_panel_revision", None)
        if actualizar_panel is not None:
            actualizar_panel()

    def _tick(self) -> None:
        if not self.investigacion_iniciada:
            return
        restantes = max(0, int(self.fin - time.monotonic()))
        self.reloj.configure(text=f"{restantes // 60:02d}:{restantes % 60:02d}")
        color = estado_reloj(restantes, self.caso["duracion"])
        if self.resuelto or color == "verde":
            color_hex = COLOR_AMBAR
        elif color == "amarillo":
            color_hex = COLOR_AMBAR
        else:
            color_hex = "#B83B3B" if restantes % 2 == 0 else "#5A2222"
        self.reloj.configure(text_color=color_hex)
        if restantes == 0 and not self.resuelto:
            self.investigacion_iniciada = False
            self.capitulos_fallidos.add(self.capitulo)
            self.savegame["fallidos"] = sorted(self.capitulos_fallidos)
            self.savegame["resultado_actual"] = "tiempo_agotado"
            self.caso["respuestas"].append({
                "hora": datetime.now().isoformat(timespec="seconds"),
                "correcto": False, "causa": "tiempo_agotado",
            })
            self._mostrar_descanso(
                "El reloj llegó a cero. La terminal borró el rastro; este nodo queda sin estrella."
            )
            return
        self.after(250, self._tick)

    def _mostrar_tablas_estadisticas(self) -> None:
        ventana = ctk.CTkToplevel(self)
        ventana.title("Tablas estadísticas · α = 0.05")
        ventana.geometry(
            f"{min(1050, max(700, int(self.winfo_screenwidth() * 0.72)))}x"
            f"{min(760, max(520, int(self.winfo_screenheight() * 0.76)))}",
        )
        ventana.minsize(620, 480)
        ventana.transient(self)
        ventana.grab_set()

        ventana.grid_columnconfigure(0, weight=1)
        ventana.grid_rowconfigure(1, weight=1)
        tablas = {
            "z": {
                "nombre": "Normal estándar Z",
                "archivo": "tabla_z.png",
                "titulo": "Distribución Normal Estándar Z",
                "columnas": ("α", "Z crítico"),
                "filas": (("0.05", "1.96"),),
            },
            "ks": {
                "nombre": "Kolmogorov–Smirnov",
                "archivo": "tabla_ks.png",
                "titulo": "Valores críticos Kolmogorov–Smirnov",
                "columnas": ("N", "d crítico (α=0.05)"),
                "filas": tuple(sorted(estadisticas.KS_CRITICOS_005.items())),
            },
            "chi2": {
                "nombre": "Distribución χ²",
                "archivo": "tabla_chi2.png",
                "titulo": "Distribución χ²",
                "columnas": ("gl", "χ² crítico (α=0.05)"),
                "filas": tuple(sorted(estadisticas.CHI_CUADRADO_CRITICOS_005.items())),
            },
        }
        carpeta_tablas = (
            Path(sys._MEIPASS) / "assets" / "tablas"
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().with_name("assets") / "tablas"
        )
        selector = ctk.CTkFrame(ventana, fg_color="transparent")
        selector.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        visor = tk.Canvas(
            ventana, bg=COLOR_MESA, highlightthickness=1,
            highlightbackground=COLOR_LATON,
        )
        scrollbar_y = ctk.CTkScrollbar(
            ventana, orientation="vertical", command=visor.yview,
        )
        scrollbar_x = ctk.CTkScrollbar(
            ventana, orientation="horizontal", command=visor.xview,
        )
        visor.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.grid_remove()
        scrollbar_x.grid_remove()
        visor.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(4, 0))
        scrollbar_y.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(4, 0))
        scrollbar_x.grid(row=2, column=0, sticky="ew", padx=10)
        controles = ctk.CTkFrame(ventana, fg_color="transparent")
        controles.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
        controles.grid_columnconfigure(0, weight=1)
        estado_zoom = ctk.CTkLabel(
            controles, text="100%", text_color=COLOR_TINTA,
            font=ctk.CTkFont(size=13),
        )
        estado_zoom.pack(side="left", padx=6)
        imagen_original: Image.Image | None = None
        imagen_tk: ImageTk.PhotoImage | None = None
        contenido_respaldo: ctk.CTkFrame | None = None
        zoom_actual = 1.0
        tabla_actual = "z"

        def ajustar_scrollbars_visor() -> None:
            limites = visor.bbox("all")
            if limites is None:
                scrollbar_y.grid_remove()
                scrollbar_x.grid_remove()
                return
            alto_contenido = limites[3] - limites[1]
            ancho_contenido = limites[2] - limites[0]
            if alto_contenido > visor.winfo_height() + 1:
                scrollbar_y.grid()
            else:
                scrollbar_y.grid_remove()
                visor.yview_moveto(0)
            if ancho_contenido > visor.winfo_width() + 1:
                scrollbar_x.grid()
            else:
                scrollbar_x.grid_remove()
                visor.xview_moveto(0)

        def dibujar_respaldo(tabla: dict, ruta: Path, aviso: str) -> None:
            nonlocal contenido_respaldo
            if contenido_respaldo is not None:
                visor.delete(contenido_respaldo._canvas_item)
                contenido_respaldo.destroy()
            visor.delete("imagen")
            contenido_respaldo = ctk.CTkFrame(
                visor, fg_color=COLOR_CARPETA, corner_radius=8,
            )
            contenido_respaldo._canvas_item = visor.create_window(
                16, 16, anchor="nw", window=contenido_respaldo,
            )
            contenido_respaldo.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                contenido_respaldo, text=aviso, justify="left", anchor="w",
                wraplength=800, text_color=COLOR_TINTA,
                font=ctk.CTkFont(size=14),
            ).pack(fill="x", padx=14, pady=(12, 4))
            ctk.CTkLabel(
                contenido_respaldo, text=f"Ruta requerida: {ruta}",
                justify="left", anchor="w", wraplength=800,
                text_color=COLOR_AMBAR, font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(fill="x", padx=14, pady=(0, 8))
            ctk.CTkLabel(
                contenido_respaldo, text=f"Tabla de respaldo · {tabla['titulo']}",
                anchor="w", text_color=COLOR_AMBAR,
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(fill="x", padx=14, pady=(4, 8))
            tabla_frame = ctk.CTkFrame(contenido_respaldo, fg_color=COLOR_NOTA)
            tabla_frame.pack(fill="x", padx=14, pady=(0, 14))
            for columna, encabezado in enumerate(tabla["columnas"]):
                tabla_frame.grid_columnconfigure(columna, weight=1, uniform="respaldo")
                ctk.CTkLabel(
                    tabla_frame, text=str(encabezado), text_color=COLOR_TINTA,
                    font=ctk.CTkFont(size=14, weight="bold"),
                ).grid(row=0, column=columna, sticky="ew", padx=6, pady=6)
            for indice, fila in enumerate(tabla["filas"], 1):
                for columna, valor in enumerate(fila):
                    ctk.CTkLabel(
                        tabla_frame, text=str(valor), fg_color=COLOR_NOTA,
                        corner_radius=4, text_color=COLOR_TINTA,
                        font=ctk.CTkFont(size=14),
                    ).grid(
                        row=indice, column=columna, sticky="ew", padx=4, pady=3,
                    )
            ventana.update_idletasks()
            visor.configure(scrollregion=visor.bbox("all"))
            ventana.after_idle(ajustar_scrollbars_visor)

        def mostrar_tabla(clave: str) -> None:
            nonlocal imagen_original, imagen_tk, zoom_actual, tabla_actual
            tabla_actual = clave
            zoom_actual = 1.0
            tabla = tablas[clave]
            ruta = carpeta_tablas / tabla["archivo"]
            imagen_tk = None
            imagen_original = None
            if ruta.is_file():
                try:
                    with Image.open(ruta) as imagen:
                        imagen_original = imagen.convert("RGB")
                except OSError as error:
                    print(f"No se pudo abrir la imagen {ruta}: {error}", file=sys.stderr)
                    dibujar_respaldo(
                        tabla, ruta,
                        f"No se pudo leer {tabla['archivo']}; coloca un PNG válido en la ruta indicada.",
                    )
                else:
                    if contenido_respaldo is not None:
                        visor.delete(contenido_respaldo._canvas_item)
                        contenido_respaldo.destroy()
                    visor.delete("all")
                    redibujar_imagen()
                    return
            else:
                dibujar_respaldo(
                    tabla, ruta,
                    f"Falta {tabla['archivo']}. Coloca ese archivo PNG en la ruta indicada "
                    "para mostrar la imagen; mientras tanto se muestra la tabla de respaldo.",
                )
            estado_zoom.configure(text="Respaldo")

        def redibujar_imagen() -> None:
            nonlocal imagen_tk
            if imagen_original is None:
                return
            ancho = max(1, round(imagen_original.width * zoom_actual))
            alto = max(1, round(imagen_original.height * zoom_actual))
            remuestreo = getattr(Image, "Resampling", Image).LANCZOS
            imagen_redimensionada = imagen_original.resize((ancho, alto), remuestreo)
            imagen_tk = ImageTk.PhotoImage(imagen_redimensionada, master=visor)
            visor.delete("all")
            visor.create_image(0, 0, image=imagen_tk, anchor="nw", tags="imagen")
            visor.configure(scrollregion=(0, 0, ancho, alto))
            estado_zoom.configure(text=f"{round(zoom_actual * 100)}%")
            ventana.after_idle(ajustar_scrollbars_visor)

        def ajustar_zoom(cambio: float) -> None:
            nonlocal zoom_actual
            if imagen_original is None:
                return
            zoom_actual = min(3.0, max(0.25, zoom_actual + cambio))
            redibujar_imagen()

        def desplazar(evento: tk.Event) -> str:
            if sys.platform == "darwin":
                visor.yview_scroll(-int(evento.delta), "units")
            elif sys.platform.startswith("win"):
                visor.yview_scroll(-int(evento.delta / 120), "units")
            elif getattr(evento, "num", None) in (4, 5):
                visor.yview_scroll(-1 if evento.num == 4 else 1, "units")
            return "break"

        for clave, tabla in tablas.items():
            ctk.CTkButton(
                selector, text=tabla["nombre"], width=180,
                command=lambda identificador=clave: mostrar_tabla(identificador),
                fg_color=COLOR_LATON, hover_color=COLOR_AMBAR,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=4)
        ctk.CTkButton(
            controles, text="−", width=42, command=lambda: ajustar_zoom(-0.15),
            fg_color=COLOR_LATON, hover_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="right", padx=3)
        ctk.CTkButton(
            controles, text="+", width=42, command=lambda: ajustar_zoom(0.15),
            fg_color=COLOR_LATON, hover_color=COLOR_AMBAR,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="right", padx=3)
        ctk.CTkButton(
            controles, text="Cerrar", command=ventana.destroy, width=100,
            fg_color="#55452F", hover_color=COLOR_LATON,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="right", padx=8)
        visor.bind("<MouseWheel>", desplazar)
        visor.bind("<Button-4>", desplazar)
        visor.bind("<Button-5>", desplazar)
        visor.bind(
            "<Configure>",
            lambda _evento: ventana.after_idle(ajustar_scrollbars_visor),
            add="+",
        )
        mostrar_tabla(tabla_actual)

    def _cargar_savegame(self) -> dict:
        try:
            contenido = json.loads(ARCHIVO_SAVEGAME.read_text(encoding="utf-8"))
            if not isinstance(contenido, dict) or contenido.get("version") != 1:
                raise ValueError("Versión de savegame desconocida.")
            return normalizar_savegame(contenido)
        except FileNotFoundError:
            try:
                old = json.loads(ARCHIVO_PROGRESO_ANTERIOR.read_text(encoding="utf-8"))
                if isinstance(old, dict):
                    modos_old = old.get("modos", {})
                    mode = old.get("modo_ejecucion", "DINAMICO")
                    state_old = modos_old.get(mode, {}) if isinstance(modos_old, dict) else {}
                    migrated = crear_savegame(
                        mode if mode in MODOS_EJECUCION else "DINAMICO",
                    )
                    migrated["capitulo_actual"] = state_old.get("capitulo", 1)
                    migrated["capitulo"] = migrated["capitulo_actual"]
                    migrated["estrellas"] = state_old.get("completados", [])
                    migrated["activo"] = bool(migrated["estrellas"])
                    return normalizar_savegame(migrated)
            except FileNotFoundError:
                pass
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                messagebox.showwarning(
                    "Progreso anterior no disponible",
                    f"Se iniciará un expediente nuevo: {error}",
                )
            return crear_savegame()
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            messagebox.showwarning(
                "Progreso no disponible", f"Se iniciará un expediente nuevo: {error}",
            )
            return crear_savegame()

    def _guardar_progreso(self) -> None:
        try:
            capitulo_actual = min(
                TOTAL_CAPITULOS,
                max(1, int(self.savegame.get("capitulo_actual", self.capitulo))),
            )
            self.savegame.update({
                "modo": self.modo_ejecucion,
                "modo_juego": modo_juego_normalizado(self.modo_ejecucion),
                "capitulo": capitulo_actual,
                "capitulo_actual": capitulo_actual,
                "estrellas": sorted(self.completados),
                "fallidos": sorted(self.capitulos_fallidos),
            })
            ARCHIVO_SAVEGAME.write_text(
                json.dumps(self.savegame, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            if hasattr(self, "mensaje"):
                self.mensaje.configure(
                    text=f"No se pudo guardar el progreso: {error}", text_color="#B83B3B",
                )
            else:
                messagebox.showerror("No se pudo guardar", str(error))


def leer_valores_entrada(
    entradas: dict[str, ctk.CTkEntry | ctk.CTkComboBox | ctk.CTkOptionMenu],
) -> dict[str, str]:
    return {clave: entrada.get() for clave, entrada in entradas.items()}


if __name__ == "__main__":
    ExpedienteMontecarlo().mainloop()

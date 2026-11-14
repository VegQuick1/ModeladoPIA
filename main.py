"""Interfaz de EXPEDIENTE MONTECARLO: El Rastro del Fantasma."""

from __future__ import annotations

import json
import time
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import casos_narrativa
import pruebas_estadisticas as estadisticas


ARCHIVO_SAVEGAME = Path(__file__).with_name("savegame.json")
ARCHIVO_PROGRESO_ANTERIOR = Path(__file__).with_name("progreso.json")
TOTAL_CAPITULOS = 14
PENALIZACION_SEGUNDOS = 25
MODOS_EJECUCION = ("DINAMICO", "OFICIAL_PDF")
COLOR_CORRECTO = "#36b37e"
COLOR_INCORRECTO = "#e55353"
UMBRAL_ANTITRAMPAS = 15
ALIAS_PREDEFINIDOS = ("Detective Vance", "Inspectora Mercer", "Agente K.")


def crear_savegame(modo: str = "DINAMICO", alias: str = "") -> dict:
    if modo not in MODOS_EJECUCION:
        raise ValueError(f"Modo de ejecución desconocido: {modo}")
    return {
        "version": 1,
        "alias": alias,
        "modo": modo,
        "capitulo": 1,
        "estrellas": [],
        "fallidos": [],
        "activo": False,
        "viaje_tiempo": False,
        "pendientes_rehacer": [],
    }


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
    return min(30, max(UMBRAL_ANTITRAMPAS, 10 + celdas // 2))


def resultado_final(savegame: dict) -> str:
    return "bueno" if len(savegame["estrellas"]) == TOTAL_CAPITULOS else "incompleto"


def normalizar_savegame(datos: dict) -> dict:
    modo = datos.get("modo", "DINAMICO")
    if modo not in MODOS_EJECUCION:
        modo = "DINAMICO"

    def capitulos(clave: str) -> list[int]:
        valores = datos.get(clave, [])
        if not isinstance(valores, list):
            return []
        return sorted({
            valor for valor in valores
            if isinstance(valor, int) and not isinstance(valor, bool)
            and 1 <= valor <= TOTAL_CAPITULOS
        })

    resultado = crear_savegame(modo, str(datos.get("alias", "")).strip())
    resultado.update({
        "capitulo": min(TOTAL_CAPITULOS, max(1, int(datos.get("capitulo", 1)))),
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


def estado_reloj(segundos: int) -> str:
    """Clasifica el umbral visual del reloj."""
    if segundos <= 60:
        return "rojo"
    if segundos <= 180:
        return "amarillo"
    return "verde"


def ajustar_cantidad_filas(actual: int, cambio: int, maxima: int, minimo: int = 1) -> int:
    if minimo < 0 or maxima < minimo:
        raise ValueError("Los límites de filas no son válidos.")
    return min(max(actual + cambio, minimo), maxima)


class TablaInteractiva(ctk.CTkScrollableFrame):
    def __init__(
        self, master: ctk.CTkBaseClass, configuracion: dict,
        entradas: dict[str, ctk.CTkEntry | ctk.CTkComboBox],
    ) -> None:
        super().__init__(master, fg_color="#10181e", corner_radius=8)
        self.configuracion = configuracion
        self.entradas = entradas
        self.filas_visibles: dict[str, int] = {}
        self.entradas_tabla: set[str] = set()
        self.grid_columnconfigure(0, weight=1)
        self._renderizar()

    def _renderizar(self) -> None:
        valores_entrada = {
            clave: self.entradas[clave].get()
            for clave in self.entradas_tabla if clave in self.entradas
        }
        for widget in self.winfo_children():
            widget.destroy()
        for clave in self.entradas_tabla:
            self.entradas.pop(clave, None)
        self.entradas_tabla.clear()
        fila_grid = 0
        for seccion in self.configuracion["secciones"]:
            ctk.CTkLabel(
                self, text=seccion["titulo"], anchor="w",
                text_color="#57d6c5", font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=fila_grid, column=0, sticky="ew", padx=8, pady=(10, 4))
            fila_grid += 1
            if seccion.get("visual") != "cuadrantes":
                encabezado = ctk.CTkFrame(self, fg_color="#1b2a32")
                encabezado.grid(row=fila_grid, column=0, sticky="ew", padx=6)
                for columna, nombre in enumerate(seccion["columnas"]):
                    encabezado.grid_columnconfigure(
                        columna, weight=1, uniform=seccion["id"],
                    )
                    ctk.CTkLabel(
                        encabezado, text=nombre, text_color="#aab9c1",
                        font=ctk.CTkFont(size=11, weight="bold"),
                    ).grid(row=0, column=columna, sticky="ew", padx=3, pady=5)
                fila_grid += 1
            visible = self.filas_visibles.setdefault(
                seccion["id"],
                seccion["filas_iniciales"] if seccion["dinamica"] else len(seccion["filas"]),
            )
            visible = min(visible, len(seccion["filas"]))
            self.filas_visibles[seccion["id"]] = visible
            cuerpo = (
                ctk.CTkScrollableFrame(
                    self, fg_color="transparent", orientation="vertical",
                    height=min(260, max(100, visible * 42)),
                )
                if seccion.get("scrollable", True)
                else ctk.CTkFrame(
                    self, fg_color="transparent",
                    height=min(420, max(100, visible * 42)),
                )
            )
            cuerpo.grid(row=fila_grid, column=0, sticky="ew", padx=6)
            cantidad_columnas = 2 if seccion.get("visual") == "cuadrantes" else len(
                seccion["columnas"],
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
                    bloque = ctk.CTkFrame(cuerpo, fg_color="#1b2a32", corner_radius=6)
                    bloque.grid(
                        row=fila, column=columna, sticky="nsew",
                        padx=5, pady=5,
                    )
                    ctk.CTkLabel(
                        bloque, text=etiqueta, text_color="#aab9c1",
                    ).pack(pady=(5, 2))
                    fo_celda = por_indice[indice][1]
                    campo = next(
                        item for item in self.configuracion["campos"]
                        if item["id"] == fo_celda["campo"]
                    )
                    entrada = ctk.CTkEntry(
                        bloque, placeholder_text=campo["etiqueta"],
                        border_color="#354650", justify="center",
                    )
                    if campo["id"] in valores_entrada:
                        entrada.insert(0, valores_entrada[campo["id"]])
                    entrada.pack(fill="x", padx=8, pady=(0, 5))
                    self.entradas[campo["id"]] = entrada
                    self.entradas_tabla.add(campo["id"])
                    ctk.CTkLabel(
                        bloque, text=f'FE = {por_indice[indice][2]["valor"]}',
                        text_color="#78909c",
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
                                    border_color="#354650",
                                )
                                entrada.set("")
                            else:
                                placeholder = (
                                    campo["etiqueta"]
                                    if campo["tipo"].startswith("fracción")
                                    else campo["tipo"]
                                )
                                entrada = ctk.CTkEntry(
                                    cuerpo, placeholder_text=placeholder,
                                    border_color="#354650",
                                )
                            if campo["id"] in valores_entrada:
                                valor_anterior = valores_entrada[campo["id"]]
                                if campo["tipo"] == "selector":
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
                            ctk.CTkLabel(
                                cuerpo, text=str(celda["valor"]), anchor="center",
                                fg_color="#16202a", corner_radius=4,
                                text_color="#c3d0d6",
                            ).grid(
                                row=indice, column=columna, sticky="ew", padx=3, pady=2,
                            )
            fila_grid += 1
            if seccion["dinamica"]:
                controles = ctk.CTkFrame(self, fg_color="transparent")
                controles.grid(row=fila_grid, column=0, sticky="w", padx=6, pady=(3, 8))
                ctk.CTkButton(
                    controles, text="+ Agregar fila", width=120,
                    command=lambda clave=seccion["id"]: self.agregar_fila(clave),
                ).pack(side="left", padx=3)
                ctk.CTkButton(
                    controles, text="− Quitar fila", width=120,
                    command=lambda clave=seccion["id"]: self.quitar_fila(clave),
                ).pack(side="left", padx=3)
                fila_grid += 1

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
            entrada.configure(border_color=color)

    def _seccion(self, clave: str) -> dict:
        return next(seccion for seccion in self.configuracion["secciones"]
                    if seccion["id"] == clave)


class ExpedienteMontecarlo(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("EXPEDIENTE MONTECARLO | El Rastro del Fantasma")
        self.geometry("1340x900")
        self.minsize(1000, 720)
        self.configure(fg_color="#0b1014")

        self.savegame = self._cargar_savegame()
        self.modo_ejecucion = self.savegame["modo"]
        self.capitulo = self.savegame["capitulo"]
        self.completados = set(self.savegame["estrellas"])
        self.capitulos_fallidos = set(self.savegame["fallidos"])
        self.caso = casos_narrativa.crear_caso(self.capitulo, modo_ejecucion=self.modo_ejecucion)
        self.fin = 0.0
        self.inicio_capitulo = 0.0
        self.investigacion_iniciada = False
        self.resuelto = False
        self.demo = ctk.BooleanVar(value=False)
        self.entradas: dict[str, ctk.CTkEntry | ctk.CTkComboBox] = {}
        self._modo_nuevo = self.modo_ejecucion

        self._construir_interfaz()
        self._renderizar_caso(reiniciar_reloj=False)
        self._mostrar_menu()

    def _construir_interfaz(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        encabezado = ctk.CTkFrame(self, fg_color="#111b22", corner_radius=0, height=58)
        encabezado.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(
            encabezado, text="◈ EXPEDIENTE MONTECARLO",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#57d6c5",
        ).pack(side="left", padx=22, pady=14)
        ctk.CTkLabel(
            encabezado, text="UNIDAD DE ANÁLISIS FORENSE  /  CLASIFICADO",
            font=ctk.CTkFont(size=12), text_color="#78909c",
        ).pack(side="right", padx=24)

        self.lateral = ctk.CTkFrame(self, width=278, fg_color="#10181e", corner_radius=0)
        self.lateral.grid(row=1, column=0, sticky="nsew")
        self.lateral.grid_propagate(False)
        ctk.CTkLabel(
            self.lateral, text="ARCHIVO ACTIVO", text_color="#78909c",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=(24, 6))
        ctk.CTkLabel(
            self.lateral, text="◉", font=ctk.CTkFont(size=74), text_color="#d05e5e",
        ).pack(pady=(8, 0))
        ctk.CTkLabel(
            self.lateral, text='SOSPECHOSO: "EL ARQUITECTO"',
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=8)
        self.estado = ctk.CTkLabel(
            self.lateral, text="INVESTIGACIÓN NO INICIADA",
            text_color="#78909c", font=ctk.CTkFont(size=11),
        )
        self.estado.pack()
        self.etiqueta_caso = ctk.CTkLabel(
            self.lateral, text="", wraplength=238,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.etiqueta_caso.pack(pady=(28, 8), padx=14)
        ctk.CTkLabel(
            self.lateral, text="TIEMPO RESTANTE",
            text_color="#78909c", font=ctk.CTkFont(size=11),
        ).pack(pady=(15, 2))
        self.reloj = ctk.CTkLabel(
            self.lateral, text="10:00", font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#57d6c5",
        )
        self.reloj.pack(pady=2)
        self.progreso_label = ctk.CTkLabel(self.lateral, text="", text_color="#78909c")
        self.progreso_label.pack(pady=12)
        self.modo_insignia = ctk.CTkLabel(
            self.lateral, text="", text_color="#57d6c5",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.modo_insignia.pack(pady=(4, 8))
        self.cambiar_modo_boton = ctk.CTkButton(
            self.lateral, text="", command=self._mostrar_menu,
            fg_color="#263842", hover_color="#354c58", height=34,
        )
        self.cambiar_modo_boton.pack(fill="x", padx=16, pady=(4, 8))
        self.demo_switch = ctk.CTkSwitch(
            self.lateral, text="Modo demostración docente",
            variable=self.demo, command=self._actualizar_bloqueo,
        )
        self.demo_switch.pack(side="bottom", padx=18, pady=20)

        self.tabs = ctk.CTkTabview(self, fg_color="#0b1014")
        self.tabs.grid(row=1, column=1, sticky="nsew", padx=(8, 18), pady=12)
        self.tabs.add("Expediente")
        self.tabs.add("Auditoría V&V")
        self._crear_pestana_expediente()
        self._crear_pestana_auditoria()

        self.menu_frame = ctk.CTkFrame(self, fg_color="#0b1014", corner_radius=0)
        self.menu_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=45, pady=25)
        self.menu_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.menu_frame, text="EXPEDIENTE MONTECARLO",
            text_color="#57d6c5", font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, pady=(6, 2))
        ctk.CTkLabel(
            self.menu_frame, text="EL RASTRO DEL FANTASMA",
            font=ctk.CTkFont(size=30, weight="bold"), text_color="#e6edf0",
        ).grid(row=1, column=0, pady=(0, 4))
        ctk.CTkLabel(
            self.menu_frame,
            text="La lluvia no borra los datos. Elige un expediente y conserva la cadena de custodia.",
            text_color="#aab9c1", font=ctk.CTkFont(size=14),
        ).grid(row=2, column=0, pady=(0, 12))
        self.mapa_progreso = ctk.CTkFrame(self.menu_frame, fg_color="#10181e")
        self.mapa_progreso.grid(row=3, column=0, padx=20, pady=8)
        self.botones_modo = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        self.botones_modo.grid(row=4, column=0, pady=8)
        ctk.CTkButton(
            self.botones_modo, text="Jugar Modo Apuntes (Oficial)",
            command=lambda: self._nuevo_juego("OFICIAL_PDF"), width=270,
            fg_color="#8a5924", hover_color="#a66c2c",
        ).pack(side="left", padx=7)
        ctk.CTkButton(
            self.botones_modo, text="Jugar Modo Dinámico (Semillas Aleatorias)",
            command=lambda: self._nuevo_juego("DINAMICO"), width=300,
        ).pack(side="left", padx=7)
        self.boton_continuar = ctk.CTkButton(
            self.menu_frame, text="Continuar Investigación",
            command=self._continuar_investigacion, width=300, height=40,
        )
        self.boton_continuar.grid(row=5, column=0, pady=(5, 3))
        ctk.CTkButton(
            self.menu_frame, text="Restablecer Progreso",
            command=self._restablecer_progreso, width=220,
            fg_color="#40292c", hover_color="#67353a",
        ).grid(row=6, column=0, pady=(3, 5))

        self.dialogo_frame = ctk.CTkFrame(self, fg_color="#0b1014")
        self.dialogo_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.dialogo_frame.grid_columnconfigure(0, weight=1)
        self.alias_seleccionado = ctk.StringVar(value=ALIAS_PREDEFINIDOS[0])
        ctk.CTkLabel(
            self.dialogo_frame, text="ARCHIVO DE INGRESO · 02:13 A. M.",
            text_color="#57d6c5", font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, pady=(65, 16))
        ctk.CTkLabel(
            self.dialogo_frame,
            text="— La ciudad está bajo lluvia, detective. El expediente no espera.\nElija el nombre que quedará en la cadena de custodia.",
            justify="center", text_color="#d5e0e5", font=ctk.CTkFont(size=17),
        ).grid(row=1, column=0, pady=12)
        self.alias_menu = ctk.CTkComboBox(
            self.dialogo_frame, values=list(ALIAS_PREDEFINIDOS) + ["Alias personalizado"],
            variable=self.alias_seleccionado, width=310, command=self._cambio_alias,
        )
        self.alias_menu.grid(row=2, column=0, pady=8)
        self.alias_personalizado = ctk.CTkEntry(
            self.dialogo_frame, placeholder_text="Escriba su alias",
            width=310,
        )
        self.alias_personalizado.grid(row=3, column=0, pady=8)
        self.alias_personalizado.grid_remove()
        ctk.CTkButton(
            self.dialogo_frame, text="Entrar al expediente",
            command=self._confirmar_nuevo_juego, width=260,
        ).grid(row=4, column=0, pady=(18, 8))
        ctk.CTkButton(
            self.dialogo_frame, text="Volver al menú",
            command=self._mostrar_menu, width=180, fg_color="#263842",
        ).grid(row=5, column=0, pady=5)

        self.transicion_frame = ctk.CTkFrame(self, fg_color="#0b1014")
        self.transicion_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.transicion_frame.grid_columnconfigure(0, weight=1)
        self.transicion_titulo = ctk.CTkLabel(
            self.transicion_frame, text="", text_color="#57d6c5",
            font=ctk.CTkFont(size=19, weight="bold"),
        )
        self.transicion_titulo.grid(row=0, column=0, pady=(70, 18))
        self.transicion_texto = ctk.CTkLabel(
            self.transicion_frame, text="", justify="center", wraplength=760,
            text_color="#d5e0e5", font=ctk.CTkFont(size=17),
        )
        self.transicion_texto.grid(row=1, column=0, padx=30, pady=14)
        self.boton_iniciar_nodo = ctk.CTkButton(
            self.transicion_frame, text="Iniciar Nodo",
            command=self._iniciar_nodo, width=240,
        )
        self.boton_iniciar_nodo.grid(row=2, column=0, pady=(25, 8))
        ctk.CTkButton(
            self.transicion_frame, text="Volver al Menú Principal",
            command=self._mostrar_menu, width=240, fg_color="#263842",
        ).grid(row=3, column=0, pady=6)

        self.descanso_frame = ctk.CTkFrame(self, fg_color="#0b1014")
        self.descanso_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.descanso_frame.grid_columnconfigure(0, weight=1)
        self.descanso_titulo = ctk.CTkLabel(
            self.descanso_frame, text="", text_color="#57d6c5",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.descanso_titulo.grid(row=0, column=0, pady=(65, 18))
        self.descanso_texto = ctk.CTkLabel(
            self.descanso_frame, text="", wraplength=760, justify="center",
            text_color="#d5e0e5", font=ctk.CTkFont(size=17),
        )
        self.descanso_texto.grid(row=1, column=0, padx=30, pady=12)
        self.boton_descanso_continuar = ctk.CTkButton(
            self.descanso_frame, text="Continuar al siguiente capítulo",
            command=self._continuar_desde_descanso, width=310,
        )
        self.boton_descanso_continuar.grid(row=2, column=0, pady=(20, 7))
        ctk.CTkButton(
            self.descanso_frame, text="Guardar y volver al Menú Principal",
            command=self._mostrar_menu, width=310, fg_color="#263842",
        ).grid(row=3, column=0, pady=7)

        self.final_frame = ctk.CTkFrame(self, fg_color="#0b1014")
        self.final_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=50, pady=50)
        self.final_frame.grid_columnconfigure(0, weight=1)
        self.final_titulo = ctk.CTkLabel(
            self.final_frame, text="", text_color="#57d6c5",
            font=ctk.CTkFont(size=25, weight="bold"),
        )
        self.final_titulo.grid(row=0, column=0, pady=(55, 16))
        self.final_texto = ctk.CTkLabel(
            self.final_frame, text="", wraplength=800, justify="center",
            text_color="#d5e0e5", font=ctk.CTkFont(size=17),
        )
        self.final_texto.grid(row=1, column=0, padx=30, pady=15)
        self.boton_viaje = ctk.CTkButton(
            self.final_frame, text="Volver en el tiempo: reconstruir nodos sin estrella",
            command=self._iniciar_viaje_tiempo, width=440,
        )
        self.boton_viaje.grid(row=2, column=0, pady=(20, 8))
        self.boton_final_no = ctk.CTkButton(
            self.final_frame, text="No. Cerrar el expediente",
            command=self._final_malo, width=300, fg_color="#40292c",
        )
        self.boton_final_no.grid(row=3, column=0, pady=7)
        ctk.CTkButton(
            self.final_frame, text="Volver al Menú Principal",
            command=self._mostrar_menu, width=220, fg_color="#263842",
        ).grid(row=4, column=0, pady=12)

        for pantalla in (self.dialogo_frame, self.transicion_frame, self.descanso_frame, self.final_frame):
            pantalla.grid_remove()

    def _crear_pestana_expediente(self) -> None:
        tab = self.tabs.tab("Expediente")
        tab.grid_columnconfigure(0, weight=4)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        self.cabecera_caso = ctk.CTkLabel(
            tab, text="TRANSMISIÓN INTERCEPTADA",
            text_color="#57d6c5", font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.cabecera_caso.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 2))
        self.narrativa = ctk.CTkLabel(
            tab, text="", justify="left", anchor="nw", wraplength=920,
            font=ctk.CTkFont(size=15), text_color="#d5e0e5",
        )
        self.narrativa.grid(row=1, column=0, sticky="ew", padx=14, pady=10)
        self.formula_label = ctk.CTkLabel(
            tab, text="", justify="left", anchor="w", wraplength=250,
            fg_color="#16202a", corner_radius=8, text_color="#f0b35a",
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.formula_label.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=10)
        self.formula_label.grid_remove()
        self.tabla_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.tabla_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=12, pady=8)
        self.tabla_frame.grid_columnconfigure(0, weight=1)
        self.tabla_frame.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(tab, fg_color="#111b22")
        panel.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=10)
        panel.grid_columnconfigure(0, weight=1)
        self.formato = ctk.CTkLabel(
            panel, text="", anchor="w", wraplength=900, text_color="#aab9c1",
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
        )
        self.verificar.pack(side="left", padx=4)
        self.ver_tabla = ctk.CTkButton(
            controles, text="Ver tabla completa / auditoría",
            command=self._abrir_auditoria,
        )
        self.ver_tabla.pack(side="left", padx=4)
        self.tablas_boton = ctk.CTkButton(
            controles, text="Ver Tablas Estadísticas (Z / KS / χ²)",
            command=self._mostrar_tablas_estadisticas,
        )
        self.mensaje = ctk.CTkLabel(
            panel, text="", anchor="w", wraplength=900,
        )
        self.mensaje.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 6))

        navegacion = ctk.CTkFrame(panel, fg_color="transparent")
        navegacion.grid(row=4, column=0, sticky="ew", padx=8, pady=(2, 10))
        self.anterior = ctk.CTkButton(
            navegacion, text="← Anterior", width=120, command=lambda: self._navegar(-1),
        )
        self.anterior.pack(side="left", padx=4)
        self.selector_capitulo = ctk.CTkComboBox(
            navegacion, values=[f"{i:02d}" for i in range(1, TOTAL_CAPITULOS + 1)],
            width=100, state="readonly", command=self._seleccion_capitulo,
        )
        self.selector_capitulo.pack(side="left", padx=4)
        self.siguiente = ctk.CTkButton(
            navegacion, text="Siguiente →", width=120, command=lambda: self._navegar(1),
        )
        self.siguiente.pack(side="left", padx=4)

        self.victoria = ctk.CTkFrame(tab, fg_color="#101c21", corner_radius=18)
        self.victoria.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=35, pady=35)
        self.victoria.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.victoria, text="INVESTIGACIÓN COMPLETADA",
            font=ctk.CTkFont(size=28, weight="bold"), text_color="#57d6c5",
        ).grid(row=0, column=0, pady=(90, 24))
        ctk.CTkLabel(
            self.victoria, text="EL ARQUITECTO HA SIDO LOCALIZADO",
            font=ctk.CTkFont(size=19), text_color="#e6edf0",
        ).grid(row=1, column=0, pady=12)
        self.coordenadas_label = ctk.CTkLabel(
            self.victoria, text="", font=ctk.CTkFont(size=25, weight="bold"),
            text_color="#f0b35a",
        )
        self.coordenadas_label.grid(row=2, column=0, pady=24)
        ctk.CTkLabel(
            self.victoria, text="14 NODOS DESCIFRADOS · EVIDENCIA GUARDADA",
            text_color="#78909c",
        ).grid(row=3, column=0, pady=12)
        self.victoria.grid_remove()

    def _crear_pestana_auditoria(self) -> None:
        tab = self.tabs.tab("Auditoría V&V")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            tab, text="AUDITORÍA FORENSE · VERIFICACIÓN Y VALIDACIÓN DEL MODELO",
            text_color="#57d6c5", font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=12)
        self.auditoria_texto = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#10181e", text_color="#d5e0e5",
        )
        self.auditoria_texto.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        botones = ctk.CTkFrame(tab, fg_color="transparent")
        botones.grid(row=2, column=0, sticky="e", padx=10, pady=10)
        ctk.CTkButton(
            botones, text="Exportar evidencia JSON",
            command=lambda: self._exportar("json"),
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            botones, text="Exportar evidencia TXT",
            command=lambda: self._exportar("txt"),
        ).pack(side="left", padx=5)

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
        self._ocultar_pantallas()
        self._actualizar_mapa_progreso()
        self.boton_continuar.configure(
            state="normal" if self.savegame["activo"] else "disabled",
        )
        self.menu_frame.grid()

    def _actualizar_mapa_progreso(self) -> None:
        for widget in self.mapa_progreso.winfo_children():
            widget.destroy()
        self.mapa_progreso.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.mapa_progreso, text=f"INVESTIGADOR: {self.savegame['alias'] or 'SIN IDENTIFICAR'}",
            text_color="#f0b35a", font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8, 4))
        for numero in range(1, TOTAL_CAPITULOS + 1):
            estado = estado_nodo(numero, self.savegame)
            texto = f"{estado} NODO {numero:02d}"
            color = "#243a31" if estado == "★" else "#3a2528" if estado == "⚠" else "#1a252c"
            boton = ctk.CTkButton(
                self.mapa_progreso, text=texto, width=170, height=34,
                fg_color=color, hover_color="#354c58", state="disabled",
            )
            boton.grid(
                row=1 + (numero - 1) // 4, column=(numero - 1) % 4,
                padx=6, pady=5,
            )

    def _nuevo_juego(self, modo_ejecucion: str) -> None:
        if modo_ejecucion not in MODOS_EJECUCION:
            raise ValueError(f"Modo de ejecución desconocido: {modo_ejecucion}")
        self._modo_nuevo = modo_ejecucion
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
        self.savegame = crear_savegame(self._modo_nuevo, alias)
        self.modo_ejecucion = self._modo_nuevo
        self.completados.clear()
        self.capitulos_fallidos.clear()
        self.capitulo = 1
        self.savegame["activo"] = True
        self.caso = casos_narrativa.crear_caso(1, modo_ejecucion=self.modo_ejecucion)
        self._guardar_progreso()
        self._mostrar_interludio()

    def _continuar_investigacion(self) -> None:
        self.modo_ejecucion = self.savegame["modo"]
        self.capitulo = self.savegame["capitulo"]
        self.completados = set(self.savegame["estrellas"])
        self.capitulos_fallidos = set(self.savegame["fallidos"])
        self.caso = casos_narrativa.crear_caso(
            self.capitulo, modo_ejecucion=self.modo_ejecucion,
        )
        if not self.savegame["alias"]:
            self._nuevo_juego(self.modo_ejecucion)
            return
        self._mostrar_interludio()

    def _mostrar_interludio(self) -> None:
        self.investigacion_iniciada = False
        self._ocultar_pantallas()
        textos = {
            1: "La primera terminal guarda una operación modular. Reconstruya cada rastro sin saltarse la repetición.",
            2: "El flujo cae sobre una potencia de dos. El período esperado deja una marca al cuarto del módulo.",
            3: "Diez señales esperan bajo la lluvia. Su centro y su dispersión dirán si la secuencia es confiable.",
            4: "Ordene las marcas de tiempo; la mayor distancia entre observación y proporción será la pista.",
            5: "Cuatro intervalos reparten las llegadas. Compare lo observado con lo que el modelo esperaba.",
            6: "Los dígitos repetidos dejan huecos. Agrupe las frecuencias antes de emitir dictamen.",
            7: "Las señales llegan en parejas. Ubíquelas a cada lado del eje y cuente los cuadrantes.",
            8: "Cinco decimales, siete posibles huellas. Clasifique las manos antes de cerrar el expediente.",
            9: "El tiempo entre llegadas no es uniforme; una transformación logarítmica revela su medida.",
            10: "Cuatro envases pasan por una línea entre dos límites conocidos. Interpole cada marca.",
            11: "El mensaje cambia de regla al cruzar la mitad del intervalo. La frontera importa.",
            12: "Las probabilidades se acumulan en silencio hasta que la certeza roce el 99.99%.",
            13: "La caja no siempre está libre cuando llega el siguiente cliente. Reconstruya la espera.",
            14: "La apuesta crece después de cada pérdida. El saldo y la secuencia decidirán el cierre.",
        }
        alias = self.savegame["alias"] or "Investigador"
        self.transicion_titulo.configure(
            text=f"{alias} · NODO {self.capitulo:02d} / {TOTAL_CAPITULOS}",
        )
        self.transicion_texto.configure(text=textos[self.capitulo])
        self.transicion_frame.grid()

    def _iniciar_nodo(self) -> None:
        self._ocultar_pantallas()
        self.lateral.grid()
        self.tabs.grid()
        self.investigacion_iniciada = True
        self.estado.configure(
            text=f"RASTRO ACTIVO · {self.savegame['alias']}",
            text_color="#57d6c5",
        )
        self._renderizar_caso(reiniciar_reloj=True)
        self.inicio_capitulo = time.monotonic()
        self.after(250, self._tick)

    def _mostrar_descanso(self, mensaje: str, marcado: bool = False) -> None:
        self.investigacion_iniciada = False
        self._ocultar_pantallas()
        if self.savegame.get("resultado_actual") == "tiempo_agotado":
            self.boton_descanso_continuar.configure(
                text="Generar nueva semilla y reintentar",
            )
        else:
            self.boton_descanso_continuar.configure(
                text="Continuar al siguiente capítulo",
            )
        estado = "EVIDENCIA BAJO SOSPECHA" if marcado else (
            "NODO ASEGURADO" if self.capitulo in self.completados else "RASTRO INTERRUMPIDO"
        )
        self.descanso_titulo.configure(text=f"{estado} · CAPÍTULO {self.capitulo:02d}")
        self.descanso_texto.configure(
            text=f"— {self.savegame['alias']}: {mensaje}",
        )
        self.descanso_frame.grid()
        self._guardar_progreso()

    def _continuar_desde_descanso(self) -> None:
        queue = self.savegame["pendientes_rehacer"]
        if self.savegame.get("resultado_actual") == "tiempo_agotado":
            self.caso = casos_narrativa.crear_caso(
                self.capitulo, modo_ejecucion=self.modo_ejecucion,
            )
            self.savegame["resultado_actual"] = ""
            self.savegame["capitulo"] = self.capitulo
            self._guardar_progreso()
            self._mostrar_interludio()
            return
        if self.savegame["viaje_tiempo"]:
            if self.capitulo not in self.savegame["estrellas"] and self.capitulo not in queue:
                queue.append(self.capitulo)
            if queue:
                self.capitulo = queue.pop(0)
                self._cargar_caso_actual()
                self._mostrar_interludio()
                return
            self.savegame["viaje_tiempo"] = False
            self._mostrar_final()
            return
        if self.capitulo >= TOTAL_CAPITULOS:
            self._mostrar_final()
            return
        self.capitulo += 1
        self._cargar_caso_actual()
        self._mostrar_interludio()

    def _cargar_caso_actual(self) -> None:
        self.savegame["capitulo"] = self.capitulo
        self.savegame["activo"] = True
        self.caso = casos_narrativa.crear_caso(
            self.capitulo, modo_ejecucion=self.modo_ejecucion,
        )
        self._guardar_progreso()

    def _mostrar_final(self) -> None:
        self.investigacion_iniciada = False
        self._ocultar_pantallas()
        limpio = resultado_final(self.savegame) == "bueno"
        self.final_titulo.configure(
            text="EXPEDIENTE CERRADO · PRUEBA IRREFUTABLE" if limpio
            else "EXPEDIENTE INCOMPLETO · EL RASTRO SE PIERDE",
            text_color="#57d6c5" if limpio else "#e55353",
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
        self.final_titulo.configure(text="FINAL MALO · PRUEBAS INSUFICIENTES", text_color="#e55353")
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
            "MODO: OFICIAL LIBRETA / PDF"
            if self.modo_ejecucion == "OFICIAL_PDF" else "MODO: DINÁMICO"
        )
        self.modo_insignia.configure(text=texto)
        boton = (
            "Menú Principal"
        )
        self.cambiar_modo_boton.configure(text=boton)

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
        self.tabla = TablaInteractiva(
            self.tabla_frame, self.caso["tabla_interactiva"], self.entradas,
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self._renderizar_campos()
        self.mensaje.configure(text="")
        self.selector_capitulo.set(f"{self.capitulo:02d}")
        self.verificar.configure(state="disabled" if self.resuelto else "normal")
        self.victoria.grid_remove()
        self._actualizar_navegacion()
        self._actualizar_bloqueo()
        self._actualizar_auditoria()
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
                text_color="#aab9c1", font=ctk.CTkFont(size=12),
            ).pack(fill="x", pady=(1, 3))
            if campo["tipo"] == "selector":
                entrada = ctk.CTkComboBox(
                    celda, values=campo["opciones"], state="readonly",
                )
                entrada.set("")
            else:
                entrada = ctk.CTkEntry(celda, placeholder_text=campo["tipo"])
            entrada.pack(fill="x")
            self.entradas[campo["id"]] = entrada

    def _verificar(self) -> None:
        if self.resuelto:
            return
        respuesta = {clave: entrada.get() for clave, entrada in self.entradas.items()}
        caso_activo = dict(self.caso)
        caso_activo["campos"] = [
            campo for campo in self.caso["campos"] if campo["id"] in respuesta
        ]
        resultado = casos_narrativa.validar_respuesta(
            caso_activo, respuesta, filas_dinamicas=self.tabla.cantidad_filas(),
        )
        self.tabla.colorear(resultado["campos_correctos"], resultado["campos_incorrectos"])
        self.caso["respuestas"].append({
            "hora": datetime.now().isoformat(timespec="seconds"),
            "entrada": respuesta, "correcto": resultado["correcto"],
            "campos_incorrectos": resultado["campos_incorrectos"],
        })
        transcurrido = time.monotonic() - self.inicio_capitulo
        minimo = minimo_segundos_humanos(self.caso)
        if (
            resultado["correcto"] and not self.demo.get()
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
                marcado=True,
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
            self.estado.configure(text="NODO DESCIFRADO", text_color="#57d6c5")
            self.mensaje.configure(
                text="SOLUCIÓN CONFIRMADA. El rastro continúa…", text_color="#57d6c5",
            )
            self.verificar.configure(state="disabled")
            self._mostrar_descanso(
                "Las cifras coinciden. El registro queda sellado en la cadena de custodia."
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
                text_color="#f0b35a",
            )
        elif resultado.get("longitud_invalida"):
            self.fin -= PENALIZACION_SEGUNDOS
            self.mensaje.configure(
                text=f"{resultado['diagnostico']} · Penalización: −25 s",
                text_color="#f0b35a",
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
                text_color="#f0b35a",
            )
        self._actualizar_navegacion()
        self._actualizar_auditoria()
        self._guardar_progreso()

    def _mostrar_victoria(self) -> None:
        self._mostrar_final()

    def _navegar(self, desplazamiento: int) -> None:
        destino = self.capitulo + desplazamiento
        if not 1 <= destino <= TOTAL_CAPITULOS:
            return
        if not self.demo.get() and desplazamiento > 0 and not self.resuelto:
            return
        if not self.demo.get() and destino > max(self.completados, default=0) + 1:
            return
        self._cambiar_capitulo(destino)

    def _seleccion_capitulo(self, seleccion: str) -> None:
        if not self.demo.get():
            return
        self._cambiar_capitulo(int(seleccion))

    def _cambiar_capitulo(self, numero: int) -> None:
        if numero == self.capitulo:
            return
        self.capitulo = numero
        self.caso = casos_narrativa.crear_caso(numero, modo_ejecucion=self.modo_ejecucion)
        self.estado.configure(text="MODO DEMOSTRACIÓN" if self.demo.get() else "RASTRO ACTIVO")
        self._renderizar_caso(reiniciar_reloj=True)
        self.tabs.set("Expediente")

    def _actualizar_navegacion(self) -> None:
        self.anterior.configure(state="normal" if self.capitulo > 1 else "disabled")
        puede_avanzar = (
            self.capitulo < TOTAL_CAPITULOS
            and (self.demo.get() or self.resuelto)
        )
        self.siguiente.configure(state="normal" if puede_avanzar else "disabled")
        self.selector_capitulo.configure(
            state="readonly" if self.demo.get() else "disabled",
        )

    def _tick(self) -> None:
        if not self.investigacion_iniciada:
            return
        restantes = max(0, int(self.fin - time.monotonic()))
        self.reloj.configure(text=f"{restantes // 60:02d}:{restantes % 60:02d}")
        color = estado_reloj(restantes)
        if self.resuelto or color == "verde":
            color_hex = "#57d6c5"
        elif color == "amarillo":
            color_hex = "#f0b35a"
        else:
            color_hex = "#ff5555" if restantes % 2 == 0 else "#701f25"
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

    def _actualizar_bloqueo(self) -> None:
        if not hasattr(self, "ver_tabla"):
            return
        disponible = self.resuelto or self.demo.get()
        self.ver_tabla.configure(state="normal" if disponible else "disabled")
        self._actualizar_navegacion()

    def _abrir_auditoria(self) -> None:
        if self.resuelto or self.demo.get():
            self.tabs.set("Auditoría V&V")

    def _mostrar_tablas_estadisticas(self) -> None:
        ventana = ctk.CTkToplevel(self)
        ventana.title("Tablas estadísticas · α = 0.05")
        ventana.geometry("620x650")
        ventana.transient(self)
        ventana.grab_set()

        contenido = ctk.CTkScrollableFrame(ventana, fg_color="#10181e")
        contenido.pack(fill="both", expand=True, padx=14, pady=14)

        def agregar_tabla(titulo: str, columnas: tuple[str, ...], filas: list[tuple]) -> None:
            ctk.CTkLabel(
                contenido, text=titulo, anchor="w", text_color="#57d6c5",
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(fill="x", padx=8, pady=(12, 4))
            tabla = ctk.CTkFrame(contenido, fg_color="#17232a")
            tabla.pack(fill="x", padx=8, pady=3)
            for columna, encabezado in enumerate(columnas):
                tabla.grid_columnconfigure(columna, weight=1)
                ctk.CTkLabel(
                    tabla, text=encabezado, text_color="#aab9c1",
                    font=ctk.CTkFont(size=11, weight="bold"),
                ).grid(row=0, column=columna, sticky="ew", padx=5, pady=5)
            for indice, fila in enumerate(filas, 1):
                for columna, valor in enumerate(fila):
                    ctk.CTkLabel(
                        tabla, text=str(valor), fg_color="#16202a",
                        corner_radius=4, text_color="#d5e0e5",
                    ).grid(
                        row=indice, column=columna, sticky="ew", padx=3, pady=2,
                    )

        agregar_tabla(
            "Prueba de promedios",
            ("α", "Z crítico"),
            (("0.05", "1.96"),),
        )
        agregar_tabla(
            "Kolmogorov–Smirnov",
            ("N", "d crítico (α=0.05)"),
            tuple(sorted(estadisticas.KS_CRITICOS_005.items())),
        )
        agregar_tabla(
            "Chi-cuadrado",
            ("gl", "χ² crítico (α=0.05)"),
            tuple(sorted(estadisticas.CHI_CUADRADO_CRITICOS_005.items())),
        )
        ctk.CTkButton(
            contenido, text="Cerrar", command=ventana.destroy, width=120,
        ).pack(pady=14)

    def _actualizar_auditoria(self) -> None:
        mostrar_solucion = self.resuelto or self.demo.get()
        documento = construir_documento_auditoria(self.caso, mostrar_solucion)
        self._documento_auditoria = documento
        self.auditoria_texto.configure(state="normal")
        self.auditoria_texto.delete("1.0", "end")
        self.auditoria_texto.insert(
            "1.0", json.dumps(documento, ensure_ascii=False, indent=2),
        )
        self.auditoria_texto.configure(state="disabled")

    def _exportar(self, formato: str) -> None:
        if not (self.resuelto or self.demo.get()):
            return
        extension = ".json" if formato == "json" else ".txt"
        destino = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(f"Archivo {formato.upper()}", f"*{extension}")],
            initialfile=f"auditoria_capitulo_{self.capitulo}{extension}",
        )
        if not destino:
            return
        contenido = json.dumps(self._documento_auditoria, ensure_ascii=False, indent=2)
        if formato == "txt":
            contenido = (
                "AUDITORÍA FORENSE — EXPEDIENTE MONTECARLO\n"
                f"Capítulo: {self.capitulo} — {self.caso['titulo']}\n"
                f"Semilla: {self.caso['semilla']}\n\n{contenido}"
            )
        try:
            Path(destino).write_text(contenido, encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Error de exportación", str(error))
            return
        messagebox.showinfo("Exportación completa", f"Reporte guardado en:\n{destino}")

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
                    migrated["capitulo"] = state_old.get("capitulo", 1)
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
            self.savegame.update({
                "modo": self.modo_ejecucion,
                "capitulo": self.capitulo,
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
                    text=f"No se pudo guardar el progreso: {error}", text_color="#ff5555",
                )
            else:
                messagebox.showerror("No se pudo guardar", str(error))


def _contar_muestra(caso: dict) -> int | None:
    auditoria = caso["auditoria"]
    for clave in ("tamano_muestra", "n_digitos", "n_parejas", "n_huecos"):
        if clave in auditoria:
            return auditoria[clave]
    for clave in ("valores_R", "digitos", "tabla_generada", "corridas_R", "filas"):
        if clave in auditoria:
            valor = auditoria[clave]
            return sum(map(len, valor)) if clave == "corridas_R" else len(valor)
    if "exitos" in auditoria:
        return auditoria["total"]
    return None


def construir_documento_auditoria(caso: dict, mostrar_solucion: bool = True) -> dict:
    auditoria = caso["auditoria"]
    return {
        "proyecto": "EXPEDIENTE MONTECARLO: El Rastro del Fantasma",
        "modo_ejecucion": caso["modo_ejecucion"],
        "origen_problema": caso["origen_problema"],
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "capitulo": caso["numero"], "total_capitulos": TOTAL_CAPITULOS,
        "titulo": caso["titulo"], "semilla": caso["semilla"],
        "duracion_segundos": casos_narrativa.DURACION_CAPITULO,
        "tamano_muestra": _contar_muestra(caso),
        "hipotesis": {
            "H0": auditoria.get("hipotesis", "Según el método estadístico del capítulo"),
            "alpha": auditoria.get("alpha", 0.05),
            "resultados_pruebas": _extraer_resultados_pruebas(auditoria),
        },
        "transitorio_vs_estable": _analisis_transitorio_estable(caso),
        "tabla_reto": caso["tabla"],
        "motor_y_resultados": auditoria,
        "solucion": caso["esperado"] if mostrar_solucion else "Bloqueada hasta resolver el capítulo.",
        "intentos": caso["respuestas"],
        "verificacion": (
            "Resultados calculados por los motores matemáticos a partir de los datos "
            "del preset oficial."
            if caso["modo_ejecucion"] == "OFICIAL_PDF" else
            "Tablas y respuestas calculadas dinámicamente a partir de la semilla."
        ),
    }


def _extraer_resultados_pruebas(valor: dict) -> dict:
    resultados = {}
    for clave, contenido in valor.items():
        if isinstance(contenido, dict):
            if "acepta" in contenido:
                resultados[clave] = contenido
            else:
                resultados.update(_extraer_resultados_pruebas(contenido))
    return resultados


def _analisis_transitorio_estable(caso: dict) -> dict:
    auditoria = caso["auditoria"]
    if "filas" in auditoria and auditoria["filas"] and "Tiempo espera en sistema" in auditoria["filas"][0]:
        muestra = [fila["Tiempo espera en sistema"] for fila in auditoria["filas"]]
    elif "corridas" in auditoria:
        muestra = [corrida["saldo_final"] for corrida in auditoria["corridas"]]
    elif "tabla_generada" in auditoria:
        muestra = [
            float(Fraction(fila["R"])) for fila in auditoria["tabla_generada"]
        ]
    else:
        return {
            "estado": "No aplica: el método no genera evolución de estados en el tiempo.",
            "metodo": "No se infiere estacionariedad para muestras independientes.",
            "n": 0,
        }
    corte = max(1, len(muestra) // 10)
    inicial, restante = muestra[:corte], muestra[corte:]
    return {
        "estado": "Comparación descriptiva, no prueba formal de estacionariedad.",
        "metodo": "Primer 10% como transitorio aproximado y segmento restante como candidato estable.",
        "n": len(muestra),
        "transitorio": {"n": len(inicial), "media": sum(inicial) / len(inicial)},
        "segmento_restante": {
            "n": len(restante),
            "media": sum(restante) / len(restante) if restante else None,
        },
    }


if __name__ == "__main__":
    ExpedienteMontecarlo().mainloop()

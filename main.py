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


ARCHIVO_PROGRESO = Path(__file__).with_name("progreso.json")
TOTAL_CAPITULOS = 14
PENALIZACION_SEGUNDOS = 25
MODOS_EJECUCION = ("DINAMICO", "OFICIAL_PDF")
COLOR_CORRECTO = "#36b37e"
COLOR_INCORRECTO = "#e55353"


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
            encabezado = ctk.CTkFrame(self, fg_color="#1b2a32")
            encabezado.grid(row=fila_grid, column=0, sticky="ew", padx=6)
            for columna, nombre in enumerate(seccion["columnas"]):
                encabezado.grid_columnconfigure(columna, weight=1, uniform=seccion["id"])
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
            cuerpo = ctk.CTkScrollableFrame(
                self, fg_color="transparent", orientation="vertical",
                height=min(260, max(100, visible * 42)),
            )
            cuerpo.grid(row=fila_grid, column=0, sticky="ew", padx=6)
            for columna in range(len(seccion["columnas"])):
                cuerpo.grid_columnconfigure(columna, weight=1, uniform=seccion["id"])
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
                                campo["etiqueta"] if campo["tipo"].startswith("fracción")
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

        progreso = self._cargar_progreso()
        self.modo_ejecucion = progreso["modo_ejecucion"]
        self.progreso_modos = progreso["modos"]
        estado_modo = self.progreso_modos[self.modo_ejecucion]
        self.capitulo = estado_modo["capitulo"]
        self.completados = set(estado_modo["completados"])
        self.caso = casos_narrativa.crear_caso(
            self.capitulo, estado_modo.get("semilla"), self.modo_ejecucion,
        )
        self.fin = 0.0
        self.investigacion_iniciada = False
        self.resuelto = self.capitulo in self.completados
        self.demo = ctk.BooleanVar(value=False)
        self.entradas: dict[str, ctk.CTkEntry | ctk.CTkComboBox] = {}

        self._construir_interfaz()
        self._renderizar_caso(reiniciar_reloj=False)
        self._mostrar_prologo()

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
            self.lateral, text="", command=self._alternar_modo,
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

        self.prologo = ctk.CTkFrame(self, fg_color="#0b1014", corner_radius=0)
        self.prologo.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=45, pady=36)
        self.prologo.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.prologo, text="EXPEDIENTE MONTECARLO",
            text_color="#57d6c5", font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, pady=(42, 16))
        ctk.CTkLabel(
            self.prologo, text="EL RASTRO DEL FANTASMA",
            font=ctk.CTkFont(size=34, weight="bold"), text_color="#e6edf0",
        ).grid(row=1, column=0, pady=(0, 24))
        historia = (
            "El Arquitecto, un ciberdelincuente que ha evadido a las autoridades, "
            "fragmentó las coordenadas de su escondite en 14 nodos encriptados dentro "
            "de una red de servidores.\n\n"
            "Cada nodo está protegido por un modelo estocástico o una prueba estadística "
            "que dejó como firma. Como analista forense, reconstruirás las secuencias, "
            "verificarás los modelos y descifrarás cada fragmento de la pista.\n\n"
            "La investigación consta de 14 capítulos secuenciales. Cada expediente "
            "dispone de 10 minutos. Una respuesta incorrecta consume 25 segundos; "
            "si el reloj llega a cero, el nodo genera datos nuevos."
        )
        ctk.CTkLabel(
            self.prologo, text=historia, justify="left", anchor="center",
            wraplength=860, font=ctk.CTkFont(size=18), text_color="#c3d0d6",
        ).grid(row=2, column=0, padx=35, pady=12)
        self.iniciar_dinamico = ctk.CTkButton(
            self.prologo, text="Iniciar Modo Dinámico (Semillas Aleatorias)",
            command=lambda: self._iniciar_investigacion("DINAMICO"),
            height=48, width=390, font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.iniciar_dinamico.grid(row=3, column=0, pady=(24, 8))
        self.iniciar_oficial = ctk.CTkButton(
            self.prologo, text="Iniciar Modo Ejercicios Oficiales (Libreta / PDF)",
            command=lambda: self._iniciar_investigacion("OFICIAL_PDF"),
            height=48, width=390, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#8a5924", hover_color="#a66c2c",
        )
        self.iniciar_oficial.grid(row=4, column=0, pady=8)
        ctk.CTkLabel(
            self.prologo, text="14 NODOS · α = 0.05 · EVIDENCIA REPRODUCIBLE",
            text_color="#78909c", font=ctk.CTkFont(size=12),
        ).grid(row=5, column=0, pady=(8, 20))

    def _crear_pestana_expediente(self) -> None:
        tab = self.tabs.tab("Expediente")
        tab.grid_columnconfigure(0, weight=1)
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
        self.tabla_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.tabla_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        self.tabla_frame.grid_columnconfigure(0, weight=1)
        self.tabla_frame.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(tab, fg_color="#111b22")
        panel.grid(row=3, column=0, sticky="ew", padx=12, pady=10)
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

    def _mostrar_prologo(self) -> None:
        self.lateral.grid_remove()
        self.tabs.grid_remove()
        self.prologo.grid()
        self.reloj.configure(text="10:00")

    def _iniciar_investigacion(self, modo_ejecucion: str) -> None:
        self._seleccionar_modo(modo_ejecucion)
        self.investigacion_iniciada = True
        self.prologo.grid_remove()
        self.lateral.grid()
        self.tabs.grid()
        self.estado.configure(text="RASTRO ACTIVO", text_color="#57d6c5")
        self._actualizar_insignia_modo()
        self._renderizar_caso(reiniciar_reloj=True)
        self.after(250, self._tick)

    def _seleccionar_modo(self, modo_ejecucion: str) -> None:
        if modo_ejecucion not in MODOS_EJECUCION:
            raise ValueError(f"Modo de ejecución desconocido: {modo_ejecucion}")
        if modo_ejecucion == self.modo_ejecucion:
            return
        self.modo_ejecucion = modo_ejecucion
        estado = self.progreso_modos[modo_ejecucion]
        if self.investigacion_iniciada:
            estado["capitulo"] = self.capitulo
        self.capitulo = estado["capitulo"]
        self.completados = set(estado["completados"])
        self.caso = casos_narrativa.crear_caso(
            self.capitulo, estado.get("semilla"), self.modo_ejecucion,
        )
        self._actualizar_insignia_modo()
        if self.investigacion_iniciada:
            self.estado.configure(text=f"MODO {self.modo_ejecucion}", text_color="#57d6c5")
            self._renderizar_caso(reiniciar_reloj=True)
            self.tabs.set("Expediente")

    def _alternar_modo(self) -> None:
        destino = "OFICIAL_PDF" if self.modo_ejecucion == "DINAMICO" else "DINAMICO"
        self._seleccionar_modo(destino)

    def _actualizar_insignia_modo(self) -> None:
        if not hasattr(self, "modo_insignia"):
            return
        texto = (
            "MODO: OFICIAL LIBRETA / PDF"
            if self.modo_ejecucion == "OFICIAL_PDF" else "MODO: DINÁMICO"
        )
        self.modo_insignia.configure(text=texto)
        boton = (
            "Cambiar a Modo Dinámico"
            if self.modo_ejecucion == "OFICIAL_PDF"
            else "Cambiar a Libreta / PDF"
        )
        self.cambiar_modo_boton.configure(text=boton)

    def _renderizar_caso(self, reiniciar_reloj: bool) -> None:
        self.resuelto = self.capitulo in self.completados
        if reiniciar_reloj:
            self.fin = time.monotonic() + casos_narrativa.DURACION_CAPITULO
        self.etiqueta_caso.configure(
            text=f"CAPÍTULO {self.capitulo:02d}\n{self.caso['titulo'].upper()}",
        )
        self.progreso_label.configure(
            text=f"CAPÍTULOS RESUELTOS: {len(self.completados)} / {TOTAL_CAPITULOS}",
        )
        self._actualizar_insignia_modo()
        self.cabecera_caso.configure(
            text=f"NODO ENCRIPTADO {self.capitulo:02d} / {TOTAL_CAPITULOS}",
        )
        self.narrativa.configure(text=self.caso["narrativa"])
        self.formato.configure(text=self.caso["formato"])
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
        if resultado["correcto"]:
            self.resuelto = True
            self.completados.add(self.capitulo)
            self.fin = time.monotonic()
            self.estado.configure(text="NODO DESCIFRADO", text_color="#57d6c5")
            self.mensaje.configure(
                text="SOLUCIÓN CONFIRMADA. El rastro continúa…", text_color="#57d6c5",
            )
            self.verificar.configure(state="disabled")
            if self.capitulo == TOTAL_CAPITULOS:
                self._mostrar_victoria()
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
        self.estado.configure(text="RASTRO LOCALIZADO", text_color="#57d6c5")
        self.coordenadas_label.configure(text=self.caso["coordenadas"])
        self.victoria.grid()

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
            self.caso = casos_narrativa.crear_caso(self.capitulo)
            self.estado.configure(text="NODO BORRADO · NUEVA SEMILLA", text_color="#ff5555")
            self.mensaje.configure(
                text="Tiempo agotado. El nodo se regenera con datos nuevos.",
                text_color="#ff5555",
            )
            self._renderizar_caso(reiniciar_reloj=True)
            self.estado.configure(text="NUEVA SEMILLA ACTIVA", text_color="#f0b35a")
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

    def _cargar_progreso(self) -> dict:
        try:
            progreso = json.loads(ARCHIVO_PROGRESO.read_text(encoding="utf-8"))
            if progreso.get("version") == 3:
                estados_guardados = progreso.get("modos")
                if not isinstance(estados_guardados, dict):
                    estados_guardados = {}
                modos = {}
                for modo in MODOS_EJECUCION:
                    estado = estados_guardados.get(modo, {})
                    if not isinstance(estado, dict):
                        estado = {}
                    modos[modo] = {
                        "capitulo": min(TOTAL_CAPITULOS, max(1, int(estado.get("capitulo", 1)))),
                        "completados": [
                            numero for numero in estado.get("completados", [])
                            if isinstance(numero, int) and 1 <= numero <= TOTAL_CAPITULOS
                        ],
                        "semilla": estado.get("semilla"),
                    }
                modo_activo = progreso.get("modo_ejecucion", "DINAMICO")
                if modo_activo not in MODOS_EJECUCION:
                    modo_activo = "DINAMICO"
                return {"modo_ejecucion": modo_activo, "modos": modos}
            if progreso.get("version") == 2:
                dinamico = {
                    "capitulo": min(TOTAL_CAPITULOS, max(1, int(progreso.get("capitulo", 1)))),
                    "completados": [
                        numero for numero in progreso.get("completados", [])
                        if isinstance(numero, int) and 1 <= numero <= TOTAL_CAPITULOS
                    ],
                    "semilla": progreso.get("semilla"),
                }
                return {
                    "modo_ejecucion": "DINAMICO",
                    "modos": {
                        "DINAMICO": dinamico,
                        "OFICIAL_PDF": {"capitulo": dinamico["capitulo"], "completados": []},
                    },
                }
            if progreso.get("version") == 1:
                completados = [
                    numero for numero in progreso.get("completados", [])
                    if isinstance(numero, int) and 1 <= numero <= TOTAL_CAPITULOS
                ]
                dinamico = {"capitulo": 1, "completados": completados}
            else:
                dinamico = {"capitulo": 1, "completados": []}
            return {
                "modo_ejecucion": "DINAMICO",
                "modos": {
                    "DINAMICO": dinamico,
                    "OFICIAL_PDF": {"capitulo": 1, "completados": []},
                },
            }
        except FileNotFoundError:
            return {
                "modo_ejecucion": "DINAMICO",
                "modos": {
                    "DINAMICO": {"capitulo": 1, "completados": []},
                    "OFICIAL_PDF": {"capitulo": 1, "completados": []},
                },
            }
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            messagebox.showwarning(
                "Progreso no disponible", f"Se iniciará un expediente nuevo: {error}",
            )
            return {
                "modo_ejecucion": "DINAMICO",
                "modos": {
                    "DINAMICO": {"capitulo": 1, "completados": []},
                    "OFICIAL_PDF": {"capitulo": 1, "completados": []},
                },
            }

    def _guardar_progreso(self) -> None:
        try:
            self.progreso_modos[self.modo_ejecucion] = {
                "capitulo": self.capitulo,
                "completados": sorted(self.completados),
                "semilla": self.caso["semilla"],
            }
            ARCHIVO_PROGRESO.write_text(json.dumps({
                "version": 3, "modo_ejecucion": self.modo_ejecucion,
                "modos": self.progreso_modos,
            }, indent=2), encoding="utf-8")
        except OSError as error:
            self.mensaje.configure(
                text=f"No se pudo guardar el progreso: {error}", text_color="#ff5555",
            )


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

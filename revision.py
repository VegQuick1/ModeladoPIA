"""Herramientas de revisión, cargadas solo en la edición de evaluación."""

from __future__ import annotations

import json
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from tkinter import filedialog, messagebox
from types import MethodType

import customtkinter as ctk

import pruebas_estadisticas as estadisticas

TOTAL_CAPITULOS = 14
COLOR_LATON = "#8C6D3F"
COLOR_VERIFICADO = "#4E9A67"


def instalar_revision(aplicacion: ctk.CTk) -> None:
    aplicacion.revision_activa = False
    for metodo in (
        _actualizar_auditoria,
        _activar_revision,
        _mostrar_respuestas_exactas,
        _actualizar_panel_revision,
        _seleccion_revision_capitulo,
        _completar_respuestas,
        _crear_pestana_auditoria,
        _exportar,
    ):
        setattr(aplicacion, metodo.__name__, MethodType(metodo, aplicacion))
    aplicacion.bind_all("<Control-Shift-D>", aplicacion._activar_revision)
    aplicacion.bind_all("<Control-Shift-d>", aplicacion._activar_revision)


def construir_respuestas_exactas(caso: dict) -> dict:
    filas_tabla = []
    for seccion in caso["tabla_interactiva"]["secciones"]:
        filas = []
        for fila in seccion["filas"]:
            filas.append([
                caso["esperado"][celda["campo"]]
                if "campo" in celda else celda["valor"]
                for celda in fila
            ])
        filas_tabla.append({
            "seccion": seccion["titulo"],
            "columnas": seccion["columnas"],
            "filas": filas,
        })
    return {
        "capitulo": caso["numero"],
        "titulo": caso["titulo"],
        "respuestas": [
            {
                "campo": campo["etiqueta"],
                "respuesta": caso["esperado"][campo["id"]],
            }
            for campo in caso["campos"]
        ],
        "estadisticos_y_veredicto": caso["auditoria"],
        "tablas_criticas": {
            "Z_alpha_0.05": 1.96,
            "Kolmogorov_Smirnov_alpha_0.05": estadisticas.KS_CRITICOS_005,
            "χ²_alpha_0.05": estadisticas.CHI_CUADRADO_CRITICOS_005,
        },
        "tabla_interactiva_resuelta": filas_tabla,
    }


def construir_documento_auditoria(caso: dict, mostrar_solucion: bool = True) -> dict:
    auditoria = caso["auditoria"]
    bloqueado = "Bloqueado hasta resolver el capítulo."
    return {
        "proyecto": "EXPEDIENTE MONTECARLO: El Rastro del Fantasma",
        "modo_ejecucion": caso["modo_ejecucion"],
        "origen_problema": caso["origen_problema"],
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "capitulo": caso["numero"], "total_capitulos": TOTAL_CAPITULOS,
        "titulo": caso["titulo"], "semilla": caso["semilla"],
        "duracion_segundos": caso["duracion"],
        "tamano_muestra": _contar_muestra(caso),
        "hipotesis": {
            "H0": auditoria.get("hipotesis", "Según el método estadístico del capítulo"),
            "alpha": auditoria.get("alpha", 0.05),
            "resultados_pruebas": (
                _extraer_resultados_pruebas(auditoria) if mostrar_solucion else bloqueado
            ),
        },
        "transitorio_vs_estable": (
            _analisis_transitorio_estable(caso) if mostrar_solucion else bloqueado
        ),
        "tabla_reto": (
            caso["tabla"] if mostrar_solucion else _tabla_reto_bloqueada(caso)
        ),
        "motor_y_resultados": auditoria if mostrar_solucion else bloqueado,
        "solucion": caso["esperado"] if mostrar_solucion else bloqueado,
        "intentos": caso["respuestas"],
        "verificacion": (
            "Resultados calculados por los motores matemáticos a partir de los datos "
            "del preset oficial."
            if caso["modo_ejecucion"] == "OFICIAL_PDF" else
            "Tablas y respuestas calculadas dinámicamente a partir de la semilla."
        ),
    }


def _contar_muestra(caso: dict) -> int | None:
    auditoria = caso["auditoria"]
    for clave in ("tamano_muestra", "n_digitos", "n_parejas", "n_huecos"):
        if clave in auditoria:
            return auditoria[clave]
    for clave in (
        "valores_R", "digitos", "tabla_generada", "tabla_completa",
        "corridas_R", "filas",
    ):
        if clave in auditoria:
            valor = auditoria[clave]
            return sum(map(len, valor)) if clave == "corridas_R" else len(valor)
    if "exitos" in auditoria:
        return auditoria["total"]
    return None


def _tabla_reto_bloqueada(caso: dict) -> list[dict]:
    secciones = []
    for seccion in caso["tabla_interactiva"]["secciones"]:
        filas = [
            [
                "Por resolver" if "campo" in celda else celda["valor"]
                for celda in fila
            ]
            for fila in seccion["filas"]
        ]
        secciones.append({
            "seccion": seccion["titulo"],
            "columnas": seccion["columnas"],
            "filas": filas,
        })
    return secciones


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
    if (
        "filas" in auditoria and auditoria["filas"]
        and "Tiempo espera en sistema" in auditoria["filas"][0]
    ):
        muestra = [fila["Tiempo espera en sistema"] for fila in auditoria["filas"]]
    elif (
        "filas" in auditoria and auditoria["filas"]
        and "Inventario final" in auditoria["filas"][0]
    ):
        muestra = [fila["Inventario final"] for fila in auditoria["filas"]]
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


def _crear_pestana_auditoria(self, tab: ctk.CTkFrame) -> None:
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(1, weight=1)
    ctk.CTkLabel(
        tab, text="AUDITORÍA FORENSE · VERIFICACIÓN Y VALIDACIÓN DEL MODELO",
        text_color="#E0A952", font=ctk.CTkFont(size=14, weight="bold"),
    ).grid(row=0, column=0, sticky="w", padx=12, pady=12)
    self.auditoria_texto = ctk.CTkTextbox(
        tab, font=ctk.CTkFont(family="Consolas", size=12),
        fg_color="#211D19", text_color="#E8DDCA",
    )
    self.auditoria_texto.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
    botones = ctk.CTkFrame(tab, fg_color="transparent")
    botones.grid(row=2, column=0, sticky="e", padx=10, pady=10)
    ctk.CTkButton(
        botones, text="Exportar evidencia JSON",
        command=lambda: self._exportar("json"),
        fg_color=COLOR_LATON, hover_color="#A57C44",
    ).pack(side="left", padx=5)
    ctk.CTkButton(
        botones, text="Exportar evidencia TXT",
        command=lambda: self._exportar("txt"),
        fg_color=COLOR_LATON, hover_color="#A57C44",
    ).pack(side="left", padx=5)


def _actualizar_auditoria(self) -> None:
    if (
        not hasattr(self, "auditoria_texto")
        or not hasattr(self, "revision_ventana")
        or not self.revision_ventana.winfo_exists()
    ):
        return
    documento = construir_documento_auditoria(
        self.caso, self.resuelto or self.revision_activa,
    )
    self._documento_auditoria = documento
    self.auditoria_texto.configure(state="normal")
    self.auditoria_texto.delete("1.0", "end")
    self.auditoria_texto.insert(
        "1.0", json.dumps(documento, ensure_ascii=False, indent=2),
    )
    self.auditoria_texto.configure(state="disabled")


def _activar_revision(self, _evento: object = None) -> str:
    del _evento
    self.revision_activa = True
    self._mostrar_respuestas_exactas()
    return "break"


def _mostrar_respuestas_exactas(self) -> None:
    if (
        hasattr(self, "revision_ventana")
        and self.revision_ventana.winfo_exists()
    ):
        self.revision_ventana.lift()
        self._actualizar_panel_revision()
        return

    ventana = ctk.CTkToplevel(self)
    self.revision_ventana = ventana
    ventana.title("Panel de revisión")
    ventana.geometry("900x760")
    ventana.minsize(600, 450)
    ventana.transient(self)

    selector_frame = ctk.CTkFrame(ventana, fg_color="transparent")
    selector_frame.pack(fill="x", padx=14, pady=(14, 6))
    ctk.CTkLabel(selector_frame, text="Capítulo").pack(side="left", padx=(0, 8))
    self.selector_revision = ctk.CTkComboBox(
        selector_frame,
        values=[f"{i:02d}" for i in range(1, TOTAL_CAPITULOS + 1)],
        width=100, state="readonly", command=self._seleccion_revision_capitulo,
    )
    self.selector_revision.pack(side="left")
    self.selector_revision.set(f"{self.capitulo:02d}")

    self.revision_tabs = ctk.CTkTabview(ventana, fg_color="#181512")
    self.revision_tabs.pack(fill="both", expand=True, padx=14, pady=8)
    self.revision_tabs.add("Respuestas exactas")
    self.revision_tabs.add("Auditoría V&V")
    respuestas_tab = self.revision_tabs.tab("Respuestas exactas")
    respuestas_tab.grid_columnconfigure(0, weight=1)
    respuestas_tab.grid_rowconfigure(0, weight=1)
    self.respuestas_texto = ctk.CTkTextbox(
        respuestas_tab, font=ctk.CTkFont(family="Consolas", size=12),
        fg_color="#211D19", text_color="#E8DDCA",
    )
    self.respuestas_texto.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    self._crear_pestana_auditoria(self.revision_tabs.tab("Auditoría V&V"))

    botones = ctk.CTkFrame(ventana, fg_color="transparent")
    botones.pack(fill="x", padx=14, pady=(0, 14))
    ctk.CTkButton(
        botones, text="Completar respuestas", command=self._completar_respuestas,
        fg_color=COLOR_VERIFICADO, hover_color="#3D7A52",
    ).pack(side="left")
    ctk.CTkButton(
        botones, text="Cerrar", command=ventana.destroy, width=110,
        fg_color=COLOR_LATON,
    ).pack(side="right")
    self._actualizar_panel_revision()


def _actualizar_panel_revision(self) -> None:
    if (
        not hasattr(self, "respuestas_texto")
        or not hasattr(self, "revision_ventana")
        or not self.revision_ventana.winfo_exists()
    ):
        return
    self.selector_revision.set(f"{self.capitulo:02d}")
    self.respuestas_texto.configure(state="normal")
    self.respuestas_texto.delete("1.0", "end")
    self.respuestas_texto.insert(
        "1.0",
        json.dumps(
            construir_respuestas_exactas(self.caso),
            ensure_ascii=False, indent=2,
        ),
    )
    self.respuestas_texto.configure(state="disabled")
    self._actualizar_auditoria()


def _seleccion_revision_capitulo(self, seleccion: str) -> None:
    self._cambiar_capitulo(int(seleccion))


def _completar_respuestas(self) -> None:
    for seccion in self.caso["tabla_interactiva"]["secciones"]:
        if seccion["dinamica"]:
            self.tabla.filas_visibles[seccion["id"]] = min(
                seccion["filas_paro"], seccion["max_filas"],
            )
    self.tabla._renderizar()
    for clave, entrada in self.entradas.items():
        valor = str(self.caso["esperado"][clave])
        if isinstance(entrada, (ctk.CTkComboBox, ctk.CTkOptionMenu)):
            entrada.set(valor)
        else:
            entrada.delete(0, "end")
            entrada.insert(0, valor)
    if any(
        seccion["id"] == "volados"
        for seccion in self.caso["tabla_interactiva"]["secciones"]
    ):
        self.tabla.recalcular_corridas_volados()
    tablero = getattr(self, "tablero_clasificacion", None)
    if tablero is not None:
        tablero.completar()


def _exportar(self, formato: str) -> None:
    if not (self.resuelto or self.revision_activa):
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

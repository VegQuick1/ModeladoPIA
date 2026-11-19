"""Ilustraciones vectoriales noir para las pantallas narrativas."""

from __future__ import annotations

import math
import tkinter as tk
from importlib import import_module
from pathlib import Path


_ESCENAS = {
    "ingreso", "transicion", "final_bueno", "final_malo",
    *(f"capitulo_{numero:02d}" for numero in range(1, 15)),
}
_FONDO = "#12100E"
_SUPERFICIE = "#181512"
_PAPEL = "#241F1A"
_NOTA = "#241F1A"
_LATON = "#A67C46"
_AMBAR = "#F5B942"
_VERDE = "#4E9A67"
_ROJO = "#B83B3B"
_TINTA = "#F5EFE6"


class _Pintor:
    def __init__(self, lienzo: tk.Canvas, ancho: int, alto: int) -> None:
        self.canvas = lienzo
        self.sx = ancho / 800
        self.sy = alto / 220
        self.sf = min(self.sx, self.sy)

    def rect(
        self, x1: float, y1: float, x2: float, y2: float,
        fill: str, outline: str = "", width: float = 1,
    ) -> None:
        self.canvas.create_rectangle(
            self.x(x1), self.y(y1), self.x(x2), self.y(y2),
            fill=fill, outline=outline, width=max(1, width * self.sf),
        )

    def line(
        self, puntos: list[tuple[float, float]], fill: str = _TINTA,
        width: float = 2, smooth: bool = False,
    ) -> None:
        coordenadas = [
            coordenada
            for punto in puntos
            for coordenada in (self.x(punto[0]), self.y(punto[1]))
        ]
        self.canvas.create_line(
            *coordenadas, fill=fill, width=max(1, width * self.sf),
            smooth=smooth, capstyle=tk.ROUND, joinstyle=tk.ROUND,
        )

    def oval(
        self, x1: float, y1: float, x2: float, y2: float,
        fill: str, outline: str = "", width: float = 1,
    ) -> None:
        self.canvas.create_oval(
            self.x(x1), self.y(y1), self.x(x2), self.y(y2),
            fill=fill, outline=outline, width=max(1, width * self.sf),
        )

    def polygon(self, puntos: list[tuple[float, float]], fill: str, outline: str = "") -> None:
        coordenadas = [
            coordenada
            for punto in puntos
            for coordenada in (self.x(punto[0]), self.y(punto[1]))
        ]
        self.canvas.create_polygon(coordenadas, fill=fill, outline=outline)

    def text(
        self, x: float, y: float, texto: str, fill: str = _TINTA,
        size: int = 12, anchor: str = "center", family: str = "Consolas",
    ) -> None:
        self.canvas.create_text(
            self.x(x), self.y(y), text=texto, fill=fill,
            font=(family, max(8, round(size * self.sf)), "bold"),
            anchor=anchor,
        )

    def x(self, value: float) -> float:
        return value * self.sx

    def y(self, value: float) -> float:
        return value * self.sy


def _fondo(p: _Pintor) -> None:
    colores = (_FONDO, "#1D1915", _SUPERFICIE)
    for banda in range(24):
        color = colores[min(2, banda * 3 // 24)]
        y1 = 220 * banda / 24
        y2 = 220 * (banda + 1) / 24
        p.rect(0, y1, 800, y2, color)


def _lluvia(p: _Pintor, limite: int = 220) -> None:
    for indice in range(34):
        x = (indice * 71 + 29) % 800
        y = (indice * 43 + 17) % limite
        p.line([(x, y), (x - 9, min(limite, y + 18))], "#53616A", 1)


def _lampara(p: _Pintor, x: int = 590, y: int = 40) -> None:
    for radio, color in ((68, "#3A3020"), (48, "#49391F"), (28, "#654C26")):
        p.oval(x - radio, y - radio // 2, x + radio, y + radio, color)
    p.line([(x, y + 10), (x - 28, y + 49), (x + 5, y + 49)], _LATON, 5)
    p.oval(x - 15, y + 43, x + 17, y + 52, _AMBAR)


def _ventana(p: _Pintor, x: int, y: int, ancho: int, alto: int) -> None:
    p.rect(x, y, x + ancho, y + alto, "#253039", _LATON, 2)
    for torre in range(5):
        tx = x + 8 + torre * (ancho // 5)
        altura = 22 + (torre * 17) % max(25, alto - 24)
        p.rect(tx, y + alto - altura, tx + ancho // 9, y + alto, "#182025")
    p.line([(x + ancho // 2, y), (x + ancho // 2, y + alto)], _LATON, 2)
    p.line([(x, y + alto // 2), (x + ancho, y + alto // 2)], _LATON, 2)
    for indice in range(9):
        rx = x + (indice * 31 + 12) % max(1, ancho)
        ry = y + (indice * 23 + 9) % max(1, alto)
        p.line([(rx, ry), (rx - 5, ry + 12)], "#66757B", 1)


def _engranaje(p: _Pintor, cx: int, cy: int, radio: int, dientes: int = 12) -> None:
    p.oval(cx - radio, cy - radio, cx + radio, cy + radio, _NOTA, _AMBAR, 2)
    for indice in range(dientes):
        angulo = 2 * math.pi * indice / dientes
        x1 = cx + math.cos(angulo) * (radio - 4)
        y1 = cy + math.sin(angulo) * (radio - 4)
        x2 = cx + math.cos(angulo) * (radio + 7)
        y2 = cy + math.sin(angulo) * (radio + 7)
        p.line([(x1, y1), (x2, y2)], _AMBAR, 4)
    p.oval(cx - 8, cy - 8, cx + 8, cy + 8, _FONDO, _LATON, 2)


def _grafica(
    p: _Pintor, puntos: list[tuple[float, float]], color: str = _AMBAR,
    smooth: bool = False,
) -> None:
    p.line([(330, 185), (745, 185)], _LATON, 1)
    p.line([(330, 185), (330, 30)], _LATON, 1)
    p.line(puntos, color, 3, smooth)


def _escena_ingreso(p: _Pintor) -> None:
    _fondo(p)
    _ventana(p, 55, 22, 300, 137)
    for y in range(34, 144, 14):
        p.line([(60, y), (350, y)], "#514A3D", 2)
    _lluvia(p, 155)
    p.rect(0, 164, 800, 220, "#241D16", _LATON, 1)
    _lampara(p, 575, 42)
    p.polygon([(558, 87), (611, 87), (650, 168), (520, 168)], "#352A1A")
    p.rect(436, 155, 715, 200, _PAPEL, _LATON, 2)
    p.rect(456, 165, 695, 192, "#392F23", _LATON, 1)
    p.text(575, 180, "EXPEDIENTE · SIN ABRIR", _AMBAR, 13)
    p.text(110, 198, "ARCHIVO DE INGRESO · 02:13 A. M.", _TINTA, 12, "w")


def _escena_tablero(p: _Pintor, progreso: int) -> None:
    _fondo(p)
    p.rect(42, 18, 758, 202, "#3A2D20", _LATON, 3)
    p.rect(51, 26, 749, 194, "#493827")
    nodos = [(110 + (i % 7) * 96, 74 if i < 7 else 150) for i in range(14)]
    for indice in range(13):
        p.line([nodos[indice], nodos[indice + 1]], "#843A32", 3)
    for indice, (x, y) in enumerate(nodos, 1):
        color = _VERDE if indice <= progreso else "#786750"
        p.oval(x - 14, y - 14, x + 14, y + 14, color, _AMBAR, 1)
        p.text(x, y + 27, f"{indice:02d}", _TINTA, 9)
    p.text(400, 16, f"TABLERO DE PISTAS · {progreso} / 14", _AMBAR, 11)


def _escena_final(p: _Pintor, bueno: bool) -> None:
    _fondo(p)
    _lluvia(p)
    _ventana(p, 465, 22, 290, 145)
    p.rect(0, 170, 800, 220, "#211A16")
    if bueno:
        p.polygon([(98, 171), (133, 87), (169, 171)], "#101315")
        p.oval(122, 91, 145, 115, "#0E1113")
        p.rect(126, 112, 142, 171, "#0E1113")
        p.line([(145, 115), (480, 65)], _VERDE, 2)
        p.line([(145, 115), (520, 145)], _VERDE, 2)
        p.oval(476, 62, 490, 76, _AMBAR)
        p.text(555, 187, "COORDENADAS TRIANGULADAS", _AMBAR, 11)
    else:
        p.rect(162, 144, 268, 155, "#4B4135", _LATON, 2)
        p.rect(174, 76, 254, 145, _NOTA, _LATON, 2)
        p.rect(176, 60, 252, 86, "#493A2B", _LATON, 2)
        p.rect(170, 154, 178, 204, "#4B4135")
        p.rect(250, 154, 258, 204, "#4B4135")
        p.rect(526, 120, 690, 185, "#090D10", _LATON, 2)
        p.text(607, 147, "SIN SEÑAL", _ROJO, 12)
        p.text(575, 199, "LA SILLA QUEDÓ VACÍA", _AMBAR, 11)


def _escena_capitulo(p: _Pintor, numero: int) -> None:
    _fondo(p)
    p.rect(34, 24, 766, 197, _PAPEL, _LATON, 1)
    p.text(60, 42, f"NODO {numero:02d} · INDICIO TÉCNICO", _AMBAR, 11, "w")
    if numero in (1, 2):
        _engranaje(p, 135, 125, 40, 10 if numero == 1 else 14)
        _engranaje(p, 235, 125, 30, 12)
        if numero == 2:
            p.rect(302, 81, 368, 167, "#171717", _LATON, 2)
            for y in (95, 119, 143):
                p.line([(311, y), (359, y)], _AMBAR, 3)
        p.text(522, 104, "Xₙ₊₁ = (aXₙ + c) mod m" if numero == 1 else "Xₙ₊₁ = aXₙ mod m", _TINTA, 14)
        p.text(522, 136, "SEMILLA · CICLO · PERIODO", _AMBAR, 10)
    elif numero in (3, 4, 5, 6, 7, 8, 12):
        if numero in (3, 5, 8, 12):
            alturas = [32, 54, 81, 112, 86, 57, 34]
            for indice, alto in enumerate(alturas):
                x = 355 + indice * 48
                p.rect(x, 184 - alto, x + 28, 184, _AMBAR if indice == 3 else _LATON)
            if numero == 3:
                puntos = [(350 + i * 18, 145 - 90 * math.exp(-((i - 22) / 11) ** 2)) for i in range(45)]
                p.line(puntos, "#D8C59F", 2, True)
            p.text(528, 57, "FO · FE · χ²", _AMBAR, 12)
        elif numero == 4:
            puntos = [(350 + i * 9, 174 - i * 2.4) for i in range(45)]
            p.line(puntos, _AMBAR, 3)
            p.line([(350, 174), (755, 34)], "#D8C59F", 2)
            p.text(547, 59, "Dₙ = max |Fₙ − F|", _AMBAR, 12)
        elif numero == 6:
            p.text(370, 102, "2", _TINTA, 22)
            p.line([(400, 102), (496, 102)], _ROJO, 3)
            p.text(448, 79, "hueco", _AMBAR, 10)
            p.text(525, 102, "2", _TINTA, 22)
            p.text(545, 143, "DIGITOS REPETIDOS", _AMBAR, 10)
        elif numero == 7:
            p.rect(390, 63, 560, 174, "", _LATON, 2)
            p.line([(475, 63), (475, 174)], _LATON, 1)
            p.line([(390, 118), (560, 118)], _LATON, 1)
            for x, y in ((418, 95), (442, 81), (510, 146), (535, 138), (430, 147)):
                p.oval(x - 4, y - 4, x + 4, y + 4, _AMBAR)
            p.text(655, 114, "PAREJAS · CUADRANTES", _TINTA, 10)
        else:
            for indice in range(4):
                x = 385 + indice * 68
                p.rect(x, 78, x + 51, 157, "#4B3827", _AMBAR, 2)
                p.text(x + 25, 117, ("A", "K", "7", "Q")[indice], _TINTA, 17)
                p.oval(x + 15, 151, x + 40, 176, _VERDE, _LATON, 1)
    elif numero in (9, 10, 11):
        if numero == 9:
            puntos = [(355 + i * 8, 52 + 126 * (1 - math.exp(-i / 10))) for i in range(49)]
            _grafica(p, puntos)
            p.oval(635, 49, 720, 134, "", _AMBAR, 3)
            p.line([(677, 91), (677, 64)], _AMBAR, 3)
            p.line([(677, 91), (700, 105)], _AMBAR, 3)
        elif numero == 10:
            _grafica(p, [(360, 65), (360, 65), (735, 65), (735, 65)])
            for x in range(380, 730, 58):
                p.line([(x, 65), (x, 185)], "#76654C", 1)
            p.text(545, 48, "DENSIDAD CONSTANTE", _AMBAR, 10)
        else:
            _grafica(p, [(350, 173), (470, 129), (590, 129), (590, 70), (745, 44)])
            p.line([(590, 60), (590, 185)], _ROJO, 2)
            p.text(590, 48, "CAMBIO DE TRAMO", _AMBAR, 10)
    elif numero == 13:
        for fila in range(3):
            y = 81 + fila * 38
            p.line([(365, y), (737, y)], _LATON, 3)
            for columna in range(5):
                x = 390 + columna * 67
                p.rect(x, y - 25, x + 38, y - 2, "#58452F", _AMBAR, 1)
        p.text(555, 181, "ENTRADAS · SALIDAS · EXISTENCIAS", _AMBAR, 10)
    else:
        p.oval(393, 86, 467, 160, "#6E542D", _AMBAR, 2)
        p.oval(485, 86, 559, 160, "#8B6B35", _AMBAR, 2)
        p.rect(602, 74, 725, 171, "#24402F", _LATON, 2)
        for indice in range(4):
            p.oval(618 + indice * 24, 132, 638 + indice * 24, 152, _AMBAR)
        p.text(664, 58, "APUESTA · SALDO · META", _TINTA, 10)


def _cargar_png(canvas: tk.Canvas, ruta: Path, ancho: int, alto: int) -> bool:
    if not ruta.is_file():
        return False
    try:
        image_module = import_module("PIL.Image")
        image_tk_module = import_module("PIL.ImageTk")
    except ImportError as error:
        raise RuntimeError(
            f"Existe {ruta}, pero se necesita Pillow para cargar esa ilustración."
        ) from error
    with image_module.open(ruta) as imagen:
        remuestreo = getattr(image_module, "Resampling", image_module).LANCZOS
        imagen_redimensionada = imagen.convert("RGB").resize(
            (ancho, alto), remuestreo,
        )
    photo = image_tk_module.PhotoImage(imagen_redimensionada, master=canvas)
    canvas._imagen_escena = photo
    canvas.create_image(0, 0, image=photo, anchor="nw")
    return True


def renderizar_escena(
    canvas: tk.Canvas, escena_id: str | int, progreso: int = 0,
    assets_dir: Path | None = None,
) -> None:
    if isinstance(escena_id, int):
        escena_id = f"capitulo_{escena_id:02d}"
    if escena_id not in _ESCENAS:
        raise ValueError(f"Escena desconocida: {escena_id}")
    ancho = max(320, canvas.winfo_width())
    alto = max(150, canvas.winfo_height())
    base_assets = assets_dir or Path(__file__).with_name("assets")
    identificador_asset = (
        escena_id[-2:] if escena_id.startswith("capitulo_") else escena_id
    )
    archivo = base_assets / f"escena_{identificador_asset}.png"
    if not archivo.is_file() and escena_id.startswith("capitulo_"):
        archivo = base_assets / f"escena_{escena_id}.png"
    canvas.delete("all")
    if _cargar_png(canvas, archivo, ancho, alto):
        return
    pintor = _Pintor(canvas, ancho, alto)
    if escena_id == "ingreso":
        _escena_ingreso(pintor)
    elif escena_id == "transicion":
        _escena_tablero(pintor, min(14, max(0, progreso)))
    elif escena_id == "final_bueno":
        _escena_final(pintor, True)
    elif escena_id == "final_malo":
        _escena_final(pintor, False)
    else:
        _escena_capitulo(pintor, int(escena_id[-2:]))


class EscenaVisual(tk.Canvas):
    def __init__(
        self, master: tk.Misc, escena_id: str | int, progreso: int = 0,
        width: int = 800, height: int = 220,
    ) -> None:
        super().__init__(
            master, width=width, height=height, bg=_FONDO,
            highlightthickness=1, highlightbackground=_LATON,
        )
        self.escena_id = escena_id
        self.progreso = progreso
        self.bind("<Configure>", self._al_redimensionar)
        self.after_idle(self.renderizar)

    def actualizar(self, escena_id: str | int, progreso: int = 0) -> None:
        self.escena_id = escena_id
        self.progreso = progreso
        self.renderizar()

    def renderizar(self) -> None:
        renderizar_escena(self, self.escena_id, self.progreso)

    def _al_redimensionar(self, evento: tk.Event) -> None:
        if evento.width > 1 and evento.height > 1:
            self.renderizar()

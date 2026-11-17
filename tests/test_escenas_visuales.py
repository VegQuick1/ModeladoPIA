import tempfile
import unittest
from pathlib import Path

from escenas_visuales import renderizar_escena


class CanvasFalso:
    def __init__(self):
        self.elementos = []

    def winfo_width(self):
        return 800

    def winfo_height(self):
        return 220

    def delete(self, _tag):
        self.elementos.clear()

    def create_rectangle(self, *args, **kwargs):
        self.elementos.append(("rectangle", args, kwargs))

    def create_line(self, *args, **kwargs):
        self.elementos.append(("line", args, kwargs))

    def create_oval(self, *args, **kwargs):
        self.elementos.append(("oval", args, kwargs))

    def create_polygon(self, *args, **kwargs):
        self.elementos.append(("polygon", args, kwargs))

    def create_text(self, *args, **kwargs):
        self.elementos.append(("text", args, kwargs))


class EscenasVisualesTests(unittest.TestCase):
    def test_todas_las_escenas_vectoriales_se_dibujan_en_canvas(self):
        escenas = [
            "ingreso", *(f"capitulo_{numero:02d}" for numero in range(1, 15)),
            "transicion", "final_bueno", "final_malo",
        ]
        with tempfile.TemporaryDirectory() as directorio:
            for escena in escenas:
                with self.subTest(escena=escena):
                    canvas = CanvasFalso()
                    renderizar_escena(
                        canvas, escena, progreso=8,
                        assets_dir=Path(directorio),
                    )
                    self.assertTrue(canvas.elementos)

    def test_acepta_capitulo_numerico_y_rechaza_escena_desconocida(self):
        canvas = CanvasFalso()
        renderizar_escena(canvas, 14)
        self.assertTrue(canvas.elementos)
        with self.assertRaises(ValueError):
            renderizar_escena(canvas, "capitulo_15")


if __name__ == "__main__":
    unittest.main()

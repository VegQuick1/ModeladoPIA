# EXPEDIENTE MONTECARLO

Aplicación educativa de escritorio para practicar generación de números
aleatorios, pruebas estadísticas y simulación de sistemas. La partida puede
usar ejercicios de la libreta o crear casos reproducibles a partir de una
semilla.

## Inicio

Abre la aplicación ya preparada desde su acceso directo o inicia `main.py` en
el entorno configurado para el proyecto. En una investigación nueva, elige
Modo Apuntes (Oficial) o Modo Dinámico y registra el alias del detective. El
modo queda fijado durante esa partida. Si ya hay progreso, continúa desde el
capítulo pendiente; usa «Restablecer Progreso» para empezar de nuevo y elegir
otro modo.

## Capítulos

1. Generador congruencial mixto
2. Generador congruencial multiplicativo
3. Prueba de promedios
4. Kolmogorov-Smirnov
5. Prueba de frecuencias
6. Prueba de distancias
7. Prueba de series
8. Prueba de Póker
9. Distribución exponencial
10. Distribución uniforme
11. Distribución empírica
12. Distribución de Poisson
13. Inventario estocástico
14. Juego de volados con Martingala

## Módulos

- `main.py`: interfaz, reloj, navegación, guardado y exportación de auditorías.
- `escenas_visuales.py`: ilustraciones vectoriales de las pantallas narrativas;
  admite imágenes opcionales en `assets/escena_*.png`.
- `casos_narrativa.py`: casos oficiales y dinámicos, tablas y validación.
- `motores_generadores.py`: generadores congruenciales y pruebas de periodo.
- `pruebas_estadisticas.py`: pruebas de uniformidad e independencia.
- `variables_no_uniformes.py`: transformaciones de distribuciones.
- `sistemas_aplicados.py`: cola, inventario y juego de Martingala.
- `tests/`: pruebas de los motores, los capítulos y la persistencia.

El progreso se guarda en `savegame.json`. Ejecuta la suite desde la raíz del
proyecto con `pytest`.

## Ejecutable para macOS

El ejecutable de Windows no puede ejecutarse directamente en macOS. PyInstaller
tampoco puede cruzar sistemas desde Windows: el paquete `.app` debe construirse
en una máquina macOS.

El flujo de GitHub Actions incluido crea automáticamente
`Expediente-Montecarlo-macOS.zip` en una ejecución de macOS. Actívalo desde
**Actions > Build macOS app > Run workflow** y descarga el archivo desde
**Artifacts**. Los archivos de Windows no se modifican ni se sobrescriben.

Para crear la aplicación localmente desde macOS:

```bash
python3 -m venv .venv-macos
source .venv-macos/bin/activate
python -m pip install -r requirements.txt -r requirements-build.txt
pyinstaller --clean --noconfirm ExpedienteMontecarlo.spec
codesign --force --deep --sign - "dist/Expediente Montecarlo.app"
```

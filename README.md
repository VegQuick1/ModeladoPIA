# EXPEDIENTE MONTECARLO: El Rastro del Fantasma

Novela visual educativa de investigación para Modelado y Simulación de Sistemas.
Requiere Python 3.10+ y `customtkinter`.

## Ejecución

```powershell
python -m pip install -r requirements.txt
python main.py
```

La aplicación presenta un prólogo antes de iniciar el reloj. Cada capítulo
dispone de 600 segundos, excepto Poisson (capítulo 12), con 720 segundos. Cada
respuesta incorrecta descuenta 25 segundos; los errores de sintaxis en
fracciones se explican sin penalización. El reloj está verde por encima de
180 s, amarillo entre 61 y 180 s, y rojo parpadeante durante los últimos 60 s.
El progreso se guarda en `savegame.json`; un `progreso.json` anterior se puede
migrar al iniciar. El modo demostración habilita la auditoría matemática y la
navegación libre entre capítulos. Desde la pestaña **Auditoría V&V** se exporta
la corrida actual a JSON o TXT.

El prólogo ofrece dos modos: **Dinámico**, que conserva los problemas
pseudoaleatorios por semilla, y **Modo: Oficial Libreta / PDF**, con los 14
ejercicios oficiales en el orden de la libreta. El modo se elige al iniciar una
partida. La auditoría y sus exportaciones incluyen `modo_ejecucion` y
`origen_problema`; los capítulos estadísticos también disponen de una vista de
tablas críticas Z, KS y χ².

Los capítulos se resuelven en tablas interactivas: los datos conocidos son de
solo lectura y los resultados se escriben directamente en celdas editables.
Los capítulos iterativos ofrecen controles para agregar o quitar filas, validan
el punto exacto de paro y muestran el resultado por celda. Los generadores
oficiales muestran los números rectangulares como fracciones `Xᵢ/m` e incluyen
la comprobación de periodo. Las pruebas oficiales de
frecuencias y series conservan los cálculos de las tablas del curso; la prueba
de distancias usa repeticiones dentro de los cinco decimales de cada R, y Póker
clasifica patrones de cinco dígitos. En el ejercicio de volados, la secuencia
oficial se consume en orden, la apuesta se duplica tras una pérdida y se
mantiene tras una victoria; la probabilidad se calcula sobre las corridas
completas y la auditoría identifica las corridas inconclusas. Si vence el
tiempo, el modo dinámico regenera el caso con otra semilla al reintentarlo; el
modo oficial conserva los datos publicados.

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
13. Cola de un canal
14. Volados con Martingala

## Módulos

- `main.py`: interfaz, reloj por `after()`, persistencia y exportación.
- `motores_generadores.py`: generadores congruenciales y condiciones de periodo.
- `pruebas_estadisticas.py`: promedios, KS, frecuencias, distancias, series y Póker;
  agrupación de categorías para las pruebas que la requieren.
- `variables_no_uniformes.py`: transformadas uniforme, exponencial, empírica y Poisson.
- `sistemas_aplicados.py`: Martingala y cola de un servidor.
- `casos_narrativa.py`: generación de expedientes y verificación tolerante.

Las semillas, secuencias y tablas dinámicas se generan al crear o reintentar
cada capítulo. Ejecuta las pruebas con `python -m pytest -q` o
`python -m unittest discover -s tests -v`.

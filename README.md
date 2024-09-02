# TFG-INFO

Autor: Marcos Martínez 

## Descripción
Se trata de una herramienta para la automatización de escaneos para la medición de cobertura móvil 
a través de dispositivos Android.  
Esta herramienta permite realiar escaneos optimizando los intervalos entre los mismos 
y creando archivos manejables para un uso más fácil.

## Requisitos 
- [Network Signal Guru](https://www.qtrun.com/en/?page_id=34)
- [Scat](https://github.com/fgsect/scat)
- [GPSLogger](https://github.com/mendhak/gpslogger/tree/master)
- [gpxpy](https://pypi.org/project/gpxpy/)
- [scikit-learn](https://scikit-learn.org/stable/) para el uso de validación cruzada

## Modo de uso

Para su ejecución se utiliza el módulo Scat, 
el módulo NSG se trata de una solución alternativa al proyecto descartada.

El programa requiere de dos argumentos 
    - Modelo del teléfono: se refiere al modelo del fabricante del chip.
    - Número de interfaz del nodo de diagnóstico, especifico de cada dispositivo.

El comando sería el siguiente:
```
$ python3 scat_analizador.py Samsung --interfaz 2
$ python3 scat_analizador.py Qualcomm --interfaz 4
$ python3 scat_analizador.py Huawei --interfaz 2
```
 Si bien es posible que ciertos dispositivos requieran acciones adicionales o no sean compatibles,
 para ello mirar [la wiki de scat](https://github.com/fgsect/scat/wiki).

## Licencia 
Se trata de software libre, modificable a gusto del usuario.
En cualquier caso este software carece de garantía de funcionamiento ni de ninguna clase.



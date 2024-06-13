from datetime import datetime
import json
import re
from json import JSONDecoder
import subprocess
import time

CONTENIDO = '/sdcard/Network_Signal_Guru/test.log'
APLICACION = 'com.qtrun.QuickTest'

DATOS_LTE = ['earfcn', 'rsrp', 'sinr', 'rssi']
DATOS_WCDMA = ['uarfcn', 'rscp', 'ecn0', 'rssi']


def extract_json_objects(text, decoder=JSONDecoder()):
    """Find JSON objects in text, and yield the decoded JSON data

    Does not attempt to look for JSON arrays, text, or other JSON types outside
    of a parent JSON object.

    """
    pos = 0
    while True:
        match = text.find('{', pos)
        if match == -1:
            break
        try:
            result, index = decoder.raw_decode(text[match:])

            yield result
            pos = match + index
        except ValueError:
            pos = match + 1

def leer_archivo_android(ruta):
    # Ejecutar el comando adb para leer el archivo
    resultado = subprocess.run(['adb', 'shell', 'cat', ruta], capture_output=True, text=True, errors='ignore')

    # Devolver el contenido del archivo
    return resultado.stdout

def acceder_paquete(package_name):
    comando = f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
    result = subprocess.run(comando, shell=True, capture_output=True, text=True)
    return result

def cerrar_app(package_name):
    comando = f"adb shell am force-stop {package_name}"
    result = subprocess.run(comando, shell=True, capture_output=True, text=True)
    return result


def lectura_continua():

    print("Empezando lectura...")
    reading = True
    datos = []

    while reading:
        print("**")
        contenido = leer_archivo_android(CONTENIDO)
        contenido = contenido.replace('España','Spain')
        contenido = contenido.replace('{',' {').replace('}','} _').replace('[',' [').replace(']','] ')
        contenido = contenido.splitlines()
        ultimo_contenido = contenido[-10:-1]
        for linea in ultimo_contenido:
            data = extract_json_objects(linea)
            l = []
            if data is not None:
                for d in data:
                    l.append(d)
            if len(l) != 0:
                if len(datos) == 0 or l != datos[-1]:
                    datos.append(l)
                    print(l)
                for elemento in l:
                    if isinstance(elemento,dict) and 'event' in elemento.keys() and elemento['event'] == 'close':
                        reading = False
                        print("Tarea finalizada")
                        break

        time.sleep(0.5)
    return datos

def lectura_con_apertura():
    print("Empezando lectura...")
    reading = True
    datos = []

    app_status = acceder_paquete(APLICACION)
    if app_status != 0:
        reading = False
    else:
        while reading:
            print("**")
            contenido = leer_archivo_android(CONTENIDO)
            contenido = contenido.replace('España', 'Spain')
            contenido = contenido.replace('{', ' {').replace('}', '} _').replace('[', ' [').replace(']', '] ')
            contenido = contenido.splitlines()
            ultimo_contenido = contenido[-10:-1]
            for linea in ultimo_contenido:
                data = extract_json_objects(linea)
                l = []
                if data is not None:
                    for d in data:
                        l.append(d)
                if len(l) != 0:
                    if len(datos) == 0 or l != datos[-1]:
                        datos.append(l)
                        print(l)
                    for elemento in l:
                        if isinstance(elemento, dict) and 'event' in elemento.keys() and elemento['event'] == 'close':
                            reading = False
                            print("Tarea finalizada")
                            break

            time.sleep(0.5)
        return datos


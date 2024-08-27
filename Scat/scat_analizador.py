'''Programa para analisis de las salidas del programa Scat'''

import json
import time
import datetime
import re
import subprocess
import gpxpy
import funciones
import lightgbm as lgb
import pandas as pd
import numpy as np
import argparse


MIN_LEVEL = -130
INTERVALO_MAX = 5
INTERVALO_MIN = 0.25

DIFF_RSRP_MIN = 2
DIFF_RSRP_MAX = 8
DIFF_RSRP_EXTR = 20

APP_LOCALIZACION = 'com.mendhak.gpslogger'
LOCALIZACION_RUTA_ARCHIVO = '/sdcard/GpsLogger'

def train_model(params, data):
    """Entrenamiento del modelo de Aprendizaje Automatico,
    Como argumentos lleva la lista de celdas y los parametros de aprendizaje,
    devuelve un modelo entrenado"""
    celdas = data
    x_train = pd.DataFrame(celdas)
    x_train = x_train.drop('earfcn',axis="columns")
    x_train = x_train.drop('time',axis="columns")
    x_train = x_train.drop('rsrq',axis="columns")
    x_train = x_train.drop('pci',axis="columns")
    x_train = x_train.drop('plmn',axis="columns")
    print(x_train)
    y_train = x_train.pop('rsrp')
    x_train = x_train.to_numpy()
    y_train = y_train.to_numpy()
    train_data = lgb.Dataset(x_train, label=y_train)

    if len(celdas) > 15:
        cv_results = lgb.cv(params, train_data)
        best_num_boost_round = len(cv_results)
        final_model = lgb.train(params, train_data, num_boost_round=best_num_boost_round)
        return final_model

    best_num_boost_round = 1
    final_model = lgb.train(params, train_data, num_boost_round=best_num_boost_round)
    return final_model

def coger_datos_geo(localizacion_ruta_archivo):
    """ Funcion para coger los datos de geolocalizacion del archivo .gpx"""
    geoloc_data_str = funciones.leer_archivo_android(localizacion_ruta_archivo)
    gpx = gpxpy.parse(geoloc_data_str)
    for track in gpx.tracks:
        for segment in track.segments:
            lat = segment.points[-1].latitude
            long = segment.points[-1].longitude
            altitud = segment.points[-1].elevation
    return lat,long,altitud
def procesar_linea(linea_decod,coordenadas):
    """Funcion para procesar una linea de analisis de cobertura LTE"""
    linea_decod = linea_decod.replace(',', ' ,').replace(':', ' :')
    match = re.search('EARFCN' + r'\s+(\S*)', linea_decod)
    if match:
        earfcn = int(match.group(1))
    match = re.search('PCI' + r'\s+(\S*)', linea_decod)
    if match:
        pci = int(match.group(1))
    match = re.search('PLMN' + r'\s+(\S*)', linea_decod)
    if match:
        plmn = int(match.group(1))
    match = re.search('RSRP :' + r'\s+(\S*)', linea_decod)
    if match:
        rsrp = float(match.group(1))
    match = re.search('RSRQ :' + r'\s+(\S*)', linea_decod)
    if match:
        rsrq = float(match.group(1))

    # Datos de geolocalizacion
    latitud,longitud,altitud = coordenadas
    # Procesado de datos de la celda
    serving_cell = {'earfcn': earfcn, 'pci': pci,
                    'plmn': plmn, 'rsrp': rsrp,
                    'rsrq': rsrq, 'time': str(datetime.datetime.now()),
                    'latitude': latitud, 'longitude': longitud, 'elevation': altitud}
    return serving_cell

if __name__ == '__main__':
    #Argumentos para el analizador y para Scat
    parser = argparse.ArgumentParser(
        description='Programa para escaneo de datos de cobertura con dispositivos Android')
    parser.add_argument('modelo',
                    type=str,
                    help='Fabricante del procesador, puede ser Samsung,Qualcomm,Huawei',
                    choices=['Samsung','Qualcomm','Huawei']
    )
    parser.add_argument('--interfaz',
                        type=int,
                        help='Interfaz del bus USB,para la ejecucion de Scat',
                        default=2
    )
    args = parser.parse_args()
    modelo = args.modelo
    modelo_procesador = args.modelo
    interfaz = args.interfaz
    bus_usb = funciones.get_interfaz_dispositivo(modelo)
    bus = str(bus_usb[0])+":"+str(bus_usb[1])
    #Para archivo de guardado
    date = str(datetime.datetime.now().strftime("%d%m%Y%H%M%S"))
    file = f'celdas{date}.json'
    path_to_file = f'ficheros_mediciones/{file}'
    #Comando de ejecucion de Scat
    comando = ['scat', '-t', funciones.COMANDO_SEGUN_MODELO[modelo_procesador],
               '-u', '-a', bus, '-i', str(interfaz)]
    proceso = subprocess.Popen(comando,bufsize=1,stdout = subprocess.PIPE, pipesize=1,text = True)
    #Direccion de la app de geolocalizacion y archivo
    fecha = str(datetime.date.today()).replace('-', '')
    archivo_localizacion = fecha + '.gpx'
    LOCALIZACION_RUTA_ARCHIVO = LOCALIZACION_RUTA_ARCHIVO + '/' + archivo_localizacion
    print(f'Archivo de geolocalizacion:{LOCALIZACION_RUTA_ARCHIVO}')
    funciones.acceder_paquete(APP_LOCALIZACION)

    #Variables generales del programa
    interval = 1
    celdas = []
    celda_ref = {}

    #Parametros de aprendizaje del modelo de AA
    params = {'num_leaves': 31, 'objective': 'regression','n_jobs':4,'learning_rate':0.5}
    params['metric'] = 'rmse'

    #Programa principal
    try:
        print('Escaneando...')
        interval_aux = interval
        while True:
            interval = interval_aux
            linea = proceso.stdout.readline()
            print(linea)
            linea_decod = linea.strip()
            # Si ya hay celdas entrenamos el modelo

            # Buscamos con tecnología LTE, para otra tecnología cambiar a partir de aqui
            if 'LTE PHY Cell Info' in linea_decod and 'NCell' not in linea_decod:# Buscamos la celda servidora
                coordenadas = coger_datos_geo(LOCALIZACION_RUTA_ARCHIVO)
                serving_cell = procesar_linea(linea_decod,coordenadas)
                if len(celdas) != 0:
                    t_modelo = train_model(params, celdas)
                # Deteccion de obstaculos grandes,
                # es necesario al menos haber establecido un pequeño recorrido de referencia
                if len(celdas) > 10 and t_modelo:
                    data = pd.DataFrame([serving_cell])
                    data = data.drop(labels=['earfcn', 'pci', 'plmn', 'rsrp', 'rsrq',  'time'], axis="columns")
                    print(data)
                    data = data.to_numpy()
                    y_pred = t_modelo.predict(data)
                    print(f"RSRP previsto : {y_pred} || RSRP : {serving_cell['rsrp']}")
                    if abs(abs(y_pred) - abs(serving_cell['rsrp'])) <= DIFF_RSRP_MIN:
                        nuevo_intervalo = interval * 1.25
                        interval = min(10, nuevo_intervalo)
                    elif DIFF_RSRP_MIN < abs(abs(y_pred) - abs(serving_cell['rsrp'])) < DIFF_RSRP_MAX:
                        nuevo_intervalo = interval
                        interval = nuevo_intervalo
                    elif abs(abs(y_pred) - abs(serving_cell['rsrp'])) > DIFF_RSRP_MAX:
                        nuevo_intervalo = min(1,interval * 0.5)
                        interval = max(0.25, nuevo_intervalo)
                        if abs(abs(y_pred) - abs(serving_cell['rsrp'])) > DIFF_RSRP_EXTR or abs(abs(celdas[-1]['rsrp']) - abs(serving_cell['rsrp'])) > DIFF_RSRP_EXTR:
                            print("Obstáculo detectado")
                print(f'Intervalo hasta el siguiente escaneo de {interval} segundos')

                celdas.append(serving_cell)
                with open(f'{path_to_file}', 'w', encoding='utf-8') as archivo:
                    archivo.write(json.dumps(celdas, indent=2))
                    print("celda guardada")
                    archivo.close()


                if serving_cell['rsrp'] < MIN_LEVEL:
                    print("Baja calidad de señal")
                    if len(celda_ref.keys()) > 0:
                        print(f"Volver a {celda_ref['latitude']},{celda_ref['longitude']}")
                    else:
                        print("Buscar localizacion de referencia")
                        print(json.dumps(serving_cell, indent=2))
                else:
                    celda_ref = serving_cell
                    print(json.dumps(serving_cell, indent=2))


            else:
                if 'EDGE' in linea_decod or 'HSPA' in linea_decod:
                    if 'RSSI' in linea_decod:
                        match = re.search('RSSI ' + r'\s+(\S*)', linea_decod)
                        if match:
                            rssi = int(match.group(1))
                            if rssi < -130:
                                print("Ausencia total de cobertura")
                            else:
                                interval_aux = interval
                                interval = 0
                    if len(celda_ref.keys()) > 0:
                        print(f"Volver a {celda_ref['latitude']},{celda_ref['longitude']}")
                    else:
                        print("Buscar localizacion de referencia")
                else:
                    inerval_aux = interval
                    interval = 0






            time.sleep(interval)




    except KeyboardInterrupt:
        proceso.terminate()
        stdout, stderr = proceso.communicate()
        funciones.cerrar_app(APP_LOCALIZACION)
        with open(f'{path_to_file}', 'w', encoding='utf-8') as archivo:
            archivo.write(json.dumps(celdas, indent=2))
            archivo.close()
        print("Tarea finalizada")
        print(stdout)

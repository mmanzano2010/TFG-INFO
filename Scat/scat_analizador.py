'''Programa para analisis de las salidas del programa Scat'''

import json
import time
import datetime
import re
import subprocess
import gpxpy
import funciones
import lightgbm as lgb
from lightgbm import LGBMRegressor
import pandas as pd
import numpy as np
import argparse


MIN_LEVEL = -130
INTERVALO_MAX = 5
INTERVALO_MIN = 0.25

DIFF_RSRP_MIN = 2
DIFF_RSRP_MAX = 8
DIFF_RSRP_EXTR = 20

def train_model(params, data):
    """Entrenamiento del modelo de Aprendizaje Automatico,
    Como argumentos lleva la lista de celdas y los parametros de aprendizaje,
    devuelve un modelo entrenado"""
    celdas = data
    X_train = pd.DataFrame(celdas)
    X_train = X_train.drop('earfcn',axis="columns")
    X_train = X_train.drop('time',axis="columns")
    X_train = X_train.drop('rsrq',axis="columns")
    X_train = X_train.drop('pci',axis="columns")
    X_train = X_train.drop('plmn',axis="columns")
    print(X_train)
    Y_train = X_train.pop('rsrp')
    X_train = X_train.to_numpy()
    Y_train = Y_train.to_numpy()
    train_data = lgb.Dataset(X_train, label=Y_train)

    if len(celdas) > 15:
        cv_results = lgb.cv(params, train_data)
        best_num_boost_round = len(cv_results)
        final_model = lgb.train(params, train_data, num_boost_round=best_num_boost_round)
        return final_model

    best_num_boost_round = 1
    final_model = lgb.train(params, train_data, num_boost_round=best_num_boost_round)
    return final_model

if __name__ == '__main__':
    #Argumentos para el analizador y para Scat
    parser = argparse.ArgumentParser(description='Programa para escaneo de datos de cobertura con dispositivos Android')
    parser.add_argument('modelo', type=str, help='Fabricante del procesador, puede ser Samsung,Qualcomm,Huawei',choices=['Samsung','Qualcomm','Huawei'])
    parser.add_argument('--interfaz', type=int, help='Interfaz del bus USB,para la ejecucion de Scat', default=2)
    args = parser.parse_args()
    modelo = args.modelo
    modelo_procesador = args.modelo
    interfaz = args.interfaz
    bus_usb = funciones.get_interfaz_dispositivo(modelo)
    bus = str(bus_usb[0])+":"+str(bus_usb[1])
    #Comando de ejecucion de Scat
    comando = ['scat', '-t', funciones.COMANDO_SEGUN_MODELO[modelo_procesador],
               '-u', '-a', bus, '-i', str(interfaz)]
    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE)
    #Direccion de la app de geolocalizacion y archivo
    app_localizacion = 'com.mendhak.gpslogger'
    localizacion_ruta_archivo = '/sdcard/GpsLogger'
    fecha = str(datetime.date.today()).replace('-', '')
    archivo_localizacion = fecha + '.gpx'
    localizacion_ruta_archivo = localizacion_ruta_archivo + '/' + archivo_localizacion
    print(f'Archivo de geolocalizacion:{localizacion_ruta_archivo}')
    funciones.acceder_paquete(app_localizacion)

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
        for linea in proceso.stdout:
            # Si ya hay celdas entrenamos el modelo
            if len(celdas)!= 0:
                t_modelo = train_model(params, celdas)

            linea_decod = linea.decode().strip()
            # Buscamos con tecnología LTE, para otra tecnología cambiar a partir de aqui
            if 'LTE PHY Cell Info' in linea_decod:
                if 'NCell' not in linea_decod: # Buscamos la celda servidora

                    linea_decod = linea_decod.replace(',', ' ,').replace(':', ' :')
                    earfcn = None
                    pci = None
                    plmn = None
                    rsrp = None
                    rsrq = None
                    lat = 0
                    long = 0
                    altitud = 0
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

                    #Datos de geolocalizacion
                    geoloc_data_str = funciones.leer_archivo_android(localizacion_ruta_archivo)
                    gpx = gpxpy.parse(geoloc_data_str)
                    for track in gpx.tracks:
                        for segment in track.segments:
                            lat = segment.points[-1].latitude
                            long = segment.points[-1].longitude
                            altitud = segment.points[-1].elevation
                    #Procesado de datos de la celda
                    serving_cell = {'earfcn': earfcn, 'pci': pci,
                                    'plmn': plmn, 'rsrp': rsrp,
                                    'rsrq': rsrq,'time': str(datetime.datetime.now()),
                                    'latitude': lat, 'longitude': long, 'elevation': altitud}

                    # Deteccion de obstaculos grandes,
                    # es necesario al menos haber establecido un pequeño recorrido de referencia
                    if len(celdas) > 10 and t_modelo:
                        data = pd.DataFrame([serving_cell])
                        data = data.drop(labels=['earfcn','pci','plmn','rsrp','rsrq','time'],axis="columns")
                        print(data)
                        data = data.to_numpy()
                        y_pred = t_modelo.predict(data)
                        print(f"RSRP previsto : {y_pred} || RSRP : {rsrp}")
                        if abs(abs(y_pred) - abs(rsrp)) <= DIFF_RSRP_MIN:
                            nuevo_intervalo = interval * 1.25
                            interval = min(10, nuevo_intervalo)
                        elif DIFF_RSRP_MIN < abs(abs(y_pred) - abs(rsrp)) < DIFF_RSRP_MAX:
                            nuevo_intervalo = interval
                            interval = nuevo_intervalo
                        elif abs(abs(y_pred) - abs(rsrp)) > DIFF_RSRP_MAX:
                            nuevo_intervalo = min(1,interval * 0.5)
                            interval = max(0.25, nuevo_intervalo)
                            if abs(abs(y_pred) - abs(rsrp)) > DIFF_RSRP_EXTR or abs(abs(celdas[-1]['rsrp']) - abs(rsrp)) > DIFF_RSRP_EXTR:
                                print("Obstáculo detectado")
                        print(f'Intervalo hasta el siguiente escaneo de {interval} segundos')

                    celdas.append(serving_cell)


                    if rsrp < MIN_LEVEL:
                        print("Baja calidad de señal")
                        if len(celda_ref.keys()) > 0:
                            print(f"Volver a {celda_ref['latitude']},{celda_ref['longitude']}")
                        else:
                            print("Buscar localizacion de referencia")
                            print(json.dumps(serving_cell, indent=2))
                    else:
                        celda_ref = serving_cell
                        print(json.dumps(serving_cell, indent=2))

                    time.sleep(interval)
            else:
                print("Ausencia total de cobertura")
                if len(celda_ref.keys()) > 0:
                    print(f"Volver a {celda_ref['latitude']},{celda_ref['longitude']}")
                else:
                    print("Buscar localizacion de referencia")


    except KeyboardInterrupt:
        proceso.terminate()
        funciones.cerrar_app(app_localizacion)
        date = str(datetime.datetime.now().strftime("%d%m%Y%H%M%S"))
        with open(f'../ficheros_mediciones/celdas{date}.json', 'w', encoding='utf-8') as archivo:
            archivo.write(json.dumps(celdas, indent=2))
        print("Tarea finalizada")

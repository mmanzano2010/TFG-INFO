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



MIN_LEVEL = -100
INTERVALO_MAX = 5
INTERVALO_MIN = 0.25

DIFF_RSRP_MIN = 2
DIFF_RSRP_MAX = 10

def train_model(params, data):
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


    num_round = min(len(celdas), 10)
    if len(celdas) > 6:
        cv_results = lgb.cv(params, train_data, num_round, nfold=3)
        best_num_boost_round = len(cv_results)

    else:
        best_num_boost_round = 1
    final_model = lgb.train(params, train_data, num_boost_round=best_num_boost_round)
    return final_model

if __name__ == '__main__':



    modelo = 'Samsung'
    modelo_procesador = 'Samsung'
    interfaz = 4
    bus_usb = funciones.get_interfaz_dispositivo(modelo)
    bus = str(bus_usb[0])+":"+str(bus_usb[1])

    comando = ['scat', '-t', funciones.COMANDO_SEGUN_MODELO[modelo_procesador],
               '-u', '-a', bus, '-i', str(interfaz)]
    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE)

    app_localizacion = 'com.mendhak.gpslogger'
    localizacion_ruta_archivo = '/sdcard/GpsLogger'
    fecha = str(datetime.date.today()).replace('-', '')
    archivo_localizacion = fecha + '.gpx'
    localizacion_ruta_archivo = localizacion_ruta_archivo + '/' + archivo_localizacion
    print(f'Archivo:{localizacion_ruta_archivo}')
    funciones.acceder_paquete(app_localizacion)

    intervalo = 2
    celdas = []
    celda_ref = {}

    params = {'num_leaves': 31, 'objective': 'regression'}
    params['metric'] = 'rmse'


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

                    geoloc_data_str = funciones.leer_archivo_android(localizacion_ruta_archivo)
                    gpx = gpxpy.parse(geoloc_data_str)
                    for track in gpx.tracks:
                        for segment in track.segments:
                            lat = segment.points[-1].latitude
                            long = segment.points[-1].longitude
                            altitud = segment.points[-1].elevation

                    serving_cell = {'earfcn': earfcn, 'pci': pci,
                                    'plmn': plmn, 'rsrp': rsrp,
                                    'rsrq': rsrq,'time': str(datetime.datetime.now()),
                                    'latitude': lat, 'longitude': long, 'elevation': altitud}

                    if len(celdas) > 10 and t_modelo:
                        data = pd.DataFrame([serving_cell])
                        data = data.drop(labels=['earfcn','pci','plmn','rsrp','rsrq','time'],axis="columns")
                        print(data)
                        data = data.to_numpy()
                        y_pred = t_modelo.predict(data)
                        print(f"RSRP previsto : {y_pred} || RSRP : {rsrp}")
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

                    time.sleep(intervalo)



    except KeyboardInterrupt:
        funciones.cerrar_app(app_localizacion)
        with open('../ficheros_mediciones/celdas.json', 'w', encoding='utf-8') as archivo:
            archivo.write(json.dumps(celdas, indent=2))
        print("Tarea finalizada")

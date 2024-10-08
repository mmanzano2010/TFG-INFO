'''Programa para analisis de las salidas del programa Scat'''

import argparse
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



MIN_LEVEL = -130
INTERVALO_MAX = 10
INTERVALO_MIN = 0.25

DIFF_RSRP_MIN = 5
DIFF_RSRP_MAX = 10
DIFF_RSRP_EXTR = 20

APP_LOCALIZACION = 'com.mendhak.gpslogger'
LOCALIZACION_RUTA_ARCHIVO = '/sdcard/GpsLogger'

def train_model(parametros, datos):
    """Entrenamiento del modelo de Aprendizaje Automatico,
    Como argumentos lleva la lista de celdas y los parametros de aprendizaje,
    devuelve un modelo entrenado"""
    celdas_entrenamiento = datos
    x_train = pd.DataFrame(celdas_entrenamiento)
    x_train = x_train.drop('earfcn',axis="columns")
    x_train = x_train.drop('time',axis="columns")
    x_train = x_train.drop('rsrq',axis="columns")
    x_train = x_train.drop('pci',axis="columns")
    x_train = x_train.drop('plmn',axis="columns")
    # print(x_train)
    y_train = x_train.pop('rsrp')
    x_train = x_train.to_numpy()
    y_train = y_train.to_numpy()
    train_data = lgb.Dataset(x_train, label=y_train)
    # Si el numero de celdas es suficiente se realiza validadcion cruzada,
    # esta parte necesita scikit-learn
    if len(celdas_entrenamiento) > 15:
        cv_results = lgb.cv(parametros, train_data)
        best_num_boost_round = len(cv_results)
        final_model = lgb.train(parametros, train_data, num_boost_round=best_num_boost_round)
        return final_model

    best_num_boost_round = 1
    final_model = lgb.train(parametros, train_data, num_boost_round=best_num_boost_round)
    return final_model

def coger_datos_geo(localizacion_ruta_archivo):
    """ Funcion para coger los datos de geolocalizacion del archivo .gpx"""
    geoloc_data_str = funciones.leer_archivo_android(localizacion_ruta_archivo)
    gpx = gpxpy.parse(geoloc_data_str)
    last_track = gpx.tracks[-1]
    last_segment = last_track.segments[-1]
    last_point = last_segment.points[-1]
    lat = last_point.latitude
    long = last_point.longitude
    altitud = last_point.elevation
    return lat,long,altitud
def procesar_linea(linea_a_decodificar, datos_geoloc):
    """Funcion para procesar una linea de analisis de cobertura LTE"""
    linea_a_decodificar = linea_a_decodificar.replace(',', ' ,').replace(':', ' :')
    earfcn = 0
    pci = 0
    plmn = 0
    rsrp = 0.0
    rsrq = 0.0
    # Busquerda de los datos en la linea
    match = re.search('EARFCN' + r'\s+(\S*)', linea_a_decodificar)
    if match:
        earfcn = int(match.group(1))
    match = re.search('PCI' + r'\s+(\S*)', linea_a_decodificar)
    if match:
        pci = int(match.group(1))
    match = re.search('PLMN' + r'\s+(\S*)', linea_a_decodificar)
    if match:
        plmn = int(match.group(1))
    match = re.search('RSRP :' + r'\s+(\S*)', linea_a_decodificar)
    if match:
        rsrp = float(match.group(1))
    match = re.search('RSRQ :' + r'\s+(\S*)', linea_a_decodificar)
    if match:
        rsrq = float(match.group(1))

    # Datos de geolocalizacion
    latitud,longitud,altitud = datos_geoloc
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
    # Busqueda lsusb
    bus_usb = funciones.get_interfaz_dispositivo(modelo)
    BUS = str(bus_usb[0]) + ":" + str(bus_usb[1])
    #Para archivo de guardado
    DATE = str(datetime.datetime.now().strftime("%d%m%Y%H%M%S"))
    file = f'celdas{DATE}.json'
    path_to_file = f'ficheros_mediciones/{file}'
    #Comando de ejecucion de Scat
    comando = ['scat', '-t', funciones.COMANDO_SEGUN_MODELO[modelo_procesador],
               '-u', '-a', BUS, '-i', str(interfaz)]
    proceso = subprocess.Popen(comando,bufsize=1,stdout = subprocess.PIPE, pipesize=1,text = True)
    #Direccion de la app de geolocalizacion y archivo
    FECHA = str(datetime.date.today()).replace('-', '')
    ARCHIVO_LOCALIZACION = FECHA + '.gpx'
    LOCALIZACION_RUTA_ARCHIVO = LOCALIZACION_RUTA_ARCHIVO + '/' + ARCHIVO_LOCALIZACION
    print(f'Archivo de geolocalizacion:{LOCALIZACION_RUTA_ARCHIVO}')
    funciones.acceder_paquete(APP_LOCALIZACION)

    #Variables generales del programa
    INTERVAL = 1
    celdas = []
    celda_ref = {}
    CICLOS = 50
    #Parametros de aprendizaje del modelo de AA
    params = {'num_leaves': 31, 'objective': 'regression','n_jobs':4,'learning_rate':0.5}
    params['metric'] = 'rmse'

    #Programa principal
    try:
        print('Escaneando...')
        INTERVAL_AUX = INTERVAL
        while True:
            INTERVAL = INTERVAL_AUX

            # Reinicio de Scat de forma periodica para la obtencion de datos mas actualizados
            if len(celdas) > CICLOS or INTERVAL >=9:
                proceso.terminate()
                time.sleep(1)
                proceso = subprocess.Popen(comando,
                                           bufsize=1,
                                           stdout=subprocess.PIPE,
                                           pipesize=1,
                                           text=True
                )
                print("REINICIO SCAT")
                # print(CICLOS)
                # print(len(celdas))

                CICLOS += 50
                INTERVAL = 1
                INTERVAL_AUX = INTERVAL
            linea = proceso.stdout.readline()
            # print(linea)
            linea_decod = linea.strip()
            # Si ya hay celdas entrenamos el modelo

            # Buscamos con tecnología LTE, para otra tecnología cambiar a partir de aqui,
            # esto comprueba que se haya detectado una celda LTE
            if 'LTE PHY Cell Info' in linea_decod and 'NCell' not in linea_decod:# Buscamos la celda servidora
                coordenadas = coger_datos_geo(LOCALIZACION_RUTA_ARCHIVO)
                serving_cell = procesar_linea(linea_decod,coordenadas)
                if len(celdas) != 0:
                    t_modelo = train_model(params,
                                           celdas
                    )
                # Calculo de intervalos con uso de modelo de AA
                if len(celdas) > 10 and t_modelo:
                    data = pd.DataFrame([serving_cell])
                    data = data.drop(labels=['earfcn', 'pci', 'plmn', 'rsrp', 'rsrq', 'time'], axis="columns")
                    print(data)
                    data = data.to_numpy()
                    y_pred = t_modelo.predict(data)
                    print(f"RSRP previsto : {y_pred} || RSRP : {serving_cell['rsrp']}")
                    if abs(abs(y_pred) - abs(serving_cell['rsrp'])) <= DIFF_RSRP_MIN:
                        nuevo_intervalo = INTERVAL * 1.25
                        INTERVAL = min(INTERVALO_MAX, nuevo_intervalo)
                        INTERVAL_AUX = INTERVAL
                    elif DIFF_RSRP_MIN < abs(abs(y_pred) - abs(serving_cell['rsrp'])) < DIFF_RSRP_MAX:
                        nuevo_intervalo = INTERVAL
                        INTERVAL = nuevo_intervalo
                        INTERVAL_AUX = INTERVAL
                    elif abs(abs(y_pred) - abs(serving_cell['rsrp'])) > DIFF_RSRP_MAX:
                        nuevo_intervalo = min(1, INTERVAL * 0.5)
                        INTERVAL = max(INTERVALO_MIN, nuevo_intervalo)
                        INTERVAL_AUX = INTERVAL
                        # Deteccion de obstaculos grandes,
                        # es necesario al menos haber establecido un pequeño recorrido de referencia
                        if abs(abs(y_pred) - abs(serving_cell['rsrp'])) > DIFF_RSRP_EXTR or abs(abs(celdas[-1]['rsrp']) - abs(serving_cell['rsrp'])) > DIFF_RSRP_EXTR:
                            print("Obstáculo detectado")
                # Notificacion del nuevo intervalo de escaneo y guardado de datos para AA
                print(f'Intervalo hasta el siguiente escaneo de {INTERVAL} segundos')

                celdas.append(serving_cell)

                # Casos de baja calidad de señal
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
                time.sleep(INTERVAL)
            elif 'LTE PHY Cell Search Measure:' in linea_decod and 'SCell' in linea_decod:
                # Estas celdas se guardan para mejorar el aprendizaje,
                # no se muestran ni intervienen en el calculo de intervalos,
                # estas lineas tienen un formato diferente a las anteriores
                latitud,longitud,altitud = coger_datos_geo(LOCALIZACION_RUTA_ARCHIVO)
                earfcn = 0
                pci = 0
                plmn = 0
                rsrp = 0.0
                rsrq = 0.0
                match = re.search('PCI' + r'\s+(\S*)', linea_decod)
                if match:
                    pci = int(match.group(1).replace(',',''))
                match = re.search('RSRP/RSRQ/RSSI:' + r'\s+(\S*)', linea_decod)
                if match:
                    valores = re.findall(r'\((.*?)\)',linea_decod)
                    valores = [float(x) for x in valores[0].split(', ')]
                    rsrp = valores[0]
                    rsrq = valores[1]
                    rssi = valores[2]
                serving_cell = {
                    'earfcn': 0,
                    'plmn': 0,
                    'pci': pci,
                    'rsrp': rsrp,
                    'rsrq': rsrq,
                    'time': str(datetime.datetime.now()),
                    'latitude': latitud, 'longitude': longitud, 'elevation': altitud}
                if serving_cell['rsrp'] != 0 or serving_cell['pci'] != 0:
                    celdas.append(serving_cell)
                    print(json.dumps(serving_cell, indent=2))


            # El resto de tecnologias y estandares de momento no se analizan
            else:
                if 'EDGE' in linea_decod or 'HSPA' in linea_decod:
                    if 'RSSI' in linea_decod:
                        match = re.search('RSSI ' + r'\s+(\S*)', linea_decod)
                        if match:
                            rssi = int(match.group(1))
                            if rssi < -130:
                                # Esto indicaria un aislamineto total de la red
                                print("Ausencia total de cobertura")
                                time.sleep(INTERVAL)

                    if len(celda_ref.keys()) > 0:
                        print(f"Volver a {celda_ref['latitude']},{celda_ref['longitude']}")
                    else:
                        print("Buscar localizacion de referencia")
                else:
                    INTERVAL_AUX = INTERVAL
                    INTERVAL = 0


    #Fin de ejecucion
    except KeyboardInterrupt:
        proceso.terminate()
        # stdout, stderr = proceso.communicate()
        funciones.cerrar_app(APP_LOCALIZACION)
        # Guardado de datos en archivo .json
        with open(f'{path_to_file}', 'w', encoding='utf-8') as archivo:
            archivo.write(json.dumps(celdas, indent=2))
            archivo.close()
        print("Tarea finalizada")
        # print(stdout)

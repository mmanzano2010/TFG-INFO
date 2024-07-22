'''Programa para analisis de las salidas del programa Scat'''

import json
import time
import datetime
import re
import subprocess
import gpxpy
import funciones

MIN_LEVEL = -100
INTERVALO_MAX = 5
INTERVALO_MIN = 0.25

DIFF_RSRP_MIN = 2
DIFF_RSRP_MAX = 10

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

    try:
        print('Escaneando...')
        for linea in proceso.stdout:

            linea_decod = linea.decode().strip()
            # Buscamos con tecnología LTE, para otra tecnología cambiar a partir de aqui
            if 'LTE PHY Cell Info' in linea_decod:
                if 'NCell' not in linea_decod:
                    linea_decod = linea_decod.replace(',', ' ,').replace(':', ' :')
                    earfcn = None
                    pci = None
                    plmn = None
                    rsrp = None
                    rsrq = None
                    lat = 0
                    long = 0
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

                    if len(celdas) > 0:
                        if abs(rsrp - celdas[-1]['rsrp']) > DIFF_RSRP_MAX:
                            intervalo = intervalo * 0.75
                            intervalo = max(intervalo, INTERVALO_MIN)
                            print(f'Modificacion del intervalo a {intervalo} segundos')
                        if abs(rsrp - celdas[-1]['rsrp']) < DIFF_RSRP_MIN:
                            intervalo = intervalo * 1.5
                            intervalo = min(intervalo, INTERVALO_MAX)
                            print(f'Modificacion del intervalo a {intervalo} segundos')

                    serving_cell = {'earfcn': earfcn, 'pci': pci,
                                    'plmn': plmn, 'rsrp': rsrp,
                                    'rsrq': rsrq,'time': str(datetime.datetime.now()),
                                    'latitude': lat, 'longitude': long}
                    celdas.append(serving_cell)
                    if rsrp < MIN_LEVEL:
                        print("Baja calidad de señal")
                        if len(celda_ref.keys()) > 0:
                            print(f'Volver a {celda_ref['latitude']},{celda_ref['longitude']}')
                        else:
                            print("Buscar localizacion de referencia")
                            print(json.dumps(serving_cell, indent=2))
                    else:
                        celda_ref = serving_cell
                        print(json.dumps(serving_cell, indent=2))

                    time.sleep(intervalo)



    except KeyboardInterrupt:
        funciones.cerrar_app(app_localizacion)
        with open('celdas.json', 'w', encoding='utf-8') as archivo:
            archivo.write(json.dumps(celdas, indent=2))
        print("Tarea finalizada")

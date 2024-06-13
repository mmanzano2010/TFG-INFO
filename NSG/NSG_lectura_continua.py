import json
import time
import datetime
import NSG_Analizador_funciones as funciones

MIN_RSSI = -90
BANDWIDTH = 50

if __name__ == '__main__':
    reading = True
    intervalo = 2
    puntos = []
    last_location = [0.0,0.0] # (latitud,longitud)
    last_rssi = 0

    while reading:
        contenido = funciones.leer_archivo_android(funciones.CONTENIDO)
        contenido = contenido.replace('España', 'Spain')
        contenido = contenido.replace('{', ' {').replace('}', '} ').replace('[', ' [').replace(']', '] ')
        contenido = contenido.splitlines()
        ultimo_contenido = contenido[-10:-1]

        for linea in ultimo_contenido:

            data = funciones.extract_json_objects(linea)
            if data is not None:

                for elemento in data:
                    print(elemento)
                    if 'latitude' in elemento.keys() and 'longitude' in elemento.keys():
                        last_location[0] = elemento['latitude']
                        last_location[1] = elemento['longitude']
                    if 'cells' in elemento.keys():

                        for ele in elemento['cells']:
                            if 'registered' in ele.keys():

                                serving_cell = ele
                                if 'rssi' in serving_cell.keys():
                                    last_rssi = serving_cell['rssi']
                                elif serving_cell['type'] == 'lte':
                                    rsrp = serving_cell['rsrp']
                                    rsrq = serving_cell['rsrq']
                                    last_rssi = (BANDWIDTH * rsrp)/rsrq
                                if len(puntos) != 0:
                                    if (abs(puntos[-1]['rssi'] - serving_cell['rssi']))>5:
                                        intervalo = intervalo*0.5
                                        if intervalo < 0.25:
                                            intervalo = 0.25
                                        print("Nuevo intervalo de "+str(intervalo)+" segundos")
                                    elif (abs(puntos[-1]['rssi'] - serving_cell['rssi']))<1 :
                                        intervalo = intervalo*1.5
                                        if intervalo > 10:
                                            intervalo = 10
                                        print("Nuevo intervalo de " + str(intervalo) + " segundos")
                                if serving_cell['rssi'] <= MIN_RSSI and len(puntos) != 0:
                                    print('Retrocede a '+str(puntos[-1]['location']))
                                elif serving_cell['rssi'] <= MIN_RSSI and len(puntos) == 0:
                                    print('Necesaria una localizacion de referencia con RSSI mayor que '+str(MIN_RSSI))
                                    print('Desplazate a una localizacion de referencia')
                                punto = {'rssi': last_rssi, 'location': last_location, 'time': datetime.datetime.now()}
                                puntos.append(punto)

                        print('****')

                    if isinstance(elemento,dict) and 'event' in elemento.keys() and elemento['event'] == 'close':
                        reading = False
                        print("Tarea finalizada")
                        intervalo = 1
                        break


            print('***___****___***')

        time.sleep(intervalo)
    print(puntos)
    with open("puntos.json", 'w', encoding='utf-8') as archivo:
        archivo.write(json.dumps(puntos, indent=2))
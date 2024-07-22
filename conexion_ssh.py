import json
import time

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
from datetime import datetime
import paramiko
import logging


if __name__ == '__main__':
    cliente = paramiko.SSHClient()
    logging.basicConfig(level=logging.DEBUG)
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    cliente.connect(hostname='192.168.1.38', username='marcos',password='1234')

    stdin, stdout, stderr = cliente.exec_command(command="source TFG/bin/activate && cat Documentos/TFG-INFO/Scat/scat_analizador.py")


    lineas = []
    # Leer la salida del comando
    try:
        while True:

            if stdout.read():
                linea = stdout.readline()
                print(linea.strip())


            # if json.loads(linea):
            #     linea = json.loads(linea)
            #
            #     data_aux = pd.DataFrame(linea)
            #     time = [datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S.%f") for fecha in data_aux['time']]
            #     linea['time'] = time
            #     lineas.append(linea)
            if stderr.read():
                print("error")
                print(stderr.read())
                break

    except KeyboardInterrupt:
        print("fin")
        cliente.exec_command("deactivate")
    cliente.close()
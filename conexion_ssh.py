import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
from datetime import datetime
import paramiko
import logging


def animate(lineas):
    xar = []
    yar = []

    for linea in lineas:
        x = linea['time']
        y = linea['rsrp']
        xar.append(x)
        yar.append(y)
    ax1.clear()
    ax1.plot(xar, yar)

if __name__ == '__main__':
    cliente = paramiko.SSHClient()
    logging.basicConfig(level=logging.DEBUG)
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    cliente.connect(hostname='192.168.1.33', username='marcos',password='1234',look_for_keys=False, allow_agent=False)

                                                                                                    #--------------Modificar y poner bien------------------#
    stdin, stdout, stderr = cliente.exec_command(command="grep 'sudo su' | 'source TFG/bin/activate' | 'python3 /Documentos/TFG-INFO/Scat/scat_analizador.py'")

    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    lineas = []
    # Leer la salida del comando
    for line in stdout.read().splitlines():

        print(line)
        linea = json.loads(line)

        data_aux = pd.DataFrame(linea)
        time = [datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S.%f") for fecha in data_aux['time']]
        linea['time'] = time
        lineas.append(linea)

    ani = animation.FuncAnimation(fig, animate(lineas), interval=1000)  # Actualiza el gráfico cada 1000 milisegundos
    plt.show()

    cliente.close()
"""Funciones para el programa de analisis de datos usando Scat"""


import subprocess

COMANDO_SEGUN_MODELO = {'Samsung': 'sec', 'Huawei': 'hisi', 'Qualcomm': 'qc'}


def get_interfaz_dispositivo(modelo):
    """Busca el numero de la inertfaz del dispositivo en el bus USB"""
    modelo = modelo.capitalize()
    process = subprocess.Popen('lsusb', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f'Error :{stderr.decode()}')
    else:
        salida = stdout.decode()
        lineas = salida.splitlines()
        for linea in lineas:
            if modelo in linea:
                # print(linea)
                linea = linea.replace(':', ' :')
                linea = linea.split(' ')
                bus = [linea[1], linea[3]]
                print(f'Bus USB:{bus}')
                return bus


def abrir_scat(modelo, bus, num_interfaz):
    """Abre el programa Scat con los argumentos que se pasan en la entrada"""
    bus_usb = '001:' + str(bus)

    comando = ['scat', '-t', COMANDO_SEGUN_MODELO[modelo],
               '-u', '-a', bus_usb, '-i', str(num_interfaz)]
    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE)
    for linea in proceso.stdout:
        linea_decod = linea.decode().strip()
        print(linea_decod)


def leer_archivo_android(ruta):
    """Ejecutar el comando adb para leer el archivo"""
    resultado = subprocess.run(['adb', 'shell', 'cat', ruta],
                               capture_output=True, text=True, errors='ignore')

    # Devolver el contenido del archivo
    return resultado.stdout


def acceder_paquete(package_name):
    """Abre la app Android que se mete en la entrada"""
    comando = f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
    result = subprocess.run(comando, shell=True, capture_output=True, text=True)
    return result


def cerrar_app(package_name):
    """Cierra la app Android que se mete en la entrada"""
    comando = f"adb shell am force-stop {package_name}"
    result = subprocess.run(comando, shell=True, capture_output=True, text=True)
    return result

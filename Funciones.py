import re
import subprocess, time, datetime

COMANDO_SEGUN_MODELO={'Samsung':'sec', 'Huawei':'hisi', 'Qualcomm':'qc'}

def get_interfaz_dispositivo(modelo):
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
                #print(linea)
                linea = linea.replace(':', ' :')
                linea = linea.split(' ')
                bus = linea[3]
                print(bus)
                return bus

def abrir_scat(modelo,bus,num_interfaz):
    bus_usb = '001:'+str(bus)

    comando = ['scat','-t', COMANDO_SEGUN_MODELO[modelo],'-u', '-a',bus_usb,'-i',str(num_interfaz)]
    proceso = subprocess.Popen(comando , stdout=subprocess.PIPE)
    for linea in proceso.stdout:
        linea_decod = linea.decode().strip()
        print(linea_decod)

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


#abrir_scat(modelo='Samsung',bus=get_interfaz_dispositivo('Samsung'),num_interfaz=4)
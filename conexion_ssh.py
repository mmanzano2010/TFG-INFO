import paramiko
import logging

if __name__ == '__main__':
    cliente = paramiko.SSHClient()
    logging.basicConfig(level=logging.DEBUG)
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    cliente.connect(hostname='192.168.1.47', username='marcos',password='mmmc2010',look_for_keys=False, allow_agent=False)


    stdin, stdout, stderr =cliente.exec_command(command='cat Documentos/TFG-INFO/celdas.json')

    # Leer la salida del comando

    for line in stdout.read().splitlines():
        print(line)
    cliente.close()
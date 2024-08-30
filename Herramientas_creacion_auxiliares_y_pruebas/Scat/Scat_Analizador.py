import json
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import sklearn
import folium
import numpy as np

def obtener_color(valor_normalizado):
    if valor_normalizado < 0.5:
        # De rojo a amarillo
        r = 255
        g = int(255 * (valor_normalizado / 0.5))
        b = 0
    else:
        # De amarillo a verde
        r = int(255 * ((1 - valor_normalizado) / 0.5))
        g = 255
        b = 0
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

if __name__ == '__main__':
    celdas_1 = None
    celdas_2 = None
    celdas_3 = None
    with open('Ultima_prueba/celdas29082024182549.json', 'r') as archivo:
        celdas_1 = json.loads(archivo.read())

        archivo.close()
    with open('Ultima_prueba/celdas29082024191059.json', 'r') as archivo:
        celdas_2 = json.loads(archivo.read())

        archivo.close()
    with open('Ultima_prueba/celdas29082024191940.json', 'r') as archivo:
        celdas_3 = json.loads(archivo.read())

        archivo.close()
    with open('Ultima_prueba/celdas29082024185314.json', 'r') as archivo:
        celdas_4 = json.loads(archivo.read())

        archivo.close()
    with open('Ultima_prueba/celdas29082024190759.json', 'r') as archivo:
        celdas_5 = json.loads(archivo.read())

        archivo.close()

    celdas_1 = pd.DataFrame(celdas_1)
    celdas_2 = pd.DataFrame(celdas_2)
    celdas_3 = pd.DataFrame(celdas_3)
    celdas_4 = pd.DataFrame(celdas_4)
    celdas_5 = pd.DataFrame(celdas_5)
    celdas = pd.concat([celdas_1,celdas_2,celdas_3,celdas_4,celdas_5],axis=0,ignore_index=True)
    celdas = celdas.sort_values(by='time')
    sns.lineplot(x=celdas['time'],y=celdas['rsrp'])
    plt.xticks([celdas['time'].iloc[0], celdas['time'].iloc[-1]], [celdas['time'].iloc[0], celdas['time'].iloc[-1]])
    plt.show()

    coordenadas = []
    for i in range(0,celdas.shape[0]):
        coordenadas.append([celdas['latitude'].iloc[i],celdas['longitude'].iloc[i]])

    mapa = folium.Map(location=[np.mean(celdas['latitude']), np.mean(celdas['longitude'])], zoom_start=25)
    valores_color = celdas['rsrp']
    valores_normalizados = (valores_color - (-130)) / ((-50) - (-130))
    cmap = plt.get_cmap('viridis')
    for coord, valor_normalizado in zip(coordenadas, valores_normalizados):
        color = cmap(valor_normalizado)
        color_hex = obtener_color(valor_normalizado)
        valor = valor_normalizado*((-50) - (-130))+(-130)
        folium.CircleMarker(
            location=coord,
            color=color_hex,
            fill = True,
            fill_opacity = 0.6,
            opacity = 1,
            popup="{} dbm".format(valor),

        ).add_to(mapa)

    # Guardar el mapa en un archivo HTML
    mapa.save('mapa_ultima_prueba.html')

    celdas.to_excel('ultima_prueba.xlsx',index=False)
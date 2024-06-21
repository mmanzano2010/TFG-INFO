import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
from datetime import datetime
import folium
def leer_archivo(archivo):
    ruta = 'mediciones/'+archivo
    with open(ruta,'r',encoding='utf-8') as file:
        entrada = file.read()
        return json.loads(entrada)
def get_color(value):
    cmap = plt.get_cmap('RdYlGn')  # Obtén el mapa de colores 'RedYellowGreen'
    norm = plt.Normalize(-135, -50)  # Normaliza los valores RSRP a la escala [0,1]

    rgba_color = cmap(norm(value))
    hex_color = mcolors.rgb2hex(rgba_color)  # Convierte RGBA a hexadecimal

    return hex_color

def make_map(data):
    m = folium.Map(location=[data['latitude'].mean(), data['longitude'].mean()], zoom_start=13)
    for i in range(0, len(data)):
        color = get_color(data.iloc[i]['rsrp'])
        folium.CircleMarker([data.iloc[i]['latitude'], data.iloc[i]['longitude']],
                            popup=data.iloc[i]['rsrp'],
                            radius=3,
                            fill=True,
                            color=color,
                            fill_color=color,
                            fill_opacity=0.5).add_to(m)
    m.render()
    m.save('map.html')
if __name__ == '__main__':
    data = leer_archivo('celdas.json')
    data_aux = pd.DataFrame(data)
    times = [datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S.%f") for fecha in data_aux['time']]
    sns.scatterplot(x=times, y=data_aux['rsrp'])
    plt.xticks(rotation=45)
    plt.show()
    make_map(data_aux)






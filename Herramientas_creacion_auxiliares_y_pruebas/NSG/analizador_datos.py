import time
import datetime
import NSG_Analizador_funciones as funciones
import lightgbm as lgb
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import sklearn
import json
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
    print("Empezando lectura...")
    reading = True
    datos = []
    datos_2 = []
    last_location = [40.713171 ,-4.073716 ,1088.700073]
    last_rsrp = 0
    with open('testLTE.log','r', encoding='utf-8',errors='ignore') as archivo:

        contenido = archivo.read()
        contenido = contenido.replace('España', 'Spain')
        contenido = contenido.replace('{', ' {').replace('}', '} _').replace('[', ' [').replace(']', '] ')
        contenido = contenido.splitlines()
        for linea in contenido:

            data = funciones.extract_json_objects(linea)
            if data is not None:

                for elemento in data:
                    print(elemento)
                    if 'time-string' in elemento.keys():
                        t = elemento['time-string']
                        t_2 = datetime.datetime.fromisoformat(t)
                        time = t_2.strftime("%H:%M:%S")
                        #time = datetime.datetime.strptime(t_2,"%H:%M:%S")
                    if 'latitude' in elemento.keys() and 'longitude' in elemento.keys() and 'altitude' in elemento.keys():
                        last_location[0] = elemento['latitude']
                        last_location[1] = elemento['longitude']
                        last_location[2] = elemento['altitude']
                    if 'type' in elemento.keys() and elemento['type'] == 'lte':
                        print("**")
                        if 'registered' in elemento.keys():
                            serving_cell = elemento
                            rsrp = elemento['rsrp']
                            pci = elemento['pci']
                            earfcn = elemento['earfcn']
                            plmn = int(str(elemento['mcc'])+str(elemento['mnc']))
                            lat = last_location[0]
                            long = last_location[1]
                            alt = last_location[2]
                            celda = {'rsrp':rsrp,'pci':pci,'plmn':plmn,'earfcn':earfcn,'time':time,'latitude':lat,'longitude':long,'altitude':alt}
                            datos.append(celda)

    archivo.close()
    with open('test_vuelta_al_pueblo.log','r', encoding='utf-8',errors='ignore') as archivo:

        contenido = archivo.read()
        contenido = contenido.replace('España', 'Spain')
        contenido = contenido.replace('{', ' {').replace('}', '} _').replace('[', ' [').replace(']', '] ')
        contenido = contenido.splitlines()
        for linea in contenido:

            data = funciones.extract_json_objects(linea)
            if data is not None:

                for elemento in data:
                    print(elemento)
                    if 'time-string' in elemento.keys():
                        t = elemento['time-string']
                        t_2 = datetime.datetime.fromisoformat(t)
                        time = t_2.strftime("%H:%M:%S")
                        #time = datetime.datetime.strptime(t_2,"%H:%M:%S")
                    if 'latitude' in elemento.keys() and 'longitude' in elemento.keys() and 'altitude' in elemento.keys():
                        last_location[0] = elemento['latitude']
                        last_location[1] = elemento['longitude']
                        last_location[2] = elemento['altitude']
                    if 'type' in elemento.keys() and elemento['type'] == 'lte':
                        print("**")
                        if 'registered' in elemento.keys():
                            serving_cell = elemento
                            rsrp = elemento['rsrp']
                            pci = elemento['pci']
                            earfcn = elemento['earfcn']
                            plmn = int(str(elemento['mcc'])+str(elemento['mnc']))
                            lat = last_location[0]
                            long = last_location[1]
                            alt = last_location[2]
                            celda = {'rsrp':rsrp,'pci':pci,'plmn':plmn,'earfcn':earfcn,'time':time,'latitude':lat,'longitude':long,'altitude':alt}
                            datos.append(celda)

    archivo.close()


    data = pd.DataFrame(datos)
    print(data)
    data = data.drop(data.index[:7])

    data = data.sort_values('time')
    celdas = pd.DataFrame(data)
    X_data = celdas['time']
    Y_data = celdas['rsrp']
    sns.lineplot(x=X_data, y=Y_data)
    plt.xticks([X_data.iloc[0], X_data.iloc[-1]], [X_data.iloc[0], X_data.iloc[-1]])
    plt.show()
    time = data.pop('time')
    correlation_matrix = data.corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
    plt.show()



    params = {'num_leaves': [10,25,30,31,45,50,65],'learning_rate': [0.2,0.3,0.4,0.5,0.6]}

    from sklearn.model_selection import GridSearchCV
    X_train = pd.DataFrame(data)
    X_train = X_train.drop('earfcn', axis="columns")
    X_train = X_train.drop('pci', axis="columns")
    X_train = X_train.drop('plmn', axis="columns")

    Y_train = X_train.pop('rsrp')

    X_eval = pd.DataFrame(datos)
    X_eval = X_eval.drop('earfcn', axis="columns")
    X_eval = X_eval.drop('pci', axis="columns")
    X_eval = X_eval.drop('plmn', axis="columns")

    Y_eval = X_eval.pop('rsrp')
    model = lgb.LGBMRegressor()

    grid_search = GridSearchCV(estimator=model, param_grid=params, cv=5, scoring='neg_mean_squared_error')
    grid_search.fit(X_train, Y_train)
    best_learning_rate = grid_search.best_params_['learning_rate']
    print(f"Mejor tasa de aprendizaje: {best_learning_rate}")



    params = {'num_leaves': 30, 'objective': 'regression', 'n_jobs': 4, 'learning_rate': 0.5}
    params['metric'] = 'rmse'
    train_data = lgb.Dataset(X_train, label=Y_train)
    cv_results = lgb.cv(params, train_data)
    best_num_boost_round = len(cv_results)
    final_model = lgb.train(params, train_data, num_boost_round=best_num_boost_round)
    Y_pred=final_model.predict(X_eval)

    mse = sklearn.metrics.mean_squared_error(Y_eval, Y_pred)
    print(f"Mean Squared Error: {mse}")

    r2 = sklearn.metrics.r2_score(Y_eval, Y_pred)
    print(f"R²: {r2}")
    best_params = grid_search.best_params_
    print(f'mejores hiperparametros{best_params}')
    celdas = data
    mapa = folium.Map(location=[celdas['latitude'].iloc[0], celdas['longitude'].iloc[0]], zoom_start=25)
    valores_color = celdas['rsrp']
    coordenadas = []

    for i in range(0,celdas.shape[0]):
        coordenadas.append([celdas['latitude'].iloc[i],celdas['longitude'].iloc[i]])
    valores_normalizados = (valores_color - (-130)) / ((-50) - (-130))
    cmap = plt.get_cmap('viridis')
    for coord, valor_normalizado in zip(coordenadas, valores_normalizados):
        color = cmap(valor_normalizado)
        color_hex = obtener_color(valor_normalizado)
        valor = valor_normalizado * (np.max(valores_color) - np.min(valores_color)) + np.min(valores_color)
        folium.CircleMarker(
            location=coord,
            color=color_hex,
            fill=True,
            fill_opacity=0.6,
            opacity=1,
            popup="{} dbm".format(valor),

        ).add_to(mapa)

    # Guardar el mapa en un archivo HTML
    mapa.save('recorridos_NSG_2.html')

    data.to_excel('pruebasNSG.xlsx',index=False)
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 16:41:40 2022

@author: jlluch
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import pandas as pd
import folium
from streamlit_folium import st_folium, folium_static
from datetime import datetime
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


APP_TITLE = 'Precio de carburantes de estaciones de servicio'
APP_SUB_TITLE = 'Fuente: Ministerio transición ecológica.'
APP_SUB_TITLE2 = 'Autor: Xavi Lluch - ai2 - UPV.    Twitter: @xavi_runner'

prov = ['ALBACETE','ALICANTE','ALMERÍA','ARABA/ÁLAVA','ASTURIAS','ÁVILA','BADAJOZ','BALEARS (ILLES)','BARCELONA','BIZKAIA','BURGOS','CÁCERES','CÁDIZ','CANTABRIA','CASTELLÓN / CASTELLÓ','CIUDAD REAL','CÓRDOBA','CORUÑA (A)','CUENCA','GIPUZKOA','GIRONA','GRANADA','GUADALAJARA','HUELVA','HUESCA','JAÉN','LEÓN','LLEIDA','LUGO',
'MADRID','MÁLAGA','MURCIA','NAVARRA','OURENSE','PALENCIA','PONTEVEDRA','RIOJA (LA)','SALAMANCA','SEGOVIA','SEVILLA','SORIA','TARRAGONA','TERUEL','TOLEDO','VALENCIA / VALÈNCIA','VALLADOLID','ZAMORA','ZARAGOZA']#,'MELILLA','CEUTA','PALMAS (LAS)','SANTA CRUZ DE TENERIFE']

cod = ['02','03', '04',  '01', '33',  '05',  '06',  '07', '08',  '48',  '09',  '10',  '11',  '39',  '12', '13',  '14',  '15', '16',  '20',  '17',  '18',  '19', '21',  '22',  
'23',  '24',  '25',  '27',  '28',  '29',  '30',  '31',  '32',  '34',  '36',  '26', '37',  '40',  '41',  '42',  '43',  '44',  '45',  '46', '47',  '49',  '50']#,  '52', '51',  '35', '38']

prov_dict = {'02': 'Albacete', '03': 'Alicante/Alacant', '04': 'Almería', '01': 'Araba/Álava', '33': 'Asturias', '05': 'Ávila', '06': 'Badajoz', '07': 'Illes Balears', '08': 'Barcelona', '48': 'Bizkaia', '09': 'Burgos', '10': 'Cáceres', '11': 'Cádiz', '39': 'Cantabria', '12': 'Castellón/Castelló', '13': 'CiudadReal', '14': 'Córdoba', '15': 'A Coruña', '16': 'Cuenca', '20': 'Gipuzkoa', '17': 'Girona', '18': 'Granada', '19': 'Guadalajara', '21': 'Huelva', '22': 'Huesca', '23': 'Jaén', '24': 'León', '25': 'Lleida', '27': 'Lugo', '28': 'Madrid', '29': 'Málaga', '30': 'Murcia', '31': 'Navarra', '32': 'Ourense', '34': 'Palencia', '35': 'Las Palmas', '36': 'Pontevedra', '26': 'La Rioja', '37': 'Salamanca', '38': 'Santa Cruz de Tenerife', '40': 'Segovia', '41': 'Sevilla', '42': 'Soria', '43': 'Tarragona', '44': 'Teruel', '45': 'Toledo', '46': 'Valencia/València', '47': 'Valladolid', '49': 'Zamora', '50': 'Zaragoza', '51': 'Ceuta', '52': 'Melilla'}

prov_geo = 'provincias.geojson'


columnas = ['Provincia', 'Municipio', 'Localidad', 'Código postal', 'Dirección','Longitud', 'Latitud', 'Toma de datos', 
           'Precio gasolina 95 E5', 'Precio gasolina 98 E5','Precio gasóleo A', 'Rótulo', 'Horario']


provincia = 'VALENCIA / VALÈNCIA'

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb
@st.cache
def cargarFichero():
    URL = "https://geoportalgasolineras.es/resources/files/preciosEESS_es.xls"
    df = pd.read_excel(URL, skiprows=3, engine="xlrd")
    # Provincia	Municipio	Localidad	Código postal	Dirección	Margen	Longitud	Latitud	Toma de datos	
    # Precio gasolina 95 E5	Precio gasolina 95 E10	Precio gasolina 95 E5 Premium	Precio gasolina 98 E5	Precio gasolina 98 E10	Precio gasóleo A	Precio gasóleo Premium	Precio gasóleo B	Precio gasóleo C	Precio bioetanol	% bioalcohol	Precio biodiésel	% éster metílico	Precio gases licuados del petróleo	Precio gas natural comprimido	Precio gas natural licuado	Precio hidrógeno	Rótulo	Tipo venta	Rem.	Horario	Tipo servicio       
    elim = ['MELILLA','CEUTA','PALMAS (LAS)','SANTA CRUZ DE TENERIFE']
    df = df[~df.Provincia.isin(elim)] 
    cols = ['Precio gasolina 95 E5','Precio gasolina 98 E5','Precio gasóleo A','Longitud','Latitud']
    df[cols]=df[cols].replace(',','.',regex=True).astype(float)
    df = df[~df['Dirección'].str.contains('CARRETERA VICALVARO A ESTACION DE')]
    FAct = "Actualizado: "+datetime.now().strftime("%d/%m/%Y %H:%M")
    return df
@st.cache
def selectData(df, combustible, provincia):
    prov_data = df.groupby('Provincia')[combustible].aggregate(['mean', 'min', 'max']).reset_index()
    prov_data['codigo'] = ''
    prov_data['codigo'] = prov_data['Provincia'].apply(lambda x: cod[prov.index(x)])
    
    dfaux = df[df.Provincia==provincia].copy()
    dfaux = dfaux[columnas]
    dfaux = dfaux.dropna(subset=[combustible]).reset_index()
    dfaux['data'] = ''
    dfaux['color'] = ''
    for i in range(len(dfaux)):
        pr = dfaux[combustible].iat[i]
        pro = dfaux.Provincia.iat[i]
        maxim = prov_data[prov_data.Provincia==pro].iat[0,3]
        minim = prov_data[prov_data.Provincia==pro].iat[0,2]
        dif = maxim-minim
        if dif == 0:
            norm = 0
        else:
            norm = (pr-minim)/dif
        if norm>=0:           
            dfaux['color'].iat[i] = '#'+rgb_to_hex((int(norm*255),int((1.0-norm)*255),0))
            dfaux['data'].iat[i] = str(dfaux.Localidad.iat[i])+"\n"+str(dfaux.Dirección.iat[i])+"\nGas 95: "+str(pr)+"€"+"\nDiesel: "+str(dfaux['Precio gasóleo A'].iat[i])+"€"
        
    return dfaux, prov_data


def display_prov_filter():    
    provincia = st.sidebar.selectbox('Provincia', prov, index=44, key='selectProv')
    return provincia

def display_comb_filter():
    return st.sidebar.radio('Combustible', ['Precio gasolina 95 E5','Precio gasolina 98 E5','Precio gasóleo A'])

def create_map(dfDib, prov_data):
    medlon=dfDib.Longitud.mean()
    medlat=dfDib.Latitud.mean()    
    m = folium.Map(location=[medlat, medlon], zoom_start=8,attr='LOL',max_bounds=True,min_zoom=5.5)
    coropletas = folium.Choropleth(geo_data=prov_geo,name="choropleth",data=prov_data,columns=["codigo", 'mean'],key_on="properties.codigo", fill_color="Greys",fill_opacity=0.4,line_opacity=1.0,legend_name="Precio medio: "+combustible)
    coropletas.add_to(m)
    for i in range(len(dfDib)):
        folium.Circle(location=[dfDib.Latitud.iat[i],dfDib.Longitud.iat[i],],popup=dfDib.data.iat[i],radius=100,color=dfDib.color.iat[i],fill=True, fill_opacity=0.7).add_to(m)
    
    if (location != None):
        folium.Marker([location.get('coords').get('latitude'), location.get('coords').get('longitude')],radius=500,popup="Mi posición",color="#3186cc",fill=True,fill_color="#3186cc").add_to(m)
    w = streamlit_js_eval(js_expressions='screen.width', key = 'SCR')

    if w>1000 :
        folium_static(m, width=900, height=600)
    else:
        folium_static(m, width=600, height=900)
   

def display_precios_provincia(df, prov_name):
    st.sidebar.subheader(f'Precio {combustible}:')    
    df = df[(df['Provincia'] == prov_name)]  
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        st.metric('Mínimo', str(df['min'].iat[0])+' €')
    with col2:        
        st.metric('Medio', str(round(df['mean'].iat[0],3))+' €')
    with col3:
        st.metric('Máximo', str(df['max'].iat[0])+' €')

def getMyPosition():
    global location 
    location = get_geolocation()
    #st.sidebar.write(location)
    
def myPosition():
    return st.sidebar.button('Mi posición', on_click= getMyPosition())

st.set_page_config(page_title=APP_TITLE,layout="wide")
st.title(APP_TITLE)
FAct = "Actualizado: "+datetime.now().strftime("%d/%m/%Y %H:%M")
st.caption(APP_SUB_TITLE+'\n'+FAct)
st.caption(APP_SUB_TITLE2)

df = cargarFichero()

myPosition()

combustible = display_comb_filter()

provincia = display_prov_filter()

dfDib, prov_data = selectData(df, combustible, provincia)

create_map(dfDib, prov_data)

baratas = dfDib.sort_values(by=combustible).reset_index(inplace=False)

st.subheader('Más baratas:')

x=10
for i in range(x+1):
    st.write(baratas.Localidad.iat[i]+' : '+baratas['Dirección'].iat[i]+' -- '+str(baratas['Código postal'].iat[i])+' -- Horario: '+str(baratas['Horario'].iat[i])+' --  Precio: '+str(baratas[combustible].iat[i])+' €')

display_precios_provincia(prov_data, provincia)
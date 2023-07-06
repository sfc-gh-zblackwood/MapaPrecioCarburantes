
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 16:41:40 2022

@author: jlluch
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium, folium_static
from datetime import datetime
import geopandas as gpd
from math import sqrt
import pytz


APP_TITLE = 'Precio de carburantes de estaciones de servicio'
APP_SUB_TITLE = 'Fuente: Ministerio transición ecológica.'
APP_SUB_TITLE2 = 'Autor: Xavi Lluch - ai2 - UPV.    Twitter:  [@xavi_runner](https://twitter.com/xavi_runner)'

prov = ['ALBACETE','ALICANTE','ALMERÍA','ARABA/ÁLAVA','ASTURIAS','ÁVILA','BADAJOZ','BALEARS (ILLES)','BARCELONA','BIZKAIA','BURGOS','CÁCERES','CÁDIZ','CANTABRIA','CASTELLÓN / CASTELLÓ','CIUDAD REAL','CÓRDOBA','CORUÑA (A)','CUENCA','GIPUZKOA','GIRONA','GRANADA','GUADALAJARA','HUELVA','HUESCA','JAÉN','LEÓN','LLEIDA','LUGO',
'MADRID','MÁLAGA','MURCIA','NAVARRA','OURENSE','PALENCIA','PONTEVEDRA','RIOJA (LA)','SALAMANCA','SEGOVIA','SEVILLA','SORIA','TARRAGONA','TERUEL','TOLEDO','VALENCIA / VALÈNCIA','VALLADOLID','ZAMORA','ZARAGOZA']#,'MELILLA','CEUTA','PALMAS (LAS)','SANTA CRUZ DE TENERIFE']

cod = ['02','03', '04',  '01', '33',  '05',  '06',  '07', '08',  '48',  '09',  '10',  '11',  '39',  '12', '13',  '14',  '15', '16',  '20',  '17',  '18',  '19', '21',  '22',  
'23',  '24',  '25',  '27',  '28',  '29',  '30',  '31',  '32',  '34',  '36',  '26', '37',  '40',  '41',  '42',  '43',  '44',  '45',  '46', '47',  '49',  '50']#,  '52', '51',  '35', '38']

prov_dict = {'02': 'Albacete', '03': 'Alicante/Alacant', '04': 'Almería', '01': 'Araba/Álava', '33': 'Asturias', '05': 'Ávila', '06': 'Badajoz', '07': 'Illes Balears', '08': 'Barcelona', '48': 'Bizkaia', '09': 'Burgos', '10': 'Cáceres', '11': 'Cádiz', '39': 'Cantabria', '12': 'Castellón/Castelló', '13': 'CiudadReal', '14': 'Córdoba', '15': 'A Coruña', '16': 'Cuenca', '20': 'Gipuzkoa', '17': 'Girona', '18': 'Granada', '19': 'Guadalajara', '21': 'Huelva', '22': 'Huesca', '23': 'Jaén', '24': 'León', '25': 'Lleida', '27': 'Lugo', '28': 'Madrid', '29': 'Málaga', '30': 'Murcia', '31': 'Navarra', '32': 'Ourense', '34': 'Palencia', '35': 'Las Palmas', '36': 'Pontevedra', '26': 'La Rioja', '37': 'Salamanca', '38': 'Santa Cruz de Tenerife', '40': 'Segovia', '41': 'Sevilla', '42': 'Soria', '43': 'Tarragona', '44': 'Teruel', '45': 'Toledo', '46': 'Valencia/València', '47': 'Valladolid', '49': 'Zamora', '50': 'Zaragoza', '51': 'Ceuta', '52': 'Melilla'}

prov_geo = 'provincias.geojson'

columnas = ['Provincia', 'Municipio', 'Localidad', 'Código postal', 'Dirección','Longitud', 'Latitud', 'Toma de datos', 
           'Precio gasolina 95 E5', 'Precio gasolina 98 E5','Precio gasóleo A', 'Rótulo', 'Horario']


def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

@st.cache_data(ttl=86400) 
def cargarFichero():
    FAct = "Actualizado: "+datetime.now(tz=pytz.timezone('Europe/Madrid')).strftime("%d/%m/%Y %H:%M")
    import requests
    import urllib3
    import io
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
    URL = "https://geoportalgasolineras.es/resources/files/preciosEESS_es.xls"

    res = requests.get(URL)
    st.write(res)
    df = pd.read_excel(io.BytesIO(res.content), skiprows=3, engine="xlrd")
    # Provincia	Municipio	Localidad	Código postal	Dirección	Margen	Longitud	Latitud	Toma de datos	
    # Precio gasolina 95 E5	Precio gasolina 95 E10	Precio gasolina 95 E5 Premium	Precio gasolina 98 E5	Precio gasolina 98 E10	Precio gasóleo A	Precio gasóleo Premium	Precio gasóleo B	Precio gasóleo C	Precio bioetanol	% bioalcohol	Precio biodiésel	% éster metílico	Precio gases licuados del petróleo	Precio gas natural comprimido	Precio gas natural licuado	Precio hidrógeno	Rótulo	Tipo venta	Rem.	Horario	Tipo servicio       
    elim = ['MELILLA','CEUTA','PALMAS (LAS)','SANTA CRUZ DE TENERIFE']
    df = df[~df.Provincia.isin(elim)] 
    cols = ['Precio gasolina 95 E5','Precio gasolina 98 E5','Precio gasóleo A','Longitud','Latitud']
    df[cols]=df[cols].replace(',','.',regex=True).astype(float)
    df = df[~df['Dirección'].str.contains('CARRETERA VICALVARO A ESTACION DE')]
    
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitud, df.Latitud))
   
    prov_data = df.groupby('Provincia')[combustible].aggregate(['mean', 'min', 'max']).reset_index()
    prov_data['codigo'] = ''
    prov_data['codigo'] = prov_data['Provincia'].apply(lambda x: cod[prov.index(x)])

    df['data'] = ''
    df['color'] = ''
    for i in range(len(df)):
        pr = df[combustible].iat[i]
        pro = df.Provincia.iat[i]
        maxim = prov_data[prov_data.Provincia==pro].iat[0,3]
        minim = prov_data[prov_data.Provincia==pro].iat[0,2]
        dif = maxim-minim
        if dif == 0:
            norm = 0
        else:
            norm = (pr-minim)/dif
        if norm>=0:           
            df['color'].iat[i] = '#'+rgb_to_hex((int(norm*255),int((1.0-norm)*255),0))
            df['data'].iat[i] = str(df.Localidad.iat[i])+"\n"+str(df.Dirección.iat[i])+"\nGas 95: "+str(pr)+"€"+"\nDiesel: "+str(df['Precio gasóleo A'].iat[i])+"€"
    return df, prov_data, gdf, FAct

def display_prov_filter():    
    provincia = st.sidebar.selectbox('Provincia', prov, index=44, key='selectProv')
    return provincia

def display_comb_filter():
    return st.sidebar.radio('Combustible', ['Precio gasolina 95 E5','Precio gasolina 98 E5','Precio gasóleo A'])

def display_precios_provincia():
    st.sidebar.subheader(f'Precio {combustible}:')    
    dfaux = prov_data[prov_data['Provincia'] == provincia]
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        st.metric('Mínimo', str(dfaux['min'].iat[0])+' €')
    with col2:        
        st.metric('Medio', str(round(dfaux['mean'].iat[0],3))+' €')
    with col3:
        st.metric('Máximo', str(dfaux['max'].iat[0])+' €')

def myPosition():
    return st.checkbox('Obtener mi posición')

def get_buffer_box_geopandas(point_lat_long, distance_km):
    # distance is d/2 of the square buffer around the point,
    # from center to corner;
    # find buffer width in meters
    buffer_width_m = (distance_km * 1000) / sqrt(2)
    (p_lat, p_long) = point_lat_long

    # Geopandas Geodataframe with a single point
    # EPSG:4326 sets Coordinate Reference System to WGS84 to match input
    wgs84_pt_gdf = gpd.GeoDataFrame(geometry = gpd.points_from_xy([p_long],[p_lat], crs='EPSG:4326'))
    
    # find suitable projected coordinate system for distance
    utm_crs = wgs84_pt_gdf.estimate_utm_crs()
    # reproject to UTM -> create square buffer (cap_style = 3) around point -> reproject back to WGS84
    wgs84_buffer = wgs84_pt_gdf.to_crs(utm_crs).buffer(buffer_width_m, cap_style=3).to_crs('EPSG:4326')
    # wgs84_buffer.bounds returns bounding box as pandas dataframe, 
    # .values[0] will extract first row as an array
    return wgs84_buffer.bounds.values[0]

st.set_page_config(page_title=APP_TITLE,layout="wide")
st.title(APP_TITLE)

combustible = display_comb_filter()
provincia = display_prov_filter()

df, prov_data, gdf, FAct = cargarFichero()

st.caption(APP_SUB_TITLE+'\n'+FAct)
st.caption(APP_SUB_TITLE2)

display_precios_provincia()

posEval = myPosition()

location = None
radio = 5

if posEval:
    location = get_geolocation()
    
if location != None:
    radio = st.slider('Distancia: ', min_value=1, max_value=15, value=5, step=1)
    latMap = location.get('coords').get('latitude')
    lonMap = location.get('coords').get('longitude')
    fg = folium.FeatureGroup(name="State bounds")
    fg.add_child(folium.Marker([latMap , lonMap ],radius=500,popup="Mi posición",color="#3186cc",fill=True,fill_color="#3186cc"))
    fg.add_child(folium.vector_layers.Circle(location=[latMap , lonMap], radius=radio*1000, color='orange'))
    bb = get_buffer_box_geopandas([location.get('coords').get('latitude'), location.get('coords').get('longitude')],radio)
    gdfSel = gdf.cx[bb[0]:bb[2], bb[1]:bb[3]]
    baratas = gdfSel.sort_values(by=combustible).reset_index(inplace=False)
    st.subheader('Más baratas a: ' + str(radio)+ ' kms de tu posición')

else :
    lonMap=df[df['Provincia'] == provincia].Longitud.mean()
    latMap=df[df['Provincia'] == provincia].Latitud.mean()    
    baratas = df[(df['Provincia'] == provincia)].sort_values(by=combustible).reset_index(inplace=False)
    st.subheader('Más baratas de la provincia: '+provincia)

x=min(len(baratas), 10)
if x>0:
    for i in range(x):
        st.write(baratas.Localidad.iat[i]+' : '+baratas['Dirección'].iat[i]+' -- '+str(baratas['Código postal'].iat[i])+' -- Horario: '+str(baratas['Horario'].iat[i])+' --  Precio: '+str(baratas[combustible].iat[i])+' €')    

m = folium.Map(location=[latMap, lonMap], zoom_start=8,attr='LOL',max_bounds=True,min_zoom=5.5)
mc = MarkerCluster()
for i in range(len(df)):
    folium.CircleMarker(location=[df.Latitud.iat[i],df.Longitud.iat[i],],popup=df.data.iat[i],radius=10,color=df.color.iat[i],fill=True, fill_opacity=0.7).add_to(mc)

mc.add_to(m)
folium.Choropleth(geo_data=prov_geo,name="choropleth",data=prov_data,columns=["codigo", 'mean'],key_on="properties.codigo", fill_color="Greys",fill_opacity=0.4,line_opacity=1.0,legend_name="Precio medio: "+combustible).add_to(m)

if location != None: 
    m.add_child(fg)

folium_static(m, width=400, height=600)

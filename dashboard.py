import os
import pandas as pd
import streamlit as st
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Análisis de Ventas", layout="wide")

# Función para cargar archivos según su extensión
def cargar_archivo(ruta):
    try:
        if ruta.endswith(".xlsx"):
            return pd.read_excel(ruta, dtype=str, header=0)
        elif ruta.endswith(".csv"):
            return pd.read_csv(ruta, dtype=str, header=0)
        else:
            raise ValueError(f"Formato de archivo no soportado: {ruta}")
    except PermissionError as e:
        st.error(f"No se pudo acceder al archivo: {ruta}. Asegúrate de que no está abierto en otra aplicación.")
        raise e

# Cargar los datos
@st.cache_data
def cargar_datos():
    # Rutas de los archivos
    rutas = {
        "FactJuneSale": "FactJuneSale.xlsx",
        "DimCity": "DimCity.xlsx",
        "DimDate": "DimDate.csv",
        "DimStockItem": "DimStockItem.csv",
        "DimCity_Coordenadas": "DimCity_Coordenadas.csv"
    }

    datos = {}
    for nombre, ruta in rutas.items():
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"El archivo {ruta} no se encuentra. Verifica las rutas.")
        datos[nombre] = cargar_archivo(ruta)

    return datos["FactJuneSale"], datos["DimCity"], datos["DimDate"], datos["DimStockItem"], datos["DimCity_Coordenadas"]

# Intentar cargar los datos
try:
    fact, dim_city, dim_date, dim_stockitem, dim_city_coordenadas = cargar_datos()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# Agregar coordenadas a DimCity desde el archivo DimCity_Coordenadas.csv
dim_city_coordenadas["City"] = dim_city_coordenadas["City"].str.strip("'")  # Limpiar posibles caracteres extra
dim_city = dim_city.merge(dim_city_coordenadas, on="City", how="left")

# Limpiar y convertir columnas numéricas en cada tabla
if "Recommended Retail Price" in dim_stockitem.columns:
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].str.replace("?", "", regex=False).str.strip()
    dim_stockitem["Recommended Retail Price"] = pd.to_numeric(dim_stockitem["Recommended Retail Price"], errors="coerce")

columnas_numericas_fact = ["Quantity", "Unit Price", "Profit", "Tax Rate", "Tax Amount"]
for columna in columnas_numericas_fact:
    if columna in fact.columns:
        fact[columna] = pd.to_numeric(fact[columna], errors="coerce")

# Sidebar - Segmentadores
st.sidebar.header("Segmentadores")
filtro_provincia = st.sidebar.multiselect("Provincia del Estado:", options=dim_city["State Province"].unique(), default=dim_city["State Province"].unique())
filtro_ciudad = st.sidebar.multiselect("Ciudad:", options=dim_city["City"].unique(), default=dim_city["City"].unique())
filtro_año_fiscal = st.sidebar.multiselect("Año Fiscal:", options=dim_date["Fiscal Year"].unique(), default=dim_date["Fiscal Year"].unique())
filtro_mes_fiscal = st.sidebar.multiselect("Mes Fiscal:", options=dim_date["Fiscal Month Label"].unique(), default=dim_date["Fiscal Month Label"].unique())

# Aplicar filtros
fact_filtrado = fact[
    (fact["City Key"].isin(dim_city[dim_city["State Province"].isin(filtro_provincia)]["City Key"])) &
    (fact["City Key"].isin(dim_city[dim_city["City"].isin(filtro_ciudad)]["City Key"])) &
    (fact["Invoice Date Key"].isin(dim_date[dim_date["Fiscal Year"].isin(filtro_año_fiscal)]["Date"])) &
    (fact["Invoice Date Key"].isin(dim_date[dim_date["Fiscal Month Label"].isin(filtro_mes_fiscal)]["Date"]))
]

# Título principal
st.title("Análisis de Ventas")

# Gráfico de Mapa de Burbujas
st.header("Tasa Impositiva Por Ciudad (Mapa)")

# Filtrar ciudades con coordenadas válidas
fact_mapa = fact_filtrado.merge(dim_city, on="City Key", how="inner")
fact_mapa = fact_mapa[(fact_mapa["Latitude"].notnull()) & (fact_mapa["Longitude"].notnull())]

if fact_mapa.empty:
    st.error("No hay datos disponibles para mostrar en el mapa. Verifica los datos y los filtros.")
else:
    fig_mapa = px.scatter_mapbox(
        fact_mapa,
        lat="Latitude",
        lon="Longitude",
        size="Tax Rate",
        color="City",
        hover_name="City",
        hover_data={"Tax Rate": True, "State Province": True},
        title="Tasa Impositiva Por Ciudad (Mapa)",
        size_max=15,
        zoom=5
    )

    fig_mapa.update_layout(mapbox_style="open-street-map")
    fig_mapa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(fig_mapa)
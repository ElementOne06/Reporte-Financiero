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

# Diccionario de coordenadas manuales
coordenadas_manual = {
    "Carson": (33.831674, -118.281693),
    "Carson City": (39.163798, -119.767403),
    "El Centro": (32.7920, -115.5631),
    "El Cerrito": (37.9161, -122.3108),
    "El Monte": (34.0736, -118.0291),
    "Austin": (30.2672, -97.7431),
    # Agrega más ciudades aquí...
}

# Cargar los datos
@st.cache_data
def cargar_datos():
    # Rutas de los archivos
    rutas = {
        "FactJuneSale": "FactJuneSale.xlsx",
        "DimCity": "DimCity.xlsx",
        "DimDate": "DimDate.csv",
        "DimStockItem": "DimStockItem.csv"
    }

    datos = {}
    for nombre, ruta in rutas.items():
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"El archivo {ruta} no se encuentra. Verifica las rutas.")
        datos[nombre] = cargar_archivo(ruta)

    return datos["FactJuneSale"], datos["DimCity"], datos["DimDate"], datos["DimStockItem"]

# Intentar cargar los datos
try:
    fact, dim_city, dim_date, dim_stockitem = cargar_datos()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# Agregar coordenadas a DimCity si no existen
coordenadas_guardadas = "DimCity_Coordenadas.csv"

if os.path.exists(coordenadas_guardadas):
    # Cargar coordenadas desde el archivo guardado
    dim_city = pd.read_csv(coordenadas_guardadas)
else:
    # Asignar coordenadas manualmente
    dim_city["Latitude"] = dim_city["City"].map(lambda x: coordenadas_manual.get(x, (None, None))[0])
    dim_city["Longitude"] = dim_city["City"].map(lambda x: coordenadas_manual.get(x, (None, None))[1])

    # Identificar ciudades sin coordenadas
    ciudades_sin_coordenadas = dim_city[dim_city["Latitude"].isnull() | dim_city["Longitude"].isnull()]
    if not ciudades_sin_coordenadas.empty:
        st.warning("Algunas ciudades no tienen coordenadas asignadas. Se asignarán valores predeterminados.")
        dim_city.loc[dim_city["Latitude"].isnull(), "Latitude"] = 0
        dim_city.loc[dim_city["Longitude"].isnull(), "Longitude"] = 0

    # Guardar las coordenadas en un archivo
    dim_city.to_csv(coordenadas_guardadas, index=False)

# Validar que las columnas necesarias existan y no estén vacías
if "City Key" not in fact.columns or "City Key" not in dim_city.columns:
    st.error("La columna 'City Key' no se encuentra en las tablas necesarias.")
    st.stop()

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

# Validar que fact_filtrado no esté vacío
if fact_filtrado.empty:
    st.error("No hay datos disponibles después de aplicar los filtros. Ajusta los filtros en la barra lateral.")
    st.stop()

# Título principal
st.title("Análisis de Ventas")

# Gráfico de Mapa de Burbujas
st.header("Tasa Impositiva Por Ciudad (Mapa)")

fact_mapa = fact_filtrado.merge(dim_city, on="City Key", how="inner")

if fact_mapa.empty:
    st.error("No hay datos disponibles para mostrar en el mapa. Verifica los datos y los filtros.")
else:
    fig_mapa = px.scatter_map(
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

    fig_mapa.update_layout(map_style="open-street-map")
    fig_mapa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(fig_mapa)
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

# Limpiar y convertir la columna "Recommended Retail Price" en dim_stockitem
if "Recommended Retail Price" in dim_stockitem.columns:
    # Convertir la columna a string para evitar errores con .str
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].astype(str)
    # Eliminar el símbolo de pregunta y espacios en blanco
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].str.replace("?", "", regex=False).str.strip()
    # Reemplazar comas por puntos para manejar decimales
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].str.replace(",", ".", regex=False)
    # Reemplazar valores no numéricos como "-" con NaN
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].replace("-", None)
    # Convertir la columna a numérico, manejando errores
    dim_stockitem["Recommended Retail Price"] = pd.to_numeric(dim_stockitem["Recommended Retail Price"], errors="coerce")


columnas_numericas_fact = ["Quantity", "Unit Price", "Profit", "Tax Rate", "Tax Amount"]
for columna in columnas_numericas_fact:
    if columna in fact.columns:
        fact[columna] = pd.to_numeric(fact[columna], errors="coerce")

# Sidebar - Segmentadores
st.sidebar.header("Segmentadores")
filtro_provincia = st.sidebar.multiselect("Provincia del Estado:", options=dim_city["State Province"].unique(), default=dim_city["State Province"].unique())

# Lista de ciudades permitidas (extraídas de la imagen)
ciudades_permitidas = [
    "Amanda Park", "Magalia", "Biggs Junction", "Cave Junction", "Jesmond Dene",
    "Glen Avon", "College Place", "Ridgemark", "Naches", "Lostine", "Kerby",
    "Long Beach", "Malott", "Twin Peaks", "South Laguna", "Venersborg", "Sekiu",
    "Lytle Creek", "Herlong", "Valley View Park"
]

# Modificar el filtro de ciudad para incluir solo las ciudades permitidas
filtro_ciudad = st.sidebar.multiselect(
    "Ciudad:",
    options=dim_city[dim_city["City"].isin(ciudades_permitidas)]["City"].unique(),
    default=dim_city[dim_city["City"].isin(ciudades_permitidas)]["City"].unique()
)

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

# Gráficos
st.header("Total de Tasa Impositiva Por Ciudad")
fig_burbujas = px.scatter(
    fact_filtrado.merge(dim_city, on="City Key"),
    x="City",
    y="Tax Rate",
    size="Tax Rate",
    color="City",
    title="Total de Tasa Impositiva Por Ciudad",
    labels={"Tax Rate": "Tasa Impositiva", "City": "Ciudad"}
)
st.plotly_chart(fig_burbujas)

st.header("Total de Profit Por Ciudad")
fig_kpi = px.bar(
    fact_filtrado.merge(dim_city, on="City Key"),
    x="City",
    y="Profit",
    title="Total de Profit Por Ciudad",
    labels={"Profit": "Profit", "City": "Ciudad"},
    text="Profit",
    color="City"
)
st.plotly_chart(fig_kpi)

st.header("Monto del Impuesto Por Provincia del Estado")
fig_anillos = px.pie(
    fact_filtrado.merge(dim_city, on="City Key"),
    names="State Province",
    values="Tax Amount",
    title="Monto del Impuesto Por Provincia del Estado",
    hole=0.4
)
st.plotly_chart(fig_anillos)

# Gráfico de líneas: Precio de Venta Por Año
st.header("Precio de Venta Por Año")

# Unir FactJuneSale con DimStockItem y DimDate
fact_lineas = fact_filtrado.merge(dim_stockitem, on="Stock Item Key", how="left") \
                           .merge(dim_date, left_on="Invoice Date Key", right_on="Date", how="left")

# Filtrar datos válidos para el gráfico
fact_lineas = fact_lineas.dropna(subset=["Calendar Year", "Recommended Retail Price"])

# Crear el gráfico de líneas
fig_lineas = px.line(
    fact_lineas,
    x="Calendar Year",  # Eje X: Año del calendario
    y="Recommended Retail Price",  # Eje Y: Precio recomendado
    title="Precio de Venta Por Año",
    markers=True
)

# Mostrar el gráfico
st.plotly_chart(fig_lineas)

# KPIs en Tarjetas
promedio_cantidad = fact["Quantity"].mean()
promedio_precio_unitario = fact["Unit Price"].mean()
total_precio_unitario = fact["Unit Price"].sum()
promedio_precio_unitario_por_cantidad = (fact["Unit Price"] * fact["Quantity"]).mean()
total_precio_unitario_por_cantidad = (fact["Unit Price"] * fact["Quantity"]).sum()

st.metric(label="Promedio de Cantidad", value=round(promedio_cantidad, 2))
st.metric(label="Promedio del Precio Unitario", value=round(promedio_precio_unitario, 2))
st.metric(label="Total de Precio Unitario", value=round(total_precio_unitario, 2))
st.metric(label="Promedio de Precio Unitario por Cantidad", value=round(promedio_precio_unitario_por_cantidad, 2))
st.metric(label="Total de Precio Unitario por Cantidad", value=round(total_precio_unitario_por_cantidad, 2))
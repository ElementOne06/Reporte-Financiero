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

# Verificar columnas necesarias
if "City Key" not in fact.columns or "City Key" not in dim_city.columns:
    st.error("La columna 'City Key' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

if "Invoice Date Key" not in fact.columns or "Date" not in dim_date.columns:
    st.error("La columna 'Invoice Date Key' o 'Date' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

# Unir tablas
fact = fact.merge(dim_city, left_on="City Key", right_on="City Key", how="left")
fact = fact.merge(dim_date, left_on="Invoice Date Key", right_on="Date", how="left")
fact = fact.merge(dim_stockitem, left_on="Stock Item Key", right_on="Stock Item Key", how="left")

# Verificar las columnas disponibles
st.write("Columnas disponibles en el DataFrame 'fact':", fact.columns)

# Verificar los primeros registros del DataFrame
st.write("Primeros registros del DataFrame 'fact':")
st.write(fact.head())

# Limpiar y convertir la columna 'Recommended Retail Price' a numérica
if "Recommended Retail Price" in fact.columns:
    fact["Recommended Retail Price"] = fact["Recommended Retail Price"].str.replace("?", "", regex=False).str.strip()
    fact["Recommended Retail Price"] = pd.to_numeric(fact["Recommended Retail Price"], errors="coerce")

# Gráfico de líneas
st.header("Precio de Venta Por Año")

# Verificar los datos utilizados en el gráfico de líneas
st.write("Datos para el gráfico de líneas:")
st.write(fact_filtrado[["Calendar Year", "Recommended Retail Price"]].dropna())

fig_lineas = px.line(
    fact_filtrado,
    x="Calendar Year",
    y="Recommended Retail Price",
    title="Precio de Venta Por Año",
    markers=True
)
st.plotly_chart(fig_lineas)

# Convertir otras columnas numéricas
if "Quantity" in fact.columns:
    fact["Quantity"] = pd.to_numeric(fact["Quantity"], errors="coerce")
if "Unit Price" in fact.columns:
    fact["Unit Price"] = pd.to_numeric(fact["Unit Price"], errors="coerce")
if "Profit" in fact.columns:
    fact["Profit"] = pd.to_numeric(fact["Profit"], errors="coerce")
if "Tax Rate" in fact.columns:
    fact["Tax Rate"] = pd.to_numeric(fact["Tax Rate"], errors="coerce")
if "Tax Amount" in fact.columns:
    fact["Tax Amount"] = pd.to_numeric(fact["Tax Amount"], errors="coerce")

# Sidebar - Segmentadores
st.sidebar.header("Segmentadores")
filtro_provincia = st.sidebar.multiselect("Provincia del Estado:", options=fact["State Province"].unique(), default=fact["State Province"].unique())
filtro_ciudad = st.sidebar.multiselect("Ciudad:", options=fact["City"].unique(), default=fact["City"].unique())
filtro_año_fiscal = st.sidebar.multiselect("Año Fiscal:", options=fact["Fiscal Year"].unique(), default=fact["Fiscal Year"].unique())
filtro_mes_fiscal = st.sidebar.multiselect("Mes Fiscal:", options=fact["Fiscal Month Label"].unique(), default=fact["Fiscal Month Label"].unique())

# Aplicar filtros
fact_filtrado = fact[
    (fact["State Province"].isin(filtro_provincia)) &
    (fact["City"].isin(filtro_ciudad)) &
    (fact["Fiscal Year"].isin(filtro_año_fiscal)) &
    (fact["Fiscal Month Label"].isin(filtro_mes_fiscal))
]

# Título principal
st.title("Análisis de Ventas")

# Gráficos
st.header("Total de Tasa Impositiva Por Ciudad")
fig_burbujas = px.scatter(
    fact_filtrado,
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
    fact_filtrado,
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
    fact_filtrado,
    names="State Province",
    values="Tax Amount",
    title="Monto del Impuesto Por Provincia del Estado",
    hole=0.4
)
st.plotly_chart(fig_anillos)

st.header("Precio de Venta Por Año")
fig_lineas = px.line(
    fact_filtrado,
    x="Calendar Year",
    y="Recommended Retail Price",
    title="Precio de Venta Por Año",
    markers=True
)
st.plotly_chart(fig_lineas)

st.header("Total de Precio Unitario por Mes en Cada Provincia del Estado")
fig_barras_agrupadas = px.bar(
    fact_filtrado,
    x="Fiscal Month Label",
    y="Unit Price",
    color="State Province",
    title="Total de Precio Unitario por Mes en Cada Provincia del Estado",
    barmode="group"
)
st.plotly_chart(fig_barras_agrupadas)

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
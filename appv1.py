import os
import pandas as pd
import streamlit as st
import plotly.express as px

# Función para cargar archivos según su extensión
def cargar_archivo(ruta):
    try:
        if ruta.endswith(".xlsx"):
            df = pd.read_excel(ruta, dtype=str, header=0)  # Forzar la primera fila como encabezado
            return df
        elif ruta.endswith(".csv"):
            df = pd.read_csv(ruta, dtype=str, header=0)  # Forzar la primera fila como encabezado
            return df
        else:
            raise ValueError(f"Formato de archivo no soportado: {ruta}")
    except PermissionError as e:
        st.error(f"No se pudo acceder al archivo: {ruta}. Asegúrate de que no está abierto en otra aplicación.")
        raise e

# Cargar los datos
@st.cache_data
def cargar_datos():
    # Rutas de los archivos
    ruta_fact = r"C:\Users\esteb\OneDrive\Documentos\Ingenieria Financiera\Semestre 2\Laboratorio de Visualizacion de Datos Financieros\Archivos - Streamlit\FactJuneSale.xlsx"
    ruta_dimcity = r"C:\Users\esteb\OneDrive\Documentos\Ingenieria Financiera\Semestre 2\Laboratorio de Visualizacion de Datos Financieros\Archivos - Streamlit\DimCity.xlsx"
    ruta_dimdate = r"C:\Users\esteb\OneDrive\Documentos\Ingenieria Financiera\Semestre 2\Laboratorio de Visualizacion de Datos Financieros\Archivos - Streamlit\DimDate.csv"
    ruta_dimstockitem = r"C:\Users\esteb\OneDrive\Documentos\Ingenieria Financiera\Semestre 2\Laboratorio de Visualizacion de Datos Financieros\Archivos - Streamlit\DimStockItem.csv"

    # Verificar existencia de los archivos y cargarlos
    archivos = {
        "FactJuneSale": ruta_fact,
        "DimCity": ruta_dimcity,
        "DimDate": ruta_dimdate,
        "DimStockItem": ruta_dimstockitem
    }
    
    datos = {}
    for nombre, ruta in archivos.items():
        if not os.path.exists(ruta):
            # Mostrar archivos disponibles en la carpeta
            carpeta = os.path.dirname(ruta)
            archivos_disponibles = os.listdir(carpeta)
            raise FileNotFoundError(
                f"El archivo no se encuentra: {ruta}\n"
                f"Archivos disponibles en la carpeta:\n{archivos_disponibles}"
            )
        datos[nombre] = cargar_archivo(ruta)

    return datos["FactJuneSale"], datos["DimCity"], datos["DimDate"], datos["DimStockItem"]

# Cargar los datos
try:
    fact, dim_city, dim_date, dim_stockitem = cargar_datos()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# Depuración: Verificar columnas
st.write("Columnas en 'FactJuneSale':", fact.columns.tolist())
st.write("Columnas en 'DimCity':", dim_city.columns.tolist())

# Verificar si las columnas necesarias están presentes
if "City Key" not in fact.columns or "City Key" not in dim_city.columns:
    st.error("La columna 'City Key' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

if "Invoice Date Key" not in fact.columns or "Date" not in dim_date.columns:
    st.error("La columna 'Invoice Date Key' o 'Date' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

# Unir tablas (si es necesario para gráficos)
fact = fact.merge(dim_city, left_on="City Key", right_on="City Key", how="left")
fact = fact.merge(dim_date, left_on="Invoice Date Key", right_on="Date", how="left")

# Convertir columnas numéricas a tipo adecuado
fact["Quantity"] = pd.to_numeric(fact["Quantity"], errors="coerce")
fact["Unit Price"] = pd.to_numeric(fact["Unit Price"], errors="coerce")
fact["Tax Rate"] = pd.to_numeric(fact["Tax Rate"], errors="coerce")

# Manejar la columna 'Recommended Retail Price'
if "Recommended Retail Price" in fact.columns:
    # Eliminar el símbolo '?' y convertir a tipo numérico
    fact["Recommended Retail Price"] = fact["Recommended Retail Price"].str.replace("?", "", regex=False)
    fact["Recommended Retail Price"] = pd.to_numeric(fact["Recommended Retail Price"], errors="coerce")
else:
    st.warning("La columna 'Recommended Retail Price' no existe en los datos. Se creará con valores predeterminados de 0.")
    fact["Recommended Retail Price"] = 0

# KPIs
promedio_cantidad = fact["Quantity"].mean(skipna=True)
promedio_precio_unitario = fact["Unit Price"].mean(skipna=True)
total_precio_unitario = fact["Unit Price"].sum(skipna=True)
promedio_precio_unitario_por_cantidad = (fact["Unit Price"] * fact["Quantity"]).mean(skipna=True)
total_precio_unitario_por_cantidad = (fact["Unit Price"] * fact["Quantity"]).sum(skipna=True)

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

# Gráficos y KPIs
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

# Gráfico de líneas (verificar columna)
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
st.metric(label="Promedio de Cantidad", value=round(promedio_cantidad, 2))
st.metric(label="Promedio del Precio Unitario", value=round(promedio_precio_unitario, 2))
st.metric(label="Total de Precio Unitario", value=round(total_precio_unitario, 2))
st.metric(label="Promedio de Precio Unitario por Cantidad", value=round(promedio_precio_unitario_por_cantidad, 2))
st.metric(label="Total de Precio Unitario por Cantidad", value=round(total_precio_unitario_por_cantidad, 2))
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
            raise FileNotFoundError(f"El archivo no se encuentra: {ruta}")
        datos[nombre] = cargar_archivo(ruta)

    return datos["FactJuneSale"], datos["DimCity"], datos["DimDate"], datos["DimStockItem"]

# Cargar los datos
try:
    fact, dim_city, dim_date, dim_stockitem = cargar_datos()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# Limpiar nombres de columnas en todos los DataFrames
def limpiar_columnas(df):
    df.columns = df.columns.str.strip()  # Elimina espacios al inicio y final
    df.columns = df.columns.str.lower()  # Convierte a minúsculas
    df.columns = df.columns.str.replace(" ", "_")  # Reemplaza espacios con guiones bajos
    return df

# Aplicar la limpieza a los DataFrames
fact = limpiar_columnas(fact)
dim_city = limpiar_columnas(dim_city)
dim_date = limpiar_columnas(dim_date)
dim_stockitem = limpiar_columnas(dim_stockitem)

# Verificar y renombrar columnas si es necesario
st.write("Columnas en 'FactJuneSale' después de limpiar:", fact.columns.tolist())
if "unit_price" not in fact.columns and "unit price" in fact.columns:
    fact.rename(columns={"unit price": "unit_price"}, inplace=True)

# Verificar si la columna 'unit_price' está presente
if "unit_price" not in fact.columns:
    st.error("La columna 'Unit Price' no existe en los datos cargados. Verifica el archivo 'FactJuneSale.xlsx'.")
    st.stop()

# Verificar otras columnas necesarias
if "city_key" not in fact.columns or "city_key" not in dim_city.columns:
    st.error("La columna 'city_key' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

if "invoice_date_key" not in fact.columns or "date" not in dim_date.columns:
    st.error("La columna 'invoice_date_key' o 'date' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

if "stock_item_key" not in fact.columns or "stock_item_key" not in dim_stockitem.columns:
    st.error("La columna 'stock_item_key' no existe en uno de los DataFrames. Verifica los nombres de las columnas.")
    st.stop()

# Unir tablas (FactJuneSale con DimCity, DimDate y DimStockItem)
fact = fact.merge(dim_city, on="city_key", how="left")
fact = fact.merge(dim_date, left_on="invoice_date_key", right_on="date", how="left")
fact = fact.merge(dim_stockitem, on="stock_item_key", how="left")

# Convertir columnas numéricas a tipo adecuado
fact["quantity"] = pd.to_numeric(fact["quantity"], errors="coerce")
fact["unit_price"] = pd.to_numeric(fact["unit_price"], errors="coerce")
fact["tax_rate"] = pd.to_numeric(fact["tax_rate"], errors="coerce")

# Manejar la columna 'recommended_retail_price' desde DimStockItem
if "recommended_retail_price" in fact.columns:
    fact["recommended_retail_price"] = pd.to_numeric(fact["recommended_retail_price"], errors="coerce")
else:
    st.error("La columna 'recommended_retail_price' no existe en 'DimStockItem'. Verifica los datos.")
    st.stop()

# KPIs
promedio_cantidad = fact["quantity"].mean(skipna=True)
promedio_precio_unitario = fact["unit_price"].mean(skipna=True)
total_precio_unitario = fact["unit_price"].sum(skipna=True)
promedio_precio_unitario_por_cantidad = (fact["unit_price"] * fact["quantity"]).mean(skipna=True)
total_precio_unitario_por_cantidad = (fact["unit_price"] * fact["quantity"]).sum(skipna=True)

# Sidebar - Segmentadores
st.sidebar.header("Segmentadores")
filtro_provincia = st.sidebar.multiselect("Provincia del Estado:", options=fact["state_province"].unique(), default=fact["state_province"].unique())
filtro_ciudad = st.sidebar.multiselect("Ciudad:", options=fact["city"].unique(), default=fact["city"].unique())
filtro_año_fiscal = st.sidebar.multiselect("Año Fiscal:", options=fact["fiscal_year"].unique(), default=fact["fiscal_year"].unique())
filtro_mes_fiscal = st.sidebar.multiselect("Mes Fiscal:", options=fact["fiscal_month_label"].unique(), default=fact["fiscal_month_label"].unique())

# Aplicar filtros
fact_filtrado = fact[
    (fact["state_province"].isin(filtro_provincia)) &
    (fact["city"].isin(filtro_ciudad)) &
    (fact["fiscal_year"].isin(filtro_año_fiscal)) &
    (fact["fiscal_month_label"].isin(filtro_mes_fiscal))
]

# Título principal
st.title("Análisis de Ventas")

# Gráficos y KPIs
st.header("Total de Tasa Impositiva Por Ciudad")
fig_burbujas = px.scatter(
    fact_filtrado,
    x="city",
    y="tax_rate",
    size="tax_rate",
    color="city",
    title="Total de Tasa Impositiva Por Ciudad",
    labels={"tax_rate": "Tasa Impositiva", "city": "Ciudad"}
)
st.plotly_chart(fig_burbujas)
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
    base_path = os.path.dirname(__file__)  # Directorio actual del script
    rutas = {
        "FactJuneSale": os.path.join(base_path, "FactJuneSale.xlsx"),
        "DimCity": os.path.join(base_path, "DimCity.xlsx"),
        "DimDate": os.path.join(base_path, "DimDate.csv"),
        "DimStockItem": os.path.join(base_path, "DimStockItem.csv")
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
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].astype(str)
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].str.replace("?", "", regex=False).str.strip()
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].str.replace(",", ".", regex=False)
    dim_stockitem["Recommended Retail Price"] = dim_stockitem["Recommended Retail Price"].replace("-", None)
    dim_stockitem["Recommended Retail Price"] = pd.to_numeric(dim_stockitem["Recommended Retail Price"], errors="coerce")

columnas_numericas_fact = ["Quantity", "Unit Price", "Profit", "Tax Rate", "Tax Amount"]
for columna in columnas_numericas_fact:
    if columna in fact.columns:
        fact[columna] = pd.to_numeric(fact[columna], errors="coerce")

# Sidebar - Segmentadores
st.sidebar.header("Segmentadores")
filtro_provincia = st.sidebar.multiselect("Provincia del Estado:", options=dim_city["State Province"].unique(), default=dim_city["State Province"].unique())

ciudades_permitidas = [
    "Amanda Park", "Magalia", "Biggs Junction", "Cave Junction", "Jesmond Dene",
    "Glen Avon", "College Place", "Ridgemark", "Naches", "Lostine", "Kerby",
    "Long Beach", "Malott", "Twin Peaks", "South Laguna", "Venersborg", "Sekiu",
    "Lytle Creek", "Herlong", "Valley View Park"
]

filtro_ciudad = st.sidebar.multiselect(
    "Ciudad:",
    options=dim_city[dim_city["City"].isin(ciudades_permitidas)]["City"].unique(),
    default=dim_city[dim_city["City"].isin(ciudades_permitidas)]["City"].unique()
)

filtro_año_fiscal = st.sidebar.multiselect("Año Fiscal:", options=dim_date["Fiscal Year"].unique(), default=dim_date["Fiscal Year"].unique())
filtro_mes_fiscal = st.sidebar.multiselect("Mes Fiscal:", options=dim_date["Month"].unique(), default=dim_date["Month"].unique())

# Aplicar filtros
fact_filtrado = fact[
    (fact["City Key"].isin(dim_city[dim_city["State Province"].isin(filtro_provincia)]["City Key"])) &
    (fact["City Key"].isin(dim_city[dim_city["City"].isin(filtro_ciudad)]["City Key"])) &
    (fact["Invoice Date Key"].isin(dim_date[dim_date["Fiscal Year"].isin(filtro_año_fiscal)]["Date"])) &
    (fact["Invoice Date Key"].isin(dim_date[dim_date["Month"].isin(filtro_mes_fiscal)]["Date"]))
]

# Título principal
st.title("Análisis de Ventas")

# KPIs en Tarjetas
promedio_cantidad = fact["Quantity"].mean()
promedio_precio_unitario = fact["Unit Price"].mean()
total_precio_unitario = fact["Unit Price"].sum()
promedio_precio_unitario_por_cantidad = (fact["Unit Price"] * fact["Quantity"]).mean()
total_precio_unitario_por_cantidad = (fact["Unit Price"] * fact["Quantity"]).sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label="Promedio de Cantidad", value=round(promedio_cantidad, 2))
col2.metric(label="Promedio del Precio Unitario", value=round(promedio_precio_unitario, 2))
col3.metric(label="Total de Precio Unitario", value=round(total_precio_unitario, 2))
col4.metric(label="Promedio de Precio Unitario por Cantidad", value=round(promedio_precio_unitario_por_cantidad, 2))
col5.metric(label="Total de Precio Unitario por Cantidad", value=round(total_precio_unitario_por_cantidad, 2))

# Gráficos
col1, col2 = st.columns(2)

with col1:
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

with col2:
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

col1, col2 = st.columns(2)

with col1:
    st.header("Monto del Impuesto Por Provincia del Estado")
    fig_anillos = px.pie(
        fact_filtrado.merge(dim_city, on="City Key"),
        names="State Province",
        values="Tax Amount",
        title="Monto del Impuesto Por Provincia del Estado",
        hole=0.4
    )
    st.plotly_chart(fig_anillos)

with col2:
    st.header("Total de Precio Unitario por Mes en cada Provincia del Estado (Barras Horizontales)")

    fact_barras = fact_filtrado.merge(dim_stockitem, on="Stock Item Key", how="left") \
                               .merge(dim_date, left_on="Invoice Date Key", right_on="Date", how="left") \
                               .merge(dim_city, on="City Key", how="left")

    fact_barras_agrupado = fact_barras.groupby(["Month", "State Province"], as_index=False).agg({"Unit Price_x": "sum"})

    fig_barras = px.bar(
        fact_barras_agrupado,
        y="Month",
        x="Unit Price_x",
        color="State Province",
        title="Total de Precio Unitario por Mes en cada Provincia del Estado",
        labels={"Month": "Mes", "Unit Price_x": "Suma de Unit Price"},
        barmode="group",
        text_auto=True
    )

    fig_barras.update_layout(
        xaxis_title="Suma de Unit Price",
        yaxis_title="Mes",
        xaxis=dict(tickformat=",")
    )

    st.plotly_chart(fig_barras)
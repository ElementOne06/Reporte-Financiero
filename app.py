import pandas as pd
import streamlit as st
import plotly.express as px

# Ruta base de los archivos
BASE_PATH = r"C:\Users\esteb\OneDrive\Documentos\Ingenieria Financiera\Semestre 2\Laboratorio de Visualizacion de Datos Financieros\Archivos - Streamlit"

# Función para cargar datos dependiendo del formato
def cargar_archivo(nombre_archivo):
    if nombre_archivo.endswith(".csv"):
        return pd.read_csv(f"{BASE_PATH}\\{nombre_archivo}")
    elif nombre_archivo.endswith(".xlsx"):
        return pd.read_excel(f"{BASE_PATH}\\{nombre_archivo}")
    else:
        st.error(f"Formato no soportado para {nombre_archivo}")
        return None

# Archivos disponibles
archivos = [
    "DimCity.xlsx",
    "DimCustomer.csv",
    "DimDate.csv",
    "DimEmployee.xlsx",
    "DimStockItem.csv",
    "FactJuneSale.xlsx",
]

# Crear la interfaz de Streamlit
st.title("Visualización de Datos Financieros")

st.sidebar.title("Opciones")
archivo_seleccionado = st.sidebar.selectbox("Selecciona un archivo para analizar", archivos)

# Cargar archivo seleccionado
df = cargar_archivo(archivo_seleccionado)

if df is not None:
    st.write(f"Mostrando datos del archivo: `{archivo_seleccionado}`")
    st.dataframe(df)

    # Mostrar algunas estadísticas básicas
    st.write("Estadísticas básicas:")
    st.write(df.describe())

    # Visualización básica de datos
    st.write("Visualización de datos:")
    columnas = df.columns.tolist()
    if len(columnas) >= 2:
        x_col = st.selectbox("Selecciona la columna X", columnas)
        y_col = st.selectbox("Selecciona la columna Y", columnas)
        fig = px.bar(df, x=x_col, y=y_col, title=f"Gráfico de {x_col} vs {y_col}")
        st.plotly_chart(fig)
    else:
        st.warning("El archivo seleccionado no tiene suficientes columnas para graficar.")
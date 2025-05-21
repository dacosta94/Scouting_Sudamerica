import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Dashboard de jugadores")

# 📥 Carga de archivo - FUERA del sidebar
st.markdown("### 📂 Cargar archivo procesado (.xlsx)")
archivo_subido = st.file_uploader("Selecciona tu archivo generado desde la sección de procesamiento", type=["xlsx"])

# 🚫 Si no se carga archivo, mostrar advertencia
if archivo_subido is None:
    st.warning("⚠️ Aún no se ha cargado el archivo procesado.")
    st.stop()

# ✅ Leer el archivo
try:
    df = pd.read_excel(archivo_subido)
    st.success("✅ Archivo cargado correctamente.")
except Exception as e:
    st.error(f"❌ Error al leer el archivo: {e}")
    st.stop()

# 🔍 Sidebar: Filtros
st.sidebar.markdown("### 🎛️ Filtros")

# Filtro por liga
ligas_disponibles = sorted(df["Liga"].dropna().unique().tolist())
ligas_opciones = ["Todas"] + ligas_disponibles
ligas_seleccionadas = st.sidebar.multiselect("Selecciona una o más ligas", options=ligas_opciones)
df_filtrado = df.copy() if "Todas" in ligas_seleccionadas or not ligas_seleccionadas else df[df["Liga"].isin(ligas_seleccionadas)]

# Filtro por Club
clubes_disponibles = sorted(df_filtrado["Club"].dropna().unique().tolist())
clubes_opciones = ["Todos"] + clubes_disponibles
clubes_seleccionados = st.sidebar.multiselect("Selecciona uno o más clubes", options=clubes_opciones)
df_filtrado = df_filtrado if "Todos" in clubes_seleccionados or not clubes_seleccionados else df_filtrado[df_filtrado["Club"].isin(clubes_seleccionados)]

# Filtros adicionales
jugadores = sorted(df_filtrado["Jugador"].dropna().unique())
jugadores_seleccionados = st.sidebar.multiselect("Jugador", jugadores)
if jugadores_seleccionados:
    df_filtrado = df_filtrado[df_filtrado["Jugador"].isin(jugadores_seleccionados)]

nacionalidades = sorted(df_filtrado["Pasaporte"].dropna().unique())
nacionalidades_seleccionadas = st.sidebar.multiselect("Nacionalidad", nacionalidades)
if nacionalidades_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado["Pasaporte"].isin(nacionalidades_seleccionadas)]

posiciones = sorted(df_filtrado["Posición Agrupada"].dropna().unique())
posiciones_seleccionadas = st.sidebar.multiselect("Posición", posiciones)
if posiciones_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado["Posición Agrupada"].isin(posiciones_seleccionadas)]

perfiles = sorted(df_filtrado["Perfil"].dropna().unique())
perfiles_seleccionados = st.sidebar.multiselect("Perfil", perfiles)
if perfiles_seleccionados:
    df_filtrado = df_filtrado[df_filtrado["Perfil"].isin(perfiles_seleccionados)]

if "Altura" in df_filtrado.columns:
    altura_min, altura_max = int(df_filtrado["Altura"].min()), int(df_filtrado["Altura"].max())
    altura_seleccionada = st.sidebar.slider("Altura (cm)", altura_min, altura_max, (altura_min, altura_max))
    df_filtrado = df_filtrado[df_filtrado["Altura"].between(*altura_seleccionada)]

if "Edad" in df_filtrado.columns:
    edad_min, edad_max = int(df_filtrado["Edad"].min()), int(df_filtrado["Edad"].max())
    edad_seleccionada = st.sidebar.slider("Edad", edad_min, edad_max, (edad_min, edad_max))
    df_filtrado = df_filtrado[df_filtrado["Edad"].between(*edad_seleccionada)]

if "Minutos jugados" in df_filtrado.columns:
    min_min, min_max = int(df_filtrado["Minutos jugados"].min()), int(df_filtrado["Minutos jugados"].max())
    minutos_seleccionados = st.sidebar.slider("Minutos jugados", min_min, min_max, (min_min, min_max))
    df_filtrado = df_filtrado[df_filtrado["Minutos jugados"].between(*minutos_seleccionados)]

# Filtro: Tipo
tipos = sorted(df_filtrado["Tipo"].dropna().unique())
tipos_seleccionados = st.sidebar.multiselect("Tipo de métrica", tipos, default=["Por 90 minutos"])
tipo_seleccionado = tipos_seleccionados[0] if tipos_seleccionados else "Por 90 minutos"
df_categoria = df_filtrado[df_filtrado["Tipo"] == tipo_seleccionado]

# Categoría de análisis
categoria = st.selectbox("Selecciona categoría de análisis", ["Resumen", "Ofensivo", "Creacion", "Defensivo", "Arquero"])

if categoria == "Resumen":
    st.markdown("### 📊 Resumen general con índices")

    columnas_resumen = [
        "Jugador", "Club", "Posición Agrupada", "Edad", "Minutos jugados",
        "indice_ofensivo", "indice_creacion", "indice_defensivo"
    ]

    columnas_resumen = [col for col in columnas_resumen if col in df_categoria.columns]

    st.dataframe(
        df_categoria[columnas_resumen]
        .sort_values("Minutos jugados", ascending=False)
        .style
        .background_gradient(subset=["indice_ofensivo", "indice_creacion", "indice_defensivo"], cmap="Greens")
        .format({col: "{:.1f}" for col in columnas_resumen if df_categoria[col].dtype in ["float64", "float32"]})
        .set_properties(**{"text-align": "center"})
        .set_table_styles([
        {"selector": "th", "props": [("font-weight", "bold"), ("text-align", "center")]}
        ])
    )


elif categoria == "Ofensivo":
    st.markdown(f"### 🎯 Métricas ofensivas ({tipo_seleccionado})")
    metricas_ofensivas = {
        "Total": ["Jugador", "Club", "indice_ofensivo", "Goles", "Asistencias", "Remates", "Regates ganados", "Toques en el área de penalti"],
        "Por 90 minutos": ["Jugador", "Club", "indice_ofensivo", "Goles/90", "Asistencias/90", "Remates/90", "Regates ganados/90", "Toques en el área de penalti/90"]
    }
    columnas = metricas_ofensivas.get(tipo_seleccionado, [])

elif categoria == "Creacion":
    st.markdown(f"### 🧠 Métricas de creacion ({tipo_seleccionado})")
    metricas_creacion = {
        "Total": ["Jugador", "Club", "indice_creacion", "Centros", "Centros al área pequeña", "Pases en el último tercio ganados", "Pases al área de penalti", "Pases en profundidad", "Jugadas claves"],
        "Por 90 minutos": ["Jugador", "Club", "indice_creacion", "Centros/90", "Centros al área pequeña/90", "Pases en el último tercio ganados/90", "Pases al área de penalti/90", "Pases en profundidad/90", "Jugadas claves/90"]
    }
    columnas = metricas_creacion.get(tipo_seleccionado, [])

elif categoria == "Defensivo":
    st.markdown(f"### 🛡️ Métricas defensivas ({tipo_seleccionado})")
    metricas_defensivas = {
        "Total": ["Jugador", "Club", "indice_defensivo", "Duelos defensivos ganados", "Interceptaciones", "Duelos aéreos ganados", "Entradas", "Tiros interceptados"],
        "Por 90 minutos": ["Jugador", "Club", "indice_defensivo", "Duelos defensivos ganados/90", "Interceptaciones/90", "Duelos aéreos ganados/90", "Entradas/90", "Tiros interceptados/90"]
    }
    columnas = metricas_defensivas.get(tipo_seleccionado, [])

elif categoria == "Arquero":
    st.markdown(f"### 🧤 Métricas de arquero ({tipo_seleccionado})")
    metricas_arquero = {
        "Total": ["Jugador", "Club", "indice_arquero", "Goles recibidos", "Goles evitados", "Paradas, %", "Salidas", "Porterías imbatidas"],
        "Por 90 minutos": ["Jugador", "Club", "indice_arquero", "Goles recibidos/90", "Goles evitados/90", "Paradas, %", "Salidas/90", "Porterías imbatidas en los 90"]
    }
    columnas = metricas_arquero.get(tipo_seleccionado, [])

if categoria != "Resumen" and columnas:
    columnas_validas = [col for col in columnas if col in df_categoria.columns]
    indice_columna = f"indice_{categoria.lower()}"

    if indice_columna in columnas_validas:
        st.dataframe(
            df_categoria[columnas_validas]
            .sort_values(indice_columna, ascending=False)
            #.head(200)
            .style
            #.background_gradient(subset=[indice_columna], cmap="Greens")
            .format({col: "{:.1f}" for col in columnas_validas if df_categoria[col].dtype in ["float64", "float32"]})
        )
    else:
        st.dataframe(
            df_categoria[columnas_validas]
            .sort_values(by=columnas_validas[2], ascending=False)
            #.head(200)
        )
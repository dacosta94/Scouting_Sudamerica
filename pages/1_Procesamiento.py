import streamlit as st
import pandas as pd
import hashlib
import os
import tempfile

st.set_page_config(page_title="Procesamiento", layout="wide")

# ========= FUNCIONES =========

def generar_id(row):
    clave = f"{row['Jugador']}_{row['País de nacimiento']}_{row['Pie']}_{row['Posición específica']}"
    return hashlib.md5(clave.encode()).hexdigest()

def procesar_archivo_excel(file):
    nombre_liga = os.path.splitext(file.name)[0].upper()
    xls = pd.ExcelFile(file)
    hoja = [s for s in xls.sheet_names if "Search" in s][0]
    df = pd.read_excel(xls, sheet_name=hoja)
    df.fillna('', inplace=True)
    df['ID_Jugador'] = df.apply(generar_id, axis=1)
    df['Liga'] = nombre_liga
    return df

def procesar_datos(df):
    import pandas as pd

    # Diccionario de agrupación de posiciones
    agrupaciones = {
        'GK': 'Portero',
        'RB': 'Lateral', 'RWB': 'Lateral',
        'RCB': 'Defensas centrales', 'CB': 'Defensas centrales', 'LCB': 'Defensas centrales',
        'LB': 'Lateral', 'LWB': 'Lateral',
        'RW': 'Mediocampistas ofensivos', 'RWF': 'Mediocampistas ofensivos',
        'RCMF': 'Mediocampistas', 'LCMF': 'Mediocampistas',
        'LW': 'Mediocampistas ofensivos', 'LWF': 'Mediocampistas ofensivos',
        'SS': 'Delantero', 'CF': 'Delantero',
        'AMF': 'Mediocampistas ofensivos',
        'DMF': 'Mediocampistas', 'RDMF': 'Mediocampistas', 'LDMF': 'Mediocampistas',
        'RAMF': 'Mediocampistas ofensivos', 'LAMF': 'Mediocampistas ofensivos'
    }

    # Diccionario para determinar el perfil
    perfil = {
        'LB': 'Izquierdo', 'LWB': 'Izquierdo', 'LCB': 'Izquierdo', 'LCMF': 'Izquierdo', 'LDMF': 'Izquierdo',
        'RB': 'Derecho', 'RWB': 'Derecho', 'RCB': 'Derecho', 'RCMF': 'Derecho', 'RDMF': 'Derecho',
        'LW': 'Izquierdo', 'LWF': 'Izquierdo', 'LAMF': 'Izquierdo',
        'RW': 'Derecho', 'RWF': 'Derecho', 'RAMF': 'Derecho',
        'CB': 'Centro', 'DMF': 'Centro', 'AMF': 'Centro', 'CF': 'Centro', 'SS': 'Centro', 'GK': 'Centro'
    }

    # Dividir posiciones
    df[['Pos1', 'Pos2']] = df['Posición específica'].str.split(',', n=1, expand=True)

    def agrupar_posiciones(row):
        if row['Pos1'] in agrupaciones:
            return agrupaciones[row['Pos1']]
        elif row['Pos2'] in agrupaciones:
            return agrupaciones[row['Pos2']]
        else:
            return None

    def determinar_perfil(row):
        if row['Pos1'] in perfil:
            return perfil[row['Pos1']]
        elif row['Pos2'] in perfil:
            return perfil[row['Pos2']]
        else:
            return 'Centro'

    df['Posición Agrupada'] = df.apply(agrupar_posiciones, axis=1)
    df['Perfil'] = df.apply(determinar_perfil, axis=1)

    # Eliminar columnas innecesarias
    columnas_a_eliminar = ['Posición específica', 'Equipo']
    df = df.drop(columns=columnas_a_eliminar)

    df.rename(columns={'Equipo durante el período seleccionado': 'Club'}, inplace=True)

    # Crear columna de 90s jugados y porcentaje minutos jugados
    df['90s_jugados'] = df['Minutos jugados'] / 90
    df['90s_jugados'] = df['90s_jugados'].round(2)

    max_minutos = 3000
    df['% minutos jugados'] = df['Minutos jugados'].apply(lambda x: min(x, max_minutos) / max_minutos * 100)

    def calcular_totales_y_ganados(df, columna_base, columna_porcentaje=None):
        if '/90' in columna_base or 'en los 90' in columna_base or 'después de' in columna_base:
            nombre_total = (
                columna_base.split('/90')[0]
                .split(' en los 90')[0]
                .split(' después de')[0]
                .strip()
            )
            # Asegurarse de que sean numéricos
            df[columna_base] = pd.to_numeric(df[columna_base], errors='coerce')
            df['90s_jugados'] = pd.to_numeric(df['90s_jugados'], errors='coerce')   

            # Calcular total
            df[nombre_total] = (df[columna_base] * df['90s_jugados']).round(0).fillna(0).astype(int)

            # Si hay porcentaje asociado
            if columna_porcentaje and columna_porcentaje in df.columns:
                # Limpieza y conversión robusta del porcentaje
                df[columna_porcentaje] = (
                    df[columna_porcentaje]
                    .astype(str)
                    .str.replace('%', '', regex=False)
                    .str.replace(',', '.', regex=False)
                )
                df[columna_porcentaje] = pd.to_numeric(df[columna_porcentaje], errors='coerce') / 100

                # Si hay datos válidos, hacer los cálculos
                if df[columna_porcentaje].notna().sum() > 0:
                    nombre_ganado = f"{nombre_total} ganados"
                    df[nombre_ganado] = (df[nombre_total] * df[columna_porcentaje]).round(0).fillna(0).astype(int)

                    nombre_ganado_90 = f"{nombre_ganado}/90"
                    df[nombre_ganado_90] = (df[columna_base] * df[columna_porcentaje]).round(2).fillna(0)
                else:
                    print(f"⚠️ Columna de porcentaje vacía: {columna_porcentaje}")

        return df

    # Lista de métricas
    metricas = [
        ('Acciones defensivas realizadas/90', None),
        ('Duelos/90', 'Duelos ganados, %'),
        ('Regates/90', 'Regates realizados, %'),
        ('Duelos atacantes/90', 'Duelos atacantes ganados, %'),
        ('Pases/90', 'Precisión pases, %'),
        ('Pases hacia adelante/90', 'Precisión pases hacia adelante, %'),
        ('Pases largos/90', 'Precisión pases largos, %'),
        ('Centros/90', 'Precisión centros, %'),
        ('Duelos defensivos/90', 'Duelos defensivos ganados, %'),
        ('Duelos aéreos en los 90', 'Duelos aéreos ganados, %'),
        ('Desmarques/90', 'Precisión desmarques, %'),
        ('Pases en el último tercio/90', 'Precisión pases en el último tercio, %'),
        ('Pases al área de penalti/90', 'Pases hacía el área pequeña, %'),
        ('Pases en profundidad/90', 'Precisión pases en profundidad, %'),
        ('Pases progresivos/90', 'Precisión pases progresivos, %'),
        ('Tiros libres directos/90', 'Tiros libres directos, %'),
        ('Aceleraciones/90', None),
        ('Posesión conquistada después de una entrada', None),
        ('Tiros interceptados/90', None),
        ('Interceptaciones/90', None),
        ('Posesión conquistada después de una interceptación', None),
        ('Faltas/90', None),
        ('Acciones de ataque exitosas/90', None),
        ('xG/90', None),
        ('Toques en el área de penalti/90', None),
        ('Carreras en progresión/90', None),
        ('Centros al área pequeña/90', None),
        ('Pases recibidos /90', None),
        ('Pases largos recibidos/90', None),
        ('Faltas recibidas/90', None),
        ('Jugadas claves/90', None),
        ('Ataque en profundidad/90', None),
        ('Centros desde el último tercio/90', None),
        ('Pases hacía atrás recibidos del arquero/90', None),
        ('Salidas/90', None),
        ('Porterías imbatidas en los 90', None),
        ('Second assists/90', None),
        ('Third assists/90', None),
        ('Tiros libres/90', None),
        ('Córneres/90', None),
        ('Entradas/90', None)
    ]

    for columna_base, columna_porcentaje in metricas:
        if columna_base in df.columns:
            df = calcular_totales_y_ganados(df, columna_base, columna_porcentaje)

    # Crear columna 'Tipo' si no existe
    if 'Tipo' not in df.columns:
        df['Tipo'] = 'Por 90 minutos'

    # Duplicar para métricas totales
    nuevo_df_totales = df.copy()
    nuevo_df_totales['Tipo'] = 'Total'

    # Concatenar ambos
    df_final = pd.concat([df, nuevo_df_totales], ignore_index=True)

    return df_final

def calcular_indice_ofensivo(df):
    columnas_y_pesos = {
        'xG': 0.3,
        'xA': 0.2,
        'Remates': 0.1,
        'Duelos atacantes ganados': 0.05,
        'Acciones de ataque exitosas':0.05,
        'Toques en el área de penalti': 0.1,
        'Regates ganados': 0.1,
        'Carreras en progresión': 0.1
    }

    for col, peso in columnas_y_pesos.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[f"{col}_puntos"] = df.groupby("Liga")[col].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0
            )
        else:
            df[f"{col}_puntos"] = 0

    df["indice_ofensivo"] = sum(
        df[f"{col}_puntos"] * peso for col, peso in columnas_y_pesos.items()
    )

    # Escalar para que el mejor de cada liga tenga 10
    df["indice_ofensivo"] = df.groupby("Liga")["indice_ofensivo"].transform(
        lambda x: (x / x.max()) * 10 if x.max() > 0 else 0
    )

    columnas_aux = [f"{col}_puntos" for col in columnas_y_pesos]
    df.drop(columns=columnas_aux, inplace=True, errors='ignore')

    return df

def calcular_indice_creacion(df):
    columnas_y_pesos = {
        'Centros': 0.05,
        'Centros al área pequeña': 0.1,
        'xA': 0.15,
        'Pases progresivos ganados':0.15,
        'Pases en el último tercio ganados': 0.10,
        'Pases al área de penalti': 0.15,
        'Pases en profundidad': 0.15,
        'Jugadas claves': 0.15
    }

    for col, peso in columnas_y_pesos.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[f"{col}_puntos"] = df.groupby("Liga")[col].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0
            )
        else:
            df[f"{col}_puntos"] = 0

    # Sumar ponderaciones (sin multiplicar aún por 10)
    df['indice_creacion'] = sum(
        df[f"{col}_puntos"] * peso for col, peso in columnas_y_pesos.items()
    )

    # Escalar para que el mejor de cada liga tenga 10
    df["indice_creacion"] = df.groupby("Liga")["indice_creacion"].transform(
        lambda x: (x / x.max()) * 10 if x.max() > 0 else 0
    )

    # Eliminar columnas auxiliares
    columnas_aux = [f"{col}_puntos" for col in columnas_y_pesos]
    df.drop(columns=columnas_aux, inplace=True, errors='ignore')

    return df

def calcular_indice_defensivo(df):
    columnas_y_pesos = {
        'Duelos defensivos ganados': 0.2,
        'Interceptaciones': 0.2,
        'Duelos aéreos ganados': 0.3,
        'Entradas': 0.2,
        'Tiros interceptados': 0.1
    }

    for col, peso in columnas_y_pesos.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[f"{col}_puntos"] = df.groupby("Liga")[col].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0
            )
        else:
            df[f"{col}_puntos"] = 0

    df['indice_defensivo'] = sum(
        df[f"{col}_puntos"] * peso for col, peso in columnas_y_pesos.items()
    )

    df["indice_defensivo"] = df.groupby("Liga")["indice_defensivo"].transform(
        lambda x: (x / x.max()) * 10 if x.max() > 0 else 0
    )

    columnas_aux = [f"{col}_puntos" for col in columnas_y_pesos]
    df.drop(columns=columnas_aux, inplace=True, errors='ignore')

    return df

def calcular_indice_arquero(df):
    def normalizar_mayor_mejor(valor, min_val, max_val):
        if pd.isna(valor) or max_val == min_val:
            return 1 if valor >= 0 else 0
        return (valor - min_val) / (max_val - min_val)

    def normalizar_menor_mejor(valor, min_val, max_val):
        if pd.isna(valor) or max_val == min_val:
            return 1
        return (max_val - valor) / (max_val - min_val)

    columnas_y_funcion_peso = {
        'Goles recibidos': ('menor', 0.15),
        'Goles evitados': ('mayor', 0.35),
        'Paradas, %': ('mayor', 0.20),
        'Salidas': ('mayor', 0.15),
        'Porterías imbatidas': ('menor', 0.15)
    }

    for col, (tipo, peso) in columnas_y_funcion_peso.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

            min_por_liga = df.groupby("Liga")[col].transform("min")
            max_por_liga = df.groupby("Liga")[col].transform("max")

            if tipo == 'mayor':
                df[f"{col}_puntos"] = df[[col, 'Liga']].apply(
                    lambda row: normalizar_mayor_mejor(row[col], 
                                                       min_por_liga[row.name], 
                                                       max_por_liga[row.name]),
                    axis=1
                )
            else:
                df[f"{col}_puntos"] = df[[col, 'Liga']].apply(
                    lambda row: normalizar_menor_mejor(row[col], 
                                                       min_por_liga[row.name], 
                                                       max_por_liga[row.name]),
                    axis=1
                )
        else:
            df[f"{col}_puntos"] = 0

    # Calcular índice sin escalar aún
    df["indice_arquero"] = sum(
        df[f"{col}_puntos"] * peso for col, (_, peso) in columnas_y_funcion_peso.items()
    )

    # Escalar dentro de cada liga (máximo de cada liga = 10)
    df["indice_arquero"] = df.groupby("Liga")["indice_arquero"].transform(
        lambda x: (x / x.max()) * 10 if x.max() > 0 else 0
    )

    # Limpiar columnas auxiliares
    columnas_aux = [f"{col}_puntos" for col in columnas_y_funcion_peso]
    df.drop(columns=columnas_aux, inplace=True, errors='ignore')

    return df


# ========= INTERFAZ STREAMLIT =========

st.title("🌎 Unificador y Procesador de Ligas - Sudamérica")

st.markdown("""
1. Sube archivos Excel exportados desde Wyscout.  
2. Asegúrate de que el **nombre del archivo sea el país en mayúsculas** (ej: `ECUADOR.xlsx`).  
3. El sistema unifica todos los datos y los transforma con métricas avanzadas.
""")

archivos_cargados = st.file_uploader("📁 Sube tus archivos Excel", type=["xlsx"], accept_multiple_files=True)

if archivos_cargados:
    if st.button("🔄 Procesar y Unificar"):
        dataframes = []
        for archivo in archivos_cargados:
            try:
                df = procesar_archivo_excel(archivo)
                dataframes.append(df)
                st.success(f"✔ Procesado: {archivo.name}")
            except Exception as e:
                st.error(f"⚠ Error en {archivo.name}: {e}")

        if dataframes:
            df_final = pd.concat(dataframes, ignore_index=True)
            df_final = procesar_datos(df_final)
            df_final = calcular_indice_ofensivo(df_final)
            df_final = calcular_indice_creacion(df_final)
            df_final = calcular_indice_defensivo(df_final)
            df_final = calcular_indice_arquero(df_final)


            st.write("✅ Archivos procesados. Vista previa:")
            st.dataframe(df_final.head(10))

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                df_final.to_excel(tmp.name, index=False)
                st.download_button(
                    label="📥 Descargar archivo final procesado",
                    data=open(tmp.name, 'rb'),
                    file_name="Base_Procesada_Sudamerica.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

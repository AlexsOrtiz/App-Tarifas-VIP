from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from markupsafe import escape
import pandas as pd
import os
import glob
import re
import sqlite3
from typing import Tuple
import pandas as pd
import numpy as np
from unidecode import unidecode
from flask import send_file, jsonify, request
from io import BytesIO
import sqlite3
import os
import locale

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'
 

# Lista de municipios disponibles
MUNICIPALITIES = [
    "Guacarí", "Jamundí", "El Cerrito", "Quimbaya", "Circasia",
    "Puerto Asís", "Jericó", "Ciudad Bolívar", "Pueblorico", "Tarso", "Santa Bárbara"
]

# Función global para obtener la abreviatura deseada del municipio
# Lista de municipios disponibles
def get_file_suffix(municipio):
    abbreviations = {
        "Guacarí": "GU",
        "Jamundí": "JA",
        "El Cerrito": "CE",
        "Quimbaya": "QY",
        "Circasia": "CI",
        "Puerto Asís": "PA",
        "Jericó": "JE",
        "Ciudad Bolívar": "CB",
        "Pueblorico": "PR",
        "Tarso": "TA",
        "Santa Bárbara": "SB"
    }
    return abbreviations.get(municipio, municipio.upper())

# Función para construir la ruta base según el municipio seleccionado
import os
import re
import platform
from pathlib import Path

def get_base_path(municipio):
    mapping = {
        "Tarso": "10. C&C - Tarso - 2022",
        "Santa Bárbara": "11. UT - Santa Bárbara - 2022",
        "Pueblorico": "09. C&C - Pueblorico - 2022",
        "Jericó": "07. C&C - Jericó - 2021",
        "Jamundí": "02. UT - Jamundí - 2014",
        "Ciudad Bolívar": "08. C&C - Ciudad Bolívar - 2022",
        "Quimbaya": "04. UT - Quimbaya - 2015",
        "Puerto Asís": "06. UT - Puerto Asís - 2015",
        "Guacarí": "01. UT - Guacarí - 2014",
        "Circasia": "05. UT - Circasia - 2015",
        "El Cerrito": "03. UT - El Cerrito - 2015"
    }
    if municipio not in mapping:
        raise ValueError("Municipio no reconocido")

    if platform.system() == "Windows":
        home_dir = str(Path.home())
        base_path = os.path.join(
            home_dir,
            "OneDrive - Canales y contactos",
            "10. Gestión de proyectos",
            mapping[municipio],
            "03. Ejecución",
            "03. Gestión comercial",
            "08. Informes Gerenciales"
        )
    else:
        home_dir = str(Path.home())
        base_path = os.path.join(
            home_dir,
            "Library/CloudStorage/OneDrive-Canalesycontactos",
            "10. Gestión de proyectos",
            mapping[municipio],
            "03. Ejecución",
            "03. Gestión comercial",
            "08. Informes Gerenciales"
        )

    base_path = os.path.join(base_path, "2024")

    # Buscar la carpeta cuyo nombre, sin el prefijo numérico, sea "informes cyt"
    import re
    print(f"[DEBUG] Directorio base_path: {base_path}")
    print(f"[DEBUG] Carpetas encontradas en base_path:", os.listdir(base_path))
    target_folder = None
    for folder in os.listdir(base_path):
        folder_clean = re.sub(r'^\d+\.\s*', '', folder).lower()
        print(f"[DEBUG] Analizando carpeta: '{folder}' (limpia: '{folder_clean}')")
        if folder_clean == "informes cyt":
            target_folder = folder
            print(f"[DEBUG] Carpeta seleccionada como Informes CyT: {target_folder}")
            break
    if target_folder is None:
        raise FileNotFoundError("No se encontró la carpeta que se llame 'Informes CyT'")
    ruta_final = os.path.join(base_path, target_folder, '3. Consumo')
    print(f"[DEBUG] Ruta final seleccionada: {ruta_final}")
    return ruta_final


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/municipios', methods=['GET'])
def get_municipios():
    """Devuelve la lista de municipios disponibles."""
    return jsonify({'municipios': MUNICIPALITIES})

@app.route('/municipio/suffix', methods=['GET'])
def municipio_suffix():
    """Devuelve la abreviatura estándar para un municipio."""
    municipio = request.args.get('municipio')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    return jsonify({'suffix': get_file_suffix(municipio)})

@app.route('/municipio/basepath', methods=['GET'])
def municipio_basepath():
    """Devuelve la ruta base de trabajo para un municipio."""
    municipio = request.args.get('municipio')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta = get_base_path(municipio)
        return jsonify({'base_path': ruta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/consolidar', methods=['POST'])
def consolidar():
    data = request.get_json()
    municipio = data.get('municipio')
    if not municipio:
        print('[PROGRESO] Municipio no recibido')
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        print(f'[PROGRESO] Obteniendo ruta base para municipio: {municipio}')
        ruta_base = get_base_path(municipio)
        print(f'[PROGRESO] Ruta base obtenida: {ruta_base}')
        print('[PROGRESO] Iniciando consolidación de archivos Excel y DB...')
        ruta_csv, ruta_db = consolidar_excel_y_db(ruta_base)
        print(f'[PROGRESO] Consolidación completada. CSV: {ruta_csv}, DB: {ruta_db}')
        return jsonify({'ruta_csv': ruta_csv, 'ruta_db': ruta_db})
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        return jsonify({'error': str(e)}), 500


def consolidar_excel_y_db(
    ruta_carpeta: str,
    nombre_csv: str = 'master_consumos.csv',
    nombre_db: str = 'consumo.db'
) -> Tuple[str, str]:
    print('[PROGRESO] Buscando archivos .xlsx en la carpeta...')
    patron = os.path.join(ruta_carpeta, '*.xlsx')
    archivos = [
        f for f in glob.glob(patron)
        if not (f.endswith('master_consumos.xlsx') or f.endswith('master_consumos.csv'))
    ]
    if not archivos:
        print('[ERROR] No se encontraron archivos .xlsx')
        raise FileNotFoundError(f"No se encontraron archivos .xlsx en {ruta_carpeta}")
    print(f'[PROGRESO] {len(archivos)} archivos encontrados.')

    dfs = []
    for fichero in archivos:
        print(f'[PROGRESO] Leyendo archivo: {fichero}')
        df = pd.read_excel(fichero)
        # NO normalizamos los nombres de columnas para conservar el formato original
        dfs.append(df)

    print('[PROGRESO] Concatenando DataFrames...')
    df = pd.concat(dfs, ignore_index=True)

    print('[PROGRESO] Canonicalizando S_ID...')
    stripped_ids = {
        re.sub(r'^0+', '', str(sid)) or '0'
        for sid in df['S_ID']
    }
    def canonical_id(row):
        sid = str(row['S_ID'])
        comp = str(row.get('S_COMERCIALIZADOR', '')).lower()
        digits = re.sub(r'\D', '', sid)
        stripped = digits.lstrip('0') or '0'
        if 'celsia' in comp and stripped.endswith('0'):
            candidate = stripped[:-1]
            if candidate in stripped_ids:
                return candidate
        return stripped

    df['S_ID_CANON'] = df.apply(canonical_id, axis=1)

    print('[PROGRESO] Ordenando por S_ID_CANON, S_NIC y periodo...')
    periodo_split = df['S_PERIODO'].astype(str).str.split('-', n=1, expand=True)
    df['__anio'] = pd.to_numeric(periodo_split[0], errors='coerce')
    df['__mes']  = pd.to_numeric(periodo_split[1], errors='coerce')
    df = df.sort_values(['S_ID_CANON', 'S_NIC', '__anio', '__mes']).reset_index(drop=True)
    df = df.drop(columns=['__anio', '__mes'])

    print('[PROGRESO] Guardando CSV maestro...')
    # Columnas originales exactas más la columna canónica
    columnas_salida = [
        'S_MPIO', 'S_COMERCIALIZADOR', 'S_ID', 'S_NIC', 'S_NOMBRE',
        'S_PERIODO', 'S_FECHA_FACT', 'S_TIPO_USO', 'S_ESTRATO',
        'S_ZONA', 'S_BARRIO_VEREDA', 'S_DIRECCION', 'S_TIPO_MERCADO',
        'S_CICLO', 'CANT_KW', 'VR_CONSUMO_PESOS', 'VR_FACT',
        'VR_RECAUDO', 'VR_CARTERA_GENERADA', 'VR_CARTERA_RECUPERADA',
        'S_ID_CANON'
    ]
    df[columnas_salida].to_csv(os.path.join(ruta_carpeta, nombre_csv), index=False)

    print('[PROGRESO] Guardando base de datos SQLite...')
    ruta_db = os.path.join(ruta_carpeta, nombre_db)
    conn = sqlite3.connect(ruta_db)
    df.to_sql('lecturas', conn, if_exists='replace', index=False)
    conn.close()

    print('[PROGRESO] Consolidación finalizada.')
    return os.path.join(ruta_carpeta, nombre_csv), ruta_db



def normalizar(ruta_csv: str, ruta_db: str) -> None:
    """
    Lee la base de datos SQLite (tabla lecturas), normaliza y calcula los porcentajes de tarifa según la lógica unificada,
    y guarda los resultados tanto en la base de datos como en el archivo CSV.
    """
    print(f"[PROGRESO] Leyendo DB: {ruta_db}")
    import pandas as pd
    import sqlite3
    # Leer desde la base de datos
    conn = sqlite3.connect(ruta_db)
    df = pd.read_sql_query('SELECT * FROM lecturas', conn)
    conn.close()
    # --- Normalizar S_TIPO_USO ---
    antes_tipo = df["S_TIPO_USO"].value_counts(dropna=False).to_dict()
    def _unificar_tipo(val):
        if pd.isna(val):
            return val
        s = re.sub(r'[^a-z]', '', str(val).lower())
        if 'residencial' in s or 'resi' in s:
            return "RESIDENCIAL"
        if 'comercial' in s or 'comer' in s:
            return "COMERCIAL"
        if 'industrial' in s or 'industria' in s or 'indust' in s:
            return "INDUSTRIAL"
        if 'oficial' in s:
            return "OFICIAL"
        return val
    print("[PROGRESO] Normalizando S_TIPO_USO en DB...")
    df["S_TIPO_USO"] = df["S_TIPO_USO"].apply(_unificar_tipo)
    despues_tipo = df["S_TIPO_USO"].value_counts(dropna=False).to_dict()
    print(f"[RESUMEN] Valores antes de normalizar S_TIPO_USO en DB: {antes_tipo}")
    print(f"[RESUMEN] Valores después de normalizar S_TIPO_USO en DB: {despues_tipo}")
    # --- Normalizar S_CICLO ---
    antes_ciclo = df["S_CICLO"].value_counts(dropna=False).to_dict()
    def _unificar_ciclo(val):
        if pd.isna(val):
            return val
        s = str(val).lower()
        if 'mensual' in s:
            return "MENSUAL"
        if 'bimestral' in s:
            return "BIMESTRAL"
        if 'trimestral' in s:
            return "TRIMESTRAL"
        return val
    print("[PROGRESO] Normalizando S_CICLO en DB...")
    df["S_CICLO"] = df["S_CICLO"].apply(_unificar_ciclo)
    despues_ciclo = df["S_CICLO"].value_counts(dropna=False).to_dict()
    print(f"[RESUMEN] Valores antes de normalizar S_CICLO en DB: {antes_ciclo}")
    print(f"[RESUMEN] Valores después de normalizar S_CICLO en DB: {despues_ciclo}")

    # --- Leer lógica de porcentajes y UVT desde el Excel unificado ---
    path_logica = os.path.join(os.path.dirname(__file__), 'logica_porcentajes_guacari.xlsx')
    if not os.path.exists(path_logica):
        raise FileNotFoundError("No existe el archivo de lógica de porcentajes. Descárgalo primero.")
    df_logica = pd.read_excel(path_logica)

    # --- Calcular S_PORCENTAJE_TARIFA (real) y S_PORCENTAJE_TARIFA_ESPERADO (esperado) ---
    print("[PROGRESO] Calculando S_PORCENTAJE_TARIFA y S_PORCENTAJE_TARIFA_ESPERADO...")
    def buscar_logica(row, col):
        try:
            municipio = unidecode(str(row['S_MPIO'])).strip().upper()
            tipo_uso = unidecode(str(row['S_TIPO_USO'])).strip().upper()
            tipo_mercado = unidecode(str(row['S_TIPO_MERCADO'])).strip().upper()
            estrato = unidecode(str(row['S_ESTRATO'])).strip().upper()
            periodo = str(row['S_PERIODO'])
            try:
                anio = int(periodo.split('-')[0])
            except Exception:
                anio = 2025
            filtro = (
                (df_logica['S_MPIO'].apply(lambda x: unidecode(str(x)).strip().upper()) == municipio) &
                (df_logica['S_TIPO_USO'].apply(lambda x: unidecode(str(x)).strip().upper()) == tipo_uso) &
                (df_logica['S_TIPO_MERCADO'].apply(lambda x: unidecode(str(x)).strip().upper()) == tipo_mercado) &
                (df_logica['S_ESTRATO'].apply(lambda x: unidecode(str(x)).strip().upper()) == estrato) &
                (df_logica['AÑO'] == anio)
            )
            fila = df_logica[filtro]
            if fila.empty:
                return None
            return fila.iloc[0][col]
        except KeyError as e:
            print(f"[ERROR] KeyError: {e}. Columnas disponibles: {list(row.index)}. Valores de la fila: {row.to_dict()}")
            raise

    def calc_porcentaje_real(row):
        try:
            vr_fact = float(row['VR_FACT'])
            vr_consumo = float(row['VR_CONSUMO_PESOS'])
            if vr_consumo == 0:
                return None
            return int(round(100 * vr_fact / vr_consumo, 0))
        except Exception:
            return None

    def calc_porcentaje_esperado(row):
        try:
            cant_kw = float(row.get('CANT_KW', 0))
        except Exception:
            cant_kw = 0
        if cant_kw > 173:
            return buscar_logica(row, 'S_PORCENTAJE_TARIFA')
        else:
            porcentaje_uvt = buscar_logica(row, 'S_PORCENTAJE_UVT')
            uvt = buscar_logica(row, 'UVT')
            if porcentaje_uvt is not None and uvt is not None:
                return (porcentaje_uvt / 100.0) * float(uvt)
            else:
                return None

    df['S_PORCENTAJE_TARIFA'] = df.apply(calc_porcentaje_real, axis=1)
    df['S_VALI_TARIFARIA'] = df.apply(calc_porcentaje_esperado, axis=1)

    # --- Guardar en la base de datos ---
    print(f"[PROGRESO] Guardando normalización en DB: {ruta_db}")
    conn = sqlite3.connect(ruta_db)
    df.to_sql('lecturas', conn, if_exists='replace', index=False)
    conn.close()
    print("[PROGRESO] Actualización de la tabla 'lecturas' en DB: EXITOSA")

    # --- Guardar copia en CSV ---
    print(f"[PROGRESO] Guardando copia en CSV: {ruta_csv}")
    df.to_csv(ruta_csv, index=False)
    print("[RESUMEN] Columnas finales en master_consumos.csv:")
    print(list(df.columns))
    print("[PROGRESO] Normalización completa en DB y CSV.")


@app.route('/normalizar', methods=['POST'])
def normalizar_endpoint():
    data = request.get_json()
    municipio = data.get('municipio')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_csv = os.path.join(ruta_base, 'master_consumos.csv')
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_csv) or not os.path.exists(ruta_db):
            return jsonify({'error': 'No existen archivos para normalizar. Ejecuta la consolidación primero.'}), 400
        normalizar(ruta_csv, ruta_db)
        return jsonify({'ok': True, 'mensajes': 'Normalización completada. Revisa la terminal para detalles.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reporte_calidad', methods=['POST'])
def reporte_calidad():
    data = request.get_json()
    municipio = data.get('municipio')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        # S_CICLO
        ciclo_std = ("MENSUAL", "BIMESTRAL", "TRIMESTRAL")
        cur.execute("SELECT S_CICLO FROM lecturas")
        ciclos = [row[0] for row in cur.fetchall()]
        no_std_ciclos = [c for c in ciclos if c not in ciclo_std]
        unicos_ciclo = sorted(set(c for c in no_std_ciclos if c is not None))
        # S_TIPO_USO
        tipo_std = ("RESIDENCIAL", "COMERCIAL", "INDUSTRIAL", "OFICIAL")
        cur.execute("SELECT S_TIPO_USO FROM lecturas")
        tipos = [row[0] for row in cur.fetchall()]
        no_std_tipos = [t for t in tipos if t not in tipo_std]
        unicos_tipo = sorted(set(t for t in no_std_tipos if t is not None))
        conn.close()
        return jsonify({
            'ciclo': {
                'no_std_count': len(no_std_ciclos),
                'unicos': unicos_ciclo
            },
            'tipo_uso': {
                'no_std_count': len(no_std_tipos),
                'unicos': unicos_tipo
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/opciones_reporte', methods=['POST'])
def opciones_reporte():
    data = request.get_json()
    municipio = data.get('municipio')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        # Años únicos
        cur.execute("SELECT DISTINCT S_PERIODO FROM lecturas")
        periodos = [row[0] for row in cur.fetchall() if row[0]]
        anios = sorted(set(str(p).split('-')[0] for p in periodos if '-' in str(p)))
        # Ciclos estándar disponibles
        ciclo_std = ("MENSUAL", "BIMESTRAL", "TRIMESTRAL")
        cur.execute("SELECT DISTINCT S_CICLO FROM lecturas")
        ciclos = sorted(set(row[0] for row in cur.fetchall() if row[0] in ciclo_std))
        conn.close()
        return jsonify({'anios': anios, 'ciclos': ciclos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/promedio_consumo', methods=['POST'])
def promedio_consumo():
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        tipo_std = ("RESIDENCIAL", "COMERCIAL", "INDUSTRIAL", "OFICIAL")
        # Construir filtro SQL
        filtros = ["S_TIPO_USO IN ('RESIDENCIAL','COMERCIAL','INDUSTRIAL','OFICIAL')"]
        params = []
        if anio and anio != 'todos':
            filtros.append("substr(S_PERIODO,1,4) = ?")
            params.append(anio)
        if ciclo and ciclo != 'todos':
            filtros.append("S_CICLO = ?")
            params.append(ciclo)
        where = ' AND '.join(filtros)
        # Promedio de consumo
        sql = f"""
            SELECT S_TIPO_USO, AVG(CANT_KW), COUNT(*), AVG(VR_RECAUDO), AVG(VR_FACT)
              FROM lecturas
             WHERE {where}
          GROUP BY S_TIPO_USO
        """
        cur.execute(sql, params)
        resultados = cur.fetchall()
        data_prom = [
            {
                'tipo_uso': row[0],
                'promedio_cant_kw': round(row[1],2) if row[1] is not None else None,
                'cantidad': row[2],
                'promedio_vr_recaudo': round(row[3], 2) if row[3] is not None else None,
                'promedio_vr_fact': round(row[4], 2) if row[4] is not None else None
            }
            for row in resultados
        ]
        # --- Análisis de consumo 0/vacío y faltantes ---
        analisis = []
        if ciclo and ciclo != 'todos' and anio and anio != 'todos':
            # Definir periodos esperados según ciclo
            if ciclo == 'MENSUAL':
                periodos_esperados = [f"{anio}-{i}" for i in range(1,13)]
            elif ciclo == 'BIMESTRAL':
                periodos_esperados = [f"{anio}-{i}" for i in range(1,13,2)]
            elif ciclo == 'TRIMESTRAL':
                periodos_esperados = [f"{anio}-{i}" for i in range(1,13,3)]
            else:
                periodos_esperados = []
            for tipo in tipo_std:
                # Usuarios con consumo 0 o vacío por periodo
                cur.execute(f"""
                    SELECT S_PERIODO, COUNT(*)
                      FROM lecturas
                     WHERE S_TIPO_USO = ? AND S_CICLO = ? AND substr(S_PERIODO,1,4) = ?
                       AND (CANT_KW IS NULL OR CANT_KW = 0)
                  GROUP BY S_PERIODO
                """, (tipo, ciclo, anio))
                consumo_cero = {row[0]: row[1] for row in cur.fetchall()}
                # Datos faltantes (sin registro de consumo) por periodo esperado
                cur.execute(f"""
                    SELECT S_PERIODO
                      FROM lecturas
                     WHERE S_TIPO_USO = ? AND S_CICLO = ? AND substr(S_PERIODO,1,4) = ?
                """, (tipo, ciclo, anio))
                periodos_con_dato = set(row[0] for row in cur.fetchall())
                faltantes = [p for p in periodos_esperados if p not in periodos_con_dato]
                analisis.append({
                    'tipo_uso': tipo,
                    'consumo_cero': sum(consumo_cero.get(p,0) for p in periodos_esperados),
                    'faltantes': len(faltantes),
                    'detalle_faltantes': faltantes
                })
        conn.close()
        return jsonify({'resultados': data_prom, 'analisis': analisis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reporte_recaudo_cero', methods=['POST'])
def reporte_recaudo_cero():
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    if not municipio:
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        tipo_std = ("RESIDENCIAL", "COMERCIAL", "INDUSTRIAL", "OFICIAL")
        # Definir periodos esperados según ciclo
        if not ciclo or ciclo == 'todos' or not anio or anio == 'todos':
            return jsonify({'error': 'Selecciona año y ciclo'}), 400
        if ciclo == 'MENSUAL':
            periodos_esperados = [f"{anio}-{i}" for i in range(1,13)]
        elif ciclo == 'BIMESTRAL':
            periodos_esperados = [f"{anio}-{i}" for i in range(1,13,2)]
        elif ciclo == 'TRIMESTRAL':
            periodos_esperados = [f"{anio}-{i}" for i in range(1,13,3)]
        else:
            periodos_esperados = []
        resultado = []
        for periodo in periodos_esperados:
            for tipo in tipo_std:
                cur.execute(f"""
                    SELECT COUNT(*) FROM lecturas
                     WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ?
                       AND (CANT_KW > 0 OR (CANT_KW IS NOT NULL AND CANT_KW != 0))
                       AND (VR_RECAUDO IS NULL OR VR_RECAUDO = 0)
                """, (periodo, tipo, ciclo))
                cantidad = cur.fetchone()[0]
                resultado.append({
                    'periodo': periodo,
                    'tipo_uso': tipo,
                    'cantidad': cantidad
                })
        conn.close()
        return jsonify({'resultados': resultado})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descargar_recaudo_cero_excel', methods=['POST'])
def descargar_recaudo_cero_excel():
    import pandas as pd
    from io import BytesIO
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    periodo = data.get('periodo')
    tipo_uso = data.get('tipo_uso')
    if not municipio or not anio or not ciclo or not periodo or not tipo_uso:
        return 'Faltan parámetros', 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return 'No existe la base de datos', 400
        conn = sqlite3.connect(ruta_db)
        query = '''SELECT * FROM lecturas WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ?
                   AND (CANT_KW > 0 OR (CANT_KW IS NOT NULL AND CANT_KW != 0))
                   AND (VR_RECAUDO IS NULL OR VR_RECAUDO = 0)'''
        df = pd.read_sql_query(query, conn, params=(periodo, tipo_uso, ciclo))
        conn.close()
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        filename = f"detalle_recaudo_cero_{municipio}_{anio}_{ciclo}_{periodo}_{tipo_uso}.xlsx"
        from flask import send_file
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/detalle_recaudo_cero', methods=['POST'])
def detalle_recaudo_cero():
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    periodo = data.get('periodo')
    tipo_uso = data.get('tipo_uso')
    if not municipio or not anio or not ciclo or not periodo or not tipo_uso:
        return '<b>Faltan parámetros</b>', 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return '<b>No existe la base de datos</b>', 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT * FROM lecturas
             WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ?
               AND (CANT_KW > 0 OR (CANT_KW IS NOT NULL AND CANT_KW != 0))
               AND (VR_RECAUDO IS NULL OR VR_RECAUDO = 0)
        """, (periodo, tipo_uso, ciclo))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        conn.close()
        # Generar tabla HTML
        html = '<html><head><title>Detalle recaudo 0</title>'
        html += '<style>body{font-family:sans-serif;}table{border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px;}th{background:#e3eefd;}</style>'
        html += '</head><body>'
        html += f'<h2>Detalle recaudo 0 - {municipio} - {anio} - {ciclo} - {periodo} - {tipo_uso}</h2>'
        html += f'<b>Total registros: {len(rows)}</b><br><br>'
        html += f'<button onclick="descargarExcel()" style="background:#1a73e8;color:#fff;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;font-size:1rem;">Descargar Excel</button><br><br>'
        if rows:
            html += '<table><tr>' + ''.join(f'<th>{c}</th>' for c in colnames) + '</tr>'
            for row in rows:
                html += '<tr>' + ''.join(f'<td>{str(cell)}</td>' for cell in row) + '</tr>'
            html += '</table>'
        else:
            html += '<i>No hay registros</i>'
        html += '''
        <script>
        function descargarExcel() {
            fetch('/descargar_recaudo_cero_excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    municipio: "%s",
                    anio: "%s",
                    ciclo: "%s",
                    periodo: "%s",
                    tipo_uso: "%s"
                })
            })
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'detalle_recaudo_cero_%s_%s_%s_%s_%s.xlsx';
                document.body.appendChild(a);
                a.click();
                a.remove();
            });
        }
        </script>
        ''' % (municipio, anio, ciclo, periodo, tipo_uso, municipio, anio, ciclo, periodo, tipo_uso)
        html += '</body></html>'
        return html
    except Exception as e:
        return f'<b>Error:</b> {str(e)}', 500

@app.route('/reporte_valores_negativos', methods=['POST'])
def reporte_valores_negativos():
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    if not municipio or not anio or not ciclo or anio == 'todos' or ciclo == 'todos':
        return jsonify({'error': 'Selecciona municipio, año y ciclo'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        tipo_std = ("RESIDENCIAL", "COMERCIAL", "INDUSTRIAL", "OFICIAL")
        # Definir periodos esperados según ciclo
        if ciclo == 'MENSUAL':
            periodos_esperados = [f"{anio}-{i}" for i in range(1,13)]
        elif ciclo == 'BIMESTRAL':
            periodos_esperados = [f"{anio}-{i}" for i in range(1,13,2)]
        elif ciclo == 'TRIMESTRAL':
            periodos_esperados = [f"{anio}-{i}" for i in range(1,13,3)]
        else:
            periodos_esperados = []
        resultado = []
        for periodo in periodos_esperados:
            for tipo in tipo_std:
                # VR_RECAUDO < 0
                cur.execute(f"""
                    SELECT COUNT(*) FROM lecturas
                     WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ?
                       AND VR_RECAUDO < 0
                """, (periodo, tipo, ciclo))
                rec_neg = cur.fetchone()[0]
                # VR_FACT < 0
                cur.execute(f"""
                    SELECT COUNT(*) FROM lecturas
                     WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ?
                       AND VR_FACT < 0
                """, (periodo, tipo, ciclo))
                fact_neg = cur.fetchone()[0]
                resultado.append({
                    'periodo': periodo,
                    'tipo_uso': tipo,
                    'vr_recaudo_neg': rec_neg,
                    'vr_fact_neg': fact_neg
                })
        conn.close()
        return jsonify({'resultados': resultado})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detalle_valores_negativos', methods=['POST'])
def detalle_valores_negativos():
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    periodo = data.get('periodo')
    tipo_uso = data.get('tipo_uso')
    campo = data.get('campo')  # 'VR_RECAUDO' o 'VR_FACT'
    if not municipio or not anio or not ciclo or not periodo or not tipo_uso or not campo:
        return '<b>Faltan parámetros</b>', 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return '<b>No existe la base de datos</b>', 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT * FROM lecturas
             WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ?
               AND {campo} < 0
        """, (periodo, tipo_uso, ciclo))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        conn.close()
        html = '<html><head><title>Detalle valores negativos</title>'
        html += '<style>body{font-family:sans-serif;}table{border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px;}th{background:#e3eefd;}</style>'
        html += '</head><body>'
        html += f'<h2>Detalle {campo} negativo - {municipio} - {anio} - {ciclo} - {periodo} - {tipo_uso}</h2>'
        html += f'<b>Total registros: {len(rows)}</b><br><br>'
        html += f'<button onclick="descargarExcelNeg()" style="background:#1a73e8;color:#fff;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;font-size:1rem;">Descargar Excel</button><br><br>'
        if rows:
            html += '<table><tr>' + ''.join(f'<th>{c}</th>' for c in colnames) + '</tr>'
            for row in rows:
                html += '<tr>' + ''.join(f'<td>{str(cell)}</td>' for cell in row) + '</tr>'
            html += '</table>'
        else:
            html += '<i>No hay registros</i>'
        html += '''
        <script>
        function descargarExcelNeg() {
            fetch('/descargar_valores_negativos_excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    municipio: "%s",
                    anio: "%s",
                    ciclo: "%s",
                    periodo: "%s",
                    tipo_uso: "%s",
                    campo: "%s"
                })
            })
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'detalle_%s_negativo_%s_%s_%s_%s_%s.xlsx';
                document.body.appendChild(a);
                a.click();
                a.remove();
            });
        }
        </script>
        ''' % (municipio, anio, ciclo, periodo, tipo_uso, campo, campo.lower(), municipio, anio, ciclo, periodo, tipo_uso)
        html += '</body></html>'
        return html
    except Exception as e:
        return f'<b>Error:</b> {str(e)}', 500

@app.route('/descargar_valores_negativos_excel', methods=['POST'])
def descargar_valores_negativos_excel():
    import pandas as pd
    from io import BytesIO
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    periodo = data.get('periodo')
    tipo_uso = data.get('tipo_uso')
    campo = data.get('campo')
    if not municipio or not anio or not ciclo or not periodo or not tipo_uso or not campo:
        return 'Faltan parámetros', 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return 'No existe la base de datos', 400
        conn = sqlite3.connect(ruta_db)
        query = f'''SELECT * FROM lecturas WHERE S_PERIODO = ? AND S_TIPO_USO = ? AND S_CICLO = ? AND {campo} < 0'''
        df = pd.read_sql_query(query, conn, params=(periodo, tipo_uso, ciclo))
        conn.close()
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        filename = f"detalle_{campo.lower()}_negativo_{municipio}_{anio}_{ciclo}_{periodo}_{tipo_uso}.xlsx"
        from flask import send_file
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f'Error: {str(e)}', 500


def normaliza_cadena(s):
    if pd.isna(s):
        return ""
    return unidecode(str(s)).lower().replace(" ", "").replace("-", "")

# Elimino el endpoint y la función analizar_consumos y toda la lógica asociada

@app.route('/descargar_excesivos_excel')
def descargar_excesivos_excel():
    global _excesivos_cache
    output = BytesIO()
    _excesivos_cache.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='excesivos.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/descargar_desajustes_excel')
def descargar_desajustes_excel():
    global _desajustes_cache
    output = BytesIO()
    _desajustes_cache.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='desajustes.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/descargar_excesivos_csv')
def descargar_excesivos_csv():
    global _excesivos_cache
    output = BytesIO()
    _excesivos_cache.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='excesivos.csv', mimetype='text/csv')

@app.route('/descargar_desajustes_csv')
def descargar_desajustes_csv():
    global _desajustes_cache
    output = BytesIO()
    _desajustes_cache.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='desajustes.csv', mimetype='text/csv')

def guardar_tabla_tarifas_guacari(path_salida=None):
    import pandas as pd
    # Definir la lógica de la tabla
    data = [
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 1", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 5},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 2", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 7},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 3", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 10},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 4", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 15},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 5", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 30},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 6", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 40},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 1 RURAL DISPERSO", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 3},
        {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "CANT_KW_MAX": 173, "S_ESTRATO": "ESTRATO 2 RURAL DISPERSO", "S_CANT_KW": 730, "S_PORCENTAJE_TARIFA": 3.5},
    ]
    df = pd.DataFrame(data)
    if path_salida is None:
        path_salida = os.path.join(os.path.dirname(__file__), 'tabla_tarifas_guacari.xlsx')
    df.to_excel(path_salida, index=False)
    print(f"[PROGRESO] Tabla de tarifas GUACARÍ guardada en: {path_salida}")

def crear_tabla_porcentajes_guacari(path_salida=None):
    import pandas as pd
    data = [
        {"S_ESTRATO": "ESTRATO 1", "S_PORCENTAJE_TARIFA": 5},
        {"S_ESTRATO": "ESTRATO 2", "S_PORCENTAJE_TARIFA": 7},
        {"S_ESTRATO": "ESTRATO 3", "S_PORCENTAJE_TARIFA": 10},
        {"S_ESTRATO": "ESTRATO 4", "S_PORCENTAJE_TARIFA": 15},
        {"S_ESTRATO": "ESTRATO 5", "S_PORCENTAJE_TARIFA": 30},
        {"S_ESTRATO": "ESTRATO 6", "S_PORCENTAJE_TARIFA": 40},
        {"S_ESTRATO": "ESTRATO 1 RURAL DISPERSO", "S_PORCENTAJE_TARIFA": 3},
        {"S_ESTRATO": "ESTRATO 2 RURAL DISPERSO", "S_PORCENTAJE_TARIFA": 3.5},
    ]
    df = pd.DataFrame(data)
    if path_salida is None:
        path_salida = os.path.join(os.path.dirname(__file__), 'tabla_porcentajes_guacari.xlsx')
    df.to_excel(path_salida, index=False)
    print(f"[PROGRESO] Tabla editable de porcentajes GUACARÍ guardada en: {path_salida}")

def crear_excel_logica_porcentajes_guacari(path_salida=None):
    import pandas as pd
    data = [
        {"S_ESTRATO": "ESTRATO 1", "S_PORCENTAJE_TARIFA": 5},
        {"S_ESTRATO": "ESTRATO 2", "S_PORCENTAJE_TARIFA": 7},
        {"S_ESTRATO": "ESTRATO 3", "S_PORCENTAJE_TARIFA": 10},
        {"S_ESTRATO": "ESTRATO 4", "S_PORCENTAJE_TARIFA": 15},
        {"S_ESTRATO": "ESTRATO 5", "S_PORCENTAJE_TARIFA": 30},
        {"S_ESTRATO": "ESTRATO 6", "S_PORCENTAJE_TARIFA": 40},
        {"S_ESTRATO": "ESTRATO 1 RURAL DISPERSO", "S_PORCENTAJE_TARIFA": 3},
        {"S_ESTRATO": "ESTRATO 2 RURAL DISPERSO", "S_PORCENTAJE_TARIFA": 3.5},
    ]
    df = pd.DataFrame(data)
    if path_salida is None:
        path_salida = os.path.join(os.path.dirname(__file__), 'logica_porcentajes_guacari.xlsx')
    df.to_excel(path_salida, index=False)
    print(f"[PROGRESO] Archivo de lógica de porcentajes GUACARÍ guardado en: {path_salida}")

@app.route('/descargar_tabla_porcentajes_guacari')
def descargar_tabla_porcentajes_guacari():
    from flask import send_file
    path = os.path.join(os.path.dirname(__file__), 'tabla_porcentajes_guacari.xlsx')
    if not os.path.exists(path):
        crear_tabla_porcentajes_guacari(path)
    return send_file(path, as_attachment=True, download_name='tabla_porcentajes_guacari.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/analizar_residenciales', methods=['POST'])
def analizar_residenciales():
    import pandas as pd
    data = request.get_json()
    municipio = data.get('municipio')
    if not municipio:
        return {'error': 'Municipio requerido'}, 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return {'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}, 400
        conn = sqlite3.connect(ruta_db)
        df = pd.read_sql_query('SELECT * FROM lecturas', conn)
        conn.close()
        # Filtrar residenciales
        df = df[df['S_TIPO_USO'] == 'RESIDENCIAL']
        total_residenciales = len(df)
        # Leer lógica de porcentajes
        path_logica = os.path.join(os.path.dirname(__file__), 'logica_porcentajes_guacari.xlsx')
        if not os.path.exists(path_logica):
            return {'error': 'No existe el archivo de lógica de porcentajes.'}, 400
        df_logica = pd.read_excel(path_logica)
        estrato_to_porcentaje = {str(row['S_ESTRATO']).strip().upper(): float(row['S_PORCENTAJE_TARIFA']) for _, row in df_logica.iterrows()}
        no_cumplen = []
        for _, row in df.iterrows():
            estrato = str(row['S_ESTRATO']).strip().upper()
            porcentaje_esperado = estrato_to_porcentaje.get(estrato)
            try:
                porcentaje_real = float(row['S_PORCENTAJE_TARIFA'])
            except Exception:
                porcentaje_real = None
            if porcentaje_esperado is not None and porcentaje_real is not None:
                if abs(porcentaje_real - porcentaje_esperado) >= 1:
                    no_cumplen.append({
                        'S_ID': row['S_ID'],
                        'S_ESTRATO': estrato,
                        'PORCENTAJE_ESPERADO': porcentaje_esperado,
                        'PORCENTAJE_REAL': porcentaje_real
                    })
            else:
                no_cumplen.append({
                    'S_ID': row['S_ID'],
                    'S_ESTRATO': estrato,
                    'PORCENTAJE_ESPERADO': porcentaje_esperado,
                    'PORCENTAJE_REAL': porcentaje_real
                })
        # Guardar para descarga
        global _no_cumplen_residenciales_cache
        _no_cumplen_residenciales_cache = pd.DataFrame(no_cumplen)
        return {
            'total_residenciales': total_residenciales,
            'no_cumplen_count': len(no_cumplen),
            'no_cumplen': no_cumplen[:100]  # solo los primeros 100 para la web
        }
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/descargar_no_cumplen_residenciales')
def descargar_no_cumplen_residenciales():
    import pandas as pd
    from io import BytesIO
    global _no_cumplen_residenciales_cache
    if '_no_cumplen_residenciales_cache' not in globals() or _no_cumplen_residenciales_cache is None or _no_cumplen_residenciales_cache.empty:
        return 'No hay datos para descargar. Ejecuta el análisis primero.', 400
    output = BytesIO()
    _no_cumplen_residenciales_cache.to_excel(output, index=False)
    output.seek(0)
    from flask import send_file
    return send_file(output, as_attachment=True, download_name='no_cumplen_residenciales.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/cumplimiento_porcentajes', methods=['POST'])
def cumplimiento_porcentajes():
    print('[OBLIGATORIO] Recibida petición a /cumplimiento_porcentajes: CARGANDO...')
    import pandas as pd
    from flask import jsonify
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    print(f"[DEBUG] Llamada a /cumplimiento_porcentajes con municipio={municipio}, anio={anio}, ciclo={ciclo}")
    if not municipio:
        print("[ERROR] Municipio requerido no recibido en /cumplimiento_porcentajes")
        return jsonify({'error': 'Municipio requerido'}), 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            print(f"[ERROR] No existe la base de datos en {ruta_db}")
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        df = pd.read_sql_query('SELECT * FROM lecturas', conn)
        conn.close()
        print(f"[DEBUG] Lecturas cargadas: {len(df)} registros")
        # Filtros año y ciclo
        if anio and anio != 'todos':
            df = df[df['S_PERIODO'].astype(str).str.startswith(str(anio)+'-')]
            print(f"[DEBUG] Filtrado por año: {anio}, quedan {len(df)} registros")
        if ciclo and ciclo != 'todos':
            df = df[df['S_CICLO'] == ciclo]
            print(f"[DEBUG] Filtrado por ciclo: {ciclo}, quedan {len(df)} registros")
        # Leer lógica de porcentajes
        path_logica = os.path.join(os.path.dirname(__file__), 'logica_porcentajes_guacari.xlsx')
        if not os.path.exists(path_logica):
            print(f"[ERROR] No existe el archivo de lógica de porcentajes: {path_logica}")
            return jsonify({'error': 'No existe el archivo de lógica de porcentajes.'}), 400
        df_logica = pd.read_excel(path_logica)
        print(f"[DEBUG] Lógica de porcentajes cargada: {len(df_logica)} filas")
        # Obtener tipos de uso válidos del archivo de lógica
        tipos_validos = sorted(df_logica['S_TIPO_USO'].dropna().unique())
        print(f"[DEBUG] Tipos válidos: {tipos_validos}")
        # Filtrar solo los tipos de uso que están en la lógica
        df = df[df['S_TIPO_USO'].isin(tipos_validos)]
        print(f"[DEBUG] Filtrado por tipos válidos, quedan {len(df)} registros")
        # Crear diccionario de lógica por tipo de uso, estrato y año
        logica_dict = {}
        for _, row in df_logica.iterrows():
            municipio_log = str(row['S_MPIO']).strip().upper()
            tipo_uso = str(row['S_TIPO_USO']).strip().upper()
            estrato = str(row['S_ESTRATO']).strip().upper() if pd.notna(row['S_ESTRATO']) else ''
            anio_logic = int(row['AÑO'])
            porcentaje_tarifa = float(row['S_PORCENTAJE_TARIFA'])
            valor_esperado = float(row['VALOR_ESPERADO']) if 'VALOR_ESPERADO' in row else None
            cant_kw_logic = str(row['CANT_KW']) if 'CANT_KW' in row else '173'
            key = (municipio_log, tipo_uso, estrato, anio_logic)
            logica_dict[key] = {
                'porcentaje_tarifa': porcentaje_tarifa,
                'valor_esperado': valor_esperado,
                'cant_kw': cant_kw_logic
            }
        resultados = []
        # Usar solo los tipos de uso válidos
        tipos = tipos_validos
        periodos = sorted(df['S_PERIODO'].dropna().unique())
        print(f"[DEBUG] Periodos únicos: {periodos}")
        for periodo in periodos:
            for tipo in tipos:
                sub = df[(df['S_PERIODO'] == periodo) & (df['S_TIPO_USO'] == tipo)]
                no_cumplen_porcentaje = 0
                no_cumplen_valor = 0
                for _, row in sub.iterrows():
                    municipio_row = str(row['S_MPIO']).strip().upper()
                    estrato = str(row['S_ESTRATO']).strip().upper() if pd.notna(row['S_ESTRATO']) else ''
                    tipo_mercado = str(row['S_TIPO_MERCADO']).strip().upper() if pd.notna(row['S_TIPO_MERCADO']) else ''
                    # Obtener año del periodo
                    anio_row = None
                    if 'S_PERIODO' in row and isinstance(row['S_PERIODO'], str) and '-' in row['S_PERIODO']:
                        try:
                            anio_row = int(row['S_PERIODO'].split('-')[0])
                        except Exception:
                            pass
                    try:
                        porcentaje_real = float(row['S_PORCENTAJE_TARIFA']) if row['S_PORCENTAJE_TARIFA'] is not None else None
                        cant_kw = float(row['CANT_KW']) if row['CANT_KW'] is not None else None
                        vr_fact = float(row['VR_FACT']) if row['VR_FACT'] is not None else None
                    except Exception:
                        porcentaje_real = None
                        cant_kw = None
                        vr_fact = None
                    if cant_kw is not None:
                        # Buscar lógica correspondiente según el tipo de uso
                        if tipo == 'RESIDENCIAL':
                            key = (municipio_row, tipo, estrato, anio_row) if anio_row else None
                            logica = logica_dict.get(key) if key else None
                            if logica:
                                try:
                                    logica_cant_kw_float = float(logica['cant_kw'])
                                except (ValueError, TypeError):
                                    logica_cant_kw_float = 173.0
                                if cant_kw >= logica_cant_kw_float:
                                    porcentaje_esperado = logica['porcentaje_tarifa']
                                    if porcentaje_esperado is not None and porcentaje_real is not None:
                                        if abs(porcentaje_real - porcentaje_esperado) >= 1:
                                            no_cumplen_porcentaje += 1
                                    elif porcentaje_real is None:
                                        no_cumplen_porcentaje += 1
                                else:
                                    valor_esperado = logica['valor_esperado']
                                    if valor_esperado is not None and vr_fact is not None:
                                        if abs(vr_fact - valor_esperado) >= 1:
                                            no_cumplen_valor += 1
                                    elif vr_fact is None:
                                        no_cumplen_valor += 1
                                    else:
                                        no_cumplen_valor += 1
                            else:
                                no_cumplen_porcentaje += 1
                        else:
                            key = (municipio_row, tipo, '', anio_row) if anio_row else None
                            logica = logica_dict.get(key) if key else None
                            if logica:
                                try:
                                    logica_cant_kw_float = float(logica['cant_kw'])
                                except (ValueError, TypeError):
                                    logica_cant_kw_float = 1001.0
                                if cant_kw >= logica_cant_kw_float:
                                    porcentaje_esperado = logica['porcentaje_tarifa']
                                    if porcentaje_esperado is not None and porcentaje_real is not None:
                                        if abs(porcentaje_real - porcentaje_esperado) >= 1:
                                            no_cumplen_porcentaje += 1
                                    elif porcentaje_real is None:
                                        no_cumplen_porcentaje += 1
                                else:
                                    valor_esperado = None
                                    for _, logic_row in df_logica.iterrows():
                                        if (str(logic_row['S_MPIO']).strip().upper() == municipio_row and 
                                            str(logic_row['S_TIPO_USO']).strip().upper() == tipo and
                                            pd.isna(logic_row['S_ESTRATO'])):
                                            logic_cant_kw = str(logic_row['CANT_KW'])
                                            if '-' in logic_cant_kw:
                                                min_kw, max_kw = logic_cant_kw.split('-')
                                                try:
                                                    min_kw = float(min_kw)
                                                    max_kw = float(max_kw)
                                                    if min_kw <= cant_kw <= max_kw:
                                                        valor_esperado = float(logic_row['VALOR_ESPERADO'])
                                                        break
                                                except:
                                                    continue
                                    if valor_esperado is not None and vr_fact is not None:
                                        if abs(vr_fact - valor_esperado) >= 1:
                                            no_cumplen_valor += 1
                                    elif vr_fact is None:
                                        no_cumplen_valor += 1
                                    else:
                                        no_cumplen_valor += 1
                            else:
                                no_cumplen_porcentaje += 1
                    else:
                        no_cumplen_valor += 1
                resultados.append({
                    'periodo': periodo, 
                    'tipo_uso': tipo, 
                    'total_no_cumplen': no_cumplen_porcentaje + no_cumplen_valor
                })
        print(f"[DEBUG] Respuesta: {len(resultados)} filas de resultados, tipos={tipos}, periodos={periodos}")
        return jsonify({
            'titulo': 'Cumplimiento de tarifas',
            'tipos': tipos,
            'periodos': periodos,
            'resultados': resultados
        })
    except Exception as e:
        print(f"[ERROR] Excepción en /cumplimiento_porcentajes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/detalle_cumplimiento_porcentajes', methods=['POST'])
def detalle_cumplimiento_porcentajes():
    import pandas as pd
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    periodo = data.get('periodo')
    tipo_uso = data.get('tipo_uso')
    if not municipio or not anio or not ciclo or not periodo or not tipo_uso:
        return '<b>Faltan parámetros</b>', 400
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return '<b>No existe la base de datos</b>', 400
        conn = sqlite3.connect(ruta_db)
        
        # Obtener total general de S_IDs únicos para el período y tipo de uso
        query_total = """
            SELECT COUNT(DISTINCT S_ID) as total 
            FROM lecturas 
            WHERE S_PERIODO = ? AND S_TIPO_USO = ?
        """
        params_total = [periodo, tipo_uso]
        if ciclo and ciclo != 'todos':
            query_total += " AND S_CICLO = ?"
            params_total.append(ciclo)
            
        cur = conn.cursor()
        cur.execute(query_total, params_total)
        total_general = cur.fetchone()[0]
        
        # Obtener todos los datos para el análisis
        df = pd.read_sql_query('SELECT * FROM lecturas', conn)
        conn.close()
        
        # Filtros
        df = df[(df['S_PERIODO'] == periodo) & (df['S_TIPO_USO'] == tipo_uso)]
        if ciclo and ciclo != 'todos':
            df = df[df['S_CICLO'] == ciclo]
        # Leer lógica de porcentajes
        path_logica = os.path.join(os.path.dirname(__file__), 'logica_porcentajes_guacari.xlsx')
        if not os.path.exists(path_logica):
            return '<b>No existe el archivo de lógica de porcentajes</b>', 400
        df_logica = pd.read_excel(path_logica)

        detalle = []
        inferiores = []
        superiores = []
        inferiores_valor = []
        superiores_valor = []

        suma_dif_vr_fact = 0.0
        suma_dif_porcentaje = 0.0
        suma_total = 0.0
        count_dif_vr_fact = 0
        count_dif_porcentaje = 0

        for _, row in df.iterrows():
            # Initialize fila with all data and default values
            fila = {k: v for k, v in row.items()}
            # Round the actual percentage to an integer for display
            if 'S_PORCENTAJE_TARIFA' in fila and pd.notna(fila['S_PORCENTAJE_TARIFA']):
                try:
                    fila['S_PORCENTAJE_TARIFA'] = int(round(float(fila['S_PORCENTAJE_TARIFA']), 0))
                except (ValueError, TypeError):
                    pass # Keep original value if it cannot be converted

            fila['S_PORCENTAJE_TARIFA_ESPERADO'] = 'No aplica'
            fila['VALOR_ESPERADO'] = 'No aplica'
            fila['TIPO_INCUMPLIMIENTO'] = ''
            fila['DIFERENCIA'] = 'No aplica'
            
            # Safely get data from the current row
            try:
                cant_kw = float(row.get('CANT_KW'))
                porcentaje_real = float(row.get('S_PORCENTAJE_TARIFA')) if pd.notna(row.get('S_PORCENTAJE_TARIFA')) else None
                vr_fact = float(row.get('VR_FACT')) if pd.notna(row.get('VR_FACT')) else None
                
                current_tipo_uso = str(row.get('S_TIPO_USO')).strip().upper()
                current_municipio = str(row.get('S_MPIO')).strip().upper()
                current_estrato = str(row.get('S_ESTRATO')).strip().upper() if pd.notna(row.get('S_ESTRATO')) else ''
                anio_row = int(str(row.get('S_PERIODO')).split('-')[0])
            except (ValueError, TypeError, AttributeError):
                fila['TIPO_INCUMPLIMIENTO'] = 'datos_invalidos'
                detalle.append(fila)
                continue

            # Find the applicable logic from the logic file
            logica_aplicable = None
            q = df_logica[
                (df_logica['S_MPIO'].str.strip().str.upper() == current_municipio) &
                (df_logica['S_TIPO_USO'].str.strip().str.upper() == current_tipo_uso) &
                (df_logica['AÑO'] == anio_row)
            ]

            # Find the specific rule based on tipo_uso
            if current_tipo_uso == 'RESIDENCIAL':
                q = q[q['S_ESTRATO'].str.strip().str.upper() == current_estrato]
                if not q.empty:
                    logica_aplicable = q.iloc[0]
                    if cant_kw >= 173:
                        porcentaje_esperado = int(round(float(logica_aplicable['S_PORCENTAJE_TARIFA']), 0))
                        fila['S_PORCENTAJE_TARIFA_ESPERADO'] = porcentaje_esperado
                        if porcentaje_real is not None and abs(porcentaje_real - porcentaje_esperado) >= 1:
                            fila['TIPO_INCUMPLIMIENTO'] = 'porcentaje_superior' if porcentaje_real > porcentaje_esperado else 'porcentaje_inferior'
                    else:
                        valor_esperado = int(round(float(logica_aplicable['VALOR_ESPERADO']), 0))
                        fila['VALOR_ESPERADO'] = valor_esperado
                        if vr_fact is not None:
                            fila['DIFERENCIA'] = vr_fact - valor_esperado
                        if vr_fact is not None and abs(vr_fact - valor_esperado) >= 1:
                            fila['TIPO_INCUMPLIMIENTO'] = 'valor_superior' if vr_fact > valor_esperado else 'valor_inferior'
            else: # NON-RESIDENCIAL
                umbral_row = q[q['CANT_KW'].astype(str) == '1001']
                if not umbral_row.empty and cant_kw >= 1001:
                    logica_aplicable = umbral_row.iloc[0]
                    porcentaje_esperado = int(round(float(logica_aplicable['S_PORCENTAJE_TARIFA']), 0))
                    fila['S_PORCENTAJE_TARIFA_ESPERADO'] = porcentaje_esperado
                    if porcentaje_real is not None and abs(porcentaje_real - porcentaje_esperado) >= 1:
                        fila['TIPO_INCUMPLIMIENTO'] = 'porcentaje_superior' if porcentaje_real > porcentaje_esperado else 'porcentaje_inferior'
                else:
                    range_rows = q[q['CANT_KW'].astype(str).str.contains('-')]
                    for _, l_row in range_rows.iterrows():
                        if kw_in_range(cant_kw, l_row['CANT_KW']):
                            logica_aplicable = l_row
                            break
                    if logica_aplicable is not None:
                        valor_esperado = int(round(float(logica_aplicable['VALOR_ESPERADO']), 0)) # Redondeo a entero
                        fila['VALOR_ESPERADO'] = valor_esperado
                        if vr_fact is not None:
                            fila['DIFERENCIA'] = vr_fact - valor_esperado
                        if vr_fact is not None and abs(vr_fact - valor_esperado) >= 1:
                            fila['TIPO_INCUMPLIMIENTO'] = 'valor_superior' if vr_fact > valor_esperado else 'valor_inferior'

            if not fila['TIPO_INCUMPLIMIENTO']:
                if logica_aplicable is None:
                    fila['TIPO_INCUMPLIMIENTO'] = 'logica_no_encontrada'
                elif (fila['S_PORCENTAJE_TARIFA_ESPERADO'] == 'No aplica' and fila['VALOR_ESPERADO'] == 'No aplica'):
                    fila['TIPO_INCUMPLIMIENTO'] = 'calculo_no_aplicable'
            
            # --- CÁLCULO DE DIFERENCIA VR_FACT ---
            if (
                fila.get('VALOR_ESPERADO', 'No aplica') not in [None, '', 'No aplica', 'no aplica']
                and pd.notna(fila.get('VALOR_ESPERADO'))
            ):
                try:
                    vr_fact_num = float(fila.get('VR_FACT'))
                    valor_esperado_num = float(fila.get('VALOR_ESPERADO'))
                    diferencia = vr_fact_num - valor_esperado_num
                    fila['DIFERENCIA VR_FACT'] = round(diferencia, 1)
                    suma_dif_vr_fact += diferencia
                    suma_total += diferencia
                    count_dif_vr_fact += 1
                except (ValueError, TypeError, AttributeError):
                    fila['DIFERENCIA VR_FACT'] = 'No aplica'
            else:
                fila['DIFERENCIA VR_FACT'] = 'No aplica'
            # --- FIN CÁLCULO DE DIFERENCIA VR_FACT ---

            # --- CÁLCULO DE DIFERENCIA PORCENTAJE ---
            if (
                fila.get('S_PORCENTAJE_TARIFA_ESPERADO', 'No aplica') not in [None, '', 'No aplica', 'no aplica']
                and pd.notna(fila.get('S_PORCENTAJE_TARIFA_ESPERADO'))
            ):
                try:
                    porcentaje_esperado = float(fila.get('S_PORCENTAJE_TARIFA_ESPERADO'))
                    vr_consumo_pesos = float(fila.get('VR_CONSUMO_PESOS'))
                    vr_fact = float(fila.get('VR_FACT'))
                    valor_porcentaje = (porcentaje_esperado / 100.0) * vr_consumo_pesos
                    diferencia_porcentaje = vr_fact - valor_porcentaje
                    fila['DIFERENCIA PORCENTAJE'] = round(diferencia_porcentaje, 1)
                    suma_dif_porcentaje += diferencia_porcentaje
                    suma_total += diferencia_porcentaje
                    count_dif_porcentaje += 1
                except (ValueError, TypeError, AttributeError):
                    fila['DIFERENCIA PORCENTAJE'] = 'No aplica'
            else:
                fila['DIFERENCIA PORCENTAJE'] = 'No aplica'
            # --- FIN CÁLCULO DE DIFERENCIA PORCENTAJE ---

            if fila['TIPO_INCUMPLIMIENTO']:
                detalle.append(fila)
                if 'inferior' in fila['TIPO_INCUMPLIMIENTO']:
                    if 'porcentaje' in fila['TIPO_INCUMPLIMIENTO']: inferiores.append(fila)
                    else: inferiores_valor.append(fila)
                elif 'superior' in fila['TIPO_INCUMPLIMIENTO']:
                    if 'porcentaje' in fila['TIPO_INCUMPLIMIENTO']: superiores.append(fila)
                    else: superiores_valor.append(fila)

        global _detalle_cumplimiento_cache, _detalle_cumplimiento_inferiores, _detalle_cumplimiento_superiores
        _detalle_cumplimiento_cache = pd.DataFrame(detalle)
        _detalle_cumplimiento_inferiores = pd.DataFrame(inferiores + inferiores_valor)
        _detalle_cumplimiento_superiores = pd.DataFrame(superiores + superiores_valor)
        
        # Generar tabla HTML
        html = '<html><head><title>Detalle cumplimiento tarifas</title>'
        html += '<style>body{font-family:sans-serif;}table{border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px;}th{background:#e3eefd;}</style>'
        html += '</head><body>'
        # Contar S_IDs únicos que incumplen
        s_ids_incumplen = len(set([d['S_ID'] for d in detalle if d.get('TIPO_INCUMPLIMIENTO')]))
        
        html += f'<h2>Detalle no cumplen - {municipio} - {anio} - {ciclo} - {periodo} - {tipo_uso}</h2>'
        html += f'<div style="background:#e8f4fd; padding:12px; border-radius:8px; margin-bottom:16px; border-left:4px solid #1976d2;">'
        html += f'<b>Total S_IDs:</b> {total_general:,} &nbsp;&nbsp;|&nbsp;&nbsp; <b>S_IDs que presentan incumplimiento:</b> {s_ids_incumplen:,}<br>'
        porcentaje_incumplimiento = round((s_ids_incumplen / total_general * 100), 2) if total_general > 0 else 0
        html += f'<b>Porcentaje de incumplimiento:</b> {porcentaje_incumplimiento}%<br>'
        html += f'<small><b>Total registros detalle:</b> {len(detalle):,} (un S_ID puede tener múltiples incumplimientos)</small>'
        html += f'</div>'
        html += f'<div style="margin-bottom:18px;padding:10px 16px;background:#f5f7fa;border-radius:6px;border:1px solid #dbe2ef;max-width:700px;">'
        html += f'<b>DIFERENCIA POR CALCULO UVT :</b> {formatear_pesos(suma_dif_vr_fact)}<br>'
        html += f'<b>DIFERENCIA POR CALCULO PORCENTUAL:</b> {formatear_pesos(suma_dif_porcentaje)}<br>'
        html += '</div>'

        # Botones de filtro y descarga con mejor diseño
        html += '''
        <style>
        .boton-filtro, .boton-descargar {
            min-width: 180px;
            height: 48px;
            padding: 0 18px;
            margin: 0 8px 12px 0;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 500;
            color: #fff;
            cursor: pointer;
            transition: background 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            display: inline-block;
        }
        .boton-filtro.azul { background: #1a73e8; }
        .boton-filtro.naranja { background: #e39a1a; }
        .boton-filtro.rojo { background: #d7263d; }
        .boton-filtro.azul:hover, .boton-descargar.azul:hover { background: #155ab6; }
        .boton-filtro.naranja:hover { background: #b97a13; }
        .boton-filtro.rojo:hover { background: #a81d2e; }
        .boton-descargar.azul { background: #1a73e8; }
        .boton-descargar.azul:active { background: #155ab6; }
        .boton-descargar.verde { background: #28a745; }
        .boton-descargar.verde:hover { background: #218838; }
        .boton-descargar.verde:active { background: #1e7e34; }
        .botones-row { display: flex; flex-wrap: wrap; gap: 0 8px; margin-bottom: 18px; }
        </style>
        <div class="botones-row">
            <button class="boton-filtro azul" onclick="filtrarTabla('todos')">Ver todos</button>
            <button class="boton-filtro naranja" onclick="filtrarTabla('porcentaje_inferior')">Porcentaje inferior</button>
            <button class="boton-filtro rojo" onclick="filtrarTabla('porcentaje_superior')">Porcentaje superior</button>
            <button class="boton-filtro naranja" onclick="filtrarTabla('valor_inferior')">Valor facturado inferior</button>
            <button class="boton-filtro rojo" onclick="filtrarTabla('valor_superior')">Valor facturado superior</button>
        </div>
        <div class="botones-row">
            <button class="boton-descargar azul" onclick="descargarExcelCumplimiento()">Descargar Excel filtrado</button>
        </div>
        '''
        if detalle:
            # Unir todas las columnas originales
            all_cols = set()
            for d in detalle:
                all_cols.update(d.keys())
            all_cols = list(all_cols)
            # Orden obligatorio de columnas (sin CLASIFICACION)
            cols = [
                'S_ID', 'CANT_KW', 'S_PORCENTAJE_TARIFA', 'S_PORCENTAJE_TARIFA_ESPERADO',
                'VALOR_ESPERADO', 'VR_FACT', 'TIPO_INCUMPLIMIENTO', 'DIFERENCIA VR_FACT', 'DIFERENCIA PORCENTAJE',
                'S_MPIO', 'S_COMERCIALIZADOR', 'S_NIC', 'S_NOMBRE', 'S_PERIODO', 'S_FECHA_FACT',
                'S_TIPO_USO', 'S_ZONA', 'S_BARRIO_VEREDA', 'S_DIRECCION', 'S_TIPO_MERCADO', 'S_CICLO',
                'VR_CONSUMO_PESOS', 'VR_RECAUDO', 'VR_CARTERA_GENERADA', 'VR_CARTERA_RECUPERADA', 'S_ID_CANON', 'S_ESTRATO'
            ]
            cols += [c for c in all_cols if c not in cols]
            # Obtener lógica de porcentajes por estrato y año
            logica_dict = {}
            for _, row in df_logica.iterrows():
                key = (str(row['S_ESTRATO']).strip().upper(), int(row['AÑO']))
                logica_cant_kw = str(row['CANT_KW']) if 'CANT_KW' in row else '173'
                logica_dict[key] = logica_cant_kw
            html += f'<table id="tabla-cumplimiento"><thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead><tbody>'
            for d in detalle:
                row_html = ''.join(f'<td>{d.get(c, "-")}</td>' for c in cols)
                clase = d.get('TIPO_INCUMPLIMIENTO', '')
                html += f'<tr class="{clase}">' + row_html + '</tr>'
            html += '</tbody></table>'
        else:
            html += '<i>No hay registros</i>'
        # ... (resto del código) ...
        html += '''
        <script>
        var filtroActivo = 'todos';
        function filtrarTabla(tipo) {
            filtroActivo = tipo;
            var filas = document.querySelectorAll('#tabla-cumplimiento tbody tr');
            filas.forEach(function(tr) {
                if(tipo === 'todos') {
                    tr.style.display = '';
                } else {
                    tr.style.display = tr.classList.contains(tipo) ? '' : 'none';
                }
            });
        }
        function descargarExcelCumplimiento() {
            fetch('/descargar_detalle_cumplimiento_porcentajes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tipo: filtroActivo })
            })
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'detalle_no_cumplen_' + filtroActivo + '.xlsx';
                document.body.appendChild(a);
                a.click();
                a.remove();
            });
        }
        function descargarExcelInferiores() {
            filtroActivo = 'inferiores';
            descargarExcelCumplimiento();
        }
        function descargarExcelSuperiores() {
            filtroActivo = 'superiores';
            descargarExcelCumplimiento();
        }
        </script>
        '''
        return html
    except Exception as e:
        return f'<b>Error:</b> {str(e)}', 500

@app.route('/grafico_cumplimiento_porcentajes', methods=['POST'])
def grafico_cumplimiento_porcentajes():
    import pandas as pd
    data = request.get_json()
    municipio = data.get('municipio')
    anio = data.get('anio')
    ciclo = data.get('ciclo')
    
    if not municipio or not anio or not ciclo:
        return jsonify({'error': 'Municipio, año y ciclo requeridos'}), 400
    
    try:
        # Obtener datos de la base de datos
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        
        conn = sqlite3.connect(ruta_db)
        
        # Filtros para el período específico
        where_clause = "WHERE 1=1"
        params = []
        
        if anio != 'todos':
            where_clause += " AND substr(S_PERIODO, 1, 4) = ?"
            params.append(anio)
        if ciclo != 'todos':
            where_clause += " AND S_CICLO = ?"
            params.append(ciclo)
        
        # Total de registros para el período
        query_total = f"SELECT COUNT(*) as total FROM lecturas {where_clause}"
        total_registros = pd.read_sql_query(query_total, conn, params=params).iloc[0]['total']
        
        conn.close()
        
        # Usar el cache del detalle de cumplimiento si existe
        cache = globals().get('_detalle_cumplimiento_cache')
        if cache is None or cache.empty:
            return jsonify({'error': 'No hay datos de análisis de cumplimiento. Ejecuta el análisis primero.'}), 400
        
        # Contar por tipo de incumplimiento
        tipo_counts = cache['TIPO_INCUMPLIMIENTO'].value_counts().to_dict()
        
        # Mapear nombres más legibles
        tipo_names = {
            'porcentaje_inferior': 'Porcentaje Inferior',
            'porcentaje_superior': 'Porcentaje Superior', 
            'valor_inferior': 'Valor Inferior',
            'valor_superior': 'Valor Superior',
            'datos_invalidos': 'Datos Inválidos',
            'logica_no_encontrada': 'Lógica No Encontrada',
            'calculo_no_aplicable': 'Cálculo No Aplicable'
        }
        
        # Preparar datos para el gráfico
        chart_data = []
        for tipo, count in tipo_counts.items():
            chart_data.append({
                'tipo': tipo_names.get(tipo, tipo),
                'cantidad': count
            })
        
        total_incumplen = sum(tipo_counts.values())
        
        return jsonify({
            'periodo': f"{anio}-{ciclo}" if anio != 'todos' and ciclo != 'todos' else f"Año: {anio}, Ciclo: {ciclo}",
            'total_registros': total_registros,
            'total_incumplen': total_incumplen,
            'porcentaje_incumplimiento': round((total_incumplen / total_registros) * 100, 2) if total_registros > 0 else 0,
            'datos_grafico': chart_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descargar_detalle_cumplimiento_porcentajes', methods=['POST'])
def descargar_detalle_cumplimiento_porcentajes():
    import pandas as pd
    from io import BytesIO
    data = request.get_json()
    tipo = data.get('tipo', 'todos')
    if tipo == 'inferiores':
        cache = globals().get('_detalle_cumplimiento_inferiores')
    elif tipo == 'superiores':
        cache = globals().get('_detalle_cumplimiento_superiores')
    elif tipo == 'excesivos':
        cache = globals().get('_detalle_cumplimiento_excesivos')
    elif tipo == 'excesivos_no_incrementa':
        cache = globals().get('_detalle_cumplimiento_excesivos_no_incrementa')
    else:
        cache = globals().get('_detalle_cumplimiento_cache')
    if cache is None or cache.empty:
        return 'No hay datos para descargar. Ejecuta el análisis primero.', 400
    output = BytesIO()
    cache.to_excel(output, index=False)
    output.seek(0)
    from flask import send_file
    return send_file(output, as_attachment=True, download_name=f'detalle_no_cumplen_{tipo}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/descargar_logica_porcentajes_guacari')
def descargar_logica_porcentajes_guacari():
    """
    Permite descargar la lógica de porcentajes y UVT para Guacarí en un solo archivo Excel editable.
    Si el archivo no existe, lo crea con la estructura sugerida.
    """
    import pandas as pd
    from flask import send_file
    path = os.path.join(os.path.dirname(__file__), 'logica_porcentajes_guacari.xlsx')
    if not os.path.exists(path):
        # Estructura sugerida
        data = [
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 1", "S_PORCENTAJE_TARIFA": 5, "S_PORCENTAJE_UVT": 8.5, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 2", "S_PORCENTAJE_TARIFA": 7, "S_PORCENTAJE_UVT": 11.5, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 3", "S_PORCENTAJE_TARIFA": 10, "S_PORCENTAJE_UVT": 22.5, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 4", "S_PORCENTAJE_TARIFA": 15, "S_PORCENTAJE_UVT": 38, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 5", "S_PORCENTAJE_TARIFA": 30, "S_PORCENTAJE_UVT": 76, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 6", "S_PORCENTAJE_TARIFA": 40, "S_PORCENTAJE_UVT": 85, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 1 RURAL DISPERSO", "S_PORCENTAJE_TARIFA": 3, "S_PORCENTAJE_UVT": 2, "UVT": 49799, "AÑO": 2025},
            {"S_MPIO": "GUACARÍ", "S_TIPO_USO": "RESIDENCIAL", "S_TIPO_MERCADO": "REGULADO", "S_ESTRATO": "ESTRATO 2 RURAL DISPERSO", "S_PORCENTAJE_TARIFA": 3.5, "S_PORCENTAJE_UVT": 3, "UVT": 49799, "AÑO": 2025},
        ]
        df = pd.DataFrame(data)
        df.to_excel(path, index=False)
    return send_file(path, as_attachment=True, download_name='logica_porcentajes_guacari.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def kw_in_range(cant_kw_val, rango):
    # Asegurar que cant_kw_val sea un número
    try:
        cant_kw_val = float(cant_kw_val)
    except (ValueError, TypeError):
        return False
    
    rango = str(rango).replace(' ', '')
    if '-' in rango:
        try:
            min_kw, max_kw = rango.split('-')
            min_kw = float(min_kw)
            max_kw = float(max_kw)
            return min_kw <= cant_kw_val <= max_kw
        except (ValueError, TypeError):
            return False
    else:
        # Si solo hay un número, es el mínimo (sin tope superior)
        try:
            min_kw = float(rango)
            return cant_kw_val >= min_kw
        except (ValueError, TypeError):
            return False

def formatear_pesos(valor):
    try:
        valor = float(valor)
        partes = f"{valor:,.1f}".split(".")
        miles = partes[0].replace(",", ".")
        decimales = partes[1] if len(partes) > 1 else "0"
        return f"${miles},{decimales}"
    except Exception:
        return valor

@app.route('/promedios_multianio', methods=['POST'])
def promedios_multianio():
    data = request.get_json()
    municipio = data.get('municipio')
    years = [str(y) for y in data.get('years', [])]
    if not municipio or not years:
        return jsonify({'error': 'Municipio y años requeridos'}), 400
    municipio_upper = municipio.upper()
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return jsonify({'error': 'No existe la base de datos. Ejecuta la consolidación primero.'}), 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        resultados = {}
        s_id_info = {}
        # 1. Calcular promedios por s_id y año, incluyendo campos adicionales
        for year in years:
            cur.execute("""
                SELECT S_ID, MIN(S_NOMBRE), MIN(S_TIPO_MERCADO), MIN(S_TIPO_USO), AVG(CANT_KW), AVG(VR_FACT), AVG(VR_RECAUDO)
                FROM lecturas
                WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ?
                GROUP BY S_ID
            """, (municipio_upper, year))
            for s_id, s_nombre, s_tipo_mercado, s_tipo_uso, avg_kw, avg_fact, avg_recaudo in cur.fetchall():
                # Almacenar información del S_ID
                if s_id not in s_id_info:
                    s_id_info[s_id] = {
                        's_nombre': s_nombre,
                        's_tipo_mercado': s_tipo_mercado,
                        's_tipo_uso': s_tipo_uso
                    }
                resultados.setdefault(s_id, {})[year] = {
                    'kw': round(avg_kw,2) if avg_kw else None,
                    'fact': round(avg_fact,2) if avg_fact else None,
                    'recaudo': round(avg_recaudo,2) if avg_recaudo else None
                }
        # 2. Si el año más alto es el último disponible, tratar mes final
        last_year = max(years)
        cur.execute("""
            SELECT MAX(CAST(substr(S_PERIODO,6,2) AS INTEGER))
            FROM lecturas
            WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ?
        """, (municipio_upper, last_year))
        mes_max = cur.fetchone()[0]
        last_cons = {}
        if mes_max and mes_max > 1:
            # Promedio hasta mes anterior
            cur.execute("""
                SELECT S_ID, AVG(CANT_KW), AVG(VR_FACT), AVG(VR_RECAUDO)
                FROM lecturas
                WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ? AND CAST(substr(S_PERIODO,6,2) AS INTEGER) < ?
                GROUP BY S_ID
            """, (municipio_upper, last_year, mes_max))
            for s_id, avg_kw, avg_fact, avg_recaudo in cur.fetchall():
                if s_id in resultados:
                    resultados[s_id][last_year] = {
                        'kw': round(avg_kw,2) if avg_kw else None,
                        'fact': round(avg_fact,2) if avg_fact else None,
                        'recaudo': round(avg_recaudo,2) if avg_recaudo else None
                    }
            # Consumo del último mes
            cur.execute("""
                SELECT S_ID, SUM(CANT_KW), SUM(VR_FACT), SUM(VR_RECAUDO)
                FROM lecturas
                WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ? AND CAST(substr(S_PERIODO,6,2) AS INTEGER) = ?
                GROUP BY S_ID
            """, (municipio_upper, last_year, mes_max))
            for s_id, cons_kw, cons_fact, cons_recaudo in cur.fetchall():
                last_cons[s_id] = {
                    'kw': round(cons_kw,2) if cons_kw else None,
                    'fact': round(cons_fact,2) if cons_fact else None,
                    'recaudo': round(cons_recaudo,2) if cons_recaudo else None
                }
        # Formatear salida
        out = []
        for s_id, avs in resultados.items():
            # Obtener información adicional del S_ID
            info = s_id_info.get(s_id, {})
            
            # Obtener promedios del último año y consumo del último mes
            last_year_avg = avs.get(last_year, {}) if last_year in avs else {}
            last_consumption = last_cons.get(s_id, {})
            
            # Calcular columnas de diferencias y proporción
            def safe_calc(avg_val, cons_val, operation='diff'):
                if avg_val is None or cons_val is None or avg_val == 0 or cons_val == 0:
                    return '-'
                if operation == 'proportion':
                    return round(avg_val / cons_val, 2)
                else:  # diff
                    return round(avg_val - cons_val, 2)
            
            proporcion_dif_cant_kw = safe_calc(last_year_avg.get('kw'), last_consumption.get('kw'), 'proportion')
            dif_cant_kw = safe_calc(last_year_avg.get('kw'), last_consumption.get('kw'))
            dif_vr_fact = safe_calc(last_year_avg.get('fact'), last_consumption.get('fact'))
            dif_vr_rec = safe_calc(last_year_avg.get('recaudo'), last_consumption.get('recaudo'))
            
            out.append({
                's_id': s_id,
                's_nombre': info.get('s_nombre'),
                's_tipo_mercado': info.get('s_tipo_mercado'),
                's_tipo_uso': info.get('s_tipo_uso'),
                'averages': {y: avs[y] if y in avs else None for y in years},
                'lastConsumption': last_consumption,
                'proporcion_dif_cant_kw': proporcion_dif_cant_kw,
                'dif_cant_kw': dif_cant_kw,
                'dif_vr_fact': dif_vr_fact,
                'dif_vr_rec': dif_vr_rec
            })
        conn.close()
        return jsonify({
            'results': out,
            'lastMonth': {'year': last_year, 'month': mes_max} if mes_max else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_promedios_multianio', methods=['POST'])
def download_promedios_multianio():
    from io import BytesIO
    data = request.get_json()
    municipio = data.get('municipio')
    years = [str(y) for y in data.get('years', [])]
    if not municipio or not years:
        return 'Faltan parámetros', 400
    municipio_upper = municipio.upper()
    try:
        ruta_base = get_base_path(municipio)
        ruta_db = 'consumo.db'
        if not os.path.exists(ruta_db):
            return 'No existe la base de datos', 400
        conn = sqlite3.connect(ruta_db)
        cur = conn.cursor()
        resultados = {}
        s_id_info = {}
        for year in years:
            cur.execute("""
                SELECT S_ID, MIN(S_NOMBRE), MIN(S_TIPO_MERCADO), MIN(S_TIPO_USO), AVG(CANT_KW), AVG(VR_FACT), AVG(VR_RECAUDO)
                FROM lecturas
                WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ?
                GROUP BY S_ID
            """, (municipio_upper, year))
            for s_id, s_nombre, s_tipo_mercado, s_tipo_uso, avg_kw, avg_fact, avg_recaudo in cur.fetchall():
                # Almacenar información del S_ID
                if s_id not in s_id_info:
                    s_id_info[s_id] = {
                        's_nombre': s_nombre,
                        's_tipo_mercado': s_tipo_mercado,
                        's_tipo_uso': s_tipo_uso
                    }
                resultados.setdefault(s_id, {})[year] = {
                    'kw': round(avg_kw,2) if avg_kw else None,
                    'fact': round(avg_fact,2) if avg_fact else None,
                    'recaudo': round(avg_recaudo,2) if avg_recaudo else None
                }
        last_year = max(years)
        cur.execute("""
            SELECT MAX(CAST(substr(S_PERIODO,6,2) AS INTEGER))
            FROM lecturas
            WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ?
        """, (municipio_upper, last_year))
        mes_max = cur.fetchone()[0]
        last_cons = {}
        if mes_max and mes_max > 1:
            cur.execute("""
                SELECT S_ID, AVG(CANT_KW), AVG(VR_FACT), AVG(VR_RECAUDO)
                FROM lecturas
                WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ? AND CAST(substr(S_PERIODO,6,2) AS INTEGER) < ?
                GROUP BY S_ID
            """, (municipio_upper, last_year, mes_max))
            for s_id, avg_kw, avg_fact, avg_recaudo in cur.fetchall():
                if s_id in resultados:
                    resultados[s_id][last_year] = {
                        'kw': round(avg_kw,2) if avg_kw else None,
                        'fact': round(avg_fact,2) if avg_fact else None,
                        'recaudo': round(avg_recaudo,2) if avg_recaudo else None
                    }
            cur.execute("""
                SELECT S_ID, SUM(CANT_KW), SUM(VR_FACT), SUM(VR_RECAUDO)
                FROM lecturas
                WHERE S_MPIO = ? AND substr(S_PERIODO,1,4) = ? AND CAST(substr(S_PERIODO,6,2) AS INTEGER) = ?
                GROUP BY S_ID
            """, (municipio_upper, last_year, mes_max))
            for s_id, cons_kw, cons_fact, cons_recaudo in cur.fetchall():
                last_cons[s_id] = {
                    'kw': round(cons_kw,2) if cons_kw else None,
                    'fact': round(cons_fact,2) if cons_fact else None,
                    'recaudo': round(cons_recaudo,2) if cons_recaudo else None
                }
        # Construir DataFrame
        import pandas as pd
        cols = ['S_ID', 'S_NOMBRE', 'S_TIPO_MERCADO', 'S_TIPO_USO']
        for y in years:
            cols += [f'PROM KW {y}', f'PROM FACT {y}', f'PROM RECAUDO {y}']
        if mes_max and mes_max > 1:
            cols += [f'Consumo KW {last_year}-{mes_max}', f'Consumo FACT {last_year}-{mes_max}', f'Consumo RECAUDO {last_year}-{mes_max}']
            cols += ['PROPORCION DIF CANT_KW', 'DIF CANT_KW', 'DIF VR_FACT', 'DIF VR_REC']
        rows = []
        for s_id, avs in resultados.items():
            # Obtener información adicional del S_ID
            info = s_id_info.get(s_id, {})
            
            row = [s_id, info.get('s_nombre'), info.get('s_tipo_mercado'), info.get('s_tipo_uso')]
            for y in years:
                v = avs.get(y, {})
                row += [v.get('kw'), v.get('fact'), v.get('recaudo')]
            if mes_max and mes_max > 1:
                v = last_cons.get(s_id, {})
                row += [v.get('kw'), v.get('fact'), v.get('recaudo')]
                
                # Calcular columnas de diferencias y proporción
                def safe_calc(avg_val, cons_val, operation='diff'):
                    if avg_val is None or cons_val is None or avg_val == 0 or cons_val == 0:
                        return '-'
                    if operation == 'proportion':
                        return round(avg_val / cons_val, 2)
                    else:  # diff
                        return round(avg_val - cons_val, 2)
                
                # Obtener promedios del último año y consumo del último mes
                last_year_avg = avs.get(last_year, {}) if last_year in avs else {}
                last_consumption = last_cons.get(s_id, {})
                
                proporcion_dif_cant_kw = safe_calc(last_year_avg.get('kw'), last_consumption.get('kw'), 'proportion')
                dif_cant_kw = safe_calc(last_year_avg.get('kw'), last_consumption.get('kw'))
                dif_vr_fact = safe_calc(last_year_avg.get('fact'), last_consumption.get('fact'))
                dif_vr_rec = safe_calc(last_year_avg.get('recaudo'), last_consumption.get('recaudo'))
                
                row += [proporcion_dif_cant_kw, dif_cant_kw, dif_vr_fact, dif_vr_rec]
            rows.append(row)
        df = pd.DataFrame(rows, columns=cols)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        filename = f"promedios_multianio_{municipio}.xlsx"
        from flask import send_file
        conn.close()
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    app.run(debug=True) 

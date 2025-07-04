#!/usr/bin/env python3
"""
Interfaz web Streamlit mejorada para el sistema RAG especializado.
Incluye análisis de tablas, JOINs inteligentes y visualización de PKs.
"""

import streamlit as st
import sys
import os
import pandas as pd
from pathlib import Path
import json
import time
from datetime import datetime

# Configurar path para importaciones
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

# Configuración de la página
st.set_page_config(
    page_title="RAG SQL Agent - Análisis Inteligente",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🎯 RAG SQL Agent - Análisis Inteligente de Base de Datos</h1>
    <p>Sistema especializado para análisis de tablas Bantotal con JOINs automáticos basados en PKs</p>
</div>
""", unsafe_allow_html=True)

# Importaciones de módulos
@st.cache_resource
def load_database_explorer():
    """Cargar el explorador de base de datos"""
    try:
        from database_explorer import DatabaseExplorer
        return DatabaseExplorer()
    except ImportError:
        st.error("❌ No se pudo cargar DatabaseExplorer")
        return None

def test_connection():
    """Probar conexión a la base de datos"""
    try:
        explorer = load_database_explorer()
        if explorer and explorer.connect():
            return True, "✅ Conexión exitosa"
        else:
            return False, "❌ Error de conexión"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# Sidebar con información del sistema
with st.sidebar:
    st.header("🔧 Estado del Sistema")
    
    # Test de conexión
    if st.button("🔍 Probar Conexión"):
        with st.spinner("Probando conexión..."):
            success, message = test_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    st.markdown("---")
    
    # Configuración
    st.header("⚙️ Configuración")
    
    # Límites de búsqueda
    search_limit = st.slider("Límite de búsqueda de tablas", 5, 50, 20)
    show_all_columns = st.checkbox("Mostrar todos los campos", False)
    
    st.markdown("---")
    
    # Información del sistema
    st.header("📊 Información")
    
    try:
        explorer = load_database_explorer()
        if explorer and explorer.connect():
            overview = explorer.get_database_overview()
            if overview:
                st.metric("Total Tablas", overview.get('TOTAL_TABLES', 'N/A'))
                st.metric("Total Vistas", overview.get('TOTAL_VIEWS', 'N/A'))
                st.metric("Base de Datos", overview.get('DATABASE_NAME', 'N/A'))
                
                # Estadísticas Bantotal
                if 'bantotal_prefixes' in overview and overview['bantotal_prefixes']:
                    st.subheader("Prefijos Bantotal")
                    for prefix_info in overview['bantotal_prefixes'][:5]:
                        st.text(f"{prefix_info['PREFIX']}: {prefix_info['TABLE_COUNT']} tablas")
            explorer.close()
    except:
        st.warning("No se pudo obtener información del sistema")

# Contenido principal
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Explorador de Tablas", "🔗 Análisis de JOINs", "🧠 Consultas RAG", "📊 Reportes"])

with tab1:
    st.header("🔍 Explorador de Tablas")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Buscar tabla", placeholder="Ej: FSD601, abonados, clientes...")
    
    with col2:
        search_button = st.button("🚀 Buscar", type="primary")
    
    if search_button or search_term:
        if search_term:
            with st.spinner(f"Buscando tablas que contengan '{search_term}'..."):
                try:
                    explorer = load_database_explorer()
                    if explorer and explorer.connect():
                        tables = explorer.search_tables(search_term, limit=search_limit)
                        
                        if tables:
                            st.success(f"✅ Encontradas {len(tables)} tablas")
                            
                            # Mostrar tablas en un dataframe
                            df_tables = pd.DataFrame(tables)
                            st.dataframe(df_tables, use_container_width=True)
                            
                            # Análisis detallado de la primera tabla
                            if st.button("📋 Analizar Primera Tabla"):
                                best_table = tables[0]
                                
                                with st.expander(f"🏗️ Estructura de {best_table['full_name']}", expanded=True):
                                    structure = explorer.get_table_structure(
                                        best_table['table_name'], 
                                        best_table['schema_name']
                                    )
                                    
                                    if structure:
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            st.metric("Total Campos", structure['column_count'])
                                        
                                        with col2:
                                            st.metric("Tiene PK", "✅" if structure['has_primary_key'] else "❌")
                                        
                                        with col3:
                                            st.metric("Claves PK", len(structure['primary_keys']))
                                        
                                        # Mostrar PKs
                                        if structure['has_primary_key']:
                                            st.markdown("**🔑 Claves Primarias:**")
                                            for pk in structure['primary_keys']:
                                                st.code(pk, language="sql")
                                        
                                        # Mostrar campos
                                        st.markdown("**📋 Estructura de Campos:**")
                                        
                                        columns_data = []
                                        for col in structure['columns']:
                                            columns_data.append({
                                                'Campo': col['name'],
                                                'Tipo': col['full_type'],
                                                'Nullable': col['is_nullable'],
                                                'PK': '🔑' if col['is_primary_key'] == 'YES' else '',
                                                'Posición': col['ordinal_position']
                                            })
                                        
                                        df_columns = pd.DataFrame(columns_data)
                                        
                                        if show_all_columns:
                                            st.dataframe(df_columns, use_container_width=True)
                                        else:
                                            st.dataframe(df_columns.head(10), use_container_width=True)
                                            if len(df_columns) > 10:
                                                st.info(f"Mostrando 10 de {len(df_columns)} campos. Activa 'Mostrar todos los campos' en la barra lateral para ver todos.")
                        else:
                            st.warning(f"❌ No se encontraron tablas con '{search_term}'")
                        
                        explorer.close()
                    else:
                        st.error("❌ No se pudo conectar a la base de datos")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.info("Ingresa un término de búsqueda")

with tab2:
    st.header("🔗 Análisis de JOINs Inteligentes")
    
    table_for_joins = st.text_input("🎯 Tabla para análisis de JOINs", placeholder="Ej: FSD601")
    
    if st.button("🧠 Generar JOINs Inteligentes"):
        if table_for_joins:
            with st.spinner(f"Analizando relaciones de {table_for_joins}..."):
                try:
                    # Importar el generador de JOINs
                    sys.path.insert(0, str(project_root))
                    from smart_join_generator import find_related_tables, generate_smart_joins
                    
                    explorer = load_database_explorer()
                    if explorer and explorer.connect():
                        # Obtener estructura de la tabla principal
                        structure = explorer.get_table_structure(table_for_joins)
                        
                        if structure:
                            st.success(f"✅ Tabla {table_for_joins} encontrada")
                            
                            # Mostrar PKs
                            if structure['has_primary_key']:
                                st.markdown("**🔑 Claves Primarias:**")
                                pk_cols = st.columns(len(structure['primary_keys']))
                                for i, pk in enumerate(structure['primary_keys']):
                                    pk_cols[i].code(pk)
                            
                            # Buscar tablas relacionadas
                            related_tables = find_related_tables(explorer, table_for_joins)
                            
                            if related_tables:
                                st.success(f"✅ Encontradas {len(related_tables)} tablas relacionadas")
                                
                                # Mostrar tablas relacionadas
                                with st.expander("📊 Tablas Relacionadas", expanded=True):
                                    for table_name, table_info in related_tables.items():
                                        with st.container():
                                            st.markdown(f"**{table_name}**")
                                            
                                            common_fields = [field['field'] for field in table_info['common_fields']]
                                            st.write(f"Campos comunes: {', '.join(common_fields)}")
                                            
                                            for condition in table_info['join_conditions']:
                                                st.code(condition, language="sql")
                                            
                                            st.markdown("---")
                                
                                # Generar consultas SQL
                                queries = generate_smart_joins(table_for_joins, related_tables)
                                
                                if queries:
                                    st.header("🚀 Consultas SQL Generadas")
                                    
                                    for i, query_info in enumerate(queries):
                                        with st.expander(f"Query {i+1}: {query_info['description']}", expanded=False):
                                            st.write(f"**Tablas:** {', '.join(query_info['tables'])}")
                                            st.write(f"**Campos comunes:** {query_info['common_fields']}")
                                            
                                            st.code(query_info['sql'], language="sql")
                                            
                                            # Botón para copiar
                                            if st.button(f"📋 Copiar Query {i+1}", key=f"copy_{i}"):
                                                st.success("Query copiada al portapapeles (funcionalidad simulada)")
                            else:
                                st.warning("❌ No se encontraron tablas relacionadas")
                        else:
                            st.error(f"❌ No se encontró la tabla {table_for_joins}")
                        
                        explorer.close()
                    else:
                        st.error("❌ No se pudo conectar a la base de datos")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.info("Ingresa el nombre de una tabla")

with tab3:
    st.header("🧠 Consultas RAG Inteligentes")
    
    query_input = st.text_area(
        "💬 Ingresa tu consulta:", 
        placeholder="Ej: SELECT de FSD601 con relaciones usando claves primarias",
        height=100
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🚀 Ejecutar Consulta", type="primary"):
            if query_input:
                with st.spinner("Procesando consulta..."):
                    try:
                        # Aquí iría la integración con el sistema RAG
                        st.info("🔄 Funcionalidad RAG en desarrollo")
                        st.code(f"# Tu consulta:\n{query_input}", language="python")
                        
                        # Simulación de respuesta
                        st.markdown("**Respuesta simulada:**")
                        st.success("Esta sería la respuesta del sistema RAG basada en tu consulta.")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Por favor ingresa una consulta")

with tab4:
    st.header("📊 Reportes del Sistema")
    
    report_type = st.selectbox(
        "Tipo de Reporte:",
        ["Resumen de Base de Datos", "Análisis de Prefijos Bantotal", "Tablas sin PK", "Estadísticas de Uso"]
    )
    
    if st.button("📈 Generar Reporte"):
        with st.spinner("Generando reporte..."):
            try:
                explorer = load_database_explorer()
                if explorer and explorer.connect():
                    
                    if report_type == "Resumen de Base de Datos":
                        overview = explorer.get_database_overview()
                        if overview:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Total Tablas", overview.get('TOTAL_TABLES', 'N/A'))
                            
                            with col2:
                                st.metric("Total Vistas", overview.get('TOTAL_VIEWS', 'N/A'))
                            
                            with col3:
                                st.metric("Esquemas", overview.get('TOTAL_SCHEMAS', 'N/A'))
                    
                    elif report_type == "Análisis de Prefijos Bantotal":
                        overview = explorer.get_database_overview()
                        if overview and 'bantotal_prefixes' in overview:
                            df_prefixes = pd.DataFrame(overview['bantotal_prefixes'])
                            st.bar_chart(df_prefixes.set_index('PREFIX')['TABLE_COUNT'])
                            st.dataframe(df_prefixes, use_container_width=True)
                    
                    explorer.close()
                else:
                    st.error("❌ No se pudo conectar a la base de datos")
                    
            except Exception as e:
                st.error(f"❌ Error generando reporte: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    🎯 RAG SQL Agent - Sistema especializado para análisis de bases de datos Bantotal<br>
    Desarrollado con Streamlit y Python
</div>
""", unsafe_allow_html=True)
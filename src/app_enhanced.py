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
    """Cargar el explorador de base de datos mejorado"""
    try:
        from database_explorer_pymssql import DatabaseExplorer
        return DatabaseExplorer()
    except ImportError:
        # Fallback al explorador genérico
        try:
            from database_explorer import DatabaseExplorer
            st.warning("⚠️ Usando explorador genérico - algunas funciones limitadas")
            return DatabaseExplorer()
        except ImportError:
            st.error("❌ No se pudo cargar ningún DatabaseExplorer")
            return None

@st.cache_resource
def load_rag_director():
    """Cargar el director RAG"""
    try:
        from agent_director import AgentDirector
        return AgentDirector()
    except ImportError as e:
        st.error(f"❌ No se pudo cargar AgentDirector: {e}")
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
    
    # Estado del sistema RAG
    st.markdown("### 🤖 Sistema RAG")
    
    try:
        director = load_rag_director()
        if director:
            st.success("✅ Director RAG: Activo")
            
            # Mostrar estadísticas del director
            stats = director.get_director_stats()
            if stats:
                st.metric("Consultas Procesadas", stats.get('total_queries', 0))
                st.metric("Consultas SQL", stats.get('sql_queries_routed', 0))
                st.metric("Consultas Docs", stats.get('docs_queries_routed', 0))
            
            # Estado de agentes
            if hasattr(director, 'sql_agent') and director.sql_agent:
                st.text("🗄️ SQL Agent: Activo")
            else:
                st.text("❌ SQL Agent: Inactivo")
            
            if hasattr(director, 'docs_agent') and director.docs_agent:
                st.text("📚 Docs Agent: Activo")
            else:
                st.text("❌ Docs Agent: Inactivo")
        else:
            st.error("❌ Director RAG: Inactivo")
    except Exception as e:
        st.error(f"❌ Error RAG: {str(e)[:50]}...")
    
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
                                            fk_count = len(structure.get('foreign_keys', []))
                                            st.metric("Foreign Keys", fk_count)
                                        
                                        # Descripción de la tabla si existe
                                        table_desc = structure.get('table_description', '').strip()
                                        if table_desc:
                                            st.info(f"📝 **Descripción:** {table_desc}")
                                        
                                        # Crear tabs para organizar mejor la información
                                        tab1, tab2, tab3, tab4 = st.tabs(["📋 Campos", "🔑 Claves", "📊 Índices", "🔗 Constraints"])
                                        
                                        with tab1:
                                            # Mostrar campos
                                            st.markdown("**📋 Estructura de Campos:**")
                                            
                                            # Contadores para estadísticas
                                            fields_with_desc = 0
                                            total_fields = len(structure['columns'])
                                            
                                            columns_data = []
                                            for col in structure['columns']:
                                                description = col.get('description', '').strip()
                                                if description:
                                                    fields_with_desc += 1
                                                
                                                columns_data.append({
                                                    'Campo': col['name'],
                                                    'Tipo': col['full_type'],
                                                    'Nullable': col['is_nullable'],
                                                    'PK': '🔑' if col['is_primary_key'] == 'YES' else '',
                                                    'Posición': col['ordinal_position'],
                                                    'Descripción': description if description else '(Sin descripción)'
                                                })
                                            
                                            # Mostrar estadísticas de descripciones
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Total Campos", total_fields)
                                            with col2:
                                                st.metric("Con Descripción", fields_with_desc)
                                            with col3:
                                                percentage = (fields_with_desc / total_fields * 100) if total_fields > 0 else 0
                                                st.metric("Porcentaje", f"{percentage:.1f}%")
                                            
                                            # Crear dataframe con mejor formato
                                            df_columns = pd.DataFrame(columns_data)
                                            
                                            # Configurar columnas para mejor visualización
                                            column_config = {
                                                'Campo': st.column_config.TextColumn('Campo', width="medium"),
                                                'Tipo': st.column_config.TextColumn('Tipo', width="medium"),
                                                'Nullable': st.column_config.TextColumn('Null', width="small"),
                                                'PK': st.column_config.TextColumn('PK', width="small"),
                                                'Posición': st.column_config.NumberColumn('Pos', width="small"),
                                                'Descripción': st.column_config.TextColumn('Descripción', width="large")
                                            }
                                            
                                            if show_all_columns:
                                                st.dataframe(
                                                    df_columns, 
                                                    use_container_width=True,
                                                    column_config=column_config,
                                                    hide_index=True
                                                )
                                            else:
                                                st.dataframe(
                                                    df_columns.head(10), 
                                                    use_container_width=True,
                                                    column_config=column_config,
                                                    hide_index=True
                                                )
                                                if len(df_columns) > 10:
                                                    st.info(f"Mostrando 10 de {len(df_columns)} campos. Activa 'Mostrar todos los campos' en la barra lateral para ver todos.")
                                            
                                            # Mostrar vista alternativa para campos con descripciones
                                            if fields_with_desc > 0:
                                                with st.expander(f"📝 Vista Detallada de Descripciones ({fields_with_desc} campos)", expanded=False):
                                                    for i, col in enumerate(structure['columns'], 1):
                                                        description = col.get('description', '').strip()
                                                        if description:
                                                            pk_indicator = " 🔑" if col['is_primary_key'] == 'YES' else ""
                                                            st.markdown(f"**{i}. {col['name']}**: {col['full_type']}{pk_indicator}")
                                                            st.markdown(f"   📝 {description}")
                                                            st.markdown("---")
                                        
                                        with tab2:
                                            # Claves Primarias
                                            if structure['has_primary_key']:
                                                st.markdown("**🔑 Claves Primarias:**")
                                                for pk in structure['primary_keys']:
                                                    st.code(pk, language="sql")
                                            else:
                                                st.warning("⚠️ Esta tabla no tiene claves primarias definidas")
                                            
                                            # Foreign Keys
                                            foreign_keys = structure.get('foreign_keys', [])
                                            if foreign_keys:
                                                st.markdown("**🔗 Claves Foráneas:**")
                                                fk_data = []
                                                for fk in foreign_keys:
                                                    fk_data.append({
                                                        'Campo Local': fk['column_name'],
                                                        'Constraint': fk['constraint_name'],
                                                        'Tabla Referenciada': f"{fk['referenced_schema']}.{fk['referenced_table']}",
                                                        'Campo Referenciado': fk['referenced_column']
                                                    })
                                                st.dataframe(pd.DataFrame(fk_data), use_container_width=True)
                                            else:
                                                st.info("ℹ️ No se encontraron claves foráneas")
                                        
                                        with tab3:
                                            # Índices
                                            indexes = structure.get('indexes', [])
                                            if indexes:
                                                st.markdown("**📊 Índices:**")
                                                index_data = []
                                                for idx in indexes:
                                                    index_data.append({
                                                        'Nombre': idx['index_name'],
                                                        'Tipo': idx['index_type'],
                                                        'Único': '✅' if idx['is_unique'] else '❌',
                                                        'PK': '🔑' if idx['is_primary_key'] else '',
                                                        'Columnas': idx['columns']
                                                    })
                                                st.dataframe(pd.DataFrame(index_data), use_container_width=True)
                                            else:
                                                st.info("ℹ️ No se encontraron índices")
                                        
                                        with tab4:
                                            # Constraints
                                            constraints = structure.get('constraints', [])
                                            if constraints:
                                                st.markdown("**🔗 Constraints:**")
                                                const_data = []
                                                for const in constraints:
                                                    const_data.append({
                                                        'Nombre': const['CONSTRAINT_NAME'],
                                                        'Tipo': const['CONSTRAINT_TYPE'],
                                                        'Columnas': const['columns'] or 'N/A'
                                                    })
                                                st.dataframe(pd.DataFrame(const_data), use_container_width=True)
                                            else:
                                                st.info("ℹ️ No se encontraron constraints adicionales")
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
                                st.success(f"✅ Encontradas {len(related_tables)} tablas relacionadas usando algoritmo de primeras 9 PKs")
                                
                                # Mostrar estadísticas de confianza
                                if related_tables:
                                    high_conf = sum(1 for info in related_tables.values() if info.get('confidence', 0) >= 0.5)
                                    med_conf = sum(1 for info in related_tables.values() if 0.3 <= info.get('confidence', 0) < 0.5)
                                    low_conf = sum(1 for info in related_tables.values() if info.get('confidence', 0) < 0.3)
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    col1.metric("🔥 Alta Confianza", high_conf, help="Confianza ≥ 50%")
                                    col2.metric("🔶 Media Confianza", med_conf, help="Confianza 30-50%")
                                    col3.metric("🔷 Baja Confianza", low_conf, help="Confianza < 30%")
                                    col4.metric("📊 Total Tablas", len(related_tables))
                                
                                # Mostrar tablas relacionadas con confianza mejorada
                                with st.expander("📊 Tablas Relacionadas (Primeras 9 PKs)", expanded=True):
                                    # Ordenar por confianza
                                    sorted_tables = sorted(
                                        related_tables.items(),
                                        key=lambda x: x[1].get('confidence', len(x[1]['common_fields'])/9.0),
                                        reverse=True
                                    )
                                    
                                    for table_name, table_info in sorted_tables:
                                        with st.container():
                                            # Header con confianza
                                            confidence = table_info.get('confidence', len(table_info['common_fields'])/9.0)
                                            match_count = table_info.get('match_count', len(table_info['common_fields']))
                                            
                                            if confidence >= 0.5:
                                                confidence_color = "🔥"  # Alta
                                            elif confidence >= 0.3:
                                                confidence_color = "🔶"  # Media  
                                            else:
                                                confidence_color = "🔷"  # Baja
                                            
                                            st.markdown(f"**{confidence_color} {table_name}** - {confidence:.1%} confianza ({match_count}/9 PKs)")
                                            
                                            # Mostrar campos comunes con posiciones
                                            common_fields_info = []
                                            for field in table_info['common_fields']:
                                                if isinstance(field, dict) and 'position' in field:
                                                    common_fields_info.append(f"Pos{field['position']}: {field['field']}")
                                                elif isinstance(field, dict):
                                                    common_fields_info.append(field['field'])
                                                else:
                                                    common_fields_info.append(str(field))
                                            
                                            st.write(f"🔑 **Campos PK coincidentes:** {', '.join(common_fields_info)}")
                                            
                                            # Mostrar solo primeras 3 condiciones JOIN para claridad
                                            st.write(f"🔗 **Condiciones JOIN (primeras 3 de {len(table_info['join_conditions'])}):**")
                                            for condition in table_info['join_conditions'][:3]:
                                                st.code(condition, language="sql")
                                            
                                            if len(table_info['join_conditions']) > 3:
                                                st.caption(f"... y {len(table_info['join_conditions']) - 3} condiciones más")
                                            
                                            st.markdown("---")
                                
                                # Generar consultas SQL
                                queries = generate_smart_joins(table_for_joins, related_tables)
                                
                                if queries:
                                    st.header("🚀 Consultas SQL Generadas")
                                    
                                    for i, query_info in enumerate(queries):
                                        # Determinar color del icono según confianza
                                        confidence = query_info.get('confidence', 0)
                                        if confidence >= 0.7:
                                            icon = "🔥"  # Alta confianza
                                        elif confidence >= 0.4:
                                            icon = "🔶"  # Media confianza
                                        else:
                                            icon = "🔷"  # Baja confianza
                                        
                                        with st.expander(f"{icon} Query {i+1}: {query_info['description']}", expanded=False):
                                            # Métricas mejoradas con categorías
                                            col1, col2, col3, col4 = st.columns(4)
                                            col1.metric("📋 Tablas", len(query_info['tables']))
                                            col2.metric("🔑 Campos PK", query_info['common_fields'])
                                            if 'confidence' in query_info:
                                                col3.metric("🎯 Confianza", f"{query_info['confidence']:.1%}")
                                            if 'categories' in query_info:
                                                categories_count = len(query_info['categories'])
                                                col4.metric("🏢 Categorías", categories_count, help=f"Tipos: {', '.join(query_info['categories'])}")
                                            
                                            st.write(f"**📋 Tablas involucradas:** {', '.join(query_info['tables'])}")
                                            if 'categories' in query_info and query_info['categories']:
                                                categories_display = []
                                                for cat in query_info['categories']:
                                                    cat_emoji = {
                                                        'Bantotal_Standard': '🏦',
                                                        'Bancaria_Personalizada': '💼', 
                                                        'Vista': '🔍',
                                                        'Log': '📜',
                                                        'Temporal': '⏱️',
                                                        'Backup': '💾'
                                                    }.get(cat, '📊')
                                                    categories_display.append(f"{cat_emoji} {cat}")
                                                st.write(f"**🏢 Categorías de tablas:** {', '.join(categories_display)}")
                                            
                                            # Mostrar SQL con mejor formato
                                            st.markdown("**🚀 Consulta SQL Optimizada:**")
                                            st.code(query_info['sql'], language="sql")
                                            
                                            # Botones mejorados
                                            col1, col2 = st.columns([1, 1])
                                            with col1:
                                                if st.button(f"📋 Copiar Query {i+1}", key=f"copy_{i}"):
                                                    st.success("✅ Query copiada al portapapeles (funcionalidad simulada)")
                                            with col2:
                                                if st.button(f"▶️ Ejecutar Query {i+1}", key=f"exec_{i}"):
                                                    st.info("📝 Funcionalidad de ejecución pendiente de implementar")
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
    
    # Ejemplos de consultas
    with st.expander("📋 Ejemplos de Consultas", expanded=False):
        st.markdown("""
        **Consultas SQL:**
        - `SELECT * FROM FSD601 WHERE cliente_id = 12345`
        - `Mostrar estructura de tabla FST001`
        - `Generar consulta SQL para obtener datos de clientes`
        
        **Consultas de Documentación:**
        - `Cómo configurar GeneXus para Bantotal`
        - `Manual de instalación de Bantotal`
        - `Procedimiento para crear transacciones`
        
        **Consultas Mixtas:**
        - `SQL para obtener clientes y documentación de proceso`
        - `Estructura de FSD601 y cómo usar en GeneXus`
        """)
    
    query_input = st.text_area(
        "💬 Ingresa tu consulta:", 
        placeholder="Ej: SELECT de FSD601 con relaciones usando claves primarias",
        height=100
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        execute_button = st.button("🚀 Ejecutar Consulta", type="primary")
    
    with col2:
        show_routing = st.checkbox("📊 Mostrar Routing", value=True)
    
    # Botones de consulta rápida
    st.markdown("### 🚀 Consultas Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Análisis FSD601"):
            st.session_state.quick_query = "Mostrar estructura de tabla FSD601 con todas sus claves primarias y relaciones"
    
    with col2:
        if st.button("🔍 Buscar Clientes"):
            st.session_state.quick_query = "SELECT * FROM tablas de clientes con sus datos principales"
    
    with col3:
        if st.button("📚 Manual GeneXus"):
            st.session_state.quick_query = "Cómo configurar GeneXus para trabajar con Bantotal"
    
    # Aplicar consulta rápida si existe
    if hasattr(st.session_state, 'quick_query') and st.session_state.quick_query:
        query_input = st.session_state.quick_query
        st.session_state.quick_query = None
    
    if execute_button and query_input:
        with st.spinner("Procesando consulta con sistema RAG..."):
            try:
                # Cargar director RAG
                director = load_rag_director()
                
                if director:
                    # Procesar consulta
                    start_time = time.time()
                    result = director.process_query(query_input)
                    processing_time = time.time() - start_time
                    
                    if result:
                        # Mostrar información de routing si está habilitado
                        metadata = result.get('metadata', {})
                        
                        if show_routing:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Agente Usado", result.get('agent_used', 'N/A'))
                            
                            with col2:
                                confidence = metadata.get('intent_confidence', 0)
                                st.metric("Confianza", f"{confidence:.2f}")
                            
                            with col3:
                                st.metric("Tiempo (s)", f"{processing_time:.2f}")
                        
                        # Mostrar respuesta principal
                        st.markdown("### 🎯 Respuesta del Sistema RAG")
                        
                        # Mostrar la respuesta principal
                        answer = result.get('answer', '')
                        if answer:
                            st.markdown(answer)
                        else:
                            st.warning("No se recibió respuesta del sistema")
                        
                        # Mostrar información del resultado crudo si está disponible
                        raw_result = result.get('raw_result', {})
                        if raw_result and show_routing:
                            with st.expander("🔍 Información Técnica", expanded=False):
                                if isinstance(raw_result, dict):
                                    # Para SQLAgent - mostrar detalles técnicos
                                    if 'operation' in raw_result:
                                        st.text(f"Operación: {raw_result.get('operation', 'N/A')}")
                                    if 'table_name' in raw_result:
                                        st.text(f"Tabla objetivo: {raw_result.get('table_name', 'N/A')}")
                                    if 'sources_consulted' in raw_result:
                                        st.text(f"Fuentes consultadas: {len(raw_result.get('sources_consulted', []))}")
                                    
                                    # Mostrar JSON completo
                                    st.json(raw_result)
                                else:
                                    st.text(str(raw_result))
                        
                        # Guardar en historial de sesión
                        if 'query_history' not in st.session_state:
                            st.session_state.query_history = []
                        
                        st.session_state.query_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'query': query_input,
                            'agent': result.get('agent_used', 'Unknown'),
                            'confidence': metadata.get('intent_confidence', 0),
                            'processing_time': processing_time,
                            'success': metadata.get('success', False)
                        })
                        
                    else:
                        st.error("❌ No se pudo procesar la consulta")
                else:
                    st.error("❌ No se pudo cargar el sistema RAG")
                    
            except Exception as e:
                st.error(f"❌ Error procesando consulta: {str(e)}")
                import traceback
                with st.expander("🔍 Detalles del Error", expanded=False):
                    st.code(traceback.format_exc())
    
    elif execute_button:
        st.warning("Por favor ingresa una consulta")
    
    # Mostrar historial de consultas
    if 'query_history' in st.session_state and st.session_state.query_history:
        st.markdown("### 📈 Historial de Consultas")
        
        with st.expander("📋 Ver Historial", expanded=False):
            df_history = pd.DataFrame(st.session_state.query_history)
            st.dataframe(df_history, use_container_width=True)
            
            if st.button("🗑️ Limpiar Historial"):
                st.session_state.query_history = []
                st.success("Historial limpiado")
                st.rerun()

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
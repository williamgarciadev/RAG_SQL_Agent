# src/app.py

"""
Interfaz web Streamlit para el sistema RAG especializado.
Integra SQLAgent, DocsAgent y Director para consultas inteligentes.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Configurar path para importaciones
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

# Importaciones de agentes especializados
try:
    from agent_director import AgentDirector
    from sql_agent import SQLAgent
    from docs_agent import DocsAgent
    from indexer import get_index_info

    HAS_SPECIALIZED_AGENTS = True
except ImportError as e:
    st.error(f"❌ Error importando agentes especializados: {e}")
    st.info("Asegúrate de que los agentes estén en src/")
    # Fallback al agente original
    try:
        from agent import RAGAgent

        HAS_SPECIALIZED_AGENTS = False
        st.warning("⚠️ Usando agente original como fallback")
    except ImportError:
        st.error("❌ No se pudo cargar ningún agente")
        st.stop()

# Configuración de la página
st.set_page_config(
    page_title="RAG Especializado - Bancario & GeneXus",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }

    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.25rem;
    }

    .sql-badge {
        background-color: #e3f2fd;
        color: #1976d2;
        border: 1px solid #1976d2;
    }

    .docs-badge {
        background-color: #f3e5f5;
        color: #7b1fa2;
        border: 1px solid #7b1fa2;
    }

    .mixed-badge {
        background-color: #e8f5e8;
        color: #388e3c;
        border: 1px solid #388e3c;
    }

    .query-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .answer-box {
        background-color: #e8f4fd;
        border-left: 4px solid #1f77b4;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .sql-answer-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .docs-answer-box {
        background-color: #f3e5f5;
        border-left: 4px solid #7b1fa2;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .source-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }

    .stats-box {
        background-color: #fff3cd;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }

    .confidence-high { color: #2e7d32; font-weight: bold; }
    .confidence-medium { color: #f57c00; font-weight: bold; }
    .confidence-low { color: #d32f2f; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_director():
    """Inicializar Director de agentes especializados."""
    if not HAS_SPECIALIZED_AGENTS:
        return None

    try:
        return AgentDirector()
    except Exception as e:
        st.error(f"Error inicializando Director: {e}")
        return None


@st.cache_resource
def initialize_fallback_agent():
    """Inicializar agente original como fallback."""
    try:
        from agent import RAGAgent
        return RAGAgent()
    except Exception as e:
        st.error(f"Error inicializando agente fallback: {e}")
        return None


@st.cache_data(ttl=300)
def get_cached_index_info():
    """Obtener información del índice (cached)."""
    try:
        return get_index_info()
    except Exception as e:
        return {"error": str(e)}


def format_confidence(confidence):
    """Formatear confianza con colores."""
    if confidence >= 0.7:
        return f'<span class="confidence-high">{confidence:.2f} (Alta)</span>'
    elif confidence >= 0.4:
        return f'<span class="confidence-medium">{confidence:.2f} (Media)</span>'
    else:
        return f'<span class="confidence-low">{confidence:.2f} (Baja)</span>'


def get_agent_badge(intent):
    """Obtener badge del agente según la intención."""
    badges = {
        'sql': '<span class="agent-badge sql-badge">🗄️ SQLAgent</span>',
        'docs': '<span class="agent-badge docs-badge">📚 DocsAgent</span>',
        'mixed': '<span class="agent-badge mixed-badge">🔄 Ambos Agentes</span>',
        'fallback_sql': '<span class="agent-badge sql-badge">🗄️ SQLAgent (fallback)</span>',
        'fallback_docs': '<span class="agent-badge docs-badge">📚 DocsAgent (fallback)</span>'
    }
    return badges.get(intent, '<span class="agent-badge">🤖 Agente</span>')


def main():
    """Función principal de la aplicación Streamlit."""

    # Header principal
    if HAS_SPECIALIZED_AGENTS:
        st.markdown('<h1 class="main-header">🎯 RAG Especializado - Bancario & GeneXus</h1>', unsafe_allow_html=True)
        st.markdown("### 🧠 Sistema Inteligente con Agentes Especializados")

        # Mostrar agentes disponibles
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(get_agent_badge('sql'), unsafe_allow_html=True)
            st.caption("Consultas SQL optimizadas")
        with col2:
            st.markdown(get_agent_badge('docs'), unsafe_allow_html=True)
            st.caption("Documentación técnica")
        with col3:
            st.markdown(get_agent_badge('mixed'), unsafe_allow_html=True)
            st.caption("Consultas combinadas")
    else:
        st.markdown('<h1 class="main-header">🤖 RAG Bantotal & GeneXus</h1>', unsafe_allow_html=True)
        st.markdown("### 🔍 Consulta inteligente sobre documentación técnica")

    # Sidebar con información del sistema
    with st.sidebar:
        st.header("📊 Estado del Sistema")

        # Información del índice
        with st.spinner("Verificando índice..."):
            index_info = get_cached_index_info()

        if "error" in index_info:
            st.error(f"❌ Error: {index_info['error']}")
            st.info("💡 Ejecuta: `python src/indexer.py`")
            return

        if index_info.get('exists', False):
            st.success("✅ Índice vectorial activo")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📚 Documentos", index_info.get('live_count', 0))
            with col2:
                st.metric("💾 Caracteres", f"{index_info.get('total_characters', 0):,}")

            # Estadísticas por tipo
            source_stats = index_info.get('source_statistics', {})
            if source_stats:
                st.subheader("📂 Tipos de Fuente")
                for source_type, count in source_stats.items():
                    if source_type == 'file':
                        st.write(f"📄 Archivos locales: {count}")
                    elif source_type == 'web':
                        st.write(f"🌐 URLs procesadas: {count}")
                    elif source_type in ['database_table', 'database_schema', 'database']:
                        st.write(f"🗄️ Estructuras SQL: {count}")
                    else:
                        st.write(f"❓ {source_type}: {count}")

            # Estado de agentes especializados
            if HAS_SPECIALIZED_AGENTS:
                st.subheader("🎯 Agentes Especializados")
                director = initialize_director()
                if director:
                    st.success("✅ Director activo")
                    if hasattr(director, 'sql_agent') and director.sql_agent:
                        st.success("✅ SQLAgent disponible")
                    else:
                        st.error("❌ SQLAgent no disponible")

                    if hasattr(director, 'docs_agent') and director.docs_agent:
                        st.success("✅ DocsAgent disponible")
                    else:
                        st.error("❌ DocsAgent no disponible")
                else:
                    st.error("❌ Director no disponible")

            # Información técnica
            with st.expander("🔧 Detalles Técnicos"):
                st.write(f"**Modelo embedding:** {index_info.get('embedding_model', 'N/A')}")
                st.write(f"**Colección:** {index_info.get('collection_name', 'N/A')}")
                st.write(f"**Última actualización:** {index_info.get('created_at', 'N/A')[:19]}")
                st.write(f"**Versión:** {index_info.get('version', 'N/A')}")
                st.write(f"**Agentes especializados:** {'Sí' if HAS_SPECIALIZED_AGENTS else 'No'}")
        else:
            st.error("❌ Índice no disponible")
            st.info("💡 Ejecuta: `python src/indexer.py`")
            return

    # Inicializar agentes
    if HAS_SPECIALIZED_AGENTS:
        director = initialize_director()
        if not director:
            st.error("❌ No se pudo inicializar el Director")
            return
    else:
        agent = initialize_fallback_agent()
        if not agent:
            st.error("❌ No se pudo inicializar el agente RAG")
            return

    # Interfaz principal
    st.markdown("---")

    # Ejemplos de consultas específicos para agentes
    with st.expander("💡 Ejemplos de Consultas por Agente"):
        if HAS_SPECIALIZED_AGENTS:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🗄️ SQLAgent (Consultas SQL)")
                st.markdown("""
                - SELECT de tabla abonados con todos los campos
                - generar INSERT para nuevo cliente
                - UPDATE estado del servicio
                - consultar préstamos activos
                - eliminar registros inactivos
                """)

            with col2:
                st.markdown("#### 📚 DocsAgent (Documentación)")
                st.markdown("""
                - cómo usar FOR EACH en GeneXus
                - proceso de creación de clientes en Bantotal
                - manual de instalación de GeneXus
                - configurar base de datos
                - optimizar rendimiento
                """)

            st.markdown("#### 🔄 Consultas Mixtas (Ambos Agentes)")
            st.markdown("""
            - documentación de tabla abonados y generar SELECT
            - explicar estructura y crear consulta SQL
            - proceso de alta de clientes con ejemplos SQL
            """)
        else:
            st.markdown("""
            **Sobre Préstamos Bancarios:**
            - ¿Cómo crear un préstamo en Bantotal?
            - ¿Qué son las subcuentas de cobro de cuotas?

            **Sobre Programación GeneXus:**
            - ¿Cuál es la sintaxis del comando FOR EACH?
            - ¿Cómo optimizar performance en FOR EACH?

            **Sobre Base de Datos:**
            - ¿Qué contiene la tabla FSE601?
            - ¿Cuál es el modelo entidad-relación?
            """)

    # Área de consulta
    query = st.text_input(
        "🔍 **Escribe tu consulta:**",
        placeholder="Ej: SELECT tabla abonados o cómo usar FOR EACH en GeneXus",
        help="El sistema detectará automáticamente si necesitas SQL o documentación"
    )

    # Configuración avanzada
    with st.expander("⚙️ Configuración Avanzada"):
        col1, col2 = st.columns(2)
        with col1:
            if HAS_SPECIALIZED_AGENTS:
                st.info("🧠 El Director ajusta automáticamente los parámetros por agente")
            top_k = st.slider("📄 Documentos a recuperar", 1, 10, 5)
            min_similarity = st.slider("🎯 Similitud mínima", 0.0, 1.0, 0.1, 0.05)
        with col2:
            show_sources = st.checkbox("📚 Mostrar fuentes", True)
            show_metadata = st.checkbox("📊 Mostrar metadatos", False)
            if HAS_SPECIALIZED_AGENTS:
                show_intent = st.checkbox("🧠 Mostrar análisis de intención", True)

    # Procesar consulta
    if st.button("🚀 Buscar Respuesta", type="primary") or query:
        if not query.strip():
            st.warning("⚠️ Por favor escribe una consulta")
            return

        with st.spinner("🤖 Procesando consulta..."):
            start_time = time.time()

            if HAS_SPECIALIZED_AGENTS:
                # Usar sistema de agentes especializados
                result = director.process_query(query)
                process_time = time.time() - start_time

                # Mostrar información de intención si está habilitado
                if show_intent:
                    st.markdown("### 🧠 Análisis de Intención")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"**Intención:** {result['intent'].title()}")
                    with col2:
                        confidence = result['metadata'].get('intent_confidence', 0)
                        st.markdown(f"**Confianza:** {format_confidence(confidence)}", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"**Agente:** {result['agent_used']}")

                # Mostrar badge del agente
                st.markdown(get_agent_badge(result['intent']), unsafe_allow_html=True)

            else:
                # Usar agente original
                result = agent.query(query)
                process_time = time.time() - start_time

        # Mostrar resultado
        success = result.get('metadata', {}).get('success', True)

        if success:
            # Consulta
            st.markdown(f'<div class="query-box"><strong>🔍 CONSULTA:</strong> {result["query"]}</div>',
                        unsafe_allow_html=True)

            # Respuesta con estilo según el agente
            if HAS_SPECIALIZED_AGENTS:
                intent = result.get('intent', 'unknown')
                if intent == 'sql':
                    answer_class = "sql-answer-box"
                elif intent == 'docs':
                    answer_class = "docs-answer-box"
                else:
                    answer_class = "answer-box"
            else:
                answer_class = "answer-box"

            st.markdown(f'<div class="{answer_class}"><strong>🤖 RESPUESTA:</strong><br><br>{result["answer"]}</div>',
                        unsafe_allow_html=True)

            # Mostrar advertencias para SQL
            if HAS_SPECIALIZED_AGENTS and result.get('raw_result'):
                raw = result['raw_result']
                if isinstance(raw, dict) and raw.get('warnings'):
                    st.markdown("### ⚠️ Advertencias SQL")
                    for warning in raw['warnings']:
                        st.warning(warning)

            # Fuentes
            sources = result.get('sources', [])
            if show_sources and sources:
                st.markdown("### 📚 Fuentes Consultadas")

                for i, source in enumerate(sources, 1):
                    with st.expander(f"📄 Fuente {i} - Similitud: {source.get('similarity', 0):.3f}"):
                        source_info = source.get('source', '')
                        source_name = Path(source_info).name if source.get('type') == 'file' else source_info

                        st.markdown(f"**📁 Fuente:** `{source_name}`")
                        st.markdown(f"**🏷️ Tipo:** {source.get('type', 'N/A')}")
                        st.markdown(f"**🎯 Relevancia:** {source.get('similarity', 0):.3f}")

                        excerpt = source.get('excerpt', '')
                        if excerpt:
                            st.markdown("**📝 Extracto:**")
                            st.markdown(f'<div class="source-box">{excerpt}</div>',
                                        unsafe_allow_html=True)

            # Metadatos
            if show_metadata:
                st.markdown("### 📊 Metadatos de Procesamiento")

                metadata = result.get('metadata', {})
                col1, col2, col3 = st.columns(3)

                with col1:
                    total_time = metadata.get('total_time', metadata.get('routing_time', process_time))
                    st.metric("⏱️ Tiempo Total", f"{total_time:.2f}s")

                with col2:
                    docs_found = metadata.get('documents_found', len(sources))
                    st.metric("📄 Documentos", docs_found)

                with col3:
                    if HAS_SPECIALIZED_AGENTS:
                        agent_used = result.get('agent_used', 'N/A')
                        st.metric("🤖 Agente", agent_used)
                    else:
                        gen_time = metadata.get('generation_metadata', {}).get('generation_time', 0)
                        st.metric("🤖 Generación", f"{gen_time:.2f}s")

                with st.expander("🔧 Detalles Técnicos"):
                    st.json(metadata)

            # Estadísticas de sesión
            if HAS_SPECIALIZED_AGENTS:
                stats = director.get_director_stats()
                director_stats = stats['director']

                st.markdown(f'<div class="stats-box">'
                            f'<strong>📈 Sesión Director:</strong> '
                            f'{director_stats["total_queries"]} consultas | '
                            f'SQL: {director_stats["sql_queries_routed"]} | '
                            f'Docs: {director_stats["docs_queries_routed"]} | '
                            f'Mixtas: {director_stats["mixed_queries"]} | '
                            f'Tiempo promedio: {director_stats["avg_routing_time"]:.2f}s'
                            f'</div>', unsafe_allow_html=True)
            else:
                session_stats = agent.get_session_stats()
                st.markdown(f'<div class="stats-box">'
                            f'<strong>📈 Sesión:</strong> '
                            f'{session_stats["queries_count"]} consultas | '
                            f'Éxito: {session_stats["success_rate"]:.1%} | '
                            f'Tiempo promedio: {session_stats.get("avg_retrieval_time", 0):.2f}s'
                            f'</div>', unsafe_allow_html=True)

        else:
            st.error("❌ Error procesando consulta")
            error_msg = result.get('answer', result.get('error', 'Error desconocido'))
            st.write(error_msg)

            # Mostrar sugerencias si están disponibles
            suggestions = result.get('suggestions', [])
            if suggestions:
                st.markdown("### 💡 Sugerencias")
                for suggestion in suggestions:
                    st.info(suggestion)

    # Footer
    st.markdown("---")
    if HAS_SPECIALIZED_AGENTS:
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8rem;'>
            🎯 Sistema RAG Especializado con Agentes Inteligentes<br>
            🗄️ SQLAgent • 📚 DocsAgent • 🧠 Director Orquestador<br>
            💾 Base de conocimiento actualizada automáticamente
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8rem;'>
            🤖 Sistema RAG desarrollado para consultas sobre Bantotal y GeneXus<br>
            💾 Base de conocimiento actualizada automáticamente
        </div>
        """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
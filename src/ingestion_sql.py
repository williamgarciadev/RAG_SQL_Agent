# src/ingestion_sql.py

"""
Módulo SQL para el sistema de ingesta.
Contiene todas las funciones relacionadas con extracción de metadatos de SQL Server.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

# Configuración SQL desde variables de entorno
SQL_SERVER_HOST = os.getenv('SQL_SERVER_HOST', 'localhost')
SQL_SERVER_PORT = os.getenv('SQL_SERVER_PORT', '1433')
SQL_SERVER_DATABASE = os.getenv('SQL_SERVER_DATABASE', '')
SQL_SERVER_USERNAME = os.getenv('SQL_SERVER_USERNAME', '')
SQL_SERVER_PASSWORD = os.getenv('SQL_SERVER_PASSWORD', '')
SQL_SERVER_DRIVER = os.getenv('SQL_SERVER_DRIVER', 'ODBC Driver 17 for SQL Server')


def _connect_to_sql_server():
    """Crear conexión a SQL Server genérica."""
    try:
        import pyodbc
        from sqlalchemy import create_engine, text
    except ImportError:
        logger.error("❌ Librerías SQL no disponibles. Instala: pip install pyodbc sqlalchemy")
        return None

    if not SQL_SERVER_DATABASE:
        logger.warning("⚠️ SQL_SERVER_DATABASE no configurado en .env")
        return None

    try:
        if SQL_SERVER_USERNAME and SQL_SERVER_PASSWORD:
            connection_string = (
                f"mssql+pyodbc://{SQL_SERVER_USERNAME}:{SQL_SERVER_PASSWORD}@"
                f"{SQL_SERVER_HOST}:{SQL_SERVER_PORT}/{SQL_SERVER_DATABASE}"
                f"?driver={SQL_SERVER_DRIVER.replace(' ', '+')}&TrustServerCertificate=yes"
            )
        else:
            connection_string = (
                f"mssql+pyodbc://{SQL_SERVER_HOST}:{SQL_SERVER_PORT}/{SQL_SERVER_DATABASE}"
                f"?driver={SQL_SERVER_DRIVER.replace(' ', '+')}&trusted_connection=yes&TrustServerCertificate=yes"
            )

        engine = create_engine(connection_string, echo=False)

        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1 as test"))
            result.fetchone()

        logger.info(f"✅ Conexión SQL Server exitosa: {SQL_SERVER_HOST}/{SQL_SERVER_DATABASE}")
        return engine

    except Exception as e:
        logger.error(f"❌ Error conectando a SQL Server: {e}")
        return None


def _extract_database_metadata(engine) -> str:
    """Extraer metadatos genéricos de cualquier base de datos SQL Server."""
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            # Query genérica para obtener información de CUALQUIER base de datos
            tables_query = text("""
                SELECT t.TABLE_SCHEMA,
                       t.TABLE_NAME,
                       t.TABLE_TYPE,
                       COUNT(c.COLUMN_NAME) as TOTAL_COLUMNS
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
                    AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
                WHERE t.TABLE_TYPE = 'BASE TABLE'
                  AND t.TABLE_SCHEMA NOT IN ('sys', 'information_schema')
                GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME, t.TABLE_TYPE
                ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
            """)

            tables_result = conn.execute(tables_query)
            tables = tables_result.fetchall()

            metadata_text = f"""=== METADATOS DE BASE DE DATOS SQL SERVER ===
Host: {SQL_SERVER_HOST}
Base de Datos: {SQL_SERVER_DATABASE}
Total Tablas: {len(tables)}
Fecha Extracción: {datetime.now().isoformat()}

=== ESQUEMAS Y TABLAS ===

"""

            current_schema = None
            for table in tables[:200]:  # Limitar a 200 tablas
                schema, table_name, table_type, column_count = table

                if current_schema != schema:
                    current_schema = schema
                    metadata_text += f"\n--- ESQUEMA: {schema} ---\n"

                metadata_text += f"\nTABLA: {schema}.{table_name}\n"
                metadata_text += f"Tipo: {table_type}\n"
                metadata_text += f"Total Columnas: {column_count}\n\n"

            if len(tables) > 200:
                metadata_text += f"\n... y {len(tables) - 200} tablas adicionales en la base de datos."

        return metadata_text

    except Exception as e:
        logger.error(f"❌ Error extrayendo metadatos SQL: {e}")
        return ""


def _format_database_overview(overview: Dict) -> str:
    """Formatear vista general de la base de datos para ingesta RAG."""
    overview_text = f"""# 📊 Vista General de Base de Datos: {overview['database_name']}

## Resumen Ejecutivo
- **Base de datos:** {overview['database_name']}
- **Total de tablas:** {overview['total_tables']:,}
- **Total de vistas:** {overview['total_views']:,}
- **Esquemas activos:** {overview['total_schemas']}
- **Fecha de extracción:** {overview['generated_at'][:19]}

## 🏗️ Arquitectura por Esquemas

Esta base de datos está organizada en {overview['total_schemas']} esquemas principales:

"""
    
    # Top esquemas
    for schema in overview.get('top_schemas', [])[:10]:
        overview_text += f"### Esquema: {schema['schema']}\n"
        overview_text += f"- **Tablas:** {schema['tables']}\n"
        overview_text += f"- **Descripción:** Esquema con {schema['tables']} tablas del sistema\n\n"
    
    # Tablas más complejas
    overview_text += "## 🧩 Tablas Principales por Complejidad\n\n"
    
    for table in overview.get('most_complex_tables', [])[:15]:
        overview_text += f"- **{table['table']}:** {table['columns']} campos\n"
    
    overview_text += f"""

## 🔍 Guía de Búsqueda de Tablas

Para encontrar información específica sobre tablas en esta base de datos:

1. **Búsqueda por funcionalidad:**
   - Abonados/Clientes: buscar "ABONADO", "CLIENT", "CUSTOMER"
   - Servicios: buscar "SERVIC", "PRODUCT", "PLAN"
   - Facturación: buscar "FACTUR", "BILLING", "INVOICE"
   - Pagos: buscar "PAGO", "PAYMENT", "COBRO"

2. **Consultas SQL recomendadas:**
   ```sql
   -- Buscar tabla específica como Abonados
   SELECT TABLE_NAME, TABLE_SCHEMA 
   FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_NAME LIKE '%ABONADO%' OR TABLE_NAME LIKE '%CLIENT%';
   
   -- Ver estructura de tabla encontrada
   SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
   FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_NAME = 'nombre_tabla_encontrada'
   ORDER BY ORDINAL_POSITION;
   ```

Este documento fue generado automáticamente como parte del sistema RAG.
"""
    
    return overview_text


def _create_table_batches(all_tables: List[Dict], batch_size: int) -> List[List[Dict]]:
    """Crear lotes inteligentes de tablas para procesamiento eficiente."""
    # Ordenar por relevancia y complejidad
    sorted_tables = sorted(all_tables, key=lambda t: (-t['relevance'], -t['column_count']))
    
    # Crear lotes
    batches = []
    for i in range(0, len(sorted_tables), batch_size):
        batch = sorted_tables[i:i + batch_size]
        batches.append(batch)
    
    return batches


def _process_table_batch(explorer, batch_tables: List[Dict], batch_num: int) -> List[Tuple[str, Dict[str, Any]]]:
    """Procesar un lote de tablas de manera eficiente."""
    batch_docs = []
    
    for table_info in batch_tables:
        try:
            table_name = table_info['table_name']
            schema = table_info['schema']
            full_name = table_info['full_name']
            
            # Obtener estructura completa
            structure = explorer.get_table_structure(table_name, schema)
            
            if structure:
                # Generar documentación de la tabla
                table_doc = _format_table_documentation(structure, explorer)
                
                # Metadatos para RAG
                table_metadata = {
                    'source': f"sql_server://{SQL_SERVER_HOST}/{SQL_SERVER_DATABASE}",
                    'source_type': 'database_table',
                    'filename': f"{full_name.replace('.', '_')}_structure.md",
                    'file_type': '.md',
                    'extracted_at': datetime.now().isoformat(),
                    'table_name': table_name,
                    'schema_name': schema,
                    'full_table_name': full_name,
                    'column_count': structure['column_count'],
                    'has_primary_keys': len(structure['primary_keys']) > 0,
                    'has_foreign_keys': len(structure['foreign_keys']) > 0,
                    'batch_number': batch_num,
                    'document_type': 'table_structure'
                }
                
                batch_docs.append((table_doc, table_metadata))
                logger.debug(f"📋 Documentada: {full_name}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error procesando tabla {table_info.get('full_name', 'unknown')}: {e}")
    
    return batch_docs


def _format_table_documentation(structure: Dict, explorer) -> str:
    """Formatear documentación completa de una tabla para RAG."""
    full_name = structure['full_name']
    table_name = structure['table_name']
    schema = structure['schema']
    columns = structure['columns']
    
    # Generar query SELECT optimizado
    select_query = explorer.generate_select_query(table_name, schema, limit=10)
    
    doc_text = f"""# 🗂️ Tabla: {full_name}

## Información General
- **Esquema:** {schema}
- **Nombre de tabla:** {table_name}
- **Nombre completo:** {full_name}
- **Total de campos:** {structure['column_count']}

## 🔑 Claves y Relaciones

"""
    
    # Claves primarias
    if structure['primary_keys']:
        doc_text += f"### Claves Primarias\n"
        for pk in structure['primary_keys']:
            doc_text += f"- `{pk}`\n"
        doc_text += "\n"
    
    # Claves foráneas
    if structure['foreign_keys']:
        doc_text += f"### Claves Foráneas\n"
        for fk in structure['foreign_keys']:
            doc_text += f"- `{fk['column']}` → `{fk['references']}.{fk['ref_column']}`\n"
        doc_text += "\n"
    
    # Estructura detallada
    doc_text += "## 📋 Estructura Completa de Campos\n\n"
    doc_text += "| Pos | Campo | Tipo | Nulos | Clave | Default |\n"
    doc_text += "|-----|-------|------|-------|-------|----------|\n"
    
    for col in columns:
        pos = col['position']
        name = col['name']
        full_type = col['full_type']
        nullable = "✅" if col['nullable'] else "❌"
        key_type = col['key_type'] or ""
        default = col['default'] or ""
        
        doc_text += f"| {pos} | `{name}` | {full_type} | {nullable} | {key_type} | {default} |\n"
    
    # Query de ejemplo
    doc_text += f"\n## 🔍 Query SELECT de Ejemplo\n\n"
    doc_text += f"```sql\n{select_query}\n```\n\n"
    
    # Sugerencias de uso específicas
    doc_text += f"## 💡 Sugerencias de Consulta\n\n"
    
    if structure['primary_keys']:
        pk_list = "`, `".join(structure['primary_keys'])
        doc_text += f"**Búsqueda por clave primaria:**\n"
        doc_text += f"```sql\nSELECT * FROM {full_name} WHERE `{pk_list}` = valor;\n```\n\n"
    
    # Detectar campos comunes y sugerir consultas
    text_fields = [col for col in columns if any(dt in col['data_type'].lower() for dt in ['varchar', 'char', 'text', 'nvarchar'])]
    if text_fields:
        example_field = text_fields[0]['name']
        doc_text += f"**Búsqueda por texto:**\n"
        doc_text += f"```sql\nSELECT * FROM {full_name} WHERE {example_field} LIKE '%texto%';\n```\n\n"
    
    date_fields = [col for col in columns if any(dt in col['data_type'].lower() for dt in ['date', 'time', 'datetime'])]
    if date_fields:
        example_date = date_fields[0]['name']
        doc_text += f"**Filtro por fecha:**\n"
        doc_text += f"```sql\nSELECT * FROM {full_name} WHERE {example_date} >= '2024-01-01';\n```\n\n"
    
    doc_text += f"---\n"
    doc_text += f"*Documentación generada automáticamente para facilitar consultas RAG sobre {full_name}.*"
    
    return doc_text


def _extract_schema_documentation(explorer, top_schemas: List[Dict]) -> List[Tuple[str, Dict[str, Any]]]:
    """Extraer documentación de esquemas principales."""
    schema_docs = []
    
    for schema_info in top_schemas[:5]:  # Solo top 5 esquemas
        schema_name = schema_info['schema']
        table_count = schema_info['tables']
        
        try:
            # Obtener tablas del esquema
            schema_tables = explorer.search_tables(f"", limit=50)
            schema_tables = [t for t in schema_tables if t['schema'] == schema_name]
            
            if schema_tables:
                schema_doc = _format_schema_documentation(schema_name, schema_tables, table_count)
                
                schema_metadata = {
                    'source': f"sql_server://{SQL_SERVER_HOST}/{SQL_SERVER_DATABASE}",
                    'source_type': 'database_schema',
                    'filename': f"schema_{schema_name}_overview.md",
                    'file_type': '.md',
                    'extracted_at': datetime.now().isoformat(),
                    'schema_name': schema_name,
                    'table_count': table_count,
                    'document_type': 'schema_overview'
                }
                
                schema_docs.append((schema_doc, schema_metadata))
                logger.info(f"📁 Esquema documentado: {schema_name} ({table_count} tablas)")
                
        except Exception as e:
            logger.warning(f"⚠️ Error documentando esquema {schema_name}: {e}")
    
    return schema_docs


def _format_schema_documentation(schema_name: str, schema_tables: List[Dict], total_tables: int) -> str:
    """Formatear documentación de un esquema específico."""
    doc_text = f"""# 📁 Esquema: {schema_name}

## Resumen del Esquema
- **Nombre del esquema:** {schema_name}
- **Total de tablas:** {total_tables}
- **Base de datos:** {SQL_SERVER_DATABASE}

## 🗂️ Tablas del Esquema

"""
    
    # Agrupar tablas por complejidad
    complex_tables = [t for t in schema_tables if t['column_count'] > 20]
    medium_tables = [t for t in schema_tables if 10 < t['column_count'] <= 20]
    simple_tables = [t for t in schema_tables if t['column_count'] <= 10]
    
    if complex_tables:
        doc_text += "### 🧩 Tablas Complejas (>20 campos)\n"
        for table in sorted(complex_tables, key=lambda t: -t['column_count'])[:10]:
            doc_text += f"- **{table['table_name']}** - {table['column_count']} campos\n"
        doc_text += "\n"
    
    if medium_tables:
        doc_text += "### 📋 Tablas Intermedias (11-20 campos)\n"
        for table in sorted(medium_tables, key=lambda t: -t['column_count'])[:15]:
            doc_text += f"- **{table['table_name']}** - {table['column_count']} campos\n"
        doc_text += "\n"
    
    if simple_tables:
        doc_text += "### 📝 Tablas Simples (≤10 campos)\n"
        for table in sorted(simple_tables, key=lambda t: t['table_name'])[:20]:
            doc_text += f"- **{table['table_name']}** - {table['column_count']} campos\n"
        doc_text += "\n"
    
    # Queries útiles para el esquema
    doc_text += f"## 🔍 Consultas Útiles\n\n"
    doc_text += f"```sql\n"
    doc_text += f"-- Ver todas las tablas del esquema {schema_name}\n"
    doc_text += f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES\n"
    doc_text += f"WHERE TABLE_SCHEMA = '{schema_name}'\n"
    doc_text += f"ORDER BY TABLE_NAME;\n\n"
    
    doc_text += f"-- Buscar tablas por patrón (ej: Abonados)\n"
    doc_text += f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES\n"
    doc_text += f"WHERE TABLE_SCHEMA = '{schema_name}' \n"
    doc_text += f"  AND TABLE_NAME LIKE '%ABONADO%'\n"
    doc_text += f"ORDER BY TABLE_NAME;\n"
    doc_text += f"```\n\n"
    
    return doc_text


def _basic_sql_extraction() -> List[Tuple[str, Dict[str, Any]]]:
    """Extracción básica de metadatos SQL (fallback)."""
    engine = _connect_to_sql_server()
    if not engine:
        return []

    try:
        metadata_text = _extract_database_metadata(engine)
        if metadata_text:
            metadata_dict = {
                'source': f"sql_server://{SQL_SERVER_HOST}/{SQL_SERVER_DATABASE}",
                'source_type': 'database',
                'filename': f"{SQL_SERVER_DATABASE}_metadata_basic.sql",
                'file_type': '.sql',
                'extracted_at': datetime.now().isoformat(),
                'total_tables': metadata_text.count('TABLA:'),
                'extraction_method': 'basic'
            }

            logger.info(f"✅ Metadatos SQL Server básicos: {metadata_dict['total_tables']} tablas")
            return [(metadata_text, metadata_dict)]

    except Exception as e:
        logger.error(f"❌ Error en extracción básica SQL: {e}")
    finally:
        try:
            engine.dispose()
        except:
            pass

    return []


def _load_from_sql_server_advanced() -> List[Tuple[str, Dict[str, Any]]]:
    """Función principal para carga avanzada usando explorador de BD."""
    try:
        from database_explorer import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        docs = []
        
        # Vista general
        overview = explorer.get_database_overview()
        if overview:
            overview_text = _format_database_overview(overview)
            overview_metadata = {
                'source': f"sql_server://{SQL_SERVER_HOST}/{SQL_SERVER_DATABASE}",
                'source_type': 'database',
                'filename': f"{SQL_SERVER_DATABASE}_overview.md",
                'file_type': '.md',
                'extracted_at': datetime.now().isoformat(),
                'document_type': 'database_overview'
            }
            docs.append((overview_text, overview_metadata))
        
        return docs
        
    except ImportError:
        logger.warning("⚠️ DatabaseExplorer no disponible, usando extracción básica")
        return _basic_sql_extraction()


def test_sql_connection() -> bool:
    """Probar conexión SQL Server."""
    engine = _connect_to_sql_server()
    if not engine:
        return False

    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT COUNT(*) as total_tables FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"))
            total_tables = result.fetchone()[0]

            logger.info(f"✅ Conexión exitosa: {total_tables} tablas en {SQL_SERVER_DATABASE}")
            
            # Buscar tabla Abonados como ejemplo
            tables_result = conn.execute(text("""
                SELECT TABLE_NAME, TABLE_SCHEMA 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE '%ABONADO%' OR TABLE_NAME LIKE '%CLIENT%'
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """))
            
            found_tables = tables_result.fetchall()
            if found_tables:
                logger.info("📋 Tablas relacionadas con Abonados/Clientes encontradas:")
                for table in found_tables:
                    logger.info(f"   • {table[1]}.{table[0]}")
            else:
                logger.info("ℹ️ No se encontraron tablas con patrón 'Abonado' o 'Client'")

        engine.dispose()
        return True

    except Exception as e:
        logger.error(f"❌ Error probando conexión: {e}")
        return False
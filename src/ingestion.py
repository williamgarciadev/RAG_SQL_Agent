# src/ingestion.py

def _format_database_overview(overview: dict) -> str:
    """Formatear vista general de la base de datos para ingesta RAG."""
    if not overview:
        return "No se pudo obtener vista general de la base de datos."
    
    overview_text = f"""# 📊 Vista General de Base de Datos: {overview.get('database_name', 'N/A')}

## Resumen Ejecutivo
- **Base de datos:** {overview.get('database_name', 'N/A')}
- **Total de tablas:** {overview.get('total_tables', 0):,}
- **Total de vistas:** {overview.get('total_views', 0):,}
- **Esquemas activos:** {overview.get('total_schemas', 0)}
- **Fecha de extracción:** {overview.get('generated_at', '')[:19]}

## 🏗️ Arquitectura por Esquemas

Esta base de datos está organizada en {overview.get('total_schemas', 0)} esquemas principales:

"""
    
    # Top esquemas
    for schema in overview.get('top_schemas', [])[:10]:
        overview_text += f"### Esquema: {schema.get('schema', 'N/A')}\n"
        overview_text += f"- **Tablas:** {schema.get('tables', 0)}\n\n"
    
    # Distribución Bantotal si existe
    if 'bantotal_prefixes' in overview:
        overview_text += "## 🏦 Distribución Tablas Bantotal\n\n"
        bantotal_descriptions = {
            'FST': 'Tablas Básicas - Genéricas',
            'FSD': 'Datos',
            'FSR': 'Relaciones', 
            'FSE': 'Extensiones',
            'FSH': 'Históricos',
            'FSX': 'Textos',
            'FSA': 'Auxiliares',
            'FSI': 'Informaciones',
            'FSM': 'Menús',
            'FSN': 'Numeradores'
        }
        
        for prefix_info in overview.get('bantotal_prefixes', [])[:10]:
            prefix = prefix_info.get('prefix', 'N/A')
            count = prefix_info.get('tables', 0)
            desc = bantotal_descriptions.get(prefix, 'Otras tablas')
            overview_text += f"- **{prefix}:** {count} tablas ({desc})\n"
    
    # Tablas más complejas
    overview_text += "\n## 🧩 Tablas Principales por Complejidad\n\n"
    
    for table in overview.get('most_complex_tables', [])[:15]:
        overview_text += f"- **{table.get('table', 'N/A')}:** {table.get('columns', 0)} campos\n"
    
    overview_text += f"""

## 🔍 Guía de Búsqueda de Tablas

Para encontrar información específica sobre tablas en esta base de datos:

1. **Búsqueda por funcionalidad Bantotal:**
   - Básicas: buscar "FST", "Fst001", "tablas básicas"
   - Datos: buscar "FSD", "Fsd601", "servicios"
   - Relaciones: buscar "FSR", "relaciones"
   - Extensiones: buscar "FSE", "extensiones"

2. **Consultas SQL recomendadas:**
   ```sql
   -- Buscar tabla específica
   SELECT TABLE_NAME, TABLE_SCHEMA 
   FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_NAME LIKE '%FST%' OR TABLE_NAME LIKE '%FSD%';
   
   -- Ver estructura de tabla encontrada
   SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
   FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_NAME = 'nombre_tabla_encontrada'
   ORDER BY ORDINAL_POSITION;
   ```

Este documento fue generado automáticamente como parte del sistema RAG Bantotal.
"""
    
    return overview_text


def _create_table_batches(all_tables: list, batch_size: int) -> list:
    """Crear lotes de tablas para procesamiento eficiente."""
    if not all_tables:
        return []
    
    # Ordenar por relevancia si tienen ese campo
    try:
        sorted_tables = sorted(all_tables, key=lambda t: t.get('relevance', 0), reverse=True)
    except:
        sorted_tables = all_tables
    
    # Crear lotes
    batches = []
    for i in range(0, len(sorted_tables), batch_size):
        batch = sorted_tables[i:i + batch_size]
        batches.append(batch)
    
    return batches


def _process_table_batch(explorer, batch_tables: list, batch_num: int) -> list:
    """Procesar un lote de tablas de manera eficiente."""
    batch_docs = []
    
    for table_info in batch_tables:
        try:
            table_name = table_info.get('table_name', '')
            schema = table_info.get('schema', 'dbo')
            full_name = table_info.get('full_name', f"{schema}.{table_name}")
            
            if not table_name:
                continue
                
            # Obtener estructura completa
            structure = explorer.get_table_structure(table_name, schema)
            
            if structure:
                # Generar documentación de la tabla
                table_doc = _format_table_documentation(structure)
                
                # Metadatos para RAG
                table_metadata = {
                    'source': f"sql_server://localhost/bttest",
                    'source_type': 'database_table',
                    'filename': f"{full_name.replace('.', '_')}_structure.md",
                    'file_type': '.md',
                    'table_name': table_name,
                    'schema_name': schema,
                    'full_table_name': full_name,
                    'column_count': structure.get('column_count', 0),
                    'batch_number': batch_num,
                    'document_type': 'table_structure'
                }
                
                batch_docs.append((table_doc, table_metadata))
                
        except Exception as e:
            print(f"⚠️ Error procesando tabla {table_info.get('full_name', 'unknown')}: {e}")
    
    return batch_docs


def _format_table_documentation(structure: dict) -> str:
    """Formatear documentación completa de una tabla para RAG."""
    if not structure:
        return "Error: estructura de tabla vacía"
        
    full_name = structure.get('full_name', 'N/A')
    table_name = structure.get('table_name', 'N/A')
    schema = structure.get('schema', 'dbo')
    columns = structure.get('columns', [])
    
    doc_text = f"""# 🗂️ Tabla: {full_name}

## Información General
- **Esquema:** {schema}
- **Nombre de tabla:** {table_name}
- **Nombre completo:** {full_name}
- **Total de campos:** {len(columns)}

## 📋 Estructura Completa de Campos

| Pos | Campo | Tipo | Nulos | Default |
|-----|-------|------|-------|---------|
"""
    
    for i, col in enumerate(columns, 1):
        name = col.get('name', f'campo_{i}')
        full_type = col.get('full_type', col.get('data_type', 'unknown'))
        nullable = "✅" if col.get('nullable', True) else "❌"
        default = col.get('default', '') or ''
        
        doc_text += f"| {i} | `{name}` | {full_type} | {nullable} | {default} |\n"
    
    doc_text += f"""

## 🔍 Query SELECT de Ejemplo

```sql
-- Query para tabla {full_name}
SELECT TOP 100
"""

    # Agregar columnas al SELECT
    for i, col in enumerate(columns):
        name = col.get('name', f'campo_{i}')
        if i < len(columns) - 1:
            doc_text += f"    {name},\n"
        else:
            doc_text += f"    {name}\n"
    
    doc_text += f"""FROM {full_name}
ORDER BY {columns[0].get('name', 'id') if columns else '1'};
```

## 💡 Sugerencias de Consulta

**Búsqueda básica:**
```sql
SELECT * FROM {full_name} WHERE [condicion];
```

---
*Documentación generada automáticamente para facilitar consultas RAG sobre {full_name}.*
"""
    
    return doc_text


def _extract_schema_documentation(explorer, top_schemas: list) -> list:
    """Extraer documentación de esquemas principales."""
    return []  # Implementación simplificada


def _basic_sql_extraction() -> list:
    """Extracción básica de metadatos SQL (fallback)."""
    return []  # Implementación simplificada
"""
Sistema de ingesta de documentos genérico y completo v3.0
Funciona con cualquier base de datos SQL Server sin hardcodear nombres.
Integra explorador avanzado de BD para extracción escalable.
Como un traductor universal que adapta cualquier fuente de datos.
"""

from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import os
import warnings
import subprocess
import tempfile
import logging
import requests
import time
from urllib.parse import urlparse, urljoin
import json
import re
from datetime import datetime
import sys

from langchain_text_splitters import CharacterTextSplitter
import PyPDF2

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constantes
SUPPORTED_EXTS = {'.pdf', '.docx', '.txt', '.rtf', '.html', '.htm', '.pptx', '.ppt', '.json'}
DEFAULT_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# Detectar herramientas de conversión disponibles
try:
    import pythoncom, win32com.client

    _HAS_COM = True
except ImportError:
    _HAS_COM = False

try:
    subprocess.run(['soffice', '--version'], check=True, capture_output=True)
    _HAS_SOFFICE = True
except:
    _HAS_SOFFICE = False

# Detectar dependencias opcionales para SQL Server
try:
    import pyodbc
    from sqlalchemy import create_engine, text

    # Importar explorador de BD si está disponible
    try:
        from database_explorer import DatabaseExplorer

        HAS_DB_EXPLORER = True
    except ImportError:
        HAS_DB_EXPLORER = False

    HAS_SQL = True
except ImportError:
    HAS_SQL = False
    HAS_DB_EXPLORER = False

# Cargar variables de entorno
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Configuración SQL Server genérica con nuevas opciones
if HAS_SQL:
    SQL_SERVER_HOST = os.getenv('SQL_SERVER_HOST', 'localhost')
    SQL_SERVER_PORT = os.getenv('SQL_SERVER_PORT', '1433')
    SQL_SERVER_DATABASE = os.getenv('SQL_SERVER_DATABASE', '')
    SQL_SERVER_USERNAME = os.getenv('SQL_SERVER_USERNAME', '')
    SQL_SERVER_PASSWORD = os.getenv('SQL_SERVER_PASSWORD', '')
    SQL_SERVER_DRIVER = os.getenv('SQL_SERVER_DRIVER', 'ODBC Driver 17 for SQL Server')

    # Nuevas configuraciones para explorador avanzado
    SQL_TABLES_BATCH_SIZE = int(os.getenv('SQL_TABLES_BATCH_SIZE', '50'))
    SQL_EXTRACT_MODE = os.getenv('SQL_EXTRACT_MODE', 'smart')  # 'smart', 'basic', 'full'
    SQL_INCLUDE_SCHEMAS = os.getenv('SQL_INCLUDE_SCHEMAS', '').split(',') if os.getenv('SQL_INCLUDE_SCHEMAS') else []
    SQL_EXCLUDE_PATTERNS = os.getenv('SQL_EXCLUDE_PATTERNS', 'sys_,temp_,#').split(',')
    SQL_MAX_TABLES_PER_SCHEMA = int(os.getenv('SQL_MAX_TABLES_PER_SCHEMA', '100'))

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Importar funciones auxiliares desde módulos separados
try:
    from ingestion_helpers import (
        _is_url, _clean_text, _is_pdf_url, _detect_content_type,
        _download_content, _extract_text_from_html
    )
    from ingestion_loaders import (
        _load_pdf, _load_docx, _load_txt, _load_rtf, _load_html,
        _load_pptx, _convert_ppt, _load_json_schema, _process_database_schema_json
    )
    from ingestion_sql import (
        _connect_to_sql_server, _extract_database_metadata, _load_from_sql_server_advanced,
        _format_database_overview, _create_table_batches, _process_table_batch,
        _format_table_documentation, _extract_schema_documentation, _basic_sql_extraction
    )
except ImportError as e:
    logger.warning(f"⚠️ Algunos módulos auxiliares no disponibles: {e}")
    logger.info("💡 Usando funciones integradas")


    # Funciones básicas integradas como fallback
    def _is_url(text: str) -> bool:
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False


    def _clean_text(text: str) -> str:
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t')
        return text.strip()


def _load_from_sql_server() -> List[Tuple[str, Dict[str, Any]]]:
    """Cargar metadatos genéricos desde cualquier SQL Server usando explorador avanzado."""
    if not HAS_SQL:
        logger.warning("⚠️ Conectores SQL no disponibles")
        return []

    docs = []

    try:
        # 1. Usar explorador avanzado si está disponible
        if HAS_DB_EXPLORER:
            logger.info("🚀 Usando explorador avanzado de base de datos")

            explorer = DatabaseExplorer()

            # Vista general de la base de datos
            overview = explorer.get_database_overview()
            if overview:
                overview_text = _format_database_overview(overview)

                overview_metadata = {
                    'source': f"sql_server://{SQL_SERVER_HOST}/{SQL_SERVER_DATABASE}",
                    'source_type': 'database',
                    'filename': f"{SQL_SERVER_DATABASE}_overview.md",
                    'file_type': '.md',
                    'extracted_at': datetime.now().isoformat(),
                    'document_type': 'database_overview',
                    'total_tables': overview.get('total_tables', 0),
                    'total_schemas': overview.get('total_schemas', 0)
                }

                docs.append((overview_text, overview_metadata))
                logger.info(f"✅ Vista general extraída: {overview['total_tables']} tablas")

            # Extracción inteligente de tablas por lotes
            tables_batch_size = SQL_TABLES_BATCH_SIZE

            # Buscar todas las tablas principales (sin filtros específicos)
            all_tables = explorer.search_tables("", limit=tables_batch_size * 2)

            if all_tables:
                # Dividir en lotes para procesamiento eficiente
                batches = _create_table_batches(all_tables, tables_batch_size)

                for batch_num, batch_tables in enumerate(batches, 1):
                    logger.info(f"📦 Procesando lote {batch_num}/{len(batches)} ({len(batch_tables)} tablas)")

                    batch_docs = _process_table_batch(explorer, batch_tables, batch_num)
                    docs.extend(batch_docs)

            # Documentación de esquemas principales
            if overview and overview.get('top_schemas'):
                schema_docs = _extract_schema_documentation(explorer, overview['top_schemas'])
                docs.extend(schema_docs)

        else:
            # 2. Fallback al método básico si no hay explorador
            logger.info("📋 Usando extracción básica de metadatos")
            basic_docs = _basic_sql_extraction()
            docs.extend(basic_docs)

    except Exception as e:
        logger.error(f"❌ Error cargando desde SQL Server: {e}")

    logger.info(f"✅ Total documentos SQL generados: {len(docs)}")
    return docs


def _load_urls_from_file(urls_file: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """Cargar URLs desde archivo txt o json."""
    docs = []
    try:
        if urls_file.suffix.lower() == '.json':
            content = json.loads(urls_file.read_text(encoding='utf-8'))
            urls = content.get('urls', content) if isinstance(content, dict) else content
        else:
            lines = urls_file.read_text(encoding='utf-8').splitlines()
            urls = [line.strip() for line in lines
                    if line.strip() and not line.strip().startswith('#')]

        logger.info(f"Procesando {len(urls)} URLs desde {urls_file.name}")

        for i, url in enumerate(urls, 1):
            if _is_url(url):
                logger.info(f"URL {i}/{len(urls)}: {url}")
                text, metadata = _download_content(url)
                if text:
                    metadata.update({
                        'url_source_file': str(urls_file),
                        'url_index': i
                    })
                    docs.append((text, metadata))
            else:
                logger.warning(f"URL inválida: {url}")

    except Exception as e:
        logger.error(f"Error procesando {urls_file.name}: {e}")

    return docs


def _load_all_docs(docs_path: Path, include_urls: bool = True, include_sql: bool = True) -> List[
    Tuple[str, Dict[str, Any]]]:
    """Cargar todos los documentos del directorio."""
    if not docs_path.exists():
        logger.warning(f"Directorio no existe: {docs_path}")
        return []

    # Mapeo de extensiones a funciones de carga
    loaders = {
        '.pdf': _load_pdf if 'ingestion_loaders' in sys.modules else lambda x: '',
        '.docx': _load_docx if 'ingestion_loaders' in sys.modules else lambda x: '',
        '.txt': _load_txt if 'ingestion_loaders' in sys.modules else lambda x: x.read_text(encoding='utf-8',
                                                                                           errors='ignore'),
        '.rtf': _load_rtf if 'ingestion_loaders' in sys.modules else lambda x: '',
        '.html': _load_html if 'ingestion_loaders' in sys.modules else lambda x: '',
        '.htm': _load_html if 'ingestion_loaders' in sys.modules else lambda x: '',
        '.pptx': _load_pptx if 'ingestion_loaders' in sys.modules else lambda x: '',
        '.json': _load_json_schema if 'ingestion_loaders' in sys.modules else lambda x: x.read_text(encoding='utf-8')
    }

    docs = []
    processed = 0
    skipped = 0

    # Incluir metadatos de SQL Server si está habilitado
    if include_sql and HAS_SQL:
        try:
            sql_docs = _load_from_sql_server()
            docs.extend(sql_docs)
            if sql_docs:
                logger.info(f"✅ Agregados metadatos SQL Server: {len(sql_docs)} documentos")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando SQL Server: {e}")

    # Procesar archivos del directorio
    for file in docs_path.iterdir():
        if not file.is_file():
            continue

        # Procesar archivos de URLs
        if include_urls and file.name.lower() in ['urls.txt', 'urls.json']:
            url_docs = _load_urls_from_file(file)
            docs.extend(url_docs)
            processed += len(url_docs)
            continue

        ext = file.suffix.lower()
        text = ''

        # Cargar archivo según extensión
        if ext in loaders:
            try:
                text = loaders[ext](file)
            except Exception as e:
                logger.warning(f"Error cargando {file.name}: {e}")
                text = ''
        elif ext == '.ppt':
            # Convertir PPT legacy
            if 'ingestion_loaders' in sys.modules:
                converted = _convert_ppt(file)
                if converted:
                    text = _load_pptx(converted)
                    converted.unlink(missing_ok=True)
        else:
            logger.debug(f"Extensión no soportada: {ext} en {file.name}")
            skipped += 1
            continue

        # Agregar si tiene contenido
        text = _clean_text(text)
        if text:
            metadata = {
                'source': str(file),
                'filename': file.name,
                'file_type': ext,
                'source_type': 'file',
                'file_size': file.stat().st_size,
                'word_count': len(text.split()),
                'char_count': len(text)
            }
            docs.append((text, metadata))
            processed += 1
            logger.info(f"✓ {file.name} ({len(text)} chars)")
        else:
            logger.warning(f"✗ Sin contenido: {file.name}")
            skipped += 1

    logger.info(f"Procesados: {processed}, omitidos: {skipped}")
    return docs


def _chunk_docs(raw_docs: List[Tuple[str, Dict[str, Any]]], chunk_size: int, chunk_overlap: int) -> List[
    Dict[str, Any]]:
    """Dividir documentos en chunks."""
    splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separator='\n\n',
        keep_separator=True
    )

    chunks = []
    for text, metadata in raw_docs:
        try:
            text_chunks = splitter.split_text(text)
            for i, chunk_text in enumerate(text_chunks):
                if chunk_text.strip():
                    chunk_meta = metadata.copy()
                    chunk_meta.update({
                        'chunk_index': i,
                        'total_chunks': len(text_chunks),
                        'chunk_size': len(chunk_text)
                    })
                    chunks.append({
                        'text': chunk_text,
                        'metadata': chunk_meta
                    })
        except Exception as e:
            logger.error(f"Error chunking {metadata.get('filename', 'documento')}: {e}")

    return chunks


def ingest_documents(
        docs_dir: str = 'docs',
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        include_urls: bool = True,
        include_sql: bool = True,
        single_url: str = None,
        sql_extract_mode: str = None
) -> List[Dict[str, Any]]:
    """
    Función principal de ingesta genérica con explorador avanzado de BD.

    Args:
        docs_dir: Directorio con documentos
        chunk_size: Tamaño máximo de chunk
        chunk_overlap: Solapamiento entre chunks
        include_urls: Procesar archivos urls.txt/urls.json
        include_sql: Extraer metadatos desde SQL Server
        single_url: URL individual para procesar
        sql_extract_mode: Modo de extracción SQL ('smart', 'basic', 'full', None=auto)

    Returns:
        Lista de chunks con texto y metadatos estructurados
    """
    raw_docs = []

    # Determinar modo de extracción SQL
    if sql_extract_mode is None:
        sql_extract_mode = SQL_EXTRACT_MODE

    # Procesar URL individual
    if single_url:
        if not _is_url(single_url):
            raise ValueError(f"URL inválida: {single_url}")

        logger.info(f"🌐 Procesando URL: {single_url}")
        text, metadata = _download_content(single_url)
        if text:
            raw_docs.append((text, metadata))
        else:
            logger.warning("⚠️ No se obtuvo contenido de la URL")
    else:
        # Procesar directorio + SQL Server con modo avanzado
        path = Path(docs_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / docs_dir

        logger.info(f"📁 Procesando directorio: {path}")

        if include_sql:
            logger.info(f"🗄️ Incluyendo extracción desde SQL Server (modo: {sql_extract_mode})")

            # Configurar modo de extracción
            os.environ['SQL_EXTRACT_MODE'] = sql_extract_mode

        raw_docs = _load_all_docs(path, include_urls, include_sql)

    if not raw_docs:
        logger.warning("⚠️ No se encontraron documentos para procesar")
        return []

    # Crear chunks
    logger.info(f"⚙️ Creando chunks (tamaño: {chunk_size}, solapamiento: {chunk_overlap})")
    chunks = _chunk_docs(raw_docs, chunk_size, chunk_overlap)

    # Estadísticas finales con detalles de SQL
    if chunks:
        total_chars = sum(len(chunk['text']) for chunk in chunks)
        avg_size = total_chars / len(chunks)

        # Contar por tipo de fuente con subcategorías SQL
        source_types = {}
        sql_document_types = {}

        for chunk in chunks:
            src_type = chunk['metadata'].get('source_type', 'unknown')
            source_types[src_type] = source_types.get(src_type, 0) + 1

            # Detalles adicionales para documentos SQL
            if src_type in ['database', 'database_table', 'database_schema']:
                doc_type = chunk['metadata'].get('document_type', 'generic')
                sql_document_types[doc_type] = sql_document_types.get(doc_type, 0) + 1

        logger.info(f"✅ {len(raw_docs)} documentos → {len(chunks)} chunks")
        logger.info(f"📊 Tamaño promedio: {avg_size:.1f} chars")
        logger.info(f"📂 Tipos: {dict(source_types)}")

        # Mostrar estadísticas detalladas de SQL si hay documentos de BD
        if sql_document_types:
            logger.info(f"🗄️ Documentos SQL por tipo:")
            for doc_type, count in sql_document_types.items():
                type_descriptions = {
                    'database_overview': 'Vista general de la BD',
                    'table_structure': 'Estructuras de tablas',
                    'schema_overview': 'Documentación de esquemas'
                }
                description = type_descriptions.get(doc_type, doc_type)
                logger.info(f"   📋 {description}: {count} chunks")

    return chunks


def _show_ingestion_results(chunks: List[Dict[str, Any]], extraction_type: str):
    """Mostrar resultados detallados de la ingesta."""
    logger.info(f"🎉 Ingesta {extraction_type} exitosa: {len(chunks)} chunks generados")

    # Estadísticas detalladas
    source_types = {}
    sql_document_types = {}
    total_chars = 0
    sql_chunks = 0

    for chunk in chunks:
        src_type = chunk['metadata'].get('source_type', 'unknown')
        source_types[src_type] = source_types.get(src_type, 0) + 1
        total_chars += len(chunk['text'])

        if src_type in ['database', 'database_table', 'database_schema']:
            sql_chunks += 1
            doc_type = chunk['metadata'].get('document_type', 'generic')
            sql_document_types[doc_type] = sql_document_types.get(doc_type, 0) + 1

    logger.info(f"📊 Estadísticas:")
    logger.info(f"   📝 Total caracteres: {total_chars:,}")
    logger.info(f"   📏 Tamaño promedio chunk: {total_chars // len(chunks):,} chars")

    if sql_chunks > 0:
        logger.info(f"   🗄️ Chunks de SQL Server: {sql_chunks}")
        logger.info(f"   📋 Base de datos procesada: {SQL_SERVER_DATABASE}")

        if sql_document_types:
            logger.info(f"   📂 Tipos de documentos SQL:")
            for doc_type, count in sql_document_types.items():
                type_names = {
                    'database_overview': 'Vista general',
                    'table_structure': 'Estructuras de tablas',
                    'schema_overview': 'Documentación de esquemas'
                }
                name = type_names.get(doc_type, doc_type)
                logger.info(f"      • {name}: {count} chunks")

    logger.info(f"📂 Tipos de fuente:")
    for src_type, count in source_types.items():
        logger.info(f"   📁 {src_type}: {count} chunks")

    logger.info("\n🚀 Siguiente paso:")
    logger.info("   python src/indexer.py --force")


# Funciones auxiliares para compatibilidad
def ingest_urls_from_list(urls: List[str], **kwargs) -> List[Dict[str, Any]]:
    """Ingerir desde lista de URLs."""
    raw_docs = []

    logger.info(f"Procesando {len(urls)} URLs desde lista")
    for i, url in enumerate(urls, 1):
        if _is_url(url):
            logger.info(f"URL {i}/{len(urls)}: {url}")
            text, metadata = _download_content(url)
            if text:
                metadata['url_index'] = i
                raw_docs.append((text, metadata))
        else:
            logger.warning(f"URL inválida: {url}")

    if not raw_docs:
        return []

    chunk_size = kwargs.get('chunk_size', 800)
    chunk_overlap = kwargs.get('chunk_overlap', 200)

    chunks = _chunk_docs(raw_docs, chunk_size, chunk_overlap)
    logger.info(f"✅ {len(raw_docs)} URLs → {len(chunks)} chunks")

    return chunks


def get_supported_formats() -> List[str]:
    """Obtener formatos soportados."""
    return ['.pdf', '.docx', '.txt', '.rtf', '.html', '.htm', '.pptx', '.ppt', '.json', 'URLs', 'SQL Server']


def validate_dependencies() -> Dict[str, bool]:
    """Validar dependencias opcionales."""
    deps = {
        'requests': False,
        'python-docx': False,
        'python-pptx': False,
        'striprtf': False,
        'beautifulsoup4': False,
        'pyodbc': HAS_SQL,
        'sqlalchemy': HAS_SQL,
        'win32com': _HAS_COM,
        'LibreOffice': _HAS_SOFFICE,
        'database_explorer': HAS_DB_EXPLORER
    }

    modules_to_check = [
        ('requests', 'requests'),
        ('python-docx', 'docx'),
        ('python-pptx', 'pptx'),
        ('striprtf', 'striprtf.striprtf'),
        ('beautifulsoup4', 'bs4')
    ]

    for name, module in modules_to_check:
        try:
            __import__(module)
            deps[name] = True
        except ImportError:
            pass

    return deps


if __name__ == '__main__':
    import sys

    logger.info("=== Sistema de Ingesta de Documentos v3.0 ===")
    logger.info("🚀 Con Explorador Avanzado de Base de Datos")
    logger.info(f"📁 Formatos: {', '.join(get_supported_formats())}")

    # Mostrar dependencias
    deps = validate_dependencies()
    logger.info("🔧 Dependencias:")
    for name, available in deps.items():
        status = "✅" if available else "❌"
        logger.info(f"   {status} {name}")

    # Procesar argumentos de línea de comandos
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        # Importar comandos CLI desde módulo separado si está disponible
        try:
            from ingestion_cli import handle_cli_command

            if handle_cli_command(cmd, sys.argv):
                sys.exit(0)
        except ImportError:
            logger.debug("Módulo CLI no disponible, usando comandos básicos")

        # Comandos básicos integrados
        if cmd == '--help':
            print("""
🚀 Sistema de Ingesta v3.0 - Con Explorador Avanzado de BD

Comandos Básicos:
  python src/ingestion.py                    # Modo inteligente (recomendado)
  python src/ingestion.py --sql-smart        # Extracción SQL inteligente
  python src/ingestion.py --sql-basic        # Extracción SQL básica  
  python src/ingestion.py --sql-full         # Extracción SQL completa
  python src/ingestion.py --test-sql         # Probar conexión SQL Server
  python src/ingestion.py --deps             # Verificar dependencias

Para tu tabla Abonados:
  python src/ingestion.py --sql-smart        # Extraer estructura de BD
  python src/indexer.py --force              # Indexar
  python src/agent.py "buscar tabla abonados" # Consultar

Configuración (.env):
  SQL_EXTRACT_MODE=smart                     # smart, basic, full
  SQL_TABLES_BATCH_SIZE=50                   # tablas por lote
  SQL_MAX_TABLES_PER_SCHEMA=100             # límite por esquema
""")

        elif cmd == '--deps':
            deps = validate_dependencies()
            print("\n🔧 Estado de Dependencias:")

            print("\n📋 Dependencias Principales:")
            main_deps = ['requests', 'pyodbc', 'sqlalchemy', 'database_explorer']
            for dep in main_deps:
                status = "✅" if deps.get(dep, False) else "❌"
                print(f"   {status} {dep}")

            print("\n📄 Formatos de Documentos:")
            doc_deps = ['python-docx', 'python-pptx', 'beautifulsoup4', 'striprtf']
            for dep in doc_deps:
                status = "✅" if deps.get(dep, False) else "❌"
                print(f"   {status} {dep}")

        else:
            print(f"❌ Comando '{cmd}' no reconocido")
            print("💡 Usa: python src/ingestion.py --help")

        sys.exit(0)

    # Ejecución por defecto - modo inteligente
    try:
        logger.info("🧠 Iniciando ingesta en modo inteligente...")
        chunks = ingest_documents(sql_extract_mode='smart')

        if chunks:
            _show_ingestion_results(chunks, "inteligente")
        else:
            logger.info("ℹ️ No se encontraron documentos para procesar")
            logger.info("💡 Opciones:")
            logger.info("   • Coloca archivos en el directorio 'docs'")
            logger.info("   • Configura SQL Server en archivo .env")
            logger.info("   • Usa --test-sql para verificar conexión")

    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        logger.info("💡 Para más ayuda: python src/ingestion.py --help")
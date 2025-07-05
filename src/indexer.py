# src/indexer.py

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import os
from dotenv import load_dotenv
import logging
import json
import hashlib
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Importar ChromaDB
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    logger.info("✅ ChromaDB disponible")
except ImportError:
    logger.error("❌ ChromaDB no instalado")
    logger.error("Instala con: pip install chromadb")
    exit(1)


def setup_python_path():
    """Configurar Python path para importaciones."""
    import sys
    import os

    # Agregar directorio actual y padre al path
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent

    paths_to_add = [
        str(current_dir),  # src/
        str(parent_dir),  # raíz del proyecto
        str(parent_dir / 'src')  # src/ desde raíz
    ]

    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)


# Configurar path antes de importaciones
setup_python_path()

# Importar sistema de ingesta
try:
    from ingestion import ingest_documents, SUPPORTED_EXTS, PROJECT_ROOT

    logger.info("✅ Sistema de ingesta disponible")
except ImportError:
    try:
        from src.ingestion import ingest_documents

        logger.info("✅ Sistema de ingesta disponible (src)")
    except ImportError as e:
        logger.error(f"❌ Error importando ingesta: {e}")
        logger.error("📍 Archivo actual: " + str(Path(__file__).resolve()))
        logger.error("📁 Directorio actual: " + str(Path.cwd()))
        logger.error("🔍 Busca ingestion.py en:")
        logger.error(f"   • {Path(__file__).parent / 'ingestion.py'}")
        logger.error(f"   • {Path.cwd() / 'src' / 'ingestion.py'}")
        exit(1)

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    try:
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        logger.warning("⚠️ python-dotenv no instalado, variables de entorno .env no cargadas")
        logger.info("💡 Instala con: pip install python-dotenv")

# Configuración
CHROMA_DB_DIR = os.getenv('CHROMA_DB_DIR', 'chroma_db')
COLLECTION_NAME = os.getenv('CHROMA_COLLECTION', 'documents')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

# Preparar directorio (relativo al proyecto, no al script)
chroma_path = Path(CHROMA_DB_DIR) if Path(CHROMA_DB_DIR).is_absolute() else PROJECT_ROOT / CHROMA_DB_DIR
chroma_path.mkdir(parents=True, exist_ok=True)

# Cliente ChromaDB global
chroma_client = None
chroma_collection = None


def initialize_chroma_client():
    """Inicializar cliente ChromaDB."""
    global chroma_client

    try:
        # Configurar cliente persistente
        chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        logger.info(f"✅ Cliente ChromaDB inicializado en: {chroma_path.resolve()}")
        return True

    except Exception as e:
        logger.error(f"❌ Error inicializando ChromaDB: {e}")
        return False


def get_or_create_collection(force_recreate: bool = False):
    """Obtener o crear colección ChromaDB."""
    global chroma_collection

    if not chroma_client:
        logger.error("❌ Cliente ChromaDB no inicializado")
        return None

    try:
        # Eliminar colección existente si se fuerza recreación
        if force_recreate:
            try:
                chroma_client.delete_collection(name=COLLECTION_NAME)
                logger.info(f"🗑️ Colección '{COLLECTION_NAME}' eliminada")
            except Exception:
                pass  # La colección no existía

        # Intentar obtener colección existente
        try:
            chroma_collection = chroma_client.get_collection(name=COLLECTION_NAME)
            count = chroma_collection.count()
            logger.info(f"📂 Colección existente cargada: '{COLLECTION_NAME}' ({count} documentos)")

        except Exception:
            # Crear nueva colección
            chroma_collection = chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={
                    "hnsw:space": "cosine",
                    "created_at": datetime.now().isoformat()
                }
            )
            logger.info(f"✨ Nueva colección creada: '{COLLECTION_NAME}'")

        return chroma_collection

    except Exception as e:
        logger.error(f"❌ Error con colección ChromaDB: {e}")
        return None


def prepare_documents_for_chroma(chunks: List[Dict[str, Any]]) -> tuple:
    """Preparar documentos para ChromaDB con optimizaciones para documentos grandes."""
    documents = []
    metadatas = []
    ids = []

    logger.info(f"📋 Preparando {len(chunks)} chunks para ChromaDB...")

    for i, chunk in enumerate(chunks):
        # Texto del documento
        text = chunk.get('text', '').strip()
        if not text:
            continue

        # Limitar tamaño de texto para evitar problemas de memoria
        if len(text) > 8000:  # Límite por chunk
            text = text[:8000] + "... [texto truncado]"
            logger.debug(f"Chunk {i} truncado de {len(chunk.get('text', ''))} a 8000 caracteres")

        documents.append(text)

        # Preparar metadatos (solo tipos simples y limitados)
        metadata = chunk.get('metadata', {})
        clean_metadata = {}

        # Campos esenciales solamente
        essential_fields = ['source', 'filename', 'file_type', 'source_type', 'chunk_index', 'page_number']

        for key, value in metadata.items():
            if key in essential_fields and isinstance(value, (str, int, float, bool)):
                # Limitar longitud de strings en metadatos
                if isinstance(value, str) and len(value) > 200:
                    clean_metadata[key] = value[:200] + "..."
                else:
                    clean_metadata[key] = value
            elif key == 'chunk_id':
                clean_metadata[key] = i

        # Agregar metadatos mínimos adicionales
        clean_metadata.update({
            'text_length': len(text),
            'indexed_at': datetime.now().isoformat()[:19]  # Sin microsegundos
        })

        metadatas.append(clean_metadata)
        ids.append(f"doc_{i:07d}")  # IDs con más padding para grandes volúmenes

        # Progreso cada 100 chunks
        if (i + 1) % 100 == 0:
            logger.info(f"📦 Preparados {i + 1}/{len(chunks)} chunks...")

    logger.info(f"✅ {len(documents)} documentos listos para ChromaDB")
    return documents, metadatas, ids


def build_index(
        docs_dir: str = 'docs',
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        include_urls: bool = True,
        single_url: str = None,
        force_rebuild: bool = False,
        check_changes: bool = True
) -> bool:
    """
    Construir índice vectorial usando ChromaDB puro con detección inteligente de cambios.

    Args:
        docs_dir: Directorio con documentos
        chunk_size: Tamaño de chunks
        chunk_overlap: Solapamiento entre chunks
        include_urls: Incluir URLs desde archivos
        single_url: URL individual para procesar
        force_rebuild: Forzar reconstrucción completa
        check_changes: Verificar cambios antes de reconstruir

    Returns:
        True si se construyó exitosamente
    """
    logger.info("🚀 Iniciando construcción de índice vectorial")

    # Inicializar ChromaDB
    if not initialize_chroma_client():
        return False

    # Verificar si necesita reconstrucción
    if check_changes and not single_url:
        should_rebuild, reason = should_rebuild_index(force_rebuild)

        if not should_rebuild:
            logger.info(f"✅ {reason}")
            logger.info("📂 Usando índice existente (sin cambios detectados)")

            # Cargar colección existente
            collection = get_or_create_collection(force_recreate=False)
            if collection:
                count = collection.count()
                logger.info(f"📊 Índice actual: {count} documentos")
                return True
            else:
                logger.warning("⚠️ Error cargando índice existente, reconstruyendo...")
                should_rebuild = True
                reason = "Error accediendo índice existente"

        if should_rebuild:
            logger.info(f"🔄 Reconstrucción necesaria: {reason}")

            # Mostrar detalles de cambios si no es forzado
            if not force_rebuild:
                changes = get_source_changes(docs_dir)
                if changes['files_added']:
                    logger.info(f"  ➕ Archivos nuevos: {len(changes['files_added'])}")
                    for file in changes['files_added'][:3]:  # Mostrar solo los primeros 3
                        logger.info(f"     • {Path(file).name}")
                    if len(changes['files_added']) > 3:
                        logger.info(f"     • ... y {len(changes['files_added']) - 3} más")

                if changes['files_modified']:
                    logger.info(f"  🔄 Archivos modificados: {len(changes['files_modified'])}")
                    for file in changes['files_modified'][:3]:
                        logger.info(f"     • {Path(file).name}")
                    if len(changes['files_modified']) > 3:
                        logger.info(f"     • ... y {len(changes['files_modified']) - 3} más")

                if changes['files_deleted']:
                    logger.info(f"  ➖ Archivos eliminados: {len(changes['files_deleted'])}")
                    for file in changes['files_deleted'][:3]:
                        logger.info(f"     • {Path(file).name}")

                if changes['urls_file_modified']:
                    logger.info(f"  🌐 Archivo urls.txt modificado")

    # Obtener/crear colección (recrear si necesario)
    collection = get_or_create_collection(
        force_recreate=should_rebuild if 'should_rebuild' in locals() else force_rebuild)
    if not collection:
        return False

    # Ingerir documentos
    logger.info("📥 Ingiriendo documentos...")
    chunks = ingest_documents(
        docs_dir=docs_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        include_urls=include_urls,
        single_url=single_url
    )

    if not chunks:
        logger.warning("⚠️ No se generaron chunks para indexar")
        return False

    logger.info(f"📄 Procesados {len(chunks)} chunks para indexación")

    # Preparar documentos para ChromaDB
    documents, metadatas, ids = prepare_documents_for_chroma(chunks)

    if not documents:
        logger.warning("⚠️ No hay documentos válidos para indexar")
        return False

    # Añadir documentos a ChromaDB en lotes
    try:
        batch_size = 100
        total_added = 0

        logger.info("💾 Indexando documentos en ChromaDB...")

        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            batch_docs = documents[i:end_idx]
            batch_metas = metadatas[i:end_idx]
            batch_ids = ids[i:end_idx]

            # Añadir lote a ChromaDB
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )

            total_added += len(batch_docs)
            logger.info(f"📦 Lote {i // batch_size + 1}: {len(batch_docs)} docs (Total: {total_added})")

        # Verificar conteo final
        final_count = collection.count()
        logger.info(f"✅ Indexación completada: {final_count} documentos en ChromaDB")

        # Guardar metadatos del índice con signatures
        save_index_metadata(final_count, chunks)

        return True

    except Exception as e:
        logger.error(f"❌ Error durante indexación: {e}")
        return False


def search_index(
        query: str,
        top_k: int = 5,
        filter_metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Buscar en el índice vectorial.

    Args:
        query: Texto de consulta
        top_k: Número de resultados
        filter_metadata: Filtros de metadatos (opcional)

    Returns:
        Lista de resultados con texto, metadatos y puntuaciones
    """
    if not chroma_client:
        if not initialize_chroma_client():
            return []

    try:
        # Obtener colección
        collection = chroma_client.get_collection(name=COLLECTION_NAME)

        logger.info(f"🔍 Buscando: '{query}' (top {top_k})")

        # Preparar parámetros de búsqueda
        search_params = {
            'query_texts': [query],
            'n_results': min(top_k, collection.count())
        }

        # Agregar filtros si se especifican
        if filter_metadata:
            search_params['where'] = filter_metadata

        # Realizar búsqueda
        results = collection.query(**search_params)

        # Formatear resultados
        formatted_results = []

        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                # Calcular similitud desde distancia
                distance = results['distances'][0][i] if results.get('distances') else 0
                similarity = max(0, 1 - distance) if distance <= 1 else 1 / (1 + distance)

                result = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                    'id': results['ids'][0][i],
                    'distance': distance,
                    'similarity': similarity,
                    'rank': i + 1
                }
                formatted_results.append(result)

        logger.info(f"📋 Encontrados {len(formatted_results)} resultados")
        return formatted_results

    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        return []


def calculate_content_hash(chunks: List[Dict[str, Any]]) -> str:
    """Calcular hash del contenido para detectar cambios."""
    # Crear string único basado en fuentes y timestamps
    content_signatures = []

    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        source = metadata.get('source', '')

        # Para archivos locales, usar timestamp de modificación
        if metadata.get('source_type') == 'file':
            try:
                file_path = Path(source)
                if file_path.exists():
                    mtime = file_path.stat().st_mtime
                    size = file_path.stat().st_size
                    signature = f"{source}:{mtime}:{size}"
                else:
                    signature = f"{source}:deleted"
            except:
                signature = f"{source}:error"

        # Para URLs, usar timestamp de descarga y tamaño
        elif metadata.get('source_type') == 'web':
            download_time = metadata.get('download_timestamp', 0)
            content_length = metadata.get('content_length', 0)
            signature = f"{source}:{download_time}:{content_length}"

        else:
            signature = f"{source}:unknown"

        content_signatures.append(signature)

    # Crear hash MD5 de todas las signatures
    combined = '\n'.join(sorted(content_signatures))
    return hashlib.md5(combined.encode('utf-8')).hexdigest()


def get_source_changes(docs_dir: str = 'docs') -> Dict[str, Any]:
    """Detectar cambios en archivos y URLs."""
    changes = {
        'files_added': [],
        'files_modified': [],
        'files_deleted': [],
        'urls_file_modified': False,
        'has_changes': False
    }

    # Cargar metadatos anteriores si existen
    metadata_path = chroma_path / 'index_metadata.json'
    previous_files = {}
    previous_urls_hash = None

    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            previous_files = metadata.get('file_signatures', {})
            previous_urls_hash = metadata.get('urls_file_hash')
        except:
            pass

    # Verificar archivos en directorio
    docs_path = Path(docs_dir) if Path(docs_dir).is_absolute() else PROJECT_ROOT / docs_dir
    current_files = {}

    if docs_path.exists():
        for file in docs_path.iterdir():
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTS:
                try:
                    mtime = file.stat().st_mtime
                    size = file.stat().st_size
                    signature = f"{mtime}:{size}"
                    current_files[str(file)] = signature

                    # Verificar si es nuevo o modificado
                    if str(file) not in previous_files:
                        changes['files_added'].append(str(file))
                    elif previous_files[str(file)] != signature:
                        changes['files_modified'].append(str(file))

                except Exception as e:
                    logger.warning(f"Error verificando archivo {file}: {e}")

    # Detectar archivos eliminados
    for prev_file in previous_files:
        if prev_file not in current_files:
            changes['files_deleted'].append(prev_file)

    # Verificar archivo de URLs
    urls_file = docs_path / 'urls.txt' if docs_path.exists() else None
    if urls_file and urls_file.exists():
        try:
            urls_content = urls_file.read_text(encoding='utf-8')
            current_urls_hash = hashlib.md5(urls_content.encode('utf-8')).hexdigest()

            if previous_urls_hash != current_urls_hash:
                changes['urls_file_modified'] = True
        except Exception as e:
            logger.warning(f"Error verificando urls.txt: {e}")

    # Determinar si hay cambios significativos
    changes['has_changes'] = bool(
        changes['files_added'] or
        changes['files_modified'] or
        changes['files_deleted'] or
        changes['urls_file_modified']
    )

    return changes


def should_rebuild_index(force_rebuild: bool = False) -> Tuple[bool, str]:
    """
    Determinar si se debe reconstruir el índice.
    Retorna (should_rebuild, reason).
    """
    if force_rebuild:
        return True, "Reconstrucción forzada por usuario"

    # Verificar si existe índice
    metadata_path = chroma_path / 'index_metadata.json'
    if not metadata_path.exists():
        return True, "No existe índice previo"

    try:
        # Verificar si existe colección en ChromaDB
        if not chroma_client:
            initialize_chroma_client()

        if chroma_client:
            try:
                collection = chroma_client.get_collection(name=COLLECTION_NAME)
                if collection.count() == 0:
                    return True, "Colección ChromaDB vacía"
            except:
                return True, "Colección ChromaDB no existe"
    except:
        return True, "Error accediendo a ChromaDB"

    # Detectar cambios en archivos
    changes = get_source_changes()

    if changes['has_changes']:
        reasons = []
        if changes['files_added']:
            reasons.append(f"{len(changes['files_added'])} archivos nuevos")
        if changes['files_modified']:
            reasons.append(f"{len(changes['files_modified'])} archivos modificados")
        if changes['files_deleted']:
            reasons.append(f"{len(changes['files_deleted'])} archivos eliminados")
        if changes['urls_file_modified']:
            reasons.append("archivo urls.txt modificado")

        return True, "Cambios detectados: " + ", ".join(reasons)

    return False, "No hay cambios desde última indexación"


def save_index_metadata(doc_count: int, chunks: List[Dict[str, Any]]):
    """Guardar metadatos del índice con signatures para detección de cambios."""
    # Calcular estadísticas
    source_stats = {}
    total_chars = 0
    file_signatures = {}

    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        source_type = metadata.get('source_type', 'unknown')
        source_stats[source_type] = source_stats.get(source_type, 0) + 1
        total_chars += len(chunk.get('text', ''))

        # Guardar signature de archivos para detección de cambios
        source = metadata.get('source', '')
        if metadata.get('source_type') == 'file':
            try:
                file_path = Path(source)
                if file_path.exists():
                    mtime = file_path.stat().st_mtime
                    size = file_path.stat().st_size
                    file_signatures[source] = f"{mtime}:{size}"
            except:
                pass

    # Hash del archivo urls.txt si existe
    urls_file_hash = None
    docs_path = PROJECT_ROOT / 'docs'
    urls_file = docs_path / 'urls.txt'
    if urls_file.exists():
        try:
            urls_content = urls_file.read_text(encoding='utf-8')
            urls_file_hash = hashlib.md5(urls_content.encode('utf-8')).hexdigest()
        except:
            pass

    # Crear metadatos completos
    index_metadata = {
        'created_at': datetime.now().isoformat(),
        'document_count': doc_count,
        'collection_name': COLLECTION_NAME,
        'embedding_model': EMBEDDING_MODEL,
        'chroma_db_path': str(chroma_path.resolve()),
        'source_statistics': source_stats,
        'total_characters': total_chars,
        'average_chunk_size': total_chars / doc_count if doc_count > 0 else 0,
        'content_hash': calculate_content_hash(chunks),
        'file_signatures': file_signatures,
        'urls_file_hash': urls_file_hash,
        'version': '2.0'
    }

    # Guardar en archivo JSON
    metadata_path = chroma_path / 'index_metadata.json'
    metadata_path.write_text(
        json.dumps(index_metadata, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    logger.info(f"💾 Metadatos con signatures guardados: {metadata_path}")


def get_index_info() -> Dict[str, Any]:
    """Obtener información completa del índice."""
    metadata_path = chroma_path / 'index_metadata.json'

    # Información básica
    info = {
        'exists': False,
        'path': str(chroma_path.resolve()),
        'collection_name': COLLECTION_NAME
    }

    # Cargar metadatos si existen
    if metadata_path.exists():
        try:
            stored_metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            info.update(stored_metadata)
            info['exists'] = True
        except Exception as e:
            info['metadata_error'] = str(e)

    # Información en vivo de ChromaDB
    try:
        if not chroma_client:
            initialize_chroma_client()

        if chroma_client:
            collection = chroma_client.get_collection(name=COLLECTION_NAME)
            info['live_count'] = collection.count()
            info['chroma_available'] = True
    except Exception as e:
        info['chroma_error'] = str(e)
        info['chroma_available'] = False

    return info


def delete_index():
    """Eliminar índice completamente."""
    try:
        # Eliminar colección de ChromaDB
        if not chroma_client:
            initialize_chroma_client()

        if chroma_client:
            try:
                chroma_client.delete_collection(name=COLLECTION_NAME)
                logger.info(f"🗑️ Colección '{COLLECTION_NAME}' eliminada de ChromaDB")
            except Exception:
                logger.info("ℹ️ Colección no existía en ChromaDB")

        # Eliminar directorio completo
        if chroma_path.exists():
            import shutil
            shutil.rmtree(chroma_path)
            logger.info(f"🗑️ Directorio eliminado: {chroma_path}")
        else:
            logger.info("ℹ️ Directorio no existe")

    except Exception as e:
        logger.error(f"❌ Error eliminando índice: {e}")


def main():
    """Función principal con CLI."""
    import sys

    logger.info("=== Indexador Vectorial ChromaDB ===")
    logger.info(f"📁 Base de datos: {chroma_path.resolve()}")
    logger.info(f"📦 Colección: {COLLECTION_NAME}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == '--info':
            info = get_index_info()
            print("\n📊 Información del Índice:")
            print(json.dumps(info, indent=2, ensure_ascii=False))
            return

        elif cmd == '--check':
            logger.info("🔍 Verificando cambios en documentos...")
            changes = get_source_changes()

            print("\n📊 Estado de Cambios:")
            print(f"Archivos nuevos: {len(changes['files_added'])}")
            print(f"Archivos modificados: {len(changes['files_modified'])}")
            print(f"Archivos eliminados: {len(changes['files_deleted'])}")
            print(f"URLs modificadas: {'Sí' if changes['urls_file_modified'] else 'No'}")
            print(f"Requiere reconstrucción: {'Sí' if changes['has_changes'] else 'No'}")

            if changes['files_added']:
                print(f"\n➕ Archivos nuevos ({len(changes['files_added'])}):")
                for file in changes['files_added']:
                    print(f"  • {Path(file).name}")

            if changes['files_modified']:
                print(f"\n🔄 Archivos modificados ({len(changes['files_modified'])}):")
                for file in changes['files_modified']:
                    print(f"  • {Path(file).name}")

            if changes['files_deleted']:
                print(f"\n➖ Archivos eliminados ({len(changes['files_deleted'])}):")
                for file in changes['files_deleted']:
                    print(f"  • {Path(file).name}")

            should_rebuild, reason = should_rebuild_index()
            print(f"\n🤖 Recomendación: {reason}")
            return

        elif cmd == '--force':
            logger.info("⚡ Forzando reconstrucción completa...")
            success = build_index(force_rebuild=True, check_changes=False)
            if success:
                logger.info("✅ Índice reconstruido forzadamente")
            else:
                logger.error("❌ Error en reconstrucción forzada")
            return

        elif cmd == '--delete':
            confirm = input("⚠️ ¿Eliminar índice completo? (y/N): ")
            if confirm.lower() in ['y', 'yes', 's', 'si']:
                delete_index()
            else:
                logger.info("Operación cancelada")
            return

        elif cmd == '--search' and len(sys.argv) > 2:
            query_text = ' '.join(sys.argv[2:])
            results = search_index(query_text, top_k=5)

            if results:
                print(f"\n🔍 Resultados para: '{query_text}'\n")
                for result in results:
                    print(f"--- Resultado {result['rank']} (Similitud: {result['similarity']:.3f}) ---")
                    print(f"Texto: {result['text'][:300]}...")
                    print(f"Fuente: {result['metadata'].get('source', 'Desconocida')}")
                    print(f"Tipo: {result['metadata'].get('source_type', 'N/A')}")
                    print(f"ID: {result['id']}")
                    print()
            else:
                print("❌ No se encontraron resultados")
            return

        elif cmd == '--help':
            print("""
🔧 Indexador Vectorial - Comandos Disponibles:

Construcción Inteligente:
  python src/indexer.py                    # Auto-detectar cambios y actualizar
  python src/indexer.py --check            # Solo verificar cambios (no indexar)
  python src/indexer.py --force            # Forzar reconstrucción completa

Información:
  python src/indexer.py --info             # Mostrar información del índice

Búsqueda:
  python src/indexer.py --search <consulta> # Buscar en el índice

Gestión:
  python src/indexer.py --delete           # Eliminar índice completo
  python src/indexer.py --help             # Mostrar esta ayuda

🧠 Detección Automática de Cambios:
  • Detecta archivos nuevos, modificados o eliminados
  • Monitorea cambios en urls.txt
  • Solo re-indexa cuando es necesario
  • Usa timestamps y tamaños de archivo para detectar cambios

📋 Ejemplos:
  python src/indexer.py --check            # Ver qué ha cambiado
  python src/indexer.py                    # Actualizar solo si hay cambios
  python src/indexer.py --search "comando for each"
  python src/indexer.py --force            # Reconstruir todo desde cero
""")
            return

    # Construcción por defecto
    logger.info("🏗️ Iniciando construcción de índice...")

    try:
        success = build_index()

        if success:
            logger.info("🎉 ¡Indexación completada exitosamente!")

            # Mostrar estadísticas
            info = get_index_info()
            logger.info(f"📊 Documentos indexados: {info.get('live_count', 'N/A')}")
            logger.info(f"🔗 Tipos de fuente: {info.get('source_statistics', {})}")
            logger.info(f"📝 Caracteres totales: {info.get('total_characters', 'N/A'):,}")

            print("\n💡 Comandos útiles:")
            print("  python src/indexer.py --search 'tu consulta'")
            print("  python src/indexer.py --info")

        else:
            logger.error("❌ Error en la indexación")
            logger.info("💡 Verifica que tengas documentos en el directorio 'docs'")
            logger.info("💡 O prueba: python src/indexer.py --help")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Operación cancelada por el usuario")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")


if __name__ == '__main__':
    main()
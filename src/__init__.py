# src/__init__.py

"""
Paquete de herramientas RAG para análisis de documentos y búsqueda semántica.

Módulos disponibles:
- ingestion: Sistema de ingesta de documentos (PDF, DOCX, URLs, etc.)
- indexer: Indexador vectorial con ChromaDB para búsqueda semántica
"""

__version__ = "2.0.0"
__author__ = "RAG SQL Agent"

# Importaciones opcionales para facilitar el uso
try:
    from .ingestion import ingest_documents
    from .indexer import build_index, search_index

    __all__ = [
        'ingest_documents',
        'build_index',
        'search_index'
    ]
except ImportError:
    # En caso de dependencias faltantes, solo exponer versión
    __all__ = ['__version__']
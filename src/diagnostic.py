# src/diagnostic.py

"""
Script de diagnóstico para verificar el entorno y dependencias.
Ejecutar si hay problemas con imports o configuración.
"""

import sys
import os
from pathlib import Path


def diagnose_environment():
    """Diagnóstico completo del entorno."""
    print("🔍 === DIAGNÓSTICO DEL ENTORNO RAG ===\n")

    # 1. Información de Python
    print("🐍 Python:")
    print(f"   Versión: {sys.version}")
    print(f"   Ejecutable: {sys.executable}")
    print(f"   Plataforma: {sys.platform}")

    # 2. Directorio actual
    print(f"\n📁 Directorios:")
    print(f"   Actual: {Path.cwd()}")
    print(f"   Script: {Path(__file__).parent}")
    print(f"   Padre: {Path(__file__).parent.parent}")

    # 3. Python Path
    print(f"\n🛤️ Python Path:")
    for i, path in enumerate(sys.path[:5], 1):
        print(f"   {i}. {path}")
    if len(sys.path) > 5:
        print(f"   ... y {len(sys.path) - 5} más")

    # 4. Verificar archivos clave
    print(f"\n📄 Archivos clave:")

    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent

    files_to_check = [
        current_dir / "ingestion.py",
        current_dir / "indexer.py",
        current_dir / "__init__.py",
        parent_dir / "src" / "ingestion.py",
        parent_dir / "src" / "indexer.py",
        parent_dir / ".env"
    ]

    for file_path in files_to_check:
        exists = "✅" if file_path.exists() else "❌"
        print(f"   {exists} {file_path}")

    # 5. Verificar dependencias
    print(f"\n📦 Dependencias:")

    dependencies = [
        "chromadb",
        "requests",
        "python-dotenv",
        "PyPDF2",
        "python-pptx",
        "beautifulsoup4",
        "striprtf"
    ]

    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} (pip install {dep})")

    # 6. Probar importaciones locales
    print(f"\n🔗 Importaciones locales:")

    # Agregar paths
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(parent_dir))

    try:
        from ingestion import ingest_documents
        print(f"   ✅ from ingestion import ingest_documents")
    except ImportError as e:
        print(f"   ❌ from ingestion import ingest_documents: {e}")

    try:
        from src.ingestion import ingest_documents
        print(f"   ✅ from src.ingestion import ingest_documents")
    except ImportError as e:
        print(f"   ❌ from src.ingestion import ingest_documents: {e}")

    # 7. Verificar ChromaDB
    print(f"\n💾 ChromaDB:")
    try:
        import chromadb
        client = chromadb.Client()
        print(f"   ✅ ChromaDB funcional")
        print(f"   📊 Versión: {chromadb.__version__}")
    except Exception as e:
        print(f"   ❌ Error con ChromaDB: {e}")

    # 8. Directorio docs
    print(f"\n📚 Directorio de documentos:")
    docs_dir = parent_dir / "docs"
    if docs_dir.exists():
        files = list(docs_dir.glob("*"))
        print(f"   ✅ {docs_dir} ({len(files)} archivos)")

        # Mostrar algunos archivos
        for file in files[:5]:
            print(f"      • {file.name}")
        if len(files) > 5:
            print(f"      • ... y {len(files) - 5} más")
    else:
        print(f"   ❌ {docs_dir} no existe")

    print(f"\n🎯 === RECOMENDACIONES ===")

    # Directorio actual correcto
    if Path.cwd().name != "RAG_SQL_Agent":
        print(f"💡 Ejecuta desde el directorio raíz del proyecto:")
        print(f"   cd {parent_dir}")

    # Comando correcto
    print(f"💡 Comandos recomendados:")
    print(f"   python src/indexer.py --check")
    print(f"   python src/indexer.py")

    # Virtual env
    if "venv" not in sys.executable and ".venv" not in sys.executable:
        print(f"⚠️  No pareces estar en un entorno virtual")
        print(f"   Activa el venv: .venv\\Scripts\\activate")


if __name__ == "__main__":
    diagnose_environment()
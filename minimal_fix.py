# minimal_fix.py - Ajuste mínimo para el error sys

from pathlib import Path
import re

def fix_sys_import_minimal():
    """Agregar import sys de forma mínima al archivo ingestion.py"""
    
    ingestion_file = Path('src/ingestion.py')
    
    if not ingestion_file.exists():
        print("❌ src/ingestion.py no encontrado")
        return False
    
    print("🔧 Aplicando ajuste mínimo para import sys...")
    
    # Leer contenido
    content = ingestion_file.read_text(encoding='utf-8')
    
    # Verificar si ya tiene import sys
    if 'import sys' in content:
        print("✅ import sys ya existe")
        return True
    
    # Buscar la línea específica donde agregar import sys
    lines = content.split('\n')
    new_lines = []
    sys_added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Agregar import sys después de los imports de datetime 
        # (justo antes de las importaciones de langchain_text_splitters)
        if 'from datetime import datetime' in line and not sys_added:
            new_lines.append('import sys')
            sys_added = True
    
    if not sys_added:
        # Si no encontró el lugar específico, agregarlo después de los imports principales
        for i, line in enumerate(lines):
            if 'from langchain_text_splitters import CharacterTextSplitter' in line:
                lines.insert(i, 'import sys')
                new_lines = lines
                sys_added = True
                break
    
    if sys_added:
        # Guardar archivo
        new_content = '\n'.join(new_lines)
        
        # Crear backup
        backup_file = ingestion_file.with_suffix('.py.backup')
        backup_file.write_text(content, encoding='utf-8')
        print(f"📋 Backup creado: {backup_file}")
        
        # Escribir archivo corregido
        ingestion_file.write_text(new_content, encoding='utf-8')
        print("✅ import sys agregado correctamente")
        return True
    else:
        print("❌ No se pudo encontrar lugar apropiado para agregar import sys")
        return False

def test_fix():
    """Probar que el fix funciona"""
    print("\n🧪 Probando corrección...")
    
    try:
        import sys
        sys.path.append('src')
        
        # Recargar módulo si ya estaba cargado
        if 'ingestion' in sys.modules:
            import importlib
            importlib.reload(sys.modules['ingestion'])
        
        from src.ingestion import ingest_documents
        print("✅ ingestion.py se importa sin errores")
        
        # Probar función básica (sin SQL para evitar dependencias)
        chunks = ingest_documents(
            docs_dir='docs',
            include_sql=False,
            chunk_size=800,
            chunk_overlap=200
        )
        
        print(f"✅ ingest_documents funciona: {len(chunks)} chunks generados")
        
        if len(chunks) > 0:
            print(f"📄 Primer chunk preview: {chunks[0]['text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error persistente: {e}")
        import traceback
        print("📋 Traceback completo:")
        traceback.print_exc()
        return False

def create_minimal_docs():
    """Crear documentos mínimos para probar el sistema"""
    print("\n📄 Creando documentos de prueba...")
    
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    
    # Documento simple sobre FSD601
    fsd601_doc = docs_dir / 'tabla_fsd601.txt'
    fsd601_content = """Tabla FSD601 - Servicios Financieros

Esta tabla contiene información sobre los servicios financieros del banco.

Campos principales:
- FSD601ID: Identificador único del servicio
- FSD601CODIGO: Código del servicio
- FSD601NOMBRE: Nombre descriptivo del servicio
- FSD601TIPO: Tipo de servicio (CC=Cuenta Corriente, CA=Caja Ahorro)
- FSD601ESTADO: Estado del servicio (A=Activo, I=Inactivo)
- FSD601FECHA: Fecha de creación del servicio

Consulta SQL típica:
SELECT FSD601ID, FSD601CODIGO, FSD601NOMBRE, FSD601TIPO, FSD601ESTADO
FROM dbo.FSD601 
WHERE FSD601ESTADO = 'A'
ORDER BY FSD601NOMBRE

Este servicio es fundamental para la gestión de productos bancarios.
"""
    
    # Documento GeneXus básico
    genexus_doc = docs_dir / 'genexus_basico.txt'
    genexus_content = """Manual GeneXus - Comandos Básicos

FOR EACH es uno de los comandos más importantes en GeneXus.

Sintaxis básica:
FOR EACH tabla
  WHERE condicion
    // acciones
ENDFOR

Ejemplo para tabla FSD601:
FOR EACH FSD601
  WHERE FSD601Estado = 'A'
    &codigo = FSD601Codigo
    &nombre = FSD601Nombre
ENDFOR

Best practices:
1. Siempre usar WHERE para filtrar
2. Indexar campos de búsqueda
3. Usar variables tipadas
4. Manejar excepciones apropiadamente
"""
    
    try:
        fsd601_doc.write_text(fsd601_content, encoding='utf-8')
        genexus_doc.write_text(genexus_content, encoding='utf-8')
        
        print(f"✅ Documentos creados:")
        print(f"   📄 {fsd601_doc}")
        print(f"   📄 {genexus_doc}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando documentos: {e}")
        return False

def main():
    """Ejecutar ajuste mínimo"""
    print("🔧 AJUSTE MÍNIMO PARA SISTEMA RAG")
    print("=" * 40)
    
    success_count = 0
    
    # 1. Fix import sys
    if fix_sys_import_minimal():
        success_count += 1
    
    # 2. Crear docs mínimos
    if create_minimal_docs():
        success_count += 1
    
    # 3. Probar sistema
    if test_fix():
        success_count += 1
    
    print(f"\n📊 RESULTADO:")
    print(f"   Correcciones exitosas: {success_count}/3")
    
    if success_count >= 2:
        print(f"\n🎉 ¡Listo para continuar!")
        print(f"💡 Próximo paso:")
        print(f"   python src/indexer.py --force")
    else:
        print(f"\n⚠️ Requiere ajustes manuales")

if __name__ == "__main__":
    main()
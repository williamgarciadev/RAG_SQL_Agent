#!/usr/bin/env python3
"""
Diagnóstico Rápido del Sistema RAG
Identifica y resuelve problemas comunes.
"""

import sys
from pathlib import Path

# Configurar paths
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_chroma_index():
    """Verificar estado del índice ChromaDB."""
    print_header("ESTADO DEL ÍNDICE CHROMADB")
    
    try:
        from indexer import get_index_info, search_index
        
        # Información general
        info = get_index_info()
        if info.get('exists'):
            print(f"✅ Índice existe: {info.get('live_count', 0)} documentos")
            print(f"📊 Tipos de fuente: {info.get('source_statistics', {})}")
        else:
            print("❌ Índice no existe")
            return False
        
        # Probar búsqueda simple
        print(f"\n🔍 Probando búsqueda simple...")
        try:
            results = search_index("tabla", top_k=3)
            print(f"✅ Búsqueda funcional: {len(results)} resultados")
            
            if results:
                print(f"\n📋 Primeros resultados:")
                for i, result in enumerate(results[:3], 1):
                    metadata = result.get('metadata', {})
                    source = metadata.get('source', 'N/A')
                    source_type = metadata.get('source_type', 'N/A')
                    similarity = result.get('similarity', 0)
                    
                    print(f"   {i}. Fuente: {Path(source).name if source != 'N/A' else 'N/A'}")
                    print(f"      Tipo: {source_type}")
                    print(f"      Similitud: {similarity:.3f}")
                    print(f"      Extracto: {result.get('text', '')[:100]}...")
                    print()
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando indexer: {e}")
        return False

def check_sql_structures():
    """Verificar si hay estructuras SQL indexadas."""
    print_header("ESTRUCTURAS SQL EN EL ÍNDICE")
    
    try:
        from indexer import search_index
        
        # Buscar documentos SQL
        sql_terms = ['tabla', 'database', 'sql server', 'estructura', 'campo']
        sql_docs = []
        
        for term in sql_terms:
            try:
                results = search_index(term, top_k=5)
                for result in results:
                    metadata = result.get('metadata', {})
                    if metadata.get('source_type') in ['database_table', 'database_schema', 'database']:
                        sql_docs.append(result)
            except Exception as e:
                print(f"⚠️ Error buscando '{term}': {e}")
        
        if sql_docs:
            print(f"✅ Encontradas {len(sql_docs)} estructuras SQL indexadas")
            
            # Mostrar ejemplos
            unique_tables = set()
            for doc in sql_docs[:10]:
                metadata = doc.get('metadata', {})
                table_name = metadata.get('table_name', metadata.get('filename', 'N/A'))
                source_type = metadata.get('source_type', 'N/A')
                unique_tables.add(f"{table_name} ({source_type})")
            
            print(f"\n📋 Ejemplos de estructuras encontradas:")
            for table in list(unique_tables)[:5]:
                print(f"   • {table}")
                
        else:
            print("❌ No se encontraron estructuras SQL indexadas")
            print("\n💡 SOLUCIÓN:")
            print("   1. Configurar conexión SQL en .env")
            print("   2. python src/ingestion.py --sql-smart")
            print("   3. python src/indexer.py --force")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_database_explorer():
    """Verificar DatabaseExplorer."""
    print_header("DATABASE EXPLORER")
    
    try:
        from database_explorer import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        print("✅ DatabaseExplorer inicializado")
        
        # Probar búsqueda de tabla FSD601
        print(f"\n🔍 Buscando tabla FSD601...")
        results = explorer.search_tables("FSD601", limit=5)
        
        if results:
            print(f"✅ Encontradas {len(results)} tablas:")
            for table in results:
                print(f"   • {table['full_name']} ({table['column_count']} campos)")
                
            # Probar estructura de la primera tabla
            if results:
                best_table = results[0]
                print(f"\n🏗️ Obteniendo estructura de {best_table['full_name']}...")
                
                structure = explorer.get_table_structure(
                    best_table['table_name'], 
                    best_table['schema']
                )
                
                if structure:
                    print(f"✅ Estructura obtenida: {structure['column_count']} campos")
                    print(f"   Primeros campos:")
                    for col in structure['columns'][:5]:
                        print(f"   • {col['name']}: {col['full_type']}")
                else:
                    print("❌ No se pudo obtener estructura")
        else:
            print("❌ Tabla FSD601 no encontrada")
            print("\n🔍 Probando búsqueda general...")
            
            all_tables = explorer.search_tables("", limit=10)
            if all_tables:
                print(f"✅ Encontradas {len(all_tables)} tablas en la BD:")
                for table in all_tables[:5]:
                    print(f"   • {table['full_name']} ({table['column_count']} campos)")
                if len(all_tables) > 5:
                    print(f"   ... y {len(all_tables) - 5} más")
            else:
                print("❌ No se encontraron tablas en la BD")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ DatabaseExplorer no disponible: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_sql_connection():
    """Verificar conexión SQL Server."""
    print_header("CONEXIÓN SQL SERVER")
    
    try:
        from ingestion_sql import test_sql_connection
        
        if test_sql_connection():
            print("✅ Conexión SQL Server funcional")
            return True
        else:
            print("❌ Problema con conexión SQL Server")
            return False
            
    except ImportError:
        try:
            # Fallback con ingestion básico
            from ingestion import test_sql_connection
            
            if test_sql_connection():
                print("✅ Conexión SQL Server funcional (básica)")
                return True
            else:
                print("❌ Problema con conexión SQL Server")
                return False
                
        except Exception as e:
            print(f"❌ Error probando conexión: {e}")
            return False

def suggest_solutions():
    """Sugerir soluciones basadas en los problemas encontrados."""
    print_header("SOLUCIONES RECOMENDADAS")
    
    print("🔧 Para resolver el problema con tabla FSD601:")
    print()
    print("1️⃣ VERIFICAR CONEXIÓN SQL:")
    print("   python src/ingestion.py --test-sql")
    print()
    print("2️⃣ EXTRAER ESTRUCTURAS DE BD:")
    print("   python src/ingestion.py --sql-smart")
    print()
    print("3️⃣ REINDEXAR TODO:")
    print("   python src/indexer.py --force")
    print()
    print("4️⃣ PROBAR BÚSQUEDA DIRECTA:")
    print("   python src/database_explorer.py search \"FSD601\"")
    print()
    print("5️⃣ CONSULTA GENÉRICA:")
    print("   python rag.py \"consultar tabla FSD601\"")
    print()
    print("💡 Si la tabla no existe, prueba con:")
    print("   python rag.py \"SELECT tabla abonados\"")
    print("   python rag.py \"SELECT tabla clientes\"")

def main():
    """Ejecutar diagnóstico completo."""
    print("🎯" + "="*58 + "🎯")
    print("🔍 DIAGNÓSTICO RÁPIDO DEL SISTEMA RAG")
    print("🎯" + "="*58 + "🎯")
    
    issues = []
    
    # 1. Verificar índice ChromaDB
    if not check_chroma_index():
        issues.append("Índice ChromaDB")
    
    # 2. Verificar estructuras SQL
    if not check_sql_structures():
        issues.append("Estructuras SQL")
    
    # 3. Verificar DatabaseExplorer
    if not check_database_explorer():
        issues.append("DatabaseExplorer")
    
    # 4. Verificar conexión SQL
    if not check_sql_connection():
        issues.append("Conexión SQL")
    
    # Resumen
    print_header("RESUMEN DEL DIAGNÓSTICO")
    
    if not issues:
        print("✅ SISTEMA FUNCIONANDO CORRECTAMENTE")
        print("💡 La tabla FSD601 simplemente no existe en tu BD")
        print("🔍 Prueba con: python rag.py \"SELECT tabla abonados\"")
    else:
        print(f"❌ PROBLEMAS ENCONTRADOS: {', '.join(issues)}")
        suggest_solutions()
    
    print(f"\n📁 Ejecutándose desde: {project_root}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⏹️ Diagnóstico cancelado")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        print("🔧 Verifica que estés ejecutando desde la raíz del proyecto")
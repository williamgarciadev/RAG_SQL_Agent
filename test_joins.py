#!/usr/bin/env python3
"""
Script para probar las mejoras de JOINs y ORDER BY
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_enhanced_sql_generation():
    """Probar la generación mejorada de SQL."""
    
    print("🧪 PROBANDO MEJORAS DE JOINs y ORDER BY")
    print("="*50)
    
    try:
        from database_explorer import DatabaseExplorer
        
        # Crear explorador
        explorer = DatabaseExplorer()
        
        # Probar conexión
        if not explorer.connect():
            print("❌ No se pudo conectar a la base de datos")
            return
        
        print("✅ Conexión exitosa")
        
        # Probar búsqueda de tablas
        print("\n🔍 Buscando tablas FSD...")
        tables = explorer.search_tables("FSD", limit=5)
        
        if not tables:
            print("❌ No se encontraron tablas FSD")
            return
        
        print(f"✅ Encontradas {len(tables)} tablas:")
        for table in tables:
            print(f"  📋 {table['full_name']} ({table['column_count']} campos)")
        
        # Probar generación con JOINs
        test_table = tables[0]
        table_name = test_table['table_name']
        schema = test_table['schema']
        
        print(f"\n🚀 Generando SELECT con JOINs para {table_name}...")
        
        # Sin JOINs
        sql_simple = explorer.generate_select_query(
            table_name=table_name,
            schema=schema,
            include_joins=False
        )
        
        print(f"\n📄 SQL SIN JOINs:")
        print("-" * 40)
        print(sql_simple)
        
        # Con JOINs
        sql_with_joins = explorer.generate_select_query(
            table_name=table_name,
            schema=schema,
            include_joins=True,
            join_type='LEFT'
        )
        
        print(f"\n📄 SQL CON JOINs:")
        print("-" * 40)
        print(sql_with_joins)
        
        # Probar con INNER JOIN
        sql_inner_join = explorer.generate_select_query(
            table_name=table_name,
            schema=schema,
            include_joins=True,
            join_type='INNER'
        )
        
        print(f"\n📄 SQL CON INNER JOINs:")
        print("-" * 40)
        print(sql_inner_join)
        
        print(f"\n✅ ¡Prueba completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

def test_rag_with_joins():
    """Probar el sistema RAG con consultas que requieren JOINs."""
    
    print("\n🧪 PROBANDO RAG CON JOINs")
    print("="*50)
    
    try:
        from agent_director import AgentDirector
        
        # Crear director
        director = AgentDirector()
        
        # Consultas de prueba
        test_queries = [
            "SELECT de FSD601 con relaciones",
            "generar consulta con join para tabla FSD602",
            "mostrar FSD601 con inner join",
            "consulta con left join tabla servicios"
        ]
        
        for query in test_queries:
            print(f"\n💬 Consulta: '{query}'")
            print("-" * 40)
            
            response = director.process_query(query)
            
            if response.get('sql_generated'):
                print("✅ SQL generado:")
                print(response['sql_generated'])
            else:
                print("❌ No se generó SQL")
                print(f"Respuesta: {response.get('response', 'Sin respuesta')}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error en prueba RAG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ejecutar pruebas
    test_enhanced_sql_generation()
    test_rag_with_joins()
    
    print(f"\n🎉 PRUEBAS COMPLETADAS")
    print("="*50)
    print("💡 Para usar en producción:")
    print("   python rag.py \"SELECT de FSD601 con relaciones\"")
    print("   python rag.py \"generar consulta con join para tabla servicios\"")
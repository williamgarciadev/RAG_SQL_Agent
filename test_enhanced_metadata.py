#!/usr/bin/env python3
"""
Script de prueba para metadata mejorada (índices, constraints, foreign keys)
"""

import sys
import os
from pathlib import Path

# Configurar path
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

def test_enhanced_metadata(table_name='FST023', schema='dbo'):
    """Probar metadata completa de una tabla."""
    
    try:
        from database_explorer_pymssql import DatabaseExplorer
        
        print(f"🔍 Probando metadata completa de tabla {schema}.{table_name}...")
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar a la base de datos")
            return False
        
        print("✅ Conexión establecida")
        
        # Obtener estructura completa
        structure = explorer.get_table_structure(table_name, schema)
        
        if not structure:
            print(f"❌ No se encontró la tabla {schema}.{table_name}")
            return False
        
        print(f"\n📊 === METADATA COMPLETA DE {structure['full_name']} ===")
        
        # 1. Información básica
        print(f"\n📋 INFORMACIÓN BÁSICA:")
        print(f"  • Nombre completo: {structure['full_name']}")
        print(f"  • Total campos: {structure['column_count']}")
        print(f"  • Tiene PK: {'✅' if structure['has_primary_key'] else '❌'}")
        
        # Descripción de la tabla
        table_desc = structure.get('table_description', '').strip()
        if table_desc:
            print(f"  • Descripción tabla: {table_desc}")
        
        # 2. Claves Primarias
        print(f"\n🔑 CLAVES PRIMARIAS:")
        if structure['primary_keys']:
            for pk in structure['primary_keys']:
                print(f"  • {pk}")
        else:
            print("  ⚠️ No hay claves primarias")
        
        # 3. Foreign Keys
        print(f"\n🔗 CLAVES FORÁNEAS:")
        foreign_keys = structure.get('foreign_keys', [])
        if foreign_keys:
            for fk in foreign_keys:
                print(f"  • {fk['column_name']} → {fk['referenced_schema']}.{fk['referenced_table']}.{fk['referenced_column']}")
                print(f"    Constraint: {fk['constraint_name']}")
        else:
            print("  ℹ️ No hay claves foráneas")
        
        # 4. Índices
        print(f"\n📊 ÍNDICES:")
        indexes = structure.get('indexes', [])
        if indexes:
            for idx in indexes:
                unique_text = " (ÚNICO)" if idx['is_unique'] else ""
                pk_text = " (PK)" if idx['is_primary_key'] else ""
                print(f"  • {idx['index_name']}: {idx['index_type']}{unique_text}{pk_text}")
                print(f"    Columnas: {idx['columns']}")
        else:
            print("  ℹ️ No hay índices")
        
        # 5. Constraints
        print(f"\n🔗 CONSTRAINTS:")
        constraints = structure.get('constraints', [])
        if constraints:
            for const in constraints:
                columns_text = const['columns'] if const['columns'] else 'N/A'
                print(f"  • {const['CONSTRAINT_NAME']}: {const['CONSTRAINT_TYPE']}")
                print(f"    Columnas: {columns_text}")
        else:
            print("  ℹ️ No hay constraints adicionales")
        
        # 6. Campos con descripciones (resumen)
        print(f"\n📝 CAMPOS CON DESCRIPCIONES:")
        fields_with_desc = 0
        for col in structure['columns']:
            if col.get('description', '').strip():
                fields_with_desc += 1
                print(f"  • {col['name']}: {col.get('description', '')}")
        
        if fields_with_desc == 0:
            print("  ℹ️ No hay campos con descripciones")
        
        # 7. Resumen estadístico
        print(f"\n📈 RESUMEN:")
        print(f"  • Total campos: {structure['column_count']}")
        print(f"  • Campos con descripción: {fields_with_desc}")
        print(f"  • Claves primarias: {len(structure['primary_keys'])}")
        print(f"  • Claves foráneas: {len(foreign_keys)}")
        print(f"  • Índices: {len(indexes)}")
        print(f"  • Constraints: {len(constraints)}")
        
        explorer.close()
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_interface():
    """Mostrar cómo probar en la interfaz web."""
    print("\n🌐 PARA PROBAR EN LA INTERFAZ WEB:")
    print("=" * 50)
    print("1. Ejecutar: streamlit run src/app_enhanced.py")
    print("2. Ir a la pestaña '🔍 Explorador de Tablas'")
    print("3. Buscar una tabla (ej: FST023)")
    print("4. Hacer clic en 'Analizar Primera Tabla'")
    print("5. Verificar las nuevas pestañas:")
    print("   • 📋 Campos - Tabla con descripciones")
    print("   • 🔑 Claves - Primary Keys y Foreign Keys")
    print("   • 📊 Índices - Información de índices")
    print("   • 🔗 Constraints - Constraints adicionales")
    print("\n✨ ¡La metadata completa debería aparecer organizadamente!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Probar metadata completa de tablas')
    parser.add_argument('--table', '-t', default='FST023', help='Nombre de la tabla a probar')
    parser.add_argument('--schema', '-s', default='dbo', help='Esquema de la tabla')
    parser.add_argument('--web-help', action='store_true', help='Mostrar ayuda para interfaz web')
    
    args = parser.parse_args()
    
    if args.web_help:
        test_web_interface()
    else:
        test_enhanced_metadata(args.table, args.schema)
        print()
        test_web_interface()
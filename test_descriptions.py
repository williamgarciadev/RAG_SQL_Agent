#!/usr/bin/env python3
"""
Script de prueba para verificar descripciones de campos
"""

import sys
import os
from pathlib import Path

# Configurar path
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

def test_table_descriptions(table_name='FST001', schema='dbo'):
    """Probar descripciones de una tabla específica."""
    
    try:
        from database_explorer_pymssql import DatabaseExplorer
        
        print(f"🔍 Probando descripciones de tabla {table_name}...")
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar a la base de datos")
            return False
        
        print("✅ Conexión establecida")
        
        # Obtener estructura
        structure = explorer.get_table_structure(table_name, schema)
        
        if not structure:
            print(f"❌ No se encontró la tabla {schema}.{table_name}")
            return False
        
        print(f"\n📊 Tabla: {structure['full_name']}")
        print(f"📊 Total campos: {structure['column_count']}")
        
        # Verificar descripciones
        fields_with_desc = 0
        fields_without_desc = 0
        
        print(f"\n📋 Campos (mostrando todos):")
        for i, col in enumerate(structure['columns'], 1):
            pk_indicator = " 🔑" if col['is_primary_key'] == 'YES' else ""
            description = col.get('description', '').strip()
            
            print(f"  {i:2d}. {col['name']}: {col['full_type']}{pk_indicator}")
            
            if description:
                print(f"      📝 {description}")
                fields_with_desc += 1
            else:
                print(f"      ⚪ Sin descripción")
                fields_without_desc += 1
        
        # Resumen
        print(f"\n📈 Resumen:")
        print(f"  ✅ Campos con descripción: {fields_with_desc}")
        print(f"  ⚪ Campos sin descripción: {fields_without_desc}")
        print(f"  📊 Total campos: {structure['column_count']}")
        
        if fields_with_desc > 0:
            print(f"  🎯 Porcentaje con descripción: {(fields_with_desc/structure['column_count']*100):.1f}%")
        
        explorer.close()
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multiple_tables():
    """Probar varias tablas comunes."""
    
    tables_to_test = [
        ('FST001', 'dbo'),
        ('FSD601', 'dbo'),
        ('FSR001', 'dbo'),
        # Agregar más tablas aquí
    ]
    
    print("🧪 Probando múltiples tablas...\n")
    
    for table_name, schema in tables_to_test:
        print("=" * 60)
        success = test_table_descriptions(table_name, schema)
        if not success:
            print(f"⚠️ Fallo en {table_name}")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Probar descripciones de campos en tablas')
    parser.add_argument('--table', '-t', default='FST001', help='Nombre de la tabla a probar')
    parser.add_argument('--schema', '-s', default='dbo', help='Esquema de la tabla')
    parser.add_argument('--multiple', '-m', action='store_true', help='Probar múltiples tablas')
    
    args = parser.parse_args()
    
    if args.multiple:
        test_multiple_tables()
    else:
        test_table_descriptions(args.table, args.schema)
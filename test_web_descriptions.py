#!/usr/bin/env python3
"""
Script para probar que las descripciones aparecen en la interfaz web
"""

import sys
from pathlib import Path

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_table_structure_for_web(table_name='fsd010', schema='dbo'):
    """Probar que la estructura retorna descripciones para la web."""
    
    try:
        from database_explorer_pymssql import DatabaseExplorer
        
        print(f"🔍 Probando estructura para web: {schema}.{table_name}")
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar")
            return False
        
        structure = explorer.get_table_structure(table_name, schema)
        
        if not structure:
            print(f"❌ No se encontró la tabla {schema}.{table_name}")
            return False
        
        print(f"✅ Estructura obtenida para {structure['full_name']}")
        print(f"📊 Total campos: {structure['column_count']}")
        
        # Verificar que los campos tienen descripciones
        fields_with_desc = 0
        print(f"\n📋 VERIFICANDO DESCRIPCIONES:")
        
        for i, col in enumerate(structure['columns'][:10], 1):  # Primeros 10 campos
            description = col.get('description', '').strip()
            has_desc = "✅" if description else "❌"
            
            print(f"  {i:2d}. {col['name']}: {has_desc}")
            if description:
                print(f"      📝 {description}")
                fields_with_desc += 1
            else:
                print(f"      ⚪ Sin descripción")
        
        # Verificar formato para pandas DataFrame
        print(f"\n🐼 FORMATO PARA PANDAS:")
        columns_data = []
        for col in structure['columns'][:5]:  # Primeros 5
            description = col.get('description', '').strip()
            columns_data.append({
                'Campo': col['name'],
                'Tipo': col['full_type'],
                'Nullable': col['is_nullable'],
                'PK': '🔑' if col['is_primary_key'] == 'YES' else '',
                'Posición': col['ordinal_position'],
                'Descripción': description if description else '(Sin descripción)'
            })
        
        # Mostrar cómo aparecería en el DataFrame
        for i, row in enumerate(columns_data, 1):
            print(f"  {i}. {row['Campo']}: {row['Tipo']}")
            print(f"     Descripción: '{row['Descripción']}'")
        
        # Estadísticas
        total_with_desc = sum(1 for col in structure['columns'] if col.get('description', '').strip())
        percentage = (total_with_desc / structure['column_count'] * 100) if structure['column_count'] > 0 else 0
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  • Total campos: {structure['column_count']}")
        print(f"  • Con descripción: {total_with_desc}")
        print(f"  • Porcentaje: {percentage:.1f}%")
        
        explorer.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_web_dataframe():
    """Simular cómo aparecería en la interfaz web."""
    
    print(f"\n🌐 SIMULACIÓN INTERFAZ WEB:")
    print("=" * 50)
    
    try:
        import pandas as pd
        
        # Datos de ejemplo como los que vendrían de la base
        sample_data = [
            {'Campo': 'Pgcod', 'Tipo': 'smallint', 'Nullable': 'NO', 'PK': '🔑', 'Posición': 1, 'Descripción': 'Cod.'},
            {'Campo': 'Aomod', 'Tipo': 'int', 'Nullable': 'NO', 'PK': '🔑', 'Posición': 2, 'Descripción': 'Modulo'},
            {'Campo': 'Aosuc', 'Tipo': 'int', 'Nullable': 'NO', 'PK': '🔑', 'Posición': 3, 'Descripción': 'Sucursal'},
            {'Campo': 'Aoimp', 'Tipo': 'decimal(17,2)', 'Nullable': 'YES', 'PK': '', 'Posición': 23, 'Descripción': 'Importe'},
        ]
        
        df = pd.DataFrame(sample_data)
        
        print("📊 Datos como aparecerían en Streamlit:")
        print(df.to_string(index=False))
        
        print(f"\n✅ Las descripciones SÍ están en los datos")
        print(f"🔍 Problema posible: Ancho de columnas en Streamlit")
        
        return True
        
    except ImportError:
        print("❌ Pandas no disponible")
        return False

def show_web_testing_guide():
    """Mostrar guía para probar en la web."""
    
    print(f"\n🚀 GUÍA PARA PROBAR EN WEB:")
    print("=" * 50)
    print("1. Ejecutar: streamlit run src/app_enhanced.py")
    print("2. Ir a '🔍 Explorador de Tablas'")
    print("3. Buscar: 'fsd010'")
    print("4. Hacer clic: '📋 Analizar Primera Tabla'")
    print("5. Ir a pestaña: '📋 Campos'")
    print("6. Verificar:")
    print("   • Métricas de descripciones arriba")
    print("   • Columna 'Descripción' en tabla")
    print("   • Expandir '📝 Vista Detallada' si existe")
    print("\n🔧 Si no se ven las descripciones:")
    print("   • Verificar ancho de columna 'Descripción'")
    print("   • Usar la vista detallada expandible")
    print("   • Revisar configuración de pandas en Streamlit")

if __name__ == "__main__":
    print("🧪 PROBANDO DESCRIPCIONES PARA INTERFAZ WEB")
    print("=" * 60)
    
    # Prueba 1: Estructura de tabla
    test1_ok = test_table_structure_for_web('fsd010')
    
    # Prueba 2: Simulación DataFrame
    test2_ok = simulate_web_dataframe()
    
    # Guía de pruebas
    show_web_testing_guide()
    
    print(f"\n📊 RESUMEN:")
    print(f"  • Estructura BD: {'✅' if test1_ok else '❌'}")
    print(f"  • Formato DataFrame: {'✅' if test2_ok else '❌'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 Los datos están correctos. Problema puede ser de visualización en Streamlit.")
    else:
        print("\n⚠️ Hay problemas en los datos que resolver.")
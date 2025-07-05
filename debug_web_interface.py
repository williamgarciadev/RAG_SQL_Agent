#!/usr/bin/env python3
"""
Script para debuggear la interfaz web y las descripciones
"""

import sys
from pathlib import Path

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def debug_web_interface_flow():
    """Simular exactamente lo que hace la interfaz web."""
    
    try:
        print("🔍 DEBUGGING INTERFAZ WEB - Flujo completo")
        print("=" * 60)
        
        # 1. Simular load_database_explorer()
        print("1. Cargando database explorer...")
        from database_explorer import DatabaseExplorer
        explorer = DatabaseExplorer()
        print("✅ Explorer cargado")
        
        # 2. Simular conexión
        print("2. Conectando a la base de datos...")
        if not explorer.connect():
            print("❌ Error de conexión")
            return False
        print("✅ Conexión establecida")
        
        # 3. Simular search_tables
        print("3. Buscando tabla FSD010...")
        search_term = "FSD010"
        tables = explorer.search_tables(search_term, limit=20)
        print(f"✅ Encontradas {len(tables)} tablas")
        
        if not tables:
            print("❌ No se encontraron tablas")
            return False
        
        # 4. Mostrar información de la tabla encontrada
        best_table = tables[0]
        print(f"📊 Primera tabla: {best_table}")
        
        # 5. Simular get_table_structure exactamente como la web
        print("4. Obteniendo estructura de tabla...")
        structure = explorer.get_table_structure(
            best_table['table_name'], 
            best_table['schema_name']
        )
        
        if not structure:
            print("❌ No se pudo obtener estructura")
            return False
        
        print(f"✅ Estructura obtenida: {structure['column_count']} campos")
        
        # 6. SIMULAR EXACTAMENTE EL CÓDIGO DE LA WEB
        print("\n5. Simulando lógica de conteo de la interfaz web...")
        print("-" * 50)
        
        # Contadores para estadísticas
        fields_with_desc = 0
        total_fields = len(structure['columns'])
        
        columns_data = []
        for col in structure['columns']:
            description = col.get('description', '').strip()
            print(f"Campo: {col['name']}, Descripción: '{description}', Len: {len(description)}")
            
            if description:
                fields_with_desc += 1
            
            columns_data.append({
                'Campo': col['name'],
                'Tipo': col['full_type'],
                'Nullable': col['is_nullable'],
                'PK': '🔑' if col['is_primary_key'] == 'YES' else '',
                'Posición': col['ordinal_position'],
                'Descripción': description if description else '(Sin descripción)'
            })
        
        # 7. Mostrar estadísticas finales
        print(f"\n📊 ESTADÍSTICAS FINALES:")
        print(f"  • Total campos: {total_fields}")
        print(f"  • Con descripción: {fields_with_desc}")
        percentage = (fields_with_desc / total_fields * 100) if total_fields > 0 else 0
        print(f"  • Porcentaje: {percentage:.1f}%")
        
        # 8. Verificar datos del DataFrame
        print(f"\n📋 DATOS DEL DATAFRAME (primeros 5):")
        for i, row in enumerate(columns_data[:5], 1):
            desc_preview = row['Descripción'][:20] + "..." if len(row['Descripción']) > 20 else row['Descripción']
            print(f"  {i}. {row['Campo']}: '{desc_preview}'")
        
        explorer.close()
        
        return fields_with_desc > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_direct_database_structure():
    """Verificar directamente la estructura desde la base de datos."""
    
    print("\n🔍 VERIFICACIÓN DIRECTA DE BASE DE DATOS")
    print("=" * 60)
    
    try:
        from database_explorer_pymssql import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        if not explorer.connect():
            print("❌ Error de conexión")
            return False
        
        # Ejecutar la consulta directa que usa el sistema
        query = """
        SELECT 
            c.COLUMN_NAME as name,
            c.DATA_TYPE as data_type,
            c.CHARACTER_MAXIMUM_LENGTH as max_length,
            c.IS_NULLABLE as is_nullable,
            c.COLUMN_DEFAULT as default_value,
            c.ORDINAL_POSITION as ordinal_position,
            CASE 
                WHEN c.DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar') 
                THEN c.DATA_TYPE + '(' + CAST(ISNULL(c.CHARACTER_MAXIMUM_LENGTH, 0) AS VARCHAR) + ')'
                WHEN c.DATA_TYPE IN ('decimal', 'numeric')
                THEN c.DATA_TYPE + '(' + CAST(c.NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(c.NUMERIC_SCALE AS VARCHAR) + ')'
                ELSE c.DATA_TYPE
            END as full_type,
            CASE 
                WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES'
                ELSE 'NO'
            END as is_primary_key,
            ISNULL(CAST(ep.value AS NVARCHAR(MAX)), '') as description
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku 
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.TABLE_NAME = 'FSD010'
            AND tc.TABLE_SCHEMA = 'dbo'
            AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
        LEFT JOIN sys.extended_properties ep ON ep.major_id = OBJECT_ID('dbo.FSD010')
            AND ep.minor_id = c.ORDINAL_POSITION
            AND ep.name = 'MS_Description'
        WHERE c.TABLE_NAME = 'FSD010'
        AND c.TABLE_SCHEMA = 'dbo'
        ORDER BY c.ORDINAL_POSITION
        """
        
        results = explorer.execute_query(query)
        
        print(f"✅ Consulta ejecutada: {len(results)} campos")
        
        with_desc = 0
        for i, result in enumerate(results[:10], 1):
            desc = result.get('description', '').strip()
            if desc:
                with_desc += 1
            print(f"  {i}. {result['name']}: '{desc}' (tipo: {type(desc)}, len: {len(desc)})")
        
        print(f"\n📊 TOTAL: {with_desc}/{len(results)} campos con descripción")
        
        explorer.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 DEBUGGING DESCRIPCIONES EN INTERFAZ WEB")
    print("=" * 70)
    
    # Test 1: Flujo completo de la interfaz web
    test1_ok = debug_web_interface_flow()
    
    # Test 2: Verificación directa de BD
    test2_ok = debug_direct_database_structure()
    
    print(f"\n📊 RESUMEN:")
    print(f"  • Flujo interfaz web: {'✅' if test1_ok else '❌'}")
    print(f"  • Consulta directa BD: {'✅' if test2_ok else '❌'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 Los datos están correctos. El problema puede ser de caché en Streamlit.")
        print("💡 Soluciones:")
        print("  1. Reiniciar Streamlit: Ctrl+C y volver a ejecutar")
        print("  2. Limpiar caché: Presionar 'C' en Streamlit")
        print("  3. Verificar que no haya caché del @st.cache_resource")
    else:
        print("\n⚠️ Hay problemas que resolver en los datos.")
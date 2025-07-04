#!/usr/bin/env python3
"""
Probar consulta SQL directa para descripciones
"""

import sys
from pathlib import Path

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_sql_query(table_name='FST001', schema='dbo'):
    """Ejecutar la consulta SQL directamente."""
    
    try:
        from database_explorer_pymssql import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar")
            return
        
        # La consulta exacta que usa el sistema
        query = f"""
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
            WHERE tc.TABLE_NAME = '{table_name}'
            AND tc.TABLE_SCHEMA = '{schema}'
            AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
        LEFT JOIN sys.extended_properties ep ON ep.major_id = OBJECT_ID('{schema}.{table_name}')
            AND ep.minor_id = c.ORDINAL_POSITION
            AND ep.name = 'MS_Description'
        WHERE c.TABLE_NAME = '{table_name}'
        AND c.TABLE_SCHEMA = '{schema}'
        ORDER BY c.ORDINAL_POSITION
        """
        
        print(f"🔍 Ejecutando consulta para {schema}.{table_name}...")
        print(f"📝 Consulta SQL:")
        print("-" * 50)
        print(query)
        print("-" * 50)
        
        results = explorer.execute_query(query)
        
        if results:
            print(f"✅ Encontrados {len(results)} campos")
            
            for result in results[:5]:  # Mostrar primeros 5
                desc = result.get('description', '').strip()
                print(f"  • {result['name']}: {result['full_type']}")
                if desc:
                    print(f"    📝 {desc}")
                else:
                    print(f"    ⚪ Sin descripción")
        else:
            print("❌ No se encontraron resultados")
        
        explorer.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    table_name = sys.argv[1] if len(sys.argv) > 1 else 'FST001'
    schema = sys.argv[2] if len(sys.argv) > 2 else 'dbo'
    
    test_sql_query(table_name, schema)
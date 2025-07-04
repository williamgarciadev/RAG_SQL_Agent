#!/usr/bin/env python3
"""
Generador de JOINs Inteligente - Basado en PKs reales
"""

import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from database_explorer_pymssql import DatabaseExplorer
except ImportError:
    from database_explorer import DatabaseExplorer

def find_related_tables(explorer, main_table: str, schema: str = 'dbo') -> dict:
    """Encontrar tablas relacionadas basadas en las PKs de la tabla principal"""
    
    # Obtener estructura de la tabla principal
    main_structure = explorer.get_table_structure(main_table, schema)
    if not main_structure:
        return {}
    
    # Obtener PKs de la tabla principal
    main_pks = main_structure['primary_keys']
    if not main_pks:
        print(f"⚠️  {main_table} no tiene claves primarias")
        return {}
    
    print(f"🔑 PKs de {main_table}: {', '.join(main_pks)}")
    
    # Buscar tablas que contengan estos campos como FK
    related_tables = {}
    
    # Query para buscar tablas con campos similares a nuestras PKs
    for pk in main_pks:
        query = f"""
        SELECT DISTINCT
            c.TABLE_SCHEMA,
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.COLUMN_NAME = '{pk}'
        AND c.TABLE_NAME != '{main_table}'
        AND c.TABLE_SCHEMA = '{schema}'
        ORDER BY c.TABLE_NAME
        """
        
        results = explorer.execute_query(query)
        
        if results:
            print(f"\n📋 Tablas con campo '{pk}':")
            for result in results:
                table_name = result['TABLE_NAME']
                if table_name not in related_tables:
                    related_tables[table_name] = {
                        'schema': result['TABLE_SCHEMA'],
                        'common_fields': [],
                        'join_conditions': []
                    }
                
                related_tables[table_name]['common_fields'].append({
                    'field': pk,
                    'type': result['DATA_TYPE']
                })
                
                related_tables[table_name]['join_conditions'].append(
                    f"{schema}.{main_table}.{pk} = {result['TABLE_SCHEMA']}.{table_name}.{pk}"
                )
                
                print(f"   • {result['TABLE_SCHEMA']}.{table_name}.{pk}")
    
    return related_tables

def generate_smart_joins(main_table: str, related_tables: dict, max_joins: int = 3) -> list:
    """Generar consultas SQL con JOINs inteligentes"""
    
    queries = []
    
    # Obtener las tablas más relevantes (las que más campos comunes tienen)
    sorted_tables = sorted(
        related_tables.items(),
        key=lambda x: len(x[1]['common_fields']),
        reverse=True
    )
    
    # Generar diferentes tipos de consultas
    
    # 1. JOIN con la tabla más relacionada
    if sorted_tables:
        best_table = sorted_tables[0]
        table_name = best_table[0]
        table_info = best_table[1]
        
        join_conditions = ' AND '.join(table_info['join_conditions'])
        
        query1 = f"""-- SELECT con JOIN a tabla más relacionada
SELECT 
    f601.*,
    {table_info['schema']}.{table_name}.*
FROM dbo.{main_table} f601
INNER JOIN {table_info['schema']}.{table_name} 
    ON {join_conditions};"""
        
        queries.append({
            'description': f'JOIN con {table_name} (tabla más relacionada)',
            'sql': query1,
            'tables': [main_table, table_name],
            'common_fields': len(table_info['common_fields'])
        })
    
    # 2. JOIN múltiple con las top 3 tablas
    if len(sorted_tables) >= 2:
        top_tables = sorted_tables[:min(max_joins, len(sorted_tables))]
        
        select_parts = [f"f601.*"]
        join_parts = []
        
        for i, (table_name, table_info) in enumerate(top_tables):
            alias = f"t{i+1}"
            select_parts.append(f"{alias}.*")
            join_conditions = ' AND '.join([
                condition.replace(f"{table_info['schema']}.{table_name}", alias)
                for condition in table_info['join_conditions']
            ])
            join_parts.append(f"LEFT JOIN {table_info['schema']}.{table_name} {alias} ON {join_conditions}")
        
        query2 = f"""-- SELECT con JOINs múltiples
SELECT 
    {','.join(select_parts)}
FROM dbo.{main_table} f601
{chr(10).join(join_parts)};"""
        
        queries.append({
            'description': f'JOIN múltiple con {len(top_tables)} tablas',
            'sql': query2,
            'tables': [main_table] + [t[0] for t in top_tables],
            'common_fields': sum(len(t[1]['common_fields']) for t in top_tables)
        })
    
    # 3. Consulta de análisis de relaciones
    if sorted_tables:
        analysis_query = f"""-- Análisis de registros relacionados
SELECT 
    'Tabla principal' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.{main_table}

UNION ALL
"""
        
        union_parts = []
        for table_name, table_info in sorted_tables[:5]:  # Top 5 tablas
            union_parts.append(f"""SELECT 
    '{table_name}' as Tabla,
    COUNT(*) as Total_Registros
FROM {table_info['schema']}.{table_name}""")
        
        analysis_query += "\nUNION ALL\n".join(union_parts) + ";"
        
        queries.append({
            'description': 'Análisis de registros por tabla',
            'sql': analysis_query,
            'tables': [main_table] + [t[0] for t in sorted_tables[:5]],
            'common_fields': 0
        })
    
    return queries

def main():
    """Generar JOINs inteligentes para FSD601"""
    print("🎯" + "="*70 + "🎯")
    print("🧠 GENERADOR DE JOINS INTELIGENTE - BASADO EN PKs REALES")
    print("🎯" + "="*70 + "🎯")
    
    try:
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar a la base de datos")
            return
        
        main_table = "Fsd601"
        
        print(f"\n🔍 Analizando tabla {main_table}...")
        
        # Encontrar tablas relacionadas
        related_tables = find_related_tables(explorer, main_table)
        
        if not related_tables:
            print(f"\n❌ No se encontraron tablas relacionadas con {main_table}")
            return
        
        print(f"\n✅ Encontradas {len(related_tables)} tablas relacionadas")
        
        # Generar JOINs inteligentes
        queries = generate_smart_joins(main_table, related_tables)
        
        print(f"\n🚀 CONSULTAS SQL GENERADAS:")
        print("=" * 70)
        
        for i, query_info in enumerate(queries, 1):
            print(f"\n{i}. {query_info['description']}")
            print(f"   Tablas: {', '.join(query_info['tables'])}")
            print(f"   Campos comunes: {query_info['common_fields']}")
            print()
            print(query_info['sql'])
            print("-" * 70)
        
        # Guardar consultas en archivo
        output_file = "fsd601_smart_joins.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- JOINs INTELIGENTES PARA FSD601\n")
            f.write("-- Generado automáticamente basado en PKs reales\n\n")
            
            for i, query_info in enumerate(queries, 1):
                f.write(f"-- {i}. {query_info['description']}\n")
                f.write(f"-- Tablas: {', '.join(query_info['tables'])}\n")
                f.write(f"-- Campos comunes: {query_info['common_fields']}\n")
                f.write(query_info['sql'])
                f.write("\n\n")
        
        print(f"\n💾 Consultas guardadas en: {output_file}")
        
        explorer.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
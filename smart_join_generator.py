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
    """Encontrar tablas relacionadas basadas en las primeras 9 PKs de la tabla principal
    
    Optimizado para miles de tablas usando una sola query y cache.
    """
    
    # Obtener estructura de la tabla principal
    main_structure = explorer.get_table_structure(main_table, schema)
    if not main_structure:
        return {}
    
    # Obtener PKs de la tabla principal
    main_pks = main_structure['primary_keys']
    if not main_pks:
        print(f"⚠️  {main_table} no tiene claves primarias")
        return {}
    
    # Tomar solo las primeras 9 PKs para optimizar
    first_9_pks = main_pks[:9]
    print(f"🔑 Primeras 9 PKs de {main_table}: {', '.join(first_9_pks)}")
    
    # Cache para evitar consultas repetidas
    cache_key = f"{main_table}_{hash(tuple(first_9_pks))}"
    if hasattr(explorer, '_join_cache') and cache_key in explorer._join_cache:
        print("📋 Usando cache para tablas relacionadas")
        return explorer._join_cache[cache_key]
    
    # Query optimizada con múltiples categorías de tablas
    pk_conditions = []
    for i, pk in enumerate(first_9_pks, 1):
        pk_conditions.append(f"(c.COLUMN_NAME = '{pk}' AND c.ORDINAL_POSITION = {i})")
    
    query = f"""
    WITH TableMatches AS (
        SELECT 
            c.TABLE_SCHEMA,
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.ORDINAL_POSITION,
            COUNT(*) OVER (PARTITION BY c.TABLE_NAME) as match_count,
            CASE 
                WHEN c.TABLE_NAME LIKE 'Fs%' THEN 'Bantotal_Standard'
                WHEN c.TABLE_NAME LIKE '%_temp' OR c.TABLE_NAME LIKE 'temp_%' THEN 'Temporal'
                WHEN c.TABLE_NAME LIKE '%_bkp' OR c.TABLE_NAME LIKE 'bkp_%' OR c.TABLE_NAME LIKE '%backup%' THEN 'Backup'
                WHEN c.TABLE_NAME LIKE 'v_%' OR c.TABLE_NAME LIKE '%_view' THEN 'Vista'
                WHEN c.TABLE_NAME LIKE 'log_%' OR c.TABLE_NAME LIKE '%_log' THEN 'Log'
                WHEN c.TABLE_NAME LIKE 'sys%' OR c.TABLE_NAME LIKE 'INFORMATION_SCHEMA%' THEN 'Sistema'
                ELSE 'Bancaria_Personalizada'
            END as table_category
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE ({' OR '.join(pk_conditions)})
        AND c.TABLE_NAME != '{main_table}'
        AND c.TABLE_SCHEMA = '{schema}'
        -- Excluir solo tablas claramente de sistema o temporales
        AND c.TABLE_NAME NOT LIKE 'sys%'
        AND c.TABLE_NAME NOT LIKE 'INFORMATION_SCHEMA%'
        AND c.TABLE_NAME NOT LIKE '%_temp'
        AND c.TABLE_NAME NOT LIKE 'temp_%'
        AND c.TABLE_NAME NOT LIKE '%_bkp'
        AND c.TABLE_NAME NOT LIKE 'bkp_%'
    )
    SELECT 
        TABLE_SCHEMA,
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE,
        ORDINAL_POSITION,
        match_count,
        table_category
    FROM TableMatches
    WHERE match_count >= 2  -- Al menos 2 campos coinciden
    ORDER BY 
        CASE table_category 
            WHEN 'Bantotal_Standard' THEN 1 
            WHEN 'Bancaria_Personalizada' THEN 2
            WHEN 'Vista' THEN 3
            ELSE 4
        END,
        match_count DESC, 
        TABLE_NAME, 
        ORDINAL_POSITION
    """
    
    results = explorer.execute_query(query)
    related_tables = {}
    categories_stats = {}
    
    if results:
        unique_tables = set(r['TABLE_NAME'] for r in results)
        print(f"\n📋 Encontradas {len(unique_tables)} tablas con coincidencias:")
        
        # Agrupar por tabla
        for result in results:
            table_name = result['TABLE_NAME']
            category = result['table_category']
            
            if table_name not in related_tables:
                related_tables[table_name] = {
                    'schema': result['TABLE_SCHEMA'],
                    'common_fields': [],
                    'join_conditions': [],
                    'match_count': result['match_count'],
                    'confidence': min(result['match_count'] / 9.0, 1.0),  # Normalizado a 9 campos
                    'category': category
                }
            
            related_tables[table_name]['common_fields'].append({
                'field': result['COLUMN_NAME'],
                'type': result['DATA_TYPE'],
                'position': result['ORDINAL_POSITION']
            })
            
            related_tables[table_name]['join_conditions'].append(
                f"{schema}.{main_table}.{result['COLUMN_NAME']} = {result['TABLE_SCHEMA']}.{table_name}.{result['COLUMN_NAME']}"
            )
            
            # Contar por categoría
            if category not in categories_stats:
                categories_stats[category] = 0
            categories_stats[category] += 1
        
        # Mostrar estadísticas por categoría
        print(f"\n📊 Distribución por categorías:")
        for category, count in sorted(categories_stats.items(), key=lambda x: x[1], reverse=True):
            category_emoji = {
                'Bantotal_Standard': '🏦',
                'Bancaria_Personalizada': '💼', 
                'Vista': '🔍',
                'Log': '📜',
                'Temporal': '⏱️',
                'Backup': '💾'
            }.get(category, '📊')
            print(f"   {category_emoji} {category}: {count} tablas")
        
        # Mostrar resumen ordenado por categoría y confianza
        print(f"\n📊 Resumen por tabla:")
        for table_name, info in sorted(related_tables.items(), 
                                     key=lambda x: (x[1]['category'] == 'Bantotal_Standard', x[1]['confidence']), 
                                     reverse=True):
            category_emoji = {
                'Bantotal_Standard': '🏦',
                'Bancaria_Personalizada': '💼', 
                'Vista': '🔍',
                'Log': '📜',
                'Temporal': '⏱️',
                'Backup': '💾'
            }.get(info['category'], '📊')
            print(f"   {category_emoji} {table_name}: {info['match_count']} campos ({info['confidence']:.1%} confianza) [{info['category']}]")
    
    # Guardar en cache
    if not hasattr(explorer, '_join_cache'):
        explorer._join_cache = {}
    explorer._join_cache[cache_key] = related_tables
    
    return related_tables

def generate_smart_joins(main_table: str, related_tables: dict, max_joins: int = 3) -> list:
    """Generar consultas SQL con JOINs inteligentes basados en las primeras 9 PKs
    
    Optimizado para alta confianza y performance.
    """
    
    queries = []
    
    # Obtener las tablas más relevantes por confianza (no solo cantidad)
    sorted_tables = sorted(
        related_tables.items(),
        key=lambda x: (x[1]['confidence'], x[1]['match_count']),
        reverse=True
    )
    
    # Generar diferentes tipos de consultas
    
    # 1. JOIN con la tabla de mayor confianza
    if sorted_tables:
        best_table = sorted_tables[0]
        table_name = best_table[0]
        table_info = best_table[1]
        
        # Usar solo las primeras 9 condiciones de JOIN para performance
        join_conditions = ' AND '.join(table_info['join_conditions'][:9])
        
        query1 = f"""-- SELECT con JOIN a tabla de mayor confianza ({table_info['confidence']:.1%})
-- Primeras 9 PKs: {', '.join([f['field'] for f in table_info['common_fields'][:9]])}
SELECT TOP 1000
    f601.*,
    {table_info['schema']}.{table_name}.*
FROM dbo.{main_table} f601
INNER JOIN {table_info['schema']}.{table_name} 
    ON {join_conditions}
ORDER BY f601.Pgcod, f601.Ppmod;"""
        
        queries.append({
            'description': f'JOIN con {table_name} (confianza {table_info["confidence"]:.1%}) [{table_info.get("category", "Sin categoría")}]',
            'sql': query1,
            'tables': [main_table, table_name],
            'common_fields': table_info['match_count'],
            'confidence': table_info['confidence'],
            'categories': [table_info.get('category', 'Sin categoría')]
        })
    
    # 2. JOIN múltiple con las top 3 tablas de alta confianza
    if len(sorted_tables) >= 2:
        # Filtrar solo tablas con confianza >= 30%
        high_confidence_tables = [(name, info) for name, info in sorted_tables 
                                if info['confidence'] >= 0.3]
        
        top_tables = high_confidence_tables[:min(max_joins, len(high_confidence_tables))]
        
        if top_tables:
            select_parts = [f"f601.*"]
            join_parts = []
            
            for i, (table_name, table_info) in enumerate(top_tables):
                alias = f"t{i+1}"
                select_parts.append(f"{alias}.*")
                # Usar solo primeras 9 condiciones de JOIN
                join_conditions = ' AND '.join([
                    condition.replace(f"{table_info['schema']}.{table_name}", alias)
                    for condition in table_info['join_conditions'][:9]
                ])
                join_parts.append(f"LEFT JOIN {table_info['schema']}.{table_name} {alias} ON {join_conditions}")
            
            confidences = [f"{info['confidence']:.1%}" for _, info in top_tables]
            query2 = f"""-- SELECT con JOINs múltiples (confianzas: {', '.join(confidences)})
-- Optimizado para las primeras 9 PKs por tabla
SELECT TOP 500
    {','.join(select_parts)}
FROM dbo.{main_table} f601
{chr(10).join(join_parts)}
ORDER BY f601.Pgcod, f601.Ppmod;"""
            
            categories = list(set(info.get('category', 'Sin categoría') for _, info in top_tables))
            queries.append({
                'description': f'JOIN múltiple con {len(top_tables)} tablas (confianza promedio: {sum(info["confidence"] for _, info in top_tables)/len(top_tables):.1%}) [Categorías: {", ".join(categories)}]',
                'sql': query2,
                'tables': [main_table] + [t[0] for t in top_tables],
                'common_fields': sum(t[1]['match_count'] for t in top_tables),
                'confidence': sum(info['confidence'] for _, info in top_tables) / len(top_tables),
                'categories': categories
            })
    
    # 3. Consulta de análisis de relaciones con confianza
    if sorted_tables:
        # Solo incluir tablas con confianza >= 20%
        analysis_tables = [(name, info) for name, info in sorted_tables 
                         if info['confidence'] >= 0.2][:5]
        
        if analysis_tables:
            analysis_query = f"""-- Análisis de registros relacionados con confianza
SELECT 
    'Tabla principal' as Tabla,
    COUNT(*) as Total_Registros,
    '100%' as Confianza
FROM dbo.{main_table}

UNION ALL
"""
            
            union_parts = []
            for table_name, table_info in analysis_tables:
                union_parts.append(f"""SELECT 
    '{table_name}' as Tabla,
    COUNT(*) as Total_Registros,
    '{table_info['confidence']:.1%}' as Confianza
FROM {table_info['schema']}.{table_name}""")
            
            analysis_query += "\nUNION ALL\n".join(union_parts) + "\nORDER BY Confianza DESC;"
            
            categories = list(set(info.get('category', 'Sin categoría') for _, info in analysis_tables))
            queries.append({
                'description': f'Análisis de registros por tabla (Top {len(analysis_tables)} con confianza >= 20%) [Categorías: {", ".join(categories)}]',
                'sql': analysis_query,
                'tables': [main_table] + [t[0] for t in analysis_tables],
                'common_fields': sum(t[1]['match_count'] for t in analysis_tables),
                'confidence': sum(info['confidence'] for _, info in analysis_tables) / len(analysis_tables),
                'categories': categories
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
        
        # Mostrar estadísticas de confianza y categorías
        if related_tables:
            high_conf = sum(1 for info in related_tables.values() if info['confidence'] >= 0.5)
            med_conf = sum(1 for info in related_tables.values() if 0.3 <= info['confidence'] < 0.5)
            low_conf = sum(1 for info in related_tables.values() if info['confidence'] < 0.3)
            
            bantotal_std = sum(1 for info in related_tables.values() if info['category'] == 'Bantotal_Standard')
            bancaria_pers = sum(1 for info in related_tables.values() if info['category'] == 'Bancaria_Personalizada')
            
            print(f"📊 Confianza: {high_conf} altas (≥50%), {med_conf} medias (30-50%), {low_conf} bajas (<30%)")
            print(f"🏦 Categorías: {bantotal_std} Bantotal estándar, {bancaria_pers} bancarias personalizadas, {len(related_tables) - bantotal_std - bancaria_pers} otras")
        
        # Generar JOINs inteligentes
        queries = generate_smart_joins(main_table, related_tables)
        
        print(f"\n🚀 CONSULTAS SQL GENERADAS:")
        print("=" * 70)
        
        for i, query_info in enumerate(queries, 1):
            print(f"\n{i}. {query_info['description']}")
            print(f"   Tablas: {', '.join(query_info['tables'])}")
            print(f"   Campos comunes: {query_info['common_fields']}")
            if 'confidence' in query_info:
                print(f"   Confianza: {query_info['confidence']:.1%}")
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
                if 'confidence' in query_info:
                    f.write(f"-- Confianza: {query_info['confidence']:.1%}\n")
                if 'categories' in query_info:
                    f.write(f"-- Categorías: {', '.join(query_info['categories'])}\n")
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
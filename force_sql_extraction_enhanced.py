#!/usr/bin/env python3
"""
Script para forzar extracción SQL con metadata mejorada
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def extract_enhanced_sql_metadata():
    """Extraer metadata SQL con la nueva funcionalidad."""
    
    try:
        from database_explorer_pymssql import DatabaseExplorer
        
        print("🔍 Iniciando extracción SQL con metadata mejorada...")
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar a SQL Server")
            return False
        
        print("✅ Conexión establecida a SQL Server")
        
        # 1. Obtener overview general
        print("📊 Obteniendo vista general de la base de datos...")
        overview = explorer.get_database_overview()
        
        if not overview:
            print("❌ No se pudo obtener overview")
            return False
        
        print(f"✅ Overview obtenido: {overview.get('DATABASE_NAME')} - {overview.get('TOTAL_TABLES')} tablas")
        
        # 2. Obtener tablas importantes con metadata completa
        print("🔍 Obteniendo metadata de tablas importantes...")
        
        important_tables = ['FST001', 'FST023', 'FSD010', 'FSD601']
        enhanced_metadata = {
            'database_overview': overview,
            'tables_with_enhanced_metadata': {},
            'extraction_info': {
                'timestamp': datetime.now().isoformat(),
                'enhanced_features': [
                    'field_descriptions',
                    'table_descriptions', 
                    'foreign_keys',
                    'indexes',
                    'constraints'
                ]
            }
        }
        
        for table_name in important_tables:
            print(f"  📋 Procesando {table_name}...")
            
            # Buscar tabla
            search_results = explorer.search_tables(table_name, limit=1)
            if not search_results:
                print(f"    ❌ No encontrada: {table_name}")
                continue
            
            table_info = search_results[0]
            
            # Obtener estructura completa con nueva metadata
            structure = explorer.get_table_structure(
                table_info['table_name'], 
                table_info['schema_name']
            )
            
            if structure:
                # Contar descripciones
                fields_with_desc = sum(1 for col in structure['columns'] if col.get('description', '').strip())
                
                enhanced_metadata['tables_with_enhanced_metadata'][table_name] = {
                    'basic_info': {
                        'full_name': structure['full_name'],
                        'column_count': structure['column_count'],
                        'has_primary_key': structure['has_primary_key']
                    },
                    'enhanced_metadata': {
                        'table_description': structure.get('table_description', ''),
                        'fields_with_descriptions': fields_with_desc,
                        'foreign_keys_count': len(structure.get('foreign_keys', [])),
                        'indexes_count': len(structure.get('indexes', [])),
                        'constraints_count': len(structure.get('constraints', []))
                    },
                    'sample_fields': structure['columns'][:5]  # Primeros 5 campos como muestra
                }
                
                print(f"    ✅ {table_name}: {fields_with_desc}/{structure['column_count']} campos con descripción")
            else:
                print(f"    ❌ No se pudo obtener estructura: {table_name}")
        
        # 3. Guardar metadata mejorada
        output_file = Path(__file__).parent / 'docs' / 'enhanced_sql_metadata.json'
        
        print(f"💾 Guardando metadata mejorada en {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Metadata guardada: {output_file}")
        
        # 4. Generar documento de texto para RAG
        rag_content = generate_rag_document(enhanced_metadata)
        
        rag_file = Path(__file__).parent / 'docs' / 'enhanced_sql_for_rag.txt'
        
        print(f"📝 Generando documento RAG en {rag_file}...")
        
        with open(rag_file, 'w', encoding='utf-8') as f:
            f.write(rag_content)
        
        print(f"✅ Documento RAG generado: {rag_file}")
        
        explorer.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_rag_document(metadata):
    """Generar documento optimizado para RAG."""
    
    content = []
    
    # Header
    content.append("# METADATA MEJORADA DE BASE DE DATOS SQL SERVER")
    content.append("# Sistema RAG - Extracto con Descripciones, Índices y Constraints")
    content.append("")
    
    # Overview
    overview = metadata['database_overview']
    content.append(f"## VISTA GENERAL")
    content.append(f"Base de datos: {overview.get('DATABASE_NAME', 'N/A')}")
    content.append(f"Total tablas: {overview.get('TOTAL_TABLES', 0)}")
    content.append(f"Total vistas: {overview.get('TOTAL_VIEWS', 0)}")
    content.append(f"Esquemas: {overview.get('TOTAL_SCHEMAS', 0)}")
    content.append("")
    
    # Prefijos Bantotal
    if 'bantotal_prefixes' in overview:
        content.append("## DISTRIBUCIÓN TABLAS BANTOTAL")
        for prefix_info in overview['bantotal_prefixes']:
            prefix = prefix_info.get('PREFIX', '')
            count = prefix_info.get('TABLE_COUNT', 0)
            content.append(f"{prefix}: {count} tablas")
        content.append("")
    
    # Tablas con metadata mejorada
    content.append("## TABLAS CON METADATA COMPLETA")
    content.append("")
    
    for table_name, table_data in metadata['tables_with_enhanced_metadata'].items():
        basic = table_data['basic_info']
        enhanced = table_data['enhanced_metadata']
        
        content.append(f"### TABLA {table_name}")
        content.append(f"Nombre completo: {basic['full_name']}")
        content.append(f"Total campos: {basic['column_count']}")
        content.append(f"Tiene PK: {'Sí' if basic['has_primary_key'] else 'No'}")
        
        if enhanced['table_description']:
            content.append(f"Descripción: {enhanced['table_description']}")
        
        content.append(f"Campos con descripción: {enhanced['fields_with_descriptions']}")
        content.append(f"Foreign Keys: {enhanced['foreign_keys_count']}")
        content.append(f"Índices: {enhanced['indexes_count']}")
        content.append(f"Constraints: {enhanced['constraints_count']}")
        content.append("")
        
        # Campos de muestra
        content.append("CAMPOS DE MUESTRA:")
        for field in table_data['sample_fields']:
            pk_indicator = " (PK)" if field['is_primary_key'] == 'YES' else ""
            description = field.get('description', '').strip()
            desc_text = f" - {description}" if description else ""
            content.append(f"  {field['name']}: {field['full_type']}{pk_indicator}{desc_text}")
        
        content.append("")
    
    # Footer
    extraction_info = metadata['extraction_info']
    content.append("## INFORMACIÓN DE EXTRACCIÓN")
    content.append(f"Timestamp: {extraction_info['timestamp']}")
    content.append("Características mejoradas:")
    for feature in extraction_info['enhanced_features']:
        content.append(f"  - {feature}")
    content.append("")
    content.append("Este documento contiene metadata mejorada para consultas RAG inteligentes")
    content.append("Incluye descripciones de campos, índices, foreign keys y constraints")
    
    return "\n".join(content)

if __name__ == "__main__":
    print("🚀 EXTRACCIÓN SQL CON METADATA MEJORADA")
    print("=" * 60)
    
    success = extract_enhanced_sql_metadata()
    
    if success:
        print("\n✅ EXTRACCIÓN COMPLETADA")
        print("📂 Archivos generados:")
        print("  • docs/enhanced_sql_metadata.json")
        print("  • docs/enhanced_sql_for_rag.txt")
        print("\n🔄 Siguiente paso:")
        print("  python3 src/indexer.py --force")
    else:
        print("\n❌ EXTRACCIÓN FALLÓ")
        print("🔧 Verifica la conexión SQL Server")
# fix_format_function.py - Agregar función faltante a ingestion.py

from pathlib import Path

def add_missing_function():
    """Agregar función _format_database_overview faltante"""
    
    print("🔧 Agregando función _format_database_overview...")
    
    ingestion_file = Path('src/ingestion.py')
    content = ingestion_file.read_text(encoding='utf-8')
    
    # Verificar si ya existe la función
    if '_format_database_overview' in content and 'def _format_database_overview' in content:
        print("✅ Función ya existe")
        return True
    
    # Función a agregar
    missing_function = '''
def _format_database_overview(overview: dict) -> str:
    """Formatear vista general de la base de datos para ingesta RAG."""
    if not overview:
        return "No se pudo obtener vista general de la base de datos."
    
    overview_text = f"""# 📊 Vista General de Base de Datos: {overview.get('database_name', 'N/A')}

## Resumen Ejecutivo
- **Base de datos:** {overview.get('database_name', 'N/A')}
- **Total de tablas:** {overview.get('total_tables', 0):,}
- **Total de vistas:** {overview.get('total_views', 0):,}
- **Esquemas activos:** {overview.get('total_schemas', 0)}
- **Fecha de extracción:** {overview.get('generated_at', '')[:19]}

## 🏗️ Arquitectura por Esquemas

Esta base de datos está organizada en {overview.get('total_schemas', 0)} esquemas principales:

"""
    
    # Top esquemas
    for schema in overview.get('top_schemas', [])[:10]:
        overview_text += f"### Esquema: {schema.get('schema', 'N/A')}\\n"
        overview_text += f"- **Tablas:** {schema.get('tables', 0)}\\n\\n"
    
    # Distribución Bantotal si existe
    if 'bantotal_prefixes' in overview:
        overview_text += "## 🏦 Distribución Tablas Bantotal\\n\\n"
        bantotal_descriptions = {
            'FST': 'Tablas Básicas - Genéricas',
            'FSD': 'Datos',
            'FSR': 'Relaciones', 
            'FSE': 'Extensiones',
            'FSH': 'Históricos',
            'FSX': 'Textos',
            'FSA': 'Auxiliares',
            'FSI': 'Informaciones',
            'FSM': 'Menús',
            'FSN': 'Numeradores'
        }
        
        for prefix_info in overview.get('bantotal_prefixes', [])[:10]:
            prefix = prefix_info.get('prefix', 'N/A')
            count = prefix_info.get('tables', 0)
            desc = bantotal_descriptions.get(prefix, 'Otras tablas')
            overview_text += f"- **{prefix}:** {count} tablas ({desc})\\n"
    
    # Tablas más complejas
    overview_text += "\\n## 🧩 Tablas Principales por Complejidad\\n\\n"
    
    for table in overview.get('most_complex_tables', [])[:15]:
        overview_text += f"- **{table.get('table', 'N/A')}:** {table.get('columns', 0)} campos\\n"
    
    overview_text += f"""

## 🔍 Guía de Búsqueda de Tablas

Para encontrar información específica sobre tablas en esta base de datos:

1. **Búsqueda por funcionalidad Bantotal:**
   - Básicas: buscar "FST", "Fst001", "tablas básicas"
   - Datos: buscar "FSD", "Fsd601", "servicios"
   - Relaciones: buscar "FSR", "relaciones"
   - Extensiones: buscar "FSE", "extensiones"

2. **Consultas SQL recomendadas:**
   ```sql
   -- Buscar tabla específica
   SELECT TABLE_NAME, TABLE_SCHEMA 
   FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_NAME LIKE '%FST%' OR TABLE_NAME LIKE '%FSD%';
   
   -- Ver estructura de tabla encontrada
   SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
   FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_NAME = 'nombre_tabla_encontrada'
   ORDER BY ORDINAL_POSITION;
   ```

Este documento fue generado automáticamente como parte del sistema RAG Bantotal.
"""
    
    return overview_text


def _create_table_batches(all_tables: list, batch_size: int) -> list:
    """Crear lotes de tablas para procesamiento eficiente."""
    if not all_tables:
        return []
    
    # Ordenar por relevancia si tienen ese campo
    try:
        sorted_tables = sorted(all_tables, key=lambda t: t.get('relevance', 0), reverse=True)
    except:
        sorted_tables = all_tables
    
    # Crear lotes
    batches = []
    for i in range(0, len(sorted_tables), batch_size):
        batch = sorted_tables[i:i + batch_size]
        batches.append(batch)
    
    return batches


def _process_table_batch(explorer, batch_tables: list, batch_num: int) -> list:
    """Procesar un lote de tablas de manera eficiente."""
    batch_docs = []
    
    for table_info in batch_tables:
        try:
            table_name = table_info.get('table_name', '')
            schema = table_info.get('schema', 'dbo')
            full_name = table_info.get('full_name', f"{schema}.{table_name}")
            
            if not table_name:
                continue
                
            # Obtener estructura completa
            structure = explorer.get_table_structure(table_name, schema)
            
            if structure:
                # Generar documentación de la tabla
                table_doc = _format_table_documentation(structure)
                
                # Metadatos para RAG
                table_metadata = {
                    'source': f"sql_server://localhost/bttest",
                    'source_type': 'database_table',
                    'filename': f"{full_name.replace('.', '_')}_structure.md",
                    'file_type': '.md',
                    'table_name': table_name,
                    'schema_name': schema,
                    'full_table_name': full_name,
                    'column_count': structure.get('column_count', 0),
                    'batch_number': batch_num,
                    'document_type': 'table_structure'
                }
                
                batch_docs.append((table_doc, table_metadata))
                
        except Exception as e:
            print(f"⚠️ Error procesando tabla {table_info.get('full_name', 'unknown')}: {e}")
    
    return batch_docs


def _format_table_documentation(structure: dict) -> str:
    """Formatear documentación completa de una tabla para RAG."""
    if not structure:
        return "Error: estructura de tabla vacía"
        
    full_name = structure.get('full_name', 'N/A')
    table_name = structure.get('table_name', 'N/A')
    schema = structure.get('schema', 'dbo')
    columns = structure.get('columns', [])
    
    doc_text = f"""# 🗂️ Tabla: {full_name}

## Información General
- **Esquema:** {schema}
- **Nombre de tabla:** {table_name}
- **Nombre completo:** {full_name}
- **Total de campos:** {len(columns)}

## 📋 Estructura Completa de Campos

| Pos | Campo | Tipo | Nulos | Default |
|-----|-------|------|-------|---------|
"""
    
    for i, col in enumerate(columns, 1):
        name = col.get('name', f'campo_{i}')
        full_type = col.get('full_type', col.get('data_type', 'unknown'))
        nullable = "✅" if col.get('nullable', True) else "❌"
        default = col.get('default', '') or ''
        
        doc_text += f"| {i} | `{name}` | {full_type} | {nullable} | {default} |\\n"
    
    doc_text += f"""

## 🔍 Query SELECT de Ejemplo

```sql
-- Query para tabla {full_name}
SELECT TOP 100
"""

    # Agregar columnas al SELECT
    for i, col in enumerate(columns):
        name = col.get('name', f'campo_{i}')
        if i < len(columns) - 1:
            doc_text += f"    {name},\\n"
        else:
            doc_text += f"    {name}\\n"
    
    doc_text += f"""FROM {full_name}
ORDER BY {columns[0].get('name', 'id') if columns else '1'};
```

## 💡 Sugerencias de Consulta

**Búsqueda básica:**
```sql
SELECT * FROM {full_name} WHERE [condicion];
```

---
*Documentación generada automáticamente para facilitar consultas RAG sobre {full_name}.*
"""
    
    return doc_text


def _extract_schema_documentation(explorer, top_schemas: list) -> list:
    """Extraer documentación de esquemas principales."""
    return []  # Implementación simplificada


def _basic_sql_extraction() -> list:
    """Extracción básica de metadatos SQL (fallback)."""
    return []  # Implementación simplificada

'''
    
    # Buscar lugar para insertar la función
    lines = content.split('\n')
    insert_pos = -1
    
    # Buscar después de las funciones auxiliares integradas
    for i, line in enumerate(lines):
        if 'def _load_from_sql_server():' in line:
            insert_pos = i
            break
    
    if insert_pos == -1:
        # Si no encuentra lugar específico, insertar después de imports
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('import') and not line.startswith('from') and not line.startswith('#'):
                insert_pos = i
                break
    
    if insert_pos != -1:
        # Insertar función
        function_lines = missing_function.strip().split('\n')
        lines[insert_pos:insert_pos] = function_lines
        
        # Guardar archivo
        new_content = '\n'.join(lines)
        ingestion_file.write_text(new_content, encoding='utf-8')
        print("✅ Función _format_database_overview agregada")
        return True
    else:
        print("❌ No se pudo encontrar lugar para insertar función")
        return False

if __name__ == "__main__":
    print("🔧 CORRIGIENDO FUNCIÓN FALTANTE")
    print("=" * 40)
    
    if add_missing_function():
        print("\n🎉 ¡Función agregada exitosamente!")
        print("💡 Ahora ejecuta:")
        print("   python src/indexer.py --force")
        print("   python rag.py \"SELECT tabla FPP096\"")
    else:
        print("\n❌ Error agregando función")
        print("💡 El sistema sigue funcionando sin esta función")
# bantotal_config.py - Configuración específica para miles de tablas Bantotal

import os
import json
import sys
from pathlib import Path

def fix_database_explorer_import():
    """Corregir problema de importación en database_explorer.py"""
    
    print("🔧 Corrigiendo database_explorer.py...")
    
    explorer_file = Path('src/database_explorer.py')
    
    if not explorer_file.exists():
        print("❌ database_explorer.py no existe, recreando...")
        return create_minimal_database_explorer()
    
    try:
        # Intentar importar para verificar
        sys.path.append('src')
        from database_explorer import DatabaseExplorer
        print("✅ DatabaseExplorer importa correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en DatabaseExplorer: {e}")
        print("🔄 Recreando archivo...")
        return create_minimal_database_explorer()

def create_minimal_database_explorer():
    """Crear database_explorer.py mínimo pero funcional"""
    
    explorer_content = '''# src/database_explorer.py
"""
Explorador de Base de Datos - Optimizado para Bantotal
Maneja miles de tablas FST, FSD, FSR, FSE, FSH, FSX, FSA, FSI, FSM, FSN
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# Verificar dependencias SQL
try:
    import pyodbc
    from sqlalchemy import create_engine, text
    HAS_SQL = True
except ImportError:
    HAS_SQL = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class DatabaseExplorer:
    """Explorador optimizado para bases de datos Bantotal."""
    
    def __init__(self):
        if not HAS_SQL:
            raise ImportError("pyodbc y sqlalchemy requeridos")
            
        self.connection_string = self._build_connection_string()
        self.engine = None
        self.stats = {'tables_processed': 0, 'total_query_time': 0}
    
    def _build_connection_string(self) -> str:
        """Construir string de conexión."""
        host = os.getenv('SQL_SERVER_HOST', 'localhost')
        port = os.getenv('SQL_SERVER_PORT', '1433')
        database = os.getenv('SQL_SERVER_DATABASE')
        username = os.getenv('SQL_SERVER_USERNAME')
        password = os.getenv('SQL_SERVER_PASSWORD')
        driver = os.getenv('SQL_SERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        
        if not database:
            raise ValueError("SQL_SERVER_DATABASE requerido en .env")
        
        if username and password:
            return (
                f"mssql+pyodbc://{username}:{password}@"
                f"{host}:{port}/{database}"
                f"?driver={driver.replace(' ', '+')}&TrustServerCertificate=yes"
            )
        else:
            return (
                f"mssql+pyodbc://{host}:{port}/{database}"
                f"?driver={driver.replace(' ', '+')}&trusted_connection=yes&TrustServerCertificate=yes"
            )
    
    def connect(self) -> bool:
        """Establecer conexión."""
        try:
            self.engine = create_engine(self.connection_string, echo=False)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"❌ Error conexión: {e}")
            return False
    
    def get_database_overview(self) -> Dict:
        """Vista general con focus en tablas Bantotal."""
        if not self.engine and not self.connect():
            return {}
        
        try:
            with self.engine.connect() as conn:
                # Estadísticas generales
                overview_query = text("""
                    SELECT 
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                         WHERE TABLE_TYPE = 'BASE TABLE') as TOTAL_TABLES,
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.VIEWS) as TOTAL_VIEWS,
                        (SELECT COUNT(DISTINCT TABLE_SCHEMA) FROM INFORMATION_SCHEMA.TABLES) as TOTAL_SCHEMAS,
                        DB_NAME() as DATABASE_NAME
                """)
                
                result = conn.execute(overview_query).fetchone()
                
                # Análisis específico de tablas Bantotal
                bantotal_query = text("""
                    SELECT 
                        SUBSTRING(TABLE_NAME, 1, 3) as PREFIX,
                        COUNT(*) as TABLE_COUNT
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    AND TABLE_NAME LIKE 'FS[TDRSEHXAIMN]%'
                    GROUP BY SUBSTRING(TABLE_NAME, 1, 3)
                    ORDER BY COUNT(*) DESC
                """)
                
                bantotal_tables = conn.execute(bantotal_query).fetchall()
                
                # Esquemas principales
                schemas_query = text("""
                    SELECT TOP 10
                        TABLE_SCHEMA,
                        COUNT(*) as TABLE_COUNT
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    GROUP BY TABLE_SCHEMA
                    ORDER BY COUNT(*) DESC
                """)
                
                schemas = conn.execute(schemas_query).fetchall()
                
                return {
                    'database_name': result[3],
                    'total_tables': result[0],
                    'total_views': result[1],
                    'total_schemas': result[2],
                    'bantotal_prefixes': [{'prefix': b[0], 'tables': b[1]} for b in bantotal_tables],
                    'top_schemas': [{'schema': s[0], 'tables': s[1]} for s in schemas],
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error overview: {e}")
            return {}
    
    def search_tables(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Buscar tablas con optimización para Bantotal."""
        if not self.engine and not self.connect():
            return []
        
        try:
            with self.engine.connect() as conn:
                if not search_term.strip():
                    # Obtener todas las tablas priorizando Bantotal
                    search_query = text("""
                        SELECT TOP (:limit)
                            TABLE_SCHEMA,
                            TABLE_NAME,
                            TABLE_SCHEMA + '.' + TABLE_NAME as FULL_NAME,
                            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c 
                             WHERE c.TABLE_NAME = t.TABLE_NAME AND c.TABLE_SCHEMA = t.TABLE_SCHEMA) as COLUMN_COUNT,
                            CASE 
                                WHEN TABLE_NAME LIKE 'FST%' THEN 100  -- Tablas Básicas
                                WHEN TABLE_NAME LIKE 'FSD%' THEN 90   -- Datos
                                WHEN TABLE_NAME LIKE 'FSR%' THEN 80   -- Relaciones
                                WHEN TABLE_NAME LIKE 'FSE%' THEN 70   -- Extensiones
                                WHEN TABLE_NAME LIKE 'FSH%' THEN 60   -- Históricos
                                WHEN TABLE_NAME LIKE 'FSX%' THEN 50   -- Textos
                                WHEN TABLE_NAME LIKE 'FSA%' THEN 40   -- Auxiliares
                                WHEN TABLE_NAME LIKE 'FSI%' THEN 30   -- Informaciones
                                WHEN TABLE_NAME LIKE 'FSM%' THEN 20   -- Menús
                                WHEN TABLE_NAME LIKE 'FSN%' THEN 10   -- Numeradores
                                ELSE 5
                            END as RELEVANCE_SCORE
                        FROM INFORMATION_SCHEMA.TABLES t
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        ORDER BY RELEVANCE_SCORE DESC, TABLE_NAME
                    """)
                    params = {'limit': limit}
                else:
                    search_query = text("""
                        SELECT TOP (:limit)
                            TABLE_SCHEMA,
                            TABLE_NAME,
                            TABLE_SCHEMA + '.' + TABLE_NAME as FULL_NAME,
                            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c 
                             WHERE c.TABLE_NAME = t.TABLE_NAME AND c.TABLE_SCHEMA = t.TABLE_SCHEMA) as COLUMN_COUNT,
                            CASE 
                                WHEN TABLE_NAME = :exact_term THEN 1000
                                WHEN TABLE_NAME LIKE :exact_pattern THEN 900
                                WHEN TABLE_NAME LIKE 'FST%' AND TABLE_NAME LIKE :contains_pattern THEN 800
                                WHEN TABLE_NAME LIKE 'FSD%' AND TABLE_NAME LIKE :contains_pattern THEN 700
                                WHEN TABLE_NAME LIKE :start_pattern THEN 600
                                WHEN TABLE_NAME LIKE :contains_pattern THEN 500
                                ELSE 100
                            END as RELEVANCE_SCORE
                        FROM INFORMATION_SCHEMA.TABLES t
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        AND (
                            TABLE_NAME LIKE :contains_pattern 
                            OR TABLE_SCHEMA LIKE :contains_pattern
                        )
                        ORDER BY RELEVANCE_SCORE DESC, TABLE_NAME
                    """)
                    params = {
                        'limit': limit,
                        'exact_term': search_term.upper(),
                        'exact_pattern': f'{search_term.upper()}',
                        'start_pattern': f'{search_term.upper()}%',
                        'contains_pattern': f'%{search_term.upper()}%'
                    }
                
                results = conn.execute(search_query, params).fetchall()
                
                return [
                    {
                        'schema': row[0],
                        'table_name': row[1],
                        'full_name': row[2],
                        'column_count': row[3],
                        'relevance': row[4]
                    }
                    for row in results
                ]
                
        except Exception as e:
            print(f"❌ Error búsqueda: {e}")
            return []
    
    def get_table_structure(self, table_name: str, schema: str = None) -> Optional[Dict]:
        """Obtener estructura de tabla."""
        if '.' in table_name and not schema:
            schema, table_name = table_name.split('.', 1)
        
        if not self.engine and not self.connect():
            return None
        
        try:
            with self.engine.connect() as conn:
                structure_query = text("""
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        ISNULL(c.CHARACTER_MAXIMUM_LENGTH, 0) as MAX_LENGTH,
                        ISNULL(c.NUMERIC_PRECISION, 0) as PRECISION,
                        ISNULL(c.NUMERIC_SCALE, 0) as SCALE,
                        c.IS_NULLABLE,
                        c.COLUMN_DEFAULT,
                        c.ORDINAL_POSITION
                    FROM INFORMATION_SCHEMA.COLUMNS c
                    WHERE c.TABLE_NAME = :table_name
                    """ + (f" AND c.TABLE_SCHEMA = :schema" if schema else "") + """
                    ORDER BY c.ORDINAL_POSITION
                """)
                
                params = {'table_name': table_name}
                if schema:
                    params['schema'] = schema
                
                columns = conn.execute(structure_query, params).fetchall()
                
                if not columns:
                    return None
                
                processed_columns = []
                for col in columns:
                    type_str = col[1]
                    if col[2] > 0:
                        type_str += f"({col[2]})" if col[2] != -1 else "(MAX)"
                    elif col[3] > 0:
                        if col[4] > 0:
                            type_str += f"({col[3]},{col[4]})"
                        else:
                            type_str += f"({col[3]})"
                    
                    processed_columns.append({
                        'name': col[0],
                        'data_type': col[1],
                        'full_type': type_str,
                        'nullable': col[5] == 'YES',
                        'default': col[6],
                        'position': col[7],
                        'key_type': None
                    })
                
                return {
                    'schema': schema or 'dbo',
                    'table_name': table_name,
                    'full_name': f"{schema or 'dbo'}.{table_name}",
                    'column_count': len(processed_columns),
                    'columns': processed_columns,
                    'primary_keys': [],
                    'foreign_keys': [],
                    'extracted_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error estructura {table_name}: {e}")
            return None
    
    def generate_select_query(self, table_name: str, schema: str = None, limit: int = 100) -> str:
        """Generar SELECT para tabla."""
        structure = self.get_table_structure(table_name, schema)
        if not structure:
            return f"-- Error: No se pudo obtener estructura de {table_name}"
        
        full_name = structure['full_name']
        columns = structure['columns']
        
        query_parts = [
            f"-- Query para tabla Bantotal: {full_name}",
            f"-- Total campos: {len(columns)}",
            f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"SELECT TOP {limit}"
        ]
        
        for i, col in enumerate(columns):
            col_line = f"    {col['name']}"
            if i < len(columns) - 1:
                col_line += ","
            query_parts.append(col_line)
        
        query_parts.extend([
            f"FROM {full_name}",
            f"ORDER BY {columns[0]['name']}"
        ])
        
        return "\\n".join(query_parts)
'''
    
    explorer_file = Path('src/database_explorer.py')
    explorer_file.write_text(explorer_content, encoding='utf-8')
    print("✅ database_explorer.py recreado para Bantotal")
    return True

def create_bantotal_extraction_strategy():
    """Crear estrategia específica para tablas Bantotal"""
    
    print("📋 Creando estrategia de extracción Bantotal...")
    
    strategy = {
        "description": "Estrategia de extracción para miles de tablas Bantotal",
        "bantotal_nomenclature": {
            "FST": "Tablas Básicas - Genéricas",
            "FSD": "Datos", 
            "FSR": "Relaciones",
            "FSE": "Extensiones",
            "FSH": "Históricos",
            "FSX": "Textos",
            "FSA": "Auxiliares", 
            "FSI": "Informaciones",
            "FSM": "Menús",
            "FSN": "Numeradores"
        },
        "extraction_phases": [
            {
                "phase": 1,
                "name": "Tablas Básicas Bantotal",
                "patterns": ["FST"],
                "priority": "CRITICAL",
                "batch_size": 100,
                "description": "Tablas genéricas fundamentales del sistema"
            },
            {
                "phase": 2,
                "name": "Datos Core",
                "patterns": ["FSD"],
                "priority": "HIGH",
                "batch_size": 150,
                "description": "Tablas de datos principales"
            },
            {
                "phase": 3,
                "name": "Relaciones y Extensiones",
                "patterns": ["FSR", "FSE"],
                "priority": "HIGH", 
                "batch_size": 200,
                "description": "Tablas de relaciones y extensiones"
            },
            {
                "phase": 4,
                "name": "Información y Auxiliares",
                "patterns": ["FSI", "FSA"],
                "priority": "MEDIUM",
                "batch_size": 250,
                "description": "Tablas de información y auxiliares"
            },
            {
                "phase": 5,
                "name": "Históricos y Textos",
                "patterns": ["FSH", "FSX"],
                "priority": "LOW",
                "batch_size": 300,
                "description": "Tablas de históricos y textos"
            },
            {
                "phase": 6,
                "name": "Menús y Numeradores",
                "patterns": ["FSM", "FSN"],
                "priority": "LOW",
                "batch_size": 200,
                "description": "Tablas de menús y numeradores"
            }
        ],
        "search_optimizations": {
            "common_queries": [
                "FST001", "FST002", "FST003",  # Tablas básicas comunes
                "FSD601", "FSD602", "FSD603",  # Servicios
                "FSE001", "FSE002",            # Extensiones
                "ABONADO", "CLIENTE", "CUENTA", "SERVICIO"
            ],
            "priority_patterns": ["FST", "FSD", "FSR", "FSE"]
        }
    }
    
    strategy_file = Path('bantotal_extraction_strategy.json')
    strategy_file.write_text(
        json.dumps(strategy, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    print(f"✅ Estrategia Bantotal guardada: {strategy_file}")
    return True

def test_bantotal_connection():
    """Probar conexión y analizar tablas Bantotal"""
    
    print("🔍 Analizando base de datos Bantotal...")
    
    try:
        sys.path.append('src')
        from database_explorer import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar")
            return False
        
        overview = explorer.get_database_overview()
        
        if overview:
            print(f"\n📊 ANÁLISIS BANTOTAL:")
            print(f"   📋 Total tablas: {overview['total_tables']:,}")
            print(f"   🏦 Base de datos: {overview['database_name']}")
            
            if 'bantotal_prefixes' in overview:
                print(f"\n🎯 Distribución tablas Bantotal:")
                bantotal_total = 0
                for prefix_info in overview['bantotal_prefixes']:
                    prefix = prefix_info['prefix']
                    count = prefix_info['tables']
                    bantotal_total += count
                    
                    descriptions = {
                        'FST': 'Tablas Básicas',
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
                    
                    desc = descriptions.get(prefix, 'Otras')
                    print(f"   {prefix}: {count:,} tablas ({desc})")
                
                print(f"\n🎯 Total tablas Bantotal: {bantotal_total:,}")
                percentage = (bantotal_total / overview['total_tables']) * 100
                print(f"📊 Porcentaje Bantotal: {percentage:.1f}%")
            
            # Buscar tabla específica
            print(f"\n🔍 Buscando FSD601...")
            fsd601_results = explorer.search_tables("FSD601", limit=5)
            if fsd601_results:
                print(f"✅ Encontrada FSD601:")
                for result in fsd601_results:
                    print(f"   📋 {result['full_name']} ({result['column_count']} campos)")
            else:
                print(f"❌ FSD601 no encontrada")
            
            return True
        else:
            print("❌ No se pudo obtener overview")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Configurar sistema para Bantotal"""
    
    print("🏦 CONFIGURACIÓN ESPECÍFICA BANTOTAL")
    print("=" * 50)
    
    success_count = 0
    
    # 1. Corregir database_explorer
    if fix_database_explorer_import():
        success_count += 1
    
    # 2. Crear estrategia Bantotal
    if create_bantotal_extraction_strategy():
        success_count += 1
    
    # 3. Probar conexión
    if test_bantotal_connection():
        success_count += 1
    
    print(f"\n📊 RESULTADO:")
    print(f"   Configuraciones exitosas: {success_count}/3")
    
    if success_count >= 2:
        print(f"\n🎉 ¡Sistema configurado para Bantotal!")
        print(f"💡 El sistema ahora entiende la nomenclatura:")
        print(f"   🏗️ FST = Tablas Básicas")
        print(f"   📊 FSD = Datos (ej: FSD601)")
        print(f"   🔗 FSR = Relaciones")
        print(f"   📈 FSE = Extensiones")
        print(f"   📚 FSH = Históricos")
        
        print(f"\n🚀 Próximo paso:")
        print(f"   python src/indexer.py --force")
        
        print(f"\n🧪 Prueba consultas:")
        print(f"   python rag.py \"SELECT tabla FSD601\"")
        print(f"   python rag.py \"buscar tablas FST\"")
        print(f"   python rag.py \"estructura tabla servicios\"")
    else:
        print(f"\n⚠️ Revisar errores antes de continuar")

if __name__ == "__main__":
    main()
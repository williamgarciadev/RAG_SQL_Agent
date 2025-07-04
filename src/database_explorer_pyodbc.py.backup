# src/database_explorer.py
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
    
    def generate_select_query(self, table_name: str, schema: str = None, limit: int = 100, 
                             include_joins: bool = True, join_type: str = 'LEFT') -> str:
        """Generar SELECT para tabla con JOINs inteligentes."""
        structure = self.get_table_structure(table_name, schema)
        if not structure:
            return f"-- Error: No se pudo obtener estructura de {table_name}"
        
        full_name = structure['full_name']
        columns = structure['columns']
        
        # Detectar relaciones para JOINs automáticos
        joins_info = self._detect_table_relationships(table_name, schema) if include_joins else []
        
        query_parts = [
            f"-- Query optimizada para tabla Bantotal: {full_name}",
            f"-- Total campos: {len(columns)}",
            f"-- JOINs detectados: {len(joins_info)}",
            f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"SELECT TOP {limit}"
        ]
        
        # Agregar campos de la tabla principal
        main_alias = self._get_table_alias(table_name)
        for i, col in enumerate(columns):
            col_line = f"    {main_alias}.{col['name']}"
            if i < len(columns) - 1 or joins_info:
                col_line += ","
            query_parts.append(col_line)
        
        # Agregar campos de tablas relacionadas
        for join_info in joins_info:
            related_cols = self._get_essential_columns(join_info['related_table'])
            for j, col in enumerate(related_cols):
                col_line = f"    {join_info['alias']}.{col} AS {join_info['alias']}_{col}"
                if j < len(related_cols) - 1 or join_info != joins_info[-1]:
                    col_line += ","
                query_parts.append(col_line)
        
        # FROM con alias
        query_parts.append(f"FROM {full_name} {main_alias}")
        
        # Agregar JOINs
        for join_info in joins_info:
            join_line = f"{join_type} JOIN {join_info['related_table']} {join_info['alias']}"
            join_line += f" ON {main_alias}.{join_info['foreign_key']} = {join_info['alias']}.{join_info['primary_key']}"
            query_parts.append(join_line)
        
        # ORDER BY inteligente
        order_by_clause = self._generate_smart_order_by(columns, main_alias)
        query_parts.append(order_by_clause)
        
        # Agregar ejemplos de filtros comunes
        if self._is_bantotal_table(table_name):
            query_parts.extend(self._generate_bantotal_filters(table_name, main_alias))
        
        return "\n".join(query_parts)
    
    def _detect_table_relationships(self, table_name: str, schema: str = None) -> List[Dict]:
        """Detectar relaciones FK para generar JOINs automáticos."""
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                # Buscar Foreign Keys de la tabla
                fk_query = text("""
                    SELECT 
                        fk.name AS constraint_name,
                        OBJECT_NAME(fk.parent_object_id) AS table_name,
                        COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS column_name,
                        OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
                        COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column
                    FROM sys.foreign_keys fk
                    INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                    WHERE OBJECT_NAME(fk.parent_object_id) = :table_name
                """)
                
                fk_results = conn.execute(fk_query, {'table_name': table_name}).fetchall()
                
                relationships = []
                for fk in fk_results:
                    alias = self._get_table_alias(fk[3])
                    relationships.append({
                        'constraint_name': fk[0],
                        'foreign_key': fk[2],
                        'related_table': fk[3],
                        'primary_key': fk[4],
                        'alias': alias
                    })
                
                return relationships[:3]  # Limitar a 3 JOINs para mantener legibilidad
                
        except Exception as e:
            print(f"❌ Error detectando relaciones para {table_name}: {e}")
            return []
    
    def _get_table_alias(self, table_name: str) -> str:
        """Generar alias inteligente para tabla."""
        if table_name.startswith('FST'):
            return 'tb'  # Tabla Básica
        elif table_name.startswith('FSD'):
            return 'dt'  # Datos
        elif table_name.startswith('FSR'):
            return 'rl'  # Relaciones
        elif table_name.startswith('FSE'):
            return 'ex'  # Extensiones
        elif table_name.startswith('FSH'):
            return 'hs'  # Históricos
        elif table_name.startswith('FSA'):
            return 'ax'  # Auxiliares
        else:
            # Generar alias basado en las primeras letras
            return ''.join([c.lower() for c in table_name[:3] if c.isalpha()])
    
    def _get_essential_columns(self, table_name: str) -> List[str]:
        """Obtener columnas esenciales de una tabla relacionada."""
        # Patrones comunes para columnas importantes
        essential_patterns = [
            'nombre', 'descripcion', 'codigo', 'id', 'estado', 'fecha',
            'activo', 'vigente', 'tipo', 'categoria'
        ]
        
        structure = self.get_table_structure(table_name)
        if not structure:
            return []
        
        essential_cols = []
        for col in structure['columns'][:5]:  # Primeras 5 columnas
            col_name = col['name'].lower()
            if any(pattern in col_name for pattern in essential_patterns):
                essential_cols.append(col['name'])
        
        return essential_cols[:3]  # Máximo 3 columnas por JOIN
    
    def _generate_smart_order_by(self, columns: List[Dict], alias: str) -> str:
        """Generar ORDER BY inteligente."""
        # Buscar columnas de orden prioritario
        priority_patterns = [
            'fecha', 'id', 'codigo', 'numero', 'secuencia',
            'orden', 'prioridad', 'estado'
        ]
        
        order_columns = []
        
        # Buscar columnas con patrones prioritarios
        for pattern in priority_patterns:
            for col in columns:
                if pattern in col['name'].lower() and col['name'] not in [oc.split('.')[-1] for oc in order_columns]:
                    order_columns.append(f"{alias}.{col['name']}")
                    if len(order_columns) >= 2:
                        break
            if len(order_columns) >= 2:
                break
        
        # Si no se encontraron columnas prioritarias, usar las primeras
        if not order_columns:
            order_columns = [f"{alias}.{columns[0]['name']}"]
        
        return f"ORDER BY {', '.join(order_columns)}"
    
    def _is_bantotal_table(self, table_name: str) -> bool:
        """Verificar si es tabla Bantotal."""
        return table_name.upper().startswith(('FST', 'FSD', 'FSR', 'FSE', 'FSH', 'FSX', 'FSA', 'FSI', 'FSM', 'FSN'))
    
    def _generate_bantotal_filters(self, table_name: str, alias: str) -> List[str]:
        """Generar filtros comunes para tablas Bantotal."""
        filters = [
            "",
            "-- Filtros comunes para tabla Bantotal:",
        ]
        
        if table_name.startswith('FSD'):
            filters.extend([
                f"-- WHERE {alias}.estado = 'ACTIVO'",
                f"-- WHERE {alias}.fecha_vigencia >= GETDATE()",
                f"-- WHERE {alias}.sucursal = 1"
            ])
        elif table_name.startswith('FST'):
            filters.extend([
                f"-- WHERE {alias}.activo = 1",
                f"-- WHERE {alias}.fecha_proceso = CONVERT(DATE, GETDATE())"
            ])
        else:
            filters.extend([
                f"-- WHERE {alias}.estado IN ('ACTIVO', 'VIGENTE')",
                f"-- WHERE {alias}.fecha_creacion >= '2024-01-01'"
            ])
        
        return filters

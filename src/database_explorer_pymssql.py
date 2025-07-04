# src/database_explorer_pymssql.py
"""
Explorador de Base de Datos - Optimizado para Bantotal usando pymssql
Maneja miles de tablas FST, FSD, FSR, FSE, FSH, FSX, FSA, FSI, FSM, FSN
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# Verificar dependencias SQL
try:
    import pymssql
    HAS_SQL = True
except ImportError:
    HAS_SQL = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class DatabaseExplorer:
    """Explorador optimizado para bases de datos Bantotal usando pymssql."""
    
    def __init__(self):
        if not HAS_SQL:
            raise ImportError("pymssql requerido")
        
        self.connection = None
        self.stats = {'tables_processed': 0, 'total_query_time': 0}
    
    def connect(self) -> bool:
        """Establecer conexión usando pymssql."""
        try:
            host = os.getenv('SQL_SERVER_HOST', 'localhost')
            port = int(os.getenv('SQL_SERVER_PORT', '1433'))
            database = os.getenv('SQL_SERVER_DATABASE')
            username = os.getenv('SQL_SERVER_USERNAME')
            password = os.getenv('SQL_SERVER_PASSWORD')
            
            if not all([database, username, password]):
                raise ValueError("Configuración SQL incompleta en .env")
            
            self.connection = pymssql.connect(
                server=host,
                port=port,
                user=username,
                password=password,
                database=database
            )
            
            # Probar conexión
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error conexión: {e}")
            return False
    
    def execute_query(self, query: str) -> List[Dict]:
        """Ejecutar consulta y retornar resultados como lista de diccionarios."""
        if not self.connection and not self.connect():
            return []
        
        try:
            cursor = self.connection.cursor(as_dict=True)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results if results else []
        except Exception as e:
            print(f"❌ Error ejecutando consulta: {e}")
            print(f"🔍 Query: {query[:200]}...")
            return []
    
    def search_tables(self, search_term: str = "", limit: int = 20) -> List[Dict]:
        """Buscar tablas con término específico."""
        if not self.connection and not self.connect():
            return []
        
        # Query para buscar tablas
        if search_term:
            query = f"""
            SELECT 
                TABLE_SCHEMA as schema_name,
                TABLE_NAME as table_name,
                TABLE_SCHEMA + '.' + TABLE_NAME as full_name,
                (SELECT COUNT(*) 
                 FROM INFORMATION_SCHEMA.COLUMNS c 
                 WHERE c.TABLE_NAME = t.TABLE_NAME 
                 AND c.TABLE_SCHEMA = t.TABLE_SCHEMA) as column_count
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND (TABLE_NAME LIKE '%{search_term}%' OR TABLE_NAME = '{search_term}')
            ORDER BY 
                CASE 
                    WHEN TABLE_NAME = '{search_term}' THEN 0
                    WHEN TABLE_NAME LIKE 'FST%' THEN 1
                    WHEN TABLE_NAME LIKE 'FSD%' THEN 2  
                    WHEN TABLE_NAME LIKE 'FSR%' THEN 3
                    WHEN TABLE_NAME LIKE 'FSE%' THEN 4
                    ELSE 5
                END,
                TABLE_NAME
            """
        else:
            query = f"""
            SELECT TOP {limit}
                TABLE_SCHEMA as schema_name,
                TABLE_NAME as table_name,
                TABLE_SCHEMA + '.' + TABLE_NAME as full_name,
                (SELECT COUNT(*) 
                 FROM INFORMATION_SCHEMA.COLUMNS c 
                 WHERE c.TABLE_NAME = t.TABLE_NAME 
                 AND c.TABLE_SCHEMA = t.TABLE_SCHEMA) as column_count
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY 
                CASE 
                    WHEN TABLE_NAME LIKE 'FST%' THEN 1
                    WHEN TABLE_NAME LIKE 'FSD%' THEN 2  
                    WHEN TABLE_NAME LIKE 'FSR%' THEN 3
                    WHEN TABLE_NAME LIKE 'FSE%' THEN 4
                    ELSE 5
                END,
                TABLE_NAME
            """
        
        return self.execute_query(query)
    
    def get_table_structure(self, table_name: str, schema: str = 'dbo') -> Optional[Dict]:
        """Obtener estructura completa de una tabla incluyendo PKs."""
        if not self.connection and not self.connect():
            return None
        
        # Query para obtener estructura completa con descripciones
        structure_query = f"""
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
        
        columns = self.execute_query(structure_query)
        
        if not columns:
            return None
        
        # Obtener información de PKs
        pk_query = f"""
        SELECT 
            ku.COLUMN_NAME,
            ku.ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku 
            ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        WHERE tc.TABLE_NAME = '{table_name}'
        AND tc.TABLE_SCHEMA = '{schema}'
        AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY ku.ORDINAL_POSITION
        """
        
        primary_keys = self.execute_query(pk_query)
        
        # Obtener metadata adicional
        metadata = self._get_additional_metadata(table_name, schema)
        
        return {
            'table_name': table_name,
            'schema': schema,
            'full_name': f"{schema}.{table_name}",
            'column_count': len(columns),
            'columns': columns,
            'primary_keys': [pk['COLUMN_NAME'] for pk in primary_keys],
            'has_primary_key': len(primary_keys) > 0,
            'foreign_keys': metadata.get('foreign_keys', []),
            'indexes': metadata.get('indexes', []),
            'constraints': metadata.get('constraints', []),
            'table_description': metadata.get('table_description', '')
        }
    
    def _get_additional_metadata(self, table_name: str, schema: str = 'dbo') -> Dict:
        """Obtener metadata adicional: foreign keys, índices, constraints."""
        metadata = {
            'foreign_keys': [],
            'indexes': [],
            'constraints': [],
            'table_description': ''
        }
        
        try:
            # 1. Foreign Keys
            fk_query = f"""
            SELECT 
                kcu.COLUMN_NAME as column_name,
                kcu.CONSTRAINT_NAME as constraint_name,
                kcu2.TABLE_SCHEMA as referenced_schema,
                kcu2.TABLE_NAME as referenced_table,
                kcu2.COLUMN_NAME as referenced_column
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc 
                ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu2 
                ON rc.UNIQUE_CONSTRAINT_NAME = kcu2.CONSTRAINT_NAME
            WHERE kcu.TABLE_NAME = '{table_name}'
            AND kcu.TABLE_SCHEMA = '{schema}'
            ORDER BY kcu.ORDINAL_POSITION
            """
            
            fk_results = self.execute_query(fk_query)
            metadata['foreign_keys'] = fk_results
            
            # 2. Índices
            index_query = f"""
            SELECT 
                i.name as index_name,
                i.type_desc as index_type,
                i.is_unique,
                i.is_primary_key,
                STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID('{schema}.{table_name}')
            AND i.name IS NOT NULL
            GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
            ORDER BY i.is_primary_key DESC, i.is_unique DESC
            """
            
            index_results = self.execute_query(index_query)
            metadata['indexes'] = index_results
            
            # 3. Constraints adicionales
            constraint_query = f"""
            SELECT 
                tc.CONSTRAINT_NAME,
                tc.CONSTRAINT_TYPE,
                STRING_AGG(kcu.COLUMN_NAME, ', ') as columns
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.TABLE_NAME = '{table_name}'
            AND tc.TABLE_SCHEMA = '{schema}'
            GROUP BY tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE
            ORDER BY tc.CONSTRAINT_TYPE
            """
            
            constraint_results = self.execute_query(constraint_query)
            metadata['constraints'] = constraint_results
            
            # 4. Descripción de la tabla
            table_desc_query = f"""
            SELECT CAST(ep.value AS NVARCHAR(MAX)) as table_description
            FROM sys.extended_properties ep
            WHERE ep.major_id = OBJECT_ID('{schema}.{table_name}')
            AND ep.minor_id = 0
            AND ep.name = 'MS_Description'
            """
            
            table_desc_results = self.execute_query(table_desc_query)
            if table_desc_results:
                metadata['table_description'] = table_desc_results[0].get('table_description', '')
            
        except Exception as e:
            print(f"⚠️ Error obteniendo metadata adicional: {e}")
        
        return metadata
    
    def get_database_overview(self) -> Dict:
        """Vista general con focus en tablas Bantotal."""
        if not self.connection and not self.connect():
            return {}
        
        # Estadísticas generales
        overview_query = """
        SELECT 
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
             WHERE TABLE_TYPE = 'BASE TABLE') as TOTAL_TABLES,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.VIEWS) as TOTAL_VIEWS,
            (SELECT COUNT(DISTINCT TABLE_SCHEMA) FROM INFORMATION_SCHEMA.TABLES) as TOTAL_SCHEMAS,
            DB_NAME() as DATABASE_NAME
        """
        
        general_stats = self.execute_query(overview_query)
        
        # Análisis específico de tablas Bantotal
        bantotal_query = """
        SELECT 
            SUBSTRING(TABLE_NAME, 1, 3) as PREFIX,
            COUNT(*) as TABLE_COUNT
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_NAME LIKE 'FS[TDRSEHXAIMN]%'
        GROUP BY SUBSTRING(TABLE_NAME, 1, 3)
        ORDER BY COUNT(*) DESC
        """
        
        bantotal_stats = self.execute_query(bantotal_query)
        
        if general_stats:
            overview = general_stats[0].copy()
            overview['bantotal_prefixes'] = bantotal_stats
            return overview
        
        return {}
    
    def close(self):
        """Cerrar conexión."""
        if self.connection:
            self.connection.close()
            self.connection = None

def search_fsd601():
    """Función específica para buscar FSD601 y mostrar su estructura con PKs"""
    print("🔍 Buscando tabla FSD601 con pymssql...")
    
    try:
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar a la base de datos")
            return
        
        print("✅ Conexión establecida")
        
        # Buscar tabla FSD601
        tables = explorer.search_tables("FSD601", limit=10)
        
        if tables:
            print(f"✅ Encontradas {len(tables)} tablas que contienen 'FSD601':")
            for table in tables:
                print(f"   • {table['full_name']} ({table['column_count']} campos)")
            
            # Obtener estructura de la primera tabla
            best_table = tables[0]
            print(f"\n🏗️ Estructura de {best_table['full_name']}:")
            
            structure = explorer.get_table_structure(
                best_table['table_name'], 
                best_table['schema_name']
            )
            
            if structure:
                print(f"📊 Total campos: {structure['column_count']}")
                
                if structure['has_primary_key']:
                    print(f"🔑 Claves primarias: {', '.join(structure['primary_keys'])}")
                else:
                    print("⚠️  No se encontraron claves primarias")
                
                print(f"\n📋 Campos (primeros 10):")
                for col in structure['columns'][:10]:
                    pk_indicator = " 🔑" if col['is_primary_key'] == 'YES' else ""
                    description = f" - {col['description']}" if col['description'] else ""
                    print(f"   • {col['name']}: {col['full_type']}{pk_indicator}{description}")
                
                if len(structure['columns']) > 10:
                    print(f"   ... y {len(structure['columns']) - 10} campos más")
            
        else:
            print("❌ No se encontró tabla FSD601")
            
            # Mostrar tablas disponibles
            print("\n🔍 Tablas disponibles (primeras 10):")
            all_tables = explorer.search_tables("", limit=10)
            if all_tables:
                for table in all_tables:
                    print(f"   • {table['full_name']}")
            else:
                print("❌ No se pudieron obtener las tablas")
        
        explorer.close()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_fsd601()
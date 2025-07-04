# force_sql_extraction.py - Forzar extracción de estructuras SQL reales

import sys
import os
from pathlib import Path
import time

def test_sql_connection_direct():
    """Probar conexión SQL directa"""
    
    print("🔍 Probando conexión directa a SQL Server...")
    
    try:
        import pyodbc
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Leer configuración
        host = os.getenv('SQL_SERVER_HOST', 'localhost')
        port = os.getenv('SQL_SERVER_PORT', '1433')
        database = os.getenv('SQL_SERVER_DATABASE', '')
        username = os.getenv('SQL_SERVER_USERNAME', '')
        password = os.getenv('SQL_SERVER_PASSWORD', '')
        
        print(f"📋 Conectando a: {host}:{port}/{database}")
        
        # Crear conexión
        connection_string = (
            f"mssql+pyodbc://{username}:{password}@"
            f"{host}:{port}/{database}"
            f"?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        )
        
        engine = create_engine(connection_string, echo=False)
        
        with engine.connect() as conn:
            # Probar conexión básica
            result = conn.execute(text("SELECT @@VERSION, DB_NAME()"))
            version, db_name = result.fetchone()
            
            print(f"✅ Conectado exitosamente")
            print(f"   Base de datos: {db_name}")
            print(f"   SQL Server: {version[:50]}...")
            
            # Contar tablas totales
            result = conn.execute(text("""
                SELECT COUNT(*) as total_tables 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """))
            total_tables = result.fetchone()[0]
            print(f"   Total tablas: {total_tables:,}")
            
            # Buscar tablas Bantotal específicas
            result = conn.execute(text("""
                SELECT 
                    SUBSTRING(TABLE_NAME, 1, 3) as PREFIX,
                    COUNT(*) as COUNT
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_NAME LIKE 'FS[TDRSEHXAIMN]%'
                GROUP BY SUBSTRING(TABLE_NAME, 1, 3)
                ORDER BY COUNT(*) DESC
            """))
            
            bantotal_tables = result.fetchall()
            if bantotal_tables:
                print(f"\n🏦 Tablas Bantotal encontradas:")
                total_bantotal = 0
                for prefix, count in bantotal_tables:
                    total_bantotal += count
                    print(f"   {prefix}: {count:,} tablas")
                print(f"   Total Bantotal: {total_bantotal:,}")
            
            # Buscar tabla específica con estructura detallada
            print(f"\n🔍 Buscando tabla con estructura similar a tu ejemplo...")
            
            # Buscar tablas que contengan campos típicos como los que mostraste
            result = conn.execute(text("""
                SELECT TOP 5
                    t.TABLE_NAME,
                    COUNT(c.COLUMN_NAME) as COLUMN_COUNT
                FROM INFORMATION_SCHEMA.TABLES t
                INNER JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
                WHERE t.TABLE_TYPE = 'BASE TABLE'
                AND (
                    c.COLUMN_NAME LIKE 'Pg%' OR 
                    c.COLUMN_NAME LIKE 'Pp%' OR
                    c.COLUMN_NAME LIKE 'D601%'
                )
                GROUP BY t.TABLE_NAME
                ORDER BY COUNT(c.COLUMN_NAME) DESC
            """))
            
            similar_tables = result.fetchall()
            if similar_tables:
                print(f"📋 Tablas con estructura similar:")
                for table_name, col_count in similar_tables:
                    print(f"   {table_name}: {col_count} campos similares")
                    
                # Obtener estructura de la primera tabla
                first_table = similar_tables[0][0]
                print(f"\n🔍 Estructura de {first_table}:")
                
                result = conn.execute(text(f"""
                    SELECT TOP 10
                        COLUMN_NAME,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{first_table}'
                    ORDER BY ORDINAL_POSITION
                """))
                
                columns = result.fetchall()
                for col_name, data_type, max_len, nullable in columns:
                    len_str = f"({max_len})" if max_len else ""
                    null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                    print(f"   {col_name}: {data_type}{len_str} {null_str}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def force_indexer_with_sql():
    """Forzar indexador para extraer estructuras SQL reales"""
    
    print("\n🚀 Forzando extracción de estructuras SQL reales...")
    
    try:
        # Ejecutar indexador con SQL habilitado
        os.system("python src/indexer.py --force")
        return True
    except Exception as e:
        print(f"❌ Error ejecutando indexador: {e}")
        return False

def verify_indexed_content():
    """Verificar que se indexaron las estructuras reales"""
    
    print("\n🔍 Verificando contenido indexado...")
    
    try:
        sys.path.append('src')
        from indexer import get_index_info, search_index, initialize_chroma_client
        
        # Inicializar cliente
        initialize_chroma_client()
        
        # Obtener info del índice
        info = get_index_info()
        
        if info.get('exists'):
            doc_count = info.get('live_count', 0)
            print(f"✅ Índice activo: {doc_count:,} documentos")
            
            # Buscar documentos SQL específicos
            sql_results = search_index("tabla estructura", top_k=5)
            
            if sql_results:
                print(f"📋 Documentos de estructura encontrados:")
                for i, result in enumerate(sql_results, 1):
                    metadata = result.get('metadata', {})
                    source_type = metadata.get('source_type', 'unknown')
                    filename = metadata.get('filename', 'N/A')
                    similarity = result.get('similarity', 0)
                    
                    print(f"   {i}. {filename} ({source_type}) - Similitud: {similarity:.3f}")
                    
                    # Mostrar preview del contenido si es estructura de BD
                    if source_type in ['database_table', 'database']:
                        preview = result.get('text', '')[:200]
                        print(f"      Preview: {preview}...")
            
            # Buscar tabla específica
            print(f"\n🔍 Buscando FSD601 en índice...")
            fsd_results = search_index("FSD601", top_k=3)
            
            if fsd_results:
                for result in fsd_results:
                    text = result.get('text', '')
                    if 'FSD601' in text and ('campo' in text.lower() or 'column' in text.lower()):
                        print(f"✅ Encontrada estructura real de FSD601")
                        print(f"   Preview: {text[:300]}...")
                        break
            else:
                print(f"⚠️ FSD601 no encontrada en índice")
            
            return doc_count > 0
        else:
            print(f"❌ Índice no existe")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando índice: {e}")
        return False

def test_final_query():
    """Probar consulta final con estructuras reales"""
    
    print("\n🧪 Probando consulta con estructuras reales...")
    
    try:
        # Simular consulta como lo haría rag.py
        sys.path.append('src')
        from sql_agent import SQLAgent
        
        agent = SQLAgent()
        result = agent.generate_sql_query("SELECT tabla con campos Pgcod Ppmod")
        
        if result.get('sql_generated'):
            print(f"✅ SQL generado con estructuras reales:")
            print(f"```sql")
            print(result['sql_generated'])
            print(f"```")
            
            if result.get('sources'):
                print(f"\n📚 Fuentes utilizadas:")
                for source in result['sources']:
                    print(f"   • {source.get('source', 'N/A')}")
            
            return True
        else:
            error = result.get('error', 'Error desconocido')
            print(f"❌ No se pudo generar SQL: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        return False

def main():
    """Ejecutar extracción completa de estructuras SQL"""
    
    print("🗄️ EXTRACCIÓN FORZADA DE ESTRUCTURAS SQL REALES")
    print("=" * 55)
    
    success_count = 0
    
    # 1. Probar conexión directa
    if test_sql_connection_direct():
        success_count += 1
    
    # 2. Forzar indexador
    print(f"\n" + "="*50)
    print(f"🚀 EJECUTANDO INDEXADOR COMPLETO...")
    print(f"⏱️ Esto puede tomar 10-20 minutos para miles de tablas")
    print(f"="*50)
    
    if force_indexer_with_sql():
        success_count += 1
    
    # 3. Verificar contenido indexado
    if verify_indexed_content():
        success_count += 1
    
    # 4. Probar consulta final
    if test_final_query():
        success_count += 1
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   Pasos completados: {success_count}/4")
    
    if success_count >= 3:
        print(f"\n🎉 ¡SISTEMA RAG BANCARIO COMPLETAMENTE OPERATIVO!")
        print(f"")
        print(f"🎯 Ahora puedes consultar MILES de tablas reales:")
        print(f"   python rag.py \"SELECT tabla con campos Pgcod\"")
        print(f"   python rag.py \"estructura tabla FSD601\"")
        print(f"   python rag.py \"buscar tablas con D601\"")
        print(f"   python rag.py \"generar INSERT para tabla con Ppmod\"")
        print(f"")
        print(f"🌐 Interfaz web:")
        print(f"   streamlit run src/app.py")
        print(f"")
        print(f"🏦 Tu sistema conoce la estructura REAL de tu BD Bantotal")
    else:
        print(f"\n⚠️ Sistema parcialmente operativo")
        print(f"💡 Revisar errores y reejecutar indexador si es necesario")

if __name__ == "__main__":
    main()
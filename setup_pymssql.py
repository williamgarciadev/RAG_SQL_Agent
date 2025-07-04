#!/usr/bin/env python3
"""
Configuración para usar pymssql en lugar de pyodbc
"""

import os
import sys
from pathlib import Path

def create_pymssql_config():
    """Crear configuración para pymssql"""
    
    # Crear archivo .env si no existe
    env_file = Path('.env')
    
    if not env_file.exists():
        print("🔧 Creando archivo .env...")
        
        env_content = """# RAG SQL Agent - Configuración
# Configuración Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2:latest

# Configuración SQL Server (usando pymssql)
SQL_SERVER_HOST=192.168.1.6
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=datoscabledb
SQL_SERVER_USERNAME=sa
SQL_SERVER_PASSWORD=Yg181008
SQL_SERVER_DRIVER=pymssql

# Configuración RAG
TOP_K_RESULTS=5
MIN_SIMILARITY=0.1
CHROMA_DB_DIR=chroma_db
CHROMA_COLLECTION=documents
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Configuración específica para pymssql
USE_PYMSSQL=true
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Archivo .env creado")
    else:
        print("ℹ️  Archivo .env ya existe")
        
        # Verificar si tiene configuración de pymssql
        with open(env_file, 'r') as f:
            content = f.read()
        
        if 'USE_PYMSSQL' not in content:
            print("🔧 Agregando configuración pymssql al .env...")
            with open(env_file, 'a') as f:
                f.write('\n# Configuración específica para pymssql\nUSE_PYMSSQL=true\n')
            print("✅ Configuración pymssql agregada")

def create_database_adapter():
    """Crear adaptador para pymssql"""
    
    adapter_content = '''"""
Adaptador de Base de Datos - Soporte para pymssql y pyodbc
"""

import os
from typing import Dict, List, Optional, Any

# Intentar importar drivers disponibles
HAS_PYMSSQL = False
HAS_PYODBC = False

try:
    import pymssql
    HAS_PYMSSQL = True
except ImportError:
    pass

try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    pass

class DatabaseAdapter:
    """Adaptador que funciona con pymssql o pyodbc"""
    
    def __init__(self):
        self.use_pymssql = os.getenv('USE_PYMSSQL', 'false').lower() == 'true'
        self.connection = None
        
        if self.use_pymssql and not HAS_PYMSSQL:
            raise ImportError("pymssql no está instalado")
        
        if not self.use_pymssql and not HAS_PYODBC:
            raise ImportError("pyodbc no está instalado")
    
    def connect(self):
        """Conectar usando el driver disponible"""
        host = os.getenv('SQL_SERVER_HOST', 'localhost')
        port = int(os.getenv('SQL_SERVER_PORT', '1433'))
        database = os.getenv('SQL_SERVER_DATABASE')
        username = os.getenv('SQL_SERVER_USERNAME')
        password = os.getenv('SQL_SERVER_PASSWORD')
        
        if not all([database, username, password]):
            raise ValueError("Configuración SQL incompleta en .env")
        
        if self.use_pymssql:
            self.connection = pymssql.connect(
                server=host,
                port=port,
                user=username,
                password=password,
                database=database
            )
        else:
            driver = os.getenv('SQL_SERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
            connection_string = f"""
            DRIVER={{{driver}}};
            SERVER={host};
            PORT={port};
            DATABASE={database};
            UID={username};
            PWD={password}
            """
            self.connection = pyodbc.connect(connection_string)
        
        return self.connection
    
    def execute_query(self, query: str) -> List[Dict]:
        """Ejecutar consulta y retornar resultados"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        # Obtener nombres de columnas
        columns = [desc[0] for desc in cursor.description]
        
        # Obtener datos
        rows = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        return results
    
    def close(self):
        """Cerrar conexión"""
        if self.connection:
            self.connection.close()
            self.connection = None

# Instancia global
db_adapter = DatabaseAdapter()
'''
    
    # Crear archivo del adaptador
    adapter_file = Path('src/database_adapter.py')
    with open(adapter_file, 'w') as f:
        f.write(adapter_content)
    
    print("✅ Adaptador de base de datos creado")

def test_setup():
    """Probar la configuración"""
    print("\n🔍 Probando configuración...")
    
    try:
        # Probar importación del adaptador
        sys.path.insert(0, 'src')
        from database_adapter import db_adapter
        
        # Probar conexión
        connection = db_adapter.connect()
        result = db_adapter.execute_query("SELECT 1 as test")
        
        print(f"✅ Conexión exitosa: {result[0]['test']}")
        
        db_adapter.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Configurar sistema para pymssql"""
    print("🎯" + "="*50 + "🎯")
    print("🔧 CONFIGURACIÓN PYMSSQL PARA RAG SQL AGENT")
    print("🎯" + "="*50 + "🎯")
    
    print("\n1. Creando configuración...")
    create_pymssql_config()
    
    print("\n2. Creando adaptador de base de datos...")
    create_database_adapter()
    
    print("\n3. Probando configuración...")
    if test_setup():
        print("\n🎉 ¡Configuración exitosa!")
        print("\n💡 Ahora puedes usar:")
        print("   python rag.py 'SELECT estructura de FSD601'")
        print("   python diagnose.py")
    else:
        print("\n❌ Error en configuración")
        print("🔧 Revisa los mensajes de error anteriores")

if __name__ == "__main__":
    main()
"""
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

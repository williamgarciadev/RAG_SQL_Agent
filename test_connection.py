#!/usr/bin/env python3
"""
Test simple de conexión a SQL Server
"""

def test_pyodbc_connection():
    """Test con pyodbc"""
    try:
        import pyodbc
        
        # Configurar tus datos aquí
        server = "192.168.1.6"  # IP de tu servidor Windows
        database = "datoscabledb"
        username = "sa"
        password = "Yg181008"
        
        # Intentar conexión
        connection_string = f"""
        DRIVER={{ODBC Driver 17 for SQL Server}};
        SERVER={server};
        DATABASE={database};
        UID={username};
        PWD={password}
        """
        
        print("🔍 Intentando conexión con pyodbc...")
        conn = pyodbc.connect(connection_string)
        
        # Test simple
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        print(f"✅ Conexión exitosa con pyodbc: {result[0]}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error con pyodbc: {e}")
        return False

def test_pymssql_connection():
    """Test con pymssql (alternativa)"""
    try:
        import pymssql
        
        # Configurar tus datos aquí
        server = "192.168.1.6"  # IP de tu servidor Windows
        database = "datoscabledb"
        username = "sa"
        password = "Yg181008"
        
        print("🔍 Intentando conexión con pymssql...")
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database
        )
        
        # Test simple
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        print(f"✅ Conexión exitosa con pymssql: {result[0]}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error con pymssql: {e}")
        return False

def test_sqlalchemy_connection():
    """Test con SQLAlchemy"""
    try:
        from sqlalchemy import create_engine, text
        
        # Configurar tus datos aquí
        server = "192.168.1.6"  # IP de tu servidor Windows
        database = "datoscabledb"
        username = "sa"
        password = "Yg181008"


        print("🔍 Intentando conexión con SQLAlchemy...")
        
        # Connection string para SQLAlchemy
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        
        engine = create_engine(connection_string)
        
        # Test simple
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Conexión exitosa con SQLAlchemy: {row[0]}")
            return True
            
    except Exception as e:
        print(f"❌ Error con SQLAlchemy: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🎯" + "="*50 + "🎯")
    print("🔍 TEST DE CONEXIÓN A SQL SERVER")
    print("🎯" + "="*50 + "🎯")
    
    # Instrucciones
    print("\n⚠️  ANTES DE EJECUTAR:")
    print("   1. Edita este archivo y cambia los valores:")
    print("      - server: IP de tu Windows")
    print("      - database: nombre de tu base de datos")
    print("      - username: tu usuario SQL")
    print("      - password: tu contraseña")
    print("   2. Asegúrate de que SQL Server esté corriendo")
    print("   3. Verifica que el puerto 1433 esté abierto")
    print()
    
    # Test 1: pyodbc
    success_pyodbc = test_pyodbc_connection()
    
    # Test 2: pymssql (si está disponible)
    success_pymssql = test_pymssql_connection()
    
    # Test 3: SQLAlchemy
    success_sqlalchemy = test_sqlalchemy_connection()
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN:")
    print(f"   pyodbc: {'✅ OK' if success_pyodbc else '❌ FALLO'}")
    print(f"   pymssql: {'✅ OK' if success_pymssql else '❌ FALLO'}")
    print(f"   SQLAlchemy: {'✅ OK' if success_sqlalchemy else '❌ FALLO'}")
    
    if any([success_pyodbc, success_pymssql, success_sqlalchemy]):
        print("\n🎉 ¡Al menos una conexión funciona!")
    else:
        print("\n❌ Ninguna conexión funciona. Revisar configuración.")

if __name__ == "__main__":
    main()
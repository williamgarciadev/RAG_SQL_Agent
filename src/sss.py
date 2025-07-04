import os
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

try:
    import pyodbc
    from sqlalchemy import create_engine, text

    # Obtener configuración
    host = os.getenv('SQL_SERVER_HOST', 'localhost')
    port = os.getenv('SQL_SERVER_PORT', '1433')
    database = os.getenv('SQL_SERVER_DATABASE', 'Bantotal')
    username = os.getenv('SQL_SERVER_USERNAME', '')
    password = os.getenv('SQL_SERVER_PASSWORD', '')
    driver = os.getenv('SQL_SERVER_DRIVER', 'ODBC Driver 17 for SQL Server')

    print(f"🔌 Intentando conectar a: {host}:{port}/{database}")

    # Crear string de conexión
    if username and password:
        connection_string = (
            f"mssql+pyodbc://{username}:{password}@"
            f"{host}:{port}/{database}"
            f"?driver={driver.replace(' ', '+')}&TrustServerCertificate=yes"
        )
        print("🔑 Usando autenticación SQL Server")
    else:
        connection_string = (
            f"mssql+pyodbc://{host}:{port}/{database}"
            f"?driver={driver.replace(' ', '+')}&trusted_connection=yes&TrustServerCertificate=yes"
        )
        print("🔑 Usando autenticación Windows")

    # Probar conexión
    engine = create_engine(connection_string, echo=False)

    with engine.connect() as conn:
        # Probar query simple
        result = conn.execute(text("SELECT 1 as test"))
        result.fetchone()
        print("✅ Conexión SQL Server exitosa!")

        # Verificar si existe tabla Abonados
        check_table = conn.execute(text("""
                                        SELECT COUNT(*) as existe
                                        FROM INFORMATION_SCHEMA.TABLES
                                        WHERE TABLE_NAME = 'Abonados'
                                        """))
        existe = check_table.fetchone()[0]

        if existe > 0:
            print("✅ Tabla 'Abonados' encontrada en la base de datos")

            # Contar registros
            count_query = conn.execute(text("SELECT COUNT(*) FROM Abonados"))
            total_registros = count_query.fetchone()[0]
            print(f"📊 Total registros en Abonados: {total_registros:,}")

        else:
            print("⚠️  Tabla 'Abonados' NO encontrada")
            print("💡 Verificar:")
            print("   • Nombre exacto de la tabla")
            print("   • Esquema (dbo.Abonados?)")
            print("   • Permisos de lectura")

        # Mostrar primeras 5 tablas disponibles
        tables_query = conn.execute(text("""
                                         SELECT TOP 5 TABLE_NAME
                                         FROM INFORMATION_SCHEMA.TABLES
                                         WHERE TABLE_TYPE = 'BASE TABLE'
                                         ORDER BY TABLE_NAME
                                         """))

        print("\n📋 Primeras 5 tablas disponibles:")
        for row in tables_query:
            print(f"   • {row[0]}")

except ImportError as e:
    print(f"❌ Error: Dependencias faltantes - {e}")
    print("💡 Instalar: pip install pyodbc sqlalchemy")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("💡 Verificar:")
    print("   • Configuración en .env")
    print("   • Servidor SQL Server ejecutándose")
    print("   • Credenciales correctas")
    print("   • Firewall/puertos abiertos")
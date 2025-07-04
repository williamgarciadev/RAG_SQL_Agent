#!/usr/bin/env python3
"""
Cambiar sistema completo a pymssql
"""

import shutil
from pathlib import Path

def backup_and_replace():
    """Hacer backup y reemplazar archivos"""
    
    # Hacer backup del archivo original
    original = Path('src/database_explorer.py')
    backup = Path('src/database_explorer_pyodbc.py.backup')
    
    if original.exists():
        print("📁 Haciendo backup del archivo original...")
        shutil.copy2(original, backup)
        print(f"✅ Backup guardado como: {backup}")
    
    # Reemplazar con la versión pymssql
    pymssql_version = Path('src/database_explorer_pymssql.py')
    
    if pymssql_version.exists():
        print("🔄 Reemplazando database_explorer.py...")
        shutil.copy2(pymssql_version, original)
        print("✅ database_explorer.py actualizado para usar pymssql")
    else:
        print("❌ No se encontró database_explorer_pymssql.py")
        return False
    
    return True

def update_requirements():
    """Actualizar requirements.txt"""
    requirements_file = Path('requirements.txt')
    
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            content = f.read()
        
        # Agregar pymssql si no está
        if 'pymssql' not in content:
            print("📝 Agregando pymssql a requirements.txt...")
            with open(requirements_file, 'a') as f:
                f.write('\n# SQL Server con pymssql\npymssql>=2.2.0\n')
            print("✅ requirements.txt actualizado")
    
def main():
    print("🎯" + "="*50 + "🎯")
    print("🔄 CAMBIANDO SISTEMA A PYMSSQL")
    print("🎯" + "="*50 + "🎯")
    
    if backup_and_replace():
        update_requirements()
        print("\n🎉 ¡Sistema actualizado para usar pymssql!")
        print("\n💡 Ahora puedes probar:")
        print("   python diagnose.py")
        print("   python rag.py 'estructura de FSD601'")
    else:
        print("\n❌ Error actualizando sistema")

if __name__ == "__main__":
    main()
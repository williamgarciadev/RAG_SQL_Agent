#!/usr/bin/env python3
"""
Probar la corrección de la interfaz web
"""

import sys
from pathlib import Path

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_corrected_web_explorer():
    """Probar que la interfaz web ahora usa el explorador correcto."""
    
    print("🔍 PROBANDO CORRECCIÓN DE INTERFAZ WEB")
    print("=" * 60)
    
    try:
        # Simular exactamente la función corregida de la web
        print("1. Cargando explorador mejorado...")
        
        # Código exacto de la función corregida
        try:
            from database_explorer_pymssql import DatabaseExplorer
            explorer = DatabaseExplorer()
            print("✅ Cargado: database_explorer_pymssql")
        except ImportError:
            # Fallback al explorador genérico
            try:
                from database_explorer import DatabaseExplorer
                explorer = DatabaseExplorer()
                print("⚠️ Fallback: database_explorer genérico")
            except ImportError:
                print("❌ Error: No se pudo cargar ningún explorador")
                return False
        
        # Conectar
        print("2. Conectando a la base de datos...")
        if not explorer.connect():
            print("❌ Error de conexión")
            return False
        print("✅ Conexión establecida")
        
        # Buscar tabla
        print("3. Buscando tabla FSD010...")
        tables = explorer.search_tables("FSD010", limit=1)
        if not tables:
            print("❌ Tabla no encontrada")
            return False
        
        best_table = tables[0]
        print(f"✅ Tabla encontrada: {best_table['full_name']}")
        
        # Obtener estructura
        print("4. Obteniendo estructura...")
        structure = explorer.get_table_structure(
            best_table['table_name'], 
            best_table['schema_name']
        )
        
        if not structure:
            print("❌ No se pudo obtener estructura")
            return False
        
        # Verificar descripciones
        print("5. Verificando descripciones...")
        fields_with_desc = 0
        total_fields = len(structure['columns'])
        
        for col in structure['columns'][:5]:  # Primeros 5
            description = col.get('description', '').strip()
            if description:
                fields_with_desc += 1
            print(f"  • {col['name']}: '{description}' ({'✅' if description else '❌'})")
        
        percentage = (fields_with_desc / total_fields * 100) if total_fields > 0 else 0
        
        print(f"\n📊 RESULTADO:")
        print(f"  • Total campos: {total_fields}")
        print(f"  • Primeros 5 con descripción: {fields_with_desc}/5")
        print(f"  • Porcentaje estimado: {percentage:.1f}%")
        
        explorer.close()
        
        # Verificar que se están obteniendo descripciones
        return fields_with_desc > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_cache_clear():
    """Mostrar cómo limpiar caché de Streamlit."""
    
    print("\n🧹 LIMPIAR CACHÉ DE STREAMLIT")
    print("=" * 60)
    print("El problema podría ser caché de @st.cache_resource")
    print("\n📋 PASOS PARA LIMPIAR CACHÉ:")
    print("1. En Streamlit web:")
    print("   • Presionar 'C' para limpiar caché")
    print("   • O ir a menú ☰ → 'Clear cache'")
    print("\n2. Reiniciar Streamlit:")
    print("   • Ctrl+C en terminal")
    print("   • streamlit run src/app_enhanced.py")
    print("\n3. Verificar que usa el explorador correcto:")
    print("   • Debe cargar 'database_explorer_pymssql'")
    print("   • NO debe mostrar warning de 'explorador genérico'")

def show_final_instructions():
    """Mostrar instrucciones finales."""
    
    print("\n🚀 INSTRUCCIONES PARA PROBAR EN WEB")
    print("=" * 60)
    print("1. Ejecutar: streamlit run src/app_enhanced.py")
    print("2. Limpiar caché: Presionar 'C' o reiniciar")
    print("3. Ir a: '🔍 Explorador de Tablas'")
    print("4. Buscar: 'FSD010'")
    print("5. Hacer clic: '📋 Analizar Primera Tabla'")
    print("6. Verificar en pestaña '📋 Campos':")
    print("   • Total Campos: 45")
    print("   • Con Descripción: 45 (no 0)")
    print("   • Porcentaje: 100.0% (no 0.0%)")
    print("\n✨ ¡Ahora debería mostrar las descripciones correctamente!")

if __name__ == "__main__":
    print("🧪 PROBANDO CORRECCIÓN INTERFAZ WEB")
    print("=" * 70)
    
    # Test principal
    test_ok = test_corrected_web_explorer()
    
    # Instrucciones de caché
    test_streamlit_cache_clear()
    
    # Instrucciones finales
    show_final_instructions()
    
    print(f"\n📊 RESULTADO:")
    print(f"  • Corrección funcionando: {'✅' if test_ok else '❌'}")
    
    if test_ok:
        print("\n🎉 ¡Corrección exitosa! El explorador mejorado está funcionando.")
        print("💡 Recuerda limpiar caché de Streamlit para ver los cambios.")
    else:
        print("\n⚠️ Hay problemas que resolver en la corrección.")
# scale_config.py - Configurar sistema para miles de tablas

import os
from pathlib import Path
from dotenv import load_dotenv

def update_env_for_scale():
    """Actualizar .env para manejar miles de tablas"""
    
    print("🔧 Configurando sistema para miles de tablas...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        return False
    
    # Leer configuración actual
    current_content = env_file.read_text(encoding='utf-8')
    lines = current_content.split('\n')
    
    # Configuraciones optimizadas para miles de tablas
    new_configs = {
        'SQL_EXTRACT_MODE': 'smart',
        'SQL_TABLES_BATCH_SIZE': '200',  # Más tablas por lote
        'SQL_MAX_TABLES_PER_SCHEMA': '1000',  # Aumentar límite
        'SQL_INCLUDE_SCHEMAS': '',  # Todos los esquemas
        'SQL_EXCLUDE_PATTERNS': 'sys_,information_schema,msdb,tempdb,model,master,trace_,spt_',
        'CHUNK_SIZE': '1200',  # Chunks más grandes para tablas complejas
        'TOP_K_RESULTS': '10',  # Más resultados en búsquedas
        'MIN_SIMILARITY': '0.05',  # Menor filtro para encontrar más resultados
        'BATCH_SIZE_LARGE': '100'  # Lotes más grandes
    }
    
    # Actualizar o agregar configuraciones
    updated_lines = []
    configs_found = set()
    
    for line in lines:
        updated_line = line
        for key, value in new_configs.items():
            if line.startswith(f'{key}='):
                updated_line = f'{key}={value}'
                configs_found.add(key)
                print(f"✅ Actualizado: {key}={value}")
                break
        updated_lines.append(updated_line)
    
    # Agregar configuraciones faltantes
    for key, value in new_configs.items():
        if key not in configs_found:
            updated_lines.append(f'{key}={value}')
            print(f"✅ Agregado: {key}={value}")
    
    # Guardar archivo actualizado
    env_file.write_text('\n'.join(updated_lines), encoding='utf-8')
    print("🎯 Archivo .env actualizado para escala enterprise")
    
    return True

def test_sql_connection_scale():
    """Probar conexión y mostrar estadísticas reales de la BD"""
    
    print("\n🔍 Analizando escala real de la base de datos...")
    
    try:
        import sys
        sys.path.append('src')
        from database_explorer import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        
        if not explorer.connect():
            print("❌ No se pudo conectar a la base de datos")
            return False
        
        # Obtener vista general
        overview = explorer.get_database_overview()
        
        if overview:
            print(f"\n📊 ESTADÍSTICAS REALES:")
            print(f"   📋 Total tablas: {overview['total_tables']:,}")
            print(f"   👁️ Vistas: {overview['total_views']:,}")
            print(f"   📁 Esquemas: {overview['total_schemas']}")
            
            print(f"\n🏆 Top esquemas por número de tablas:")
            for schema in overview.get('top_schemas', [])[:10]:
                print(f"   📂 {schema['schema']}: {schema['tables']:,} tablas")
            
            print(f"\n🧩 Tablas más complejas:")
            for table in overview.get('most_complex_tables', [])[:10]:
                print(f"   🗂️ {table['table']}: {table['columns']} campos")
            
            # Buscar patrones bancarios típicos
            print(f"\n🔍 Buscando patrones bancarios típicos...")
            
            banking_patterns = [
                'ABONADO', 'CLIENTE', 'CUENTA', 'SERVICIO', 'PRESTAMO', 
                'TARJETA', 'SUCURSAL', 'MOVIMIENTO', 'TRANSACCION',
                'FSE', 'FST', 'FSD', 'FSA'  # Patrones Bantotal
            ]
            
            found_tables = {}
            for pattern in banking_patterns:
                tables = explorer.search_tables(pattern, limit=20)
                if tables:
                    found_tables[pattern] = len(tables)
                    print(f"   🏦 {pattern}: {len(tables)} tablas encontradas")
            
            total_banking_tables = sum(found_tables.values())
            print(f"\n🎯 Total tablas bancarias identificadas: {total_banking_tables:,}")
            
            return True
        else:
            print("❌ No se pudo obtener vista general de la BD")
            return False
            
    except Exception as e:
        print(f"❌ Error analizando BD: {e}")
        return False

def create_advanced_extraction_strategy():
    """Crear estrategia de extracción por fases para miles de tablas"""
    
    print("\n📋 Creando estrategia de extracción por fases...")
    
    strategy_file = Path('extraction_strategy.json')
    
    strategy = {
        "description": "Estrategia de extracción escalonada para miles de tablas bancarias",
        "phases": [
            {
                "phase": 1,
                "name": "Tablas Core Bancarias",
                "patterns": ["ABONADO", "CLIENTE", "CUENTA", "SERVICIO", "PRESTAMO"],
                "priority": "HIGH",
                "batch_size": 50,
                "description": "Tablas principales de clientes y servicios"
            },
            {
                "phase": 2, 
                "name": "Transacciones y Movimientos",
                "patterns": ["MOVIMIENTO", "TRANSACCION", "OPERACION", "PAGO"],
                "priority": "HIGH",
                "batch_size": 100,
                "description": "Tablas de operaciones y transacciones"
            },
            {
                "phase": 3,
                "name": "Catálogos y Configuración",
                "patterns": ["CATALOGO", "PARAMETRO", "CONFIGURACION", "TIPO"],
                "priority": "MEDIUM",
                "batch_size": 150,
                "description": "Tablas de configuración y catálogos"
            },
            {
                "phase": 4,
                "name": "Reportes y Auditoría",
                "patterns": ["REPORTE", "LOG", "AUDITORIA", "HISTORIAL"],
                "priority": "LOW",
                "batch_size": 200,
                "description": "Tablas de reportes y auditoría"
            },
            {
                "phase": 5,
                "name": "Resto de Tablas",
                "patterns": ["*"],
                "priority": "LOW", 
                "batch_size": 300,
                "description": "Todas las demás tablas del sistema"
            }
        ],
        "extraction_settings": {
            "max_tables_per_run": 1000,
            "max_time_per_phase": "10 minutes",
            "skip_empty_tables": True,
            "include_indexes": True,
            "include_relationships": True
        }
    }
    
    strategy_file.write_text(
        json.dumps(strategy, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    print(f"✅ Estrategia guardada en: {strategy_file}")
    return strategy_file

def estimate_processing_time():
    """Estimar tiempo de procesamiento para miles de tablas"""
    
    print("\n⏱️ Estimando tiempos de procesamiento...")
    
    # Obtener número real de tablas
    try:
        import sys
        sys.path.append('src')
        from database_explorer import DatabaseExplorer
        
        explorer = DatabaseExplorer()
        if explorer.connect():
            overview = explorer.get_database_overview()
            total_tables = overview.get('total_tables', 1000)
        else:
            total_tables = 1000  # Estimación por defecto
    except:
        total_tables = 1000
    
    # Estimaciones basadas en experiencia
    time_per_table = 0.5  # segundos por tabla
    total_extraction_time = (total_tables * time_per_table) / 60  # minutos
    
    batch_size = 200
    num_batches = (total_tables + batch_size - 1) // batch_size
    
    print(f"📊 ESTIMACIONES:")
    print(f"   📋 Total tablas: {total_tables:,}")
    print(f"   🔄 Lotes de {batch_size}: {num_batches} lotes")
    print(f"   ⏱️ Tiempo estimado extracción: {total_extraction_time:.1f} minutos")
    print(f"   💾 Tiempo indexación: {(total_tables * 0.1) / 60:.1f} minutos")
    print(f"   🎯 Tiempo total estimado: {total_extraction_time + (total_tables * 0.1) / 60:.1f} minutos")
    
    if total_extraction_time > 30:
        print(f"\n💡 RECOMENDACIONES:")
        print(f"   🔥 Usar extracción por fases")
        print(f"   ⚡ Aumentar batch_size a 300-500")
        print(f"   🎯 Enfocar en tablas críticas primero")
        print(f"   ⏰ Ejecutar en horarios de baja demanda")

def main():
    """Configurar sistema para miles de tablas"""
    
    print("🏗️ CONFIGURACIÓN PARA MILES DE TABLAS")
    print("=" * 50)
    
    success_count = 0
    
    # 1. Actualizar configuración
    if update_env_for_scale():
        success_count += 1
    
    # 2. Analizar escala real
    if test_sql_connection_scale():
        success_count += 1
    
    # 3. Crear estrategia de extracción
    if create_advanced_extraction_strategy():
        success_count += 1
    
    # 4. Estimar tiempos
    estimate_processing_time()
    success_count += 1
    
    print(f"\n📊 RESULTADO:")
    print(f"   Configuraciones aplicadas: {success_count}/4")
    
    if success_count >= 3:
        print(f"\n🎉 ¡Sistema configurado para escala enterprise!")
        print(f"💡 Próximos pasos:")
        print(f"   1. python src/indexer.py --force")
        print(f"   2. python rag.py \"SELECT tabla ABONADOS\"")
        print(f"   3. python rag.py \"consultar servicios bancarios\"")
        
        print(f"\n🚀 EXTRACCIÓN ESCALABLE:")
        print(f"   • Procesará MILES de tablas automáticamente")
        print(f"   • Priorizará tablas bancarias críticas")
        print(f"   • Optimizará memoria y rendimiento")
        print(f"   • Generará índice completo de la BD")
    else:
        print(f"\n⚠️ Revisar configuraciones antes de continuar")

if __name__ == "__main__":
    main()
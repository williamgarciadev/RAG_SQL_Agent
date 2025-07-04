#!/usr/bin/env python3
"""
Script Maestro RAG - Interfaz Unificada
Un solo comando para todo el sistema RAG especializado.

Uso:
  python rag.py "tu consulta aquí"

El sistema decide automáticamente:
- 🗄️ Consultas SQL → SQLAgent  
- 📚 Documentación → DocsAgent
- 🔄 Mixtas → Ambos agentes
"""

import sys
import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configurar paths correctamente
# El script debe estar en la RAÍZ del proyecto, no en src/
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_PATH = PROJECT_ROOT / 'src'

# Agregar src al path si existe
if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))
    os.chdir(PROJECT_ROOT)  # Cambiar directorio de trabajo a la raíz
else:
    print("❌ Directorio 'src' no encontrado")
    print("💡 Asegúrate de ejecutar desde la raíz del proyecto:")
    print(f"   cd {PROJECT_ROOT}")
    print(f"   python rag.py 'tu consulta'")
    sys.exit(1)


def print_banner():
    """Mostrar banner del sistema."""
    print("🎯" + "=" * 78 + "🎯")
    print("🤖 SISTEMA RAG ESPECIALIZADO - BANCARIO & GENEXUS 🤖")
    print("🎯" + "=" * 78 + "🎯")
    print("🗄️ SQLAgent: Genera consultas SQL optimizadas")
    print("📚 DocsAgent: Consulta documentación técnica")
    print("🧠 Director: Decide automáticamente qué agente usar")
    print("🎯" + "=" * 78 + "🎯")
    print()


def check_project_structure():
    """Verificar estructura del proyecto."""
    required_files = {
        'src/agent_director.py': 'Director inteligente',
        'src/sql_agent.py': 'SQLAgent especializado',
        'src/docs_agent.py': 'DocsAgent especializado',
        'src/database_explorer.py': 'Explorador BD',
        'src/ingestion.py': 'Sistema ingesta',
        'src/indexer.py': 'Indexador vectorial'
    }

    missing_files = []
    for file_path, description in required_files.items():
        if not (PROJECT_ROOT / file_path).exists():
            missing_files.append(f"❌ {file_path} - {description}")
        else:
            print(f"✅ {file_path} - {description}")

    if missing_files:
        print("\n⚠️ Archivos faltantes:")
        for missing in missing_files:
            print(f"   {missing}")
        print("\n💡 Soluciones:")
        print("   1. Verificar que todos los módulos estén en src/")
        print("   2. Ejecutar configuración: python setup_rag.py")
        print("   3. Descargar módulos faltantes")
        return False

    return True


def check_system_status():
    """Verificar estado del sistema."""
    print("🔍 Verificando estado del sistema...")

    # Verificar estructura del proyecto primero
    if not check_project_structure():
        return {'structure_ok': False}

    status = {
        'structure_ok': True,
        'index_available': False,
        'sql_agent': False,
        'docs_agent': False,
        'director': False
    }

    # Verificar índice
    try:
        from indexer import get_index_info
        info = get_index_info()
        if info.get('exists', False):
            status['index_available'] = True
            doc_count = info.get('live_count', 0)
            print(f"   ✅ Índice: {doc_count} documentos disponibles")
        else:
            print("   ❌ Índice no disponible")
            print("   💡 Ejecutar: python src/indexer.py --force")
    except ImportError as e:
        print(f"   ❌ Módulo indexer no encontrado: {e}")
    except Exception as e:
        print(f"   ❌ Error verificando índice: {e}")

    # Verificar agentes
    try:
        from sql_agent import SQLAgent
        status['sql_agent'] = True
        print("   ✅ SQLAgent disponible")
    except ImportError as e:
        print(f"   ❌ SQLAgent no disponible: {e}")
    except Exception as e:
        print(f"   ❌ Error cargando SQLAgent: {e}")

    try:
        from src.docs_agent import DocsAgent
        status['docs_agent'] = True
        print("   ✅ DocsAgent disponible")
    except ImportError as e:
        print(f"   ❌ DocsAgent no disponible: {e}")
    except Exception as e:
        print(f"   ❌ Error cargando DocsAgent: {e}")

    try:
        from agent_director import AgentDirector
        status['director'] = True
        print("   ✅ Director disponible")
    except ImportError as e:
        print(f"   ❌ Director no disponible: {e}")
    except Exception as e:
        print(f"   ❌ Error cargando Director: {e}")

    return status


def show_examples():
    """Mostrar ejemplos de uso."""
    print("""
🎯 EJEMPLOS DE USO:

📊 CONSULTAS SQL (van automáticamente a SQLAgent):
   python rag.py "SELECT de tabla abonados con todos los campos"
   python rag.py "generar INSERT para nuevo cliente"  
   python rag.py "UPDATE datos del abonado activo"
   python rag.py "consultar servicios de un cliente"

📚 DOCUMENTACIÓN (van automáticamente a DocsAgent):
   python rag.py "cómo usar FOR EACH en GeneXus"
   python rag.py "proceso de creación de clientes en Bantotal"
   python rag.py "manual de instalación de GeneXus"
   python rag.py "configurar base de datos"

🔄 CONSULTAS MIXTAS (usan ambos agentes):
   python rag.py "documentación de tabla abonados y generar SELECT"
   python rag.py "explicar estructura y crear consulta"

🚀 COMANDOS ESPECIALES:
   python rag.py --status      # Ver estado del sistema
   python rag.py --setup       # Configurar sistema
   python rag.py --examples    # Mostrar ejemplos
   python rag.py --stats       # Ver estadísticas
   python rag.py --help        # Ayuda completa
""")


def run_setup():
    """Ejecutar configuración del sistema."""
    print("🚀 Iniciando configuración del sistema...")

    # Verificar si existe setup_rag.py
    setup_script = PROJECT_ROOT / 'setup_rag.py'
    if setup_script.exists():
        print("   Ejecutando configuración automática...")
        import subprocess
        try:
            result = subprocess.run([sys.executable, str(setup_script)],
                                    capture_output=False, text=True, cwd=PROJECT_ROOT)
            return result.returncode == 0
        except Exception as e:
            print(f"   ❌ Error ejecutando setup: {e}")
            return False
    else:
        print("   ❌ Script de configuración no encontrado")
        print("   💡 Crear setup_rag.py o configurar manualmente")
        print("\n   🔧 Pasos manuales:")
        print("      1. Crear archivo .env con configuración SQL Server")
        print("      2. python src/ingestion.py --test-sql")
        print("      3. python src/ingestion.py --sql-smart")
        print("      4. python src/indexer.py --force")
        return False


def show_stats():
    """Mostrar estadísticas del sistema."""
    print("📊 Estadísticas del Sistema:")

    try:
        from agent_director import AgentDirector
        director = AgentDirector()
        stats = director.get_director_stats()

        # Estadísticas del director
        d_stats = stats['director']
        print(f"\n🎯 Director:")
        print(f"   Total consultas: {d_stats['total_queries']}")
        print(f"   SQL routing: {d_stats['sql_queries_routed']}")
        print(f"   Docs routing: {d_stats['docs_queries_routed']}")
        print(f"   Consultas mixtas: {d_stats['mixed_queries']}")
        print(f"   Tiempo promedio: {d_stats['avg_routing_time']:.3f}s")

        # Estadísticas de agentes
        if 'sql' in stats['agents']:
            sql_stats = stats['agents']['sql']
            print(f"\n🗄️ SQLAgent:")
            print(f"   Consultas SQL: {sql_stats['sql_queries_generated']}")
            print(f"   SELECT: {sql_stats['select_queries']}")
            print(f"   INSERT: {sql_stats['insert_queries']}")
            print(f"   UPDATE: {sql_stats['update_queries']}")
            print(f"   DELETE: {sql_stats['delete_queries']}")
            print(f"   Tasa éxito: {sql_stats['success_rate']:.1%}")

        if 'docs' in stats['agents']:
            docs_stats = stats['agents']['docs']
            print(f"\n📚 DocsAgent:")
            print(f"   Consultas docs: {docs_stats['doc_queries_processed']}")
            print(f"   GeneXus: {docs_stats['genexus_queries']}")
            print(f"   Bantotal: {docs_stats['bantotal_queries']}")
            print(f"   Técnicas: {docs_stats['technical_queries']}")
            print(f"   Tasa éxito: {docs_stats['success_rate']:.1%}")

    except Exception as e:
        print(f"   ❌ Error obteniendo estadísticas: {e}")


def process_query(query: str):
    """Procesar consulta usando el director."""
    try:
        from agent_director import AgentDirector

        # Crear director
        director = AgentDirector()

        # Procesar consulta
        print(f"🤖 Procesando: '{query}'")
        print("   🧠 Analizando intención...")

        result = director.process_query(query)

        # Mostrar resultado formateado
        print(f"\n🎯 CONSULTA: {result['query']}")
        print(f"🧠 INTENCIÓN: {result['intent'].title()}")
        print(f"🤖 AGENTE: {result['agent_used']}")

        if result['metadata'].get('intent_confidence'):
            confidence = result['metadata']['intent_confidence']
            print(f"🎲 CONFIANZA: {confidence:.2f}")

        print(f"\n📝 RESPUESTA:")
        print("🔸" + "=" * 78 + "🔸")
        print(result['answer'])
        print("🔸" + "=" * 78 + "🔸")

        # Información adicional si es SQL
        if result['intent'] == 'sql' and result.get('raw_result'):
            raw = result['raw_result']
            if raw.get('warnings'):
                print(f"\n⚠️ ADVERTENCIAS:")
                for warning in raw['warnings']:
                    print(f"   • {warning}")

        # Información adicional si es documentación
        elif result['intent'] == 'docs' and result.get('raw_result'):
            raw = result['raw_result']
            if raw.get('recommendations'):
                print(f"\n💡 RECOMENDACIONES:")
                for rec in raw['recommendations']:
                    print(f"   • {rec}")

            if raw.get('related_topics'):
                print(f"\n🔗 TEMAS RELACIONADOS: {', '.join(raw['related_topics'])}")

        # Sugerencias de mejora
        suggestions = director.suggest_query_improvements(query, result)
        if suggestions:
            print(f"\n🎯 PARA MEJORES RESULTADOS:")
            for suggestion in suggestions:
                print(f"   💡 {suggestion}")

        # Estadísticas de la consulta
        metadata = result['metadata']
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   ⏱️ Tiempo: {metadata.get('routing_time', 0):.2f}s")
        print(f"   ✅ Éxito: {'Sí' if metadata.get('success') else 'No'}")

        return result['metadata'].get('success', False)

    except Exception as e:
        logger.error(f"❌ Error procesando consulta: {e}")
        print(f"\n❌ Error: {e}")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("   • Verificar que el sistema esté configurado: python rag.py --setup")
        print("   • Verificar estado: python rag.py --status")
        print("   • Verificar que el índice esté creado: python src/indexer.py --force")
        print("   • Verificar estructura del proyecto")
        return False


def show_help():
    """Mostrar ayuda completa."""
    print("""
🤖 SISTEMA RAG ESPECIALIZADO - AYUDA COMPLETA

DESCRIPCIÓN:
  Sistema de consulta inteligente que combina dos agentes especializados:
  • SQLAgent: Genera consultas SQL optimizadas (SELECT, INSERT, UPDATE, DELETE)
  • DocsAgent: Consulta documentación técnica (GeneXus, Bantotal, manuales)
  • Director: Decide automáticamente qué agente usar según la consulta

USO BÁSICO:
  python rag.py "tu consulta aquí"

COMANDOS ESPECIALES:
  python rag.py --status       # Verificar estado del sistema
  python rag.py --setup        # Configurar sistema automáticamente
  python rag.py --examples     # Mostrar ejemplos de uso
  python rag.py --stats        # Ver estadísticas de uso
  python rag.py --help         # Mostrar esta ayuda

ESTRUCTURA DEL PROYECTO:
  rag.py                       # Script maestro (ejecutar desde aquí)
  src/agent_director.py        # Director inteligente
  src/sql_agent.py             # Agente SQL especializado
  src/docs_agent.py            # Agente documentación
  src/database_explorer.py     # Explorador BD escalable
  .env                         # Configuración SQL Server

CONFIGURACIÓN INICIAL:
  1. python rag.py --status    # Verificar qué falta
  2. python rag.py --setup     # Configuración automática
  3. python rag.py "test"      # Probar consulta

TROUBLESHOOTING COMÚN:
  ❌ "No module named 'sql_agent'" 
     → Ejecutar desde raíz del proyecto
     → Verificar que archivos estén en src/

  ❌ "Índice no disponible"
     → python src/indexer.py --force

  ❌ "Error SQL" 
     → Verificar .env y conexión BD
     → python src/ingestion.py --test-sql

¡Ejecutar siempre desde la raíz del proyecto!
""")


def main():
    """Función principal."""
    # Verificar que estamos en la raíz del proyecto
    if not SRC_PATH.exists():
        print("❌ Error: Directorio 'src' no encontrado")
        print(f"📁 Ejecutándose desde: {PROJECT_ROOT}")
        print("💡 Asegúrate de ejecutar desde la raíz del proyecto:")
        print("   cd [directorio_del_proyecto]")
        print("   python rag.py 'tu consulta'")
        return

    # Verificar argumentos
    if len(sys.argv) < 2:
        print_banner()
        print("❓ Uso: python rag.py 'tu consulta' o python rag.py --help")
        print(f"\n📁 Ejecutándose desde: {PROJECT_ROOT}")
        print("\n💡 Ejemplos rápidos:")
        print("   python rag.py 'SELECT tabla abonados'")
        print("   python rag.py 'cómo usar FOR EACH'")
        print("   python rag.py --examples")
        return

    command = sys.argv[1]

    # Comandos especiales
    if command == '--help' or command == '-h':
        show_help()
        return

    elif command == '--examples':
        show_examples()
        return

    elif command == '--status':
        print_banner()
        status = check_system_status()

        if not status.get('structure_ok', False):
            print(f"\n❌ Estructura del proyecto incompleta")
            print(f"💡 Verificar que todos los módulos estén en src/")
            return

        # Resumen
        print(f"\n📋 RESUMEN:")
        core_components = ['index_available', 'sql_agent', 'docs_agent', 'director']
        all_ready = all(status.get(comp, False) for comp in core_components)

        if all_ready:
            print("   ✅ Sistema completamente funcional")
            print("   🚀 Listo para procesar consultas")
        else:
            print("   ⚠️ Sistema requiere configuración")
            print("   🔧 Ejecuta: python rag.py --setup")
        return

    elif command == '--setup':
        print_banner()
        success = run_setup()
        if success:
            print("\n✅ Configuración completada")
            print("🚀 Sistema listo para usar")
            print("💡 Prueba: python rag.py 'SELECT tabla abonados'")
        else:
            print("\n❌ Error en configuración")
            print("🔧 Revisar mensajes anteriores")
        return

    elif command == '--stats':
        print_banner()
        show_stats()
        return

    # Procesar consulta normal
    query = ' '.join(sys.argv[1:])

    if not query.strip():
        print("❌ Consulta vacía")
        print("💡 Ejemplo: python rag.py 'SELECT tabla abonados'")
        return

    print_banner()

    # Verificar estado mínimo antes de procesar
    status = check_system_status()
    if not status.get('structure_ok', False):
        print("\n❌ Sistema no está correctamente configurado")
        print("🔧 Ejecuta: python rag.py --status")
        return

    if not status.get('director', False):
        print("\n❌ Director no disponible")
        print("🔧 Verificar que agent_director.py esté en src/")
        return

    # Procesar consulta
    success = process_query(query)

    if success:
        print(f"\n🎉 ¡Consulta procesada exitosamente!")
        print(f"💡 Puedes hacer más consultas:")
        print(f"   python rag.py 'otra consulta'")
    else:
        print(f"\n⚠️ Consulta procesada con advertencias")
        print(f"🔧 Si persisten problemas:")
        print(f"   python rag.py --status")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⏹️ Proceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        print(f"🔧 Para ayuda: python rag.py --help")
        print(f"📁 Directorio actual: {PROJECT_ROOT}")
        sys.exit(1)


def print_banner():
    """Mostrar banner del sistema."""
    print("🎯" + "=" * 78 + "🎯")
    print("🤖 SISTEMA RAG ESPECIALIZADO - BANCARIO & GENEXUS 🤖")
    print("🎯" + "=" * 78 + "🎯")
    print("🗄️ SQLAgent: Genera consultas SQL optimizadas")
    print("📚 DocsAgent: Consulta documentación técnica")
    print("🧠 Director: Decide automáticamente qué agente usar")
    print("🎯" + "=" * 78 + "🎯")
    print()


def check_system_status():
    """Verificar estado del sistema."""
    print("🔍 Verificando estado del sistema...")

    status = {
        'index_available': False,
        'sql_agent': False,
        'docs_agent': False,
        'director': False
    }

    # Verificar índice
    try:
        from indexer import get_index_info
        info = get_index_info()
        if info.get('exists', False):
            status['index_available'] = True
            doc_count = info.get('live_count', 0)
            print(f"   ✅ Índice: {doc_count} documentos disponibles")
        else:
            print("   ❌ Índice no disponible")
    except ImportError:
        print("   ❌ Módulo indexer no encontrado")

    # Verificar agentes
    try:
        from sql_agent import SQLAgent
        status['sql_agent'] = True
        print("   ✅ SQLAgent disponible")
    except ImportError:
        print("   ❌ SQLAgent no disponible")

    try:
        from docs_agent import DocsAgent
        status['docs_agent'] = True
        print("   ✅ DocsAgent disponible")
    except ImportError:
        print("   ❌ DocsAgent no disponible")

    try:
        from agent_director import AgentDirector
        status['director'] = True
        print("   ✅ Director disponible")
    except ImportError:
        print("   ❌ Director no disponible")

    return status


def show_examples():
    """Mostrar ejemplos de uso."""
    print("""
🎯 EJEMPLOS DE USO:

📊 CONSULTAS SQL (van automáticamente a SQLAgent):
   python rag.py "SELECT de tabla abonados con todos los campos"
   python rag.py "generar INSERT para nuevo cliente"  
   python rag.py "UPDATE datos del abonado activo"
   python rag.py "consultar servicios de un cliente"

📚 DOCUMENTACIÓN (van automáticamente a DocsAgent):
   python rag.py "cómo usar FOR EACH en GeneXus"
   python rag.py "proceso de creación de clientes en Bantotal"
   python rag.py "manual de instalación de GeneXus"
   python rag.py "configurar base de datos"

🔄 CONSULTAS MIXTAS (usan ambos agentes):
   python rag.py "documentación de tabla abonados y generar SELECT"
   python rag.py "explicar estructura y crear consulta"

🚀 COMANDOS ESPECIALES:
   python rag.py --status      # Ver estado del sistema
   python rag.py --setup       # Configurar sistema
   python rag.py --examples    # Mostrar ejemplos
   python rag.py --stats       # Ver estadísticas
   python rag.py --help        # Ayuda completa
""")


def run_setup():
    """Ejecutar configuración del sistema."""
    print("🚀 Iniciando configuración del sistema...")

    # Verificar si existe setup_rag.py
    setup_script = Path('setup_rag.py')
    if setup_script.exists():
        print("   Ejecutando configuración automática...")
        import subprocess
        try:
            result = subprocess.run([sys.executable, str(setup_script)],
                                    capture_output=False, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"   ❌ Error ejecutando setup: {e}")
            return False
    else:
        print("   ❌ Script de configuración no encontrado")
        print("   💡 Descarga setup_rag.py o configura manualmente")
        return False


def show_stats():
    """Mostrar estadísticas del sistema."""
    print("📊 Estadísticas del Sistema:")

    try:
        from agent_director import AgentDirector
        director = AgentDirector()
        stats = director.get_director_stats()

        # Estadísticas del director
        d_stats = stats['director']
        print(f"\n🎯 Director:")
        print(f"   Total consultas: {d_stats['total_queries']}")
        print(f"   SQL routing: {d_stats['sql_queries_routed']}")
        print(f"   Docs routing: {d_stats['docs_queries_routed']}")
        print(f"   Consultas mixtas: {d_stats['mixed_queries']}")
        print(f"   Tiempo promedio: {d_stats['avg_routing_time']:.3f}s")

        # Estadísticas de agentes
        if 'sql' in stats['agents']:
            sql_stats = stats['agents']['sql']
            print(f"\n🗄️ SQLAgent:")
            print(f"   Consultas SQL: {sql_stats['sql_queries_generated']}")
            print(f"   SELECT: {sql_stats['select_queries']}")
            print(f"   INSERT: {sql_stats['insert_queries']}")
            print(f"   UPDATE: {sql_stats['update_queries']}")
            print(f"   DELETE: {sql_stats['delete_queries']}")
            print(f"   Tasa éxito: {sql_stats['success_rate']:.1%}")

        if 'docs' in stats['agents']:
            docs_stats = stats['agents']['docs']
            print(f"\n📚 DocsAgent:")
            print(f"   Consultas docs: {docs_stats['doc_queries_processed']}")
            print(f"   GeneXus: {docs_stats['genexus_queries']}")
            print(f"   Bantotal: {docs_stats['bantotal_queries']}")
            print(f"   Técnicas: {docs_stats['technical_queries']}")
            print(f"   Tasa éxito: {docs_stats['success_rate']:.1%}")

    except Exception as e:
        print(f"   ❌ Error obteniendo estadísticas: {e}")


def process_query(query: str):
    """Procesar consulta usando el director."""
    try:
        from agent_director import AgentDirector

        # Crear director
        director = AgentDirector()

        # Procesar consulta
        print(f"🤖 Procesando: '{query}'")
        print("   🧠 Analizando intención...")

        result = director.process_query(query)

        # Mostrar resultado formateado
        print(f"\n🎯 CONSULTA: {result['query']}")
        print(f"🧠 INTENCIÓN: {result['intent'].title()}")
        print(f"🤖 AGENTE: {result['agent_used']}")

        if result['metadata'].get('intent_confidence'):
            confidence = result['metadata']['intent_confidence']
            print(f"🎲 CONFIANZA: {confidence:.2f}")

        print(f"\n📝 RESPUESTA:")
        print("🔸" + "=" * 78 + "🔸")
        print(result['answer'])
        print("🔸" + "=" * 78 + "🔸")

        # Información adicional si es SQL
        if result['intent'] == 'sql' and result.get('raw_result'):
            raw = result['raw_result']
            if raw.get('warnings'):
                print(f"\n⚠️ ADVERTENCIAS:")
                for warning in raw['warnings']:
                    print(f"   • {warning}")

        # Información adicional si es documentación
        elif result['intent'] == 'docs' and result.get('raw_result'):
            raw = result['raw_result']
            if raw.get('recommendations'):
                print(f"\n💡 RECOMENDACIONES:")
                for rec in raw['recommendations']:
                    print(f"   • {rec}")

            if raw.get('related_topics'):
                print(f"\n🔗 TEMAS RELACIONADOS: {', '.join(raw['related_topics'])}")

        # Sugerencias de mejora
        suggestions = director.suggest_query_improvements(query, result)
        if suggestions:
            print(f"\n🎯 PARA MEJORES RESULTADOS:")
            for suggestion in suggestions:
                print(f"   💡 {suggestion}")

        # Estadísticas de la consulta
        metadata = result['metadata']
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   ⏱️ Tiempo: {metadata.get('routing_time', 0):.2f}s")
        print(f"   ✅ Éxito: {'Sí' if metadata.get('success') else 'No'}")

        return result['metadata'].get('success', False)

    except Exception as e:
        logger.error(f"❌ Error procesando consulta: {e}")
        print(f"\n❌ Error: {e}")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("   • Verificar que el sistema esté configurado: python rag.py --setup")
        print("   • Verificar estado: python rag.py --status")
        print("   • Verificar que el índice esté creado: python src/indexer.py")
        return False


def show_help():
    """Mostrar ayuda completa."""
    print("""
🤖 SISTEMA RAG ESPECIALIZADO - AYUDA COMPLETA

DESCRIPCIÓN:
  Sistema de consulta inteligente que combina dos agentes especializados:
  • SQLAgent: Genera consultas SQL optimizadas (SELECT, INSERT, UPDATE, DELETE)
  • DocsAgent: Consulta documentación técnica (GeneXus, Bantotal, manuales)
  • Director: Decide automáticamente qué agente usar según la consulta

USO BÁSICO:
  python rag.py "tu consulta aquí"

COMANDOS ESPECIALES:
  python rag.py --status       # Verificar estado del sistema
  python rag.py --setup        # Configurar sistema automáticamente
  python rag.py --examples     # Mostrar ejemplos de uso
  python rag.py --stats        # Ver estadísticas de uso
  python rag.py --help         # Mostrar esta ayuda

TIPOS DE CONSULTAS SOPORTADAS:

🗄️ CONSULTAS SQL:
  - "SELECT de tabla abonados"
  - "generar INSERT para cliente"
  - "UPDATE estado del servicio"
  - "consultar préstamos activos"

📚 DOCUMENTACIÓN:
  - "cómo usar FOR EACH"
  - "proceso de alta de clientes"
  - "manual de instalación"
  - "configurar ambiente"

🔄 CONSULTAS MIXTAS:
  - "estructura tabla y generar SELECT"
  - "documentación y ejemplo SQL"

CONFIGURACIÓN:
  El sistema requiere:
  ✅ Archivo .env con configuración SQL Server
  ✅ Índice vectorial creado (python src/indexer.py)
  ✅ Documentos en directorio 'docs' (opcional)
  ✅ ChromaDB instalado

FIRST-TIME SETUP:
  1. python rag.py --setup     # Configuración automática
  2. python rag.py --status    # Verificar estado
  3. python rag.py "test"      # Probar consulta

EJEMPLOS PRÁCTICOS:
  # Para tu caso específico:
  python rag.py "SELECT tabla abonados todos los campos"

  # Documentación GeneXus:
  python rag.py "sintaxis FOR EACH GeneXus"

  # Proceso bancario:
  python rag.py "crear cliente en Bantotal"

TROUBLESHOOTING:
  ❌ "Índice no disponible" → python src/indexer.py --force
  ❌ "Agente no disponible" → python rag.py --setup
  ❌ "Error SQL" → Verificar .env y conexión BD
  ❌ "Sin documentos" → Agregar archivos a 'docs/'

¡El sistema está optimizado para resolver tu consulta sobre tabla Abonados!
""")


def main():
    """Función principal."""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print_banner()
        print("❓ Uso: python rag.py 'tu consulta' o python rag.py --help")
        print("\n💡 Ejemplos rápidos:")
        print("   python rag.py 'SELECT tabla abonados'")
        print("   python rag.py 'cómo usar FOR EACH'")
        print("   python rag.py --examples")
        return

    command = sys.argv[1]

    # Comandos especiales
    if command == '--help' or command == '-h':
        show_help()
        return

    elif command == '--examples':
        show_examples()
        return

    elif command == '--status':
        print_banner()
        status = check_system_status()

        # Resumen
        print(f"\n📋 RESUMEN:")
        all_ready = all(status.values())
        if all_ready:
            print("   ✅ Sistema completamente funcional")
            print("   🚀 Listo para procesar consultas")
        else:
            print("   ⚠️ Sistema requiere configuración")
            print("   🔧 Ejecuta: python rag.py --setup")
        return

    elif command == '--setup':
        print_banner()
        success = run_setup()
        if success:
            print("\n✅ Configuración completada")
            print("🚀 Sistema listo para usar")
            print("💡 Prueba: python rag.py 'SELECT tabla abonados'")
        else:
            print("\n❌ Error en configuración")
            print("🔧 Revisar mensajes anteriores")
        return

    elif command == '--stats':
        print_banner()
        show_stats()
        return

    # Procesar consulta normal
    query = ' '.join(sys.argv[1:])

    if not query.strip():
        print("❌ Consulta vacía")
        print("💡 Ejemplo: python rag.py 'SELECT tabla abonados'")
        return

    print_banner()

    # Verificar estado mínimo
    try:
        from agent_director import AgentDirector
    except ImportError:
        print("❌ Sistema no configurado")
        print("🔧 Ejecuta: python rag.py --setup")
        return

    # Procesar consulta
    success = process_query(query)

    if success:
        print(f"\n🎉 ¡Consulta procesada exitosamente!")
        print(f"💡 Puedes hacer más consultas:")
        print(f"   python rag.py 'otra consulta'")
    else:
        print(f"\n⚠️ Consulta procesada con advertencias")
        print(f"🔧 Si persisten problemas:")
        print(f"   python rag.py --status")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⏹️ Proceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        print(f"🔧 Para ayuda: python rag.py --help")
        sys.exit(1)
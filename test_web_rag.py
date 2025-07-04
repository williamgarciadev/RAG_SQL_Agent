#!/usr/bin/env python3
"""
Script de prueba para verificar que RAG funciona en web
"""

import sys
from pathlib import Path

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_director_response_format():
    """Probar el formato de respuesta del director."""
    
    try:
        from agent_director import AgentDirector
        
        print("🔍 Probando formato de respuesta del AgentDirector...")
        
        director = AgentDirector()
        
        query = "Generar consulta SQL para obtener datos de clientes"
        print(f"📝 Consulta: {query}")
        
        result = director.process_query(query)
        
        print("\n📊 FORMATO DE RESPUESTA:")
        print("=" * 50)
        
        # Verificar estructura
        print(f"✅ Resultado tipo: {type(result)}")
        
        if isinstance(result, dict):
            print("\n🔑 Claves principales:")
            for key in result.keys():
                value = result[key]
                if isinstance(value, str) and len(value) > 100:
                    preview = value[:97] + "..."
                elif isinstance(value, dict):
                    preview = f"Dict con {len(value)} claves"
                else:
                    preview = str(value)
                print(f"  • {key}: {preview}")
            
            # Verificar campos críticos para la web
            print("\n🌐 COMPATIBILIDAD WEB:")
            web_fields = [
                ('agent_used', 'Agente usado'),
                ('answer', 'Respuesta principal'),
                ('metadata', 'Metadatos'),
                ('metadata.intent_confidence', 'Confianza'),
                ('metadata.success', 'Estado de éxito')
            ]
            
            for field, description in web_fields:
                if '.' in field:
                    keys = field.split('.')
                    value = result
                    try:
                        for k in keys:
                            value = value[k]
                        status = "✅"
                    except (KeyError, TypeError):
                        value = "NO ENCONTRADO"
                        status = "❌"
                else:
                    value = result.get(field, "NO ENCONTRADO")
                    status = "✅" if field in result else "❌"
                
                print(f"  {status} {description}: {value}")
            
            # Mostrar respuesta principal
            answer = result.get('answer', '')
            if answer:
                print(f"\n📝 RESPUESTA PRINCIPAL (primeros 200 chars):")
                print("-" * 50)
                print(answer[:200] + ("..." if len(answer) > 200 else ""))
            
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_compatibility():
    """Probar compatibilidad específica con la interfaz web."""
    
    print("\n🌐 PROBANDO COMPATIBILIDAD WEB:")
    print("=" * 50)
    
    try:
        # Simular lo que hace la interfaz web
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        
        # Cargar director como lo hace la web
        from agent_director import AgentDirector
        
        director = AgentDirector()
        
        # Procesar consulta
        query_input = "Generar consulta SQL para obtener datos de clientes"
        result = director.process_query(query_input)
        
        # Verificar campos que la web necesita
        print("🔍 Verificando campos necesarios para la web...")
        
        # 1. Verificar que result existe
        if not result:
            print("❌ No se recibió resultado")
            return False
        
        print("✅ Resultado recibido")
        
        # 2. Verificar metadata
        metadata = result.get('metadata', {})
        if not metadata:
            print("❌ No hay metadata")
            return False
        
        print("✅ Metadata presente")
        
        # 3. Verificar campos específicos
        agent_used = result.get('agent_used', 'N/A')
        print(f"✅ Agente usado: {agent_used}")
        
        confidence = metadata.get('intent_confidence', 0)
        print(f"✅ Confianza: {confidence}")
        
        answer = result.get('answer', '')
        if answer:
            print(f"✅ Respuesta presente: {len(answer)} caracteres")
        else:
            print("❌ No hay respuesta principal")
            return False
        
        success = metadata.get('success', False)
        print(f"✅ Estado éxito: {success}")
        
        print("\n🎉 ¡Compatibilidad web verificada!")
        return True
        
    except Exception as e:
        print(f"❌ Error en compatibilidad web: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_web_instructions():
    """Mostrar instrucciones para probar en la web."""
    
    print("\n🚀 INSTRUCCIONES PARA PROBAR EN WEB:")
    print("=" * 50)
    print("1. Ejecutar: streamlit run src/app_enhanced.py")
    print("2. Ir a la pestaña '🧠 Consultas RAG Inteligentes'")
    print("3. Escribir: 'Generar consulta SQL para obtener datos de clientes'")
    print("4. Activar 'Mostrar Routing' para ver detalles")
    print("5. Hacer clic en '🚀 Ejecutar Consulta'")
    print("\n✨ ¡Ahora debería mostrar la respuesta correctamente!")
    print("\n🔧 Si sigue sin funcionar:")
    print("  • Verificar logs en la terminal de Streamlit")
    print("  • Revisar que no haya errores de importación")
    print("  • Confirmar que el sistema RAG funciona en línea de comandos")

if __name__ == "__main__":
    print("🧪 PROBANDO SISTEMA RAG PARA INTERFAZ WEB")
    print("=" * 60)
    
    # Prueba 1: Formato de respuesta
    test1_ok = test_director_response_format()
    
    # Prueba 2: Compatibilidad web
    test2_ok = test_web_compatibility()
    
    # Mostrar instrucciones
    show_web_instructions()
    
    # Resumen
    print(f"\n📊 RESUMEN DE PRUEBAS:")
    print(f"  • Formato respuesta: {'✅' if test1_ok else '❌'}")
    print(f"  • Compatibilidad web: {'✅' if test2_ok else '❌'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 ¡El sistema debería funcionar en la interfaz web!")
    else:
        print("\n⚠️ Hay problemas que resolver antes de usar la web")
# src/agent_director.py

"""
Agente Director - Orquestador Inteligente
Decide automáticamente qué agente especializado usar:
- SQLAgent: Para consultas SQL (SELECT, INSERT, UPDATE, DELETE)
- DocsAgent: Para consultas de documentación técnica
También maneja consultas mixtas y proporciona interfaz unificada.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import logging
import json
import time
import re
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Importaciones de agentes especializados
try:
    from sql_agent import SQLAgent
    from docs_agent import DocsAgent
    logger.info("✅ Agentes especializados disponibles")
except ImportError as e:
    logger.error(f"❌ Error importando agentes: {e}")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AgentDirector:
    """Director que orquesta entre agentes especializados."""

    def __init__(self):
        """Inicializar director y agentes especializados."""
        
        # Inicializar agentes especializados
        try:
            self.sql_agent = SQLAgent()
            logger.info("✅ SQLAgent inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando SQLAgent: {e}")
            self.sql_agent = None

        try:
            self.docs_agent = DocsAgent()
            logger.info("✅ DocsAgent inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando DocsAgent: {e}")
            self.docs_agent = None

        if not self.sql_agent and not self.docs_agent:
            raise Exception("No se pudo inicializar ningún agente especializado")

        # Estadísticas del director
        self.director_stats = {
            'total_queries': 0,
            'sql_queries_routed': 0,
            'docs_queries_routed': 0,
            'mixed_queries': 0,
            'routing_errors': 0,
            'avg_routing_time': 0,
            'session_start': datetime.now().isoformat()
        }

        # Patrones para clasificación inteligente
        self.sql_patterns = {
            'select': ['select', 'consultar', 'obtener', 'mostrar', 'buscar', 'listar', 'query', 'tabla'],
            'insert': ['insert', 'insertar', 'agregar', 'añadir', 'crear registro', 'nuevo'],
            'update': ['update', 'actualizar', 'modificar', 'cambiar', 'editar'],
            'delete': ['delete', 'eliminar', 'borrar', 'quitar'],
            'database': ['base de datos', 'bd', 'sql server', 'tabla', 'campo', 'columna', 'clave']
        }

        self.docs_patterns = {
            'genexus': ['genexus', 'gx', 'for each', 'transaction', 'web panel', 'procedure'],
            'bantotal': ['bantotal', 'banco', 'financiero', 'proceso bancario', 'cliente bancario'],
            'technical': ['instalación', 'configuración', 'setup', 'deployment', 'manual'],
            'procedure': ['cómo', 'como', 'pasos', 'tutorial', 'guía', 'procedimiento'],
            'documentation': ['documentación', 'manual', 'ayuda', 'información', 'explicar']
        }

    def _classify_query_intent(self, query: str) -> Tuple[str, float]:
        """
        Clasificar la intención de la consulta.
        Retorna (tipo, confianza) donde tipo es 'sql', 'docs' o 'mixed'.
        """
        query_lower = query.lower()
        
        # Calcular puntuaciones
        sql_score = 0
        docs_score = 0
        
        # Evaluar patrones SQL
        for category, patterns in self.sql_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    sql_score += 1
                    if category in ['select', 'insert', 'update', 'delete']:
                        sql_score += 2  # Mayor peso para operaciones SQL directas
        
        # Evaluar patrones de documentación
        for category, patterns in self.docs_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    docs_score += 1
                    if category == 'procedure' and any(word in query_lower for word in ['cómo', 'como']):
                        docs_score += 2  # Mayor peso para consultas de procedimientos

        # Patrones específicos que indican SQL
        if any(word in query_lower for word in ['generar sql', 'query sql', 'select de', 'insert en', 'update de']):
            sql_score += 5

        # Patrones específicos que indican documentación
        if any(word in query_lower for word in ['documentación de', 'manual de', 'cómo hacer', 'explicar cómo']):
            docs_score += 5

        # Determinar tipo y confianza
        total_score = sql_score + docs_score
        
        if total_score == 0:
            return 'docs', 0.5  # Por defecto, documentación con baja confianza
        
        sql_confidence = sql_score / total_score
        docs_confidence = docs_score / total_score
        
        if sql_confidence > 0.7:
            return 'sql', sql_confidence
        elif docs_confidence > 0.7:
            return 'docs', docs_confidence
        elif abs(sql_confidence - docs_confidence) < 0.2:
            return 'mixed', 0.5
        elif sql_confidence > docs_confidence:
            return 'sql', sql_confidence
        else:
            return 'docs', docs_confidence

    def _handle_mixed_query(self, query: str) -> Dict[str, Any]:
        """Manejar consultas que requieren ambos agentes."""
        
        results = {
            'query': query,
            'intent': 'mixed',
            'sql_result': None,
            'docs_result': None,
            'combined_answer': '',
            'metadata': {
                'both_agents_used': True,
                'success': False
            }
        }

        # Intentar con ambos agentes
        if self.sql_agent:
            try:
                sql_result = self.sql_agent.generate_sql_query(query)
                results['sql_result'] = sql_result
            except Exception as e:
                logger.warning(f"⚠️ Error en SQLAgent para consulta mixta: {e}")

        if self.docs_agent:
            try:
                docs_result = self.docs_agent.query_documentation(query)
                results['docs_result'] = docs_result
            except Exception as e:
                logger.warning(f"⚠️ Error en DocsAgent para consulta mixta: {e}")

        # Combinar resultados
        answer_parts = []
        
        if results['sql_result'] and results['sql_result'].get('sql_generated'):
            answer_parts.append("## 🗄️ Consulta SQL Generada\n")
            answer_parts.append("```sql")
            answer_parts.append(results['sql_result']['sql_generated'])
            answer_parts.append("```\n")
            
            if results['sql_result'].get('explanation'):
                answer_parts.append(f"**Explicación:** {results['sql_result']['explanation']}\n")

        if results['docs_result'] and results['docs_result'].get('answer'):
            answer_parts.append("## 📚 Información de Documentación\n")
            answer_parts.append(results['docs_result']['answer'])

        if answer_parts:
            results['combined_answer'] = '\n'.join(answer_parts)
            results['metadata']['success'] = True
        else:
            results['combined_answer'] = "No se pudo generar una respuesta completa usando ambos agentes."

        return results

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Procesar consulta dirigiéndola al agente apropiado.
        
        Args:
            user_query: Consulta del usuario
            
        Returns:
            Resultado unificado con respuesta y metadatos
        """
        start_time = time.time()
        self.director_stats['total_queries'] += 1

        logger.info(f"🎯 Director procesando: '{user_query}'")

        # Clasificar intención
        intent, confidence = self._classify_query_intent(user_query)
        logger.info(f"🧠 Intención detectada: {intent} (confianza: {confidence:.2f})")

        try:
            if intent == 'sql' and self.sql_agent:
                # Dirigir a SQLAgent
                self.director_stats['sql_queries_routed'] += 1
                result = self.sql_agent.generate_sql_query(user_query)
                
                # Formatear respuesta unificada
                unified_result = {
                    'query': user_query,
                    'intent': 'sql',
                    'agent_used': 'SQLAgent',
                    'answer': self._format_sql_response(result),
                    'raw_result': result,
                    'metadata': {
                        'intent_confidence': confidence,
                        'agent_routing': 'sql',
                        'routing_time': time.time() - start_time,
                        'success': result['metadata']['success']
                    }
                }

            elif intent == 'docs' and self.docs_agent:
                # Dirigir a DocsAgent
                self.director_stats['docs_queries_routed'] += 1
                result = self.docs_agent.query_documentation(user_query)
                
                # Formatear respuesta unificada
                unified_result = {
                    'query': user_query,
                    'intent': 'docs',
                    'agent_used': 'DocsAgent',
                    'answer': result.get('answer', 'No se encontró respuesta'),
                    'raw_result': result,
                    'metadata': {
                        'intent_confidence': confidence,
                        'agent_routing': 'docs',
                        'routing_time': time.time() - start_time,
                        'success': result['metadata']['success']
                    }
                }

            elif intent == 'mixed':
                # Usar ambos agentes
                self.director_stats['mixed_queries'] += 1
                unified_result = self._handle_mixed_query(user_query)
                unified_result['metadata']['intent_confidence'] = confidence
                unified_result['metadata']['routing_time'] = time.time() - start_time

            else:
                # Fallback - usar el agente disponible
                if self.sql_agent:
                    logger.info("🔄 Fallback a SQLAgent")
                    result = self.sql_agent.generate_sql_query(user_query)
                    unified_result = {
                        'query': user_query,
                        'intent': 'fallback_sql',
                        'agent_used': 'SQLAgent (fallback)',
                        'answer': self._format_sql_response(result),
                        'raw_result': result,
                        'metadata': {
                            'intent_confidence': confidence,
                            'agent_routing': 'fallback_sql',
                            'routing_time': time.time() - start_time,
                            'success': result['metadata']['success']
                        }
                    }
                elif self.docs_agent:
                    logger.info("🔄 Fallback a DocsAgent")
                    result = self.docs_agent.query_documentation(user_query)
                    unified_result = {
                        'query': user_query,
                        'intent': 'fallback_docs',
                        'agent_used': 'DocsAgent (fallback)',
                        'answer': result.get('answer', 'No se encontró respuesta'),
                        'raw_result': result,
                        'metadata': {
                            'intent_confidence': confidence,
                            'agent_routing': 'fallback_docs',
                            'routing_time': time.time() - start_time,
                            'success': result['metadata']['success']
                        }
                    }
                else:
                    unified_result = {
                        'query': user_query,
                        'intent': 'error',
                        'agent_used': 'None',
                        'answer': 'No hay agentes especializados disponibles',
                        'raw_result': None,
                        'metadata': {
                            'intent_confidence': 0,
                            'agent_routing': 'error',
                            'routing_time': time.time() - start_time,
                            'success': False
                        }
                    }

        except Exception as e:
            logger.error(f"❌ Error en routing: {e}")
            self.director_stats['routing_errors'] += 1
            
            unified_result = {
                'query': user_query,
                'intent': 'error',
                'agent_used': 'None',
                'answer': f'Error procesando consulta: {str(e)}',
                'raw_result': None,
                'metadata': {
                    'intent_confidence': confidence,
                    'agent_routing': 'error',
                    'routing_time': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                }
            }

        # Actualizar estadísticas
        routing_time = unified_result['metadata']['routing_time']
        total_time = self.director_stats['total_queries']
        current_avg = self.director_stats['avg_routing_time']
        self.director_stats['avg_routing_time'] = (current_avg * (total_time - 1) + routing_time) / total_time

        logger.info(f"✅ Director completado: {intent} -> {unified_result['agent_used']} ({routing_time:.2f}s)")
        
        return unified_result

    def _format_sql_response(self, sql_result: Dict[str, Any]) -> str:
        """Formatear respuesta de SQLAgent para presentación unificada."""
        if not sql_result.get('sql_generated'):
            return sql_result.get('error', 'No se pudo generar consulta SQL')

        response_parts = [
            f"## 🗄️ Consulta {sql_result['operation']} Generada\n"
        ]

        # SQL generado
        response_parts.append("```sql")
        response_parts.append(sql_result['sql_generated'])
        response_parts.append("```\n")

        # Explicación si existe
        if sql_result.get('explanation'):
            response_parts.append(f"**Explicación:** {sql_result['explanation']}\n")

        # Advertencias si existen
        if sql_result.get('warnings'):
            response_parts.append("### ⚠️ Advertencias:")
            for warning in sql_result['warnings']:
                response_parts.append(f"- {warning}")
            response_parts.append("")

        # Fuentes consultadas
        if sql_result.get('sources'):
            response_parts.append("### 📚 Estructuras de Tabla Consultadas:")
            for i, source in enumerate(sql_result['sources'], 1):
                source_name = Path(source.get('source', '')).name or source.get('source', 'N/A')
                response_parts.append(f"{i}. {source_name}")

        return '\n'.join(response_parts)

    def get_director_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del director y agentes."""
        stats = {
            'director': self.director_stats.copy(),
            'agents': {}
        }

        # Estadísticas de agentes especializados
        if self.sql_agent:
            stats['agents']['sql'] = self.sql_agent.get_session_stats()

        if self.docs_agent:
            stats['agents']['docs'] = self.docs_agent.get_session_stats()

        # Calcular métricas agregadas
        total_queries = self.director_stats['total_queries']
        if total_queries > 0:
            stats['director']['sql_routing_rate'] = self.director_stats['sql_queries_routed'] / total_queries
            stats['director']['docs_routing_rate'] = self.director_stats['docs_queries_routed'] / total_queries
            stats['director']['mixed_routing_rate'] = self.director_stats['mixed_queries'] / total_queries
            stats['director']['error_rate'] = self.director_stats['routing_errors'] / total_queries

        return stats

    def suggest_query_improvements(self, query: str, result: Dict[str, Any]) -> List[str]:
        """Sugerir mejoras para consultas futuras."""
        suggestions = []
        
        intent = result.get('intent', '')
        confidence = result.get('metadata', {}).get('intent_confidence', 0)
        
        # Sugerencias basadas en confianza
        if confidence < 0.6:
            suggestions.append("Especifica más claramente si buscas generar SQL o consultar documentación")
        
        # Sugerencias específicas por tipo
        if intent == 'sql':
            if 'tabla' not in query.lower():
                suggestions.append("Menciona el nombre de la tabla específica para mejores resultados")
            if not any(op in query.lower() for op in ['select', 'insert', 'update', 'delete']):
                suggestions.append("Especifica la operación SQL deseada (SELECT, INSERT, UPDATE, DELETE)")
                
        elif intent == 'docs':
            if not any(tech in query.lower() for tech in ['genexus', 'bantotal']):
                suggestions.append("Especifica la tecnología (GeneXus o Bantotal) para respuestas más precisas")
            if 'cómo' not in query.lower() and 'como' not in query.lower():
                suggestions.append("Usa preguntas específicas como '¿cómo hacer...?' para mejores resultados")

        return suggestions


def main():
    """Función principal para pruebas desde línea de comandos."""
    import sys

    if len(sys.argv) < 2:
        print("""
🎯 Agente Director - Orquestador Inteligente

El Director decide automáticamente qué agente usar:
  🗄️ SQLAgent: Para consultas SQL (SELECT, INSERT, UPDATE, DELETE)
  📚 DocsAgent: Para documentación técnica (GeneXus, Bantotal, procedimientos)

Uso:
  python src/agent_director.py "tu consulta aquí"

Ejemplos que van a SQLAgent:
  python src/agent_director.py "SELECT de tabla abonados con todos los campos"
  python src/agent_director.py "generar INSERT para nuevo cliente"
  python src/agent_director.py "UPDATE datos del abonado"

Ejemplos que van a DocsAgent:
  python src/agent_director.py "cómo usar FOR EACH en GeneXus"
  python src/agent_director.py "proceso de creación de clientes en Bantotal"
  python src/agent_director.py "manual de instalación"

Ejemplos mixtos (ambos agentes):
  python src/agent_director.py "documentación de tabla abonados y generar SELECT"
  python src/agent_director.py "explicar estructura y crear consulta"

Capacidades:
  🧠 Clasificación inteligente de intención
  🎯 Routing automático al agente apropiado  
  🔄 Manejo de consultas mixtas
  📊 Estadísticas unificadas
  💡 Sugerencias de mejora
""")
        return

    query = ' '.join(sys.argv[1:])

    try:
        # Crear director
        director = AgentDirector()

        # Procesar consulta
        result = director.process_query(query)

        # Mostrar resultado
        print(f"\n🎯 CONSULTA: {result['query']}")
        print(f"🧠 INTENCIÓN: {result['intent'].title()}")
        print(f"🤖 AGENTE USADO: {result['agent_used']}")
        print(f"🎲 CONFIANZA: {result['metadata'].get('intent_confidence', 0):.2f}")
        
        print(f"\n📝 RESPUESTA:")
        print("=" * 80)
        print(result['answer'])
        print("=" * 80)

        # Sugerencias de mejora
        suggestions = director.suggest_query_improvements(query, result)
        if suggestions:
            print(f"\n💡 SUGERENCIAS PARA MEJORAR:")
            for suggestion in suggestions:
                print(f"   • {suggestion}")

        # Estadísticas
        metadata = result['metadata']
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Tiempo de routing: {metadata['routing_time']:.2f}s")
        print(f"   Éxito: {'Sí' if metadata['success'] else 'No'}")

        # Estadísticas del director
        stats = director.get_director_stats()
        director_stats = stats['director']
        print(f"   Total consultas: {director_stats['total_queries']}")
        print(f"   SQL routing: {director_stats['sql_queries_routed']}")
        print(f"   Docs routing: {director_stats['docs_queries_routed']}")
        print(f"   Consultas mixtas: {director_stats['mixed_queries']}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"\n❌ Error procesando consulta: {e}")


if __name__ == '__main__':
    main()
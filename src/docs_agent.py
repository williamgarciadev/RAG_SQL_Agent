# src/docs_agent.py

"""
Agente de Documentos Especializado
Se enfoca exclusivamente en consultas sobre documentación técnica:
- Manuales de GeneXus
- Documentación de Bantotal
- Guías técnicas y procedimientos
- Best practices y configuraciones
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

# Importaciones locales
try:
    from indexer import search_index, get_index_info, initialize_chroma_client

    logger.info("✅ Indexer disponible")
except ImportError as e:
    logger.error(f"❌ Error importando indexer: {e}")
    exit(1)

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Configuración
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
DEFAULT_MODEL = os.getenv('OLLAMA_CHAT_MODEL', 'llama3.2:latest')
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '5'))
MIN_SIMILARITY = float(os.getenv('MIN_SIMILARITY', '0.1'))


class DocsAgent:
    """Agente especializado exclusivamente en documentación técnica."""

    def __init__(
            self,
            model_name: str = DEFAULT_MODEL,
            ollama_url: str = OLLAMA_BASE_URL
    ):
        """Inicializar agente de documentos especializado."""
        self.model_name = model_name
        self.ollama_url = ollama_url

        # Verificar disponibilidad del índice
        self._check_index_availability()

        # Verificar disponibilidad de Ollama
        self.has_ollama = self._check_ollama_availability()

        # Estadísticas de sesión
        self.session_stats = {
            'doc_queries_processed': 0,
            'genexus_queries': 0,
            'bantotal_queries': 0,
            'technical_queries': 0,
            'procedure_queries': 0,
            'successful_responses': 0,
            'failed_responses': 0
        }

        # Tipos de documentación reconocidos
        self.doc_types = {
            'genexus': ['genexus', 'gx', 'for each', 'transaction', 'web panel', 'procedure'],
            'bantotal': ['bantotal', 'banco', 'financiero', 'préstamo', 'cuenta', 'cliente bancario'],
            'technical': ['instalación', 'configuración', 'setup', 'deployment', 'architecture'],
            'procedure': ['procedimiento', 'pasos', 'tutorial', 'guía', 'manual', 'how to']
        }

    def _check_index_availability(self):
        """Verificar que el índice vectorial esté disponible."""
        try:
            info = get_index_info()
            if not info.get('exists', False):
                raise Exception("Índice vectorial no existe")

            doc_count = info.get('live_count', 0)
            logger.info(f"✅ Índice documentos disponible: {doc_count} documentos")

        except Exception as e:
            logger.error(f"❌ Error verificando índice: {e}")
            logger.error("💡 Ejecuta: python src/indexer.py")
            raise

    def _check_ollama_availability(self):
        """Verificar disponibilidad de Ollama."""
        if not HAS_REQUESTS:
            logger.warning("⚠️ Sin requests - modo solo búsqueda directa")
            return False

        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                available_models = [m['name'] for m in models.get('models', [])]

                if self.model_name in available_models:
                    logger.info(f"✅ Ollama disponible: {self.model_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Modelo {self.model_name} no encontrado")
                    return False
            else:
                logger.warning(f"⚠️ Ollama responde con código {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"⚠️ Ollama no disponible: {e}")
            return False

    def _detect_documentation_type(self, query: str) -> str:
        """Detectar tipo de documentación solicitada."""
        query_lower = query.lower()

        # Contar coincidencias por tipo
        type_scores = {}
        for doc_type, keywords in self.doc_types.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                type_scores[doc_type] = score

        # Retornar el tipo con mayor puntuación
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]

        return 'general'

    def _extract_technical_concepts(self, query: str) -> List[str]:
        """Extraer conceptos técnicos específicos de la consulta."""
        concepts = []
        query_lower = query.lower()

        # Conceptos de GeneXus
        gx_concepts = [
            'for each', 'transaction', 'web panel', 'procedure', 'data provider',
            'business component', 'sdt', 'variable', 'attribute', 'table',
            'index', 'foreign key', 'generator', 'pattern', 'theme'
        ]

        # Conceptos de Bantotal
        bantotal_concepts = [
            'préstamo', 'cuenta corriente', 'ahorro', 'tarjeta', 'cliente',
            'sucursal', 'moneda', 'tasa', 'garantía', 'amortización',
            'contabilidad', 'balance', 'movimiento', 'transacción bancaria'
        ]

        # Conceptos técnicos generales
        tech_concepts = [
            'instalación', 'configuración', 'base de datos', 'servidor',
            'deployment', 'performance', 'optimización', 'backup',
            'seguridad', 'usuario', 'permisos', 'api', 'web service'
        ]

        all_concepts = gx_concepts + bantotal_concepts + tech_concepts

        for concept in all_concepts:
            if concept in query_lower:
                concepts.append(concept)

        return concepts

    def _retrieve_documentation_context(self, query: str) -> List[Dict[str, Any]]:
        """Recuperar contexto específico de documentación."""
        try:
            # Inicializar ChromaDB si es necesario
            initialize_chroma_client()

            # Detectar tipo de documentación
            doc_type = self._detect_documentation_type(query)
            logger.info(f"📋 Tipo de documentación: {doc_type}")

            # Extraer conceptos técnicos
            concepts = self._extract_technical_concepts(query)

            # Construir términos de búsqueda
            search_terms = [query]

            # Agregar conceptos específicos
            for concept in concepts:
                search_terms.append(concept)

            # Agregar términos por tipo de documentación
            if doc_type in self.doc_types:
                search_terms.extend(self.doc_types[doc_type][:3])  # Top 3 keywords

            # Buscar documentos excluyendo estructuras de BD
            all_results = []
            for term in search_terms[:5]:  # Limitar búsquedas
                try:
                    results = search_index(
                        query=term,
                        top_k=TOP_K_RESULTS,
                        filter_metadata=None  # Sin filtros para evitar errores de ChromaDB
                    )
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"⚠️ Error buscando '{term}': {e}")

            # Si no hay resultados específicos, buscar en general
            if not all_results:
                try:
                    results = search_index(query=query, top_k=TOP_K_RESULTS * 2)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"❌ Error en búsqueda general: {e}")

            # Filtrar manualmente para excluir estructuras de BD
            if all_results:
                filtered_results = []
                for result in all_results:
                    metadata = result.get('metadata', {})
                    source_type = metadata.get('source_type', '')

                    # Excluir documentos de estructura de BD
                    if source_type not in ['database_table', 'database_schema', 'database']:
                        filtered_results.append(result)

                all_results = filtered_results

            # Filtrar y deduplicar
            unique_results = []
            seen_ids = set()
            for result in all_results:
                if result.get('id') not in seen_ids and result.get('similarity', 0) >= MIN_SIMILARITY:
                    seen_ids.add(result.get('id'))
                    unique_results.append(result)

            # Ordenar por similitud y filtrar por tipo de fuente
            unique_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)

            logger.info(f"📚 Recuperados {len(unique_results)} documentos relevantes")
            return unique_results[:TOP_K_RESULTS]

        except Exception as e:
            logger.error(f"❌ Error en recuperación de documentos: {e}")
            return []

    def _build_documentation_context(self, documents: List[Dict[str, Any]], query: str, doc_type: str) -> str:
        """Construir contexto especializado para consultas de documentación."""
        if not documents:
            return "No se encontraron documentos técnicos relevantes."

        context_parts = [
            f"=== DOCUMENTACIÓN {doc_type.upper()} RELEVANTE ===\n"
        ]

        # Agrupar documentos por tipo de fuente
        files_docs = [d for d in documents if d.get('metadata', {}).get('source_type') == 'file']
        web_docs = [d for d in documents if d.get('metadata', {}).get('source_type') == 'web']

        if files_docs:
            context_parts.append("📄 DOCUMENTOS LOCALES:\n")
            for i, doc in enumerate(files_docs, 1):
                metadata = doc.get('metadata', {})
                filename = metadata.get('filename', 'Archivo desconocido')
                similarity = doc.get('similarity', 0)

                doc_info = f"\n--- DOCUMENTO {i}: {filename} ---"
                doc_info += f"\nRelevancia: {similarity:.3f}"
                doc_info += f"\nContenido:\n{doc.get('text', '')[:800]}..."

                context_parts.append(doc_info)

        if web_docs:
            context_parts.append("\n🌐 RECURSOS WEB:\n")
            for i, doc in enumerate(web_docs, 1):
                metadata = doc.get('metadata', {})
                source = metadata.get('source', 'URL desconocida')
                similarity = doc.get('similarity', 0)

                doc_info = f"\n--- RECURSO WEB {i} ---"
                doc_info += f"\nFuente: {source}"
                doc_info += f"\nRelevancia: {similarity:.3f}"
                doc_info += f"\nContenido:\n{doc.get('text', '')[:800]}..."

                context_parts.append(doc_info)

        context_parts.append(f"\n{'=' * 60}\n")
        return "".join(context_parts)

    def _generate_documentation_prompt(self, query: str, context: str, doc_type: str) -> str:
        """Generar prompt especializado para consultas de documentación."""

        type_instructions = {
            'genexus': """
Eres un experto en GeneXus con años de experiencia en desarrollo.
Enfócate en:
- Sintaxis exacta de comandos y objetos
- Best practices de desarrollo
- Patrones de diseño recomendados
- Configuraciones específicas
- Solución de problemas comunes
""",
            'bantotal': """
Eres un especialista en sistemas bancarios Bantotal.
Enfócate en:
- Procesos bancarios y financieros
- Configuración de productos
- Procedimientos operativos
- Integraciones típicas
- Manejo de clientes y cuentas
""",
            'technical': """
Eres un arquitecto de software especializado en sistemas empresariales.
Enfócate en:
- Configuraciones de sistema
- Arquitectura y deployment
- Optimización de rendimiento
- Seguridad y mejores prácticas
- Troubleshooting técnico
""",
            'procedure': """
Eres un documentalista técnico experto en crear guías claras.
Enfócate en:
- Pasos detallados y ordenados
- Prerequisitos y consideraciones
- Ejemplos prácticos
- Posibles problemas y soluciones
- Verificación de resultados
"""
        }

        instruction = type_instructions.get(doc_type, """
Eres un consultor técnico especializado en sistemas empresariales.
Proporciona información precisa y práctica basada en la documentación.
""")

        base_prompt = f"""{instruction.strip()}

INSTRUCCIONES ESPECÍFICAS:
1. Responder ÚNICAMENTE basándote en la documentación proporcionada
2. Si la información no está disponible, indicarlo claramente
3. Proporcionar ejemplos prácticos cuando sea posible
4. Explicar en términos claros pero técnicamente precisos
5. Incluir advertencias o consideraciones importantes
6. Citar las fuentes cuando sea relevante

DOCUMENTACIÓN DISPONIBLE:
{context}

CONSULTA DEL USUARIO: {query}

RESPUESTA ESPECIALIZADA:"""

        return base_prompt

    def query_documentation(self, user_query: str) -> Dict[str, Any]:
        """Procesar consulta sobre documentación técnica."""
        start_time = time.time()
        self.session_stats['doc_queries_processed'] += 1

        logger.info(f"📚 Consultando documentación: '{user_query}'")

        # Detectar tipo de documentación
        doc_type = self._detect_documentation_type(user_query)
        logger.info(f"📋 Tipo detectado: {doc_type}")

        # Actualizar estadísticas por tipo
        stat_key = f"{doc_type}_queries"
        if stat_key in self.session_stats:
            self.session_stats[stat_key] += 1

        # Recuperar contexto de documentación
        documents = self._retrieve_documentation_context(user_query)

        if not documents:
            return {
                'query': user_query,
                'answer': None,
                'doc_type': doc_type,
                'error': "No se encontró documentación relevante para tu consulta",
                'suggestions': [
                    "Intenta usar términos más específicos",
                    "Verifica que hay documentos indexados del tema",
                    "Especifica si buscas info de GeneXus o Bantotal",
                    "Pregunta sobre procedimientos o configuraciones específicas"
                ],
                'metadata': {
                    'success': False,
                    'total_time': time.time() - start_time
                }
            }

        # Construir contexto especializado
        context = self._build_documentation_context(documents, user_query, doc_type)

        # Generar respuesta
        if self.has_ollama:
            doc_result = self._generate_answer_with_ai(user_query, context, doc_type)
        else:
            doc_result = self._generate_answer_fallback(user_query, context, doc_type)

        # Resultado final
        total_time = time.time() - start_time

        result = {
            'query': user_query,
            'answer': doc_result['answer'],
            'doc_type': doc_type,
            'concepts_found': self._extract_technical_concepts(user_query),
            'recommendations': doc_result.get('recommendations', []),
            'related_topics': doc_result.get('related_topics', []),
            'sources': [
                {
                    'source': doc['metadata'].get('source', ''),
                    'type': doc['metadata'].get('source_type', ''),
                    'filename': doc['metadata'].get('filename', ''),
                    'similarity': doc.get('similarity', 0),
                    'excerpt': doc.get('text', '')[:200] + "..." if len(doc.get('text', '')) > 200 else doc.get('text',
                                                                                                                '')
                }
                for doc in documents
            ],
            'metadata': {
                'documentation_type': doc_type,
                'documents_found': len(documents),
                'total_time': total_time,
                'has_ai': self.has_ollama,
                'timestamp': datetime.now().isoformat(),
                'success': doc_result['answer'] is not None
            }
        }

        if result['metadata']['success']:
            self.session_stats['successful_responses'] += 1
        else:
            self.session_stats['failed_responses'] += 1

        logger.info(f"✅ Respuesta documentación generada ({total_time:.2f}s)")
        return result

    def _generate_answer_with_ai(self, query: str, context: str, doc_type: str) -> Dict[str, Any]:
        """Generar respuesta usando IA (Ollama)."""
        try:
            prompt = self._generate_documentation_prompt(query, context, doc_type)

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Moderadamente creativo pero preciso
                        "top_p": 0.9,
                        "max_tokens": 2000
                    }
                },
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                answer_text = result.get('response', '').strip()

                # Extraer recomendaciones y temas relacionados
                recommendations = self._extract_recommendations_from_answer(answer_text)
                related_topics = self._extract_related_topics_from_answer(answer_text, doc_type)

                return {
                    'answer': answer_text,
                    'recommendations': recommendations,
                    'related_topics': related_topics
                }
            else:
                logger.error(f"❌ Error Ollama: {response.status_code}")
                return self._generate_answer_fallback(query, context, doc_type)

        except Exception as e:
            logger.error(f"❌ Error generando respuesta con IA: {e}")
            return self._generate_answer_fallback(query, context, doc_type)

    def _generate_answer_fallback(self, query: str, context: str, doc_type: str) -> Dict[str, Any]:
        """Generar respuesta sin IA usando extracción de información."""

        # Extraer información relevante del contexto
        answer_parts = []

        # Agregar introducción basada en el tipo
        type_intros = {
            'genexus': '## 🔧 Información sobre GeneXus\n\n',
            'bantotal': '## 🏦 Información sobre Bantotal\n\n',
            'technical': '## ⚙️ Información Técnica\n\n',
            'procedure': '## 📋 Procedimiento\n\n'
        }

        answer_parts.append(type_intros.get(doc_type, '## 📚 Información Encontrada\n\n'))

        # Extraer información clave de los documentos
        if "DOCUMENTO 1" in context or "RECURSO WEB 1" in context:
            # Procesar documentos individuales
            docs_sections = re.split(r'--- (DOCUMENTO|RECURSO WEB) \d+', context)

            for i, section in enumerate(docs_sections[1:], 1):
                if '---' in section:
                    lines = section.split('\n')
                    content_started = False
                    relevant_content = []

                    for line in lines:
                        if 'Contenido:' in line:
                            content_started = True
                            continue

                        if content_started and line.strip():
                            relevant_content.append(line.strip())
                            if len(relevant_content) >= 5:  # Limitar extracto
                                break

                    if relevant_content:
                        answer_parts.append(f"### 📄 Fuente {i}\n")
                        answer_parts.append('\n'.join(relevant_content[:3]))
                        answer_parts.append('\n\n')

        # Agregar información de contexto general si no hay documentos específicos
        if len(answer_parts) == 1:  # Solo el header
            answer_parts.append("Basándome en la documentación disponible:\n\n")

            # Extraer primeras líneas relevantes del contexto
            context_lines = context.split('\n')
            relevant_lines = []

            for line in context_lines:
                if len(line.strip()) > 20 and not line.startswith('---') and 'Relevancia:' not in line:
                    relevant_lines.append(line.strip())
                    if len(relevant_lines) >= 8:
                        break

            if relevant_lines:
                answer_parts.extend(relevant_lines[:5])
                answer_parts.append('\n\n')

        # Agregar recomendaciones genéricas
        recommendations = []
        related_topics = []

        if doc_type == 'genexus':
            recommendations = [
                "Consultar la documentación oficial de GeneXus",
                "Revisar ejemplos en GeneXus Training",
                "Verificar la versión específica que estás usando"
            ]
            related_topics = ["Patterns", "Business Components", "Web Panels", "Procedures"]

        elif doc_type == 'bantotal':
            recommendations = [
                "Verificar configuración del módulo específico",
                "Consultar manual de operaciones",
                "Revisar con el administrador del sistema"
            ]
            related_topics = ["Clientes", "Productos", "Contabilidad", "Reportes"]

        else:
            recommendations = [
                "Revisar documentación técnica específica",
                "Consultar con el equipo técnico",
                "Verificar configuraciones del sistema"
            ]

        # Finalizar respuesta
        answer_parts.append("\n---\n")
        answer_parts.append(
            "💡 **Nota:** Esta respuesta se basa en búsqueda de documentos técnicos sin procesamiento de IA avanzado.")

        return {
            'answer': ''.join(answer_parts),
            'recommendations': recommendations,
            'related_topics': related_topics
        }

    def _extract_recommendations_from_answer(self, answer: str) -> List[str]:
        """Extraer recomendaciones del texto de respuesta."""
        recommendations = []

        # Buscar patrones de recomendaciones
        rec_patterns = [
            r'Recomendación:? (.+)',
            r'Se recomienda (.+)',
            r'Es recomendable (.+)',
            r'Deberías (.+)',
            r'Te sugiero (.+)'
        ]

        for pattern in rec_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            recommendations.extend(matches)

        # Limpiar y limitar
        clean_recs = []
        for rec in recommendations:
            clean_rec = rec.strip().rstrip('.')
            if len(clean_rec) > 10 and clean_rec not in clean_recs:
                clean_recs.append(clean_rec)

        return clean_recs[:3]  # Máximo 3 recomendaciones

    def _extract_related_topics_from_answer(self, answer: str, doc_type: str) -> List[str]:
        """Extraer temas relacionados del contexto y tipo de documentación."""
        related_topics = []
        answer_lower = answer.lower()

        # Temas por tipo de documentación
        topic_keywords = {
            'genexus': {
                'development': ['transaction', 'web panel', 'procedure', 'business component'],
                'data': ['sdt', 'variable', 'attribute', 'table', 'index'],
                'patterns': ['work with', 'transaction', 'pattern', 'template'],
                'deployment': ['deployment', 'generator', 'environment', 'build']
            },
            'bantotal': {
                'clients': ['cliente', 'persona', 'empresa', 'tercero'],
                'products': ['producto', 'cuenta', 'préstamo', 'depósito'],
                'operations': ['transacción', 'movimiento', 'operación', 'proceso'],
                'configuration': ['parametrización', 'configuración', 'setup', 'módulo']
            },
            'technical': {
                'installation': ['instalación', 'setup', 'configuración', 'deployment'],
                'performance': ['performance', 'optimización', 'tuning', 'monitoring'],
                'security': ['seguridad', 'permisos', 'autenticación', 'autorización'],
                'integration': ['integración', 'api', 'web service', 'interface']
            }
        }

        # Buscar temas mencionados en la respuesta
        if doc_type in topic_keywords:
            for category, keywords in topic_keywords[doc_type].items():
                for keyword in keywords:
                    if keyword in answer_lower:
                        related_topics.append(category.title())
                        break  # Solo agregar la categoría una vez

        # Agregar temas específicos encontrados
        specific_topics = []
        for line in answer.split('\n'):
            if any(word in line.lower() for word in ['ver también', 'relacionado', 'consultar']):
                # Extraer temas mencionados
                words = line.split()
                for word in words:
                    if len(word) > 4 and word.isalpha():
                        specific_topics.append(word.title())

        related_topics.extend(specific_topics[:3])

        return list(set(related_topics))[:5]  # Máximo 5 temas únicos

    def get_session_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la sesión de documentación."""
        total_queries = self.session_stats['doc_queries_processed']

        return {
            **self.session_stats,
            'success_rate': (
                    self.session_stats['successful_responses'] / max(1, total_queries)
            ),
            'most_used_doc_type': max(
                ['genexus', 'bantotal', 'technical', 'procedure'],
                key=lambda doc_type: self.session_stats.get(f'{doc_type}_queries', 0)
            ),
            'avg_documents_per_query': sum([
                self.session_stats.get(f'{t}_queries', 0)
                for t in ['genexus', 'bantotal', 'technical', 'procedure']
            ]) / max(1, total_queries)
        }


def main():
    """Función principal para pruebas desde línea de comandos."""
    import sys

    if len(sys.argv) < 2:
        print("""
📚 Agente de Documentos Especializado - Consultas Técnicas

Uso:
  python src/docs_agent.py "tu consulta sobre documentación"

Ejemplos para GeneXus:
  python src/docs_agent.py "cómo usar FOR EACH en GeneXus"
  python src/docs_agent.py "crear Web Panel con filtros"
  python src/docs_agent.py "sintaxis de procedimientos"

Ejemplos para Bantotal:
  python src/docs_agent.py "proceso de creación de clientes"
  python src/docs_agent.py "configurar productos bancarios"
  python src/docs_agent.py "manejo de garantías"

Ejemplos Técnicos:
  python src/docs_agent.py "instalación de GeneXus"
  python src/docs_agent.py "configurar base de datos"
  python src/docs_agent.py "optimizar rendimiento"

Ejemplos de Procedimientos:
  python src/docs_agent.py "pasos para deployment"
  python src/docs_agent.py "tutorial de configuración"
  python src/docs_agent.py "guía de troubleshooting"

Capacidades:
  ✅ Consulta manuales y documentación técnica
  ✅ Detecta automáticamente el tipo de documentación
  ✅ Proporciona respuestas contextualizadas
  ✅ Incluye recomendaciones y temas relacionados
  ✅ Cita fuentes específicas de documentos
""")
        return

    query = ' '.join(sys.argv[1:])

    try:
        # Crear agente de documentos
        agent = DocsAgent()

        # Procesar consulta
        result = agent.query_documentation(query)

        # Mostrar resultado
        print(f"\n📚 CONSULTA: {result['query']}")
        print(f"📋 TIPO DE DOCUMENTACIÓN: {result['doc_type'].title()}")

        if result.get('concepts_found'):
            print(f"🔍 CONCEPTOS ENCONTRADOS: {', '.join(result['concepts_found'])}")

        if result['answer']:
            print(f"\n📖 RESPUESTA:")
            print("=" * 80)
            print(result['answer'])
            print("=" * 80)

            if result.get('recommendations'):
                print(f"\n💡 RECOMENDACIONES:")
                for i, rec in enumerate(result['recommendations'], 1):
                    print(f"   {i}. {rec}")

            if result.get('related_topics'):
                print(f"\n🔗 TEMAS RELACIONADOS:")
                print(f"   {', '.join(result['related_topics'])}")
        else:
            print(f"\n❌ ERROR: {result.get('error', 'No se pudo generar respuesta')}")

            if result.get('suggestions'):
                print(f"\n💡 SUGERENCIAS:")
                for suggestion in result['suggestions']:
                    print(f"   • {suggestion}")

        if result.get('sources'):
            print(f"\n📚 FUENTES CONSULTADAS:")
            for i, source in enumerate(result['sources'], 1):
                if source.get('filename'):
                    source_name = source['filename']
                else:
                    source_name = Path(source.get('source', '')).name or 'N/A'

                print(f"   {i}. {source_name}")
                print(f"      Tipo: {source.get('type', 'N/A')}")
                print(f"      Similitud: {source.get('similarity', 0):.3f}")
                if source.get('excerpt'):
                    print(f"      Extracto: {source['excerpt'][:100]}...")
                print()

        # Estadísticas
        metadata = result['metadata']
        print(f"📊 ESTADÍSTICAS:")
        print(f"   Tiempo: {metadata['total_time']:.2f}s")
        print(f"   Documentos encontrados: {metadata['documents_found']}")
        print(f"   IA disponible: {'Sí' if metadata['has_ai'] else 'No'}")

        # Estadísticas de sesión
        stats = agent.get_session_stats()
        print(f"   Consultas en sesión: {stats['doc_queries_processed']}")
        print(f"   Tipo más consultado: {stats['most_used_doc_type'].title()}")
        print(f"   Tasa de éxito: {stats['success_rate']:.1%}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"\n❌ Error procesando consulta: {e}")


if __name__ == '__main__':
    main()
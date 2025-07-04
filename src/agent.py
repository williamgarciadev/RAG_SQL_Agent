# src/agent.py

"""
Agente RAG que orquesta la recuperación de documentos y generación de respuestas.
Combina búsqueda semántica con LLMs para responder preguntas sobre la base de conocimiento.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import logging
import json
import time
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

# Importaciones opcionales para LLMs
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logger.warning("⚠️ requests no disponible - funcionalidad LLM limitada")

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    logger.debug("python-dotenv no disponible")

# Configuración
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
DEFAULT_MODEL = os.getenv('OLLAMA_CHAT_MODEL', 'llama3.2:latest')
MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', '4000'))
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '5'))
MIN_SIMILARITY = float(os.getenv('MIN_SIMILARITY', '0.1'))


class RAGAgent:
    """Agente RAG que combina recuperación de documentos con generación de respuestas."""

    def __init__(
            self,
            model_name: str = DEFAULT_MODEL,
            ollama_url: str = OLLAMA_BASE_URL,
            top_k: int = TOP_K_RESULTS,
            min_similarity: float = MIN_SIMILARITY
    ):
        """
        Inicializar agente RAG.

        Args:
            model_name: Modelo de Ollama para generación
            ollama_url: URL del servidor Ollama
            top_k: Número máximo de documentos a recuperar
            min_similarity: Similitud mínima para incluir documentos
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.top_k = top_k
        self.min_similarity = min_similarity

        # Verificar disponibilidad del índice
        self._check_index_availability()

        # Verificar disponibilidad de Ollama
        self._check_ollama_availability()

        # Estadísticas de sesión
        self.session_stats = {
            'queries_count': 0,
            'total_retrieval_time': 0,
            'total_generation_time': 0,
            'successful_responses': 0,
            'failed_responses': 0
        }

    def _check_index_availability(self):
        """Verificar que el índice vectorial esté disponible."""
        try:
            info = get_index_info()
            if not info.get('exists', False):
                raise Exception("Índice vectorial no existe")

            doc_count = info.get('live_count', 0)
            logger.info(f"✅ Índice disponible: {doc_count} documentos")

        except Exception as e:
            logger.error(f"❌ Error verificando índice: {e}")
            logger.error("💡 Ejecuta: python src/indexer.py")
            raise

    def _check_ollama_availability(self):
        """Verificar disponibilidad de Ollama."""
        if not HAS_REQUESTS:
            logger.warning("⚠️ Sin requests - modo solo recuperación")
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
                    logger.info(f"💡 Modelos disponibles: {available_models}")
                    return False
            else:
                logger.warning(f"⚠️ Ollama responde con código {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"⚠️ Ollama no disponible: {e}")
            logger.info("💡 Ejecuta: ollama serve")
            return False

    def retrieve_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Recuperar documentos relevantes para la consulta.

        Args:
            query: Consulta del usuario

        Returns:
            Lista de documentos relevantes con metadatos
        """
        start_time = time.time()

        try:
            # Inicializar ChromaDB si es necesario
            initialize_chroma_client()

            # Buscar documentos
            results = search_index(
                query=query,
                top_k=self.top_k,
                filter_metadata=None
            )

            # Filtrar por similitud mínima
            filtered_results = [
                r for r in results
                if r.get('similarity', 0) >= self.min_similarity
            ]

            retrieval_time = time.time() - start_time
            self.session_stats['total_retrieval_time'] += retrieval_time

            logger.info(f"📋 Recuperados {len(filtered_results)} documentos ({retrieval_time:.2f}s)")

            return filtered_results

        except Exception as e:
            logger.error(f"❌ Error en recuperación: {e}")
            return []

    def _build_context(self, documents: List[Dict[str, Any]], query: str) -> str:
        """Construir contexto para el LLM desde documentos recuperados."""
        if not documents:
            return "No se encontraron documentos relevantes."

        context_parts = [
            "=== DOCUMENTOS RELEVANTES ===\n"
        ]

        total_chars = 0
        for i, doc in enumerate(documents, 1):
            # Información del documento
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Fuente desconocida')
            source_type = metadata.get('source_type', 'N/A')
            similarity = doc.get('similarity', 0)

            # Texto del documento (truncar si es muy largo)
            text = doc.get('text', '')
            if len(text) > 800:
                text = text[:800] + "..."

            doc_info = f"\n--- DOCUMENTO {i} ---"
            doc_info += f"\nFuente: {Path(source).name if source_type == 'file' else source}"
            doc_info += f"\nTipo: {source_type}"
            doc_info += f"\nRelevancia: {similarity:.3f}"
            doc_info += f"\nContenido:\n{text}\n"

            # Verificar límite de contexto
            if total_chars + len(doc_info) > MAX_CONTEXT_LENGTH:
                context_parts.append(
                    f"\n[... {len(documents) - i + 1} documentos adicionales omitidos por límite de contexto ...]")
                break

            context_parts.append(doc_info)
            total_chars += len(doc_info)

        return "".join(context_parts)

    def generate_response(self, query: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generar respuesta usando LLM con el contexto recuperado.

        Args:
            query: Consulta original del usuario
            context: Contexto construido desde documentos

        Returns:
            Tupla de (respuesta, metadatos_generacion)
        """
        if not HAS_REQUESTS:
            return self._generate_fallback_response(query, context)

        start_time = time.time()

        # Construir prompt
        system_prompt = """Eres un asistente experto en sistemas bancarios Bantotal y programación GeneXus/SQL. 

Tu tarea es responder preguntas utilizando únicamente la información proporcionada en los documentos de contexto.

INSTRUCCIONES ESPECIALES:
1. Si te piden generar código SQL, consultas o queries, debes crearlos basándote en la información técnica disponible
2. Para consultas SQL sobre tablas de Bantotal, usa los nombres de campos y estructuras que aparecen en la documentación
3. Si la información específica no está disponible, pero hay información relacionada, menciona qué información SÍ tienes disponible
4. Cita las fuentes cuando sea relevante (nombre del archivo o URL)
5. Sé preciso y técnico cuando sea apropiado
6. Para queries SQL, incluye comentarios explicativos
7. Si hay múltiples opciones o enfoques, menciónalos
8. Responde en español de manera clara y profesional

FORMATO PARA CÓDIGO SQL:
- Usa nombres de tablas y campos exactos de la documentación
- Incluye filtros importantes (como d601co = 'S' para registros confirmados)
- Agrega comentarios explicativos
- Ordena los resultados de manera lógica

DOCUMENTOS DE CONTEXTO:
{context}

PREGUNTA DEL USUARIO: {query}

RESPUESTA:"""

        prompt = system_prompt.format(context=context, query=query)

        try:
            # Realizar petición a Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 1000
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()

                generation_time = time.time() - start_time
                self.session_stats['total_generation_time'] += generation_time
                self.session_stats['successful_responses'] += 1

                metadata = {
                    'model_used': self.model_name,
                    'generation_time': generation_time,
                    'tokens_generated': len(answer.split()),
                    'prompt_length': len(prompt),
                    'success': True
                }

                logger.info(f"✅ Respuesta generada ({generation_time:.2f}s)")
                return answer, metadata

            else:
                logger.error(f"❌ Error Ollama: {response.status_code}")
                self.session_stats['failed_responses'] += 1
                return self._generate_fallback_response(query, context)

        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            self.session_stats['failed_responses'] += 1
            return self._generate_fallback_response(query, context)

    def _generate_fallback_response(self, query: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """Generar respuesta de fallback sin LLM usando análisis de texto."""

        # Extraer información clave de los documentos
        response_parts = []

        # Analizar query para determinar tipo de respuesta
        query_lower = query.lower()
        is_table_query = any(word in query_lower for word in ['tabla', 'table', 'fse', 'fst', 'contiene'])
        is_how_query = any(word in query_lower for word in ['cómo', 'como', 'how', 'pasos', 'proceso'])
        is_what_query = any(word in query_lower for word in ['qué', 'que', 'what', 'cuál', 'cual'])

        # Procesar documentos del contexto
        if "DOCUMENTO 1" in context:
            # Extraer información de cada documento
            docs = context.split("--- DOCUMENTO")
            relevant_info = []

            for doc in docs[1:]:  # Saltar el header
                if "---" in doc:
                    lines = doc.split('\n')
                    source_line = next((line for line in lines if "Fuente:" in line), "")
                    content_lines = []

                    # Extraer contenido relevante
                    in_content = False
                    for line in lines:
                        if "Contenido:" in line:
                            in_content = True
                            content_lines.append(line.replace("Contenido:", "").strip())
                        elif in_content and line.strip():
                            content_lines.append(line.strip())

                    if content_lines:
                        content = " ".join(content_lines)
                        source = source_line.replace("Fuente:", "").strip()

                        # Extraer información específica según el tipo de consulta
                        if is_table_query and any(table in content.upper() for table in ['FSE', 'FST', 'TABLA']):
                            relevant_info.append(f"📄 **{source}:**\n{content[:300]}...")
                        elif is_how_query and any(
                                word in content.lower() for word in ['paso', 'proceso', 'instalación', 'configurar']):
                            relevant_info.append(f"🔧 **{source}:**\n{content[:300]}...")
                        elif content:
                            relevant_info.append(f"📋 **{source}:**\n{content[:200]}...")

            if relevant_info:
                if is_table_query:
                    response_parts.append("## 🗃️ Información sobre Tablas del Sistema")
                    response_parts.append("Basándome en la documentación encontrada:")
                elif is_how_query:
                    response_parts.append("## 🔧 Proceso/Procedimiento")
                    response_parts.append("Según la documentación:")
                elif is_what_query:
                    response_parts.append("## 📋 Información Encontrada")
                    response_parts.append("De acuerdo a los documentos:")

                response_parts.extend(relevant_info[:3])  # Máximo 3 fuentes

                response_parts.append("\n---")
                response_parts.append(
                    "💡 **Nota:** Esta respuesta se basa en búsqueda de documentos sin procesamiento de IA.")

        if not response_parts:
            response_parts.append("## 🔍 Información Encontrada")
            response_parts.append("Se encontraron documentos relacionados con tu consulta:")
            response_parts.append(context[:500] + "...")

        # Agregar sugerencias para habilitar IA
        response_parts.extend([
            "\n---",
            "## 🤖 Para Respuestas Mejoradas con IA",
            "Para obtener respuestas más precisas y contextualizadas:",
            "",
            "1. **Instalar Ollama:** https://ollama.ai",
            "2. **Ejecutar servidor:** `ollama serve`",
            "3. **Descargar modelo:** `ollama pull llama3.2:3b`",
            "",
            "**Modelos recomendados:**",
            "- `phi3:mini` (2GB) - Rápido y eficiente",
            "- `llama3.2:3b` (2GB) - Buena calidad",
            "- `llama3.2:latest` (7GB) - Máxima calidad"
        ])

        response = "\n".join(response_parts)

        metadata = {
            'model_used': 'fallback_enhanced',
            'generation_time': 0,
            'success': True,  # Cambiado a True porque sí genera respuesta útil
            'fallback_reason': 'LLM no disponible - usando análisis de texto',
            'query_type': 'table' if is_table_query else 'how' if is_how_query else 'what' if is_what_query else 'general'
        }

        return response, metadata

    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Procesar consulta completa: recuperación + generación.

        Args:
            user_query: Pregunta del usuario

        Returns:
            Diccionario con respuesta completa y metadatos
        """
        start_time = time.time()
        self.session_stats['queries_count'] += 1

        logger.info(f"🔍 Procesando consulta: '{user_query}'")

        # 1. Recuperar documentos relevantes
        documents = self.retrieve_documents(user_query)

        if not documents:
            return {
                'query': user_query,
                'answer': "No se encontraron documentos relevantes para tu consulta. Intenta con términos diferentes o más específicos.",
                'sources': [],
                'metadata': {
                    'documents_found': 0,
                    'total_time': time.time() - start_time,
                    'success': False
                }
            }

        # 2. Construir contexto
        context = self._build_context(documents, user_query)

        # 3. Generar respuesta
        answer, gen_metadata = self.generate_response(user_query, context)

        # 4. Preparar respuesta completa
        total_time = time.time() - start_time

        result = {
            'query': user_query,
            'answer': answer,
            'sources': [
                {
                    'source': doc['metadata'].get('source', ''),
                    'type': doc['metadata'].get('source_type', ''),
                    'similarity': doc.get('similarity', 0),
                    'excerpt': doc.get('text', '')[:200] + "..." if len(doc.get('text', '')) > 200 else doc.get('text',
                                                                                                                '')
                }
                for doc in documents
            ],
            'metadata': {
                'documents_found': len(documents),
                'total_time': total_time,
                'generation_metadata': gen_metadata,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
        }

        logger.info(f"✅ Consulta completada ({total_time:.2f}s)")
        return result

    def get_session_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la sesión actual."""
        return {
            **self.session_stats,
            'avg_retrieval_time': (
                    self.session_stats['total_retrieval_time'] / max(1, self.session_stats['queries_count'])
            ),
            'avg_generation_time': (
                    self.session_stats['total_generation_time'] / max(1, self.session_stats['successful_responses'])
            ),
            'success_rate': (
                    self.session_stats['successful_responses'] / max(1, self.session_stats['queries_count'])
            )
        }


def main():
    """Función principal para pruebas desde línea de comandos."""
    import sys

    if len(sys.argv) < 2:
        print("""
🤖 Agente RAG - Consultas sobre Bantotal y GeneXus

Uso:
  python src/agent.py "tu consulta aquí"

Ejemplos:
  python src/agent.py "como crear un préstamo en Bantotal"
  python src/agent.py "sintaxis comando for each GeneXus"
  python src/agent.py "tabla FSE601 que contiene"
""")
        return

    query = ' '.join(sys.argv[1:])

    try:
        # Crear agente
        agent = RAGAgent()

        # Procesar consulta
        result = agent.query(query)

        # Mostrar resultado
        print(f"\n🔍 CONSULTA: {result['query']}")
        print(f"\n🤖 RESPUESTA:")
        print(result['answer'])

        if result['sources']:
            print(f"\n📚 FUENTES ({len(result['sources'])} documentos):")
            for i, source in enumerate(result['sources'], 1):
                print(f"\n{i}. {Path(source['source']).name if source['type'] == 'file' else source['source']}")
                print(f"   Relevancia: {source['similarity']:.3f}")
                print(f"   Extracto: {source['excerpt']}")

        # Estadísticas
        metadata = result['metadata']
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Tiempo total: {metadata['total_time']:.2f}s")
        print(f"   Documentos encontrados: {metadata['documents_found']}")

        # Estadísticas de sesión
        stats = agent.get_session_stats()
        print(f"   Consultas en sesión: {stats['queries_count']}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"\n❌ Error procesando consulta: {e}")


if __name__ == '__main__':
    main()
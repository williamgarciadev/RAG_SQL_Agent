# src/sql_agent.py

"""
Agente SQL Especializado
Se enfoca exclusivamente en generar consultas SQL: SELECT, INSERT, UPDATE, DELETE
Optimizado para estructuras de bases de datos bancarios como Bantotal.
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
    from database_explorer import DatabaseExplorer

    HAS_DB_EXPLORER = True
except ImportError:
    HAS_DB_EXPLORER = False

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
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '3'))
MIN_SIMILARITY = float(os.getenv('MIN_SIMILARITY', '0.2'))


class SQLAgent:
    """Agente especializado exclusivamente en consultas SQL."""

    def __init__(
            self,
            model_name: str = DEFAULT_MODEL,
            ollama_url: str = OLLAMA_BASE_URL
    ):
        """Inicializar agente SQL especializado."""
        self.model_name = model_name
        self.ollama_url = ollama_url

        # Verificar disponibilidad del índice
        self._check_index_availability()

        # Verificar disponibilidad de Ollama
        self.has_ollama = self._check_ollama_availability()

        # Cargar explorador de BD si está disponible
        self.explorer = None
        if HAS_DB_EXPLORER:
            try:
                self.explorer = DatabaseExplorer()
                logger.info("✅ DatabaseExplorer cargado")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando DatabaseExplorer: {e}")

        # Estadísticas de sesión
        self.session_stats = {
            'sql_queries_generated': 0,
            'select_queries': 0,
            'insert_queries': 0,
            'update_queries': 0,
            'delete_queries': 0,
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
            logger.info(f"✅ Índice SQL disponible: {doc_count} documentos")

        except Exception as e:
            logger.error(f"❌ Error verificando índice: {e}")
            logger.error("💡 Ejecuta: python src/indexer.py")
            raise

    def _check_ollama_availability(self):
        """Verificar disponibilidad de Ollama."""
        if not HAS_REQUESTS:
            logger.warning("⚠️ Sin requests - modo solo consulta directa")
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

    def _detect_sql_operation(self, query: str) -> str:
        """Detectar tipo de operación SQL solicitada."""
        query_lower = query.lower()

        # Patrones para detectar operaciones
        if any(word in query_lower for word in ['select', 'consultar', 'obtener', 'buscar', 'mostrar', 'listar']):
            return 'SELECT'
        elif any(word in query_lower for word in ['insert', 'insertar', 'agregar', 'añadir', 'crear registro']):
            return 'INSERT'
        elif any(word in query_lower for word in ['update', 'actualizar', 'modificar', 'cambiar', 'editar']):
            return 'UPDATE'
        elif any(word in query_lower for word in ['delete', 'eliminar', 'borrar', 'quitar']):
            return 'DELETE'
        else:
            # Por defecto, asumir SELECT
            return 'SELECT'

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extraer nombre de tabla de la consulta."""
        query_lower = query.lower()

        # Patrones comunes para extraer tabla
        table_patterns = [
            r'tabla\s+(\w+)',
            r'table\s+(\w+)',
            r'de\s+(\w+)',
            r'from\s+(\w+)',
            r'into\s+(\w+)',
            r'en\s+(\w+)',
            r'(\w*abonado\w*)',
            r'(\w*client\w*)',
            r'(\w*customer\w*)',
            r'(\w*usuario\w*)',
            r'(\w*cuenta\w*)',
            r'(\w*servicio\w*)'
        ]

        for pattern in table_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(1)

        return None

    def _retrieve_sql_context(self, query: str) -> List[Dict[str, Any]]:
        """Recuperar contexto específico para SQL."""
        try:
            # Inicializar ChromaDB si es necesario
            initialize_chroma_client()

            # Búsqueda específica para estructuras de tablas
            search_terms = []

            # Extraer tabla mencionada
            table_name = self._extract_table_name(query)
            if table_name:
                search_terms.append(f"tabla {table_name}")
                search_terms.append(f"structure {table_name}")
                search_terms.append(f"campos {table_name}")

            # Búsqueda por tipo de operación
            operation = self._detect_sql_operation(query)
            search_terms.append(f"SQL {operation}")
            search_terms.append(f"query {operation}")

            # Buscar documentos relevantes
            all_results = []
            for term in search_terms:
                try:
                    # Intentar primero con filtros de metadatos
                    results = search_index(
                        query=term,
                        top_k=TOP_K_RESULTS,
                        filter_metadata=None  # Temporalmente sin filtros para evitar errores
                    )
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"⚠️ Error buscando '{term}': {e}")
                    # Continuar con el siguiente término

            # Si no hay resultados específicos de tablas, buscar en general
            if not all_results:
                try:
                    results = search_index(query=query, top_k=TOP_K_RESULTS)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"❌ Error en búsqueda general: {e}")

            # Filtrar manualmente por tipo de fuente SQL si es necesario
            if all_results:
                sql_results = []
                for result in all_results:
                    metadata = result.get('metadata', {})
                    source_type = metadata.get('source_type', '')

                    # Filtrar para incluir solo documentos SQL
                    if source_type in ['database_table', 'database_schema', 'database']:
                        sql_results.append(result)

                # Si hay resultados SQL específicos, usarlos; sino usar todos
                all_results = sql_results if sql_results else all_results

            # Filtrar y deduplicar
            unique_results = []
            seen_ids = set()
            for result in all_results:
                if result.get('id') not in seen_ids and result.get('similarity', 0) >= MIN_SIMILARITY:
                    seen_ids.add(result.get('id'))
                    unique_results.append(result)

            # Ordenar por similitud
            unique_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)

            logger.info(f"📋 Recuperados {len(unique_results)} documentos SQL relevantes")
            return unique_results[:TOP_K_RESULTS]

        except Exception as e:
            logger.error(f"❌ Error en recuperación SQL: {e}")
            return []

    def _get_table_structure_from_explorer(self, table_name: str) -> Optional[Dict]:
        """Obtener estructura de tabla usando DatabaseExplorer."""
        if not self.explorer:
            return None

        try:
            # Buscar tabla por nombre
            search_results = self.explorer.search_tables(table_name, limit=5)

            if not search_results:
                return None

            # Tomar la más relevante
            best_match = search_results[0]

            # Obtener estructura completa
            structure = self.explorer.get_table_structure(
                best_match['table_name'],
                best_match['schema_name']
            )

            return structure

        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo estructura de {table_name}: {e}")
            return None

    def _build_sql_context(self, documents: List[Dict[str, Any]], query: str, operation: str) -> str:
        """Construir contexto especializado para generación SQL."""
        if not documents:
            return "No se encontraron estructuras de tablas relevantes."

        context_parts = [
            f"=== CONTEXTO PARA GENERACIÓN DE {operation} ===\n"
        ]

        # Extraer tabla objetivo
        target_table = self._extract_table_name(query)

        if target_table and self.explorer:
            # Intentar obtener estructura exacta
            structure = self._get_table_structure_from_explorer(target_table)
            if structure:
                context_parts.append(f"ESTRUCTURA EXACTA DE TABLA {structure['full_name']}:")
                context_parts.append(f"Total campos: {structure['column_count']}")

                # Campos con detalles
                context_parts.append("\nCAMPOS DISPONIBLES:")
                for col in structure['columns']:
                    key_info = " [PK]" if col['is_primary_key'] == 'YES' else ""
                    nullable = " NULL" if col['is_nullable'] == 'YES' else " NOT NULL"
                    context_parts.append(f"- {col['name']}: {col['full_type']}{nullable}{key_info}")

                # Claves primarias
                if structure['primary_keys']:
                    context_parts.append(f"\nCLAVES PRIMARIAS: {', '.join(structure['primary_keys'])}")

                # Claves foráneas
                foreign_keys = structure.get('foreign_keys', [])
                if foreign_keys:
                    context_parts.append("\nCLAVES FORÁNEAS:")
                    for fk in foreign_keys:
                        context_parts.append(f"- {fk['column_name']} → {fk['referenced_schema']}.{fk['referenced_table']}.{fk['referenced_column']}")

                context_parts.append("\n" + "=" * 50 + "\n")

        # Agregar documentos recuperados como contexto adicional
        for i, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Fuente desconocida')
            similarity = doc.get('similarity', 0)

            doc_info = f"\n--- DOCUMENTO ADICIONAL {i} ---"
            doc_info += f"\nFuente: {Path(source).name if 'file' in str(source) else source}"
            doc_info += f"\nRelevancia: {similarity:.3f}"
            doc_info += f"\nContenido:\n{doc.get('text', '')[:600]}..."

            context_parts.append(doc_info)

        return "".join(context_parts)

    def _generate_sql_prompt(self, query: str, context: str, operation: str) -> str:
        """Generar prompt especializado para SQL."""

        base_prompt = f"""Eres un experto en SQL Server especializado en sistemas bancarios como Bantotal.

Tu tarea es generar consultas {operation} precisas y optimizadas basándote únicamente en la información de estructuras de tablas proporcionada.

REGLAS ESTRICTAS:
1. SOLO generar SQL válido para SQL Server
2. Usar únicamente tablas y campos que aparezcan en el contexto
3. Incluir comentarios explicativos en español
4. Optimizar para rendimiento (usar índices cuando sea posible)
5. Validar tipos de datos y restricciones
6. Para campos de fecha, usar formato 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS'
7. Usar nombres de tabla completos (esquema.tabla) cuando sea posible

FORMATO DE RESPUESTA:
- Comenzar con comentarios explicando la consulta
- Mostrar el SQL optimizado
- Agregar ejemplos de uso si es relevante
- Incluir consideraciones de rendimiento

CONTEXTO DE TABLAS DISPONIBLES:
{context}

CONSULTA DEL USUARIO: {query}

GENERAR CONSULTA {operation}:"""

        return base_prompt

    def generate_sql_query(self, user_query: str) -> Dict[str, Any]:
        """Generar consulta SQL basada en la solicitud del usuario."""
        start_time = time.time()
        self.session_stats['sql_queries_generated'] += 1

        logger.info(f"🔍 Generando SQL para: '{user_query}'")

        # Detectar tipo de operación
        operation = self._detect_sql_operation(user_query)
        logger.info(f"🎯 Operación detectada: {operation}")

        # Actualizar estadísticas por operación
        stat_key = f"{operation.lower()}_queries"
        if stat_key in self.session_stats:
            self.session_stats[stat_key] += 1

        # Recuperar contexto de estructuras de tablas
        documents = self._retrieve_sql_context(user_query)

        if not documents:
            return {
                'query': user_query,
                'sql_generated': None,
                'operation': operation,
                'error': "No se encontraron estructuras de tablas relevantes",
                'suggestions': [
                    "Especifica el nombre de la tabla (ej: 'SELECT de tabla abonados')",
                    "Verifica que la tabla esté indexada en el sistema",
                    "Usa términos más específicos (ej: 'consultar clientes activos')"
                ],
                'metadata': {
                    'success': False,
                    'total_time': time.time() - start_time
                }
            }

        # Construir contexto especializado
        context = self._build_sql_context(documents, user_query, operation)

        # Generar SQL
        if self.has_ollama:
            sql_result = self._generate_sql_with_ai(user_query, context, operation)
        else:
            sql_result = self._generate_sql_fallback(user_query, context, operation)

        # Resultado final
        total_time = time.time() - start_time

        result = {
            'query': user_query,
            'sql_generated': sql_result['sql'],
            'operation': operation,
            'explanation': sql_result.get('explanation', ''),
            'warnings': sql_result.get('warnings', []),
            'examples': sql_result.get('examples', []),
            'sources': [
                {
                    'source': doc['metadata'].get('source', ''),
                    'type': doc['metadata'].get('source_type', ''),
                    'similarity': doc.get('similarity', 0)
                }
                for doc in documents
            ],
            'metadata': {
                'operation_type': operation,
                'documents_used': len(documents),
                'total_time': total_time,
                'has_ai': self.has_ollama,
                'timestamp': datetime.now().isoformat(),
                'success': sql_result['sql'] is not None
            }
        }

        if result['metadata']['success']:
            self.session_stats['successful_responses'] += 1
        else:
            self.session_stats['failed_responses'] += 1

        logger.info(f"✅ SQL {operation} generado ({total_time:.2f}s)")
        return result

    def _generate_sql_with_ai(self, query: str, context: str, operation: str) -> Dict[str, Any]:
        """Generar SQL usando IA (Ollama)."""
        try:
            prompt = self._generate_sql_prompt(query, context, operation)

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Muy bajo para SQL preciso
                        "top_p": 0.9,
                        "max_tokens": 1500
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                sql_text = result.get('response', '').strip()

                # Extraer SQL del texto generado
                sql_code = self._extract_sql_from_response(sql_text)
                explanation = self._extract_explanation_from_response(sql_text)

                return {
                    'sql': sql_code,
                    'explanation': explanation,
                    'warnings': self._validate_sql(sql_code) if sql_code else [],
                    'examples': []
                }
            else:
                logger.error(f"❌ Error Ollama: {response.status_code}")
                return self._generate_sql_fallback(query, context, operation)

        except Exception as e:
            logger.error(f"❌ Error generando SQL con IA: {e}")
            return self._generate_sql_fallback(query, context, operation)

    def _generate_sql_fallback(self, query: str, context: str, operation: str) -> Dict[str, Any]:
        """Generar SQL sin IA usando templates."""

        # Extraer tabla objetivo
        table_name = self._extract_table_name(query)

        if not table_name:
            return {
                'sql': None,
                'explanation': 'No se pudo identificar la tabla objetivo',
                'warnings': ['Especifica el nombre de la tabla en tu consulta'],
                'examples': []
            }

        # Obtener estructura de tabla si está disponible
        structure = None
        if self.explorer:
            structure = self._get_table_structure_from_explorer(table_name)

        if not structure:
            # Template básico sin estructura
            if operation == 'SELECT':
                sql = f"""-- Consulta SELECT básica para tabla {table_name}
-- NOTA: Ajustar campos según estructura real de la tabla
SELECT TOP 100 *
FROM dbo.{table_name}
ORDER BY 1;

-- Ejemplo con filtros comunes:
-- WHERE campo_estado = 'ACTIVO'
-- WHERE fecha_creacion >= '2024-01-01'"""

            elif operation == 'INSERT':
                sql = f"""-- Plantilla INSERT para tabla {table_name}
-- NOTA: Ajustar campos y valores según estructura real
INSERT INTO dbo.{table_name} (
    campo1,
    campo2,
    campo3
) VALUES (
    'valor1',
    'valor2',
    'valor3'
);"""

            elif operation == 'UPDATE':
                sql = f"""-- Plantilla UPDATE para tabla {table_name}
-- NOTA: Ajustar campos y condiciones según estructura real
UPDATE dbo.{table_name}
SET campo1 = 'nuevo_valor',
    campo2 = 'otro_valor',
    fecha_modificacion = GETDATE()
WHERE id = 123;  -- Ajustar condición WHERE"""

            else:  # DELETE
                sql = f"""-- Plantilla DELETE para tabla {table_name}
-- CUIDADO: Siempre usar WHERE para evitar borrar todos los registros
DELETE FROM dbo.{table_name}
WHERE id = 123;  -- Ajustar condición WHERE

-- Para borrado lógico (recomendado):
-- UPDATE dbo.{table_name} SET estado = 'INACTIVO' WHERE id = 123;"""

            return {
                'sql': sql,
                'explanation': f'Plantilla {operation} básica para {table_name}. Requiere ajustes según estructura real.',
                'warnings': ['No se encontró estructura de tabla', 'Revisar campos y tipos antes de ejecutar'],
                'examples': []
            }

        else:
            # Generar SQL con estructura conocida
            return self._generate_sql_with_structure(query, structure, operation)

    def _generate_sql_with_structure(self, query: str, structure: Dict, operation: str) -> Dict[str, Any]:
        """Generar SQL conociendo la estructura exacta de la tabla."""

        full_table_name = structure['full_name']
        columns = structure['columns']
        primary_keys = structure.get('primary_keys', [])

        if operation == 'SELECT':
            # Determinar si incluir JOINs
            query_lower = query.lower()
            include_joins = any(word in query_lower for word in ['join', 'relacion', 'relacionar', 'con', 'detalle'])
            join_type = 'INNER' if 'inner' in query_lower else 'LEFT'
            
            # Usar el generador mejorado del DatabaseExplorer
            if hasattr(self, 'db_explorer') and self.db_explorer:
                table_name = structure['table_name']
                schema = structure.get('schema', 'dbo')
                
                # Generar query con JOINs automáticos
                sql = self.db_explorer.generate_select_query(
                    table_name=table_name,
                    schema=schema,
                    limit=100,
                    include_joins=include_joins,
                    join_type=join_type
                )
            else:
                # Fallback al método anterior si no hay DatabaseExplorer
                if 'todos los campos' in query_lower or 'all fields' in query_lower or '*' in query_lower:
                    # Mostrar todos los campos
                    field_list = [f"    {col['name']}" for col in columns]
                    fields_joined = ',\n'.join(field_list)
                    sql = f"""-- Consulta SELECT completa para {full_table_name}
-- Total de campos: {len(columns)}
-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SELECT TOP 100
{fields_joined}
FROM {full_table_name}"""
                else:
                    # Mostrar campos principales (primeros 10)
                    main_fields = [f"    {col['name']}" for col in columns[:10]]
                    if len(columns) > 10:
                        main_fields.append(f"    -- ... y {len(columns) - 10} campos más")

                    fields_to_join = main_fields[:-1] if len(columns) > 10 else main_fields
                    main_fields_joined = ',\n'.join(fields_to_join)

                    sql = f"""-- Consulta SELECT principal para {full_table_name}
-- Mostrando primeros 10 campos de {len(columns)} totales

SELECT TOP 100
{main_fields_joined}
FROM {full_table_name}"""

                # Agregar ORDER BY usando clave primaria si existe
                if primary_keys:
                    sql += f"\nORDER BY {', '.join(primary_keys)};"
                else:
                    sql += f"\nORDER BY {columns[0]['name']};"

                # Agregar ejemplos de filtros
                sql += "\n\n-- Ejemplos de filtros comunes:"

                # Buscar campos típicos para filtros
                for col in columns[:5]:
                    col_name = col['name']
                    data_type = col['data_type'].lower()

                    if 'estado' in col_name.lower():
                        sql += f"\n-- WHERE {col_name} = 'ACTIVO'"
                    elif 'fecha' in col_name.lower() or 'date' in data_type:
                        sql += f"\n-- WHERE {col_name} >= '2024-01-01'"
                    elif any(word in col_name.lower() for word in ['nombre', 'descripcion', 'name']):
                        sql += f"\n-- WHERE {col_name} LIKE '%texto%'"
                    elif any(word in data_type for word in ['int', 'numeric', 'decimal']):
                        sql += f"\n-- WHERE {col_name} = 123"

        elif operation == 'INSERT':
            # Campos no nulos y sin default
            required_fields = [col for col in columns if
                               col['is_nullable'] == 'NO' and not col.get('default_value') and col['is_primary_key'] != 'YES']
            optional_fields = [col for col in columns if col['is_nullable'] == 'YES' or col.get('default_value')]

            field_names = [col['name'] for col in required_fields]
            field_values = []

            for col in required_fields:
                data_type = col['data_type'].lower()
                if any(dt in data_type for dt in ['varchar', 'char', 'text', 'nvarchar']):
                    field_values.append("'valor_texto'")
                elif any(dt in data_type for dt in ['int', 'bigint']):
                    field_values.append("123")
                elif any(dt in data_type for dt in ['decimal', 'numeric', 'money']):
                    field_values.append("100.00")
                elif any(dt in data_type for dt in ['date', 'datetime']):
                    field_values.append("'2024-01-01'")
                else:
                    field_values.append("'valor'")

            field_names_joined = ',\n    '.join(field_names)
            field_values_joined = ',\n    '.join(field_values)

            sql = f"""-- INSERT para {full_table_name}
-- Campos obligatorios: {len(required_fields)}
-- Campos opcionales disponibles: {len(optional_fields)}

INSERT INTO {full_table_name} (
    {field_names_joined}
) VALUES (
    {field_values_joined}
);"""

            if optional_fields:
                sql += f"\n\n-- Campos opcionales disponibles:"
                for col in optional_fields[:5]:
                    sql += f"\n-- {col['name']}: {col['full_type']}"

        elif operation == 'UPDATE':
            # Usar campos editables (no claves primarias)
            editable_fields = [col for col in columns if col['is_primary_key'] != 'YES'][:5]

            set_clauses = []
            for col in editable_fields:
                data_type = col['data_type'].lower()
                if any(dt in data_type for dt in ['varchar', 'char', 'text']):
                    set_clauses.append(f"    {col['name']} = 'nuevo_valor'")
                elif any(dt in data_type for dt in ['date', 'datetime']):
                    set_clauses.append(f"    {col['name']} = GETDATE()")
                else:
                    set_clauses.append(f"    {col['name']} = 'nuevo_valor'")

            where_clause = primary_keys[0] if primary_keys else columns[0]['name']
            set_clauses_joined = ',\n'.join(set_clauses)

            sql = f"""-- UPDATE para {full_table_name}
-- Actualizar registros específicos

UPDATE {full_table_name}
SET
{set_clauses_joined},
    fecha_modificacion = GETDATE()  -- Si existe este campo
WHERE {where_clause} = 123;  -- Ajustar valor según necesidad

-- IMPORTANTE: Siempre usar WHERE para evitar actualizar todos los registros"""

        else:  # DELETE
            where_clause = primary_keys[0] if primary_keys else columns[0]['name']

            sql = f"""-- DELETE para {full_table_name}
-- CUIDADO: Operación irreversible

-- Borrado específico:
DELETE FROM {full_table_name}
WHERE {where_clause} = 123;  -- Ajustar valor

-- Alternativa recomendada - Borrado lógico (si existe campo estado):
-- UPDATE {full_table_name} 
-- SET estado = 'INACTIVO', fecha_baja = GETDATE()
-- WHERE {where_clause} = 123;

-- NUNCA ejecutar sin WHERE:
-- DELETE FROM {full_table_name};  -- ¡ESTO BORRA TODO!"""

        return {
            'sql': sql,
            'explanation': f'Consulta {operation} generada para {full_table_name} con {len(columns)} campos disponibles.',
            'warnings': self._validate_sql(sql),
            'examples': []
        }

    def _extract_sql_from_response(self, response_text: str) -> Optional[str]:
        """Extraer código SQL del texto de respuesta."""
        # Buscar bloques de código SQL
        sql_patterns = [
            r'```sql\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'SELECT.*?;',
            r'INSERT.*?;',
            r'UPDATE.*?;',
            r'DELETE.*?;'
        ]

        for pattern in sql_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Si no encuentra patrones, buscar líneas que parezcan SQL
        lines = response_text.split('\n')
        sql_lines = []
        in_sql = False

        for line in lines:
            line_clean = line.strip()
            if any(word in line_clean.upper() for word in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE']):
                in_sql = True

            if in_sql:
                sql_lines.append(line)
                if line_clean.endswith(';'):
                    break

        return '\n'.join(sql_lines) if sql_lines else None

    def _extract_explanation_from_response(self, response_text: str) -> str:
        """Extraer explicación del texto de respuesta."""
        # Buscar texto antes del SQL
        lines = response_text.split('\n')
        explanation_lines = []

        for line in lines:
            if any(word in line.upper() for word in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                break
            if line.strip() and not line.startswith('```'):
                explanation_lines.append(line.strip())

        return ' '.join(explanation_lines) if explanation_lines else 'Consulta SQL generada.'

    def _validate_sql(self, sql: str) -> List[str]:
        """Validar SQL y retornar advertencias."""
        warnings = []

        if not sql:
            return ['No se generó código SQL']

        sql_upper = sql.upper()

        # Validaciones básicas
        if 'DELETE' in sql_upper and 'WHERE' not in sql_upper:
            warnings.append('⚠️ DELETE sin WHERE puede borrar todos los registros')

        if 'UPDATE' in sql_upper and 'WHERE' not in sql_upper:
            warnings.append('⚠️ UPDATE sin WHERE puede modificar todos los registros')

        if 'SELECT *' in sql_upper and 'TOP' not in sql_upper and 'LIMIT' not in sql_upper:
            warnings.append('💡 Considera usar TOP N para limitar resultados')

        if 'DROP' in sql_upper or 'TRUNCATE' in sql_upper:
            warnings.append('🚨 Operación destructiva detectada')

        return warnings

    def get_session_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la sesión SQL."""
        total_queries = self.session_stats['sql_queries_generated']

        return {
            **self.session_stats,
            'success_rate': (
                    self.session_stats['successful_responses'] / max(1, total_queries)
            ),
            'most_used_operation': max(
                ['select', 'insert', 'update', 'delete'],
                key=lambda op: self.session_stats.get(f'{op}_queries', 0)
            )
        }


def main():
    """Función principal para pruebas desde línea de comandos."""
    import sys

    if len(sys.argv) < 2:
        print("""
🗄️ Agente SQL Especializado - Consultas Bancarias

Uso:
  python src/sql_agent.py "tu consulta SQL aquí"

Ejemplos para SELECT:
  python src/sql_agent.py "SELECT de tabla abonados con todos los campos"
  python src/sql_agent.py "consultar clientes activos"
  python src/sql_agent.py "mostrar servicios de un cliente"

Ejemplos para INSERT:
  python src/sql_agent.py "INSERT nuevo abonado"
  python src/sql_agent.py "agregar cliente con datos"

Ejemplos para UPDATE:
  python src/sql_agent.py "UPDATE datos del abonado"
  python src/sql_agent.py "actualizar estado del cliente"

Ejemplos para DELETE:
  python src/sql_agent.py "DELETE abonado inactivo"
  python src/sql_agent.py "eliminar servicio cancelado"

Capacidades:
  ✅ Genera SQL optimizado para SQL Server
  ✅ Usa estructura real de las tablas
  ✅ Incluye validaciones y advertencias
  ✅ Ejemplos específicos para bancarios
  ✅ Comentarios explicativos en español
""")
        return

    query = ' '.join(sys.argv[1:])

    try:
        # Crear agente SQL
        agent = SQLAgent()

        # Procesar consulta
        result = agent.generate_sql_query(query)

        # Mostrar resultado
        print(f"\n🔍 CONSULTA: {result['query']}")
        print(f"🎯 OPERACIÓN: {result['operation']}")

        if result['sql_generated']:
            print(f"\n🗄️ SQL GENERADO:")
            print("=" * 80)
            print(result['sql_generated'])
            print("=" * 80)

            if result.get('explanation'):
                print(f"\n💡 EXPLICACIÓN:")
                print(result['explanation'])

            if result.get('warnings'):
                print(f"\n⚠️ ADVERTENCIAS:")
                for warning in result['warnings']:
                    print(f"   • {warning}")
        else:
            print(f"\n❌ ERROR: {result.get('error', 'No se pudo generar SQL')}")

            if result.get('suggestions'):
                print(f"\n💡 SUGERENCIAS:")
                for suggestion in result['suggestions']:
                    print(f"   • {suggestion}")

        if result.get('sources'):
            print(f"\n📚 FUENTES CONSULTADAS:")
            for i, source in enumerate(result['sources'], 1):
                source_name = Path(source['source']).name if source.get('source') else 'N/A'
                print(f"   {i}. {source_name} (similitud: {source.get('similarity', 0):.3f})")

        # Estadísticas
        metadata = result['metadata']
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Tiempo: {metadata['total_time']:.2f}s")
        print(f"   Documentos usados: {metadata['documents_used']}")
        print(f"   IA disponible: {'Sí' if metadata['has_ai'] else 'No'}")

        # Estadísticas de sesión
        stats = agent.get_session_stats()
        print(f"   Consultas en sesión: {stats['sql_queries_generated']}")
        print(f"   Operación más usada: {stats['most_used_operation'].upper()}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"\n❌ Error procesando consulta: {e}")


if __name__ == '__main__':
    main()
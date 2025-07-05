# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Arquitectura del Sistema

Este es un **RAG SQL Agent** especializado en consultas bancarias (Bantotal/GeneXus) que utiliza una arquitectura de **agentes especializados** con un **director orquestador**.

### Componentes Principales:

1. **Agent Director** (`src/agent_director.py`) - Orquestador que decide qué agente usar según la intención de la consulta
2. **SQL Agent** (`src/sql_agent.py`) - Genera consultas SQL con JOINs inteligentes para Bantotal
3. **Docs Agent** (`src/docs_agent.py`) - Consultas sobre documentación técnica GeneXus/Bantotal
4. **Database Explorer** (`src/database_explorer.py`) - Explorador SQL Server optimizado para Bantotal
5. **Indexer & ChromaDB** (`src/indexer.py`) - Sistema de vectores para búsqueda semántica
6. **Ingestion System** (`src/ingestion.py`) - Procesa documentos PDF/DOCX y metadatos SQL

### Interfaces:
- **CLI Principal:** `python rag.py "tu consulta"`
- **Web Interface:** `streamlit run src/app.py`

## 🔧 Comandos de Desarrollo

### Instalación y Setup:
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar sistema para Bantotal
python bantotal_config.py

# Crear índice vectorial
python src/indexer.py --force

# Probar conexión SQL Server
python test_connection.py
```

### Comandos Principales:
```bash
# Consultas CLI
python rag.py "SELECT tabla abonados"
python rag.py "cómo usar FOR EACH en GeneXus"

# Estado del sistema
python rag.py --status
python rag.py --stats
python rag.py --setup

# Interfaz web
streamlit run src/app.py

# Diagnóstico
python diagnose.py
python test_joins.py
python test_enhanced_metadata.py
```

## 🏦 Especialización Bancaria Bantotal

### Nomenclatura de Tablas:
- **FST:** Tablas Básicas (clientes, sucursales)
- **FSD:** Datos (operaciones, servicios)  
- **FSR:** Relaciones entre entidades
- **FSE:** Extensiones y configuraciones
- **FSH:** Históricos y auditoría
- **FSX:** Textos y descripciones
- **FSA:** Auxiliares y catálogos

### JOINs Inteligentes:
- Detección automática de Foreign Keys por posición de campos
- Patrones Bantotal: Pgcod (Empresa) + módulo + sucursal + moneda
- Máximo 3 JOINs por consulta para legibilidad

## ⚙️ Configuración Importante

### Variables de Entorno (.env):
```bash
# SQL Server
SQL_SERVER_HOST=localhost
SQL_SERVER_DATABASE=Bantotal
SQL_SERVER_USERNAME=user
SQL_SERVER_PASSWORD=password

# Ollama LLM  
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2:latest

# ChromaDB
CHROMA_DB_DIR=chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Archivos de Configuración:
- `bantotal_extraction_strategy.json` - Estrategia de extracción por fases
- `enhanced_sql_metadata.json` - Metadatos enriquecidos de tablas
- `estructura_tablas_kb_nativa_micro.json` - Mapeo de estructuras

## 🚀 Optimizaciones de Performance

### Problemas Identificados:
- Tiempo de respuesta: 60-76 segundos promedio
- Búsquedas excesivas: 23 términos por consulta
- Falta de caché para consultas repetidas

### Mejoras Implementadas:
- Reducción de términos: 23 → 10 búsquedas
- Cache en memoria para consultas recientes
- Búsqueda priorizada por relevancia
- Metadatos estáticos precargados

## ✅ Instrucciones generales de trabajo

1. Primero, analiza el problema, revisa la base de código para identificar los archivos relevantes y escribe un plan usando TodoWrite.
2. El plan debe contener una lista de tareas que puedas marcar como completadas conforme avances.
3. Antes de comenzar a trabajar, consulta conmigo para que pueda verificar y aprobar el plan.
4. Luego, comienza a ejecutar las tareas del plan, marcándolas como completadas a medida que las termines.
5. En cada paso, proporciona una explicación general y clara de los cambios que realizaste.
6. Haz cada tarea y cambio de código lo más simple posible. Evita cambios masivos. Cada cambio debe afectar la menor cantidad de código posible.
7. Finalmente, añade una sección de revisión al final del archivo con un resumen de los cambios que realizaste y cualquier información relevante adicional.
8. Realiza commit y push de los cambios después de cada tarea completada, siguiendo buenas prácticas en los mensajes de commit.

---

## 🔐 Revisión de seguridad

Antes de confirmar cada cambio:
- [ ] Asegurarse de que no haya datos sensibles expuestos en frontend o backend.
- [ ] Verificar que las API estén protegidas contra accesos indebidos.
- [ ] Revisar que los formularios tengan validación contra entradas maliciosas (XSS, SQLi).
- [ ] No dejar claves, tokens ni secretos en el código. Usar variables de entorno.

---

## 📘 Explicación de cambios

Después de cada tarea:
- [ ] Explica en lenguaje claro qué funcionalidad agregaste.
- [ ] Muestra qué archivos cambiaste y por qué.
- [ ] Enseña el flujo de cómo funciona, como si lo explicaras a un desarrollador junior.
- [ ] Usa ejemplos simples o comentarios clave si es útil.

---

## 🧠 Productividad creativa

Mientras se espera respuesta o carga:
- [ ] Usar el tiempo para pensar ideas nuevas (producto, contenido, negocios).
- [ ] Reflexionar sobre lo aprendido o lo que se puede mejorar del sistema.
- [ ] Aprovechar este chat como espacio creativo y estratégico.
- [ ] Puedes pedirme ayuda para lluvia de ideas, validación de conceptos o simplemente organizar tus pensamientos.
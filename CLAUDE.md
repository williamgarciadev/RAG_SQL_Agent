# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is a specialized RAG (Retrieval-Augmented Generation) system designed for banking and financial systems, specifically optimized for Bantotal ERP environments. The system provides intelligent SQL query generation and documentation retrieval through a multi-agent architecture.

## Key Architecture Components

### Agent Architecture
- **AgentDirector** (`src/agent_director.py`): Intelligent orchestrator that routes queries to appropriate specialized agents
- **SQLAgent** (`src/sql_agent.py`): Generates optimized SQL queries (SELECT, INSERT, UPDATE, DELETE) for banking databases
- **DocsAgent** (`src/docs_agent.py`): Handles technical documentation queries for GeneXus and Bantotal manuals
- **DatabaseExplorer** (`src/database_explorer.py`): Explores database structures, optimized for Bantotal table nomenclature

### Core System Components
- **Indexer** (`src/indexer.py`): Manages ChromaDB vector database for document and schema indexing
- **Ingestion** (`src/ingestion.py`): Processes and indexes technical documentation and database schemas
- **Master RAG Script** (`rag.py`): Main entry point - unified interface for all system functionality

## Running the System

### Main Commands

**Primary interface:**
```bash
python rag.py "your query here"
```

**Web interface:**
```bash
streamlit run src/app.py
```

**Force re-indexing:**
```bash
python src/indexer.py --force
```

**Database analysis:**
```bash
python bantotal_config.py
```

### Configuration Scripts

- `bantotal_config.py`: Configure system for Bantotal-specific table structures
- `scale_config.py`: Performance optimization for large databases
- `diagnose.py`: System health check and troubleshooting

## Bantotal-Specific Knowledge

### Table Nomenclature
The system understands Bantotal's table naming conventions:
- **FST**: Tablas Básicas - Generic fundamental tables
- **FSD**: Datos - Main data tables (e.g., FSD601 for services)
- **FSR**: Relaciones - Relationship tables
- **FSE**: Extensiones - Extension tables
- **FSH**: Históricos - Historical data tables
- **FSX**: Textos - Text/description tables
- **FSA**: Auxiliares - Auxiliary tables
- **FSI**: Informaciones - Information tables
- **FSM**: Menús - Menu/interface tables
- **FSN**: Numeradores - Counter/sequence tables

### Query Classification
The AgentDirector automatically classifies queries:
- **SQL queries**: Patterns like "SELECT", "consultar tabla", "generar SQL"
- **Documentation queries**: Patterns like "cómo hacer", "manual de", "procedimiento"
- **Mixed queries**: Require both SQL generation and documentation lookup

## Environment Setup

### Required Dependencies
- `chromadb`: Vector database for document storage
- `streamlit`: Web interface framework
- `pyodbc`: SQL Server connectivity
- `sqlalchemy`: Database ORM
- `requests`: HTTP client for Ollama integration
- `python-dotenv`: Environment variable management

### Environment Variables
Create a `.env` file with:
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2:latest
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=your_database
SQL_SERVER_USERNAME=your_username
SQL_SERVER_PASSWORD=your_password
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
TOP_K_RESULTS=5
MIN_SIMILARITY=0.1
```

## Development Commands

### Testing and Diagnostics
```bash
# System health check
python diagnose.py

# Database connection test
python bantotal_config.py

# Force SQL extraction
python force_sql_extraction.py

# Enable auto-extraction
python enable_auto_sql_extraction.py
```

### Data Management
```bash
# Re-index all documents
python src/indexer.py --force

# Ingest new documents
python src/ingestion.py

# SQL-specific ingestion
python src/ingestion_sql.py
```

## Key Design Patterns

### Agent Routing Logic
The system uses pattern matching and confidence scoring to route queries:
1. Query classification based on keyword patterns
2. Confidence scoring for SQL vs documentation intent
3. Mixed query handling for complex requests requiring both agents

### Database Optimization
- Bantotal-specific table prioritization (FST > FSD > FSR > FSE)
- Batch processing for large table sets
- Intelligent caching for frequently accessed schemas

### Error Handling
- Graceful degradation when agents are unavailable
- Comprehensive logging for debugging
- Automatic fallback to available agents

## File Structure Context

### Root Level
- `rag.py`: Main entry point
- `bantotal_config.py`: Bantotal-specific configuration
- `bantotal_extraction_strategy.json`: Extraction strategy for Bantotal tables
- `docs/`: Technical documentation corpus

### Source Directory (`src/`)
- Agent implementations and core system logic
- ChromaDB management and indexing
- Web interface and utilities

### Data Storage
- `chroma_db/`: Vector database storage
- `docs/`: PDF manuals, Word documents, and technical references

## Common Workflow Patterns

1. **New Feature Development**: Start with `diagnose.py` to understand system state
2. **Database Changes**: Run `bantotal_config.py` to reconfigure for new schemas
3. **Documentation Updates**: Use `src/ingestion.py` to re-index new documents
4. **Performance Issues**: Use `scale_config.py` for optimization

## Integration Points

- **Ollama**: Local LLM for query processing
- **SQL Server**: Primary database backend
- **ChromaDB**: Vector storage for RAG functionality
- **Streamlit**: Web interface framework
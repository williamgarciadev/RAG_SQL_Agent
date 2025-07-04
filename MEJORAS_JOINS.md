# Mejoras en Generación de SQL con JOINs y ORDER BY

## Resumen de Mejoras

Se ha mejorado el sistema RAG para generar consultas SELECT más inteligentes que incluyen:

### ✅ **JOINs Automáticos**
- Detección automática de Foreign Keys
- Generación de LEFT JOIN e INNER JOIN
- Límite de 3 JOINs por consulta para mantener legibilidad
- Alias inteligentes basados en prefijos Bantotal

### ✅ **ORDER BY Inteligente**
- Priorización de columnas como 'fecha', 'id', 'codigo'
- Uso de claves primarias cuando están disponibles
- Múltiples criterios de ordenamiento

### ✅ **Filtros Bantotal**
- Filtros específicos por tipo de tabla (FST, FSD, etc.)
- Ejemplos contextuales de WHERE clauses
- Comentarios con filtros comunes

## Funcionalidades Agregadas

### 1. **Detección de Relaciones**
```python
def _detect_table_relationships(self, table_name: str, schema: str = None) -> List[Dict]:
    """Detectar relaciones FK para generar JOINs automáticos."""
```

### 2. **Alias Inteligentes**
```python
def _get_table_alias(self, table_name: str) -> str:
    """Generar alias inteligente para tabla."""
    # FST -> 'tb' (Tabla Básica)
    # FSD -> 'dt' (Datos)
    # FSR -> 'rl' (Relaciones)
```

### 3. **Columnas Esenciales**
```python
def _get_essential_columns(self, table_name: str) -> List[str]:
    """Obtener columnas esenciales de una tabla relacionada."""
    # Busca: 'nombre', 'descripcion', 'codigo', 'id', 'estado'
```

### 4. **ORDER BY Inteligente**
```python
def _generate_smart_order_by(self, columns: List[Dict], alias: str) -> str:
    """Generar ORDER BY inteligente."""
    # Prioriza: 'fecha', 'id', 'codigo', 'numero', 'secuencia'
```

## Uso del Sistema Mejorado

### **Consultas que Activan JOINs**
```bash
# Estas consultas activan JOINs automáticos:
python rag.py "SELECT de FSD601 con relaciones"
python rag.py "generar consulta con join para tabla servicios"
python rag.py "mostrar FSD601 con inner join"
python rag.py "consulta con left join tabla FSD602"
```

### **Tipos de JOIN Soportados**
- **LEFT JOIN** (por defecto): Incluye todos los registros de la tabla principal
- **INNER JOIN**: Solo registros que tienen coincidencias en ambas tablas

### **Palabras Clave que Detectan JOINs**
- `join`, `relacion`, `relacionar`, `con`, `detalle`
- `inner` (fuerza INNER JOIN)
- Sin palabras clave = LEFT JOIN por defecto

## Ejemplo de SQL Generado

### **Antes (SQL Simple)**
```sql
SELECT TOP 100
    campo1,
    campo2,
    campo3
FROM dbo.FSD601
ORDER BY campo1
```

### **Después (SQL con JOINs)**
```sql
-- Query optimizada para tabla Bantotal: dbo.FSD601
-- Total campos: 15
-- JOINs detectados: 2
-- Generado: 2024-01-15 10:30:00

SELECT TOP 100
    dt.campo1,
    dt.campo2,
    dt.campo3,
    tb.codigo AS tb_codigo,
    tb.nombre AS tb_nombre,
    rl.descripcion AS rl_descripcion
FROM dbo.FSD601 dt
LEFT JOIN dbo.FST001 tb ON dt.tipo_id = tb.id
LEFT JOIN dbo.FSR001 rl ON dt.relacion_id = rl.id
ORDER BY dt.fecha_proceso, dt.id

-- Filtros comunes para tabla Bantotal:
-- WHERE dt.estado = 'ACTIVO'
-- WHERE dt.fecha_vigencia >= GETDATE()
-- WHERE dt.sucursal = 1
```

## Configuración

### **Parámetros Disponibles**
```python
explorer.generate_select_query(
    table_name="FSD601",
    schema="dbo",
    limit=100,
    include_joins=True,      # Activar JOINs automáticos
    join_type='LEFT'         # 'LEFT' o 'INNER'
)
```

### **Variables de Control**
- `include_joins`: Activar/desactivar JOINs automáticos
- `join_type`: Tipo de JOIN ('LEFT' o 'INNER')
- `limit`: Número máximo de registros a retornar

## Pruebas

### **Script de Prueba**
```bash
python test_joins.py
```

### **Pruebas Manuales**
```bash
# Probar con diferentes tipos de consultas
python rag.py "SELECT de FSD601"                    # Sin JOINs
python rag.py "SELECT de FSD601 con relaciones"     # Con JOINs
python rag.py "generar inner join para FSD602"      # INNER JOIN
```

## Beneficios

### **🎯 Para Desarrolladores**
- Consultas más completas y útiles
- Menos tiempo escribiendo JOINs manualmente
- Mejor comprensión de las relaciones entre tablas

### **🏦 Para Analistas Bancarios**
- Consultas que incluyen información relacionada automáticamente
- Filtros específicos para el dominio bancario
- Ordenamiento inteligente por campos relevantes

### **📊 Para el Sistema**
- Mejor utilización de la información de foreign keys
- Consultas más eficientes y legibles
- Mantiene compatibilidad con el sistema anterior

## Archivos Modificados

1. **`src/database_explorer.py`** - Generador principal de SQL
2. **`src/sql_agent.py`** - Integración con el agente SQL
3. **`test_joins.py`** - Script de pruebas
4. **`MEJORAS_JOINS.md`** - Esta documentación
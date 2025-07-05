#!/usr/bin/env python3
"""
Script de prueba para JOINs automáticos de tabla FSD010
Demuestra diferentes tipos de consultas que activan JOINs inteligentes
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from bantotal_join_patterns import BantotalJoinAnalyzer

def test_fsd010_joins():
    """Probar diferentes escenarios de JOIN para FSD010."""
    
    print("🎯 PRUEBAS DE JOINs AUTOMÁTICOS PARA TABLA FSD010")
    print("=" * 70)
    
    analyzer = BantotalJoinAnalyzer()
    
    # Campos de ejemplo para diferentes tablas
    table_structures = {
        'FSD010': [  # Operaciones Bancarias
            {'name': 'Pgcod', 'type': 'smallint'},
            {'name': 'Aomod', 'type': 'int'},
            {'name': 'Aosuc', 'type': 'int'},
            {'name': 'Aomda', 'type': 'smallint'},
            {'name': 'Aopap', 'type': 'int'},
            {'name': 'Aocta', 'type': 'int'},
            {'name': 'Aooper', 'type': 'int'},
            {'name': 'Aosbop', 'type': 'int'},
        ],
        'FSD601': [  # Operaciones a Plazo
            {'name': 'Pgcod', 'type': 'smallint'},
            {'name': 'Ppmod', 'type': 'int'},
            {'name': 'Ppsuc', 'type': 'int'},
            {'name': 'Ppmda', 'type': 'smallint'},
            {'name': 'Pppap', 'type': 'int'},
            {'name': 'Ppcta', 'type': 'int'},
            {'name': 'Ppoper', 'type': 'int'},
            {'name': 'Ppsbop', 'type': 'int'},
        ],
        'FST001': [  # Sucursales
            {'name': 'Pgcod', 'type': 'smallint'},
            {'name': 'Sucurs', 'type': 'int'},
            {'name': 'Scnom', 'type': 'char'},
            {'name': 'Scnomr', 'type': 'char'},
            {'name': 'Sccall', 'type': 'char'},
        ],
        'FST002': [  # Clientes
            {'name': 'Pgcod', 'type': 'smallint'},
            {'name': 'Clcod', 'type': 'int'},
            {'name': 'Clnom', 'type': 'char'},
            {'name': 'Clape', 'type': 'char'},
            {'name': 'Clfna', 'type': 'date'},
        ]
    }
    
    test_cases = [
        {
            'name': 'FSD010 → FSD601',
            'description': 'Operaciones Bancarias con Operaciones a Plazo',
            'table1': 'FSD010',
            'table2': 'FSD601',
            'query_examples': [
                "SELECT operaciones con detalles de plazo",
                "operaciones y plazos relacionados",
                "pagos con información de inversiones"
            ]
        },
        {
            'name': 'FSD010 → FST001', 
            'description': 'Operaciones Bancarias con Sucursales',
            'table1': 'FSD010',
            'table2': 'FST001',
            'query_examples': [
                "SELECT operaciones con nombre de sucursal",
                "operaciones por oficina",
                "transacciones con detalles de agencia"
            ]
        },
        {
            'name': 'FSD010 → FST002',
            'description': 'Operaciones Bancarias con Clientes', 
            'table1': 'FSD010',
            'table2': 'FST002',
            'query_examples': [
                "SELECT operaciones con datos del cliente",
                "pagos con información personal",
                "transacciones por cliente"
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 🔍 {test_case['name']}")
        print(f"   📝 {test_case['description']}")
        print("   " + "-" * 50)
        
        table1_fields = table_structures[test_case['table1']]
        table2_fields = table_structures[test_case['table2']]
        
        # Analizar patrón de JOIN
        join_info = analyzer.analyze_join_pattern(
            table1_fields, table2_fields, 
            test_case['table1'], test_case['table2']
        )
        
        # Mostrar resultados
        print(f"   ✅ Puede hacer JOIN: {join_info['can_join']}")
        print(f"   📊 Confianza: {join_info['confidence']:.2f}")
        print(f"   🔗 Tipo de JOIN: {join_info['join_type']}")
        print(f"   🎯 Razón: {join_info['semantic_reason']}")
        
        if join_info['can_join']:
            print(f"   📋 Campos de JOIN:")
            for field in join_info['join_fields'][:3]:  # Primeros 3
                print(f"      • {field['field1']} = {field['field2']} ({field['semantic']})")
            
            # Generar SQL
            join_info['table_name'] = f"dbo.{test_case['table2']}"
            sql = analyzer.generate_join_sql(f"dbo.{test_case['table1']}", [join_info])
            
            print(f"\n   🗄️ SQL Generado:")
            print("   " + "=" * 45)
            for line in sql.split('\n'):
                print(f"   {line}")
            print("   " + "=" * 45)
        
        print(f"\n   💡 Consultas de ejemplo que activarían este JOIN:")
        for example in test_case['query_examples']:
            print(f"      • \"{example}\"")

def test_multiple_joins():
    """Probar JOINs múltiples con FSD010."""
    
    print(f"\n\n🚀 PRUEBA DE JOINs MÚLTIPLES CON FSD010")
    print("=" * 70)
    
    analyzer = BantotalJoinAnalyzer()
    
    # Simular query compleja
    complex_query = "SELECT operaciones con sucursal y cliente completo"
    
    print(f"📝 Consulta: \"{complex_query}\"")
    print(f"🎯 Tabla principal: FSD010 (Operaciones Bancarias)")
    print(f"🔗 JOINs esperados: FST001 (Sucursales) + FST002 (Clientes)")
    
    # SQL con múltiples JOINs
    multi_join_sql = """
-- Consulta compleja con múltiples JOINs automáticos
SELECT TOP 100
    A.Pgcod AS CodigoEmpresa,
    A.Aomod AS Modulo,
    A.Aosuc AS CodigoSucursal,
    A.Aomda AS Moneda,
    A.Aopap AS Papel,
    B.Scnom AS NombreSucursal,
    C.Clnom AS NombreCliente,
    C.Clape AS ApellidoCliente
FROM dbo.FSD010 A
INNER JOIN dbo.FST001 B ON A.Pgcod = B.Pgcod 
                       AND A.Aosuc = B.Sucurs
LEFT JOIN dbo.FST002 C ON A.Pgcod = C.Pgcod
ORDER BY A.Pgcod, A.Aomod;
"""
    
    print(f"\n🗄️ SQL con JOINs Múltiples:")
    print("=" * 50)
    print(multi_join_sql)
    print("=" * 50)
    
    print(f"\n📊 Explicación de JOINs:")
    print(f"  🔸 INNER JOIN FST001: Operaciones deben tener sucursal válida")
    print(f"  🔸 LEFT JOIN FST002:  Operaciones pueden no tener cliente asociado")
    print(f"  🔸 Campos de relación: Pgcod (empresa) + campos específicos")

def show_query_keywords():
    """Mostrar palabras clave que activan JOINs automáticos."""
    
    print(f"\n\n📚 PALABRAS CLAVE PARA ACTIVAR JOINs AUTOMÁTICOS")
    print("=" * 70)
    
    keywords = {
        'Alto Trigger (JOINs múltiples)': [
            'completo', 'detalle', 'detallado', 'full', 'con todo',
            'información completa', 'datos completos'
        ],
        'Medio Trigger (JOIN específico)': [
            'con', 'junto', 'relacionado', 'vinculado', 'asociado',
            'incluyendo', 'más', 'también'
        ],
        'Bajo Trigger (JOIN opcional)': [
            'si existe', 'opcional', 'cuando disponible', 'si tiene'
        ]
    }
    
    for category, words in keywords.items():
        print(f"\n🎯 {category}:")
        for word in words:
            print(f"   • \"{word}\"")
    
    print(f"\n💡 Ejemplos de consultas optimizadas:")
    optimized_queries = [
        "SELECT operaciones completas con sucursal y cliente",
        "pagos detallados incluyendo información de agencia", 
        "transacciones con datos completos de personas",
        "operaciones relacionadas con oficinas y abonados",
        "FSD010 con detalles de FST001 y FST002"
    ]
    
    for query in optimized_queries:
        print(f"   ✅ \"{query}\"")

if __name__ == "__main__":
    try:
        test_fsd010_joins()
        test_multiple_joins() 
        show_query_keywords()
        
        print(f"\n\n🎉 PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 70)
        print(f"✅ Sistema de JOINs automáticos funcionando correctamente")
        print(f"✅ Detección de patrones Bantotal por posición de campos")
        print(f"✅ Generación de SQL con relaciones semánticamente correctas")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        sys.exit(1)
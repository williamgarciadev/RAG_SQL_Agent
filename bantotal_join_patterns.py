# Análisis de Patrones de JOIN en Tablas Bantotal
# Implementación de detección automática de relaciones por posición de campos

class BantotalJoinAnalyzer:
    """
    Analizador de patrones de JOIN para tablas Bantotal.
    Detecta relaciones basadas en la posición y semántica de campos.
    """
    
    def __init__(self):
        # Patrones de campos estándar Bantotal por posición
        self.FIELD_PATTERNS = {
            1: 'Pgcod',      # Siempre Código Empresa (común en todas)
            2: '{prefix}mod', # Módulo con prefijo de tabla
            3: '{prefix}suc', # Sucursal con prefijo de tabla  
            4: '{prefix}mda', # Moneda con prefijo de tabla
            5: '{prefix}pap', # Papel con prefijo de tabla
            6: '{prefix}cta', # Cuenta (opcional)
            7: '{prefix}oper',# Operación (opcional)
            8: '{prefix}sbop',# Sub-operación (opcional)
            9: '{prefix}tope',# Tipo operación (opcional)
        }
        
        # Mapeo de prefijos por tabla
        self.TABLE_PREFIXES = {
            'FSD010': 'Ao',  # Operaciones (Account Operations)
            'FSD601': 'Pp',  # Op. a Plazo (Plazo Products)
            'FST001': 'Sc',  # Sucursales (Sucursal Code)
            'FST002': 'Cl',  # Clientes (Client)
            'FST003': 'Ab',  # Abonados (Abonado)
            'FSR001': 'Rel', # Relaciones
        }
        
        # Reglas semánticas de negocio bancario
        self.SEMANTIC_RULES = {
            ('FSD010', 'FSD601'): 'LEFT',   # Operaciones -> Op. Plazo
            ('FSD010', 'FST001'): 'INNER',  # Operaciones -> Sucursales  
            ('FSD010', 'FST002'): 'LEFT',   # Operaciones -> Clientes
            ('FSD601', 'FST001'): 'INNER',  # Op. Plazo -> Sucursales
            ('FSD601', 'FST002'): 'LEFT',   # Op. Plazo -> Clientes
            ('FST002', 'FST001'): 'INNER',  # Clientes -> Sucursales
        }
    
    def analyze_join_pattern(self, table1_fields, table2_fields, table1_name, table2_name):
        """
        Analiza el patrón de JOIN entre dos tablas basado en posición de campos.
        
        Args:
            table1_fields: Lista de campos de la tabla 1
            table2_fields: Lista de campos de la tabla 2
            table1_name: Nombre de tabla 1
            table2_name: Nombre de tabla 2
            
        Returns:
            Dict con información del JOIN detectado
        """
        
        join_info = {
            'can_join': False,
            'join_fields': [],
            'confidence': 0.0,
            'join_type': 'LEFT',
            'semantic_reason': ''
        }
        
        # Verificar si ambas son tablas Bantotal
        if not (table1_name.upper().startswith('FS') and table2_name.upper().startswith('FS')):
            return join_info
        
        prefix1 = self.TABLE_PREFIXES.get(table1_name.upper())
        prefix2 = self.TABLE_PREFIXES.get(table2_name.upper())
        
        if not (prefix1 and prefix2):
            return join_info
        
        # Analizar campos por posición
        min_fields = min(len(table1_fields), len(table2_fields))
        matching_positions = []
        
        for pos in range(min_fields):
            field1 = table1_fields[pos]
            field2 = table2_fields[pos]
            
            # Verificar patrones por posición
            if pos + 1 in self.FIELD_PATTERNS:
                expected_pattern = self.FIELD_PATTERNS[pos + 1]
                
                if pos == 0:  # Posición 1: Pgcod (siempre igual)
                    if field1['name'] == 'Pgcod' and field2['name'] == 'Pgcod':
                        matching_positions.append({
                            'position': pos + 1,
                            'field1': field1['name'],
                            'field2': field2['name'],
                            'match_type': 'exact',
                            'semantic': 'Código Empresa'
                        })
                else:  # Posiciones 2+: Con prefijos diferentes
                    pattern_suffix = expected_pattern.replace('{prefix}', '')
                    expected_field1 = f"{prefix1}{pattern_suffix}"
                    expected_field2 = f"{prefix2}{pattern_suffix}"
                    
                    if (field1['name'] == expected_field1 and 
                        field2['name'] == expected_field2):
                        matching_positions.append({
                            'position': pos + 1,
                            'field1': field1['name'],
                            'field2': field2['name'],
                            'match_type': 'pattern',
                            'semantic': self._get_field_semantic(pattern_suffix)
                        })
        
        # Calcular confianza
        if len(matching_positions) >= 2:  # Al menos Pgcod + 1 más
            join_info['can_join'] = True
            join_info['join_fields'] = matching_positions
            join_info['confidence'] = min(len(matching_positions) / 5.0, 1.0)  # Max 5 campos
            
            # Determinar tipo de JOIN por reglas semánticas
            join_info['join_type'] = self._determine_join_type(table1_name, table2_name)
            join_info['semantic_reason'] = self._get_semantic_reason(table1_name, table2_name)
        
        return join_info
    
    def _get_field_semantic(self, suffix):
        """Obtener descripción semántica del campo."""
        semantics = {
            'mod': 'Módulo',
            'suc': 'Sucursal',
            'mda': 'Moneda',
            'pap': 'Papel',
            'cta': 'Cuenta',
            'oper': 'Operación',
            'sbop': 'Sub-operación',
            'tope': 'Tipo de Operación'
        }
        return semantics.get(suffix, f'Campo {suffix}')
    
    def _determine_join_type(self, table1, table2):
        """Determinar tipo de JOIN basado en reglas semánticas."""
        key = (table1.upper(), table2.upper())
        reverse_key = (table2.upper(), table1.upper())
        
        if key in self.SEMANTIC_RULES:
            return self.SEMANTIC_RULES[key]
        elif reverse_key in self.SEMANTIC_RULES:
            return self.SEMANTIC_RULES[reverse_key]
        
        return 'LEFT'  # Default conservador
    
    def _get_semantic_reason(self, table1, table2):
        """Obtener razón semántica del JOIN."""
        descriptions = {
            'FSD010': 'Operaciones Bancarias',
            'FSD601': 'Operaciones a Plazo',
            'FST001': 'Sucursales',
            'FST002': 'Clientes',
            'FST003': 'Abonados'
        }
        
        desc1 = descriptions.get(table1.upper(), table1)
        desc2 = descriptions.get(table2.upper(), table2)
        
        return f"Relación entre {desc1} y {desc2}"
    
    def generate_join_sql(self, main_table, join_info_list, limit=100):
        """
        Generar SQL con JOINs automáticos.
        
        Args:
            main_table: Tabla principal
            join_info_list: Lista de información de JOINs
            limit: Límite de registros
            
        Returns:
            String con SQL generado
        """
        
        if not join_info_list:
            return f"SELECT TOP {limit} * FROM {main_table};"
        
        # Alias para tablas
        aliases = ['A', 'B', 'C', 'D']
        main_alias = aliases[0]
        
        sql_parts = []
        sql_parts.append("-- SQL con JOINs automáticos basado en patrones Bantotal")
        
        # SELECT con campos principales
        select_fields = [f"{main_alias}.*"]
        
        # FROM principal
        sql_parts.append(f"SELECT TOP {limit}")
        sql_parts.append(f"    {main_alias}.*")
        
        # Agregar campos descriptivos de tablas relacionadas
        for i, join_info in enumerate(join_info_list[:3]):  # Máximo 3 JOINs
            alias = aliases[i + 1]
            table_name = join_info.get('table_name', f'Related{i+1}')
            
            # Campos descriptivos específicos por tipo de tabla
            if 'FST001' in table_name:  # Sucursales
                sql_parts.append(f"    {alias}.Scnom AS NombreSucursal{i+1}")
            elif 'FST002' in table_name or 'FST003' in table_name:  # Clientes/Abonados
                sql_parts.append(f"    {alias}.Clnom AS NombreCliente{i+1}")
        
        sql_parts.append(f"FROM {main_table} {main_alias}")
        
        # Generar JOINs
        for i, join_info in enumerate(join_info_list[:3]):
            if not join_info['can_join']:
                continue
                
            alias = aliases[i + 1]
            table_name = join_info.get('table_name', f'Related{i+1}')
            join_type = join_info['join_type']
            
            # Condiciones de JOIN
            join_conditions = []
            for field_info in join_info['join_fields'][:3]:  # Primeros 3 campos
                field1 = field_info['field1']
                field2 = field_info['field2']
                join_conditions.append(f"{main_alias}.{field1} = {alias}.{field2}")
            
            join_condition = ' AND '.join(join_conditions)
            sql_parts.append(f"{join_type} JOIN {table_name} {alias} ON {join_condition}")
        
        # ORDER BY
        sql_parts.append(f"ORDER BY {main_alias}.Pgcod")
        
        return '\n'.join(sql_parts) + ';'


# Ejemplo de uso
if __name__ == "__main__":
    analyzer = BantotalJoinAnalyzer()
    
    # Campos de ejemplo FSD010
    fsd010_fields = [
        {'name': 'Pgcod', 'type': 'smallint'},
        {'name': 'Aomod', 'type': 'int'},
        {'name': 'Aosuc', 'type': 'int'},
        {'name': 'Aomda', 'type': 'smallint'},
        {'name': 'Aopap', 'type': 'int'},
    ]
    
    # Campos de ejemplo FSD601
    fsd601_fields = [
        {'name': 'Pgcod', 'type': 'smallint'},
        {'name': 'Ppmod', 'type': 'int'},
        {'name': 'Ppsuc', 'type': 'int'},
        {'name': 'Ppmda', 'type': 'smallint'},
        {'name': 'Pppap', 'type': 'int'},
    ]
    
    # Analizar patrón
    join_pattern = analyzer.analyze_join_pattern(
        fsd010_fields, fsd601_fields, 'FSD010', 'FSD601'
    )
    
    print("🔍 Análisis de JOIN Pattern:")
    print(f"Puede hacer JOIN: {join_pattern['can_join']}")
    print(f"Confianza: {join_pattern['confidence']:.2f}")
    print(f"Tipo de JOIN: {join_pattern['join_type']}")
    print(f"Razón: {join_pattern['semantic_reason']}")
    
    print("\n📊 Campos de JOIN detectados:")
    for field in join_pattern['join_fields']:
        print(f"  Pos {field['position']}: {field['field1']} = {field['field2']} ({field['semantic']})")
    
    # Generar SQL
    join_info_list = [{'table_name': 'dbo.FSD601', **join_pattern}]
    sql = analyzer.generate_join_sql('dbo.FSD010', join_info_list)
    
    print(f"\n🗄️ SQL Generado:")
    print(sql)
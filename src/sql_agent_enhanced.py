    def _get_enhanced_metadata(self, table_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """Obtener metadatos enriquecidos de enhanced_sql_metadata.json."""
        if not table_name:
            return None
            
        # Metadatos estáticos desde el JSON (podría cargarse dinámicamente)
        enhanced_tables = {
            'FST001': {
                'description': 'Sucursales',
                'column_count': 12,
                'foreign_keys_count': 2,
                'indexes_count': 2,
                'sample_fields': [
                    {'name': 'Pgcod', 'full_type': 'smallint', 'is_primary_key': 'YES', 'description': 'Código Empresa'},
                    {'name': 'Sucurs', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Código Sucursal'},
                    {'name': 'Scnom', 'full_type': 'char(30)', 'is_primary_key': 'NO', 'description': 'Nombre Sucursal'},
                ]
            },
            'FST023': {
                'description': 'Género de Personas Físicas',
                'column_count': 4,
                'foreign_keys_count': 0, 
                'indexes_count': 1,
                'sample_fields': [
                    {'name': 'FST023Cod', 'full_type': 'char(1)', 'is_primary_key': 'YES', 'description': 'Código de Identidad de Género'},
                    {'name': 'FST023Dsc', 'full_type': 'char(20)', 'is_primary_key': 'NO', 'description': 'Descripción de Identidad de Género'},
                ]
            },
            'FSD010': {
                'description': 'Operaciones Bancarias',
                'column_count': 45,
                'foreign_keys_count': 13,
                'indexes_count': 10,
                'sample_fields': [
                    {'name': 'Pgcod', 'full_type': 'smallint', 'is_primary_key': 'YES', 'description': 'Código Empresa'},
                    {'name': 'Aomod', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Módulo'},
                    {'name': 'Aosuc', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Sucursal'},
                    {'name': 'Aomda', 'full_type': 'smallint', 'is_primary_key': 'YES', 'description': 'Moneda'},
                    {'name': 'Aopap', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Papel'},
                ]
            },
            'FSD601': {
                'description': 'Operaciones a Plazo',
                'column_count': 31,
                'foreign_keys_count': 11,
                'indexes_count': 10,
                'sample_fields': [
                    {'name': 'Pgcod', 'full_type': 'smallint', 'is_primary_key': 'YES', 'description': 'Código Empresa'},
                    {'name': 'Ppmod', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Módulo'},
                    {'name': 'Ppsuc', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Sucursal'},
                    {'name': 'Ppmda', 'full_type': 'smallint', 'is_primary_key': 'YES', 'description': 'Moneda'},
                    {'name': 'Pppap', 'full_type': 'int', 'is_primary_key': 'YES', 'description': 'Papel'},
                ]
            }
        }
        
        return enhanced_tables.get(table_name.upper())
-- JOINs INTELIGENTES PARA FSD601
-- Generado automáticamente basado en PKs reales

-- 1. JOIN con Fpp002 (tabla más relacionada)
-- Tablas: Fsd601, Fpp002
-- Campos comunes: 11
-- SELECT con JOIN a tabla más relacionada
SELECT 
    f601.*,
    dbo.Fpp002.*
FROM dbo.Fsd601 f601
INNER JOIN dbo.Fpp002 
    ON dbo.Fsd601.Pgcod = dbo.Fpp002.Pgcod AND dbo.Fsd601.Ppmod = dbo.Fpp002.Ppmod AND dbo.Fsd601.Ppsuc = dbo.Fpp002.Ppsuc AND dbo.Fsd601.Ppmda = dbo.Fpp002.Ppmda AND dbo.Fsd601.Pppap = dbo.Fpp002.Pppap AND dbo.Fsd601.Ppcta = dbo.Fpp002.Ppcta AND dbo.Fsd601.Ppoper = dbo.Fpp002.Ppoper AND dbo.Fsd601.Ppsbop = dbo.Fpp002.Ppsbop AND dbo.Fsd601.Pptope = dbo.Fpp002.Pptope AND dbo.Fsd601.Ppfpag = dbo.Fpp002.Ppfpag AND dbo.Fsd601.Pptipo = dbo.Fpp002.Pptipo;

-- 2. JOIN múltiple con 3 tablas
-- Tablas: Fsd601, Fpp002, Fpp003, Fsd602
-- Campos comunes: 33
-- SELECT con JOINs múltiples
SELECT 
    f601.*,t1.*,t2.*,t3.*
FROM dbo.Fsd601 f601
LEFT JOIN dbo.Fpp002 t1 ON dbo.Fsd601.Pgcod = t1.Pgcod AND dbo.Fsd601.Ppmod = t1.Ppmod AND dbo.Fsd601.Ppsuc = t1.Ppsuc AND dbo.Fsd601.Ppmda = t1.Ppmda AND dbo.Fsd601.Pppap = t1.Pppap AND dbo.Fsd601.Ppcta = t1.Ppcta AND dbo.Fsd601.Ppoper = t1.Ppoper AND dbo.Fsd601.Ppsbop = t1.Ppsbop AND dbo.Fsd601.Pptope = t1.Pptope AND dbo.Fsd601.Ppfpag = t1.Ppfpag AND dbo.Fsd601.Pptipo = t1.Pptipo
LEFT JOIN dbo.Fpp003 t2 ON dbo.Fsd601.Pgcod = t2.Pgcod AND dbo.Fsd601.Ppmod = t2.Ppmod AND dbo.Fsd601.Ppsuc = t2.Ppsuc AND dbo.Fsd601.Ppmda = t2.Ppmda AND dbo.Fsd601.Pppap = t2.Pppap AND dbo.Fsd601.Ppcta = t2.Ppcta AND dbo.Fsd601.Ppoper = t2.Ppoper AND dbo.Fsd601.Ppsbop = t2.Ppsbop AND dbo.Fsd601.Pptope = t2.Pptope AND dbo.Fsd601.Ppfpag = t2.Ppfpag AND dbo.Fsd601.Pptipo = t2.Pptipo
LEFT JOIN dbo.Fsd602 t3 ON dbo.Fsd601.Pgcod = t3.Pgcod AND dbo.Fsd601.Ppmod = t3.Ppmod AND dbo.Fsd601.Ppsuc = t3.Ppsuc AND dbo.Fsd601.Ppmda = t3.Ppmda AND dbo.Fsd601.Pppap = t3.Pppap AND dbo.Fsd601.Ppcta = t3.Ppcta AND dbo.Fsd601.Ppoper = t3.Ppoper AND dbo.Fsd601.Ppsbop = t3.Ppsbop AND dbo.Fsd601.Pptope = t3.Pptope AND dbo.Fsd601.Ppfpag = t3.Ppfpag AND dbo.Fsd601.Pptipo = t3.Pptipo;

-- 3. Análisis de registros por tabla
-- Tablas: Fsd601, Fpp002, Fpp003, Fsd602, Fsd611, Fsd612
-- Campos comunes: 0
-- Análisis de registros relacionados
SELECT 
    'Tabla principal' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.Fsd601

UNION ALL
SELECT 
    'Fpp002' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.Fpp002
UNION ALL
SELECT 
    'Fpp003' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.Fpp003
UNION ALL
SELECT 
    'Fsd602' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.Fsd602
UNION ALL
SELECT 
    'Fsd611' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.Fsd611
UNION ALL
SELECT 
    'Fsd612' as Tabla,
    COUNT(*) as Total_Registros
FROM dbo.Fsd612;


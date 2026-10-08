// Consultas de Power Query (lenguaje M) para cargar las tablas del Excel en Power BI.
// Cómo usarlas: Inicio > Transformar datos > Nueva fuente > Consulta en blanco > Editor avanzado.
// Pegá una consulta por cada tabla y cambiá la ruta del archivo por la tuya.
// Si usás tu Excel real, la ruta es la de TablaWishList.xlsx (necesita la hoja Analisis: guardá un artículo desde la app).

// ---------- Consulta 1: TablaAnalisis ----------
let
    Origen = Excel.Workbook(File.Contents("C:\RUTA\A\TU\ARCHIVO\WishList_demo.xlsx"), null, true),
    Tabla = Origen{[Item = "TablaAnalisis", Kind = "Table"]}[Data],
    Tipos = Table.TransformColumnTypes(
        Tabla,
        {
            {"Costo Estimado", type number},
            {"Urgencia", Int64.Type},
            {"Valor", Int64.Type},
            {"Puntaje", type number},
            {"% del Ingreso", type number},
            {"Impacto en Fondo %", type number},
            {"Compromiso Mensual", type number},
            {"Meses de Espera", type number},
            {"Fecha de alta", type date},
            {"Fecha Estimada", type date}
        }
    )
in
    Tipos

// ---------- Consulta 2: TablaPerfil ----------
let
    Origen = Excel.Workbook(File.Contents("C:\RUTA\A\TU\ARCHIVO\WishList_demo.xlsx"), null, true),
    Tabla = Origen{[Item = "TablaPerfil", Kind = "Table"]}[Data],
    Tipos = Table.TransformColumnTypes(
        Tabla,
        {
            {"Ingreso Neto Mensual", type number},
            {"Gastos fijos", type number},
            {"Deseos ya gastados", type number},
            {"Ahorro actual", type number},
            {"Meses de Fondo de emergencia objetivo", type number}
        }
    )
in
    Tipos

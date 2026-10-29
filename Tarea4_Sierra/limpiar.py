"""Limpieza de Online Retail (UCI). Se reutiliza en la Parte 6 y en el proyecto.

Uso:
    from limpiar import cargar, limpiar
    crudo = cargar("data/Online Retail.xlsx")
    limpio = limpiar(crudo)                                   # DataFrame limpio
    limpio, bitacora = limpiar(crudo, devolver_bitacora=True)  # + bitácora 1.3

Las reglas se aplican en este orden (el orden cambia los conteos):
    1. Filas duplicadas exactas                      -> se van
    2. Facturas que no empiezan con dígito ni con C  -> se van (A = "Adjust bad debt")
    3. Pedidos anulados con un ajuste "Manual"        -> se van
    4. StockCode que no son productos                -> se van (portes, comisiones, cargos...)
    5. UnitPrice <= 0                                -> se van
    6. Quantity < 0 en facturas que no son C         -> se van (ajustes de inventario)
Las cancelaciones (facturas con C) se quedan y restan el día en que ocurren.
Las filas sin CustomerID se quedan; la Parte 6 las filtra con `solo_clientes=True`.
"""
import re

import numpy as np
import pandas as pd

COLUMNAS_TEXTO = {"InvoiceNo": str, "StockCode": str, "CustomerID": str}

# Códigos que no empiezan con cinco dígitos y que NO son mercancía.
# (Los que sí son productos, como PADS o DCGS..., no están en la lista.)
CODIGOS_NO_PRODUCTO = {
    "POST",          # POSTAGE: cobro de envío
    "DOT",           # DOTCOM POSTAGE: cobro de envío
    "C2",            # CARRIAGE: cobro de transporte
    "M",             # Manual: ajustes manuales de precio
    "D",             # Discount: descuento administrativo
    "S",             # SAMPLES
    "B",             # Adjust bad debt
    "CRUK",          # CRUK Commission: comisión a una ONG
    "AMAZONFEE",     # comisión de Amazon
    "BANK CHARGES",  # cargos bancarios
    "ADJUST", "ADJUST2",
    "TEST001", "TEST002",
}
PREFIJOS_NO_PRODUCTO = ("GIFT_",)  # gift_0001_10, ...: vales de regalo


def cargar(ruta):
    """Lee el .xlsx original con InvoiceNo, StockCode y CustomerID como texto.

    Si se leyeran como números: InvoiceNo mezcla '536365' con 'C536379' (pandas
    deja una columna con tipos mezclados), StockCode mezcla 85123 con '85123A'
    (los códigos numéricos perderían su identidad de texto) y CustomerID, al
    tener vacíos, se convertiría en float (17850.0), lo que rompe los cruces.
    """
    df = pd.read_excel(ruta, dtype=COLUMNAS_TEXTO)
    return normalizar(df)


def normalizar(df):
    df = df.copy()
    for c in COLUMNAS_TEXTO:
        s = df[c].astype("string").str.strip()
        df[c] = s.str.replace(r"\.0$", "", regex=True)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    return df


def es_cancelacion(df):
    return df["InvoiceNo"].str.upper().str.startswith("C").fillna(False).astype(bool)


def es_no_producto(df):
    sc = df["StockCode"].str.upper().fillna("")
    return sc.isin(CODIGOS_NO_PRODUCTO) | sc.str.startswith(PREFIJOS_NO_PRODUCTO)


def _pedidos_anulados_manual(df, minimo=1000.0, dias=2):
    """Índices de líneas de venta anuladas con una línea 'M' (Manual) en una factura C.

    Caso típico: un pedido grande se registra con su producto y se cancela con
    un ajuste Manual del mismo monto. Si la regla 4 borra el Manual sin borrar
    el pedido, la limpieza crearía una venta que nunca existió.
    """
    monto = df["Quantity"] * df["UnitPrice"]
    canc = df[es_cancelacion(df) & (df["StockCode"].str.upper() == "M") & (monto.abs() >= minimo)]
    ventas = df[~es_cancelacion(df) & ~es_no_producto(df) & (monto >= minimo)]
    quitar = []
    for _, c in canc.iterrows():
        objetivo = round(abs(c["Quantity"] * c["UnitPrice"]), 2)
        if pd.isna(c["CustomerID"]):
            mismo_cliente = ventas["CustomerID"].isna()
        else:
            mismo_cliente = (ventas["CustomerID"] == c["CustomerID"]).fillna(False)
        cand = ventas[
            mismo_cliente.astype(bool)
            & ((c["InvoiceDate"] - ventas["InvoiceDate"]).abs() <= pd.Timedelta(days=dias))
            & ((ventas["Quantity"] * ventas["UnitPrice"]).round(2) == objetivo)
        ]
        if len(cand):
            quitar.append(cand.index[0])
    return pd.Index(quitar)


def limpiar(df, devolver_bitacora=False, solo_clientes=False):
    """Devuelve el DataFrame limpio (y opcionalmente la bitácora de limpieza)."""
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        df = normalizar(df)
    bitacora = []

    def registrar(orden, regla, decision, mascara):
        quitado = df[mascara]
        bitacora.append({
            "orden": orden, "regla": regla, "decisión": decision,
            "filas eliminadas": int(mascara.sum()),
            "monto eliminado (£)": float((quitado["Quantity"] * quitado["UnitPrice"]).sum()),
            "|monto| eliminado (£)": float((quitado["Quantity"] * quitado["UnitPrice"]).abs().sum()),
        })
        return df[~mascara]

    df = registrar(1, "Filas duplicadas exactas", "se van", df.duplicated(keep="first"))

    inicio = df["InvoiceNo"].str[0].fillna("")
    df = registrar(2, "Factura no empieza con dígito ni con C", "se van",
                   ~(inicio.str.isdigit() | (inicio.str.upper() == "C")))

    df = registrar(3, "Pedido anulado con ajuste Manual (M)", "se van",
                   df.index.isin(_pedidos_anulados_manual(df)))

    df = registrar(4, "StockCode que no es producto", "se van", es_no_producto(df))

    df = registrar(5, "UnitPrice <= 0", "se van", df["UnitPrice"] <= 0)

    df = registrar(6, "Quantity < 0 en factura que no es C", "se van",
                   (df["Quantity"] < 0) & ~es_cancelacion(df))

    if solo_clientes:
        df = registrar(7, "Sin CustomerID (solo para RFM)", "se van", df["CustomerID"].isna())

    df = df.copy()
    df["EsCancelacion"] = es_cancelacion(df)
    df["Venta"] = df["Quantity"] * df["UnitPrice"]
    df["Fecha"] = df["InvoiceDate"].dt.normalize()
    df = df.reset_index(drop=True)

    if devolver_bitacora:
        return df, pd.DataFrame(bitacora)
    return df

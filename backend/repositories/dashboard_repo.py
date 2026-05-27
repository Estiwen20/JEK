from backend.database.connection import get_connection
from datetime import datetime, timedelta


def obtener_ventas_por_hora_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        filas = conn.execute("""
            SELECT strftime('%H', fecha_pago) as hora,
                   SUM(total) as total
            FROM facturas
            WHERE fecha_pago LIKE ?
            GROUP BY hora
            ORDER BY hora
        """, (f"{hoy}%",)).fetchall()
    return {f["hora"]: f["total"] for f in filas}


def obtener_platos_mas_pedidos_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        filas = conn.execute("""
            SELECT pl.nombre, SUM(pp.cantidad) as total
            FROM pedido_platos pp
            JOIN platos pl ON pp.plato_id = pl.id
            JOIN pedidos pe ON pp.pedido_id = pe.id
            WHERE pe.fecha LIKE ?
            GROUP BY pl.id
            ORDER BY total DESC
            LIMIT 5
        """, (f"{hoy}%",)).fetchall()
    return [(f["nombre"], f["total"]) for f in filas]


def obtener_pedidos_por_estado():
    with get_connection() as conn:
        filas = conn.execute("""
            SELECT estado, COUNT(*) as total
            FROM pedidos
            WHERE estado != 'cerrado'
            GROUP BY estado
        """).fetchall()
    return {f["estado"]: f["total"] for f in filas}


def obtener_ingresos_ultimos_7_dias():
    resultado = []
    for i in range(6, -1, -1):
        dia = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        with get_connection() as conn:
            f = conn.execute("""
                SELECT COALESCE(SUM(total), 0) as total
                FROM facturas
                WHERE fecha_pago LIKE ?
            """, (f"{dia}%",)).fetchone()
        resultado.append((dia, f["total"]))
    return resultado


def obtener_metricas_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        ventas = conn.execute("""
            SELECT COALESCE(SUM(total), 0) as total
            FROM facturas WHERE fecha_pago LIKE ?
        """, (f"{hoy}%",)).fetchone()["total"]

        facturas = conn.execute("""
            SELECT COUNT(*) as total
            FROM facturas WHERE fecha_pago LIKE ?
        """, (f"{hoy}%",)).fetchone()["total"]

        pedidos_activos = conn.execute("""
            SELECT COUNT(*) as total
            FROM pedidos WHERE estado NOT IN ('cerrado')
        """).fetchone()["total"]

        pedidos_listos = conn.execute("""
            SELECT COUNT(*) as total
            FROM pedidos WHERE estado = 'listo'
        """).fetchone()["total"]

        mesas_ocupadas = conn.execute("""
            SELECT COUNT(*) as total
            FROM mesas WHERE estado = 'ocupada'
        """).fetchone()["total"]

        total_mesas = conn.execute("""
            SELECT COUNT(*) as total FROM mesas
        """).fetchone()["total"]

    return {
        "ventas_hoy": ventas,
        "facturas_hoy": facturas,
        "pedidos_activos": pedidos_activos,
        "pedidos_listos": pedidos_listos,
        "mesas_ocupadas": mesas_ocupadas,
        "total_mesas": total_mesas,
    }
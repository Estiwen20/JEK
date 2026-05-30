from backend.database.connection import get_connection
from datetime import datetime, timedelta


def obtener_ventas_por_hora(fecha):
    with get_connection() as conn:
        filas = conn.execute("""
            SELECT strftime('%H', fecha_pago) as hora,
                   SUM(total) as total
            FROM facturas
            WHERE fecha_pago LIKE ?
            GROUP BY hora
            ORDER BY hora
        """, (f"{fecha}%",)).fetchall()
    return {f["hora"]: f["total"] for f in filas}


def obtener_platos_mas_pedidos(fecha_inicio, fecha_fin):
    with get_connection() as conn:
        filas = conn.execute("""
            SELECT pl.nombre, SUM(pp.cantidad) as total
            FROM pedido_platos pp
            JOIN platos pl ON pp.plato_id = pl.id
            JOIN pedidos pe ON pp.pedido_id = pe.id
            WHERE pe.fecha BETWEEN ? AND ?
            GROUP BY pl.id
            ORDER BY total DESC
            LIMIT 5
        """, (f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59")).fetchall()
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


def obtener_ingresos_rango(fecha_inicio, fecha_fin):
    resultado = []
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    delta = fin - inicio
    for i in range(delta.days + 1):
        dia = (inicio + timedelta(days=i)).strftime("%Y-%m-%d")
        with get_connection() as conn:
            f = conn.execute("""
                SELECT COALESCE(SUM(total), 0) as total
                FROM facturas
                WHERE fecha_pago LIKE ?
            """, (f"{dia}%",)).fetchone()
        resultado.append((dia, f["total"]))
    return resultado


def obtener_metricas(fecha_inicio, fecha_fin):
    with get_connection() as conn:
        ventas = conn.execute("""
            SELECT COALESCE(SUM(total), 0) as total
            FROM facturas
            WHERE fecha_pago BETWEEN ? AND ?
        """, (f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59")).fetchone()["total"]

        facturas = conn.execute("""
            SELECT COUNT(*) as total
            FROM facturas
            WHERE fecha_pago BETWEEN ? AND ?
        """, (f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59")).fetchone()["total"]

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

        # Comparativa vs periodo anterior
        dias = (datetime.strptime(fecha_fin, "%Y-%m-%d") -
                datetime.strptime(fecha_inicio, "%Y-%m-%d")).days + 1
        fecha_ant_fin = (datetime.strptime(fecha_inicio, "%Y-%m-%d") -
                         timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_ant_ini = (datetime.strptime(fecha_inicio, "%Y-%m-%d") -
                         timedelta(days=dias)).strftime("%Y-%m-%d")

        ventas_ant = conn.execute("""
            SELECT COALESCE(SUM(total), 0) as total
            FROM facturas
            WHERE fecha_pago BETWEEN ? AND ?
        """, (f"{fecha_ant_ini} 00:00:00", f"{fecha_ant_fin} 23:59:59")).fetchone()["total"]

    variacion = 0
    if ventas_ant > 0:
        variacion = ((ventas - ventas_ant) / ventas_ant) * 100

    return {
        "ventas": ventas,
        "facturas": facturas,
        "pedidos_activos": pedidos_activos,
        "pedidos_listos": pedidos_listos,
        "mesas_ocupadas": mesas_ocupadas,
        "total_mesas": total_mesas,
        "variacion": variacion,
    }


def obtener_facturas_rango(fecha_inicio, fecha_fin):
    with get_connection() as conn:
        filas = conn.execute("""
            SELECT f.id, f.pedido_id, f.total, f.fecha_pago,
                   m.numero as mesa_numero
            FROM facturas f
            JOIN pedidos p ON f.pedido_id = p.id
            JOIN mesas m ON p.mesa_id = m.id
            WHERE f.fecha_pago BETWEEN ? AND ?
            ORDER BY f.fecha_pago DESC
        """, (f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59")).fetchall()
    return [dict(f) for f in filas]
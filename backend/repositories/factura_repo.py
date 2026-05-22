from backend.database.connection import get_connection
from backend.models.factura import Factura


def crear_factura(pedido_id, total, fecha_pago):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO facturas (pedido_id, total, fecha_pago) VALUES (?, ?, ?)",
            (pedido_id, total, fecha_pago)
        )


def obtener_factura_por_pedido(pedido_id):
    with get_connection() as conn:
        f = conn.execute("SELECT * FROM facturas WHERE pedido_id=?", (pedido_id,)).fetchone()
    if f:
        return Factura(id=f["id"], pedido_id=f["pedido_id"],
                       total=f["total"], fecha_pago=f["fecha_pago"])
    return None


def obtener_facturas():
    with get_connection() as conn:
        filas = conn.execute("SELECT * FROM facturas ORDER BY fecha_pago DESC").fetchall()
    return [Factura(id=f["id"], pedido_id=f["pedido_id"],
                    total=f["total"], fecha_pago=f["fecha_pago"]) for f in filas]
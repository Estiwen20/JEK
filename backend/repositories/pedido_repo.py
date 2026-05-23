from backend.database.connection import get_connection
from backend.models.pedido import Pedido, PedidoPlato


def crear_pedido(mesa_id, fecha):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO pedidos (mesa_id, estado, fecha) VALUES (?, 'abierto', ?)",
            (mesa_id, fecha)
        )
        return cursor.lastrowid


def agregar_plato_a_pedido(pedido_id, plato_id, cantidad=1):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO pedido_platos (pedido_id, plato_id, cantidad) VALUES (?, ?, ?)",
            (pedido_id, plato_id, cantidad)
        )


def quitar_plato_de_pedido(pedido_plato_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM pedido_platos WHERE id=?", (pedido_plato_id,))


def obtener_pedidos(filtro_estado=None, filtro_mesa_id=None, filtro_fecha=None):
    query = "SELECT * FROM pedidos WHERE 1=1"
    params = []
    if filtro_estado:
        query += " AND estado=?"
        params.append(filtro_estado)
    if filtro_mesa_id:
        query += " AND mesa_id=?"
        params.append(filtro_mesa_id)
    if filtro_fecha:
        query += " AND fecha LIKE ?"
        params.append(f"{filtro_fecha}%")
    query += " ORDER BY fecha DESC"
    with get_connection() as conn:
        filas = conn.execute(query, params).fetchall()
    return [Pedido(id=f["id"], mesa_id=f["mesa_id"], estado=f["estado"], fecha=f["fecha"]) for f in filas]


def obtener_items_pedido(pedido_id):
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT * FROM pedido_platos WHERE pedido_id=?", (pedido_id,)
        ).fetchall()
    return [PedidoPlato(id=f["id"], pedido_id=f["pedido_id"],
                        plato_id=f["plato_id"], cantidad=f["cantidad"]) for f in filas]


def actualizar_estado_pedido(pedido_id, nuevo_estado):
    with get_connection() as conn:
        conn.execute("UPDATE pedidos SET estado=? WHERE id=?", (nuevo_estado, pedido_id))


def eliminar_pedido(pedido_id):
    with get_connection() as conn:
        # Eliminar items del pedido
        conn.execute("DELETE FROM pedido_platos WHERE pedido_id=?", (pedido_id,))
        # Eliminar el pedido (la factura queda con pedido_id=NULL)
        conn.execute("DELETE FROM pedidos WHERE id=?", (pedido_id,))


def obtener_pedido_abierto_por_mesa(mesa_id):
    with get_connection() as conn:
        f = conn.execute(
            """SELECT * FROM pedidos
               WHERE mesa_id=? AND estado NOT IN ('cerrado')
               ORDER BY fecha DESC LIMIT 1""",
            (mesa_id,)
        ).fetchone()
    if f:
        return Pedido(id=f["id"], mesa_id=f["mesa_id"],
                      estado=f["estado"], fecha=f["fecha"])
    return None

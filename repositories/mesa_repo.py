from database.connection import get_connection
from models.mesa import Mesa


def crear_mesa(numero, capacidad, estado="disponible"):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO mesas (numero, capacidad, estado) VALUES (?, ?, ?)",
            (numero, capacidad, estado)
        )


def obtener_mesas():
    with get_connection() as conn:
        filas = conn.execute("SELECT * FROM mesas ORDER BY numero").fetchall()
    return [Mesa(id=f["id"], numero=f["numero"], capacidad=f["capacidad"], estado=f["estado"]) for f in filas]


def obtener_mesa_por_id(mesa_id):
    with get_connection() as conn:
        f = conn.execute("SELECT * FROM mesas WHERE id = ?", (mesa_id,)).fetchone()
    if f:
        return Mesa(id=f["id"], numero=f["numero"], capacidad=f["capacidad"], estado=f["estado"])
    return None


def actualizar_mesa(mesa_id, numero, capacidad, estado):
    with get_connection() as conn:
        conn.execute(
            "UPDATE mesas SET numero=?, capacidad=?, estado=? WHERE id=?",
            (numero, capacidad, estado, mesa_id)
        )


def eliminar_mesa(mesa_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM mesas WHERE id=?", (mesa_id,))
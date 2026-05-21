from database.connection import get_connection
from models.plato import Plato


def crear_plato(nombre, descripcion, precio, disponible=True):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO platos (nombre, descripcion, precio, disponible) VALUES (?, ?, ?, ?)",
            (nombre, descripcion, precio, int(disponible))
        )


def obtener_platos():
    with get_connection() as conn:
        filas = conn.execute("SELECT * FROM platos ORDER BY nombre").fetchall()
    return [Plato(id=f["id"], nombre=f["nombre"], descripcion=f["descripcion"],
                  precio=f["precio"], disponible=f["disponible"]) for f in filas]


def obtener_plato_por_id(plato_id):
    with get_connection() as conn:
        f = conn.execute("SELECT * FROM platos WHERE id=?", (plato_id,)).fetchone()
    if f:
        return Plato(id=f["id"], nombre=f["nombre"], descripcion=f["descripcion"],
                     precio=f["precio"], disponible=f["disponible"])
    return None


def actualizar_plato(plato_id, nombre, descripcion, precio, disponible):
    with get_connection() as conn:
        conn.execute(
            "UPDATE platos SET nombre=?, descripcion=?, precio=?, disponible=? WHERE id=?",
            (nombre, descripcion, precio, int(disponible), plato_id)
        )


def eliminar_plato(plato_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM platos WHERE id=?", (plato_id,))
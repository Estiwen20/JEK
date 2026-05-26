from backend.database.connection import get_connection
from backend.models.plato import Plato


def crear_plato(nombre, descripcion, precio, disponible=True, categoria="Otros", icono="🍽️"):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO platos (nombre, descripcion, precio, disponible, categoria, icono) VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, descripcion, precio, int(disponible), categoria, icono)
        )


def obtener_platos():
    with get_connection() as conn:
        filas = conn.execute("SELECT * FROM platos ORDER BY categoria, nombre").fetchall()
    return [_fila_a_plato(f) for f in filas]


def obtener_plato_por_id(plato_id):
    with get_connection() as conn:
        f = conn.execute("SELECT * FROM platos WHERE id=?", (plato_id,)).fetchone()
    return _fila_a_plato(f) if f else None


def actualizar_plato(plato_id, nombre, descripcion, precio, disponible, categoria="Otros", icono="🍽️"):
    with get_connection() as conn:
        conn.execute(
            "UPDATE platos SET nombre=?, descripcion=?, precio=?, disponible=?, categoria=?, icono=? WHERE id=?",
            (nombre, descripcion, precio, int(disponible), categoria, icono, plato_id)
        )


def eliminar_plato(plato_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM platos WHERE id=?", (plato_id,))


def _fila_a_plato(f):
    keys = f.keys() if hasattr(f, "keys") else []
    return Plato(
        id=f["id"],
        nombre=f["nombre"],
        descripcion=f["descripcion"],
        precio=f["precio"],
        disponible=f["disponible"],
        categoria=f["categoria"] if "categoria" in keys else "Otros",
        icono=f["icono"] if "icono" in keys else "🍽️",
    )
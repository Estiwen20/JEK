from database.connection import get_connection
from models.usuario import Usuario


def crear_usuario(nombre, usuario, contrasena, rol="mesero"):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO usuarios (nombre, usuario, contrasena, rol) VALUES (?, ?, ?, ?)",
            (nombre, usuario, contrasena, rol)
        )


def obtener_usuario_por_credenciales(usuario, contrasena):
    with get_connection() as conn:
        fila = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND contrasena=?",
            (usuario, contrasena)
        ).fetchone()
    if fila:
        return Usuario(id=fila["id"], nombre=fila["nombre"], usuario=fila["usuario"],
                       contrasena=fila["contrasena"], rol=fila["rol"])
    return None


def obtener_usuarios():
    with get_connection() as conn:
        filas = conn.execute("SELECT * FROM usuarios ORDER BY nombre").fetchall()
    return [Usuario(id=f["id"], nombre=f["nombre"], usuario=f["usuario"],
                    contrasena=f["contrasena"], rol=f["rol"]) for f in filas]


def eliminar_usuario(usuario_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))


def actualizar_usuario(usuario_id, nombre, usuario, contrasena, rol):
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuarios SET nombre=?, usuario=?, contrasena=?, rol=? WHERE id=?",
            (nombre, usuario, contrasena, rol, usuario_id)
        )

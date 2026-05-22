class Usuario:
    def __init__(self, id=None, nombre=None, usuario=None, contrasena=None, rol="mesero"):
        self.id = id
        self.nombre = nombre
        self.usuario = usuario
        self.contrasena = contrasena
        self.rol = rol  # 'admin' o 'mesero'

    def es_admin(self):
        return self.rol == "admin"

    def __repr__(self):
        return f"Usuario({self.usuario} | rol={self.rol})"

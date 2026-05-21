class Plato:
    def __init__(self, id=None, nombre=None, descripcion=None, precio=0.0, disponible=True):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.disponible = bool(disponible)

    def __repr__(self):
        return f"Plato({self.nombre} | ${self.precio:.2f} | {'activo' if self.disponible else 'inactivo'})"
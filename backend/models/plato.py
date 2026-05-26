class Plato:
    def __init__(self, id, nombre, descripcion, precio, disponible, categoria="Otros", icono="🍽️"):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.disponible = bool(disponible)
        self.categoria = categoria or "Otros"
        self.icono = icono or "🍽️"
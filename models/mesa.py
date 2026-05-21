class Mesa:
    def __init__(self, id=None, numero=None, capacidad=None, estado="disponible"):
        self.id = id
        self.numero = numero
        self.capacidad = capacidad
        self.estado = estado

    def __repr__(self):
        return f"Mesa(#{self.numero} | cap={self.capacidad} | estado={self.estado})"
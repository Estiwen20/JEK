from datetime import datetime


class PedidoPlato:
    def __init__(self, id=None, pedido_id=None, plato_id=None, cantidad=1):
        self.id = id
        self.pedido_id = pedido_id
        self.plato_id = plato_id
        self.cantidad = cantidad


class Pedido:
    def __init__(self, id=None, mesa_id=None, estado="abierto", fecha=None):
        self.id = id
        self.mesa_id = mesa_id
        self.estado = estado
        self.fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.items: list[PedidoPlato] = []

    def agregar_item(self, plato_id, cantidad=1):
        self.items.append(PedidoPlato(pedido_id=self.id, plato_id=plato_id, cantidad=cantidad))

    def __repr__(self):
        return f"Pedido(id={self.id} | mesa={self.mesa_id} | estado={self.estado})"
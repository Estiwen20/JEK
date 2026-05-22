class Factura:
    def __init__(self, id=None, pedido_id=None, total=0.0, fecha_pago=None):
        self.id = id
        self.pedido_id = pedido_id
        self.total = total
        self.fecha_pago = fecha_pago

    def __repr__(self):
        return f"Factura(pedido={self.pedido_id} | total=${self.total:.2f} | fecha={self.fecha_pago})"
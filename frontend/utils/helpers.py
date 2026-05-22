from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import os


def generar_factura_pdf(factura, pedido, items_con_platos, mesa):
    carpeta = "facturas"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"factura_{factura.id}.pdf")

    doc = SimpleDocTemplate(ruta, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elementos = []

    # ── Encabezado ──
    estilo_titulo = ParagraphStyle(
        "titulo", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#6c3483"),
        spaceAfter=4
    )
    estilo_sub = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#888888"),
        spaceAfter=2
    )
    elementos.append(Paragraph("🍽  Restaurante", estilo_titulo))
    elementos.append(Paragraph("Sistema de Administración de Mesas y Pedidos", estilo_sub))
    elementos.append(Spacer(1, 0.4*cm))

    # ── Info factura ──
    estilo_info = ParagraphStyle(
        "info", parent=styles["Normal"],
        fontSize=10, spaceAfter=2
    )
    elementos.append(Paragraph(f"<b>Factura N°:</b> {factura.id}", estilo_info))
    elementos.append(Paragraph(f"<b>Pedido N°:</b> {pedido.id}", estilo_info))
    elementos.append(Paragraph(f"<b>Mesa:</b> #{mesa.numero} (capacidad: {mesa.capacidad})", estilo_info))
    elementos.append(Paragraph(f"<b>Fecha de pago:</b> {factura.fecha_pago}", estilo_info))
    elementos.append(Spacer(1, 0.5*cm))

    # ── Tabla de items ──
    encabezado = [["Plato", "Precio unit.", "Cantidad", "Subtotal"]]
    filas = []
    for plato, cantidad in items_con_platos:
        subtotal = plato.precio * cantidad
        filas.append([
            plato.nombre,
            f"${plato.precio:.2f}",
            str(cantidad),
            f"${subtotal:.2f}"
        ])

    tabla_data = encabezado + filas
    tabla = Table(tabla_data, colWidths=[8*cm, 3.5*cm, 3*cm, 3.5*cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#6c3483")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  11),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f5eef8"), colors.white]),
        ("FONTSIZE",      (0, 1), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.5*cm))

    # ── Total ──
    estilo_total = ParagraphStyle(
        "total", parent=styles["Normal"],
        fontSize=13, textColor=colors.HexColor("#1e8449"),
        spaceAfter=4
    )
    elementos.append(Paragraph(f"<b>TOTAL A PAGAR: ${factura.total:.2f}</b>", estilo_total))
    elementos.append(Spacer(1, 0.8*cm))

    # ── Pie ──
    estilo_pie = ParagraphStyle(
        "pie", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#aaaaaa"),
        alignment=1
    )
    elementos.append(Paragraph("Gracias por su visita. ¡Esperamos verle pronto!", estilo_pie))

    doc.build(elementos)
    return ruta
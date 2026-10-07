"""Vale de Salida de Almacén en PDF (botón "Vale" de Entrega.tsx).

En el original el botón solo mostraba "Generando Vale..." y no generaba
nada; aquí se crea el PDF real con ReportLab."""
import io
from functools import lru_cache

from django.contrib.staticfiles import finders
from django.utils import timezone
from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

VERDE = colors.HexColor("#719c44")
VERDE_CLARO = colors.HexColor("#f2f5f0")
OSCURO = colors.HexColor("#353131")
GRIS = colors.HexColor("#817e7e")
BORDE = colors.HexColor("#c0c6b6")

EST = {
    "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=15, textColor=OSCURO, alignment=TA_RIGHT, leading=18),
    "folio": ParagraphStyle("folio", fontName="Helvetica-Bold", fontSize=11, textColor=VERDE, alignment=TA_RIGHT, leading=14),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=8.5, textColor=GRIS, alignment=TA_RIGHT, leading=11),
    "seccion": ParagraphStyle("seccion", fontName="Helvetica-Bold", fontSize=9, textColor=VERDE, leading=12, spaceBefore=4),
    "etiqueta": ParagraphStyle("etiqueta", fontName="Helvetica-Bold", fontSize=7.5, textColor=GRIS, leading=10),
    "valor": ParagraphStyle("valor", fontName="Helvetica", fontSize=10, textColor=OSCURO, leading=13),
    "celda": ParagraphStyle("celda", fontName="Helvetica", fontSize=9, textColor=OSCURO, leading=12),
    "celda_c": ParagraphStyle("celda_c", fontName="Helvetica", fontSize=9, textColor=OSCURO, leading=12, alignment=TA_CENTER),
    "head": ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, leading=10),
    "head_c": ParagraphStyle("head_c", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, leading=10, alignment=TA_CENTER),
    "firma": ParagraphStyle("firma", fontName="Helvetica", fontSize=8.5, textColor=GRIS, alignment=TA_CENTER, leading=11),
    "firma_n": ParagraphStyle("firma_n", fontName="Helvetica-Bold", fontSize=9.5, textColor=OSCURO, alignment=TA_CENTER, leading=12),
    "pie": ParagraphStyle("pie", fontName="Helvetica", fontSize=7.5, textColor=GRIS, alignment=TA_CENTER, leading=10),
}


@lru_cache(maxsize=1)
def _logo():
    """Logo JAPEM reducido y en RGB (el archivo original es CMYK y muy grande)."""
    ruta = finders.find("img/LogoVerde.jpg")
    if not ruta:
        return None
    from PIL import Image as PILImage
    im = PILImage.open(ruta).convert("RGB")
    im.thumbnail((900, 900))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue(), im.size


def _fecha(valor, formato="%d/%m/%Y %H:%M"):
    if not valor:
        return "No registrada"
    if timezone.is_aware(valor):
        valor = timezone.localtime(valor)
    return valor.strftime(formato)


def _dato(etiqueta, valor):
    return [Paragraph(etiqueta.upper(), EST["etiqueta"]), Paragraph(escape(str(valor or "Sin dato")), EST["valor"])]


def generar_vale_pdf(asignacion):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
        title=f"Vale de Salida #{asignacion.pk}", author="JAPEM",
    )
    ancho = doc.width
    historia = []

    # --- Encabezado: logo + título y folio ---
    logo = _logo()
    if logo:
        datos, (w, h) = logo
        alto = 16 * mm
        img = Image(io.BytesIO(datos), width=alto * w / h, height=alto)
    else:
        img = Paragraph("<b>JAPEM</b>", EST["valor"])
    derecha = [
        Paragraph("VALE DE SALIDA DE ALMACÉN", EST["titulo"]),
        Paragraph(f"Folio #{asignacion.pk:06d}", EST["folio"]),
        Paragraph(f"Emitido: {_fecha(timezone.now())}", EST["sub"]),
    ]
    enc = Table([[img, derecha]], colWidths=[ancho * 0.45, ancho * 0.55])
    enc.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, 0), 2, VERDE), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    historia += [enc, Spacer(1, 6 * mm)]

    # --- Institución y datos de la entrega ---
    iap = asignacion.iap
    bloque = Table(
        [
            [Paragraph("INSTITUCIÓN BENEFICIARIA", EST["seccion"]), "", Paragraph("DATOS DE LA ENTREGA", EST["seccion"]), ""],
            _dato("Nombre", iap.nombre_iap) + _dato("Estatus", asignacion.get_estatus_display().upper()),
            _dato("Rubro", iap.rubro) + _dato("Fecha de asignación", _fecha(asignacion.fecha_asignacion or asignacion.created_at)),
            _dato("Clasificación", ", ".join(iap.clasificacion_list) or "Sin dato") + _dato("Fecha de entrega", _fecha(asignacion.fecha_entrega_real)),
            _dato("Población atendida", f"{iap.personas_beneficiadas} personas") + _dato("Lugar de entrega", asignacion.lugar_entrega),
        ],
        colWidths=[ancho * 0.17, ancho * 0.33, ancho * 0.17, ancho * 0.33],
    )
    bloque.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, 0), (1, 0)), ("SPAN", (2, 0), (3, 0)),
        ("BACKGROUND", (0, 0), (-1, -1), VERDE_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE),
        ("LINEAFTER", (1, 0), (1, -1), 0.6, BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))
    historia += [bloque, Spacer(1, 6 * mm)]

    # --- Productos ---
    historia.append(Paragraph("PRODUCTOS ENTREGADOS", EST["seccion"]))
    historia.append(Spacer(1, 2 * mm))
    filas = [[
        Paragraph("#", EST["head_c"]), Paragraph("PRODUCTO", EST["head"]),
        Paragraph("CATEGORÍA", EST["head"]), Paragraph("UNIDAD", EST["head_c"]),
        Paragraph("CANTIDAD", EST["head_c"]),
    ]]
    total = 0
    for n, det in enumerate(asignacion.detalles.select_related("inventario__catalogo_producto"), start=1):
        inv = det.inventario
        unidad = (inv.catalogo_producto.unidad_medida if inv.catalogo_producto_id else None) or inv.clave_unidad or "—"
        filas.append([
            Paragraph(str(n), EST["celda_c"]), Paragraph(escape(inv.nombre_producto), EST["celda"]),
            Paragraph(escape(inv.categoria_producto or "—"), EST["celda"]), Paragraph(escape(unidad), EST["celda_c"]),
            Paragraph(f"<b>{det.cantidad}</b>", EST["celda_c"]),
        ])
        total += det.cantidad
    filas.append(["", Paragraph("<b>TOTAL DE PIEZAS</b>", EST["celda"]), "", "", Paragraph(f"<b>{total}</b>", EST["celda_c"])])
    tabla = Table(filas, colWidths=[ancho * 0.07, ancho * 0.43, ancho * 0.22, ancho * 0.13, ancho * 0.15], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9fafb")]),
        ("BACKGROUND", (0, -1), (-1, -1), VERDE_CLARO),
        ("SPAN", (1, -1), (3, -1)),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDE),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    historia += [tabla, Spacer(1, 22 * mm)]

    # --- Firmas ---
    def firma(titulo, nombre):
        return [
            Paragraph("_" * 38, EST["firma"]),
            Paragraph(escape(nombre) if nombre else "&nbsp;", EST["firma_n"]),
            Paragraph(titulo, EST["firma"]),
        ]
    firmas = Table(
        [[firma("Entrega (Responsable JAPEM)", asignacion.responsable_entrega),
          firma("Recibe (Nombre y firma — IAP)", "")]],
        colWidths=[ancho / 2, ancho / 2],
    )
    firmas.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    historia += [firmas, Spacer(1, 12 * mm)]

    historia.append(Paragraph(
        "Junta de Asistencia Privada del Estado de México · Este vale ampara la salida física "
        "de los productos listados del almacén de donativos.", EST["pie"],
    ))

    doc.build(historia)
    return buffer.getvalue()
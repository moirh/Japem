"""Algoritmo de sugerencia de IAPs para un producto de inventario.

Puerto directo de EntregaController@sugerirAsignacion (Laravel).
"""

from iaps.models import Iap

MATRIZ_REGLAS = {
    "ALIMENT": ["A1", "A2", "B2"],
    "LIMPIEZA": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "C4"],
    "ASEO": ["A1", "A2"],
    "HIGIENE": ["A1", "A2"],
    "PAÑAL": [],  # se define dinámicamente según el producto
    "PAPELERIA": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "C4"],
    "OFICINA": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "C4"],
    "COCINA": ["A1", "A2"],
    "COLCHON": ["A1", "A2"],
    "BLANCOS": ["A1", "A2"],
    "ENTRETENIMIENTO": ["A1", "A2", "B2"],
    "JUGUETE": ["A2", "A3", "B2"],
    "ESCOLAR": ["A2", "A3", "B2"],
    "DIDACTICO": ["A2", "A3"],
    "ROPA": [],  # se define dinámicamente según el producto
    "MEDICAMENTO": ["C1", "A1", "A2"],
    "CURACION": ["A1", "A2", "B1"],
    "SILLA": ["B1"],
    "REHABILITA": ["B1"],
    "PROTECCION CIVIL": ["A1", "A2", "A3", "A4", "B1", "B2", "B3"],
    "MOBILIARIO": ["A1", "A2", "A3", "A4", "B1", "B2", "B3"],
    "ANIMAL": ["D", "C4"],
}


def sugerir_iaps(inventario):
    """Devuelve una lista de dicts {iap, puntaje, razones} ordenada por
    puntaje descendente, para las IAPs candidatas a recibir `inventario`.

    NOTA: igual que el original, solo considera IAPs con estatus == "Activa"
    (no "Activo", que es el valor por defecto del modelo) — es una
    inconsistencia que ya existía en el backend Laravel; ver README.
    """
    prod_nombre = (inventario.nombre_producto or "").upper().strip()
    prod_cat = (inventario.categoria_producto or "").upper().strip()

    reglas = dict(MATRIZ_REGLAS)

    if "PAÑAL" in prod_nombre or "PAÑAL" in prod_cat:
        if "ADULTO" in prod_nombre or "GRANDE" in prod_nombre:
            reglas["PAÑAL"] = ["A1"]
        else:
            reglas["PAÑAL"] = ["A2"]

    if "ROPA" in prod_nombre or "ROPA" in prod_cat or "VESTIDO" in prod_cat:
        if "NIÑ" in prod_nombre or "BEBE" in prod_nombre or "INFANTIL" in prod_nombre:
            reglas["ROPA"] = ["A2"]
        else:
            reglas["ROPA"] = ["C1", "C2", "C3"]

    sugerencias = []

    for iap in Iap.objects.filter(estatus="Activa"):
        clase = (iap.clasificacion or "").upper()
        nec_comp = (iap.necesidad_complementaria or "").upper()

        es_candidato = False
        razones = []

        for keyword, clases_permitidas in reglas.items():
            if keyword in prod_nombre or keyword in prod_cat:
                if clase in clases_permitidas:
                    es_candidato = True
                    razones.append("Autorizado por clasificación")
                    break

        if not es_candidato and nec_comp:
            for item in nec_comp.split(","):
                item = item.strip()
                if not item:
                    continue
                if item in prod_nombre or item in prod_cat:
                    es_candidato = True
                    razones.append(f"Excepción: necesidad complementaria ({item.title()})")
                    break

        if not es_candidato:
            continue

        puntaje = 0
        if iap.es_certificada:
            puntaje += 20
            razones.append("Certificada")
        if iap.tiene_donataria_autorizada:
            puntaje += 30
            razones.append("Donataria autorizada")
        if iap.tiene_padron_beneficiarios:
            puntaje += 20
            razones.append("Padrón vigente")

        if iap.veces_donado == 0:
            puntaje += 50
        else:
            puntaje -= iap.veces_donado * 5

        sugerencias.append({"iap": iap, "puntaje": puntaje, "razones": razones})

    sugerencias.sort(key=lambda s: s["puntaje"], reverse=True)
    return sugerencias

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

URL = "https://dinamics.ccma.cat/wsarafem/arafem/tv/profile/noimage/geo/cat"


def format_date(iso_str):
    """Converteix la data ISO '2026-09-04T22:07:20+02:00' al format XMLTV '20260904220720 +0200'."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y%m%d%H%M%S %z")
    except Exception:
        return ""


def main():
    req = urllib.request.Request(
        URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error descarregant les dades: {e}")
        return

    tv = ET.Element(
        "tv",
        {
            "generator-info-name": "3Cat XMLTV Generator",
            "generator-info-url": "https://github.com",
        },
    )

    canals = data.get("canal", [])
    if isinstance(canals, dict):
        canals = [canals]

    for channel_item in canals:
        # Obtenir el nom del canal de les etiquetes o atributs
        attr = channel_item.get("@attributes", {})
        channel_name = attr.get("name")

        if not channel_name:
            continue

        # Ignorem els canals d'obertura/test 'oca' si estan completament buits
        if channel_name.startswith("oca") and not channel_item.get("ara_fem"):
            continue

        channel_id = f"{channel_name}.cat"

        # 1. Afegir la capçalera de canal <channel>
        ch_elem = ET.SubElement(tv, "channel", {"id": channel_id})
        display_name = ET.SubElement(ch_elem, "display-name")
        display_name.text = channel_name.upper()

        # 2. Afegir els programes ('ara_fem' i 'despres_fem')
        for key in ["ara_fem", "despres_fem"]:
            prog = channel_item.get(key)

            # Comprovar si el programa conté informació vàlida
            if isinstance(prog, dict) and prog.get("start_time"):
                start_xml = format_date(prog.get("start_time"))
                end_xml = format_date(prog.get("end_time"))

                if not start_xml:
                    continue

                p_attr = {"start": start_xml, "channel": channel_id}
                if end_xml:
                    p_attr["stop"] = end_xml

                p_elem = ET.SubElement(tv, "programme", p_attr)

                # Títol del programa
                titol = (
                    prog.get("titol_programa")
                    or prog.get("titol_tdt")
                    or "Sense títol"
                )
                title_el = ET.SubElement(p_elem, "title")
                title_el.text = titol

                # Subtítol / Títol del capítol
                subtitol = prog.get("titol_capitol")
                if subtitol and subtitol != titol:
                    sub_el = ET.SubElement(p_elem, "sub-title")
                    sub_el.text = subtitol

                # Sinopsi / Descripció
                sinopsi = prog.get("sinopsi")
                if sinopsi:
                    desc_el = ET.SubElement(p_elem, "desc")
                    desc_el.text = sinopsi

                # Categoria / Subgrup
                classif = prog.get("classificacio", {})
                if isinstance(classif, dict):
                    categoria = classif.get("subgrup") or classif.get("grup")
                    if categoria:
                        cat_el = ET.SubElement(p_elem, "category")
                        cat_el.text = categoria

    # Guardar l'XML resultant
    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="UTF-8", xml_declaration=True)
    print("Fitxer epg.xml generat correctament amb la informació de tots els canals.")


if __name__ == "__main__":
    main()

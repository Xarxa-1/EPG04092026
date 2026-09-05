from datetime import datetime
import json
import xml.etree.ElementTree as ET


def format_date(iso_str):
    """Converteix la data ISO al format XMLTV '20260904220720 +0200'."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y%m%d%H%M%S %z")
    except Exception:
        return ""


def main():
    # Llegim el fitxer JSON descarregat prèviament
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error llegint data.json: {e}")
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
        attr = channel_item.get("@attributes", {})
        channel_name = attr.get("name")

        if not channel_name:
            continue

        # Ignorem els canals 'oca' buits
        if channel_name.startswith("oca") and not channel_item.get("ara_fem"):
            continue

        channel_id = f"{channel_name}.cat"

        # Afegir capçalera <channel>
        ch_elem = ET.SubElement(tv, "channel", {"id": channel_id})
        display_name = ET.SubElement(ch_elem, "display-name")
        display_name.text = channel_name.upper()

        # Afegir programes ('ara_fem' i 'despres_fem')
        for key in ["ara_fem", "despres_fem"]:
            prog = channel_item.get(key)

            if isinstance(prog, dict) and prog.get("start_time"):
                start_xml = format_date(prog.get("start_time"))
                end_xml = format_date(prog.get("end_time"))

                if not start_xml:
                    continue

                p_attr = {"start": start_xml, "channel": channel_id}
                if end_xml:
                    p_attr["stop"] = end_xml

                p_elem = ET.SubElement(tv, "programme", p_attr)

                # Títol
                titol = (
                    prog.get("titol_programa")
                    or prog.get("titol_tdt")
                    or "Sense títol"
                )
                title_el = ET.SubElement(p_elem, "title")
                title_el.text = titol

                # Subtítol
                subtitol = prog.get("titol_capitol")
                if subtitol and subtitol != titol:
                    sub_el = ET.SubElement(p_elem, "sub-title")
                    sub_el.text = subtitol

                # Descripció
                sinopsi = prog.get("sinopsi")
                if sinopsi:
                    desc_el = ET.SubElement(p_elem, "desc")
                    desc_el.text = sinopsi

                # Categoria
                classif = prog.get("classificacio", {})
                if isinstance(classif, dict):
                    categoria = classif.get("subgrup") or classif.get("grup")
                    if categoria:
                        cat_el = ET.SubElement(p_elem, "category")
                        cat_el.text = categoria

    # Guardar l'XML
    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="UTF-8", xml_declaration=True)
    print("Fitxer epg.xml generat amb èxit a partir de data.json")


if __name__ == "__main__":
    main()

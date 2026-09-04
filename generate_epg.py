from datetime import datetime, timezone
import json
import urllib.request
import xml.etree.ElementTree as ET

# Canals oficials de la CCMA
CHANNELS = {
    "TV3": "tv3.cat",
    "324": "324.cat",
    "C33": "c33.cat",
    "SX3": "sx3.cat",
    "E3": "esport3.cat",
}


def format_date(iso_str):
    """Converteix '2026-09-04T22:07:20+02:00' a '20260904220720 +0200'."""
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime("%Y%m%d%H%M%S %z")


def get_channel_epg(codi_canal):
    """Descarrega la graella completa de 24h per a un canal concret."""
    # S'utilitza la data d'avui en format YYYYMMDD
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://dinamics.ccma.cat/wsarafem/graella/tv/canal/{codi_canal}/{today}"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None


def main():
    tv = ET.Element(
        "tv",
        {
            "generator-info-name": "3Cat XMLTV Generator Full",
            "generator-info-url": "https://github.com",
        },
    )

    # 1. Crear les etiquetes <channel>
    for name, channel_id in CHANNELS.items():
        ch_elem = ET.SubElement(tv, "channel", {"id": channel_id})
        display_name = ET.SubElement(ch_elem, "display-name")
        display_name.text = name

    # 2. Descarregar i afegir tots els programes de cada canal
    for codi_canal, channel_id in CHANNELS.items():
        data = get_channel_epg(codi_canal)
        if not data or "resposta" not in data:
            continue

        programes = data["resposta"].get("programa", [])
        if isinstance(programes, dict):
            programes = [programes]

        for prog in programes:
            if "start_time" not in prog or "end_time" not in prog:
                continue

            p_elem = ET.SubElement(
                tv,
                "programme",
                {
                    "start": format_date(prog["start_time"]),
                    "stop": format_date(prog["end_time"]),
                    "channel": channel_id,
                },
            )

            title = ET.SubElement(p_elem, "title")
            title.text = prog.get("titol_programa", "")

            if prog.get("titol_capitol"):
                subtitle = ET.SubElement(p_elem, "sub-title")
                subtitle.text = prog.get("titol_capitol")

            if prog.get("sinopsi"):
                desc = ET.SubElement(p_elem, "desc")
                desc.text = prog.get("sinopsi")

    # Guardar a l'arxiu XML
    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    main()

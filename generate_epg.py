from datetime import datetime, timezone
import json
import xml.etree.ElementTree as ET
import urllib.request

URL = "https://dinamics.ccma.cat/wsarafem/arafem/tv/profile/noimage/geo/cat"


def format_date(iso_str):
    """Converteix la data ISO '2026-09-04T22:07:20+02:00' al format XMLTV '20260904220720 +0200'."""
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime("%Y%m%d%H%M%S %z")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())

    tv = ET.Element(
        "tv",
        {
            "generator-info-name": "3Cat XMLTV Generator",
            "generator-info-url": "https://github.com",
        },
    )

    channels = set()
    programmes = []

    for channel_item in data.get("canal", []):
        channel_name = channel_item.get("@attributes", {}).get("name")
        if not channel_name or channel_name.startswith("oca"):
            continue

        channel_id = f"{channel_name}.cat"
        channels.add((channel_id, channel_name.upper()))

        # Extreure programació actual i posterior
        for key in ["ara_fem", "despres_fem"]:
            prog = channel_item.get(key)
            if isinstance(prog, dict) and "start_time" in prog:
                programmes.append((channel_id, prog))

    # afegir <channel>
    for ch_id, ch_name in sorted(channels):
        ch_elem = ET.SubElement(tv, "channel", {"id": ch_id})
        display_name = ET.SubElement(ch_elem, "display-name")
        display_name.text = ch_name

    # afegir <programme>
    for ch_id, prog in programmes:
        p_elem = ET.SubElement(
            tv,
            "programme",
            {
                "start": format_date(prog["start_time"]),
                "stop": format_date(prog["end_time"]),
                "channel": ch_id,
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

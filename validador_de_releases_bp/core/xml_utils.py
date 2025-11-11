import re
import xml.etree.ElementTree as ET

def limpa_arquivo(raw_data: bytes) -> str:
    text = raw_data.decode("utf-8", errors="ignore")
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    text = re.sub(r"&#x[0-9A-Fa-f]+;", "", text)
    return text

def carrega_xml(text: str) -> ET.Element:
    return ET.fromstring(text)

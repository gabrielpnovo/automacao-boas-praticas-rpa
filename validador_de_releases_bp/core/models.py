from dataclasses import dataclass
import xml.etree.ElementTree as ET

@dataclass
class BluePrismItem:
    id: str
    name: str
    root: ET.Element

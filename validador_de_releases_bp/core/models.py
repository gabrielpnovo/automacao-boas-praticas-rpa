from dataclasses import dataclass
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

@dataclass
class BluePrismItem(ABC):
    id: str
    name: str
    root: ET.Element
    namespace: str = "http://www.blueprism.co.uk/product/process"

    @property
    def ns(self):
        return {"bp": self.namespace}
    
    def find(self, path: str) -> ET.Element | None:
        """Busca um único elemento, aplicando namespace automaticamente"""
        return self.root.find(path, self.ns)

    def find_all(self, path: str) -> list[ET.Element]:
        """Busca múltiplos elementos, aplicando namespace automaticamente"""
        return self.root.findall(path, self.ns)
    
@dataclass
class BluePrismProcesso(BluePrismItem):
    def validar_publicacao(self) -> bool:
        return self.root.get("published", "false").lower() == "true"

@dataclass
class BluePrismObjeto(BluePrismItem):
    def validar_publicacao_paginas(self) -> bool:
        print(self.root)
        pages = self.find_all(".//bp:subsheet")
        print('entrou')
        for page in pages:
            nome = page.find("{http://www.blueprism.co.uk/product/process}name")
            print(nome.text)

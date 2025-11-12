from dataclasses import dataclass
from .constants import NAMESPACES as ns
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

@dataclass
class BPItem(ABC):
    id: str
    name: str
    root: ET.Element
    boas_praticas: bool = True
    # namespace: str = "http://www.blueprism.co.uk/product/process"

    # @property
    # def ns(self):
    #     return {"bp": self.namespace}
    
    # def find(self, path: str) -> ET.Element | None:
    #     """Busca um único elemento, aplicando namespace automaticamente"""
    #     return self.root.find(path, self.ns)

    # def find_all(self, path: str) -> list[ET.Element]:
    #     """Busca múltiplos elementos, aplicando namespace automaticamente"""
    #     return self.root.findall(path, self.ns)
    
@dataclass
class BPProcess(BPItem):
    def validar_publicacao(self) -> bool:
        return self.root.get("published", "false").lower() == "true"

@dataclass
class BPObject(BPItem):
    def validar_publicacao_paginas(self) -> bool:
        paginas_nao_publicadas = []
        pages = self.root.findall(".//proc:subsheet", ns)
        for page in pages:
            nome = page.find("proc:name", ns)
            if page.get('published') == "False" and nome.text not in ['Attach', 'Anotações', 'Activate']:
                paginas_nao_publicadas.append(nome.text)
        return paginas_nao_publicadas

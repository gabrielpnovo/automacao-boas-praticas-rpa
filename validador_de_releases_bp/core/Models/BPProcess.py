from dataclasses import dataclass, field
from ..constants import NAMESPACES as ns
from Models import BPItem
import xml.etree.ElementTree as ET

@dataclass
class BPProcess(BPItem):
    paginas_obrigatorias: list[str] = field(default_factory=lambda: ['InicializationParameters', 'Anotações'], init=False)
    
    # verificar se ta None
    def validar_publicacao(self):
        if self.root.get('published') is None:
            self.boas_praticas = False
            self.mas_praticas.append("Processo NÃO está publicado. Revisar!")

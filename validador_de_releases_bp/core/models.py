from dataclasses import dataclass, field
from .constants import NAMESPACES as ns
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
from collections import defaultdict


@dataclass
class BPItem(ABC):
    id: str
    name: str
    root: ET.Element
    boas_praticas: bool = True

    # estrutura de subsheets = subsheetid: {name:str, published:boolean}
    subsheets: dict[str, dict[str, str | bool]] = field(default_factory=dict, init=False)
    # estrutura de stages = stageid: {name:str, type:str, subsheetid:str}
    stages: dict[str, dict[str, str]] = field(default_factory=dict, init=False)
    mas_praticas: list[str] = field(default_factory=list, init=False)
    

    def __post_init__(self):
        self._popular_subsheets()
        self._popular_stages()

    def _popular_subsheets(self):
        for subsheet in self.root.findall(".//proc:subsheet", ns):
            subsheet_id = subsheet.get("subsheetid")
            name_tag = subsheet.find("proc:name", ns)
            if subsheet_id and name_tag is not None and name_tag.text:
                if subsheet.get("published").lower() == "true":
                    published = True
                else:
                    published = False
                self.subsheets[subsheet_id] = {
                    "name": name_tag.text,
                    "published": published
                }

    def _popular_stages(self):
        for stage in self.root.findall(".//proc:stage", ns):
            stage_id = stage.get("stageid")
            name = stage.get("name")
            type = stage.get("type")
            subsheetid_tag = stage.find("proc:subsheetid", ns)
            subsheetid = (
                subsheetid_tag.text.strip() if subsheetid_tag is not None and subsheetid_tag.text else None
            )
            if stage_id and name and type:
                self.stages[stage_id] = {
                    "name": name,
                    "type": type,
                    "subsheetid": subsheetid
                }


    def validar_excecoes_repetidas(self):
        exception_stages = {
            stage_id: info
            for stage_id, info in self.stages.items()
            if info.get("type") == "Exception"
        }

        repetidas = []

        for exception in exception_stages.values():
            
            # verifica se essa exception duplicada já está na lista de repetidas
            if not any(exception.get('name') == d[0] for d in repetidas):
                # busca qtd de repeticoes e verifica se é duplicada:
                qtd_repeticoes = sum(1 for v in exception_stages.values() if v.get('name') == exception.get('name'))

                if qtd_repeticoes > 1:
                    
                    self.boas_praticas = False
                    
                    # separa exceptions:
                    exception_duplicada = {k: v for k, v in exception_stages.items() if v.get('name') == exception.get('name')}

                    # busca nomes das subsheets
                    nomes_paginas = []
                    for exc in exception_duplicada.values():
                        
                        exception_subsheet_name = self.subsheets[exc.get('subsheetid')]['name']
                        nomes_paginas.append(exception_subsheet_name)
                    repetidas.append((exception.get('name'), nomes_paginas))
        
        for excecao, paginas in repetidas:
            paginas_str = ", ".join(paginas)
            self.mas_praticas.append(f"❌ Exceção '{excecao}' se repete nas seguintes páginas: {paginas_str}. Revisar!")
        

    
@dataclass
class BPProcess(BPItem):
    # verificar se ta None
    def validar_publicacao(self) -> bool:
        if self.root.get('published') is None:
            self.boas_praticas = False
            self.mas_praticas.append("❌ Processo NÃO está publicado. Revisar!")
            return False
        return True

@dataclass
class BPObject(BPItem):
    def validar_publicacao_paginas(self) -> bool:
        paginas_nao_publicadas = []
        pages = self.root.findall(".//proc:subsheet", ns)
        for page in pages:
            nome = page.find("proc:name", ns)
            if page.get('published').lower() == "false" and nome.text not in ['Attach', 'Anotações', 'Activate']:
                paginas_nao_publicadas.append(nome.text)
        return paginas_nao_publicadas

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
    data_items: dict[str, dict[str, str]] = field(default_factory=dict, init=False)
    mas_praticas: list[str] = field(default_factory=list, init=False)
    erros: list[str] = field(default_factory=list, init=False)


    def __post_init__(self):
        self.__popular_subsheets()
        self.__popular_stages()
        self.__popular_data_items()

    def __popular_subsheets(self):
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

    def __popular_stages(self):
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

    def __popular_data_items(self):
        for stage in self.root.findall(".//proc:stage", ns):
            if stage.get("type") == "Data":
                stage_id = stage.get("stageid")
                name = stage.get("name")
                data_type = stage.find("proc:datatype", ns)
                subsheetid_tag = stage.find("proc:subsheetid", ns)
                initial_value_tag = stage.find("proc:initialvalue", ns)
                if stage_id and name:
                    self.data_items[stage_id] = {
                        "name": name,
                        "datatype": data_type.text if data_type is not None else None,
                        "subsheetid": subsheetid_tag.text.strip() if subsheetid_tag is not None and subsheetid_tag.text else None,
                        "initialvalue": initial_value_tag.text if initial_value_tag is not None else None                        
                    }

    def __get_subsheet_name_by_id(self, subsheetid: str) -> str:
        return self.subsheets[subsheetid]['name']
        
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
                        exception_subsheet_name = self.__get_subsheet_name_by_id(exc.get('subsheetid'))
                        nomes_paginas.append(exception_subsheet_name)
                    repetidas.append((exception.get('name'), nomes_paginas))
        
        for excecao, paginas in repetidas:
            paginas_str = ", ".join(paginas)
            self.mas_praticas.append(f"❌ Exceção '{excecao}' se repete nas seguintes páginas: {paginas_str}. Revisar!")
        
    def validar_data_item_sem_type(self):
        sem_datatype = {
            stage_id: info
            for stage_id, info in self.data_items.items()
            if info.get("datatype") is None
        }
        for items in sem_datatype.values():
            self.boas_praticas = False
            subsheet_name = self.__get_subsheet_name_by_id(items['subsheetid'])
            self.erros.append(f"❌ Data Item {items['name']} na página {subsheet_name} está sem um tipo atribuído. Revisar!")

    def validar_senhas_expostas(self):
        data_items_expostos = {
            stage_id: info
            for stage_id, info in self.data_items.items()
            if (
                any(palavra in info["name"].lower() for palavra in ["senha", "password", "pass"])
                and info.get("datatype") != "password"
            )
        }
        for items in data_items_expostos.values():
            self.boas_praticas = False
            subsheet_name = self.__get_subsheet_name_by_id(items['subsheetid'])
            self.mas_praticas.append(f"⚠️ Validar se Data Item {items['name']} na página {subsheet_name} não deveria ser do tipo password")
       
@dataclass
class BPProcess(BPItem):
    # verificar se ta None
    def validar_publicacao(self):
        if self.root.get('published') is None:
            self.boas_praticas = False
            self.mas_praticas.append("❌ Processo NÃO está publicado. Revisar!")

@dataclass
class BPObject(BPItem):
    elements: dict[str, dict[str, str]] = field(default_factory=dict, init=False)
    

    def validar_publicacao_paginas(self) -> bool:

        for valor in self.subsheets.values():
            if not valor['published'] and valor['name'] not in ['Attach', 'Anotações', 'Activate']:
                print(f'Página não está publicada: {valor['name']}')
                self.boas_praticas = False
                self.mas_praticas.append(f'❌ Página "{valor['name']}" NÃO está publicada. Revisar!')

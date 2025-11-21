from dataclasses import dataclass, field
from core.constants import NAMESPACES as ns
from .BPItem import BPItem
import xml.etree.ElementTree as ET

@dataclass
class BPObject(BPItem):
    # estrutura de elements = elementid: {
    #       nome_elemento:str, 
    #           atributos: [
    #               {name:str, inuse:bool, value:str},
    #               ...
    #           ]
        # }
    elements: dict[str, dict[str, str | list[dict[str, str]]]] = field(default_factory=dict, init=False)
    paginas_obrigatorias: list[str] = field(default_factory=lambda: ['Attach', 'Activate', 'Anotações'], init=False)
    nomes_elementos: list[str] = field(default_factory=lambda: ['label', 'button', 'window', 'internal frame', 'field', 'combobox', 'radio button'], init=False)

    def __post_init__(self):
        super().__post_init__()
        self.__popular_elementos()

    def __popular_elementos(self):
        for element in self.root.findall(".//proc:element", ns):
            if element.get('name') is not None:
                name = element.get('name')
                id = element.find("proc:id", ns).text
                
                attributes = element.find("proc:attributes", ns)
                if attributes is not None:
                    self.elements[id] = {
                        "name": name
                    }
                    attributes = attributes.findall("proc:attribute", ns)
                    for attribute in attributes:
                        
                        self.elements[id].setdefault("atributes", [])

                        valor_atributo = attribute.find('proc:ProcessValue', ns).get('value')
                        
                        
                        if attribute.get('inuse') is not None:
                            
                            self.elements[id]["atributes"].append({
                                "name": attribute.get("name"),
                                "inuse": True,
                                "value": valor_atributo
                            })
                        else:

                            self.elements[id]["atributes"].append({
                                "name": attribute.get("name"),
                                "inuse": False,
                                "value": valor_atributo
                            })
    
    def validar_atributo_vazio(self):
        for valor in self.elements.values():
            for atributo in valor['atributes']:
                if atributo['inuse'] and (atributo['value'] is None or atributo['value'].strip() == ""):
                    self.boas_praticas = False
                    self.mas_praticas.append(f'Atributo "{atributo["name"]}" do elemento "{valor["name"]}" está em uso, mas vazio. Revisar!')

    def validar_match_index(self):
        for valor in self.elements.values():
            for atributo in valor['atributes']:
                if atributo['name'].lower() == 'matchindex' and atributo['inuse'] == False:
                    self.boas_praticas = False
                    self.mas_praticas.append(f'Atributo "{atributo["name"]}" do elemento "{valor["name"]}" está DESATIVADO. Revisar!')
    
    def validar_uso_region(self):
        for tag in ["region", "region-container"]:
            for region in self.root.findall(f".//proc:{tag}", ns):
                self.boas_praticas = False
                self.mas_praticas.append(f"O elemento '{region.get("name")}' está mapeado em Region, o que é fortemente desaconselhado. Revisar!")
            
    def validar_publicacao_paginas(self):
        for valor in self.subsheets.values():
            if not valor['published'] and valor['name'] not in ['Attach', 'Anotações', 'Activate', 'Detach','Clean Up', 'Anotações']:
                self.boas_praticas = False
                self.mas_praticas.append(f'Página "{valor['name']}" NÃO está publicada. Revisar!')

    def validar_attach_ou_activate_das_pags(self):
        subsheets_attach_activate = {
            subsheet_id: info
            for subsheet_id, info in self.subsheets.items()
            if info.get('name') in ('Attach', 'Activate', 'Activate Application')
        }
        attach_activate_ids = set(subsheets_attach_activate.keys())
        subsheets_normais = {
            subsheet_id: info
            for subsheet_id, info in self.subsheets.items()
            if info.get('name') not in ('Attach', 'Launch', 'Clean Up', 'Anotações')
        }
        for subsheet_id, info in subsheets_normais.items():
            # encontra o stage Start da página atual
            start_stage = None
            stages_da_subsheet = {
                stage_id: info
                for stage_id, info in self.stages.items()
                if info.get('subsheetid') == subsheet_id
            }
            for stage in stages_da_subsheet.values():
                if stage.get('type') == 'Start':
                    start_stage = stage
                    break
            # pega o onsuccess do Start
            onsuccess_stage_id = start_stage.get('onsuccess_stage_id')
            # busca o stage apontado pelo onsuccess
            prox_stage = stages_da_subsheet.get(onsuccess_stage_id)
            if prox_stage is None:
                self.boas_praticas = False
                pagina = info['name']
                continue
            
            # verifica se o stage é um SubSheet e o processid é um attach/activate
            if prox_stage.get('type') != 'SubSheet' and prox_stage.get('processid') not in attach_activate_ids:
                self.boas_praticas = False
                pagina = info['name']
                self.mas_praticas.append(f"A página '{pagina}' não inicia com Attach/Activate")

    def validar_wait_stage_sem_elemento(self):
        for stage_id, info in self.stages.items():
            if info['type'] == "WaitStart":
                stage_xml = self.root.find(f".//proc:stage[@stageid='{stage_id}']", ns)

                if not stage_xml.findall(".//proc:choice", ns):
                    self.boas_praticas = False
                    pagina = self._get_subsheet_name_by_id(info['subsheetid'])
                    self.erros.append(f'Wait Stage "{info["name"]}" na página "{pagina}" não possui nenhum elemento definido para espera. Revisar!')

    def validar_nome_elemento(self):
        for valor in self.elements.values():
            # if not any(elemento in valor['name'] for elemento in self.nomes_elementos):
            if not any(valor['name'].lower().startswith(elemento.lower()) for elemento in self.nomes_elementos):
                self.boas_praticas = False
                self.mas_praticas.append(f'O elemento "{valor["name"]}" possui um nome não convencional. Revisar!')

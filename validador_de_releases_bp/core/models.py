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
            onsuccess_stage_tag = stage.find("proc:onsuccess", ns)
            onsuccess_stage_id = (
                onsuccess_stage_tag.text.strip() if onsuccess_stage_tag is not None and onsuccess_stage_tag.text else None
            )
            processid_tag = stage.find("proc:processid", ns)
            processid = (
                processid_tag.text.strip() if processid_tag is not None and processid_tag.text else None
            )
            if stage_id and name and type:
                self.stages[stage_id] = {
                    "name": name,
                    "type": type,
                    "subsheetid": subsheetid,
                    "onsuccess_stage_id": onsuccess_stage_id,
                    "processid": processid
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

    def _get_subsheet_name_by_id(self, subsheetid: str) -> str:
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
                        exception_subsheet_name = self._get_subsheet_name_by_id(exc.get('subsheetid'))
                        nomes_paginas.append(exception_subsheet_name)
                    repetidas.append((exception.get('name'), nomes_paginas))
        
        for excecao, paginas in repetidas:
            paginas_str = ", ".join(paginas)
            self.mas_praticas.append(f'Exceção "{excecao}" se repete nas seguintes páginas: "{paginas_str}". Revisar!')
        
    def validar_data_item_sem_type(self):
        sem_datatype = {
            stage_id: info
            for stage_id, info in self.data_items.items()
            if info.get("datatype") is None
        }
        for items in sem_datatype.values():
            self.boas_praticas = False
            subsheet_name = self._get_subsheet_name_by_id(items['subsheetid'])
            self.erros.append(f'Data Item "{items['name']}" na página "{subsheet_name}" está sem um tipo atribuído. Revisar!')

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
            subsheet_name = self._get_subsheet_name_by_id(items['subsheetid'])
            self.mas_praticas.append(f'Validar se Data Item "{items['name']}" na página "{subsheet_name}" não deveria ser do tipo password')

    def validar_exception_type(self):
        exception_invalidas = []

        for stage_id, info in self.stages.items():
            # queremos só stages que realmente são Exception
            if info.get("type") == "Exception":

                # pegar o elemento XML original desse stage
                stage_xml = self.root.find(f".//proc:stage[@stageid='{stage_id}']", ns)
                if stage_xml is None:
                    continue

                # busca o tipo de exceção
                exception_tag = stage_xml.find("proc:exception", ns)
                tipo_exception = exception_tag.get("type")

                # tipos válidos:
                tipos_validos = {"Business Exception", "System Exception"}

                if tipo_exception not in tipos_validos:
                    exception_invalidas.append((info["name"], tipo_exception, info["subsheetid"]))

        # registrar erros na lista de mas_praticas:
        for nome, tipo, subsheetid in exception_invalidas:
            self.boas_praticas = False
            pagina = self._get_subsheet_name_by_id(subsheetid)
            self.mas_praticas.append(
                f'Exception "{nome}" na página {pagina} possui tipo inválido: "{tipo}". Ajustar para Business Exception ou System Exception.'
            )
    
    def validar_initial_value_dos_data_items(self):
        # obs: só filtro por subsheet_id not None porque a página Initialise não tem subsheet_id e também porque as variáveis nela terão necessariamente que ter initial value, então não precisam ser considerados
        data_items_com_valor_inicial = {
            stage_id: info
            for stage_id, info in self.data_items.items()
            if info.get("initialvalue") not in (None, "") and info.get("subsheet_id") is not None
        }
        for info in data_items_com_valor_inicial.values():
            self.boas_praticas = False
            pagina = self._get_subsheet_name_by_id(info["subsheetid"])
            self.mas_praticas.append(
                f"Data Item '{info['name']}' na página '{pagina}' possui valor inicial. Validar se isso é realmente necessário."
            )

    def validar_decision_vazia(self):
        for stage_id, info in self.stages.items():
            if info['type'] == "Decision":
                stage_xml = self.root.find(f".//proc:stage[@stageid='{stage_id}']", ns)
                if stage_xml.find("proc:decision", ns).get('expression').strip() == "":
                    self.boas_praticas = False
                    pagina = self._get_subsheet_name_by_id(info['subsheetid'])
                    self.erros.append(f'Decision "{info["name"]}" na página "{pagina}" está sem expressão definida. Revisar!')

    def validar_saida_decision(self):
        for stage_id, info in self.stages.items():
            if info['type'] == "Decision":
                stage_xml = self.root.find(f".//proc:stage[@stageid='{stage_id}']", ns)
                # verifica saída yes
                if stage_xml.find("proc:ontrue", ns) is None:
                    self.boas_praticas = False
                    pagina = self._get_subsheet_name_by_id(info['subsheetid'])
                    self.erros.append(f'Decision "{info["name"]}" na página "{pagina}" não possui saída "Sim" definida. Revisar!')

                # verifica saída no
                if stage_xml.find("proc:onfalse", ns) is None:
                    self.boas_praticas = False
                    pagina = self._get_subsheet_name_by_id(info['subsheetid'])
                    self.erros.append(f'Decision "{info["name"]}" na página "{pagina}" não possui saída "Não" definida. Revisar!')

    def validar_exception_vazia(self):
        for stage_id, info in self.stages.items():
            if info['type'] == "Exception":
                stage_xml = self.root.find(f".//proc:stage[@stageid='{stage_id}']", ns)
                exception_tag = stage_xml.find("proc:exception", ns)

                #verifica exception type vazio
                if exception_tag.get('usecurrent') is None and exception_tag.get('type').strip() == '':
                    self.boas_praticas = False
                    pagina = self._get_subsheet_name_by_id(info['subsheetid'])
                    self.erros.append(f'"Exception Type" da exceção "{info["name"]}" na página "{pagina}" não está definida. Revisar!')

                #verifica exception detail vazia
                if exception_tag.get('usecurrent') is None and exception_tag.get('detail').strip() == '':
                    self.boas_praticas = False
                    pagina = self._get_subsheet_name_by_id(info['subsheetid'])
                    self.erros.append(f'"Exception Detail" da exceção "{info["name"]}" na página "{pagina}" não está definida. Revisar!')

    def validar_existencia_paginas(self):
        for pagina_obrigatoria in self.paginas_obrigatorias:
            if not any(info['name'] == pagina_obrigatoria for info in self.subsheets.values()):
                self.boas_praticas = False
                self.mas_praticas.append(f'Página obrigatória "{pagina_obrigatoria}" não encontrada. Revisar!')
       

@dataclass
class BPProcess(BPItem):
    paginas_obrigatorias: list[str] = field(default_factory=lambda: ['InicializationParameters', 'Anotações'], init=False)
    
    # verificar se ta None
    def validar_publicacao(self):
        if self.root.get('published') is None:
            self.boas_praticas = False
            self.mas_praticas.append("Processo NÃO está publicado. Revisar!")

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
    paginas_obrigatorias: list[str] = field(default_factory=lambda: ['Attach', 'Activate', 'Anotações', 'teste página'], init=False)
    nomes_elementos: list[str] = field(default_factory=lambda: ['label', 'button', 'window', 'internal frame', 'field'], init=False)

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


    


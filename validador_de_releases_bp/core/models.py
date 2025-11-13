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

    # def validar_excecoes_repetidas(self) -> list[tuple[str, list[str]]]:
        """
        Verifica exceções repetidas (stages type='Exception' com o mesmo nome)
        e retorna uma lista de tuplas (nome_excecao, [nomes_de_paginas]).
        """

        print('VALIDANDO EXCEÇÕES REPETIDAS-----------------------------------------------')
        exception_stages = {
            stage_id: info
            for stage_id, info in self.stages.items()
            if info.get("type") == "Exception"
        }
        print(f'EXCEPTION STAGES')
        # Agrupa os stages por nome
        grouped_by_name = defaultdict(list)
        for stage_id, info in exception_stages.items():
            grouped_by_name[info["name"]].append((stage_id, info))
        print('GROUPED BY NAME')
        
        # CORRIGIR ESSA PARTE QUE NÃO FUNCIONA:
        # Monta a lista de exceções repetidas com os nomes das subsheets
        # resultado = []
        # for name, infos in grouped_by_name.items():
        #     if len(infos) > 1:
        #         nomes_paginas = []
        #         for info in infos:
        #             subsheetid = info.get("subsheetid")
        #             if subsheetid and subsheetid in self.subsheets:
        #                 nome_pagina = self.subsheets[subsheetid]["name"]
        #                 nomes_paginas.append(nome_pagina)
        #         resultado.append((name, nomes_paginas))

        # return resultado
        return














        # # Busca todas as exceções no XML
        # stages = self.root.findall(".//proc:stage[@type='Exception']", ns)

        # excecoes_por_nome: dict[str, list[str]] = {}

        # for stage in stages:
        #     nome_excecao = stage.get("name")
        #     subsheetid_tag = stage.find("proc:subsheetid", ns)
        #     if not (nome_excecao and subsheetid_tag is not None):
        #         continue

        #     subsheetid = subsheetid_tag.text.strip()
        #     excecoes_por_nome.setdefault(nome_excecao, []).append(subsheetid)

        # # Identifica exceções repetidas
        # repetidas = {
        #     nome: ids for nome, ids in excecoes_por_nome.items() if len(ids) > 1
        # }

        # resultado = []
        # for nome_excecao, subsheet_ids in repetidas.items():
        #     paginas = []
        #     for sid in subsheet_ids:
        #         # Busca a subsheet correspondente
        #         subsheet = self.root.find(f".//proc:subsheet[@subsheetid='{sid}']", ns)
        #         if subsheet is not None:
        #             nome_pagina_tag = subsheet.find("proc:name", ns)
        #             if nome_pagina_tag is not None and nome_pagina_tag.text:
        #                 paginas.append(nome_pagina_tag.text)
        #     resultado.append((nome_excecao, paginas))

        # return resultado

    
@dataclass
class BPProcess(BPItem):
    # verificar se ta None
    def validar_publicacao(self) -> bool:
        if self.root.get('published') is None:
            self.boas_praticas = False
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

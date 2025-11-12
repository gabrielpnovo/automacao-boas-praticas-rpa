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

    def validar_excecoes_repetidas(self) -> list[tuple[str, list[str]]]:
        """
        Verifica exceções repetidas (stages type='Exception' com o mesmo nome)
        e retorna uma lista de tuplas (nome_excecao, [nomes_de_paginas]).
        """
        # Busca todas as exceções no XML
        stages = self.root.findall(".//proc:stage[@type='Exception']", ns)

        excecoes_por_nome: dict[str, list[str]] = {}

        for stage in stages:
            nome_excecao = stage.get("name")
            subsheetid_tag = stage.find("proc:subsheetid", ns)
            if not (nome_excecao and subsheetid_tag is not None):
                continue

            subsheetid = subsheetid_tag.text.strip()
            excecoes_por_nome.setdefault(nome_excecao, []).append(subsheetid)

        # Identifica exceções repetidas
        repetidas = {
            nome: ids for nome, ids in excecoes_por_nome.items() if len(ids) > 1
        }

        resultado = []
        for nome_excecao, subsheet_ids in repetidas.items():
            paginas = []
            for sid in subsheet_ids:
                # Busca a subsheet correspondente
                subsheet = self.root.find(f".//proc:subsheet[@subsheetid='{sid}']", ns)
                if subsheet is not None:
                    nome_pagina_tag = subsheet.find("proc:name", ns)
                    if nome_pagina_tag is not None and nome_pagina_tag.text:
                        paginas.append(nome_pagina_tag.text)
            resultado.append((nome_excecao, paginas))

        return resultado

    
@dataclass
class BPProcess(BPItem):
    def validar_publicacao(self) -> bool:
        if self.root.get('published').lower() == "false":
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

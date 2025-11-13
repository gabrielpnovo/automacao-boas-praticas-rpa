import streamlit as st
from core.xml_utils import limpa_arquivo, get_root_xml
from core.blueprism_parser import extrai_processos_e_objetos
from ui.layout import cabecalho, exibir_resultados
from core.models import BPProcess, BPObject

st.set_page_config(page_title="Validador Blue Prism", layout="wide")
cabecalho()

uploaded_file = st.file_uploader("Envie seu arquivo .bprelease", type=["bprelease"])

if uploaded_file:
    # Fase 1 - Leitura e limpeza do XML ---
    raw = uploaded_file.read()
    xml_text = limpa_arquivo(raw)
    root_completa= get_root_xml(xml_text)

    # Fase 2 - Extração de processos e objetos ---
    processos, objetos = extrai_processos_e_objetos(root_completa)

    # Fase 3 - 
    st.markdown("<h2 style='color:teal;'>🔍 Validações de Boas Práticas</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:teal;'>===== Processos =====</h3>", unsafe_allow_html=True)
    if processos:
        
        for processo in processos:
            print(f'--------------- INICIO PROCESSO {processo.name} ')
            st.markdown(f"<h4 style='color:teal;'>{processo.name}</h4>", unsafe_allow_html=True)

            processo.validar_publicacao()
            processo.validar_excecoes_repetidas()

            if len(processo.mas_praticas)>0:
                for alerta in processo.mas_praticas:
                    st.error(alerta)

            if processo.boas_praticas:
                st.success("✅ Processo dentro das boas práticas")
    else:
        print("Nenhum processo encontrado com o ID informado.")

    st.markdown("<h3 style='color:teal;'>===== Objetos =====</h3>", unsafe_allow_html=True)
    if objetos:
        for objeto in objetos:
            print(f'--------------- INICIO OBJETO {objeto.name} ')
            st.markdown(f"<h4 style='color:teal;'>{objeto.name}</h4>", unsafe_allow_html=True)
            paginas_nao_publicadas = objeto.validar_publicacao_paginas()
            # objeto.validar_publicacao_paginas()
            objeto.validar_excecoes_repetidas()
            if paginas_nao_publicadas:
                objeto.boas_praticas = False
                for pagina in paginas_nao_publicadas:
                    st.error(f"❌ Ação '{pagina}' NÃO está publicada. Revisar!")
            
            excecoes_repetidas = objeto.validar_excecoes_repetidas()
            if excecoes_repetidas:
                objeto.boas_praticas = False
                for excecao, paginas in excecoes_repetidas:
                    paginas_str = ", ".join(paginas)
                    st.error(f"❌ Exceção '{excecao}' se repete nas seguintes páginas: {paginas_str}. Revisar!")

            if len(objeto.mas_praticas)>0:
                for alerta in objeto.mas_praticas:
                    st.error(alerta)

            if objeto.boas_praticas:
                st.success("✅ Objeto dentro das boas práticas")     

    # --- Exibição no Streamlit ---
    # exibir_resultados(processos, objetos)

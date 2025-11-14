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
    processos: list[BPProcess]
    objetos:list[BPObject]
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
            processo.validar_data_item_sem_type()
            processo.validar_senhas_expostas()

            if len(processo.mas_praticas)>0:
                for alerta in processo.mas_praticas:
                    st.error(alerta)

            if len(processo.erros)>0:
                for erro in processo.erros:
                    st.error(alerta)

            if processo.boas_praticas:
                st.success("✅ Processo dentro das boas práticas")
    else:
        print("Nenhum processo encontrado com o ID informado.")

    st.markdown("<h3 style='color:teal;'>===== Objetos =====</h3>", unsafe_allow_html=True)
    if objetos:
        for objeto in objetos:
            print('============================================================ NOVA EXECUCAO ============================================================')
            print(f'--------------- INICIO OBJETO {objeto.name} ')
            st.markdown(f"<h4 style='color:teal;'>{objeto.name}</h4>", unsafe_allow_html=True)

            # if objeto.name == 'BankManager_Basic_Edge':
            #     pass
            objeto.verificar_match_index()
            # objeto.verificar_atributo_vazio()
            # objeto.validar_publicacao_paginas()
            # objeto.validar_excecoes_repetidas()
            # objeto.validar_data_item_sem_type()
            # objeto.validar_senhas_expostas()

            if len(objeto.mas_praticas)>0:
                for alerta in objeto.mas_praticas:
                    st.error(alerta)

            if len(processo.erros)>0:
                for erro in processo.erros:
                    st.error(alerta)

            if objeto.boas_praticas:
                st.success("✅ Objeto dentro das boas práticas")     

    # --- Exibição no Streamlit ---
    # exibir_resultados(processos, objetos)

import streamlit as st
from core.xml_utils import limpa_arquivo, get_root_xml
from core.blueprism_parser import extrai_processos_e_objetos
from ui.layout import cabecalho, exibir_resultados

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
    # st.subheader("🔍 Validações boas práticas:")
    st.markdown("<h2 style='color:teal;'>🔍 Validações de Boas Práticas</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:teal;'>===== Processos =====</h3>", unsafe_allow_html=True)
    if processos:
        for processo in processos:
            st.markdown(f"<h4 style='color:teal;'>{processo.name}</h4>", unsafe_allow_html=True)
            if not processo.validar_publicacao():      
                st.error(f"❌ Processo NÃO está publicado. Revisar!")
                
    else:
        print("Nenhum processo encontrado com o ID informado.")

    st.markdown("<h3 style='color:teal;'>===== Objetos =====</h3>", unsafe_allow_html=True)
    if objetos:
        for objeto in objetos:
            objeto.validar_publicacao_paginas()

    # --- Exibição no Streamlit ---
    # exibir_resultados(processos, objetos)

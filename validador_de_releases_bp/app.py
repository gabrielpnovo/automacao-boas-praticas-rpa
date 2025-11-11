import streamlit as st
from core.xml_utils import limpa_arquivo, carrega_xml
from core.blueprism_parser import extrai_processos_e_objetos

st.set_page_config(page_title="Validação Blue Prism", layout="wide")
st.subheader("Ferramenta de validação de releases Blue Prism")

uploaded_file = st.file_uploader("Envie seu arquivo .bprelease", type=["bprelease"])

if uploaded_file:
    raw_content = uploaded_file.read()
    cleaned = limpa_arquivo(raw_content)
    try:
        root = carrega_xml(cleaned)
        processos, objetos = extrai_processos_e_objetos(root)

        if processos:
            st.subheader("📘 Processos encontrados")
            st.dataframe(processos)
        else:
            st.info("Nenhum processo encontrado.")

        if objetos:
            st.subheader("📗 Objetos encontrados")
            st.dataframe(objetos)
        else:
            st.info("Nenhum objeto encontrado.")
    except Exception as e:
        st.error(f"Erro ao processar XML: {e}")

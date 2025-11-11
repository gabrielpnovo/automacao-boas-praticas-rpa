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
    st.subheader("🔍 Validação de Publicação:")
    if processos:
        for processo in processos:
            is_published = processo.root.get("published", "false").lower() == "true"
            if is_published:
                st.success(f"✅ [{processo.name}] - Processo está publicado.")
            else:
                st.error(f"❌ [{processo.name}] - Processo NÃO está publicado. Revisar!")
    else:
        print("Nenhum processo encontrado com o ID informado.")


    if objetos:
        for objeto in objetos:
            is_published = objeto.root.get("published", "false").lower() == "true"
            if is_published:    
                st.success(f"✅ [{objeto.name}] - Objeto está publicado.")
            else:
                st.error(f"❌ [{objeto.name}] - Objeto NÃO está publicado. Revisar!")   

    # --- Exibição no Streamlit ---
    # exibir_resultados(processos, objetos)

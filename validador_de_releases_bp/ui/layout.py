import streamlit as st
from ui.components import mostrar_alerta

def cabecalho():
    st.title("🔎 Ferramenta de Validação de Releases Blue Prism")
    st.caption("Analisa arquivos `.bprelease` e identifica inconsistências em processos e objetos.")
    st.divider()

def exibir_resultados(processos, objetos):
    st.subheader("📘 Processos Encontrados")
    if processos:
        st.dataframe(processos)
    else:
        mostrar_alerta("Nenhum processo encontrado.", tipo="info")

    st.subheader("📗 Objetos Encontrados")
    if objetos:
        st.dataframe(objetos)
    else:
        mostrar_alerta("Nenhum objeto encontrado.", tipo="info")

    st.divider()
    st.write("✅ Análise concluída.")

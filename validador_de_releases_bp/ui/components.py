import streamlit as st

def mostrar_alerta(mensagem, tipo="info"):
    """Exibe alertas padronizados."""
    if tipo == "erro":
        st.error(mensagem)
    elif tipo == "aviso":
        st.warning(mensagem)
    elif tipo == "sucesso":
        st.success(mensagem)
    else:
        st.info(mensagem)

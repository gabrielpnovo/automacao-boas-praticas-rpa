import streamlit as st
import re
import xml.etree.ElementTree as ET
import io

# -------------------------
# Função de limpeza do XML
# -------------------------
def limpa_arquivo(raw_data: bytes) -> str:
    """Limpa caracteres ilegais e entidades inválidas de um XML e retorna o texto limpo."""
    try:
        # Decodifica ignorando erros de UTF-8
        text = raw_data.decode("utf-8", errors="ignore")

        # Remove caracteres ilegais do XML 1.0
        illegal_xml_chars_re = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
        cleaned_text = illegal_xml_chars_re.sub("", text)

        # Remove entidades numéricas inválidas (ex: &#x1F;)
        cleaned_text = re.sub(r"&#x[0-9A-Fa-f]+;", "", cleaned_text)

        return cleaned_text

    except Exception as e:
        st.error(f"Erro ao limpar o arquivo: {e}")
        return ""


# -------------------------
# Aplicação principal
# -------------------------
st.subheader("Ferramenta de validação de releases Blue Prism")
uploaded_file = st.file_uploader("Envie seu arquivo .bprelease", type=["bprelease"])

if uploaded_file:
    st.write(f"Processando arquivo: {uploaded_file.name}")

    try:
        # 1️⃣ Lê o conteúdo e faz a limpeza
        raw_content = uploaded_file.read()
        cleaned_content = limpa_arquivo(raw_content)

        # 2️⃣ Faz o parse do XML já limpo
        tree = ET.ElementTree(ET.fromstring(cleaned_content))
        root = tree.getroot()

        # --- Namespaces usados no arquivo ---
        ns = {
            'bpr': 'http://www.blueprism.co.uk/product/release',
            'proc': 'http://www.blueprism.co.uk/product/process',
            'procgrp': 'http://www.blueprism.co.uk/product/process-group',
            'obj': 'http://www.blueprism.co.uk/product/object',
            'objgrp': 'http://www.blueprism.co.uk/product/object-group'
        }

        processos = []
        objetos = []

        # --- 1. Buscar grupos ---
        process_groups = root.findall(".//procgrp:process-group", ns)
        object_groups = root.findall(".//objgrp:object-group", ns)

        process_ids = []
        object_ids = []

        # --- 2. Coletar IDs dos grupos de processo ---
        for group in process_groups:
            for member in group.findall(".//procgrp:members/procgrp:process", ns):
                pid = member.get("id")
                if pid:
                    process_ids.append(pid)

        # --- 3. Coletar IDs dos grupos de objetos ---
        for group in object_groups:
            for member in group.findall(".//objgrp:members/objgrp:object", ns):
                oid = member.get("id")
                if oid:
                    object_ids.append(oid)

        # --- 4. Procurar as tags <process> e <object> com esses IDs ---
        for pid in process_ids:
            proc = root.find(f".//proc:process[@id='{pid}']", ns)
            if proc is not None and proc.get("name"):
                processos.append({"id": pid, "name": proc.get("name")})

        for oid in object_ids:
            obj = (
                root.find(f".//obj:object[@id='{oid}']", ns)
                or root.find(f".//proc:object[@id='{oid}']", ns)
            )
            if obj is not None and obj.get("name"):
                objetos.append({"id": oid, "name": obj.get("name")})

        # --- 5. Exibir resultados ---
        if processos:
            st.subheader("📘 Processos encontrados")
            st.dataframe(processos)
        else:
            st.info("Nenhum processo encontrado ou sem ID correspondente.")

        if objetos:
            st.subheader("📗 Objetos encontrados")
            st.dataframe(objetos)
        else:
            st.info("Nenhum objeto encontrado ou sem ID correspondente.")

    except ET.ParseError as e:
        st.error(f"Erro ao ler XML: {e}")

    finally:
        st.write("Finalizado o processamento do arquivo.")

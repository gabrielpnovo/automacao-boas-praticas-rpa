import streamlit as st
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd
import io

st.set_page_config(page_title="Validador Releases #Blue Prism", layout="centered")
st.title("🤖Agente IA: 🔷 Validador Releases #Blue Prism | Validações Estruturais")

uploaded_file = st.file_uploader("Envie seu arquivo .bpprocess, .bpobject, .bprelease ou .txt", type=["bpprocess", "bpobject", "bprelease", "xml", "txt"])

if uploaded_file:
    file_name = uploaded_file.name
    file_extension = file_name.split(".")[-1].lower()

    processos = []
    objetos = []
    erros_carregamento = []

    try:
        if file_extension == "bprelease":
            with zipfile.ZipFile(uploaded_file) as z:
                for file_info in z.infolist():
                    if file_info.filename.endswith(".bpprocess") or file_info.filename.endswith(".bpobject"):
                        with z.open(file_info) as internal_file:
                            try:
                                content = internal_file.read()
                                tree = ET.ElementTree(ET.fromstring(content))
                                root = tree.getroot()
                                if root.tag == "process":
                                    processos.append((file_info.filename, root))
                                elif root.tag == "businessobject":
                                    objetos.append((file_info.filename, root))
                            except ET.ParseError:
                                erros_carregamento.append(f"Erro ao ler {file_info.filename}. XML inválido.")
        else:
            content = uploaded_file.read()
            tree = ET.ElementTree(ET.fromstring(content))
            root = tree.getroot()
            if root.tag == "process":
                processos.append((file_name, root))
            elif root.tag == "businessobject":
                objetos.append((file_name, root))
            else:
                erros_carregamento.append("O arquivo enviado não é um processo ou objeto reconhecido.")

        # Mostrar arquivos carregados
        st.subheader("🗂️ Arquivos Carregados:")
        if processos:
            st.success(f"✅ {len(processos)} processo(s) carregado(s).")
            for p in processos:
                st.write(f"- {p[0]}")
        if objetos:
            st.success(f"✅ {len(objetos)} objeto(s) carregado(s).")
            for o in objetos:
                st.write(f"- {o[0]}")

        # Fase 2 - Validação baseada no atributo do <process>
        st.subheader("🔍 Validação de Publicação:")

        for file_name, root in processos:
            print(f'root: {root}')
            is_published = root.get("published", "false").lower() == "true"
            if is_published:
                st.success(f"✅ [{file_name}] - Processo está publicado.")
            else:
                st.error(f"❌ [{file_name}] - Processo NÃO está publicado. Revisar!")

        # Fase 3 - Validações Estruturais
        st.subheader("🔎 Fase 3: Validações de Estrutura de Processo")

        def validar_estrutura(arquivo, root):
            atencao = []
            erros = []
            erros_registrados = set()

            # validar subsheets publicados
            for subsheet in root.findall("subsheet"):
                name = subsheet.find("name")
                name = name.text
                if subsheet.get('published') == 'False':
                    erro = f'subsheet "{name}" não está publicado.'
                    erros.append(erro)
                    erros_registrados.add(erro)

            for stage in root.iter("stage"):
                tipo = stage.get("type", "").lower()
                nome = stage.get("name", "")

                # Decision com expressão vazia
                if tipo == "decision":
                    for decision in stage.iter("decision"):
                        if decision.get("expression", "").strip() == "":
                            erro = f"[{arquivo}] ⚠️ Decision '{nome}' com expressão vazia."
                            if erro not in erros_registrados:
                                erros.append(erro)
                                erros_registrados.add(erro)

                # Calculation com expressão mas sem destino
                if tipo == "calculation":
                    for calc in stage.iter("calculation"):
                        if calc.get("expression") and calc.get("stage", "").strip() == "":
                            erro = f"[{arquivo}] ⚠️ Calculation '{nome}' sem estágio de destino definido."
                            if erro not in erros_registrados:
                                erros.append(erro)
                                erros_registrados.add(erro)

                # Action sem objeto ou ação
                if tipo == "action":
                    for action in stage.iter("resource"):
                        if action.get("object", "") == "" or action.get("action", "") == "":
                            erro = f"[{arquivo}] ⚠️ Action '{nome}' sem objeto ou ação definida."
                            if erro not in erros_registrados:
                                erros.append(erro)
                                erros_registrados.add(erro)

            # Data items com tipo 'unknown'
            for item in root.iter("datatype"):
                if item.text and item.text.strip().lower() == "unknown":
                    erro = f"[{arquivo}] ⚠️ Há Data Item com tipo 'unknown'."
                    if erro not in erros_registrados:
                        atencao.append(erro)
                        erros_registrados.add(erro)

            return erros, atencao

        todos_erros = []
        total_erros = 0

        for nome_arquivo, xml_root in processos:
            st.subheader(f'Processo: {nome_arquivo}')
            erros_encontrados, atencao = validar_estrutura(nome_arquivo, xml_root)
            total_erros += len(erros_encontrados)
            if erros_encontrados:
                st.subheader("Erros:")
                for erro in erros_encontrados:
                    st.error(f'❌ {erro}')
                    todos_erros.append(erro)
            if atencao:
                st.subheader("Pontos de Atenção:")
                for aviso in atencao:
                    st.warning(f'⚠️ {aviso}')
            else:
                st.success(f"✅ [{nome_arquivo}] - Nenhum erro estrutural encontrado.")

        for nome_arquivo, xml_root in objetos:
            st.subheader(f'Objeto: {nome_arquivo}')

            erros_encontrados = validar_estrutura(nome_arquivo, xml_root)
            total_erros += len(erros_encontrados)
            if erros_encontrados:
                for erro in erros_encontrados:
                    st.error(erro)
                    todos_erros.append(erro)
            if atencao:
                st.subheader("Pontos de Atenção:")
                for aviso in atencao:
                    st.warning(aviso)
            else:
                st.success(f"✅ [{nome_arquivo}] - Nenhum erro estrutural encontrado.")

        if total_erros > 0:
            st.warning(f"⚠️ Total de {total_erros} problema(s) de estrutura encontrado(s).")

            # Exportar para CSV
            st.subheader("📄 Gerar Relatório CSV de Erros")
            df_erros = pd.DataFrame({"Erros Encontrados": todos_erros})
            csv_buffer = io.StringIO()
            df_erros.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Baixar Relatório de Erros (CSV)",
                data=csv_buffer.getvalue(),
                file_name="relatorio_erros_motor_validacao.csv",
                mime="text/csv"
            )

        if erros_carregamento:
            st.subheader("❌ Problemas durante o carregamento:")
            for erro in erros_carregamento:
                st.error(erro)

    except Exception as e:
        st.error(f"❌ Erro geral ao processar o arquivo: {str(e)}")

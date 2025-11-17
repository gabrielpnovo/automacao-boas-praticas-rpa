import pandas as pd
from io import BytesIO
import streamlit as st

# -------------------------------------------------------
# Função principal: cria o Excel consolidado
# -------------------------------------------------------
def gerar_relatorio_excel(itens_blueprism):
    """
    itens_blueprism = lista contendo instâncias de BluePrismProcesso e BluePrismObjeto
    """

    linhas = []

    for item in itens_blueprism:
        for erro in item.erros:
            linhas.append({
                "Nome": item.name,
                "Tipo": "Processo" if item.__class__.__name__ == "BPProcess" else "Objeto",
                "Tipo de Validação": "Erro",
                "Descrição": erro
            })

        for mp in item.mas_praticas:
            linhas.append({
                "Nome": item.name,
                "Tipo": "Processo" if item.__class__.__name__ == "BPProcess" else "Objeto",
                "Tipo de Validação": "Má prática",
                "Descrição": mp
            })

    df = pd.DataFrame(linhas)

    # Gerar Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")

    return output.getvalue()

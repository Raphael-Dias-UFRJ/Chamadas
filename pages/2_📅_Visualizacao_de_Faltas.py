import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(layout="wide")
st.title("📅 Visualização de Faltas por Turma e Datas")

CLASS_NAMES = [
    "6C", "7A", "7B", "7C", "7D",
    "7E", "1 GAST A", "1 ENF A", "2A", "2B"
]

conn = st.connection("gsheets", type=GSheetsConnection)

# -------- Seleções --------
turma_sel = st.selectbox("🏫 Selecione a turma", CLASS_NAMES)

df = conn.read(worksheet=turma_sel)
df = df[df['ativo'].str.lower() != 'n']
df.columns = [c.strip().lower() for c in df.columns]

# Colunas de datas (a partir da 5ª coluna)
date_cols = list(df.columns[4:])

if not date_cols:
    st.info("Ainda não há registros de chamadas para esta turma.")
    st.stop()

datas_sel = st.multiselect(
    "📅 Selecione a(s) data(s) da chamada",
    options=date_cols
)

# -------- Processamento --------
rows = []

if datas_sel:
    for _, row in df.iterrows():
        faltou_em_alguma = False
        dias_faltados = []

        for col in datas_sel:
            ocorrencias = str(row[col]).split(";")
            if "f" in ocorrencias:
                faltou_em_alguma = True
                dias_faltados.append(col)

        if faltou_em_alguma:
            rows.append({
                "Aluno": row["nome"],
                "Turma": turma_sel,
                "Dias com falta": ", ".join(dias_faltados)
            })

    df_result = pd.DataFrame(rows)

    st.subheader("📋 Alunos que faltaram nas datas selecionadas")
    st.dataframe(df_result, use_container_width=True)

else:
    st.info("Selecione pelo menos uma data para visualizar as faltas.")

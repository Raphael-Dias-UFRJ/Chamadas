import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Gráficos Bimestrais de Frequência e Ocorrências")

CLASS_NAMES = [
    "6C", "7A", "7B", "7C", "7D",
    "7E", "1 GAST A", "1 ENF A", "2A", "2B"
]

BIMESTRES = ["1Bi", "2Bi", "3Bi", "4Bi"]

OCCURRENCE_CODES = {
    "Falta": "f",
    "Rendimento": "ok",
    "Celular": "cel",
    "Conversa": "con",
    "Agressividade": "ag",
    "Dormindo": "dorm"
}

conn = st.connection("gsheets", type=GSheetsConnection)

bimestre_sel = st.selectbox("📚 Selecione o bimestre", BIMESTRES)

# -------- Funções auxiliares --------
def calcular_percentuais_por_turma(turma, df):
    total_aulas = 0
    contagem = {k: 0 for k in OCCURRENCE_CODES}

    for col in df.columns[4:]:
        total_aulas += 1
        for _, row in df.iterrows():
            ocorrencias = str(row[col]).split(";")
            for nome, cod in OCCURRENCE_CODES.items():
                if cod in ocorrencias:
                    contagem[nome] += 1

    total_registros = len(df) * total_aulas

    percentuais = {
        k: (v / total_registros) * 100 if total_registros > 0 else 0
        for k, v in contagem.items()
    }

    return percentuais

# -------- Processamento geral --------
dados_graficos = []

for turma in CLASS_NAMES:
    df = conn.read(worksheet=turma)
    df = df[df['ativo'].str.lower() != 'n']
    df.columns = [c.strip().lower() for c in df.columns]

    percentuais = calcular_percentuais_por_turma(turma, df)

    dados_graficos.append({
        "Turma": turma,
        **percentuais
    })

df_graficos = pd.DataFrame(dados_graficos)

# -------- Gráfico 1 - % de faltas por turma --------
st.subheader("📉 Percentual de Faltas por Turma")
st.bar_chart(df_graficos.set_index("Turma")["Falta"])

# -------- Gráfico 2 - % de agressividade por turma --------
st.subheader("🚨 Percentual de Registros de Agressividade por Turma")
st.bar_chart(df_graficos.set_index("Turma")["Agressividade"])

# -------- Gráfico 3 - Comparativo geral de ocorrências --------
st.subheader("📌 Comparativo Geral de Ocorrências por Turma")
st.bar_chart(df_graficos.set_index("Turma")[["Celular", "Conversa", "Dormindo"]])

# -------- Tabela resumo --------
st.subheader("📋 Tabela Resumo de Percentuais por Turma")
st.dataframe(df_graficos, use_container_width=True)

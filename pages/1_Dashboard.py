import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Dashboard de Frequência e Ocorrências")

OCC_CODES = {
    "f": "Faltas",
    "cel": "Celular",
    "con": "Conversa",
    "ag": "Agressividade",
    "dorm": "Dormindo",
    "ok": "Rendimento",
    "circ": "Circulação"

}

CLASS_NAMES = [
    "6C", "7A", "7B", "7C", "7D",
    "7E", "1 GAST A", "1 ENF A", "2A", "2B"
]

BIMESTER_SHEET = "Aulas_Bimestre"  # nome da aba com: Turma | 1Bi | 2Bi | 3Bi | 4Bi

conn = st.connection("gsheets", type=GSheetsConnection)

# --------- Funções utilitárias ---------

def count_occurrences(df):
    counts = {}
    for col in df.columns[4:]:  # colunas de datas
        for cell in df[col].dropna():
            for code in str(cell).split(";"):
                if code:
                    counts[code] = counts.get(code, 0) + 1
    return counts


def count_by_student(df):
    student_stats = {}

    for _, row in df.iterrows():
        name = row["nome"]
        student_stats[name] = {"f": 0, "cel": 0, "con": 0, "ag": 0, "dorm": 0, "ok": 0, "circ": 0}

        for col in df.columns[4:]:
            cell = str(row[col])
            for code in cell.split(";"):
                if code in student_stats[name]:
                    student_stats[name][code] += 1

    return student_stats


# --------- Consolidação geral ---------

all_students = []
all_stats = []

for turma in CLASS_NAMES:
    df = conn.read(worksheet=turma)
    df = df[df['ativo'].str.lower() != 'n']
    df.columns = [c.strip().lower() for c in df.columns]

    stats = count_by_student(df)

    for aluno, dados in stats.items():
        row = {"Turma": turma, "Aluno": aluno}
        row.update(dados)
        all_stats.append(row)

df_stats = pd.DataFrame(all_stats)

# --------- PAINEL CRÍTICO ---------

st.subheader("🚨 Painel Crítico – Top 5")

cols = st.columns(5)

for col, (code, label) in zip(cols, OCC_CODES.items()):
    top5 = (
        df_stats.sort_values(by=code, ascending=False)
        .head(5)[["Aluno", "Turma", code]]
        .rename(columns={code: label})
    )
    col.markdown(f"**Top 5 – {label}**")
    col.dataframe(top5, hide_index=True, use_container_width=True)

st.subheader("⚠️ Alunos com mais de 25% de faltas no bimestre (demanda recomposição)")

bimestre_alerta = st.selectbox(
    "Selecione o bimestre para o alerta",
    ["1bi", "2bi", "3bi", "4bi"],
    key="bimestre_alerta_25"
)

df_bi = conn.read(worksheet=BIMESTER_SHEET)
df_bi.columns = [c.strip().lower() for c in df_bi.columns]

alert_rows = []

for turma in CLASS_NAMES:
    df = conn.read(worksheet=turma)
    df = df[df['ativo'].str.lower() != 'n']
    df.columns = [c.strip().lower() for c in df.columns]

    date_cols = df.columns[4:]
    aulas_previstas = int(df_bi[df_bi["turma"] == turma][bimestre_alerta].values[0])

    for _, row in df.iterrows():
        nome = row["nome"]

        faltas = 0
        for col in date_cols:
            if "f" in str(row[col]).split(";"):
                faltas += 1

        perc_faltas_proj = round((faltas / aulas_previstas) * 100, 2) if aulas_previstas > 0 else 0

        if perc_faltas_proj > 25:
            alert_rows.append({
                "Aluno": nome,
                "Turma": turma,
                "% faltas no bimestre (projetado)": perc_faltas_proj
            })

df_alerta_25 = pd.DataFrame(alert_rows)

st.dataframe(df_alerta_25, use_container_width=True)


# --------- TABELA DE FALTAS POR ALUNO E BIMESTRE ---------

st.subheader("📚 Faltas e Ocorrências por Aluno (Real x Projetado no Bimestre)")

turma_sel = st.selectbox("Selecione a turma", CLASS_NAMES, key="turma_faltas_aluno")
bimestre = st.selectbox("Selecione o bimestre", ["1bi", "2bi", "3bi", "4bi"], key="bimestre_faltas_aluno")

df_bi = conn.read(worksheet=BIMESTER_SHEET)
df_bi.columns = [c.strip().lower() for c in df_bi.columns]

df = conn.read(worksheet=turma_sel)
df = df[df['ativo'].str.lower() != 'n']
df.columns = [c.strip().lower() for c in df.columns]

date_cols = df.columns[4:]
aulas_ministradas = len(date_cols)
aulas_previstas = int(df_bi[df_bi["turma"] == turma_sel][bimestre].values[0])

rows = []

for _, row in df.iterrows():
    nome = row["nome"]

    faltas = 0
    presencas = 0

    occ_count = {"ok": 0, "cel": 0, "con": 0, "ag": 0, "dorm": 0}

    for col in date_cols:
        ocorrencias = str(row[col]).split(";")

        if "f" in ocorrencias:
            faltas += 1
        else:
            presencas += 1
            for k in occ_count.keys():
                if k in ocorrencias:
                    occ_count[k] += 1

    perc_real = round((faltas / aulas_ministradas) * 100, 2) if aulas_ministradas > 0 else 0
    perc_proj = round((faltas / aulas_previstas) * 100, 2) if aulas_previstas > 0 else 0

    occ_perc = {
        "% rendimento (ok)": round((occ_count["ok"] / presencas) * 100, 2) if presencas > 0 else 0,
        "% celular": round((occ_count["cel"] / presencas) * 100, 2) if presencas > 0 else 0,
        "% conversa": round((occ_count["con"] / presencas) * 100, 2) if presencas > 0 else 0,
        "% agressividade": round((occ_count["ag"] / presencas) * 100, 2) if presencas > 0 else 0,
        "% dormindo": round((occ_count["dorm"] / presencas) * 100, 2) if presencas > 0 else 0,
    }

    rows.append({
        "Aluno": nome,
        "Faltas registradas": faltas,
        "% faltas (aulas já dadas)": perc_real,
        "% faltas (projeção bimestre)": perc_proj,
        **occ_perc
    })

df_faltas_aluno = pd.DataFrame(rows)

st.dataframe(df_faltas_aluno, use_container_width=True)

# --------- INSIGHTS ---------

st.info("""
🔎 **Como usar este painel:**
- Turmas com % de faltas projetadas altas podem precisar de intervenção pedagógica.
- Alunos recorrentes nos Top 5 indicam necessidade de acompanhamento individual.
- Comparar % real vs % projetada ajuda a antecipar problemas de evasão e desengajamento.
""")

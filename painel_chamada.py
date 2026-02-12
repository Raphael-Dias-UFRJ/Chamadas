import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import date

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
st.title("📋 Sistema de Chamada e Ocorrências")

OCCURRENCES = {
    "Falta": "f",
    "Presença": "p",
    "Rendimento": "ok",
    "Celular": "cel",
    "Conversa": "con",
    "Agressividade": "ag",
    "Dormindo": "dorm",
    "Circulacao": "circ"
}

# Nome das turmas disponíveis == Nomes das abas na planilha
CLASS_NAMES = [
    "6C", "7A", "7B", "7C", "7D",
    "7E", "1 GAST A", "1 ENF A", "2A", "2B"
]

# ------------- CONEXÃO ------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# ------------- SELEÇÕES -----------------
call_date = st.date_input("📅 Data da chamada", date.today())
class_name = st.selectbox("🏫 Turma", CLASS_NAMES)

num_aulas = st.number_input(
    "📚 Quantidade de aulas neste dia",
    min_value=1,
    max_value=6,
    value=1,
    step=1
)

# ------------- LEITURA DA ABA -----------
df = conn.read(worksheet=class_name)
df.columns = [c.strip().lower() for c in df.columns]

# Filtra apenas alunos ativos
df = df[df['ativo'].str.lower() != 'n']

st.subheader(f"Turma: {class_name} – {call_date} ({num_aulas} aula(s))")

# ------------- CHAMADA ------------------
records = []

for idx, row in df.iterrows():
    with st.container(border=True):
        st.markdown(f"**{row['código']} – {row['nome']}**")

        cols = st.columns(len(OCCURRENCES))
        student_occurrences = []

        for col, (label, code) in zip(cols, OCCURRENCES.items()):
            if col.checkbox(label, key=f"{class_name}_{idx}_{label}"):
                student_occurrences.append(code)

        records.append(";".join(student_occurrences))

# ------------- SALVAR NA PLANILHA -----------

if st.button("💾 Salvar chamada"):
    base_date = str(call_date)

    df_full = conn.read(worksheet=class_name)
    df_full.columns = [c.strip().lower() for c in df_full.columns]
    
    # Filtra apenas alunos ativos para salvamento
    df_full_active = df_full[df_full['ativo'].str.lower() != 'n']

    for i in range(num_aulas):
        col_name = f"{base_date} ({i+1})"

        # Salva os registros apenas para alunos ativos
        df_full.loc[df_full_active.index, col_name] = records

    conn.update(
        worksheet=class_name,
        data=df_full
    )

    st.success(f"✅ Chamada registrada para {num_aulas} aula(s) em {base_date}!")

import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import date
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
st.title("Registro de Experiência Formativa - Jacarétronics")

OCCURRENCES = {
    "Trabalho em Equipe": "eqp",
    "Organização e Planejamento": "org",
    "Comunicação": "com",
    "Resolução de Problemas": "prob",
    "Diversão": "div"
}

NIVEIS_PLANEJAMENTO = [
    "Integralmente planejado",
    "Parcialmente planejado",
    "Superficialmente planejado"
]

TIPOS_AULA = [
    "fundamentação teórica",
    "estudo de caso e análise",
    "desenvolvimento prático individual",
    "desenvolvimento em equipe",
    "apresentação e compartilhamento",
    "preparação competitiva",
    "desenvolvimento de projetos",
    "consolidação de conhecimentos",
    "desafios e missões",
    "planejamento e organização"
]

# ------------- CONEXÃO ------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# ------------- SELEÇÕES -----------------
call_date = st.date_input("📅 Data da chamada", date.today())
class_name = "Jacaretronics" # Nome fixo da aba para Jacarétronics
class_turno = st.selectbox("Turno", ["Manhã", "Tarde"])

# ------------- LEITURA DA ABA -----------
df = conn.read(worksheet=class_name)
df.columns = [c.strip().lower() for c in df.columns]

# Filtra apenas alunos ativos e do turno selecionado
df = df[(df['ativo'].str.lower() != 'n') & (df['turno'].str.lower() == class_turno.lower())]

st.subheader(f"{class_name} – {call_date}")

# ------------- PAINEL DE DADOS DA AULA -----------
st.markdown("### 📊 Dados da Aula")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_planejamento = st.selectbox(
            "🎯 Nível de Planejamento",
            NIVEIS_PLANEJAMENTO,
            key="nivel_plan"
        )
    
    with col2:
        satisfacao = st.slider(
            "😊 Satisfação com o encontro",
            min_value=0,
            max_value=10,
            value=5,
            step=1,
            key="satisfacao"
        )
    
    tipo_aula = st.multiselect(
        "📚 Tipo(s) de aula",
        TIPOS_AULA,
        key="tipo_aula"
    )

    obs = st.text_area(
        "� Observações",
        key="obs"
    )

# ------------- CHAMADA ------------------
st.markdown("### 📌 Registro de Presença")
st.caption("Busque o nome do aluno para abrir apenas o bloco de registro dele e evitar alterações acidentais nos demais.")
records = []
presences = []
categories = list(OCCURRENCES.keys())

for idx, row in df.iterrows():
    present_key = f"{class_name}_{idx}_present"
    if present_key not in st.session_state:
        st.session_state[present_key] = True

    for i, _ in enumerate(categories):
        rating_key = f"{class_name}_{idx}_cat_{i}"
        if rating_key not in st.session_state:
            st.session_state[rating_key] = 0

search_term = st.text_input(
    "🔎 Buscar aluno pelo nome",
    placeholder="Digite parte do nome",
    key="buscar_aluno_jacaretronics"
).strip().lower()

filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df['nome'].fillna('').str.lower().str.contains(search_term, na=False)]

if filtered_df.empty:
    st.info("Nenhum aluno encontrado com esse nome.")
    st.stop()

student_options = []
student_lookup = {}
for _, row in filtered_df.iterrows():
    label = f"{row['código']} – {row['nome']}"
    student_lookup[label] = row
    student_options.append(label)

selected_label = st.selectbox(
    "👤 Selecione o aluno",
    student_options,
    key="aluno_selecionado_jacaretronics"
)
selected_row = student_lookup[selected_label]
selected_idx = selected_row.name

for _, row in df.iterrows():
    if row.name != selected_idx:
        continue

    with st.expander(f"🧑‍🎓 Registro de {row['nome']}", expanded=True):
        present_key = f"{class_name}_{row.name}_present"
        present = st.checkbox(
            "Presente",
            value=st.session_state[present_key],
            key=present_key
        )

        cols = st.columns(len(categories))
        ratings = []
        for i, label in enumerate(categories):
            rating_key = f"{class_name}_{row.name}_cat_{i}"
            rating = cols[i].slider(
                label,
                min_value=0,
                max_value=5,
                value=st.session_state[rating_key],
                step=1,
                key=rating_key
            )
            ratings.append(str(rating))

# Monta os registros completos na ordem original do dataframe
for _, row in df.iterrows():
    present_key = f"{class_name}_{row.name}_present"
    present = st.session_state.get(present_key, True)
    presences.append(present)

    ratings = []
    for i, _ in enumerate(categories):
        rating_key = f"{class_name}_{row.name}_cat_{i}"
        ratings.append(str(st.session_state.get(rating_key, 0)))

    records.append(",".join(ratings))

# ------------- CÁLCULOS PARA DADOS_AULAS -----------
# Calcular número de alunos presentes (com base no checkbox 'Presente')
presentes = sum(1 for p in presences if p)

# Calcular percentual de presença
total_alunos = len(df)
percentual_presenca = (presentes / total_alunos * 100) if total_alunos > 0 else 0

# ------------- SALVAR NA PLANILHA -----------

if st.button("💾 Salvar chamada e dados da aula"):
    base_date = str(call_date)

    # Salvar na aba da turma
    df_full = conn.read(worksheet=class_name)
    df_full.columns = [c.strip().lower() for c in df_full.columns]
    
    # Filtra apenas alunos ativos para salvamento
    df_full_active = df_full[df_full['ativo'].str.lower() != 'n']

    # Usar coluna distinta por turno para evitar sobrescrita (ex: 2026-07-21_manha)
    turno_slug = class_turno.lower().replace("ã","a").replace(" ","_")
    col_name = f"{base_date}_{turno_slug}"

    # Salva os registros apenas para os alunos exibidos (mesma ordem que `df`)
    # Se o aluno não estiver presente, salva 'f' para falta em vez das notas
    save_values = []
    for i in range(len(records)):
        try:
            presente = presences[i]
        except IndexError:
            presente = True
        save_values.append(records[i] if presente else "f")

    df_full.loc[df.index, col_name] = save_values

    conn.update(
        worksheet=class_name,
        data=df_full
    )

    # Salvar na aba Dados_Aulas
    try:
        df_dados_aulas = conn.read(worksheet="Dados_Aulas")
        df_dados_aulas.columns = [c.strip() for c in df_dados_aulas.columns]
    except:
        # Se a aba não existe, criar com as colunas necessárias
        df_dados_aulas = pd.DataFrame(columns=[
            "DATA", "TURMA", "TURNO", "ALUNOS_PRESENTES", "PERCENTUAL_PRESENÇA",
            "NÍVEL_PLAN", "TIPO", "SATISFAÇÃO", "OBSERVAÇÕES"
        ])

    # Criar novo registro
    novo_registro = {
        "DATA": base_date,
        "TURMA": class_name,
        "TURNO": class_turno,
        "ALUNOS_PRESENTES": presentes,
        "PERCENTUAL_PRESENÇA": f"{percentual_presenca:.1f}%",
        "NÍVEL_PLAN": nivel_planejamento,
        "TIPO": "; ".join(tipo_aula) if tipo_aula else "",
        "SATISFAÇÃO": satisfacao,
        "OBSERVAÇÕES": obs
    }

    # Adicionar novo registro ao dataframe
    df_dados_aulas = pd.concat([df_dados_aulas, pd.DataFrame([novo_registro])], ignore_index=True)

    # Salvar na planilha
    conn.update(
        worksheet="Dados_Aulas",
        data=df_dados_aulas
    )

    st.success(f"✅ Chamada e dados da aula registrados em {base_date}!")

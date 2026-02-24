# ======================================================
# DEMOGRAPHIC AI v3 - AGENTE EMPRESARIAL (CORRIGIDO)
# ======================================================

import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from pandas import ExcelWriter

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="DemographicAI v3", page_icon="📊", layout="wide")
load_dotenv()

DB_PATH = "sqlite:///censo.db"
engine = create_engine(DB_PATH)

# --- FUNÇÕES DE SUPORTE ---
def gerar_multiplos_graficos(df):
    arquivos = []
    for i in range(1, min(4, len(df.columns))):
        plt.figure()
        df.head(10).plot(x=df.columns[0], y=df.columns[i], kind="bar")
        path = f"grafico_{i}.png"
        plt.savefig(path)
        plt.close()
        arquivos.append(path)
    return arquivos

def gerar_pdf(df, resumo="Relatório automático"):
    styles = getSampleStyleSheet()
    path = "relatorio.pdf"
    doc = SimpleDocTemplate(path)
    elementos = []
    elementos.append(Paragraph("Relatório Demográfico", styles["Heading1"]))
    elementos.append(Paragraph(resumo, styles["BodyText"]))
    elementos.append(Spacer(1, 20))
    graficos = gerar_multiplos_graficos(df)
    for g in graficos:
        elementos.append(Image(g, width=500, height=300))
        elementos.append(Spacer(1, 20))
    tabela = [df.columns.tolist()] + df.head(10).values.tolist()
    elementos.append(Table(tabela))
    doc.build(elementos)
    return path

def gerar_excel(df):
    path = "relatorio.xlsx"
    with ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name="dados", index=False)
        df.describe().to_excel(writer, sheet_name="estatisticas")
    return path

def pedido_relatorio(prompt):
    palavras = ["relatório", "relatorio", "pdf", "excel", "exportar"]
    return any(p in prompt.lower() for p in palavras)

# --- 1. SELEÇÃO DE MODELO (PRECISA VIR ANTES DO AGENTE) ---
with st.sidebar:
    st.title("📊 DemographicAI v3")
    
    model_name = st.selectbox(
        "Modelo",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    )
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# --- 2. INICIALIZAÇÃO DO AGENTE (FORA DA SIDEBAR) ---
llm = ChatGroq(
    model=model_name,
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

sql_agent = None
db_ready = False

if uploaded_file:
    # Carrega no banco
    df_upload = pd.read_csv(uploaded_file)
    df_upload.columns = df_upload.columns.str.lower().str.replace(" ", "_")
    df_upload.to_sql("dados_censo", engine, if_exists="replace", index=False)
    
    try:
        db = SQLDatabase.from_uri(DB_PATH)
        sql_agent = create_sql_agent(llm=llm, db=db, verbose=True)
        db_ready = True
    except Exception as e:
        st.error(f"Erro ao conectar banco: {e}")

# --- 3. LÓGICA DO BOTÃO NA SIDEBAR (AGORA O AGENTE JÁ EXISTE) ---
with st.sidebar:
    if uploaded_file and st.button("📄 Gerar Relatório PDF/Excel"):
        if db_ready:
            df = pd.read_sql("SELECT * FROM dados_censo", engine)
            resumo = sql_agent.run("Faça um resumo estatístico destes dados")
            
            pdf_path = gerar_pdf(df, resumo)
            excel_path = gerar_excel(df)
            
            st.success("✅ Relatórios gerados!")
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Baixar PDF", f, file_name="relatorio.pdf")
            with open(excel_path, "rb") as f:
                st.download_button("⬇️ Baixar Excel", f, file_name="relatorio.xlsx")
        else:
            st.error("Banco de dados não está pronto.")

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT PRINCIPAL ---
st.title("📊 Agente Demográfico Empresarial")

if "messages" not in st.session_state:
    st.session_state.messages = []

for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)

prompt = st.chat_input("Pergunte ou peça um relatório...")

if prompt:
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        if db_ready:
            if pedido_relatorio(prompt):
                df = pd.read_sql("SELECT * FROM dados_censo", engine)
                resumo = sql_agent.run("Faça um resumo estatístico destes dados em português")
                pdf = gerar_pdf(df, resumo)
                excel = gerar_excel(df)
                
                st.success("Relatórios gerados")
                col1, col2 = st.columns(2)
                with col1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇️ PDF", f, file_name="relatorio.pdf")
                with col2:
                    with open(excel, "rb") as f:
                        st.download_button("⬇️ Excel", f, file_name="relatorio.xlsx")
                resposta = "Relatórios gerados com sucesso."
            else:
                resposta = sql_agent.run(prompt)
        else:
            resposta = "Por favor, carregue um arquivo CSV na barra lateral primeiro."
        
        st.write(resposta)
        st.session_state.messages.append(("assistant", resposta))

# --- CSS ---
# ---------- CSS ATUALIZADO ----------
st.markdown("""
<style>

/* Fundo geral */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
}

/* Centralizar chat */
.main {
    max-width: 900px;
    margin: auto;
}

/* Bolha usuário */
[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #1e293b;
    border-radius: 15px;
    padding: 10px;
    margin: 5px 0;
    font-size: 25px;
}

/* Bolha assistente */
[data-testid="stChatMessage"][data-testid*="assistant"] {
    background-color: #0ea5e9;
    border-radius: 15px;
    padding: 10px;
    margin: 5px 0;
    font-size: 25px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #020617;
}

/* Botão */
.stButton button {
    width: 100%;
    border-radius: 10px;
    background-color: #0ea5e9;
    color: white;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)
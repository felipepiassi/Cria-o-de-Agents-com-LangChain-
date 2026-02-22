import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# ---------- CONFIGURAÇÃO ----------
st.set_page_config(
    page_title="Agente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    font-size: 22px;
}

/* Bolha assistente */
[data-testid="stChatMessage"][data-testid*="assistant"] {
    background-color: #0ea5e9;
    border-radius: 15px;
    padding: 10px;
    margin: 5px 0;
    font-size: 22px;
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

# ----------  ENV ----------
load_dotenv()

# ---------- BARRA ----------
with st.sidebar:

    st.title("🤖 Agente Groq")

    st.markdown("---")

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.session_state.store = {}
        st.rerun()

    st.markdown("---")

    st.markdown("### ⚙️ Modelo")
    model = st.selectbox(
        "Escolha o modelo",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]
    )

    st.markdown("---")

    st.markdown("### 📊 Status")
    st.success("Online")

# ---------- TITULO ----------
st.title("💬 Assistente IA")
st.caption("Powered by Groq + LangChain")

# ---------- LLM ----------
llm = ChatGroq(
    model=model,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

# ---------- MEMORIA ----------
if "store" not in st.session_state:
    st.session_state.store = {}

def get_session_history(session_id):
    if session_id not in st.session_state.store:
        st.session_state.store[session_id] = InMemoryChatMessageHistory()
    return st.session_state.store[session_id]

chain = RunnableWithMessageHistory(
    llm,
    get_session_history,
)

# ---------- SESSÃO ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = "user"

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- CHAT  ----------
for role, message in st.session_state.messages:
    with st.chat_message(role, avatar="🤖" if role=="assistant" else "👤"):
        st.write(message)

# ---------- ENTRADA ----------
prompt = st.chat_input("Digite sua mensagem...")

if prompt:

    st.session_state.messages.append(("user", prompt))

    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🤖"):

        with st.spinner("Pensando..."):
            response = chain.invoke(
                prompt,
                config={
                    "configurable": {
                        "session_id": st.session_state.session_id
                    }
                }
            )

            answer = response.content
            st.write(answer)

    st.session_state.messages.append(("assistant", answer))
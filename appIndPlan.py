import streamlit as st
import pandas as pd

# =====================
# Configuração
# =====================
st.set_page_config(
    page_title="Simulador de Capacidade – RFQ",
    layout="wide"
)

st.title("Simulador de Capacidade de Máquinas")
st.caption("Simulação de demanda industrial baseada em RFQs – horizonte de 5 anos")

# =====================
# SIDEBAR – RFQs no cenário
# =====================
st.sidebar.header("RFQs no Cenário")

# Inicializa lista no session_state
if "rfqs" not in st.session_state:
    st.session_state.rfqs = []

# Campo de entrada
nova_rfq = st.sidebar.text_input(
    "Adicionar RFQ",
    placeholder="Ex: 123456"
)

col_add, col_clear = st.sidebar.columns(2)

with col_add:
    if st.button("Adicionar"):
        if nova_rfq and nova_rfq not in st.session_state.rfqs:
            st.session_state.rfqs.append(nova_rfq)

with col_clear:
    if st.button("Limpar"):
        st.session_state.rfqs = []

st.sidebar.divider()

# Lista de RFQs adicionadas
st.sidebar.subheader("RFQs selecionadas")

if not st.session_state.rfqs:
    st.sidebar.info("Nenhuma RFQ adicionada")
else:
    for i, rfq in enumerate(st.session_state.rfqs):
        col_rfq, col_remove = st.sidebar.columns([3, 1])
        with col_rfq:
            st.write(rfq)
        with col_remove:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.rfqs.pop(i)
                st.experimental_rerun()

st.sidebar.divider()

st.sidebar.button("Rodar Simulação")


# =====================
# ETAPA 2 – Distribuição por Centro de Trabalho
# =====================
st.header("2️⃣ Distribuição de Volume por Centro de Trabalho (WC)")

st.info(
    "Os centros de trabalho e suas taxas de produção por RFQ "
    "serão obtidos da planilha '2_LN_DadosExportados'."
)

st.latex(
    r"\text{Volume WC} = \frac{\text{Volume Bruto do Ano}}{\text{Taxa de Produção do WC (RFQ)}}"
)

df_wc = pd.DataFrame({
    "RFQ": [],
    "Ano": [],
    "Centro de Trabalho (WC)": [],
    "Taxa de Produção": [],
    "Volume Distribuído WC": []
})

st.dataframe(df_wc)

# =====================
# ETAPA 3 – Simulação de Demanda (Plano Industrial)
# =====================
st.header("3️⃣ Simulação de Demanda – Plano Industrial")

st.info(
    "Os volumes distribuídos por WC serão somados à demanda natural "
    "do Plano Industrial para cada ano."
)

df_demanda_simulada = pd.DataFrame({
    "Ano": [],
    "Centro de Trabalho (WC)": [],
    "Demanda Natural (Plano Industrial)": [],
    "Demanda RFQs": [],
    "Demanda Total Simulada": []
})

st.dataframe(df_demanda_simulada)

# =====================
# ETAPA 4 – Capacidade e Quantidade de Máquinas
# =====================
st.header("4️⃣ Análise de Capacidade e Máquinas")

st.info(
    "Nesta etapa será avaliada a capacidade necessária por WC, "
    "comparando com a quantidade de máquinas existente."
)

df_capacidade = pd.DataFrame({
    "Ano": [],
    "Centro de Trabalho (WC)": [],
    "Demanda Total": [],
    "Capacidade por Máquina": [],
    "Máquinas Necessárias": [],
    "Máquinas Existentes": [],
    "Necessidade de Investimento": []
})

st.dataframe(df_capacidade)

# =====================
# RESUMO EXECUTIVO
# =====================
st.header("📊 Resumo Executivo da Simulação")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("RFQs Simuladas", len(rfqs))

with col2:
    st.metric("WCs Impactados", "--")

with col3:
    st.metric("Investimentos Necessários", "--")

# =====================
# EXPORTAÇÃO
# =====================
st.header("💾 Exportação")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.button("Exportar Resultados para Excel")

with col_exp2:
    st.button("Salvar Cenário de Simulação")

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
# SIDEBAR – Entrada de RFQs
# =====================
st.sidebar.header("RFQs para Simulação")

rfq_input = st.sidebar.text_input(
    "Número(s) da RFQ",
    help="Informe uma ou mais RFQs separadas por vírgula (ex: 12345, 67890)"
)

rfqs = [r.strip() for r in rfq_input.split(",") if r.strip()]

st.sidebar.write("RFQs consideradas:")
st.sidebar.write(rfqs if rfqs else "Nenhuma RFQ inserida")

st.sidebar.divider()

st.sidebar.button("Rodar Simulação")

# =====================
# ETAPA 1 – Volumes de vendas (RFQ)
# =====================
st.header("1️⃣ Volumes Brutos por RFQ (5 anos)")

st.info(
    "Nesta etapa serão carregados os volumes brutos previstos por RFQ "
    "a partir da planilha '1_RFQ_DadosVendas'."
)

df_volumes_rfq = pd.DataFrame({
    "RFQ": [],
    "Ano": [],
    "Volume Bruto": []
})

st.dataframe(df_volumes_rfq)

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

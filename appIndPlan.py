import streamlit as st
import pandas as pd

# =====================
# CONFIGURAÇÃO
# =====================
st.set_page_config(
    page_title="Simulador de Capacidade – RFQ / Industrial Plan",
    layout="wide"
)

st.title("Simulador de Capacidade Industrial")
st.caption("Simulação de demanda e capacidade baseada em RFQs – horizonte de 5 anos")

# =====================
# SIDEBAR – CONTROLE DE RFQs
# =====================
st.sidebar.header("RFQs no Cenário")

if "rfqs" not in st.session_state:
    st.session_state.rfqs = []

nova_rfq = st.sidebar.text_input(
    "Adicionar RFQ",
    placeholder="Ex: RFQ_123456"
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

st.sidebar.subheader("RFQs Selecionadas")

if not st.session_state.rfqs:
    st.sidebar.info("Nenhuma RFQ adicionada")
else:
    for i, rfq in enumerate(st.session_state.rfqs):
        col_rfq, col_remove = st.sidebar.columns([4, 1])
        with col_rfq:
            st.write(rfq)
        with col_remove:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.rfqs.pop(i)
                st.experimental_rerun()

st.sidebar.divider()
st.sidebar.button("Rodar Simulação")

rfqs = st.session_state.rfqs

# =====================
# ETAPA 1 – RFQ DADOS DE VENDAS
# =====================
st.header("1️⃣ RFQs – Volumes Brutos de Vendas (5 anos)")

st.info(
    "Volumes previstos por RFQ e por ano, "
    "oriundos da planilha **1_RFQ_DadosVendas**."
)


if uploaded_file is None:
st.warning("Faça o upload do arquivo Excel para continuar.")
st.stop()


# Leitura da planilha
df_rfq_raw = pd.read_excel(
uploaded_file,
sheet_name="1_RFQ_DadosVendas"
)


# Limpeza básica
df_rfq_raw.columns = df_rfq_raw.columns.astype(str).str.strip()


# Renomear coluna RFQ
df_rfq_raw = df_rfq_raw.rename(columns={"LINK": "RFQ"})


# Filtrar RFQs selecionadas
df_rfq_filtrado = df_rfq_raw[
df_rfq_raw["RFQ"].isin(rfqs)
][["RFQ"]].copy()

if df_rfq_filtrado.empty:
st.warning("Nenhuma RFQ selecionada encontrada na base.")
st.stop()

# Normalização: anos → linhas
df_rfq_vendas = df_rfq_filtrado.melt(
id_vars=["RFQ"],

var_2026="2025",
var_2026="2026",
var_2026="2027",
var_2026="2028",
var_2026="2029",
var_2026="2030"
)


df_rfq_vendas["2025"] = df_rfq_vendas["2025"].astype(int)
df_rfq_vendas["2026"] = df_rfq_vendas["2026"].astype(int)
df_rfq_vendas["2027"] = df_rfq_vendas["2027"].astype(int)
df_rfq_vendas["2028"] = df_rfq_vendas["2028"].astype(int)
df_rfq_vendas["2029"] = df_rfq_vendas["2029"].astype(int)
df_rfq_vendas["2030"] = df_rfq_vendas["2030"].astype(int)


# Exibição
st.dataframe(
df_rfq_vendas.sort_values(["RFQ", "2025", "2025", "2026","2027","2028","2029","2030"]),
use_container_width=True
)

# =====================
# ETAPA 2 – LN DADOS EXPORTADOS
# =====================
st.header("2️⃣ Distribuição por Centro de Trabalho (LN)")

st.info(
    "Centros de trabalho (WC) envolvidos por RFQ, "
    "com taxa de produção específica por cotação "
    "(planilha **2_LN_DadosExportados**)."
)

st.latex(
    r"\text{Volume WC} = \frac{\text{Volume Bruto do Ano}}{\text{Taxa de Produção do WC (RFQ)}}"
)

df_ln_wc = pd.DataFrame({
    "RFQ": [],
    "Ano": [],
    "Centro de Trabalho (WC)": [],
    "Taxa de Produção WC": [],
    "Volume Calculado WC": []
})

st.dataframe(df_ln_wc)

# =====================
# ETAPA 3 – SIMULAÇÃO DE DEMANDA
# =====================
st.header("3️⃣ Simulação de Demanda – Industrial Plan")

st.info(
    "Soma da demanda natural do Plano Industrial "
    "com os volumes calculados das RFQs selecionadas "
    "(planilha **3_Industrial_Plan_Idash**)."
)

df_demanda = pd.DataFrame({
    "Ano": [],
    "Centro de Trabalho (WC)": [],
    "Demanda Natural (Industrial Plan)": [],
    "Demanda RFQs": [],
    "Demanda Total Simulada": []
})

st.dataframe(df_demanda)

# =====================
# ETAPA 4 – CAPACIDADE E INVESTIMENTO
# =====================
st.header("4️⃣ Capacidade, Máquinas e Investimento")

st.info(
    "Análise de capacidade considerando quantidade de máquinas, "
    "capacidade planejada, OEE e verificação de necessidade de investimento."
)

df_capacidade = pd.DataFrame({
    "Ano": [],
    "Centro de Trabalho (WC)": [],
    "Capacidade Planejada": [],
    "OEE (%)": [],
    "Capacidade Efetiva": [],
    "Demanda Total": [],
    "Máquinas Existentes": [],
    "Máquinas Necessárias": [],
    "Status": []  # OK / INVEST
})

st.dataframe(df_capacidade)

# =====================
# RESUMO EXECUTIVO
# =====================
st.header("📊 Resumo Executivo")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("RFQs no Cenário", len(rfqs))

with col2:
    st.metric("Centros de Trabalho Impactados", "--")

with col3:
    st.metric("WCs com Necessidade de Investimento", "--")

# =====================
# EXPORTAÇÃO
# =====================
st.header("💾 Exportação e Cenários")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.button("Exportar Resultados (Excel)")

with col_exp2:
    st.button("Salvar Cenário de Simulação")

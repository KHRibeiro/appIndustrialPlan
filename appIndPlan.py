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

st.sidebar.divider()
st.sidebar.subheader("Base de Dados")

uploaded_file = st.sidebar.file_uploader(
    "Analise_Investimento_Modelo",
    type=["xlsx"]
)

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
# ETAPA 1 – RFQ DADOS DE VENDAS (REAL)
# =====================
st.header("1️⃣ RFQs – Volumes Brutos de Vendas (2026–2030)")

st.info(
    "Volumes brutos previstos por RFQ e por ano, "
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

# Colunas de anos (dinâmico, robusto)
colunas_anos = [c for c in df_rfq_raw.columns if c.isdigit()]

# Filtrar RFQs selecionadas
df_rfq_filtrado = df_rfq_raw[
    df_rfq_raw["RFQ"].isin(rfqs)
][["RFQ"] + colunas_anos].copy()

if df_rfq_filtrado.empty:
    st.warning("Nenhuma RFQ selecionada encontrada na base.")
    st.stop()

# Normalização: anos → linhas
df_rfq_vendas = df_rfq_filtrado.melt(
    id_vars=["RFQ"],
    value_vars=colunas_anos,
    var_name="Ano",
    value_name="Volume Bruto"
)

df_rfq_vendas["Ano"] = df_rfq_vendas["Ano"].astype(int)
df_rfq_vendas["Volume Bruto"] = df_rfq_vendas["Volume Bruto"].fillna(0)

# Exibição
st.dataframe(
    df_rfq_vendas.sort_values(["RFQ", "Ano"]),
    use_container_width=True
)

# =====================
# ETAPA 2 – DISTRIBUIÇÃO POR CENTRO DE TRABALHO (LN)
# =====================
st.header("2️⃣ Distribuição por Centro de Trabalho (LN)")

st.info(
    "Distribuição do volume bruto das RFQs por centro de trabalho (WC), "
    "utilizando a taxa de produção específica por RFQ × WC "
    "(planilha **2_LN_DadosExportados**)."
)

# Leitura da planilha LN
df_ln_raw = pd.read_excel(
    uploaded_file,
    sheet_name="2_LN_DadosExportados"
)

# Limpeza básica
df_ln_raw.columns = df_ln_raw.columns.astype(str).str.strip()

st.subheader("🔍 Diagnóstico – Colunas LN")
st.write("Colunas originais:")
st.write(list(df_ln_raw.columns))

# Renomear colunas para padrão interno
df_ln = df_ln_raw.rename(
    columns={
        "Item Fabricado": "RFQ",
        "Cent. Trab.": "WC",
        "Taxa de produção": "Taxa"
    }
)

# Manter apenas colunas relevantes
df_ln = df_ln[["RFQ", "WC", "Taxa"]].copy()

# Filtrar apenas RFQs selecionadas na simulação
df_ln = df_ln[df_ln["RFQ"].isin(rfqs)]

if df_ln.empty:
    st.warning("Nenhum WC encontrado para as RFQs selecionadas.")
    st.stop()

# =====================
# JOIN RFQ × ANO × VOLUME (Etapa 1) com LN (WC × Taxa)
# =====================
df_ln_wc = df_rfq_vendas.merge(
    df_ln,
    on="RFQ",
    how="inner"
)

# =====================
# Cálculo do volume por WC (fórmula central da Etapa 2)
# =====================
df_ln_wc["Volume Calculado WC"] = (
    df_ln_wc["Volume Bruto"] / df_ln_wc["Taxa"]
)

# Organização final
df_ln_wc = df_ln_wc[[
    "RFQ",
    "Ano",
    "WC",
    "Taxa",
    "Volume Bruto",
    "Volume Calculado WC"
]].sort_values(["WC", "Ano", "RFQ"])

# Exibição
st.dataframe(
    df_ln_wc,
    use_container_width=True
)

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

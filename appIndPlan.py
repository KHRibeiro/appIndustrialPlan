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

# Limpeza e padronização dos nomes das colunas
df_ln_raw.columns = (
    df_ln_raw.columns
    .astype(str)
    .str.strip()
    .str.replace("\n", "", regex=False)
    .str.replace("\xa0", "", regex=False)
)

#diagnóstico de leitura
#st.subheader("🔍 Diagnóstico – Colunas LN")
#st.write("Colunas originais:")
#st.write(list(df_ln_raw.columns))

# Renomear colunas para padrão interno
df_ln = df_ln_raw.rename(
    columns={
        "Item fabricado": "RFQ",
        "Cent. Trab.": "WC",
        "Taxa de produção": "Taxa"
    }
)

#Validação Segura
colunas_esperadas = ["RFQ", "WC", "Taxa"]
faltando = [c for c in colunas_esperadas if c not in df_ln.columns]

if faltando:
    st.error(f"Colunas não encontradas na LN: {faltando}")
    st.stop()

# Manter apenas colunas relevantes
df_ln = df_ln[["RFQ", "WC", "Taxa"]].copy()

#Limpeza de Dados
df_ln = df_ln.dropna(subset=["RFQ", "WC", "Taxa"])

df_ln["Taxa"] = pd.to_numeric(df_ln["Taxa"], errors="coerce")
df_ln = df_ln.dropna(subset=["Taxa"])

# Visualização de dados
st.subheader("📋 Etapa 2 – Estrutura RFQ × WC × Taxa")
st.dataframe(df_ln, use_container_width=True)

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

df_ip_raw = pd.read_excel(
    uploaded_file,
    sheet_name="3_Industrial_Plan_Idash"
)

#st.subheader("🔍 Colunas encontradas no Industrial Plan")
#st.write(df_ip_raw.columns.tolist())
#st.stop()

# =====================
# ETAPA 3 – SIMULAÇÃO DE DEMANDA (RFQ × WC × ANO)
# =====================
st.header("3️⃣ Simulação de Demanda – Industrial Plan")

st.info(
    "Conversão da demanda das RFQs em carga industrial por Centro de Trabalho (WC), "
    "considerando a taxa de produção específica de cada RFQ."
)

# ---------------------
# PRÉ-REQUISITOS
# df_rfq_raw → Etapa 1 (RFQ | 2026..2030)
# df_ln       → Etapa 2 (RFQ | WC | Taxa)
# ---------------------

# Validação básica
if df_rfq_raw.empty or df_ln.empty:
    st.warning("Dados insuficientes para simulação. Verifique as Etapas 1 e 2.")
    st.stop()

# ---------------------
# 1️⃣ RFQ × ANO → formato longo
# ---------------------
anos = ["2026", "2027", "2028", "2029", "2030"]

df_demanda_long = df_rfq_raw.melt(
    id_vars=["RFQ"],
    value_vars=anos,
    var_name="Ano",
    value_name="Volume"
)

df_demanda_long["Volume"] = (
    pd.to_numeric(df_demanda_long["Volume"], errors="coerce")
    .fillna(0)
)

# ---------------------
# 2️⃣ Cruzamento RFQ × WC
# ---------------------
df_simulacao = df_demanda_long.merge(
    df_ln,
    on="RFQ",
    how="inner"
)

# ---------------------
# 3️⃣ Cálculo da carga por WC
# Regra: Carga = Volume × Taxa
# ---------------------
df_simulacao["Carga_WC"] = df_simulacao["Volume"] * df_simulacao["Taxa"]

# ---------------------
# 4️⃣ Consolidação por WC e Ano
# ---------------------
df_wc_ano = (
    df_simulacao
    .groupby(["WC", "Ano"], as_index=False)
    .agg(
        Carga_Total_WC=("Carga_WC", "sum")
    )
)

# ---------------------
# 5️⃣ Exibição dos resultados
# ---------------------
st.subheader("📋 Detalhamento RFQ × WC × Ano")
st.dataframe(
    df_simulacao[["RFQ", "Ano", "WC", "Volume", "Taxa", "Carga_WC"]],
    use_container_width=True
)

st.subheader("🏭 Carga Total por Centro de Trabalho (WC)")
st.dataframe(
    df_wc_ano,
    use_container_width=True
)


# =====================
# INDUSTRIAL PLAN – BASE DE CAPACIDADE
# =====================
df_industrial_plan = df_ip_raw.rename(
    columns={
        "WC ID": "WC",
        "Actual machine": "Maquinas_Existentes",
        "Standard Oee": "OEE_percentual",
    }
)

# Manter apenas colunas necessárias
colunas_capacidade = [
    "WC",
    "Maquinas_Existentes",
    "OEE_percentual",
    "PLA_CAP_2025",
    "PLA_CAP_2026",
    "PLA_CAP_2027",
    "PLA_CAP_2028",
    "PLA_CAP_2029",
    "PLA_CAP_2030",
]

df_industrial_plan = df_industrial_plan[colunas_capacidade].copy()

# Limpeza
df_industrial_plan["WC"] = df_industrial_plan["WC"].astype(str).str.strip()

df_base_etapa4 = df_industrial_plan

# =========================
# ETAPA 4 – CAPACIDADE & INVESTIMENTO (ANOS EM COLUNAS)
# =========================

import numpy as np
import streamlit as st
import pandas as pd

st.header("4️⃣ Capacidade, Máquinas e Investimento")

# -------------------------------------------------
# DataFrame base (resultado da Etapa 3)
# -------------------------------------------------
df = df_base_etapa4.copy()

# -------------------------------------------------
# Identificar anos automaticamente
# -------------------------------------------------
anos = sorted({
    int(c.split("_")[-1])
    for c in df.columns
    if c.startswith("REQ_CAP_")
})

# -------------------------------------------------
# Verificação INVEST / OK
# -------------------------------------------------
status_cols = []

for ano in anos:
    col_req = f"REQ_CAP_{ano}"
    col_cap = f"TOTAL_CAP_{ano}"
    col_status = f"STATUS_{ano}"

    if col_req in df.columns and col_cap in df.columns:
        df[col_status] = np.where(
            df[col_req] > df[col_cap],
            "INVEST",
            "OK"
        )
        status_cols.append(col_status)

# -------------------------------------------------
# Coluna consolidada (se INVEST em qualquer ano)
# -------------------------------------------------
df["NECESSÁRIO INVESTIR?"] = np.where(
    df[status_cols].eq("INVEST").any(axis=1),
    "INVEST",
    "OK"
)

# -------------------------------------------------
# Ordenação final das colunas
# -------------------------------------------------
ordem = (
    ["NECESSÁRIO INVESTIR?", "WC ID", "WC NAME", "Actual machine"]
    + [f"MRSRFQ_{ano}" for ano in anos if f"MRSRFQ_{ano}" in df.columns]
    + [f"MRS_{ano}" for ano in anos if f"MRS_{ano}" in df.columns]
    + [f"REQ_CAP_{ano}" for ano in anos]
    + [f"PLA_CAP_{ano}" for ano in anos if f"PLA_CAP_{ano}" in df.columns]
    + [f"TOTAL_CAP_{ano}" for ano in anos]
    + status_cols
)

# manter só colunas existentes
ordem = [c for c in ordem if c in df.columns]

df_final = df[ordem].copy()

# -------------------------------------------------
# Exibição
# -------------------------------------------------
st.dataframe(df_final, use_container_width=True)

# -------------------------------------------------
# Exportação
# -------------------------------------------------
def to_excel(df):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Industrial_Plan")
    return output.getvalue()

st.download_button(
    "📥 Exportar Industrial Plan Final",
    to_excel(df_final),
    "industrial_plan_simulado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

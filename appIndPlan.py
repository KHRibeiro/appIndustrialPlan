import streamlit as st
import pandas as pd
import numpy as np

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
# ETAPA 1 – RFQs | Volumes Brutos
# =====================
st.header("1️⃣ RFQs – Volumes Brutos de Vendas")

df_rfq = pd.read_excel(
    uploaded_file,
    sheet_name="1_RFQ_DadosVendas"
)

df_rfq.columns = df_rfq.columns.astype(str).str.strip()
df_rfq = df_rfq.rename(columns={"LINK": "RFQ"})

anos = [c for c in df_rfq.columns if c.isdigit()]

df_rfq = df_rfq[df_rfq["RFQ"].isin(rfqs)][["RFQ"] + anos].copy()
df_rfq[anos] = df_rfq[anos].apply(pd.to_numeric, errors="coerce").fillna(0)

st.dataframe(df_rfq, use_container_width=True)


# =====================
# ETAPA 2 – LN | Distribuição por WC
# =====================

st.header("2️⃣ Distribuição RFQ × WC (LN)")

df_ln_raw = pd.read_excel(
    uploaded_file,
    sheet_name="2_LN_DadosExportados"
)

df_ln_raw.columns = (
    df_ln_raw.columns.astype(str)
    .str.strip()
    .str.replace("\n", "", regex=False)
    .str.replace("\xa0", "", regex=False)
)

rename_map = {}
for c in df_ln_raw.columns:
    if "Item" in c:
        rename_map[c] = "RFQ"
    elif "Cent" in c:
        rename_map[c] = "WC"
    elif "Taxa" in c:
        rename_map[c] = "Taxa"

df_ln = df_ln_raw.rename(columns=rename_map)

colunas_req = ["RFQ", "WC", "Taxa"]
faltantes = [c for c in colunas_req if c not in df_ln.columns]
if faltantes:
    st.error(f"Colunas ausentes na LN: {faltantes}")
    st.stop()

df_ln = df_ln[colunas_req].dropna()
df_ln["Taxa"] = pd.to_numeric(df_ln["Taxa"], errors="coerce")
df_ln = df_ln.dropna(subset=["Taxa"])

# padronizar WC → HOR-
df_ln["WC"] = "HOR-" + df_ln["WC"].astype(str).str.strip()

df_ln = df_ln[df_ln["RFQ"].isin(rfqs)]

st.dataframe(df_ln, use_container_width=True)


# =====================
# ETAPA 3 – Simulação de Demanda
# =====================
st.header("3️⃣ Simulação de Demanda Industrial")

# RFQ × WC
df_volwc = df_ln.merge(df_rfq, on="RFQ", how="inner")

# cálculo por ano
for ano in anos:
    df_volwc[f"MRSRFQ_{ano}"] = df_volwc[ano] / df_volwc["Taxa"]

cols_mrsrfq = ["RFQ", "WC"] + [f"MRSRFQ_{ano}" for ano in anos]
df_volwc = df_volwc[cols_mrsrfq]

# consolidação por WC - Montagem de volumes por centro de trabalho
#Não tem cálculo da fórmula 1

df_mrsrfq_wc = (
    df_volwc
    .groupby("WC", as_index=False)
    .sum(numeric_only=True)
)

#Exibição dos dados
st.dataframe(df_mrsrfq_wc, use_container_width=True)


# =====================
# ETAPA 4 – Capacidade & Investimento
# =====================
st.header("4️⃣ Capacidade, Máquinas e Investimento")

# Leitura do Industrial Plan
df_ip_raw = pd.read_excel(
    uploaded_file,
    sheet_name="3_Industrial_Plan_Idash"
)

# Renomear colunas
df_ip = df_ip_raw.rename(
    columns={
        "WC ID": "WC",
        "Actual machine": "Actual_machine",
        "Standard Oee": "OEE"
    }
)

# Limpar nomes de WCs
df_ip["WC"] = df_ip["WC"].astype(str).str.strip()

# Capacidades planejadas
for ano in anos:
    df_ip[f"PLA_CAP_{ano}"] = pd.to_numeric(
        df_ip.get(f"PLA_CAP_{ano}", 0), errors="coerce"
    ).fillna(0)

# Merge com volumes RFQ por WC
#df_base = df_ip.merge(
#    df_mrsrfq_wc,
#    on="WC",
#    how="left"
#)

df_base=df_ip

#st.dataframe(df_mrsrfq_wc, use_container_width=True)

# Garantir que todas as colunas MRSRFQ existam
for ano in anos:
    if f"MRSRFQ_{ano}" not in df_base.columns:
        df_base[f"MRSRFQ_{ano}"] = 0
    else:
        df_base[f"MRSRFQ_{ano}"] = df_base[f"MRSRFQ_{ano}"].fillna(0)

# Total de capacidade = PLA_CAP (modelo atual)
for ano in anos:
    df_base[f"TOTAL_CAP_{ano}"] = df_base.get(f"PLA_CAP_{ano}", 0)

# STATUS por ano: INVEST se MRSRFQ > TOTAL_CAP
status_cols = []
for ano in anos:
    col = f"STATUS_{ano}"
    df_base[col] = np.where(
        df_base[f"MRSRFQ_{ano}"] > df_base[f"TOTAL_CAP_{ano}"],
        "INVEST",
        "OK"
    )
    status_cols.append(col)

# Consolidado geral: se algum ano precisa investir → INVEST
df_base["NECESSÁRIO INVESTIR?"] = np.where(
    df_base[status_cols].eq("INVEST").any(axis=1),
    "INVEST",
    "OK"
)

# Filtro de WCs afetados
filtro_wc = st.checkbox("Mostrar apenas WCs afetados pelas RFQs")
if filtro_wc:
    df_base = df_base[df_base["NECESSÁRIO INVESTIR?"] == "INVEST"]

# Ordenação final
ordem = (
    ["NECESSÁRIO INVESTIR?", "WC", "Actual_machine", "OEE"]
    + [f"MRSRFQ_{ano}" for ano in anos]
    + [f"PLA_CAP_{ano}" for ano in anos]
    + [f"TOTAL_CAP_{ano}" for ano in anos]
    + status_cols
)
ordem = [c for c in ordem if c in df_base.columns]

df_final = df_base[ordem].copy()

st.dataframe(df_final, use_container_width=True)

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

# consolidação por WC
df_mrsrfq_wc = (
    df_volwc
    .groupby("WC", as_index=False)
    .sum(numeric_only=True)
)

st.dataframe(df_mrsrfq_wc, use_container_width=True)


# =====================
# FLAG – WC AFETADO POR RFQs
# =====================
impacto = []

for ano in anos:
    novo = f"MRSRFQ_{ano}"
    orig = f"MRSRFQ_ORIG_{ano}"

    if novo in df_sim.columns and orig in df_sim.columns:
        impacto.append(
            df_sim[novo].fillna(0) > df_sim[orig].fillna(0)
        )

df_sim["WC_AFETADO_RFQ"] = pd.concat(impacto, axis=1).any(axis=1)

# =====================
# ETAPA 4 – Capacidade & Investimento
# =====================
st.header("4️⃣ Capacidade, Máquinas e Investimento")

df_ip_raw = pd.read_excel(
    uploaded_file,
    sheet_name="3_Industrial_Plan_Idash"
)

df_ip = df_ip_raw.rename(
    columns={
        "WC ID": "WC",
        "Actual machine": "Actual_machine",
        "Standard Oee": "OEE"
    }
)

df_ip["WC"] = df_ip["WC"].astype(str).str.strip()

# capacidades planejadas
for ano in anos:
    df_ip[f"PLA_CAP_{ano}"] = pd.to_numeric(
        df_ip.get(f"PLA_CAP_{ano}", 0), errors="coerce"
    ).fillna(0)

# base etapa 4
df_base = df_ip.merge(
    df_mrsrfq_wc,
    on="WC",
    how="left"
)

# preencher RFQ ausente
for ano in anos:
    df_base[f"MRSRFQ_{ano}"] = df_base[f"MRSRFQ_{ano}"].fillna(0)

# TOTAL CAP = PLA_CAP (modelo atual)
for ano in anos:
    df_base[f"TOTAL_CAP_{ano}"] = df_base[f"PLA_CAP_{ano}"]

# STATUS por ano
status_cols = []
for ano in anos:
    col = f"STATUS_{ano}"
    df_base[col] = np.where(
        df_base[f"MRSRFQ_{ano}"] > df_base[f"TOTAL_CAP_{ano}"],
        "INVEST",
        "OK"
    )
    status_cols.append(col)

# consolidado
df_base["NECESSÁRIO INVESTIR?"] = np.where(
    df_base[status_cols].eq("INVEST").any(axis=1),
    "INVEST",
    "OK"
)

# filtro de WCs afetados
st.checkbox("Mostrar apenas WCs afetados pelas RFQs", key="filtro_wc")

if st.session_state.filtro_wc:
    df_base = df_base[
        df_base[[f"MRSRFQ_{ano}" for ano in anos]].sum(axis=1) > 0
    ]

# ordenação final
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

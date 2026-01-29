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
st.header("1️⃣ RFQs – Volumes Brutos")

df_rfq = pd.read_excel(
    uploaded_file,
    sheet_name="1_RFQ_DadosVendas"
)

df_rfq.columns = df_rfq.columns.astype(str).str.strip()
df_rfq = df_rfq.rename(columns={"LINK": "RFQ"})

# Identificar colunas de ano (2026–2030)
anos = []
for c in df_rfq.columns:
    c_str = str(c).strip()
    if c_str.isdigit() and len(c_str) == 4:
        anos.append(c_str)

anos = sorted(anos)

# Garantir nomes como string
df_rfq.columns = df_rfq.columns.map(str)

df_rfq_sel = df_rfq[df_rfq["RFQ"].isin(rfqs)][["RFQ"] + anos].copy()
df_rfq_sel[anos] = df_rfq_sel[anos].apply(pd.to_numeric, errors="coerce").fillna(0)


df_rfq_sel[anos] = df_rfq_sel[anos].fillna(0)
st.dataframe(df_rfq_sel, use_container_width=True)


# =====================
# ETAPA 2 – LN | Distribuição por WC
# =====================
st.header("2️⃣ Distribuição por Centro de Trabalho (LN)")

df_ln = pd.read_excel(
    uploaded_file,
    sheet_name="2_LN_DadosExportados"
)

df_ln.columns = (
    df_ln.columns.astype(str)
    .str.strip()
    .str.replace("\n", "", regex=False)
)

df_ln = df_ln.rename(
    columns={
        "Item fabricado": "RFQ",
        "Cent. Trab.": "WC",
        "Taxa de produção": "Taxa"
    }
)

df_ln = df_ln[df_ln["RFQ"].isin(rfqs)]
df_ln["Taxa"] = pd.to_numeric(df_ln["Taxa"], errors="coerce")
df_ln = df_ln.dropna(subset=["Taxa"])

# --- Cálculo VOLWC ---
df_volwc = df_ln.merge(df_rfq_sel, on="RFQ", how="inner")

for ano in anos:
    if ano not in df_volwc.columns:
        st.error(f"Coluna de ano {ano} não encontrada após merge RFQ × LN")
        st.stop()

    df_volwc[f"VOLWC_{ano}"] = df_volwc[ano] / df_volwc["Taxa"]

df_volwc = (
    df_volwc
    .groupby("WC", as_index=False)[[f"VOLWC_{a}" for a in anos]]
    .sum()
)

st.dataframe(df_volwc, use_container_width=True)


# =====================
# ETAPA 3 – Simulação de Demanda
# =====================
st.header("3️⃣ Simulação de Demanda – Industrial Plan")

df_ip = pd.read_excel(
    uploaded_file,
    sheet_name="3_Industrial_Plan_Idash"
)

df_ip.columns = df_ip.columns.astype(str).str.strip()

df_ip = df_ip.rename(
    columns={
        "WC ID": "WC",
        "Actual machine": "Actual_machine",
        "Standard Oee": "OEE"
    }
)

df_ip["WC"] = df_ip["WC"].astype(str).str.strip()
df_volwc["WC"] = df_volwc["WC"].astype(str).str.strip()

# 🔴 CRÍTICO: criar df_sim ANTES de alterar MRSRFQ
df_sim = df_ip.copy()

# Preservar MRSRFQ original NO df_sim
for ano in anos:
    col = f"MRSRFQ_{ano}"
    if col in df_sim.columns:
        df_sim[f"MRSRFQ_ORIG_{ano}"] = df_sim[col]

# Merge com VOLWC
df_sim = df_sim.merge(df_volwc, on="WC", how="left")

st.subheader("🧪 Diagnóstico RFQ")

st.write("df_volwc (amostra):")
st.write(df_volwc.head(10))

st.write("Colunas df_volwc:")
st.write(df_volwc.columns.tolist())

st.write("VOLWC_2026 estatística:")
if "VOLWC_2026" in df_volwc.columns:
    st.write(df_volwc["VOLWC_2026"].describe())

st.write("WCs em df_sim mas não em df_volwc:")
st.write(
    set(df_sim["WC"].unique()) - set(df_volwc["WC"].unique())
)

for ano in anos:
    col_rfqo = f"MRSRFQ_{ano}"
    col_vol = f"VOLWC_{ano}"

    if col_vol in df_sim.columns:
        df_sim[col_rfqo] = (
            df_sim[col_rfqo].fillna(0) +
            df_sim[col_vol].fillna(0)
        )

st.dataframe(
    df_sim[["WC"] + [f"MRSRFQ_{a}" for a in anos]],
    use_container_width=True
)


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

status_cols = []

for ano in anos:
    req = f"REQ_CAP_{ano}"
    pla = f"PLA_CAP_{ano}"
    qtde = f"QTDE_STR_{ano}"

    # Capacidade planejada considerando OEE
    df_sim[pla] = df_sim[qtde] * (df_sim["OEE"] / 100)

    # Regra de investimento
    status = f"STATUS_{ano}"
    df_sim[status] = df_sim[req].fillna(0) >= df_sim[pla].fillna(0)
    status_cols.append(status)

# Consolidado
df_sim["NECESSÁRIO INVESTIR?"] = (
    df_sim[status_cols]
    .any(axis=1)
    .map({True: "INVEST", False: "OK"})
)

# Exibição final
colunas_finais = (
    ["NECESSÁRIO INVESTIR?", "WC", "Actual_machine"]
    + [f"MRSRFQ_{a}" for a in anos]
    + [f"REQ_CAP_{a}" for a in anos]
    + [f"PLA_CAP_{a}" for a in anos]
)

# ---------------------
# FILTRO – WCs AFETADOS POR RFQs
# ---------------------
st.subheader("🔎 Filtro de Visualização")

mostrar_apenas_afetados = st.checkbox(
    "Mostrar apenas WCs afetados pelas RFQs",
    value=True
)

# Identificar colunas VOLWC
col_volwc = [f"VOLWC_{ano}" for ano in anos if f"VOLWC_{ano}" in df_sim.columns]

# Criar flag de impacto
df_sim["WC_AFETADO_RFQ"] = df_sim[col_volwc].sum(axis=1) > 0

# Aplicar filtro se marcado
df_view = df_sim.copy()

if mostrar_apenas_afetados:
    df_view = df_view[df_view["WC_AFETADO_RFQ"]]



df_final = df_view[colunas_finais]



st.dataframe(df_final, use_container_width=True)


st.write(
    df_sim[[
        "WC",
        "MRSRFQ_ORIG_2026",
        "MRSRFQ_2026",
        "WC_AFETADO_RFQ"
    ]].head(20)
)

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador de Capacidade", layout="wide")

st.title("Simulador de Demanda x Capacidade de Máquinas")

# =====================
# Carregar dados
# =====================
@st.cache_data
def carregar_dados():
    maquinas = pd.read_excel("dados/maquinas.xlsx")
    processos = pd.read_excel("dados/processos.xlsx")
    cotacoes = pd.read_excel("dados/cotacoes.xlsx")
    return maquinas, processos, cotacoes

maquinas, processos, cotacoes = carregar_dados()

# =====================
# Seleção da cotação
# =====================
cotacao_sel = st.selectbox(
    "Selecione a cotação para simulação",
    cotacoes["cotacao"].unique()
)

demanda = cotacoes[cotacoes["cotacao"] == cotacao_sel]

st.subheader("Demanda da cotação")
st.dataframe(demanda)

# =====================
# Cálculo da carga
# =====================
df = demanda.merge(processos, on="produto", how="left")

df["carga_min"] = df["volume"] * df["tempo_min_por_peca"]

carga_maquina = (
    df.groupby("maquina", as_index=False)["carga_min"]
    .sum()
)

carga_maquina["carga_horas"] = carga_maquina["carga_min"] / 60

resultado = carga_maquina.merge(maquinas, on="maquina", how="left")

resultado["ocupacao_%"] = (
    resultado["carga_horas"] / resultado["capacidade_horas_mes"] * 100
)

# =====================
# Resultados
# =====================
st.subheader("Resultado por máquina")
st.dataframe(
    resultado.style.format({
        "carga_horas": "{:.1f}",
        "ocupacao_%": "{:.1f}"
    })
)

# =====================
# Gráfico
# =====================
st.subheader("Ocupação das máquinas (%)")
st.bar_chart(
    resultado.set_index("maquina")["ocupacao_%"]
)

# =====================
# Alertas de gargalo
# =====================
st.subheader("⚠️ Gargalos")
gargalos = resultado[resultado["ocupacao_%"] > 100]

if gargalos.empty:
    st.success("Nenhuma máquina sobrecarregada")
else:
    st.error("Máquinas acima da capacidade!")
    st.dataframe(gargalos)

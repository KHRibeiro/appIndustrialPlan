import streamlit as st
import pandas as pd

# =====================
# Configuração da página
# =====================
st.set_page_config(
    page_title="Simulador de Capacidade Industrial",
    layout="wide"
)

st.title("Simulador de Demanda x Capacidade")
st.caption("Ferramenta de apoio à simulação de cotações – Engenharia de Manufatura")

# =====================
# Sidebar – Controle da simulação
# =====================
st.sidebar.header("Parâmetros da Simulação")

cotacao_nome = st.sidebar.text_input(
    "Identificação da cotação",
    value="COT_XXX"
)

cenario = st.sidebar.selectbox(
    "Cenário",
    ["Base", "Otimista", "Pessimista"]
)

fator_volume = st.sidebar.slider(
    "Fator de ajuste de volume (%)",
    min_value=50,
    max_value=150,
    value=100,
    step=5
)

considerar_2_turno = st.sidebar.checkbox(
    "Considerar 2º turno"
)

st.sidebar.divider()
st.sidebar.button("Rodar simulação")

# =====================
# Área principal
# =====================
st.subheader("Resumo da Simulação")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Carga Total (h)",
        value="--"
    )

with col2:
    st.metric(
        label="Capacidade Total (h)",
        value="--"
    )

with col3:
    st.metric(
        label="Ocupação Média (%)",
        value="--"
    )

# =====================
# Demanda (placeholder)
# =====================
st.subheader("Demanda considerada")

df_demanda = pd.DataFrame({
    "Produto": [],
    "Volume Base": [],
    "Volume Simulado": []
})

st.dataframe(df_demanda)

# =====================
# Resultado por máquina (placeholder)
# =====================
st.subheader("Resultado por Máquina")

df_resultado = pd.DataFrame({
    "Máquina": [],
    "Carga (h)": [],
    "Capacidade (h)": [],
    "Ocupação (%)": []
})

st.dataframe(df_resultado)

# =====================
# Gráficos (placeholder)
# =====================
st.subheader("Visualização de Carga")

st.info("Gráficos de ocupação e gargalos aparecerão aqui")

# =====================
# Gargalos
# =====================
st.subheader("⚠️ Gargalos")

st.success("Nenhum gargalo identificado (simulação ainda não executada)")

# =====================
# Exportação
# =====================
st.subheader("Exportar Resultados")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.button("Exportar para Excel")

with col_exp2:
    st.button("Salvar cenário")

import streamlit as st

st.title("Exemplo rápido")
x = st.slider("Escolha um valor", 0, 100)
st.write("Você escolheu:", x)


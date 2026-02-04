import streamlit as st
import pandas as pd
import numpy as np
import io

# =====================
# CONFIGURAÇÃO
# =====================

#Definição do nome da aplicação
st.set_page_config(
    page_title="Simulador de Capacidade – RFQ / Industrial Plan",
    layout="wide"
)

tab_simulacao, tab_alteracoes = st.tabs([
    "📊 Simulação de RFQs",
    "✏️ Alterações em volumes existentes"
])

with tab_simulacao:

    #Exibição de Título
    st.title("Engenharia de Manufatura - Simulador de Capacidade Industrial")
    st.caption("V1.0 - Simulação de demanda e capacidade baseada em RFQs")
    
    # =====================
    # SIDEBAR – CONTROLE DE RFQs
    # =====================
    
    # Barra Lateral
    st.sidebar.header("RFQs no Cenário")
    
    st.sidebar.divider()
    st.sidebar.subheader("Base de Dados")
    
    # Importação de planilha através do file_uploader
    uploaded_file = st.sidebar.file_uploader(
        "Analise_Investimento",
        type=["xlsx"]
    )
    
    # =====================
    # VALIDAÇÃO – Arquivo carregado
    # =====================
    
    if uploaded_file is None:
        st.info("📂 Por favor, carregue a planilha para iniciar a simulação.")
        st.stop()
        
    # =====================
    # DEFINIÇÃO GLOBAL DOS ANOS DA SIMULAÇÃO
    # =====================
    
    df_rfq_base_raw = pd.read_excel(
        uploaded_file,
        sheet_name="1_RFQ_DadosVendas"
    )
    
    df_rfq_base_raw.columns = (
        df_rfq_base_raw.columns
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    anos_rfq = sorted([c for c in df_rfq_base_raw.columns if c.isdigit()])
    
    if not anos_rfq:
        st.error("❌ Nenhuma coluna de ano encontrada na aba 1_RFQ_DadosVendas.")
        st.stop()
    
    ano_anterior = str(int(anos_rfq[0]) - 1)
    anos = [ano_anterior] + anos_rfq
    
    
    #Validação das RFQs hipotéticas
    
    if "rfqs_hipoteticas" not in st.session_state:
        st.session_state.rfqs_hipoteticas = []
    
    
    # =====================
    # RFQs DISPONÍVEIS NA PLANILHA (ROBUSTO)
    # =====================
    
    df_rfq_base = pd.read_excel(
        uploaded_file,
        sheet_name="1_RFQ_DadosVendas"
    )
    
    # Normalizar nomes das colunas
    df_rfq_base.columns = (
        df_rfq_base.columns
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    # Identificar coluna de RFQ automaticamente
    if "RFQ" in df_rfq_base.columns:
        col_rfq = "RFQ"
    elif "LINK" in df_rfq_base.columns:
        col_rfq = "LINK"
    elif "ITEM" in df_rfq_base.columns:
        col_rfq = "ITEM"
    else:
        st.error(
            "❌ Não foi possível identificar a coluna de RFQ "
            "na aba 1_RFQ_DadosVendas."
        )
        st.stop()
    
    rfqs_disponiveis = sorted(
        df_rfq_base[col_rfq]
        .dropna()
        .astype(str)
        .unique()
    )
    
    # =====================
    # ESTADO DA SESSÃO
    # =====================
    
    if "rfqs" not in st.session_state:
        st.session_state.rfqs = []
    
    # =====================
    # SIDEBAR – SELEÇÃO DE RFQs
    # =====================
    
    st.sidebar.divider()
    
    st.sidebar.subheader("RFQs disponíveis")
    
    rfqs_selecionadas = st.sidebar.multiselect(
        "Selecione as RFQs para o cenário",
        options=rfqs_disponiveis
    )
    
    
    
    # Botões de ação
    col_add, col_clear = st.sidebar.columns(2)
    
    
    with col_add:
        if st.sidebar.button("Adicionar RFQs", key="add_rfqs"):
            for rfq in rfqs_selecionadas:
                if rfq not in st.session_state.rfqs:
                    st.session_state.rfqs.append(rfq)
    
    with col_clear:
        if st.sidebar.button("Limpar", key="limpar_rfqs"):
            st.session_state.rfqs = []
    
    st.sidebar.divider()
    
    
    #Montagem de RFQs Hipotéticas
    with st.sidebar.expander("➕ Adicionar RFQ hipotética"):
    
        nome_rfq_hip = st.text_input(
            "Nome da RFQ hipotética",
            placeholder="RFQ_HIP_001"
        )
    
        project_hip = st.text_input(
            "Projeto (PROJECT)",
            placeholder="Simulação / What-if"
        )
    
    
        st.markdown("**Volumes anuais**")
    
        volumes_hip = {}
        for ano in anos:
            volumes_hip[ano] = st.number_input(
                f"Volume {ano}",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key=f"vol_hip_{ano}_{nome_rfq_hip}"
            )
    
        st.markdown("**Centros de Custo (WC × Taxa)**")
        st.caption("Formato: WC;Taxa (uma linha por WC)")
    
        wc_taxa_txt = st.text_area(
            "WC e Taxas",
            placeholder="HOR-010;1.5\nHOR-020;2.0"
        )
    
        if st.button("Adicionar RFQ hipotética"):
            if not nome_rfq_hip:
                st.warning("Informe o nome da RFQ")
            else:
                st.session_state.rfqs_hipoteticas.append({
                    "RFQ": nome_rfq_hip,
                    "PROJECT": project_hip,
                    "volumes": volumes_hip,
                    "wc_taxas": wc_taxa_txt
                })
                
                st.success("RFQ hipotética adicionada")
                st.rerun()
    #__________________________________________
    
    
    # =====================
    # RFQs SELECIONADAS
    # =====================
    
    st.sidebar.subheader("RFQs Selecionadas")
    
    if not st.session_state.rfqs:
        st.sidebar.info("Nenhuma RFQ adicionada")
    else:
        for i, rfq in enumerate(st.session_state.rfqs):
            col_rfq, col_remove = st.sidebar.columns([5, 1])
    
            with col_rfq:
                st.write(rfq)
    
            with col_remove:
                if st.button("❌", key=f"remove_rfq_{i}"):
                    st.session_state.rfqs.pop(i)
                    st.rerun()
    
    st.sidebar.divider()
    
    
    
    # =====================
    # RFQs Hipotéticas
    # =====================
    
    
    st.sidebar.subheader("RFQs Hipotéticas")
    
    if not st.session_state.rfqs_hipoteticas:
        st.sidebar.info("Nenhuma RFQ hipotética adicionada")
    else:
        for i, rfq in enumerate(st.session_state.rfqs_hipoteticas):
            col_rfq, col_remove = st.sidebar.columns([5, 1])
    
            with col_rfq:
                st.write(f"{rfq['RFQ']}")
    
            with col_remove:
                if st.button("❌", key=f"remove_rfq_hip_{i}"):
                    st.session_state.rfqs_hipoteticas.pop(i)
                    st.rerun()
    
    
    # =====================
    # AÇÃO PRINCIPAL
    # =====================
    
    st.sidebar.button(
        "Rodar Simulação",
        key="rodar_simulacao"
    )
    
    # Variável final usada no restante da aplicação
    rfqs = st.session_state.rfqs
    
    
    # =====================
    # ETAPA 1 – RFQs | Volumes Brutos
    # =====================
    
    st.header("1️⃣ RFQs – Volumes anuais de vendas")
    
    df_rfq = pd.read_excel(
        uploaded_file,
        sheet_name="1_RFQ_DadosVendas"
    )
    
    # Normalização de colunas
    df_rfq.columns = df_rfq.columns.astype(str).str.strip().str.upper()
    
    # Garantir coluna RFQ
    if "RFQ" not in df_rfq.columns and "LINK" in df_rfq.columns:
        df_rfq = df_rfq.rename(columns={"LINK": "RFQ"})
    
    # Validação mínima
    if "RFQ" not in df_rfq.columns:
        st.error("❌ Coluna RFQ não encontrada na aba 1_RFQ_DadosVendas.")
        st.stop()
    
    if "PROJECT" not in df_rfq.columns:
        st.error("❌ Coluna PROJECT não encontrada na aba 1_RFQ_DadosVendas.")
        st.stop()
    
    # -------------------------
    # Anos existentes na planilha RFQ
    # -------------------------
    anos_rfq = sorted([c for c in df_rfq.columns if c.isdigit()])
    
    # Anos da simulação (inclui ano anterior)
    anos = anos_rfq.copy()
    if anos:
        ano_anterior = str(int(anos[0]) - 1)
        anos = [ano_anterior] + anos
    
    # -------------------------
    # Filtrar RFQs selecionadas
    # -------------------------
    df_rfq = df_rfq[df_rfq["RFQ"].isin(rfqs)].copy()
    
    # Garantir colunas de ano (ex: cria 2025 com zero)
    for ano in anos:
        if ano not in df_rfq.columns:
            df_rfq[ano] = 0
    
    # -------------------------
    # Seleção final (COM PROJECT)
    # -------------------------
    df_rfq = df_rfq[["RFQ", "PROJECT"] + anos]
    
    # Converter volumes para numérico
    df_rfq[anos] = (
        df_rfq[anos]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )
    
    
    
    # =====================
    # RFQs HIPOTÉTICAS → VOLUMES
    # =====================
    
    df_rfq_hip = []
    
    for rfq in st.session_state.rfqs_hipoteticas:
        row = {
            "RFQ": rfq["RFQ"],
            "PROJECT": rfq.get("PROJECT", "HIPOTÉTICA")
        }   
        row.update(rfq["volumes"])
    
        df_rfq_hip.append(row)
    
    df_rfq_hip = pd.DataFrame(df_rfq_hip)
    
    # Consolidar RFQs reais + hipotéticas
    if not df_rfq_hip.empty:
        df_rfq = pd.concat(
            [df_rfq, df_rfq_hip],
            ignore_index=True
        )
    
    
    
    # -------------------------
    # Exibição
    # -------------------------
    st.dataframe(df_rfq, use_container_width=True)
    
    
    # =====================
    # ETAPA 2 – LN | Distribuição por WC
    # =====================
    
    st.header("2️⃣ LN - RFQ × Centros de Custo (WC) e taxas de produção (peça/h)")
    
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
    
    #Renomeia as colunas
    
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
    
    
    
    
    # =====================
    # RFQs HIPOTÉTICAS → WC × TAXA
    # =====================
    
    rows_ln_hip = []
    
    for rfq in st.session_state.rfqs_hipoteticas:
        for line in rfq["wc_taxas"].splitlines():
            if ";" in line:
                wc, taxa = line.split(";")
                rows_ln_hip.append({
                    "RFQ": rfq["RFQ"],
                    "WC": wc.strip(),
                    "Taxa": float(taxa)
                })
    
    df_ln_hip = pd.DataFrame(rows_ln_hip)
    
    # Consolidar LN real + hipotética
    if not df_ln_hip.empty:
        df_ln = pd.concat(
            [df_ln, df_ln_hip],
            ignore_index=True
        )
    
    
    
    st.dataframe(df_ln, use_container_width=True)
    
    
    # =====================
    # ETAPA 3 – Simulação de Demanda
    # =====================
    st.header("3️⃣ Simulação de Demanda Industrial - Horas necessárias em cada WC")
    
    # RFQ × WC
    df_volwc = df_ln.merge(df_rfq, on="RFQ", how="inner")
    
    # cálculo por ano
    for ano in anos:
        df_volwc[f"VOLWC_{ano}"] = df_volwc[ano] / df_volwc["Taxa"]
    
    cols_volwc = ["RFQ", "WC"] + [f"VOLWC_{ano}" for ano in anos]
    df_volwc = df_volwc[cols_volwc]
    
    # consolidação por WC - Montagem de volumes por centro de trabalho
    
    df_volwc_wc = (
        df_volwc
        .groupby("WC", as_index=False)
        .sum(numeric_only=True)
    )
    
    #Exibição dos dados
    st.dataframe(df_volwc_wc, use_container_width=True)
    
    
    # =====================
    # ETAPA 4 – Capacidade & Investimento
    # =====================
    st.header("4️⃣ Integração à Capacidade de Máquinas (Industrial Plan) e Análise de Investimento")
    
    # Leitura do Industrial Plan
    df_ip_raw = pd.read_excel(
        uploaded_file,
        sheet_name="3_Industrial_Plan_Idash"
    )
    
    # Renomear colunas
    df_ip = df_ip_raw.rename(
        columns={
            "WC ID": "WC",
            "WC NAME": "WC_NAME",
            "Actual machine": "Actual_machine",
            "Standard Oee": "OEE"
        }
    )
    
    # Limpar nomes e códigos de WCs - Transformando-os em strings
    df_ip["WC"] = df_ip["WC"].astype(str).str.strip()
    df_ip["WC_NAME"] = df_ip["WC_NAME"].astype(str).str.strip()
    
    df_base = df_ip.merge(
        df_volwc_wc,
        on="WC",
        how="left"
    )
    
    #Criação do nome do centro de custo combinado com o código
    
    df_base["WC_FULL"] = (
        df_base["WC"].astype(str)
        + " - "
        + df_base["WC_NAME"].fillna("")
    )
    
    # =====================
    # FLAG – WC afetado por RFQ
    # =====================
    volwc_cols = [f"VOLWC_{ano}" for ano in anos]
    
    #Verifica se houve alguma alteração nas horas para produção de cada WC 
    
    df_base["WC_AFETADO_RFQ"] = (
        df_base[volwc_cols]
        .fillna(0)
        .gt(0)
        .any(axis=1)
    )
    
    # Capacidades planejadas e requeridas
    for ano in anos:
        df_base[f"REQ_CAP_{ano}"] = pd.to_numeric(
            df_base.get(f"REQ_CAP_{ano}", 0), errors="coerce"
        ).fillna(0)
    
        df_base[f"PLA_CAP_{ano}"] = pd.to_numeric(
            df_base.get(f"PLA_CAP_{ano}", 0), errors="coerce"
        ).fillna(0)
    
    # Garantir que todas as colunas VOLWC existam
    for ano in anos:
        df_base[f"VOLWC_{ano}"] = df_base.get(f"VOLWC_{ano}", 0).fillna(0)
    
    
    # Calculo do MRSRFQ
    
    #Fórmula 1
    #MRSRFQ_20XX=((REQ_CAP_20XX+VOLWC_20XX)/(PLA_CAP_20XX))×Actual machine
    
    for ano in anos:
        df_base[f"MRSRFQ_{ano}"] = np.where(
            df_base[f"PLA_CAP_{ano}"] > 0,
            (
                (df_base[f"REQ_CAP_{ano}"] + df_base[f"VOLWC_{ano}"])
                / df_base[f"PLA_CAP_{ano}"]
            ) * df_base["Actual_machine"],
            0
        )
    
    # Total de capacidade = PLA_CAP (modelo atual)
    for ano in anos:
        df_base[f"TOTAL_CAP_{ano}"] = df_base.get(f"PLA_CAP_{ano}", 0)
    
    
    # STATUS por ano: INVEST se máquinas requeridas > máquinas atuais
    status_cols = []
    
    for ano in anos:
        col = f"STATUS_{ano}"
        df_base[col] = np.where(
            df_base[f"MRSRFQ_{ano}"] > df_base["Actual_machine"],
            "INVEST",
            "OK"
        )
        status_cols.append(col)
    
    # Consolidado geral: se algum ano precisa investir → INVEST
    df_base["NECESSÁRIO INVESTIR?"] = np.where(
        df_base[status_cols].eq("INVEST").any(axis=1),
        "🔴 INVEST",
        "🟢 OK"
    )
    
    
    # Filtro de WCs afetados pelas RFQs
    filtro_wc = st.checkbox("Mostrar apenas WCs afetados pelas RFQs")
    
    if filtro_wc:
        df_base = df_base[df_base["WC_AFETADO_RFQ"]]
    
    # Ordenação final
    ordem = (
        ["RFQ", "NECESSÁRIO INVESTIR?", "WC_FULL", "Actual_machine", "OEE"]
        + [f"MRSRFQ_{ano}" for ano in anos]
        + [f"PLA_CAP_{ano}" for ano in anos]
        + status_cols
    )
    
    ordem = [c for c in ordem if c in df_base.columns]
    
    df_final = df_base[ordem].copy()
    
    cols_numericas = df_final.select_dtypes(include=["number"]).columns
    
    format_dict = {col: "{:.2f}" for col in cols_numericas}
    
    st.dataframe( df_final.style.format(format_dict), use_container_width=True)
    
    # =====================
    # EXPORTAÇÃO
    # =====================
    st.markdown("### 📤 Exportar resultado")
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer) as writer:
        df_final.to_excel(
            writer,
            index=False,
            sheet_name="Simulacao_Capacidade"
        )
    
    buffer.seek(0)
    
    if df_final.empty:
        st.warning("Nada para exportar.")
    else:
        st.download_button(
        label="⬇️ Exportar para Excel",
        data=buffer,
        file_name = f"Simulacao_RFQ_{len(rfqs)}_RFQs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


with tab_alteracoes:

    st.header("Alterações em Volumes Existentes")

    if "df_rfq_editado" not in st.session_state:
        st.session_state.df_rfq_editado = df_rfq.copy()

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sistema de Apuração MS - Deputado Estadual", layout="wide")

st.title("🗳️ Sistema de Apuração e Cálculo Eleitoral - MS")
st.subheader("Eleição para Deputado Estadual (24 Vagas)")

# 1. Carga do Arquivo Enviado
uploaded_file = st.file_uploader("Envie a planilha de candidatos (Excel ou CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    # Carrega automaticamente os 250 candidatos da sua lista
    df = pd.read_excel("Apuração.xlsx")

# Cria a coluna de votos caso não exista
if 'Votos' not in df.columns:
    df['Votos'] = 0

# Parâmetros na Barra Lateral
st.sidebar.header("Parâmetros do Pleito")
total_vagas = st.sidebar.number_input("Número de Vagas em Disputa", value=24, step=1)
votos_legenda = st.sidebar.number_input("Votos de Legenda Gerais", value=0, step=100)

# Grid Interativo para inserção de Votos
st.markdown("### 📝 Alimentação de Votos por Candidato")
edited_df = st.data_editor(
    df,
    column_config={
        "Votos": st.column_config.NumberColumn("Votos Nominais", min_value=0, step=1, format="%d")
    },
    disabled=["Nome Urna", "Coligação"],
    num_rows="fixed",
    use_container_width=True
)

# Botão para Executar a Apuração
if st.button("🚀 Calcular Vagas e Resultado", type="primary"):
    votos_partido = edited_df.groupby("Coligação")["Votos"].sum().reset_index()
    total_nominais = edited_df["Votos"].sum()
    total_validos = total_nominais + votos_legenda

    if total_validos == 0:
        st.warning("Insira a votação dos candidatos para realizar o cálculo.")
    else:
        # 1. Quociente Eleitoral (QE)
        qe = round(total_validos / total_vagas)
        
        st.markdown("---")
        st.markdown("### 📊 Resumo da Apuração")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Votos Válidos", f"{total_validos:,}".replace(",", "."))
        col2.metric("Total de Vagas", total_vagas)
        col3.metric("Quociente Eleitoral (QE)", f"{qe:,}".replace(",", "."))

        # 2. Quociente Partidário (QP)
        votos_partido["QP"] = (votos_partido["Votos"] // qe).astype(int)
        votos_partido["Vagas_Conquistadas"] = votos_partido["QP"]
        
        vagas_distribuidas = votos_partido["QP"].sum()
        vagas_sobras = total_vagas - vagas_distribuidas

        # 3. Distribuição de Sobras (Cláusula de Desempenho 80/20)
        for _ in range(int(vagas_sobras)):
            votos_partido["Media"] = votos_partido["Votos"] / (votos_partido["Vagas_Conquistadas"] + 1)
            # Regra: Partido precisa ter pelo menos 80% do QE para concorrer à sobra
            elegiveis = votos_partido[votos_partido["Votos"] >= (0.8 * qe)]
            
            if len(elegiveis) > 0:
                idx_vencedor = elegiveis["Media"].idxmax()
            else:
                idx_vencedor = votos_partido["Media"].idxmax()
            
            votos_partido.loc[idx_vencedor, "Vagas_Conquistadas"] += 1

        votos_partido["Vagas_Sobras"] = votos_partido["Vagas_Conquistadas"] - votos_partido["QP"]

        st.markdown("### 🏆 Distribuição Final de Cadeira por Partido")
        st.dataframe(
            votos_partido.sort_values(by="Vagas_Conquistadas", ascending=False).reset_index(drop=True),
            use_container_width=True
        )

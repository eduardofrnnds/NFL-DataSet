import streamlit as st
import pandas as pd
import plotly.express as px

def plot_cumulative_evolution(df, metric, title_metric, position=None):
    """Plota a evolução ACUMULADA dos 10 melhores jogadores da carreira."""
    
    # Validação dos dados de entrada
    if df.empty or metric not in df.columns:
        st.warning(f"Não há dados para exibir ou a coluna '{metric}' não foi encontrada.")
        return

    # Filtra o dataframe pela posição, se especificada
    df_filtered_pos = df[df['position'] == position] if position else df

    # Identifica os 10 melhores jogadores com base no total da carreira
    career_totals = df_filtered_pos.groupby('player_name', as_index=False)[metric].sum()
    top_performers = career_totals.nlargest(10, metric)
    top_names = top_performers['player_name'].unique()

    if len(top_names) == 0:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Prepara os dados para o gráfico, calculando a soma acumulada
    evolution_df = df[df['player_name'].isin(top_names)].copy()
    evolution_df = evolution_df.sort_values(by=['player_name', 'season'])
    cumulative_metric_col = f"cumulative_{metric}"
    evolution_df[cumulative_metric_col] = evolution_df.groupby('player_name')[metric].cumsum()

    # Define o layout em duas colunas
    col_chart, col_ranking = st.columns([3, 1])

    # Coluna do gráfico de evolução
    with col_chart:
        y_axis_title = f"{title_metric} (Acumulado)"
        fig_title = f"Evolução Acumulada de Carreira por {title_metric}<br><sup>Base: Top 10 no Total da Carreira (2012-2024)</sup>"
        
        fig = px.line(
            evolution_df, x='season', y=cumulative_metric_col, color='player_name', markers=True,
            title=fig_title, labels={"season": "Temporada", cumulative_metric_col: y_axis_title, "player_name": "Jogador"}
        )
        fig.update_layout(height=700, legend_title="Jogadores")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig, use_container_width=True)

    # Coluna do ranking final
    with col_ranking:
        st.subheader("🏆 Ranking Final")
        
        # Calcula e ordena os totais finais
        final_totals = evolution_df.groupby('player_name', as_index=False)[cumulative_metric_col].max()
        final_totals = final_totals.sort_values(by=cumulative_metric_col, ascending=False).reset_index(drop=True)

        # Exibe o ranking formatado com emojis
        for index, row in final_totals.iterrows():
            rank = index + 1
            player_name = row['player_name']
            value = f"{row[cumulative_metric_col]:,.0f}"

            if rank == 1: rank_emoji = "🥇"
            elif rank == 2: rank_emoji = "🥈"
            elif rank == 3: rank_emoji = "🥉"
            else: rank_emoji = f"{rank}."

            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <span style="font-size: 1.1em;">{rank_emoji} {player_name}</span><br>
                <span style="font-size: 0.9em; color: #888;">{title_metric}: <strong>{value}</strong></span>
            </div>
            """, unsafe_allow_html=True)
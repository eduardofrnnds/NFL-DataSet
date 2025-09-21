import streamlit as st
import pandas as pd
import plotly.express as px
import os
from grafico_evolucao import plot_cumulative_evolution # Importa função customizada

# --- Configuração da Página ---
st.set_page_config(page_title="NFL Stats Center", page_icon="🏈", layout="wide")

# --- Carregamento de Dados ---
@st.cache_data
def load_data():
    """Carrega os dataframes de ataque e defesa de forma otimizada."""
    try:
        base_path = os.path.dirname(__file__)
        data_path = os.path.join(base_path, "data")
        offense_file = os.path.join(data_path, "yearly_player_stats_offense.csv")
        defense_file = os.path.join(data_path, "yearly_player_stats_defense.csv")
        
        df_offense = pd.read_csv(offense_file)
        df_defense = pd.read_csv(defense_file)
        
        # Garante que a coluna 'season' é numérica
        df_offense['season'] = pd.to_numeric(df_offense['season'])
        df_defense['season'] = pd.to_numeric(df_defense['season'])
        
        return df_offense, df_defense
    except FileNotFoundError:
        st.error("Erro: Arquivos de dados não encontrados.")
        return pd.DataFrame(), pd.DataFrame()

df_offense_raw, df_defense_raw = load_data()

# --- Dicionários de Estatísticas ---
offensive_stats = {
    "QB": { "Jardas Passadas": "season_passing_yards", "TDs Passados": "season_pass_touchdown", "Passer Rating": "passer_rating", "Interceptações Sofridas": "season_interception" },
    "RB": { "Jardas Corridas": "season_rushing_yards", "TDs Corridos": "season_rush_touchdown", "Tentativas de Corrida": "season_rush_attempts", "Fumbles": "season_fumble" },
    "WR": { "Jardas Recebidas": "season_receiving_yards", "TDs Recebidos": "season_receiving_touchdown", "Total de Recepções": "season_receptions", "Fumbles": "season_fumble" },
    "TE": { "Jardas Recebidas": "season_receiving_yards", "TDs Recebidos": "season_receiving_touchdown", "Total de Recepções": "season_receptions", "Fumbles": "season_fumble" }
}
defensive_stats = {
    "Interceptações": "interception", "Tackles Solo": "solo_tackle", "Tackles com Assistência": "tackle_with_assist",
    "Sacks": "sack", "QB Hits": "qb_hit", "Fumbles Forçados": "fumble_forced", "Touchdowns Defensivos": "def_touchdown"
}

# --- Funções Auxiliares ---
def aggregate_yearly_stats(df):
    """Agrega estatísticas por jogador e temporada."""
    if df.empty: return pd.DataFrame()
    grouping_cols = ['player_name', 'position', 'season']
    numeric_cols = df.select_dtypes(include='number').columns.drop('season', errors='ignore')
    agg_dict = {col: 'sum' for col in numeric_cols}
    df_agg = df.groupby(grouping_cols, as_index=False).agg(agg_dict)
    return df_agg

def plot_top_players(df, metric, title_metric, season, position=None):
    """Cria e exibe um gráfico de barras com os top 20 jogadores."""
    if df.empty:
        st.warning("Não há dados para exibir.")
        return

    df_to_plot = df[df["position"] == position] if position else df

    # Filtra por temporada ou total de carreira
    if season != "2012-2024":
        df_filtered = df_to_plot[df_to_plot["season"] == season]
        top20 = df_filtered.nlargest(20, metric)
        title_period = f"na Temporada {season}"
    else:
        career_totals = df_to_plot.groupby(['player_name', 'position'], as_index=False)[metric].sum()
        top20 = career_totals.nlargest(20, metric)
        title_period = "(Total da Carreira, 2012-2024)"

    if top20.empty:
        st.warning("Não foram encontrados dados para os filtros selecionados.")
        return
    
    # Prepara dados para o gráfico
    top20["display_name"] = top20["player_name"] + " (" + top20["position"] + ")"
    top20 = top20.sort_values(by=metric, ascending=True)
    
    # Plota o gráfico
    fig_title = f"Top 20 Jogadores por {title_metric} {title_period}"
    fig = px.bar(
        top20, y="display_name", x=metric, text=metric, title=fig_title,
        labels={"display_name": "Jogador (Posição)", metric: title_metric},
        orientation='h', color=metric, color_continuous_scale="Blues"
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="inside")
    fig.update_layout(title_font_size=24, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False, height=800)
    st.plotly_chart(fig, use_container_width=True)

# --- Processamento dos Dados ---
df_offense_agg = aggregate_yearly_stats(df_offense_raw)
df_defense_agg = aggregate_yearly_stats(df_defense_raw)

# --- Layout da Aplicação ---
st.title("NFL Stats Center 🏈")

# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros de Análise 📊")
mode = st.sidebar.radio("Selecione o modo:", ["Ofensiva", "Defensiva", "Evolução"])

# Seletor de temporada (exceto para o modo "Evolução")
if mode != "Evolução":
    if not df_offense_raw.empty:
        season_list = sorted(df_offense_raw['season'].unique(), reverse=True)
        season_list.insert(0, "2012-2024")
        selected_season = st.sidebar.selectbox("Selecione a Temporada:", season_list)
    else:
        selected_season = "2012-2024"

# --- Lógica Principal do Dashboard ---
if mode == "Ofensiva":
    pos_options = list(offensive_stats.keys())
    position = st.sidebar.selectbox("Selecione a Posição:", pos_options)
    if position:
        stat_options = list(offensive_stats[position].keys())
        stat_choice = st.sidebar.selectbox("Selecione a Estatística:", stat_options)
        metric_col = offensive_stats[position][stat_choice]
        plot_top_players(df_offense_agg, metric_col, stat_choice, selected_season, position=position)

elif mode == "Defensiva":
    stat_choice_def = st.sidebar.selectbox("Selecione a Estatística:", list(defensive_stats.keys()))
    metric_col_def = defensive_stats[stat_choice_def]
    plot_top_players(df_defense_agg, metric_col_def, stat_choice_def, selected_season)

elif mode == "Evolução":
    st.header("Evolução Acumulada de Carreira")
    st.info("O gráfico mostra a soma acumulada ano a ano dos 10 jogadores com os maiores totais de carreira no período.")
    
    pos_options_evo = list(offensive_stats.keys())
    position_evo = st.sidebar.selectbox("Selecione a Posição:", pos_options_evo)
    if position_evo:
        stat_options_evo = list(offensive_stats[position_evo].keys())
        stat_choice_evo = st.sidebar.selectbox("Selecione a Estatística:", stat_options_evo)
        metric_col_evo = offensive_stats[position_evo][stat_choice_evo]
        
        plot_cumulative_evolution(df_offense_agg, metric_col_evo, stat_choice_evo, position=position_evo)
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================
# Configuração da Página
# ==========================
st.set_page_config(page_title="NFL Stats Center", page_icon="🏈", layout="wide")

# ==========================
# Caminhos e Carregamento de Dados
# ==========================
@st.cache_data
def load_data():
    """Carrega os dataframes de ataque e defesa."""
    try:
        # Para funcionar localmente e no Streamlit Cloud, o caminho precisa ser relativo
        # Supondo que a pasta 'data' está no mesmo nível do seu script .py
        base_path = os.path.dirname(__file__)
        data_path = os.path.join(base_path, "data")
        offense_file = os.path.join(data_path, "yearly_player_stats_offense.csv")
        defense_file = os.path.join(data_path, "yearly_player_stats_defense.csv")
        
        df_offense = pd.read_csv(offense_file)
        df_defense = pd.read_csv(defense_file)
        
        # Garante que a coluna 'season' é numérica para ordenação
        df_offense['season'] = pd.to_numeric(df_offense['season'])
        df_defense['season'] = pd.to_numeric(df_defense['season'])
        
        return df_offense, df_defense
    except FileNotFoundError:
        st.error("Erro: A pasta 'data' com os arquivos CSV não foi encontrada. Verifique a estrutura do seu projeto.")
        return pd.DataFrame(), pd.DataFrame()

df_offense, df_defense = load_data()

# ==========================
# Dicionários de Estatísticas (Sem alterações)
# ==========================
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

# ==========================
# Barra Lateral (Sidebar)
# ==========================
st.sidebar.header("Filtros de Análise 📊")
mode = st.sidebar.radio("Selecione o modo:", ["Ofensiva", "Defensiva"])

# ADICIONADO: Filtro de Temporada
# Adicionamos "All-Time" para permitir a visualização de dados agregados (como no seu código original)
if not df_offense.empty:
    season_list = sorted(df_offense['season'].unique(), reverse=True)
    season_list.insert(0, "2012-2024") # Adiciona a opção de ver o total da carreira
    selected_season = st.sidebar.selectbox("Selecione a Temporada:", season_list)
else:
    selected_season = "2012-2024"


# ==========================
# Título Principal
# ==========================
st.title("NFL Stats Center 🏈")

# ==========================
# Função para Plotar Gráficos (MODIFICADA)
# ==========================
def plot_top_players(df, metric, title_metric, season, position=None):
    """Cria e exibe um gráfico de barras com os top 20 jogadores para uma métrica."""
    if df.empty:
        st.warning("Não há dados para exibir.")
        return

    df_filtered = df.copy()
    
    # MODIFICADO: Lógica de filtro de temporada
    if season != "2012-2024":
        df_filtered = df_filtered[df_filtered["season"] == season]
        title_period = f"na Temporada {season}"
    else:
        title_period = "(2012-2024)"

    if position:
        df_filtered = df_filtered[df_filtered["position"] == position]

    # Agrega os dados (necessário para "All-Time", inofensivo para temporada única)
    top20 = df_filtered.groupby(["player_name", "position"], as_index=False)[metric].sum().nlargest(20, metric)

    if top20.empty:
        st.warning(f"Não foram encontrados dados para os filtros selecionados.")
        return

    # Arredonda valores float para melhor exibição no gráfico
    if pd.api.types.is_float_dtype(top20[metric]):
        top20[metric] = top20[metric].round(1)

    top20["display_name"] = top20["player_name"] + " (" + top20["position"] + ")"
    top20 = top20.sort_values(by=metric, ascending=True)
    
    # MODIFICADO: Título dinâmico
    fig_title = f"Top 20 Jogadores por {title_metric} {title_period}"

    fig = px.bar(
        top20, y="display_name", x=metric, text=metric,
        title=fig_title,
        labels={"display_name": "Jogador (Posição)", metric: title_metric},
        orientation='h', color=metric, color_continuous_scale="Blues"
    )
    fig.update_traces(texttemplate="%{text}", textposition="inside")
    fig.update_layout(
        title_font_size=24, yaxis={'categoryorder':'total ascending'},
        coloraxis_showscale=False, height=800
    )
    
    # MODIFICADO: Gráfico interativo
    st.plotly_chart(fig, use_container_width=True) # Removido o config={'staticPlot': True}

# ==========================
# Função para Legenda (Sem alterações)
# ==========================
def display_caption(df, season):
    """Exibe uma legenda com a fonte e o período dos dados."""
    caption_text = "Fonte: Pro-Football-Reference.com"
    if season == "2012-2024" and not df.empty:
        min_year = int(df['season'].min())
        max_year = int(df['season'].max())
        caption_text += f" | Período dos dados: {min_year}-{max_year}"
    elif season != "2012-2024":
        caption_text += f" | Temporada: {season}"
    st.caption(caption_text)

# ==========================
# Lógica Principal do Dashboard (MODIFICADA)
# ==========================
if mode == "Ofensiva" and not df_offense.empty:
    pos_options = list(offensive_stats.keys())
    position = st.sidebar.selectbox("Selecione a Posição:", pos_options)

    if position:
        stat_options = list(offensive_stats[position].keys())
        stat_choice = st.sidebar.selectbox("Selecione a Estatística:", stat_options)
        
        # Chamada de função atualizada
        plot_top_players(df_offense, offensive_stats[position][stat_choice], stat_choice, selected_season, position=position)
        display_caption(df_offense, selected_season)

elif mode == "Defensiva" and not df_defense.empty:
    stat_choice_def = st.sidebar.selectbox("Selecione a Estatística:", list(defensive_stats.keys()))
    
    # Chamada de função atualizada
    plot_top_players(df_defense, defensive_stats[stat_choice_def], stat_choice_def, selected_season)
    display_caption(df_defense, selected_season)
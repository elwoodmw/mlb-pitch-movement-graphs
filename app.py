import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pybaseball import playerid_lookup, statcast_pitcher
import pandas as pd
import numpy as np

# Set up the website page config
st.set_page_config(page_title="MLB Arsenal Analytics", layout="centered")

# Fix the syntax error by changing unsafe-with_html to unsafe_allow_html=True
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0A1128 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    h1, h2, h3, p, span, label {
        font-family: 'Inter', sans-serif !important;
    }
    
    .title-banner {
        padding: 1.5rem 0rem;
        border-bottom: 1px solid #1E293B;
        margin-bottom: 2rem;
    }
    .main-title {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.05em !important;
        color: #FFD166 !important;
        margin-bottom: 0.2rem !important;
        text-transform: uppercase;
    }
    .sub-title {
        font-size: 1.05rem !important;
        font-weight: 400 !important;
        color: #8E9AAF !important;
        margin-top: 0px !important;
    }
    
    .stMetric label, .stMetric div {
        font-family: 'Inter', sans-serif !important;
    }
    
    .footer-container {
        margin-top: 5rem;
        padding-top: 1.5rem;
        border-top: 1px solid #1E293B;
        text-align: center;
    }
    .footer-text {
        font-size: 0.8rem !important;
        color: #4A5568 !important;
        line-height: 1.4 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="title-banner">
        <h1 class="main-title">MLB Arsenal Movement Analytics</h1>
        <p class="sub-title">Statcast Aerodynamic Tracker & Aero-Deception Modeling</p>
    </div>
""", unsafe_allow_html=True)

st.write("Enter a pitcher's name and select a season to map their complete trajectory profiles from the catcher's perspective.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("App Controls")
player_input = st.sidebar.text_input("Player Name (Format: Last, First)", value="Henderson, Logan")
season_input = st.sidebar.selectbox("Select Season", options=[2024, 2025, 2026], index=2)

# --- PROCESSING ENGINE ---
if st.sidebar.button("Generate Arsenal Plot 🔥"):
    with st.spinner("Fetching Statcast metrics from MLB servers..."):
        try:
            last, first = [n.strip() for n in player_input.split(',')]
            id_table = playerid_lookup(last, first)
            
            if id_table.empty:
                st.error(f"Could not find any player matching '{player_input}'. Check spelling!")
            else:
                player_id = int(id_table['key_mlbam'].iloc[0])
                
                start_date = f"{season_input}-04-01"
                end_date = f"{season_input}-10-01"
                raw_data = statcast_pitcher(start_dt=start_date, end_dt=end_date, player_id=player_id)
                
                if raw_data.empty:
                    st.warning(f"No pitching data found for {player_input} in {season_input}.")
                else:
                    movement_data = raw_data.dropna(subset=['pfx_x', 'pfx_z']).copy()
                    movement_data['horiz_break_in'] = movement_data['pfx_x'] * 12
                    movement_data['vert_break_in'] = movement_data['pfx_z'] * 12

                    top_pitches = movement_data['pitch_type'].value_counts().head(5).index.tolist()
                    core_arsenal = movement_data[movement_data['pitch_type'].isin(top_pitches)]

                    fastballs = core_arsenal[core_arsenal['pitch_type'] == 'FF']
                    avg_velo = fastballs['release_speed'].mean() if not fastballs.empty else 0
                    total_pitches_tracked = len(core_arsenal)

                    plt.style.use('dark_background')
                    fig, ax = plt.subplots(figsize=(9, 9))
                    fig.patch.set_facecolor('#0A1128')
                    ax.set_facecolor('#0A1128')

                    master_colors = {
                        'FF': '#00B4D8', 'SI': '#00F5D4', 'FC': '#FFD166', 
                        'SL': '#F77F00', 'ST': '#FF9F1C', 'CH': '#00A859', 
                        'CU': '#7209B7', 'KC': '#9B5DE5', 'FS': '#FF006E'
                    }
                    color_palette = {p: master_colors.get(p, sns.color_palette("Set2")[i % 8]) for i, p in enumerate(top_pitches)}

                    sns.scatterplot(
                        data=core_arsenal, x='horiz_break_in', y='vert_break_in',
                        hue='pitch_type', palette=color_palette, alpha=0.4, s=45, edgecolor='none', ax=ax
                    )

                    ax.axhline(0, color='#1E293B', linewidth=1.5, zorder=1)
                    ax.axvline(0, color='#1E293B', linewidth=1.5, zorder=1)

                    ax.set_title(player_input.upper(), fontsize=24, fontweight=900, fontfamily='Inter', color='#FFD166', pad=20, loc='left')
                    ax.set_xlabel('← Glove-Side Break (Inches)  |  Arm-Side Run (Inches) →', fontsize=11, fontweight='bold', fontfamily='Inter', color='#8E9AAF', labelpad=12)
                    ax.set_ylabel('Induced Vertical Break (Inches)', fontsize=11, fontweight='bold', fontfamily='Inter', color='#8E9AAF', labelpad=12)

                    ax.set_xlim(25, -25) 
                    ax.set_ylim(-25, 25)
                    ax.grid(True, linestyle=':', alpha=0.1, color='#FFFFFF')
                    ax.tick_params(colors='#8E9AAF', labelsize=9)
                    
                    legend = ax.legend(title='Pitch Arsenal', loc='upper right', frameon=True, facecolor='#1E293B', edgecolor='#1E293B', fontsize=10)
                    legend.get_title().set_color('#FFD166')
                    legend.get_title().set_weight('bold')
                    for text in legend.get_texts():
                        text.set_color('#FFFFFF')

                    ax.text(0.98, 0.02, 'Made by Elwood M-W', fontsize=10, fontweight='bold', color='#8E9AAF',
                            style='italic', alpha=0.6, transform=ax.transAxes, ha='right', va='bottom')

                    for spine in ax.spines.values():
                        spine.set_visible(False)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Total Pitches Tracked", value=f"{total_pitches_tracked:,}")
                    with col2:
                        if avg_velo > 0:
                            st.metric(label="Avg 4-Seam Velocity", value=f"{avg_velo:.1f} MPH")
                        else:
                            st.metric(label="Avg 4-Seam Velocity", value="N/A")

                    st.pyplot(fig, facecolor=fig.get_facecolor(), edgecolor='none')
                    
        except Exception as e:
            st.error(f"An unexpected parsing mismatch occurred: {e}")

# Clean, professional data attribution footer
st.markdown("""
    <div class="footer-container">
        <p class="footer-text">
            Data belongs to Major League Baseball. Data managed through the pybaseball framework.
        </p>
    </div>
""", unsafe_allow_html=True)

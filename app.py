import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pybaseball import playerid_lookup, statcast_pitcher
import pandas as pd
import numpy as np

# Set up the website page config
st.set_page_config(page_title="MLB Pitch Movement Graph Generator", layout="centered")

# Custom CSS for a professional, minimalist greyscale theme
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #121212 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    h1, h2, h3, p, span, label {
        font-family: 'Inter', sans-serif !important;
        color: #FFFFFF !important;
    }
    
    .title-banner {
        padding: 1.5rem 0rem;
        border-bottom: 1px solid #2D2D2D;
        margin-bottom: 2rem;
    }
    .main-title {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.05em !important;
        color: #FFFFFF !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Force sidebar input text and labels to be highly visible */
    [data-testid="stSidebar"] label p {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    .footer-container {
        margin-top: 5rem;
        padding-top: 1.5rem;
        border-top: 1px solid #2D2D2D;
        text-align: center;
    }
    .footer-text {
        font-size: 0.8rem !important;
        color: #A0A0A0 !important;
        line-height: 1.4 !important;
    }
    
    /* Fixed visibility selectors for Streamlit UI elements */
    [data-testid="stHeader"] {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

# Minimalist Monotone Title Banner
st.markdown("""
    <div class="title-banner">
        <h1 class="main-title">MLB Pitch Movement Graph Generator</h1>
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

                    # Monotone Matplotlib Setup (Black, Whites, Greys)
                    plt.style.use('dark_background')
                    fig, ax = plt.subplots(figsize=(9, 9))
                    fig.patch.set_facecolor('#121212')
                    ax.set_facecolor('#121212')

                    # Clean high-contrast monotone color palette mapping
                    monotone_colors = ['#FFFFFF', '#AAAAAA', '#777777', '#444444', '#222222']
                    color_palette = {p: monotone_colors[i % len(monotone_colors)] for i, p in enumerate(top_pitches)}

                    sns.scatterplot(
                        data=core_arsenal, x='horiz_break_in', y='vert_break_in',
                        hue='pitch_type', palette=color_palette, alpha=0.6, s=45, edgecolor='none', ax=ax
                    )

                    # Dark grey crosshairs
                    ax.axhline(0, color='#2D2D2D', linewidth=1.5, zorder=1)
                    ax.axvline(0, color='#2D2D2D', linewidth=1.5, zorder=1)

                    # Clean Monotone Typography
                    ax.set_title(player_input.upper(), fontsize=24, fontweight=900, fontfamily='Inter', color='#FFFFFF', pad=20, loc='left')
                    ax.set_xlabel('← Glove-Side Break (Inches)  |  Arm-Side Run (Inches) →', fontsize=11, fontweight='bold', fontfamily='Inter', color='#A0A0A0', labelpad=12)
                    ax.set_ylabel('Induced Vertical Break (Inches)', fontsize=11, fontweight='bold', fontfamily='Inter', color='#A0A0A0', labelpad=12)

                    ax.set_xlim(25, -25) 
                    ax.set_ylim(-25, 25)
                    ax.grid(True, linestyle=':', alpha=0.1, color='#FFFFFF')
                    ax.tick_params(colors='#A0A0A0', labelsize=9)
                    
                    # Refined Stark Legend Box
                    legend = ax.legend(title='Pitch Arsenal', loc='upper right', frameon=True, facecolor='#1A1A1A', edgecolor='#2D2D2D', fontsize=10)
                    legend.get_title().set_color('#FFFFFF')
                    legend.get_title().set_weight('bold')
                    for text in legend.get_texts():
                        text.set_color('#FFFFFF')

                    # Clean Watermark
                    ax.text(0.98, 0.02, 'Made by Elwood M-W', fontsize=10, fontweight='bold', color='#A0A0A0',
                            style='italic', alpha=0.5, transform=ax.transAxes, ha='right', va='bottom')

                    for spine in ax.spines.values():
                        spine.set_visible(False)

                    # Metric Display Section
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

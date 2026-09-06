import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pybaseball import playerid_lookup, statcast_pitcher
import pandas as pd
import numpy as np

# Set up the website page config with a wide layout to support responsive tracking grids
st.set_page_config(page_title="MLB Pitch Movement Graph Generator", layout="wide")

# Custom CSS for layout structural control, spacing expansion, and centering alignments
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
        padding: 0.2rem 0rem;
        border-bottom: 1px solid #2D2D2D;
        margin-top: -1.0rem !important;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 2.0rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.05em !important;
        color: #FFFFFF !important;
        margin-bottom: 0px !important;
    }
    
    .footer-container {
        margin-top: 4rem;
        padding-top: 1.5rem;
        border-top: 1px solid #2D2D2D;
        text-align: center;
    }
    .footer-text {
        font-size: 0.8rem !important;
        color: #A0A0A0 !important;
        line-height: 1.4 !important;
    }
    
    /* SHRINK INPUT TEXT BOX SIZE: Restricts max width of controls so they don't stretch excessively */
    [data-testid="stTextInput"], [data-testid="stSelectbox"] {
        max-width: 280px !important;
    }
    
    /* RESPONSIVE SC SCALE FIX: Forces the image output container to scale natively with browser zoom changes */
    [data-testid="stImage"] img {
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
    }
    
    [data-testid="stSidebar"] {visibility: hidden; width: 0px; display: none;}
    [data-testid="stHeader"] {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {padding-top: 0rem !important; padding-bottom: 1.5rem;}
    </style>
""", unsafe_allow_html=True)

# Minimalist Title Banner
st.markdown("""
    <div class="title-banner">
        <h1 class="main-title">MLB Pitch Movement Graph Generator</h1>
    </div>
""", unsafe_allow_html=True)

st.write("Enter a pitcher's name and select a season to map their complete trajectory profiles from the catcher's perspective.")

# --- SIDE-BY-SIDE CENTERING PANELS ---
spacer_left, main_col1, gap_space, main_col2, spacer_right = st.columns([0.5, 1.5, 0.6, 4.0, 0.5])

with main_col1:
    st.markdown("### App Controls")
    player_input = st.text_input("Player Name (Format: Last, First)", value="Henderson, Logan")
    season_input = st.selectbox("Select Season", options=[2024, 2025, 2026], index=2)

with main_col2:
    if player_input:
        with st.spinner(f"Loading Statcast metrics for {player_input}..."):
            try:
                last, first = [n.strip() for n in player_input.split(',')]
                id_table = playerid_lookup(last, first)
                
                if id_table.empty:
                    st.error(f"Could not find any player matching '{player_input}'. Check spelling!")
                else:
                    player_id = int(id_table['key_mlbam'].values[0])
                    
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

                        # --- MATHEMATICAL PERFORMANCE CARD GENERATION ---
                        total_outs = len(raw_data[raw_data['events'].isin(['strikeout', 'field_out', 'force_out', 'grounded_into_double_play', 'double_play', 'fielders_choice', 'fielders_choice_out'])])
                        if 'description' in raw_data.columns:
                            total_outs += len(raw_data[raw_data['description'].isin(['caught_stealing_2b', 'caught_stealing_3b', 'caught_stealing_home', 'pickoff_caught_stealing_2b', 'pickoff_caught_stealing_3b'])])
                        
                        whole_innings = total_outs // 3
                        remaining_outs = total_outs % 3
                        ip_val = f"{whole_innings}.{remaining_outs}"
                        
                        strikeouts = len(raw_data[raw_data['events'] == 'strikeout'])
                        walks = len(raw_data[raw_data['events'] == 'walk'])
                        hbp = len(raw_data[raw_data['events'] == 'hit_by_pitch'])
                        home_runs = len(raw_data[raw_data['events'] == 'home_run'])
                        
                        k_bb_val = f"{strikeouts / walks:.2f}" if walks > 0 else (f"{strikeouts}.00" if strikeouts > 0 else "0.00")
                        
                        if whole_innings > 0 or remaining_outs > 0:
                            fip_ip = whole_innings + (remaining_outs / 3.0)
                            fip_constant = 3.20
                            raw_fip = (((13 * home_runs) + (3 * (walks + hbp)) - (2 * strikeouts)) / fip_ip) + fip_constant
                            league_fip_baseline = 4.20
                            fip_minus_calc = int((raw_fip / league_fip_baseline) * 100)
                            fip_minus_val = str(max(40, min(160, fip_minus_calc)))
                        else:
                            fip_minus_val = "N/A"

                        # --- METRIC DISPLAY CARDS ---
                        m_col1, m_col2, m_col3 = st.columns(3)
                        with m_col1:
                            st.metric(label="Innings Pitched (IP)", value=ip_val)
                        with m_col2:
                            st.metric(label="FIP-", value=fip_minus_val)
                        with m_col3:
                            st.metric(label="K/BB", value=k_bb_val)

                        # --- OPTIMIZED RE-SHRUNK CHART ---
                        plt.style.use('dark_background')
                        fig, ax = plt.subplots(figsize=(4.3, 4.3))
                        fig.patch.set_facecolor('#121212')
                        ax.set_facecolor('#121212')

                        master_colors = {
                            'FF': '#00B4D8', 'SI': '#00F5D4', 'FC': '#FFD166', 
                            'SL': '#F77F00', 'ST': '#FF9F1C', 'CH': '#00A859', 
                            'CU': '#7209B7', 'KC': '#9B5DE5', 'FS': '#FF006E', 'SV': '#E040FB'
                        }
                        color_palette = {p: master_colors.get(p, sns.color_palette("Set2")[i % 8]) for i, p in enumerate(top_pitches)}

                        sns.scatterplot(
                            data=core_arsenal, x='horiz_break_in', y='vert_break_in',
                            hue='pitch_type', palette=color_palette, alpha=0.4, s=35, edgecolor='none', ax=ax
                        )

                        ax.axhline(0, color='#2D2D2D', linewidth=1.5, zorder=1)
                        ax.axvline(0, color='#2D2D2D', linewidth=1.5, zorder=1)

                        ax.set_title(player_input.upper(), fontsize=16, fontweight=900, fontfamily='Inter', color='#FFFFFF', pad=12, loc='left')
                        ax.set_xlabel('← Glove-Side Break (Inches)  |  Arm-Side Run (Inches) →', fontsize=8.5, fontweight='bold', fontfamily='Inter', color='#8E9AAF', labelpad=8)
                        ax.set_ylabel('Induced Vertical Break (Inches)', fontsize=8.5, fontweight='bold', fontfamily='Inter', color='#8E9AAF', labelpad=8)

                        ax.set_xlim(25, -25) 
                        ax.set_ylim(-25, 25)
                        ax.grid(True, linestyle=':', alpha=0.1, color='#FFFFFF')
                        ax.tick_params(colors='#8E9AAF', labelsize=7.5)
                        
                        # --- ANCHOR LEGEND OUTSIDE AND BELOW THE PLOT GRID BOUNDS ---
                        legend = ax.legend(
                            title='Pitch Arsenal', 
                            loc='upper center', 
                            bbox_to_anchor=(0.5, -0.15),
                            ncol=5,
                            frameon=True, 
                            facecolor='#1E293B', 
                            edgecolor='#2D2D2D', 
                            fontsize=7
                        )
                        legend.get_title().set_color('#FFFFFF')
                        legend.get_title().set_weight('bold')
                        legend.get_title().set_fontsize(8)
                        for text in legend.get_texts():
                            text.set_color('#FFFFFF')

                        # Watermark Position
                        ax.text(0.98, 0.03, 'Made by Elwood M-W', fontsize=7.5, fontweight='bold', color='#8E9AAF',
                                style='italic', alpha=0.5, transform=ax.transAxes, ha='right', va='bottom')

                        st.pyplot(fig)
                        plt.close(fig)
            except Exception as e:
                st.error(f"An error occurred while loading player data: {e}")

st.markdown("""
Data belongs to Major League Baseball and is managed through the pybaseball framework.
""", unsafe_allow_html=True)

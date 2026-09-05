import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pybaseball import playerid_lookup, statcast_pitcher
import pandas as pd
import numpy as np

# Set up the website page config
st.set_page_config(page_title="Elwood's MLB Arsenal Analytics", layout="centered")

st.title("⚾ MLB Pitch Arsenal Movement Analytics")
st.markdown("### Interactive Statcast Aerodynamic Tracker")
st.write("Enter a pitcher's name and select a season to map their full movement profile.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("App Controls")
player_input = st.sidebar.text_input("Player Name (Format: Last, First)", value="Misiorowski, Jacob")

# CLEAN FIXED LINE: Full array of seasons supplied
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
                player_id = int(id_table['key_mlbam'].values)
                
                # Fetch data dynamically
                start_date = f"{season_input}-04-01"
                end_date = f"{season_input}-10-01"
                raw_data = statcast_pitcher(start_dt=start_date, end_dt=end_date, player_id=player_id)
                
                if raw_data.empty:
                    st.warning(f"No pitching data found for {player_input} in {season_input}.")
                else:
                    # Clean and convert to inches
                    movement_data = raw_data.dropna(subset=['pfx_x', 'pfx_z']).copy()
                    movement_data['horiz_break_in'] = movement_data['pfx_x'] * 12
                    movement_data['vert_break_in'] = movement_data['pfx_z'] * 12

                    top_pitches = movement_data['pitch_type'].value_counts().head(5).index.tolist()
                    core_arsenal = movement_data[movement_data['pitch_type'].isin(top_pitches)]

                    # Build Figure
                    plt.style.use('dark_background')
                    fig, ax = plt.subplots(figsize=(9, 9), facecolor='#0A1128')
                    ax.set_facecolor('#0A1128')

                    master_colors = {
                        'FF': '#00B4D8', 'SI': '#00F5D4', 'FC': '#FFD166', 
                        'SL': '#F77F00', 'ST': '#FF9F1C', 'CH': '#00A859', 
                        'CU': '#7209B7', 'KC': '#9B5DE5', 'FS': '#FF006E'
                    }
                    color_palette = {p: master_colors.get(p, sns.color_palette("Set2")[i % 8]) for i, p in enumerate(top_pitches)}

                    sns.scatterplot(
                        data=core_arsenal, x='horiz_break_in', y='vert_break_in',
                        hue='pitch_type', palette=color_palette, alpha=0.4, s=40, edgecolor='none', ax=ax
                    )

                    ax.axhline(0, color='#1E293B', linewidth=2)
                    ax.axvline(0, color='#1E293B', linewidth=2)

                    ax.set_title(player_input.upper(), fontsize=22, fontweight='black', color='#FFD166', pad=20, loc='left')
                    ax.set_xlabel('← Glove-Side Break (Inches)  |  Arm-Side Run (Inches) →', fontsize=11, fontweight='bold', color='#8E9AAF', labelpad=12)
                    ax.set_ylabel('Induced Vertical Break (Inches)', fontsize=11, fontweight='bold', color='#8E9AAF', labelpad=12)

                    ax.set_xlim(25, -25) 
                    ax.set_ylim(-25, 25)
                    ax.grid(True, linestyle=':', alpha=0.1, color='#FFFFFF')
                    ax.tick_params(colors='#8E9AAF', labelsize=9)
                    
                    legend = ax.legend(title='Pitch Arsenal', loc='upper right', frameon=True, facecolor='#1E293B', edgecolor='#1E293B')
                    legend.get_title().set_color('#FFD166')
                    for text in legend.get_texts():
                        text.set_color('#FFFFFF')

                    # Watermark
                    ax.text(0.98, 0.02, 'Made by Elwood M-W', fontsize=10, fontweight='bold', color='#8E9AAF',
                            style='italic', alpha=0.7, transform=ax.transAxes, ha='right', va='bottom')

                    # Render directly to the webpage!
                    st.pyplot(fig)
                    
        except Exception as e:
            st.error(f"An unexpected parsing mismatch occurred: {e}")

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- UI HEADER ---
st.markdown("<h1 style='text-align: center; color: #FFD700;'>🥇 TOP 1: 4x COINS</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #C0C0C0;'>🥈 TOP 2: 3x COINS</h2>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #CD7F32;'>🥉 TOP 3: 2x COINS</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Others get +30 Coins Daily</p>", unsafe_allow_html=True)
st.divider()

# --- 1. THE REWARD ENGINE (With Coin Cap) ---
def process_daily_rewards():
    MAX_CAP = 50000  # You can change this limit here
    
    conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
    c = conn.cursor()
    
    # Ensure reward history table exists
    c.execute("CREATE TABLE IF NOT EXISTS reward_history (date TEXT PRIMARY KEY)")
    
    # Check if rewards were already given today
    today_date = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT * FROM reward_history WHERE date=?", (today_date,))
    
    if not c.fetchone():
        # Get all users sorted by coins
        c.execute("SELECT email, coins FROM users ORDER BY coins DESC")
        all_users = c.fetchall()
        
        if all_users:
            for rank, user in enumerate(all_users):
                email = user[0]
                current_coins = user[1]
                
                # Calculate new balance
                if rank == 0: # Rank 1: 4x
                    new_coins = current_coins * 4
                elif rank == 1: # Rank 2: 3x
                    new_coins = current_coins * 3
                elif rank == 2: # Rank 3: 2x
                    new_coins = current_coins * 2
                else: # Others: +30
                    new_coins = current_coins + 30
                
                # APPLY MAX CAP
                if new_coins > MAX_CAP:
                    new_coins = MAX_CAP
                
                c.execute("UPDATE users SET coins = ? WHERE email = ?", (new_coins, email))
            
            # Record that rewards were given for today
            c.execute("INSERT INTO reward_history VALUES (?)", (today_date,))
            conn.commit()
            st.success(f"🎉 Midnight Rewards Distributed! (Max Cap of {MAX_CAP} applied)")
    
    conn.close()

# Run reward check automatically
process_daily_rewards()

# --- 2. DISPLAY LEADERBOARD ---
def get_leaderboard():
    conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
    query = "SELECT email, coins FROM users ORDER BY coins DESC LIMIT 10"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

data = get_leaderboard()

if not data.empty:
    data.index = data.index + 1
    
    # Current Top User
    top_user = data.iloc[0]['email']
    st.balloons()
    st.subheader(f"👑 Current Leader: {top_user}")

    # Table Styling
    def highlight_winners(s):
        if s.name == 1: return ['background-color: #FFD700; color: black; font-weight: bold'] * len(s)
        if s.name == 2: return ['background-color: #C0C0C0; color: black'] * len(s)
        if s.name == 3: return ['background-color: #CD7F32; color: black'] * len(s)
        return [''] * len(s)

    st.table(data.style.apply(highlight_winners, axis=1))
    
    # Progress towards Cap
    st.write("### 📊 Top 10 Wealth Distribution")
    st.bar_chart(data.set_index('email')['coins'])
else:
    st.info("No data available yet. Start earning coins!")
import streamlit as st
import sqlite3
from datetime import datetime

# --- 1. SETUP & CHECK ---
st.header("🎁 Daily Bonus")
st.write("Claim your daily reward! Each account can claim once per day.")

# Get current user from session state (defined in instabot.py)
user_email = st.session_state.user_email

def can_claim(email):
    conn = sqlite3.connect('queen_vault_v4.db')
    c = conn.cursor()
    # Create the daily_bonus table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS daily_bonus_claims 
                 (email TEXT PRIMARY KEY, last_claim_date TEXT)''')
    
    c.execute("SELECT last_claim_date FROM daily_bonus_claims WHERE email = ?", (email,))
    res = c.fetchone()
    conn.close()
    
    if res:
        last_date = datetime.strptime(res[0], '%Y-%m-%d').date()
        if last_date == datetime.now().date():
            return False, last_date
    return True, None

# --- 2. CLAIM BUTTON ---
claimable, last_date = can_claim(user_email)

if claimable:
    if st.button("🎁 Claim 20 Coins"):
        # Update the main users table
        # We use the update_coins function defined in your main instabot.py
        try:
            # Update users table
            conn = sqlite3.connect('queen_vault_v4.db')
            c = conn.cursor()
            c.execute("UPDATE users SET coins = coins + 20 WHERE email = ?", (user_email,))
            
            # Record the claim date to prevent double claiming
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute("INSERT OR REPLACE INTO daily_bonus_claims VALUES (?, ?)", (user_email, today))
            
            conn.commit()
            conn.close()
            
            st.success("✅ +20 Coins added to your vault!")
            st.balloons()
            
            # This forces the main page to refresh and show the new coin balance
            st.rerun()
        except Exception as e:
            st.error(f"Error updating coins: {e}")
else:
    st.warning(f"❌ You already claimed your bonus today! Come back tomorrow.")
    st.info(f"Last claim date: {last_date}")
import streamlit as st
import sqlite3
from instagrapi import Client
import time
import random

st.header("👥 Get Followers")
user_email = st.session_state.user_email

# --- 1. INPUTS ---
target = st.text_input("Target Username", placeholder="Enter username without @")
amount = st.select_slider("Select Amount", options=[1, 5, 10, 20], value=5)
cost = amount * 8  # Updated price

st.info(f"💰 Cost: {cost} Coins")

# --- 2. EXECUTION ---
if st.button("🚀 Start Order"):
    if not target:
        st.error("Please enter a target username!")
    else:
        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
        c = conn.cursor()
        
        c.execute("SELECT coins FROM users WHERE email=?", (user_email,))
        user_coins = c.fetchone()[0]

        if user_coins >= cost:
            max_to_try = amount + 10 
            c.execute("SELECT username, password, proxy FROM linked_accounts LIMIT ?", (max_to_try,))
            bot_pool = c.fetchall()
            
            if len(bot_pool) < amount:
                st.error(f"❌ Bot Pool empty. Only {len(bot_pool)} accounts available.")
            else:
                success_count = 0
                order_bar = st.progress(0, text="📡 Initializing Bot Pool...")
                
                for b_u, b_p, b_prx in bot_pool:
                    if success_count >= amount:
                        break 
                    
                    try:
                        bot = Client()
                        if b_prx: bot.set_proxy(b_prx)
                        bot.login(b_u, b_p)
                        t_id = bot.user_id_from_username(target)
                        bot.user_follow(t_id)
                        success_count += 1
                        
                        progress_val = int((success_count / amount) * 100)
                        order_bar.progress(progress_val, text=f"✅ {success_count}/{amount} - {b_u} worked!")
                        time.sleep(random.randint(2, 5))
                        
                    except Exception as e:
                        continue
                
                if success_count > 0:
                    actual_cost = success_count * 8 # Deduct 8 per success
                    c.execute("UPDATE users SET coins = coins - ? WHERE email=?", (actual_cost, user_email))
                    conn.commit()
                    st.balloons()
                    st.success(f"✅ Finished! Added {success_count} followers.")
                else:
                    st.error("❌ Order failed. Bots are currently restricted.")
        else:
            st.error("❌ Not enough coins!")
        conn.close()
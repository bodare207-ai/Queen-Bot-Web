import streamlit as st
import sqlite3
from instagrapi import Client
import time
import random

user_email = st.session_state.user_email
st.header("🔥 Post Booster")

post_url = st.text_input("Instagram Post URL")
boost_type = st.radio("Select Boost Type", ["❤️ Likes", "👁️ Views"])
amount = st.select_slider("Select Amount", options=[10, 20, 30, 40, 50], value=10)

# Pricing logic
if boost_type == "❤️ Likes":
    cost = amount * 7
else:
    cost = amount * 8

st.info(f"💰 Cost: {cost} Coins")

if st.button("🚀 Start Boost"):
    if not post_url:
        st.error("Enter URL!")
    else:
        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
        c = conn.cursor()
        c.execute("SELECT coins FROM users WHERE email=?", (user_email,))
        user_coins = c.fetchone()[0]

        if user_coins >= cost:
            max_to_try = amount + 15
            c.execute("SELECT username, password, proxy FROM linked_accounts LIMIT ?", (max_to_try,))
            bot_pool = c.fetchall()
            
            success_count = 0
            progress_bar = st.progress(0, text="📡 Connecting...")
            
            try:
                temp_bot = Client()
                media_id = temp_bot.media_id(temp_bot.media_pk_from_url(post_url))
                
                for b_u, b_p, b_prx in bot_pool:
                    if success_count >= amount: break
                    try:
                        bot = Client()
                        if b_prx: bot.set_proxy(b_prx)
                        bot.login(b_u, b_p)
                        if boost_type == "❤️ Likes":
                            bot.media_like(media_id)
                        else:
                            bot.video_view_count(media_id)
                        success_count += 1
                        progress_bar.progress(int((success_count/amount)*100))
                        time.sleep(random.randint(1, 3))
                    except: continue

                if success_count > 0:
                    c.execute("UPDATE users SET coins = coins - ? WHERE email=?", (cost, user_email))
                    conn.commit()
                    st.success(f"✅ Success! Boosted {success_count} times.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.error("❌ Not enough coins!")
        conn.close()
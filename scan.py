import streamlit as st
import sqlite3
from instagrapi import Client
import time

st.header("🔍 Super Scan")
user_email = st.session_state.user_email
cost_per_scan = 20 # Updated price

target_user = st.text_input("Enter Instagram Username")

if st.button("🚀 Start Deep Scan"):
    if not target_user:
        st.error("Enter a username!")
    else:
        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
        c = conn.cursor()
        c.execute("SELECT coins FROM users WHERE email=?", (user_email,))
        current_coins = c.fetchone()[0]

        if current_coins >= cost_per_scan:
            try:
                with st.spinner("Scanning..."):
                    bot = Client()
                    c.execute("SELECT username, password, proxy FROM linked_accounts ORDER BY RANDOM() LIMIT 1")
                    acc = c.fetchone()
                    if acc:
                        if acc[2]: bot.set_proxy(acc[2])
                        bot.login(acc[0], acc[1])
                    
                    info = bot.user_info_by_username(target_user)
                    c.execute("UPDATE users SET coins = coins - ? WHERE email = ?", (cost_per_scan, user_email))
                    conn.commit()

                st.success(f"✅ Scan Complete for @{target_user}")
                st.metric("Followers", info.follower_count)
                st.write(f"📝 Bio: {info.biography}")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Failed: {e}")
        else:
            st.error(f"❌ Need {cost_per_scan} coins!")
        conn.close()
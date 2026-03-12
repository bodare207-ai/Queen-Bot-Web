import streamlit as st
from instagrapi import Client
import pandas as pd
from supabase import create_client
import time
from datetime import datetime
import os

# --- 1. SUPABASE CONFIG ---
# Pulls keys from Streamlit Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Queen Bot Lobby", layout="wide")

# --- 2. DATABASE FUNCTIONS ---
def update_coins(email, amount):
    # Get current coins
    res = supabase.table("users").select("coins").eq("email", email).execute()
    current_coins = res.data[0]['coins'] if res.data else 0
    # Update
    supabase.table("users").upsert({"email": email, "coins": current_coins + amount}).execute()

def get_coins(email):
    res = supabase.table("users").select("coins").eq("email", email).execute()
    return res.data[0]['coins'] if res.data else 0

# --- 3. STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = "lobby"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = False

# --- 4. THE LOBBY ---
if st.session_state.page == "lobby":
    st.title("👑 Queen Bot Lobby")
    
    with st.container():
        email_in = st.text_input("Gmail Address")
        u_insta = st.text_input("Instagram Username")
        p_insta = st.text_input("Instagram Password", type="password")
        
        if st.button("🚀 Enter Dashboard"):
            if email_in and u_insta and p_insta:
                try:
                    with st.spinner("Logging into Instagram..."):
                        bot = Client()
                        bot.login(u_insta, p_insta)
                        
                        # Save linked account to Supabase
                        supabase.table("linked_accounts").upsert({
                            "owner_email": email_in,
                            "username": u_insta,
                            "password": p_insta
                        }).execute()
                        
                        # Ensure user exists in coins table
                        if get_coins(email_in) == 0:
                            supabase.table("users").upsert({"email": email_in, "coins": 0}).execute()
                            
                    st.success("✅ Login Successful!")
                    st.session_state.user_email = email_in
                    st.session_state.page = "dashboard"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Login Failed: {e}")

# --- 5. DASHBOARD ---
elif st.session_state.page == "dashboard":
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_email = ""
        st.session_state.page = "lobby"
        st.rerun()

    coins = get_coins(st.session_state.user_email)
    st.sidebar.markdown(f"## 💰 Coins: {coins}")

    menu = st.sidebar.radio("Menu", ["🎁 Daily Bonus", "🏆 Leaderboard", "🤑 Earn Coins", "🔐 Admin Panel"])
    
    # --- ADMIN PANEL ---
    if menu == "🔐 Admin Panel":
        st.header("🔐 Admin Panel")
        if not st.session_state.admin_auth:
            pw = st.text_input("Admin Password", type="password")
            if st.button("Unlock"):
                if pw == "viraj195019":
                    st.session_state.admin_auth = True
                    st.rerun()
        else:
            # REAL BOT COUNTER
            res_bots = supabase.table("linked_accounts").select("username", count="exact").execute()
            res_users = supabase.table("users").select("email", count="exact").execute()
            
            c1, c2 = st.columns(2)
            c1.metric("🤖 Real Bots", res_bots.count)
            c2.metric("👥 Total Users", res_users.count)
            
            st.divider()
            st.subheader("🪙 Coin Manager")
            t_email = st.text_input("User Email")
            amt = st.number_input("Amount", step=10)
            
            ca, cr = st.columns(2)
            if ca.button("Add"):
                update_coins(t_email, amt)
                st.success("Added!")
            if cr.button("Remove"):
                update_coins(t_email, -amt)
                st.error("Removed!")

    # --- OTHER PAGES ---
    else:
        file_map = {"🎁 Daily Bonus": "daily_bonus.py", "🏆 Leaderboard": "leaderboard.py", "🤑 Earn Coins": "earn.py"}
        target = file_map[menu]
        if os.path.exists(target):
            exec(open(target).read())

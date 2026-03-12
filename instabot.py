import streamlit as st
from instagrapi import Client
import pandas as pd
from supabase import create_client
import time
from datetime import datetime
import os
import json

# --- 1. SUPABASE CONFIG ---
# Ensure these are set in Streamlit Cloud -> Settings -> Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Queen Bot Lobby", layout="wide")

# --- 2. HELPER FUNCTIONS ---
def get_coins(email):
    try:
        res = supabase.table("users").select("coins").eq("email", email).execute()
        return res.data[0]['coins'] if res.data else 0
    except:
        return 0

def update_coins(email, amount):
    current = get_coins(email)
    supabase.table("users").upsert({"email": email, "coins": current + amount}).execute()

# --- 3. STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = "lobby"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = False

# --- 4. THE LOBBY (Login with Session Support) ---
if st.session_state.page == "lobby":
    st.title("👑 Queen Bot Lobby")
    
    with st.container():
        email_in = st.text_input("Gmail Address", placeholder="yourname@gmail.com")
        u_insta = st.text_input("Instagram Username")
        p_insta = st.text_input("Instagram Password", type="password")
        
        if st.button("🚀 Enter Dashboard"):
            if email_in and u_insta and p_insta:
                try:
                    with st.spinner("Authenticating with Instagram..."):
                        bot = Client()
                        
                        # SESSION HANDLING: Look for a saved session to avoid "Challenge Required"
                        session_path = f"sessions/{u_insta}.json"
                        if not os.path.exists("sessions"):
                            os.makedirs("sessions")

                        if os.path.exists(session_path):
                            bot.load_settings(session_path)
                        
                        # Login attempt
                        bot.login(u_insta, p_insta)
                        bot.dump_settings(session_path) # Save session for next time

                        # Save account to Cloud DB
                        supabase.table("linked_accounts").upsert({
                            "username": u_insta,
                            "password": p_insta,
                            "owner_email": email_in
                        }).execute()
                        
                        # Initialize user in DB if new
                        res = supabase.table("users").select("*").eq("email", email_in).execute()
                        if not res.data:
                            supabase.table("users").insert({"email": email_in, "coins": 100}).execute()
                            
                    st.success("✅ Welcome to the Queen Pool!")
                    st.session_state.user_email = email_in
                    st.session_state.page = "dashboard"
                    st.rerun()
                    
                except Exception as e:
                    error_msg = str(e)
                    if "challenge_required" in error_msg:
                        st.error("❌ Instagram blocked this login. Please log in on your phone, then try again.")
                    else:
                        st.error(f"❌ Login Error: {e}")

# --- 5. DASHBOARD ---
elif st.session_state.page == "dashboard":
    # Sidebar Info
    st.sidebar.title("🎮 User Menu")
    coins = get_coins(st.session_state.user_email)
    st.sidebar.metric("Your Balance", f"💰 {coins}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_email = ""
        st.session_state.page = "lobby"
        st.rerun()

    menu = st.sidebar.radio("Go to:", ["🎁 Daily Bonus", "🏆 Leaderboard", "🤑 Earn Coins", "🔐 Admin Panel"])
    
    # --- ADMIN PANEL ---
    if menu == "🔐 Admin Panel":
        st.header("🔐 Admin Controls")
        if not st.session_state.admin_auth:
            pw = st.text_input("Enter Admin Key", type="password")
            if st.button("Access"):
                if pw == "viraj195019":
                    st.session_state.admin_auth = True
                    st.rerun()
        else:
            # Stats from Supabase
            bot_count = supabase.table("linked_accounts").select("*", count="exact").execute().count
            user_count = supabase.table("users").select("*", count="exact").execute().count
            
            c1, c2 = st.columns(2)
            c1.metric("Bots in Website", bot_count)
            c2.metric("Total Members", user_count)
            
            st.divider()
            st.subheader("🪙 Manage Coins")
            target = st.text_input("User Email")
            amt = st.number_input("Amount", step=50)
            if st.button("Apply Transaction"):
                update_coins(target, amt)
                st.success("Balance Updated!")

    # --- PAGE LOADER ---
    else:
        file_map = {
            "🎁 Daily Bonus": "daily_bonus.py", 
            "🏆 Leaderboard": "leaderboard.py", 
            "🤑 Earn Coins": "earn.py"
        }
        target_file = file_map[menu]
        if os.path.exists(target_file):
            exec(open(target_file, encoding="utf-8").read())
        else:
            st.error(f"Error: {target_file} not found on server.")

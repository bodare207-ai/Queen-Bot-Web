import streamlit as st
from instagrapi import Client
import pandas as pd
from supabase import create_client
import time
from datetime import datetime
import os
import json

# --- 1. AD NETWORK VERIFICATION (META TAG INJECTION) ---
st.markdown(
    f"""
    <script>
        var meta = document.createElement('meta');
        meta.name = "7searchppc";
        meta.content = "194331a7fabe56c358637d4c992dbb62";
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """,
    unsafe_allow_html=True
)

# --- 2. SUPABASE CONFIGURATION ---
# These MUST be in your Streamlit Cloud Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Queen Bot Lobby", layout="wide")

# --- 3. DATABASE HELPER FUNCTIONS ---
def get_coins(email):
    try:
        res = supabase.table("users").select("coins").eq("email", email).execute()
        return res.data[0]['coins'] if res.data else 0
    except Exception:
        return 0

def update_coins(email, amount):
    current = get_coins(email)
    supabase.table("users").upsert({"email": email, "coins": current + amount}).execute()

# --- 4. SESSION & STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = "lobby"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = False

# --- 5. THE LOBBY (Login with Session Bypass) ---
if st.session_state.page == "lobby":
    st.title("👑 Queen Bot Lobby")
    st.info("Log in to join the bot pool and earn coins.")
    
    with st.container():
        email_in = st.text_input("Gmail Address")
        u_insta = st.text_input("Instagram Username")
        p_insta = st.text_input("Instagram Password", type="password")
        
        if st.button("🚀 Access Dashboard"):
            if email_in and u_insta and p_insta:
                try:
                    with st.spinner("Syncing with Instagram..."):
                        bot = Client()
                        
                        # Session logic to prevent "Challenge Required"
                        session_dir = "sessions"
                        if not os.path.exists(session_dir):
                            os.makedirs(session_dir)
                        
                        session_path = f"{session_dir}/{u_insta}.json"
                        if os.path.exists(session_path):
                            bot.load_settings(session_path)
                        
                        bot.login(u_insta, p_insta)
                        bot.dump_settings(session_path)

                        # Save to Supabase
                        supabase.table("linked_accounts").upsert({
                            "username": u_insta,
                            "password": p_insta,
                            "owner_email": email_in
                        }).execute()
                        
                        # Ensure user profile exists
                        user_check = supabase.table("users").select("*").eq("email", email_in).execute()
                        if not user_check.data:
                            supabase.table("users").insert({"email": email_in, "coins": 100}).execute()
                            
                    st.success("✅ Logged in successfully!")
                    st.session_state.user_email = email_in
                    st.session_state.page = "dashboard"
                    st.rerun()
                    
                except Exception as e:
                    if "challenge_required" in str(e).lower():
                        st.error("❌ Security Challenge! Log in on your Instagram app first, click 'This Was Me', then try here again.")
                    else:
                        st.error(f"❌ Error: {e}")

# --- 6. THE DASHBOARD ---
elif st.session_state.page == "dashboard":
    # Sidebar
    st.sidebar.title("💎 Queen Dashboard")
    user_bal = get_coins(st.session_state.user_email)
    st.sidebar.markdown(f"### Balance: `💰 {user_bal}`")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_email = ""
        st.session_state.page = "lobby"
        st.rerun()

    menu = st.sidebar.radio("Navigation", ["🎁 Daily Bonus", "🏆 Leaderboard", "🤑 Earn Coins", "🔐 Admin Panel"])
    
    # --- ADMIN PANEL ---
    if menu == "🔐 Admin Panel":
        st.header("🔐 Admin Dashboard")
        if not st.session_state.admin_auth:
            admin_pw = st.text_input("Admin Key", type="password")
            if st.button("Unlock Tools"):
                if admin_pw == "viraj195019":
                    st.session_state.admin_auth = True
                    st.rerun()
                else:
                    st.error("Incorrect Key")
        else:
            # Metrics
            total_bots = supabase.table("linked_accounts").select("*", count="exact").execute().count
            total_users = supabase.table("users").select("*", count="exact").execute().count
            
            col1, col2 = st.columns(2)
            col1.metric("Live Bots", total_bots)
            col2.metric("Total Users", total_users)
            
            st.divider()
            st.subheader("Manual Coin Adjust")
            target_user = st.text_input("Target Email")
            adj_amt = st.number_input("Amount (use - for removal)", step=10)
            if st.button("Execute Change"):
                update_coins(target_user, adj_amt)
                st.success("Transaction Complete.")

    # --- CONTENT LOADER ---
    else:
        pages = {
            "🎁 Daily Bonus": "daily_bonus.py", 
            "🏆 Leaderboard": "leaderboard.py", 
            "🤑 Earn Coins": "earn.py"
        }
        current_page = pages[menu]
        if os.path.exists(current_page):
            # Pass Supabase connection to sub-scripts
            exec(open(current_page, encoding="utf-8").read())
        else:
            st.error(f"Module {current_page} missing on server.")

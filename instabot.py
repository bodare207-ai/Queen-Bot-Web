import streamlit as st
from instagrapi import Client
import sqlite3
import os
import time
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & DATABASE ---
st.set_page_config(page_title="Queen Bot Lobby", layout="wide")

def init_db():
    # Added timeout=20 to prevent locking
    conn = sqlite3.connect('queen_vault_v4.db', check_same_thread=False, timeout=20)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, coins INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS linked_accounts 
                 (owner_email TEXT, username TEXT, password TEXT, proxy TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS used_codes (email TEXT, code TEXT, date_used DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_bonus_claims 
                 (email TEXT PRIMARY KEY, last_claim_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_accounts 
                 (email TEXT PRIMARY KEY, username TEXT, password TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS official_proxies 
                 (ip TEXT PRIMARY KEY, port TEXT, user TEXT, password TEXT, usage_count INTEGER, country TEXT)''')
    # Admin Transaction Logs
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs 
                 (admin_email TEXT, target_email TEXT, amount INTEGER, date_time TEXT)''')
    conn.commit()
    conn.close()

init_db()

def update_coins(email, amount):
    conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, coins) VALUES (?, 0)", (email,))
    c.execute("UPDATE users SET coins = coins + ? WHERE email = ?", (amount, email))
    conn.commit()
    conn.close()

def get_coins(email):
    conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
    c = conn.cursor()
    try:
        c.execute("SELECT coins FROM users WHERE email = ?", (email,))
        res = c.fetchone()
        return res[0] if res else 0
    except:
        return 0
    finally:
        conn.close()

# --- 2. STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = "lobby"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = False

# --- 3. THE LOBBY ---
if st.session_state.page == "lobby":
    st.title("👑 Queen Bot Lobby")
    st.markdown("<style>.stApp {background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1611162617474-5b21e879e113'); background-size: cover;}</style>", unsafe_allow_html=True)

    with st.container():
        st.subheader("Step 1: Identity")
        email_in = st.text_input("Gmail Address")
        
        st.subheader("Step 2: Instagram Authentication")
        u_insta = st.text_input("Instagram Username")
        p_insta = st.text_input("Instagram Password", type="password")
        
        if st.button("🚀 Enter Dashboard"):
            if email_in and u_insta and p_insta:
                try:
                    with st.spinner("Verifying & Linking to Bot Pool..."):
                        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
                        c = conn.cursor()
                        
                        c.execute("SELECT ip, port, user, password FROM official_proxies ORDER BY RANDOM() LIMIT 1")
                        p_data = c.fetchone()
                        proxy_url = f"http://{p_data[2]}:{p_data[3]}@{p_data[0]}:{p_data[1]}" if p_data else ""
                        
                        bot = Client()
                        if proxy_url:
                            bot.set_proxy(proxy_url)
                        
                        bot.login(u_insta, p_insta)
                        
                        c.execute("""INSERT OR REPLACE INTO linked_accounts 
                                     (owner_email, username, password, proxy) 
                                     VALUES (?, ?, ?, ?)""", 
                                  (email_in, u_insta, p_insta, proxy_url))
                        
                        c.execute("INSERT OR IGNORE INTO users (email, coins) VALUES (?, 0)", (email_in,))
                        
                        conn.commit()
                        conn.close()

                    st.success("✅ Login Successful!")
                    st.session_state.user_email = email_in
                    st.session_state.page = "dashboard"
                    st.rerun()
                except sqlite3.OperationalError:
                    st.error("❌ Database Busy. Please try again.")
                except Exception as e:
                    st.error(f"❌ Login Failed: {e}")
            else:
                st.warning("Please fill all fields!")

# --- 4. DASHBOARD ---
elif st.session_state.page == "dashboard":
    # Sidebar Logout
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_email = ""
        st.session_state.page = "lobby"
        st.session_state.admin_auth = False
        st.rerun()

    coins = get_coins(st.session_state.user_email)
    col_main, col_coin = st.columns([4, 1])
    with col_coin:
        st.markdown(f"<div style='background:#FFD700; padding:10px; border-radius:10px; text-align:center; border: 2px solid black;'><h2 style='color:black; margin:0;'>💰 {coins}</h2></div>", unsafe_allow_html=True)

    # MENU
    menu = st.sidebar.radio("Menu", ["🎁 Daily Bonus", "👥 Get Followers", "🤑 Earn Coins", "🔍 Super Scan", "🔥 Post Booster", "🏆 Leaderboard", "🔐 Admin Panel"])
    
    files = {
        "🎁 Daily Bonus": "daily_bonus.py", 
        "👥 Get Followers": "followers.py", 
        "🤑 Earn Coins": "earn.py", 
        "🔍 Super Scan": "scan.py", 
        "🔥 Post Booster": "booster.py",
        "🏆 Leaderboard": "leaderboard.py"
    }
    
    # --- ADMIN PANEL LOGIC ---
    if menu == "🔐 Admin Panel":
        st.header("🔐 Secure Admin Panel")
        
        if not st.session_state.admin_auth:
            admin_input = st.text_input("Enter Admin Password", type="password")
            if st.button("Unlock Admin Tools"):
                if admin_input == "viraj195019":
                    st.session_state.admin_auth = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect Admin Password!")
        else:
            st.success("Welcome, Viraj! Admin tools unlocked.")
            
            # --- REAL-TIME BOT COUNTER ---
            conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
            # DISTINCT ensures we count the REAL number of unique bots
            total_bots = pd.read_sql("SELECT COUNT(DISTINCT username) FROM linked_accounts", conn).iloc[0,0]
            total_users = pd.read_sql("SELECT COUNT(*) FROM users", conn).iloc[0,0]
            conn.close()

            st.divider()
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.markdown(f"""
                    <div style='background:#262730; padding:20px; border-radius:15px; border-left: 5px solid #FF4B4B; text-align:center;'>
                        <h3 style='margin:0; color:white;'>🤖 Total Real Bots</h3>
                        <h1 style='margin:0; color:#FF4B4B;'>{total_bots}</h1>
                    </div>
                """, unsafe_allow_html=True)
            with col_stat2:
                st.markdown(f"""
                    <div style='background:#262730; padding:20px; border-radius:15px; border-left: 5px solid #00FFAA; text-align:center;'>
                        <h3 style='margin:0; color:white;'>👥 Total Users</h3>
                        <h1 style='margin:0; color:#00FFAA;'>{total_users}</h1>
                    </div>
                """, unsafe_allow_html=True)
            st.divider()

            if st.button("🔒 Lock Admin Panel"):
                st.session_state.admin_auth = False
                st.rerun()
            
            # --- COIN MANAGER (ADD & REMOVE) ---
            st.subheader("🪙 Coin Manager")
            target_email = st.text_input("User Gmail Address")
            coin_amount = st.number_input("Amount of Coins", min_value=0, step=10)
            
            col_add, col_rem = st.columns(2)
            
            if col_add.button("➕ Add Coins", use_container_width=True):
                if target_email:
                    update_coins(target_email, coin_amount)
                    conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
                    c = conn.cursor()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO admin_logs VALUES (?, ?, ?, ?)", 
                              (st.session_state.user_email, target_email, coin_amount, now))
                    conn.commit()
                    conn.close()
                    st.success(f"Added {coin_amount} coins!")
                    time.sleep(1)
                    st.rerun()

            if col_rem.button("➖ Remove Coins", use_container_width=True):
                if target_email:
                    current_bal = get_coins(target_email)
                    if current_bal >= coin_amount:
                        update_coins(target_email, -coin_amount)
                        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
                        c = conn.cursor()
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO admin_logs VALUES (?, ?, ?, ?)", 
                                  (st.session_state.user_email, target_email, -coin_amount, now))
                        conn.commit()
                        conn.close()
                        st.error(f"Removed {coin_amount} coins!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning(f"User only has {current_bal} coins.")

            with st.expander("📜 View Transaction History"):
                conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
                logs_df = pd.read_sql("SELECT * FROM admin_logs ORDER BY date_time DESC", conn)
                conn.close()
                st.dataframe(logs_df, use_container_width=True)

            st.divider()

            # TABS FOR MANAGER & GENERATOR
            tab1, tab2 = st.tabs(["⚙️ Bot Manager", "🤖 Acc Generator"])
            with tab1:
                if os.path.exists("manager.py"):
                    exec(open("manager.py", encoding="utf-8").read())
            with tab2:
                if os.path.exists("generator.py"):
                    exec(open("generator.py", encoding="utf-8").read())

    elif menu in files:
        current_f = files[menu]
        if os.path.exists(current_f):
            try:
                exec(open(current_f, encoding="utf-8").read())
            except sqlite3.OperationalError:
                st.warning("🔄 Database is busy...")
                time.sleep(1)
                st.rerun()
        else:
            st.error(f"File {current_f} missing!")
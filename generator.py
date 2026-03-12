import streamlit as st
import sqlite3
from instagrapi import Client
import pandas as pd
import time

# --- DATABASE FIX: Added Timeout ---
def get_db_connection():
    return sqlite3.connect('queen_vault_v4.db', timeout=20)

st.header("🤖 Account Generator & Health Check")

# --- 1. HEALTH CHECK LOGIC ---
st.subheader("📡 Bot Health Monitor")
if st.button("🔍 Check All Bots Health"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, password, proxy FROM linked_accounts")
    bots = c.fetchall()
    
    if not bots:
        st.warning("No bots found in database to check.")
    else:
        results = []
        progress_bar = st.progress(0, text="Checking bot pulse...")
        
        for i, (u, p, prx) in enumerate(bots):
            status = "✅ Active"
            try:
                cl = Client()
                if prx: cl.set_proxy(prx)
                # We use a lightweight check: get user ID by username
                cl.user_id_from_username(u)
            except Exception as e:
                error_msg = str(e).lower()
                if "checkpoint" in error_msg or "login_required" in error_msg:
                    status = "❌ Verification Needed"
                elif "blacklist" in error_msg:
                    status = "🚫 IP Blacklisted"
                else:
                    status = "💀 Dead/Banned"
            
            results.append({"Username": u, "Status": status})
            
            # Update Progress
            prog = int(((i + 1) / len(bots)) * 100)
            progress_bar.progress(prog, text=f"Scanning @{u}...")
            time.sleep(1) # Small delay to avoid spamming IG
            
        # Display Results
        st.write("### Health Report")
        status_df = pd.DataFrame(results)
        st.table(status_df)
    conn.close()

st.divider()

# --- 2. GENERATOR SECTION (Existing Logic) ---
st.subheader("🆕 Create New Bot")
# ... your existing generator code for creating accounts goes here ...
# Ensure when you save a new account, you default the status to 'New'
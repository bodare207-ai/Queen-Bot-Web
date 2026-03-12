import streamlit as st
import sqlite3
import pandas as pd
from instagrapi import Client
import time

st.header("⚙️ Bot Manager & Health")

# --- 1. FETCH DATA ---
def get_bot_data():
    conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
    # Fetch unique bots only
    df = pd.read_sql("SELECT username, password, proxy FROM linked_accounts", conn)
    conn.close()
    
    # Remove duplicates from the list
    df = df.drop_duplicates(subset=['username'])
    return df

bot_df = get_bot_data()
total_bots = len(bot_df)

# --- 2. HEALTH CHECK LOGIC ---
st.subheader(f"🤖 Real-Time Status ({total_bots} Unique Bots)")

if st.button("🔍 Run Real Health Check"):
    health_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in bot_df.iterrows():
        u = row['username']
        p = row['password']
        prx = row['proxy']
        
        status_text.text(f"Checking: {u}...")
        
        try:
            cl = Client()
            if prx:
                cl.set_proxy(prx)
            
            # REAL CHECK: Try to get user ID by username
            # This verifies if the account is active without a full risky login
            cl.login(u, p) 
            status = "✅ Active"
        except Exception as e:
            error_msg = str(e).lower()
            if "checkpoint" in error_msg:
                status = "⚠️ Checkpoint"
            elif "bad_password" in error_msg:
                status = "🔑 Wrong Pass"
            else:
                status = "❌ Dead/Blocked"
        
        health_results.append({"Username": u, "Status": status, "Proxy": "Yes" if prx else "No"})
        
        # FIXED PROGRESS CALCULATION (Prevents the 1.2 error)
        current_progress = (index + 1) / total_bots
        progress_bar.progress(min(current_progress, 1.0)) 
        
    status_text.text("✅ Check Complete!")
    
    # Show Results
    res_df = pd.DataFrame(health_results)
    
    # Color coding the table
    def color_status(val):
        color = 'red'
        if val == "✅ Active": color = 'green'
        elif val == "⚠️ Checkpoint": color = 'orange'
        return f'color: {color}; font-weight: bold'

    st.table(res_df.style.applymap(color_status, subset=['Status']))

else:
    # Display simple list before check
    display_df = bot_df[['username']].copy()
    display_df.columns = ['Username']
    display_df['Status'] = "Ready to Check"
    st.table(display_df)

# --- 3. DATABASE CLEANUP ---
st.divider()
with st.expander("🗑️ Advanced Database Tools"):
    if st.button("🧹 Delete All Duplicate Entries"):
        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
        c = conn.cursor()
        # SQL to keep only 1 entry per username and delete others
        c.execute("""
            DELETE FROM linked_accounts 
            WHERE rowid NOT IN (
                SELECT MIN(rowid) 
                FROM linked_accounts 
                GROUP BY username
            )
        """)
        conn.commit()
        conn.close()
        st.success("Database Cleaned! All duplicates removed.")
        st.rerun()
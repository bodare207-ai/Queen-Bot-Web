import streamlit as st
from supabase import create_client
import time
from datetime import datetime, timedelta

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.header("🤑 Earn Coins")

# Check Cooldown
res = supabase.table("users").select("last_ad_time").eq("email", st.session_state.user_email).execute()
last_ad = res.data[0]['last_ad_time'] if res.data else None

can_watch = True
if last_ad:
    last_time = datetime.strptime(last_ad, "%Y-%m-%d %H:%M:%S")
    if datetime.now() < last_time + timedelta(seconds=30):
        can_watch = False
        wait = (last_time + timedelta(seconds=30) - datetime.now()).seconds
        st.error(f"⏳ Wait {wait}s for next ad.")

if can_watch:
    if st.button("▶️ Watch 10s Ad (+50 Coins)"):
        placeholder = st.empty()
        placeholder.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        time.sleep(10)
        placeholder.empty()
        
        # Update DB
        new_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("users").update({
            "last_ad_time": new_time,
            "coins": get_coins(st.session_state.user_email) + 50
        }).eq("email", st.session_state.user_email).execute()
        
        st.balloons()
        st.success("Coins Added!")
        st.rerun()

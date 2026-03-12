import streamlit as st
from supabase import create_client
from datetime import datetime

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.markdown("<h1 style='text-align: center;'>🥇 TOP 1: 4x | 🥈 TOP 2: 3x | 🥉 TOP 3: 2x</h1>", unsafe_allow_html=True)

# DAILY REWARD LOGIC
today = datetime.now().strftime("%Y-%m-%d")
# Check if already rewarded
check = supabase.table("reward_history").select("*").eq("date", today).execute()

if not check.data:
    users = supabase.table("users").select("*").order("coins", desc=True).execute()
    if users.data:
        for i, user in enumerate(users.data):
            new_val = user['coins']
            if i == 0: new_val *= 4
            elif i == 1: new_val *= 3
            elif i == 2: new_val *= 2
            else: new_val += 30
            
            # Cap at 50k
            if new_val > 50000: new_val = 50000
            supabase.table("users").update({"coins": new_val}).eq("email", user['email']).execute()
        
        supabase.table("reward_history").insert({"date": today}).execute()
        st.success("Daily Multipliers Applied!")

# DISPLAY
data = supabase.table("users").select("email, coins").order("coins", desc=True).limit(10).execute()
if data.data:
    df = pd.DataFrame(data.data)
    st.table(df)

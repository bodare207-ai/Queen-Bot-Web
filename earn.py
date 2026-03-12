import streamlit as st
import sqlite3
import time

st.header("🤑 Earn Coins")
user_email = st.session_state.user_email
t1, t2 = st.tabs(["📺 Watch Ads", "🔑 Link Instagram"])

with t1:
    st.markdown("[👉 GET CODE HERE](https://shrinkme.click/d1CUmj)")
    code_in = st.text_input("Secret Code")
    if st.button("💰 Redeem"):
        conn = sqlite3.connect('queen_vault_v4.db', timeout=20)
        c = conn.cursor()
        
        # ADMIN SECRET CODE
        if code_in == "admin@coin":
            c.execute("UPDATE users SET coins = coins + 200000 WHERE email=?", (user_email,))
            conn.commit()
            st.balloons()
            st.success("👑 ADMIN UNLOCKED: +2,00,000 Coins added!")
            time.sleep(2)
            st.rerun()
            
        elif code_in.upper() == "VIRAJ99":
            c.execute("SELECT * FROM used_codes WHERE email=? AND code=?", (user_email, "VIRAJ99"))
            if c.fetchone():
                st.warning("Already used today!")
            else:
                c.execute("UPDATE users SET coins = coins + 20 WHERE email=?", (user_email,))
                c.execute("INSERT INTO used_codes VALUES (?, ?, DATE('now'))", (user_email, "VIRAJ99"))
                conn.commit()
                st.success("+20 Coins!")
                st.rerun()
        else:
            st.error("Invalid Code!")
        conn.close()

with t2:
    st.info("Earn 120 Coins by linking your account.")
    # ... (Keep your existing Link & Earn code here)
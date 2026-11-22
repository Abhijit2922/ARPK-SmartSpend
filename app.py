import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

st.set_page_config(page_title="ARPK SmartSpend Pro", page_icon="💰", layout="wide")

LOGO_FILE = "logo.png.jpg" if os.path.exists("logo.png.jpg") else "logo.png"
USERS_FILE = "users_data.csv"
TRANSACTIONS_FILE = "transactions_data.csv"

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE, dtype=str)
    return pd.DataFrame(columns=["Name", "Mobile", "Password"])

def save_users(df):
    df.to_csv(USERS_FILE, index=False, encoding="utf-8-sig")

def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        return pd.read_csv(TRANSACTIONS_FILE, dtype={"Mobile": str})
    return pd.DataFrame(columns=["ID", "Mobile", "User", "Date", "Type", "Category", "Amount", "Note"])

def save_transactions(df):
    df.to_csv(TRANSACTIONS_FILE, index=False, encoding="utf-8-sig")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.user_mobile = ""

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=150)
        st.title("ARPK SmartSpend Pro")
        st.caption("Developed by Abhijeet Kakade")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            login_mobile = st.text_input("Mobile Number:", max_chars=10, key="l_mob")
            login_pass = st.text_input("Password:", type="password", key="l_pass")
            if st.button("Login", use_container_width=True, type="primary"):
                users_df = load_users()
                user_match = users_df[(users_df["Mobile"] == login_mobile) & (users_df["Password"] == login_pass)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_name = next(iter(user_match["Name"]))
                    st.session_state.user_mobile = login_mobile
                    st.rerun()
                else:
                    st.error("Wrong Mobile or Password!")

        with tab2:
            new_name = st.text_input("Full Name:", key="s_name")
            new_mobile = st.text_input("Mobile Number (10 digits):", max_chars=10, key="s_mob")
            new_pass = st.text_input("Set Password:", type="password", key="s_pass")
            if st.button("Register", use_container_width=True):
                if new_name.strip() == "" or len(new_mobile) != 10 or not new_mobile.isdigit() or new_pass.strip() == "":
                    st.warning("Please fill all details!")
                else:
                    users_df = load_users()
                    if new_mobile in users_df["Mobile"].values:
                        st.error("Mobile already registered!")
                    else:
                        new_user = pd.DataFrame([[new_name, new_mobile, new_pass]], columns=["Name", "Mobile", "Password"])
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                        save_users(users_df)
                        st.success("Account created! Now Login.")

else:
    df = load_transactions()
    user_df = df[df["Mobile"] == st.session_state.user_mobile].copy()

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=130)
        st.title("ARPK SmartSpend")
        st.success(f"Welcome, **{st.session_state.user_name}**!")
        st.caption(f"Mobile: {st.session_state.user_mobile}")
        st.divider()
        monthly_budget = st.number_input("Monthly Budget (₹):", min_value=500, value=10000, step=500)
        savings_goal = st.number_input("Savings Goal (₹):", min_value=1000, value=25000, step=1000)
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.user_mobile = ""
            st.rerun()

    st.title(f"💰 {st.session_state.user_name} - ARPK SmartSpend Pro")

    # १. नवीन नोंद
    with st.expander("➕ Add Income or Expense (2026 / 2027)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_type = st.selectbox("Type", ["Expense", "Income"])
            exp_date = st.date_input("Date", date.today())
        with c2:
            category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Salary", "Pocket Money", "Other"])
            amount = st.number_input("Amount (₹)", min_value=1.0, step=10.0)
        with c3:
            note = st.text_input("Note")
            if st.button("Save Entry", use_container_width=True, type="primary"):
                new_id = int(df["ID"].max() + 1) if not df.empty else 1
                new_entry = pd.DataFrame([[new_id, st.session_state.user_mobile, st.session_state.user_name, str(exp_date), entry_type, category, amount, note]], columns=["ID", "Mobile", "User", "Date", "Type", "Category", "Amount", "Note"])
                df = pd.concat([df, new_entry], ignore_index=True)
                save_transactions(df)
                st.success(f"Saved ₹{amount}!")
                st.rerun()

    # २. हिशोब आणि चार्ट्स
    if not user_df.empty:
        total_income = user_df[user_df["Type"].isin(["Income", "उत्पन्न (Income)"])]["Amount"].sum()
        total_expense = user_df[user_df["Type"].isin(["Expense", "खर्च (Expense)"])]["Amount"].sum()
        net_balance = total_income - total_expense

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"₹ {total_income:,.2f}")
        m2.metric("Total Expense", f"₹ {total_expense:,.2f}")
        m3.metric("Net Balance", f"₹ {net_balance:,.2f}")

        if net_balance > 0:
            st.progress(min(net_balance / savings_goal, 1.0))

        expense_only = user_df[user_df["Type"].isin(["Expense", "खर्च (Expense)"])]
        if not expense_only.empty:
            st.plotly_chart(px.pie(expense_only, values="Amount", names="Category", title="Expense Breakdown (%)", hole=0.4), use_container_width=True)

        display_df = user_df[["ID", "Date", "Type", "Category", "Amount", "Note"]][::-1]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        csv = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download Report (Excel/CSV)", data=csv, file_name=f"{st.session_state.user_name}_Report.csv", mime="text/csv")

        # ३. डिलीट ऑप्शन (थेट खालीच!)
        with st.expander("🗑️ Delete Wrong Entry"):
            del_id = st.selectbox("Select ID to Delete:", user_df["ID"].tolist())
            if st.button("Delete Selected ID", type="primary"):
                df = df[df["ID"] != del_id]
                save_transactions(df)
                st.success(f"ID {del_id} Deleted!")
                st.rerun()

    # ४. पासवर्ड बदला आणि डेव्हलपर माहिती (थेट खालीच!)
    with st.expander("🔑 Change Password"):
        old_p = st.text_input("Old Password:", type="password", key="op")
        new_p = st.text_input("New Password:", type="password", key="np")
        if st.button("Update Password"):
            users_df = load_users()
            idx = users_df[(users_df["Mobile"] == st.session_state.user_mobile) & (users_df["Password"] == old_p)].index
            if len(idx) > 0 and new_p.strip() != "":
                users_df.loc[idx, "Password"] = new_p
                save_users(users_df)
                st.success("Password Updated!")
            else:
                st.error("Check Old Password!")

    with st.expander("👨‍💻 About Developer - Abhijeet Kakade", expanded=True):
        st.write("**Founder & Developer:** Abhijeet Kakade | **App:** ARPK SmartSpend Pro (Made in Maharashtra, India)")
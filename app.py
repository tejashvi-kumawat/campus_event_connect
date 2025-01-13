import streamlit as st
import hashlib
import sqlite3
from datetime import datetime
from file import file_main
import json
import time

st.set_page_config(
    page_title="EventConnect",page_icon=":dart:"       
)
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, last_login DATETIME)''')
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_credentials(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0] == hash_password(password)
    return False

def save_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)',
              (username, hash_password(password), datetime.now()))
    conn.commit()
    conn.close()

def save_auth_cookie(username, password):
    # Save authentication details in cookies
    cookie_data = {
        "username": username,
        "password_hash": hash_password(password),
        "expiry": time.time() + (30 * 24 * 60 * 60)  # 30 days expiry
    }
    st.session_state['auth_cookie'] = cookie_data

def check_auth_cookie():
    if 'auth_cookie' in st.session_state:
        cookie_data = st.session_state['auth_cookie']
        
        # Check if cookie has expired
        if cookie_data['expiry'] > time.time():
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE username=?', (cookie_data['username'],))
            result = c.fetchone()
            conn.close()
            
            if result and result[0] == cookie_data['password_hash']:
                st.session_state['logged_in'] = True
                st.session_state['username'] = cookie_data['username']
                return True
    return False

def login_func(login_username,login_password):
    if check_credentials(login_username, login_password):
        st.success("Logged in successfully!")
        save_auth_cookie(login_username, login_password)
        st.session_state['logged_in'] = True
        st.session_state['username'] = login_username
        st.rerun()
    else:
        st.error("Invalid username or password")

def main():
    st.title('Login Page')
    
    # Initialize the database
    init_db()
    
    # Active tab management
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Login"
    
    # Create tabs
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.session_state.active_tab = "Login"
        st.header("Login")
        login_username1 = st.text_input("Username", key="login_username")
        login_password1 = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            login_func(login_username1, login_password1)
    
    with tab2:
        st.session_state.active_tab = "Register"
        st.header("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
        
        if st.button("Register", key="register_button"):
            if reg_password != reg_password_confirm:
                st.error("Passwords do not match!")
            elif not reg_username or not reg_password:
                st.error("Please fill in all fields!")
            else:
                try:
                    save_user(reg_username, reg_password)
                    st.success("Registration successful!")
                    save_auth_cookie(reg_username, reg_password)
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = reg_username
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already exists!")
def download_database():
    try:
        with open("users.db", "rb") as db_file:
            st.download_button(
                label="Download Database",
                data=db_file,
                file_name="users.db",
                mime="application/octet-stream"
            )
    except FileNotFoundError:
        st.error("Database file not found!")

# Add this functionality to your app
if st.session_state.get('logged_in') and st.session_state['username'] == 'admin':  # Replace 'admin' with your admin username
    if st.sidebar.button("Download Database"):
        download_database()

def logout():
    # Clear session state and cookies
    if 'auth_cookie' in st.session_state:
        del st.session_state['auth_cookie']
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.rerun()

if __name__ == '__main__':
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    # Check for existing auth cookie on page load
    if not st.session_state['logged_in']:
        if check_auth_cookie():
            file_main()
        else:
            main()
    else:
        file_main()

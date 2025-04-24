import streamlit as st
import pandas as pd
import requests
# import matplotlib.pyplot as plt

st.set_page_config(page_title="Web Scraping Dashboard", layout="wide")

def check_password():
    def password_entered():
        if st.session_state["password"] == "sourav":
            st.session_state["password_correct"] = True
        else:
            st.error("Wrong password")

    if "password_correct" not in st.session_state:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        return False
    else:
        return True
    
if check_password():
    

    st.title("🕷️ Automated Web Scraped Data Dashboard")

    # API base URL
    API_URL = "http://127.0.0.1:8000"

    # 🟢 Run Spider in Background
    if st.button("Run Scraper (Async)"):
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            st.success("Spider started successfully!")
        else:
            st.error("Failed to start spider.")

    st.markdown("---")

    # 🔍 Search Section
    st.subheader("🔎 Search Data")
    col1, col2 = st.columns(2)
    name = col1.text_input("Search by Name")
    location = col2.text_input("Search by Location")

    if name or location:
        query = f"?name={name}&location={location}"
        response = requests.get(f"{API_URL}/sourav/search{query}")
        data = response.json()
        df = pd.DataFrame(data)
        st.write("🔍 Filtered Results", df)
    else:
        # Load all data
        response = requests.get(f"{API_URL}/sourav")
        data = response.json()
        df = pd.DataFrame(data)
        st.write("📄 All Scraped Data", df)

    # 📊 Visualize Position Counts
    # st.subheader("📊 Position Distribution")
    # if not df.empty and "position" in df.columns:
    #     position_counts = df['position'].value_counts()
    #     fig, ax = plt.subplots()
    #     position_counts.plot(kind="bar", ax=ax, color="skyblue")
    #     st.pyplot(fig)

    # 🗂 Paginated view
    st.subheader("📑 Paginated Data View")
    limit = st.slider("Select number of rows per page", 5, 50, 10)
    page = st.number_input("Page number", min_value=1, value=1)
    skip = (page - 1) * limit

    paginated_response = requests.get(f"{API_URL}/sourav/paginated?skip={skip}&limit={limit}")
    paginated_data = paginated_response.json()
    df_paginated = pd.DataFrame(paginated_data)

    st.write(df_paginated)


    import altair as alt

    if not df.empty and "position" in df.columns:
        chart_data = df['position'].value_counts().reset_index()
        chart_data.columns = ['Position', 'Count']
        
        chart = alt.Chart(chart_data).mark_bar().encode(
            x='Position',
            y='Count',
            tooltip=['Position', 'Count']
        ).properties(width=700)

        st.altair_chart(chart)
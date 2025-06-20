import streamlit as st
import pandas as pd
import requests
import json # Import json for better error handling of API responses
import plotly.express as px # For charting

# --- Configuration ---
# In a real application, you might load these from a config.toml or environment variables
CONFIG = {
    "API_URL": "http://localhost:8000",
    "CACHE_TTL_SECONDS": 120, # Cache data for 2 minutes
    "PAGE_TITLE": "Enterprise Data Scraper Dashboard",
    "PAGE_ICON": "📊", # Emoji icon for the page title
    "DEFAULT_SELECT_OPTION": "-- Select --"
}

st.set_page_config(
    page_title=CONFIG["PAGE_TITLE"],
    page_icon=CONFIG["PAGE_ICON"],
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Function for Column Reordering ---
def reorder_dataframe_columns(df):
    """Ensures 'id', 'company', 'name' are the first columns, then others."""
    if df.empty:
        return df

    # Desired order for the first few columns
    desired_first_columns = ['id', 'name','company']
    
    # Get existing columns
    existing_columns = df.columns.tolist()
    
    # Identify columns that are in desired_first_columns and also in the DataFrame
    # Preserve their order
    reordered_columns = [col for col in desired_first_columns if col in existing_columns]
    
    # Add any other existing columns that are not in the desired_first_columns
    # Ensure they are added only if they are not already in reordered_columns
    for col in existing_columns:
        if col not in reordered_columns:
            reordered_columns.append(col)

    return df[reordered_columns]


# --- Helper Functions for API Calls ---

@st.cache_data(ttl=CONFIG["CACHE_TTL_SECONDS"])
def get_all_data():
    try:
        response = requests.get(f"{CONFIG['API_URL']}/")
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        return reorder_dataframe_columns(df) # Apply reordering here
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to the API at {CONFIG['API_URL']}. Please ensure the FastAPI backend is running.")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching all data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CONFIG["CACHE_TTL_SECONDS"])
def get_single_company_data(company_name):
    try:
        response = requests.get(f"{CONFIG['API_URL']}/company/{company_name}")
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        return reorder_dataframe_columns(df) # Apply reordering here
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to the API at {CONFIG['API_URL']}. Please ensure the FastAPI backend is running.")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data for {company_name}: {e}")
        return pd.DataFrame()

def post_record(data):
    try:
        response = requests.post(f"{CONFIG['API_URL']}/upload", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to the API at {CONFIG['API_URL']}. Please ensure the FastAPI backend is running.")
        return None
    except requests.exceptions.RequestException as e:
        error_detail = e.response.text if e.response else 'No response body'
        st.error(f"❌ Failed to add record. Error: {e}. Detail: {error_detail}")
        return None

def update_record_api(record_id, data):
    try:
        response = requests.put(f"{CONFIG['API_URL']}/update/{record_id}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to the API at {CONFIG['API_URL']}. Please ensure the FastAPI backend is running.")
        return None
    except requests.exceptions.RequestException as e:
        error_detail = e.response.text if e.response else 'No response body'
        st.error(f"❌ Failed to update record. Error: {e}. Detail: {error_detail}")
        return None

def delete_record_api(record_id):
    try:
        response = requests.delete(f"{CONFIG['API_URL']}/delete/{record_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Could not connect to the API at {CONFIG['API_URL']}. Please ensure the FastAPI backend is running.")
        return None
    except requests.exceptions.RequestException as e:
        error_detail = e.response.text if e.response else 'No response body'
        st.error(f"❌ Failed to delete record. Error: {e}. Detail: {error_detail}")
        return None

# --- Main Dashboard Structure ---

st.title(f"{CONFIG['PAGE_ICON']} {CONFIG['PAGE_TITLE']}")
st.markdown(
    """
    Welcome to your comprehensive dashboard for managing scraped company and contact information.
    Use the sidebar to navigate between different functionalities.
    """
)

# --- Sidebar Navigation ---
st.sidebar.header("🚀 Navigation")
page_selection = st.sidebar.radio(
    "Choose a section:",
    ["Dashboard Overview", "View All Records", "Filter & Search Records", "Add New Record", "Edit Record", "Manage Records (Delete)", "About"]
)

# --- Main Content Area based on Navigation ---

if page_selection == "Dashboard Overview":
    st.header("📊 Dashboard Overview")
    st.markdown("Get a quick glance at your scraped data statistics.")

    with st.spinner("Loading dashboard data..."):
        all_data = get_all_data() # This now returns reordered columns

    if all_data.empty:
        st.warning("No data available to display dashboard overview. Please add some records.")
    else:
        # Metrics
        col_total, col_unique = st.columns(2)
        with col_total:
            st.metric(label="Total Records", value=len(all_data))
        with col_unique:
            unique_companies = all_data["company"].dropna().unique()
            st.metric(label="Unique Companies", value=len(unique_companies))

        st.markdown("---")

        # Company Distribution Chart
        st.subheader("Company Record Distribution")
        # Ensure 'company' column exists before value_counts
        if 'company' in all_data.columns and not all_data['company'].empty:
            company_counts = all_data["company"].value_counts().reset_index()
            company_counts.columns = ['Company', 'Number of Records']
            fig = px.bar(
                company_counts,
                x='Company',
                y='Number of Records',
                title='Number of Records per Company',
                labels={'Company': 'Company Name', 'Number of Records': 'Count'},
                color='Number of Records',
                color_continuous_scale=px.colors.sequential.Plasma
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data available for distribution chart.")


elif page_selection == "View All Records":
    st.header("📋 All Scraped Records")
    st.markdown("This section displays every record currently in your database.")

    with st.spinner("Fetching all records..."):
        all_data = get_all_data() # This now returns reordered columns

    if all_data.empty:
        st.warning("No records found in the database. Add new records via the 'Add New Record' section.")
    else:
        st.dataframe(all_data, use_container_width=True, hide_index=True)
        st.info(f"Total records displayed: **{len(all_data)}**")

        st.download_button(
            label="⬇️ Download All Data as CSV",
            data=all_data.to_csv(index=False).encode('utf-8'),
            file_name="all_scraped_data.csv",
            mime="text/csv",
            help="Download all currently visible records as a CSV file."
        )


elif page_selection == "Filter & Search Records":
    st.header("🔍 Filter & Search Records")
    st.markdown("Use the options below to find specific records.")

    # Get companies for filtering
    with st.spinner("Loading data for filtering..."):
        filter_data_df = get_all_data() # This now returns reordered columns
        companies = filter_data_df["company"].dropna().unique().tolist()
        companies = sorted(companies)

    col_filter, col_search = st.columns([1, 2])

    with col_filter:
        selected_company = st.selectbox(
            "Filter by Company:",
            options=[CONFIG["DEFAULT_SELECT_OPTION"]] + companies,
            help="Choose a company name to narrow down the records."
        )
    with col_search:
        search_query = st.text_input(
            "Search keywords:",
            placeholder="e.g., John Doe, Manager, example@mail.com",
            help="Search across Company, Name, Designation, and Email fields."
        )

    filtered_search_data = filter_data_df.copy()

    # Apply company filter
    if selected_company != CONFIG["DEFAULT_SELECT_OPTION"]:
        filtered_search_data = filtered_search_data[filtered_search_data["company"] == selected_company]

    # Apply text search
    if search_query:
        search_query_lower = search_query.lower()
        filtered_search_data = filtered_search_data[
            filtered_search_data.apply(lambda row:
                search_query_lower in str(row['company']).lower() or
                search_query_lower in str(row['name']).lower() or
                search_query_lower in str(row['designation']).lower() or
                search_query_lower in str(row['email']).lower(),
                axis=1
            )
        ]

    st.markdown("---")
    st.subheader("Filtered Results")
    if filtered_search_data.empty:
        st.warning("No records match your current filter/search criteria.")
    else:
        st.dataframe(filtered_search_data, use_container_width=True, hide_index=True)
        st.info(f"Showing **{len(filtered_search_data)}** record(s) matching your criteria.")

        st.download_button(
            label="⬇️ Download Filtered Data as CSV",
            data=filtered_search_data.to_csv(index=False).encode('utf-8'),
            file_name="filtered_scraped_data.csv",
            mime="text/csv",
            help="Download the currently filtered and searched records as a CSV file."
        )

elif page_selection == "Add New Record":
    st.header("➕ Add New Record")
    st.markdown("Use this form to manually add a new contact record to your database.")

    with st.form("create_record_form", clear_on_submit=True):
        st.subheader("Contact Information")
        col_company, col_name = st.columns(2)
        with col_company:
            new_company = st.text_input("Company Name", help="The organization the contact belongs to.")
        with col_name:
            new_name = st.text_input("Contact Name", help="Full name of the individual.")

        col_designation, col_phone = st.columns(2)
        with col_designation:
            new_designation = st.text_input("Designation", help="Their job title or role.")
        with col_phone:
            new_phone = st.text_input("Phone Number", help="e.g., +1 (555) 123-4567")

        new_email = st.text_input("Email Address", help="The contact's professional email.")
        new_description = st.text_area("Description / Notes", help="Any additional details or context about the record.")

        st.markdown("---")
        add_submit_button = st.form_submit_button("Submit New Record")

        if add_submit_button:
            if not new_company or not new_name:
                st.warning("Company Name and Contact Name are required fields for a new record.")
            else:
                data = {
                    "company": new_company,
                    "name": new_name,
                    "designation": new_designation,
                    "phone": new_phone,
                    "email": new_email,
                    "description": new_description
                }
                with st.spinner("Adding record..."):
                    res = post_record(data)
                if res:
                    st.success(f"🎉 Record for **{new_name}** at **{new_company}** added successfully! ID: `{res.get('id', 'N/A')}`")
                    st.cache_data.clear() # Clear cache to ensure updated data is fetched next time
                    # st.rerun() # Rerun can cause inputs to momentarily reappear
                else:
                    st.error("🚫 Failed to add record. Please check the API status and inputs provided.")

elif page_selection == "Edit Record":
    st.header("✏️ Edit Existing Record")
    st.markdown("Find a record by its ID and then update its details.")

    all_current_data = get_all_data() # This now returns reordered columns

    if all_current_data.empty:
        st.warning("No records available to edit. Please add some first.")
    else:
        # Ensure 'id' column exists and is numeric
        if 'id' in all_current_data.columns:
            record_ids = all_current_data["id"].dropna().unique().tolist()
            # Convert to int, handle potential non-numeric values gracefully
            record_ids = sorted([int(x) for x in record_ids if pd.notna(x) and str(x).isdigit()])
        else:
            record_ids = []
            st.error("The 'id' column is missing from the fetched data, cannot edit records.")

        if not record_ids:
            st.warning("No valid record IDs found to edit.")
            # Clear form state if no IDs are available
            st.session_state.edit_id_selectbox = CONFIG["DEFAULT_SELECT_OPTION"]
        else:
            # Use session state for selectbox to maintain value across reruns
            # This helps prevent the selectbox from resetting to default after an update
            if 'edit_id_selectbox' not in st.session_state:
                st.session_state.edit_id_selectbox = CONFIG["DEFAULT_SELECT_OPTION"]

            edit_id = st.selectbox(
                "Select Record ID to Edit:",
                options=[CONFIG["DEFAULT_SELECT_OPTION"]] + record_ids,
                help="Choose the ID of the record you wish to modify.",
                key="edit_id_selectbox"
            )

            selected_record_data = None
            if edit_id != CONFIG["DEFAULT_SELECT_OPTION"]:
                # Ensure the 'id' column is of integer type before filtering if it came as float
                temp_df = all_current_data.copy()
                if 'id' in temp_df.columns:
                    try:
                        temp_df['id'] = temp_df['id'].astype(int)
                    except ValueError:
                        st.error("ID column contains non-integer values.")
                        selected_record_data = None
                
                if not temp_df[temp_df["id"] == int(edit_id)].empty:
                    selected_record_data = temp_df[temp_df["id"] == int(edit_id)].iloc[0]
                    st.info(f"Currently editing record ID: **{int(edit_id)}**")
                else:
                    st.warning(f"No data found for ID {int(edit_id)}. It might have been deleted.")
                    selected_record_data = None # Reset if data not found

            with st.form("edit_record_form"):
                st.subheader("Update Information")
                col_comp_edit, col_name_edit = st.columns(2)
                with col_comp_edit:
                    edited_company = st.text_input("Company Name", value=selected_record_data["company"] if selected_record_data is not None and "company" in selected_record_data else "", key="edit_company")
                with col_name_edit:
                    edited_name = st.text_input("Contact Name", value=selected_record_data["name"] if selected_record_data is not None and "name" in selected_record_data else "", key="edit_name")

                col_desig_edit, col_phone_edit = st.columns(2)
                with col_desig_edit:
                    edited_designation = st.text_input("Designation", value=selected_record_data["designation"] if selected_record_data is not None and "designation" in selected_record_data else "", key="edit_designation")
                with col_phone_edit:
                    edited_phone = st.text_input("Phone Number", value=selected_record_data["phone"] if selected_record_data is not None and "phone" in selected_record_data else "", key="edit_phone")

                edited_email = st.text_input("Email Address", value=selected_record_data["email"] if selected_record_data is not None and "email" in selected_record_data else "", key="edit_email")
                edited_description = st.text_area("Description / Notes", value=selected_record_data["description"] if selected_record_data is not None and "description" in selected_record_data else "", key="edit_description")

                st.markdown("---")
                update_submit_button = st.form_submit_button("Update Record")

                if update_submit_button:
                    if edit_id == CONFIG["DEFAULT_SELECT_OPTION"] or selected_record_data is None:
                        st.warning("Please select a Record ID and ensure its data is loaded before updating.")
                    elif not edited_company or not edited_name:
                        st.warning("Company Name and Contact Name cannot be empty.")
                    else:
                        updated_data = {
                            "company": edited_company,
                            "name": edited_name,
                            "designation": edited_designation,
                            "phone": edited_phone,
                            "email": edited_email,
                            "description": edited_description
                        }
                        with st.spinner(f"Updating record {int(edit_id)}..."):
                            update_res = update_record_api(int(edit_id), updated_data)
                        if update_res:
                            st.success(f"✅ Record ID **{int(edit_id)}** updated successfully!")
                            st.cache_data.clear()
                            # After successful update, ideally re-select the default or a relevant state
                            # For simplicity, we can clear the current selection
                            st.session_state.edit_id_selectbox = CONFIG["DEFAULT_SELECT_OPTION"]
                            st.rerun() # Rerun to clear form and refresh selectbox
                        else:
                            st.error("🚫 Failed to update record. Check inputs and API connection.")

elif page_selection == "Manage Records (Delete)":
    st.header("🗑️ Delete Records")
    st.markdown("Permanently remove records from your database. This action cannot be undone.")

    # Get all IDs for deletion
    all_current_data = get_all_data()
    if all_current_data.empty:
        st.warning("No records found to delete.")
    else:
        # Ensure 'id' column exists and is numeric
        if 'id' in all_current_data.columns:
            delete_record_ids = all_current_data["id"].dropna().unique().tolist()
            delete_record_ids = sorted([int(x) for x in delete_record_ids if pd.notna(x) and str(x).isdigit()])
        else:
            delete_record_ids = []
            st.error("The 'id' column is missing from the fetched data, cannot delete records.")

        if not delete_record_ids:
            st.warning("No valid record IDs found to delete.")
        else:
            delete_id_selection = st.selectbox(
                "Select ID to delete:",
                options=[CONFIG["DEFAULT_SELECT_OPTION"]] + delete_record_ids,
                help="Choose the unique ID of the record you want to remove."
            )

            delete_button = st.button("Delete Selected Record", type="secondary", icon="🗑️")

            if delete_button and delete_id_selection != CONFIG["DEFAULT_SELECT_OPTION"]:
                # Use a confirmation flow
                confirm_delete_placeholder = st.empty() # Placeholder for the warning
                if confirm_delete_placeholder.warning(f"Are you absolutely sure you want to delete record with ID **{int(delete_id_selection)}**? This action cannot be undone."):
                    if st.button("Confirm Permanent Deletion", key="confirm_del_btn", type="primary", icon="🔥"):
                        with st.spinner(f"Deleting record {int(delete_id_selection)}..."):
                            del_res = delete_record_api(int(delete_id_selection))
                        if del_res:
                            st.success(f"🗑️ Record with ID **{int(delete_id_selection)}** deleted successfully!")
                            st.cache_data.clear() # Clear cache to ensure updated data is fetched
                            st.rerun() # Rerun to refresh the dashboard
                        else:
                            st.error("🚫 Failed to delete record. Please ensure the ID is correct and the API is running.")
                    else:
                        st.info("Deletion cancelled.")
            elif delete_button and delete_id_selection == CONFIG["DEFAULT_SELECT_OPTION"]:
                st.warning("Please select a valid record ID to delete.")

elif page_selection == "About":
    st.header("ℹ️ About This Dashboard")
    st.markdown(
        """
        This dashboard provides a user-friendly interface for managing data scraped from various websites.
        It leverages a **FastAPI** backend for robust data handling and **Streamlit** for interactive visualization.

        **Key Features:**
        * **Dashboard Overview:** Get quick insights into your data.
        * **View All Records:** See all collected data in one place.
        * **Filter & Search:** Easily find specific records based on company or keywords.
        * **Add New Record:** Manually input new contact information.
        * **Edit Record:** Update existing contact details.
        * **Delete Record:** Remove unwanted records from the database.
        * **Data Download:** Export filtered or all data to CSV.

        **Technologies Used:**
        * **Streamlit:** For the interactive web interface.
        * **FastAPI:** For the powerful and fast API backend.
        * **Pandas:** For data manipulation and display.
        * **Requests:** For making HTTP requests to the API.
        * **Plotly Express:** For data visualization.

        ---
        Developed as a tool for managing enterprise contact information.

        **Note:** Ensure your FastAPI backend is running at `{}` for full functionality.
        """.format(CONFIG['API_URL'])
    )
    st.markdown(f"**Current API Endpoint:** `{CONFIG['API_URL']}`")
    st.markdown(f"**Last Dashboard Refresh:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    st.markdown("---")
    st.write("For support or inquiries, please contact the developer.")


# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.info(
    "Dashboard powered by Streamlit and FastAPI. "
    f"Current time: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"
)

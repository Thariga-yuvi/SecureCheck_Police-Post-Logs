# SecureCheck: Traffic Stop Intelligence Platform
import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from PIL import Image
import datetime

# Set page configuration
st.set_page_config(
    page_title="SecureCheck Dashboard",
    page_icon="https://img.freepik.com/premium-vector/secure-icon-with-lock-shield-check-mark-as-flat-logo-design-as-internet-antivirus-guard-private_101884-1553.jpg",
    layout="wide"
)

# Render PostgreSQL Connection Setup
host = "dpg-d178l9gdl3ps73a5q1mg-a.singapore-postgres.render.com"
port = "5432"
database = "trafficdb_q63e"
username = "thariga_ds"
password = "DUyvvsd9XN1ZYXsYcxM5J6Y9L6Yzt8yl"
engine_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(engine_string)

# Fetch data from PostgreSQL
def fetch_data(query):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Upload DataFrame to PostgreSQL
def upload_to_postgres(df, table_name="traffic_stops"):
    try:
        df.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"Data pushed to PostgreSQL table: {table_name}")
    except Exception as e:
        print("Failed to push data:", e)

# Home Page

def show_dashboard():
    st.title("👮:orange[SecureCheck: Real-Time Traffic Stop Intelligence Platform]")
    try:
        image = Image.open("C:\\Users\\Yuvaraj\\OneDrive\\firstproject\\env\\traffic-stop-safely.webp")
        resized_image = image.resize((800, int(image.height * 800 / image.width)))
        st.image(resized_image, caption="Monitoring Every Mile for Public Safety")
    except Exception:
        st.warning("Header image not found.")

    data = fetch_data("SELECT * FROM traffic_stops")
    st.header("👮‍♂️ Traffic Stop Data Overview")

    if data is not None and not data.empty:
        st.dataframe(data, use_container_width=True)
        st.header("📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Stops", data.shape[0])
        col2.metric("Total Arrests", data['stop_outcome'].value_counts().get('Arrest', 0))
        col3.metric("Total Searches", int(data['search_conducted'].sum()))
        col4.metric("Unique Violations", data['violation'].nunique())
    else:
        st.warning("No data available.")
#Medium queries
query_map_medium = {
    # 🚗 Vehicle-Based
    "1.Top 10 vehicles involved in drug-related stops": """
        SELECT vehicle_number, COUNT(*) AS drug_related_count 
        FROM traffic_stops 
        WHERE drugs_related_stop = TRUE 
        GROUP BY vehicle_number 
        ORDER BY drug_related_count DESC 
        LIMIT 10;
    """,
    "2.Most frequently searched vehicles": """
        SELECT vehicle_number, COUNT(*) AS search_count 
        FROM traffic_stops 
        WHERE search_conducted = TRUE 
        GROUP BY vehicle_number 
        ORDER BY search_count DESC
        LIMIT 10;
    """,

    # 🧍 Demographic-Based
    "3.Driver age group with highest arrest rate": """
        SELECT
            CASE
                WHEN driver_age BETWEEN 10 AND 20 THEN '10-20'
                WHEN driver_age BETWEEN 21 AND 30 THEN '21-30'
                WHEN driver_age BETWEEN 31 AND 40 THEN '31-40'
                WHEN driver_age BETWEEN 41 AND 50 THEN '41-50'
                WHEN driver_age BETWEEN 51 AND 60 THEN '51-60'
                WHEN driver_age BETWEEN 61 AND 70 THEN '61-70'
                ELSE '71+'
            END AS age_group,
            COUNT(*) AS arrest_count
        FROM traffic_stops
        WHERE is_arrested = TRUE
        GROUP BY age_group
        ORDER BY arrest_count DESC
        LIMIT 1;
    """,
    "4.Gender distribution of drivers by country": """
        SELECT country_name, driver_gender, COUNT(*) AS stop_count 
        FROM traffic_stops 
        GROUP BY country_name, driver_gender 
        ORDER BY country_name, stop_count DESC;
    """,
    "5.Race and gender with highest search rate": """
        SELECT driver_race, driver_gender,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS search_count,
               (SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS search_rate
        FROM traffic_stops
        GROUP BY driver_race, driver_gender
        ORDER BY search_rate DESC
        LIMIT 1;
    """,

    # ⏰ Time & Duration-Based
    "6.Hour with most traffic stops": """
        SELECT SPLIT_PART(stop_time, ':', 1)::INT AS stop_hour, COUNT(*) AS stop_count 
        FROM traffic_stops 
        GROUP BY stop_hour 
        ORDER BY stop_count DESC 
        LIMIT 1;
    """,
    "7.Average stop duration by violation": """
        SELECT violation,
               AVG(CASE
                   WHEN stop_duration = '0-15 Min' THEN 7.5
                   WHEN stop_duration = '16-30 Min' THEN 23
                   WHEN stop_duration = '30+ Min' THEN 45
               END) AS avg_stop_duration
        FROM traffic_stops
        GROUP BY violation
        ORDER BY avg_stop_duration DESC;
    """,
    "8.Are night stops more likely to lead to arrests?": """
        SELECT
            CASE
                WHEN SPLIT_PART(stop_time, ':', 1)::INT BETWEEN 0 AND 5 THEN 'Midnight - 5 AM'
                WHEN SPLIT_PART(stop_time, ':', 1)::INT BETWEEN 6 AND 11 THEN '6 AM - 11 AM'
                WHEN SPLIT_PART(stop_time, ':', 1)::INT BETWEEN 12 AND 17 THEN '12 PM - 5 PM'
                WHEN SPLIT_PART(stop_time, ':', 1)::INT BETWEEN 18 AND 23 THEN '6 PM - 11 PM'
            END AS time_period,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrests,
            (SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS arrest_rate
        FROM traffic_stops
        GROUP BY time_period
        ORDER BY arrest_rate DESC;
    """,

    # ⚖️ Violation-Based
    "9.Violations with highest search rate": """
        SELECT violation,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS search_count,
               (SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS search_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY search_rate DESC;
    """,
    "10.Violations with highest arrest rate": """
        SELECT violation,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest_count,
               (SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrest_rate DESC;
    """,
    "11.Most common violations among drivers <25": """
        SELECT violation, COUNT(*) AS violation_count 
        FROM traffic_stops 
        WHERE driver_age < 25 
        GROUP BY violation 
        ORDER BY violation_count DESC;
    """,
    "12.Violation with lowest search and arrest rate": """
        SELECT violation,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS search_count,
               (SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS search_rate,
               SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest_count,
               (SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY search_rate ASC, arrest_rate ASC
        LIMIT 1;
    """,

    # 🌍 Location-Based
    "13.Countries with highest drug-related stop rate": """
        SELECT country_name,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_related_count,
               (SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS drug_related_rate
        FROM traffic_stops
        GROUP BY country_name
        ORDER BY drug_related_rate DESC;
    """,
    "14.Arrest rate by country and violation": """
        SELECT country_name, violation,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest_count,
               (SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS arrest_rate
        FROM traffic_stops
        GROUP BY country_name, violation
        ORDER BY arrest_rate DESC;
    """,
    "15.Country with most searches": """
        SELECT country_name, COUNT(*) AS search_count 
        FROM traffic_stops 
        WHERE search_conducted = TRUE 
        GROUP BY country_name 
        ORDER BY search_count DESC 
        LIMIT 1;
    """
}


# Complex-Level Query Mapping
query_map_advanced = {
    "1. Yearly Breakdown of Stops and Arrests by Country": """
        WITH yearly_stops AS (
    SELECT 
        country_name,
        EXTRACT(YEAR FROM TO_DATE(stop_date, 'DD-MM-YYYY')) AS stop_year,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
    FROM traffic_stops
    GROUP BY country_name, stop_year
)
SELECT 
    country_name,
    stop_year,
    total_stops,
    total_arrests,
    ROUND((total_arrests * 100.0 / total_stops), 2) AS arrest_rate,
    RANK() OVER (PARTITION BY stop_year ORDER BY total_stops DESC) AS stop_rank
FROM yearly_stops
ORDER BY stop_year DESC, stop_rank;
 """,

    "2. Driver Violation Trends Based on Age and Race": """
        WITH age_race_stats AS (
            SELECT
                driver_age,
                driver_race,
                violation,
                COUNT(*) AS violation_count
            FROM traffic_stops
            GROUP BY driver_age, driver_race, violation
        )
        SELECT
            driver_age,
            driver_race,
            violation,
            violation_count,
            RANK() OVER (PARTITION BY driver_race ORDER BY violation_count DESC) AS race_violation_rank,
            RANK() OVER (PARTITION BY driver_age ORDER BY violation_count DESC) AS age_violation_rank
        FROM age_race_stats
        ORDER BY race_violation_rank, age_violation_rank;
    """,
 "3.Time Period Analysis of Stops (Joining with Date Functions) , Number of Stops by Year,Month, Hour of the Day": """
 SELECT 
    EXTRACT(YEAR FROM TO_DATE(stop_date, 'DD-MM-YYYY')) AS Years_of_traffic_stops,
    EXTRACT(MONTH FROM TO_DATE(stop_date, 'DD-MM-YYYY')) AS Month_number_of_Year,
    TO_CHAR(TO_DATE(stop_date, 'DD-MM-YYYY'), 'Month') AS Month_of_Year,
    EXTRACT(HOUR FROM stop_time::TIME) AS Hour_of_the_day,
    DATE_TRUNC('hour', stop_time::TIME) AS Hour_timestamp_of_the_Day,
    COUNT(*) AS total_stops
FROM traffic_stops
GROUP BY 
    Years_of_traffic_stops, 
    Month_number_of_Year, 
    Month_of_Year, 
    Hour_of_the_day, 
    Hour_timestamp_of_the_Day
ORDER BY 
    Years_of_traffic_stops, 
    Month_number_of_Year, 
    Month_of_Year, 
    Hour_of_the_day, 
    Hour_timestamp_of_the_Day ASC;""",

    "4. Violations with High Search and Arrest Rates": """
        WITH violation_stats AS (
            SELECT
                violation,
                COUNT(*) AS total_stops,
                SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS search_count,
                ROUND((SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) AS search_rate,
                SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest_count,
                ROUND((SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) AS arrest_rate
            FROM traffic_stops
            GROUP BY violation
        )
        SELECT
            violation,
            total_stops,
            search_count,
            search_rate,
            arrest_count,
            arrest_rate,
            RANK() OVER (ORDER BY search_rate DESC) AS search_rank,
            RANK() OVER (ORDER BY arrest_rate DESC) AS arrest_rank
        FROM violation_stats
        ORDER BY search_rank, arrest_rank;
    """,

    "5. Driver Demographics by Country (Age, Gender, Race)": """
        SELECT
            country_name,
            driver_gender,
            driver_race,
            ROUND(AVG(driver_age), 2) AS avg_age,
            COUNT(*) AS total_stops
        FROM traffic_stops
        GROUP BY country_name, driver_gender, driver_race
        ORDER BY country_name, total_stops DESC;
    """,

    "6. Top 5 Violations with Highest Arrest Rates": """
        SELECT
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest_count,
            ROUND((SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrest_rate DESC
        LIMIT 5;
    """
}

# Show Fundamental Insights Page
def show_fundamental_insights():
    st.title("💡 Fundamental Insights")
    st.write("Explore categorized traffic stop patterns.")
    selected_query = st.selectbox("Select a Medium-Level Query", list(query_map_medium.keys()))
    if st.button("Run Medium Query"):
        query = query_map_medium.get(selected_query)
        if query:
            df = fetch_data(query)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No data returned.")
        else:
            st.error("Invalid selection.")

# Show Advanced Insights Page
def show_advanced_insights():
    st.title("🧠 Advanced Insights")
    st.write("Complex queries with subqueries, joins, and window functions.")
    selected_query = st.selectbox("Select an Advanced Query", list(query_map_advanced.keys()))
    if st.button("Run Advanced Query"):
        query = query_map_advanced.get(selected_query)
        if query:
            df = fetch_data(query)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No data returned.")
        else:
            st.error("Invalid selection.")

def show_add_log():
    st.title("📝 Add New Police Log and Predict Outcome and Violation")
    data = fetch_data("SELECT * FROM traffic_stops")

    with st.form("new_log_form"):
        stop_date = st.date_input("Stop Date")
        stop_time = st.time_input("Stop Time", step=datetime.timedelta(minutes=1))
        country_name = st.text_input("Country Name")
        driver_gender = st.selectbox("Driver Gender", ["M", "F"])
        driver_age = st.number_input("Driver Age", min_value=16, max_value=100)
        driver_race = st.text_input("Driver Race")
        search_conducted = st.selectbox("Search Conducted", ["Yes", "No"])
        search_type = st.text_input("Search Type")
        drug_related_stop = st.selectbox("Drug Related Stop", ["Yes", "No"])
        stop_duration = st.selectbox("Stop Duration", ["0-5 Min", "6-15 Min", "16-30 Min", "30+ Min"])
        vehicle_number = st.text_input("Vehicle Number")
        submitted = st.form_submit_button("Submit Log")

    if submitted:
        # Convert string fields to boolean
        search_conducted_int = 1 if search_conducted == "Yes" else 0
        drugs_related_stop_int = 1 if drug_related_stop == "Yes" else 0
        gender_full = "Male" if driver_gender == "M" else "Female"

        # Predict outcome based on similar records
        filtered = data[
            (data['driver_gender'] == driver_gender) &
            (data['driver_age'] == driver_age) &
            (data['search_conducted'] == (search_conducted == "Yes")) &
            (data['stop_duration'] == stop_duration) &
            (data['drugs_related_stop'] == (drug_related_stop == "Yes"))
        ]

        predicted_outcome = filtered['stop_outcome'].mode()[0] if not filtered.empty else "Warning"
        predicted_violation = filtered['violation'].mode()[0] if not filtered.empty else "Speeding"

        # Log confirmation message
        search_text = "A search was conducted" if search_conducted == "Yes" else "No search was conducted"
        drug_text = "was a drug-related stop" if drug_related_stop == "Yes" else "was not a drug-related stop"

        # Display prediction summary
        st.markdown(f""" 
        ### 📝 **Prediction Summary**  
        - **Predicted Stop Outcome:** `{predicted_outcome}`  
        - **Predicted Violation:** `{predicted_violation}`
        """)

        # Display success message
        st.success(
            f"Log submitted successfully!\n\n"
            f"A {driver_age}-year-old {gender_full} driver in {country_name} was stopped at {stop_time.strftime('%I:%M %p')} on {stop_date.strftime('%B %d, %Y')}. "
            f"{search_text}, and {drug_text.lower()}.\n"
            f"Stop duration: {stop_duration}.\n"
            f"Vehicle Number: {vehicle_number}."
        )

    # Footer
    st.markdown("---")
# Sidebar Navigation
selected_page = st.sidebar.radio("Navigation", ["🏠 Home", "💡 Fundamental Insights", "🧠 Advanced Insights", "📝 Add New Police Log"])

# Routing
if selected_page == "🏠 Home":
    show_dashboard()
elif selected_page == "💡 Fundamental Insights":
    show_fundamental_insights()
elif selected_page == "🧠 Advanced Insights":
    show_advanced_insights()
elif selected_page == "📝 Add New Police Log":
    show_add_log()

# Footer
st.markdown("---")
st.caption("SecureCheck - Real-Time Traffic Stop Intelligence Platform | Developed by Thariga Yuvaraj")

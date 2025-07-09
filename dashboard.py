# SecureCheck: Traffic Stop Intelligence Platform
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from PIL import Image
import datetime

# Set page configuration
st.set_page_config(
    page_title="SecureCheck Dashboard",
    page_icon="https://img.freepik.com/premium-vector/secure-icon-with-lock-shield-check-mark-as-flat-logo-design-as-internet-antivirus-guard-private_101884-1553.jpg",
    layout="wide"
)

#Render PostgreSQL Connection Setup
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
query_map_medium = {"1: What are the top 10 vehicle_Number involved in drug-related stops?" : """Select vehicle_number, drugs_related_stop 
from traffic_stops 
where drugs_related_stop = TRUE limit 10""",
"2: Which vehicles were most frequently searched?" : """select vehicle_number, count(*) as search_count
from traffic_stops 
where search_conducted = TRUE group by vehicle_number order by search_count desc limit 1""",
"3: Which driver age group had the highest arrest rate?" : """select 
	case
	when driver_age <= 18 then 'under18'
	when driver_age <= 25 then '18-25'
	when driver_age <= 35 then '26-35'
	when driver_age <= 50 then '36-50'
	when driver_age <= 65 then '51-65'
	else '65+'
end as age_group,
    driver_age,
    avg(case when is_arrested = 'True' then 1 else 0 END) as arrest_rate
from 
    traffic_stops
group by 
    driver_age
order by 
    arrest_rate DESC
limit 1;""",
"4: What is the gender distribution of drivers stopped in each country?" : """select
    country_name,
    driver_gender,
    count(*) as num_stops
from
    traffic_stops
group by
    country_name,
    driver_gender
order by
    country_name,
    driver_gender;""",
"5: Which race and gender combination has the highest search rate?" : """select
    driver_race,
    driver_gender,
    count(*) filter (where search_conducted = TRUE) as num_searches,
    count(*) as total_stops,
    round(count(*) filter (where search_conducted = TRUE) * 100.0 / count(*), 2) as search_rate
from
    traffic_stops
group by
    driver_race,
    driver_gender
order by
    search_rate desc
limit 1;""",
"6: What time of day sees the most traffic stops?" : """select 
extract (hour from stop_time) as hour_of_day,
count(*) as no_of_stops
from traffic_stops
where stop_time IS NOT NULL
group by hour_of_day
order by no_of_stops desc
limit 1;""",
"7: What is the average stop duration for different violations?" : """select violation,
round(avg(case
	when stop_duration = '0-15 Min' then 15
	when stop_duration = '16-30 Min' then 30
	when stop_duration = '30+ Min' then 45
end),3) as avg_duration
from traffic_stops
where stop_duration is not null
group by violation
order by avg_duration desc;""",
"8: Are stops during the night more likely to lead to arrests?" : """select 
  case when extract(HOUR from stop_time::time) between 6 and 17 then 'Day'
    else 'Night'
  end as time_of_day,
  count(*) as total_stops,
  sum(case when is_arrested = 'True' then 1 else 0 end) as total_arrests,
  round(sum(case when is_arrested = 'True' then 1 else 0 END) * 100.0 / count(*),2
  ) as arrest_rate_percentage
from traffic_stops
group by time_of_day;""",
"9: Which violations are most associated with searches or arrests?" : """select 
  violation,
  count(*) as total_stops,
  sum(case when search_conducted = 'True' then 1 else 0 end) as total_searches,
  sum(case when is_arrested = 'True' then 1 else 0 end) as total_arrests,
  round(sum(case when search_conducted = 'True' then 1 else 0 end) * 100.0 / count(*), 2) as search_rate_percentage,
  round(sum(case when is_arrested = 'True' then 1 else 0 end) * 100.0 / count(*), 2) as arrest_rate_percentage
from traffic_stops
group by violation
order by total_searches desc, total_arrests desc;""",
"10: Which violations are most common among younger drivers (<25)?" : """select violation,
count(*) as young_driver_stops
from traffic_stops
where driver_age < 25
group by violation
order by young_driver_stops desc;""",
"11: Is there a violation that rarely results in search or arrest?" : """select violation,
	count(*) as total_stops,
	sum(case when search_conducted = TRUE then 1 else 0 end) as total_searches,
	sum(case when is_arrested = TRUE then 1 else 0 end) as total_arrests,
	round(sum(case when search_conducted = TRUE then 1 else 0 end) *100.0 / count(*),2) as search_percent,
	round(sum(case when is_arrested = TRUE then 1 else 0 end) *100.0 / count(*),2) as arrest_percent
from traffic_stops
Group by violation
order by total_searches asc, total_arrests asc
limit 5;""",
"12: Which countries report the highest rate of drug-related stops?" : """select country_name,
count(*) as total_stops,
sum(case when drugs_related_stop = TRUE then 1 else 0 end) as total_drug_related_stops,
round(sum(case when drugs_related_stop = TRUE then 1 else 0 end) * 100.0 / count(*), 2) as total_drug_related_stops_percent
from traffic_stops
group by country_name
order by total_drug_related_stops_percent desc;""",
"13: What is the arrest rate by country and violation?" : """select country_name, violation,
count(*) as total_stops,
sum(case when is_arrested = TRUE then 1 else 0 end) as total_arrests,
round(sum(case when is_arrested = TRUE then 1 else 0 end) *100.0 / count(*),2) as arrest_percent
from traffic_stops
group by country_name, violation
order by arrest_percent desc;""",
"14: Which country has the most stops with search conducted?" : """select country_name,
count(*) as total_stops_per_country
from traffic_stops
where search_conducted = TRUE
group by country_name
order by total_stops_per_country desc
limit 1;"""
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
selected_page = st.sidebar.radio("Navigation", ["🏠 Home", "💡 Fundamental Insights", "🧠 Advanced Insights", "📝 Add New Police Log and Predict Outcome and Violation"])

# Routing
if selected_page == "🏠 Home":
    show_dashboard()
elif selected_page == "💡 Fundamental Insights":
    show_fundamental_insights()
elif selected_page == "🧠 Advanced Insights":
    show_advanced_insights()
elif selected_page == "📝 Add New Police Log and Predict Outcome and Violation":
    show_add_log()

# Footer
st.markdown("---")
st.caption("SecureCheck - Real-Time Traffic Stop Intelligence Platform | Developed by Thariga")

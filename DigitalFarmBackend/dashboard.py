import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import sqlite3
import joblib
import os

DB_PATH = "digitalfarm.db"

# Connect ONCE
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dose_mg REAL,
    treatment_days INTEGER,
    days_after_treatment INTEGER,
    prediction TEXT
)
""")

conn.commit()

# Check tables (optional debug)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

conn.close()


def load_accuracy():
    try:
        with open("accuracy.txt", "r") as f:
            return float(f.read())
    except:
        return None

def load_model():
    model_path = os.path.join(os.getcwd(), "model.pkl")
    return joblib.load(model_path)

model = load_model()

st.set_page_config(page_title="Digital Farm System", layout="wide")

BASE_URL = "https://digital-farm-backend.onrender.com"

USERS = {
    "admin": "1234",
    "farmer": "farm123",
    "vet": "vet123"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username

            if username == "admin":
                st.session_state.role = "Admin"
            elif username == "vet":
                st.session_state.role = "Veterinarian"
            else:
                st.session_state.role = "Farmer"

            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ===============================
# BACKEND CHECK
# ===============================
try:
    res = requests.get(f"{BASE_URL}/docs")  # or /predict
    if res.status_code == 200:
        st.success("✅ Backend connected")
    else:
        st.error("❌ Backend NOT reachable")
except:
    st.error("❌ Backend NOT reachable")

# ===============================
# SIDEBAR
# ===============================
page = st.sidebar.radio("Navigation", [
    "Dashboard",
    "AMU Records",
    "Analytics",
    "AI Prediction",
    "Prediction History"
])

# ===============================
# 🔥 FIXED DATA FUNCTION (ONLY FIXED PART)
# ===============================
def get_data():
    try:
        df = pd.read_csv("https://raw.githubusercontent.com/RAMYA09876/Digital-Farm-Backend/main/amu_residue_records_6000.csv")

        # 👉 FIX: CREATE MRL COLUMN
        if "mrl" not in df.columns:
            
            if "residue_mg_per_kg" in df.columns:
                df["mrl"] = df["residue_mg_per_kg"]
                
            else:
                st.error(f"❌ No residue column found. Available columns: {list(df.columns)}")
                return pd.DataFrame()

        df["mrl"] = pd.to_numeric(df["mrl"], errors="coerce").fillna(0)

        df["result"] = df["mrl"].apply(lambda x: "Safe" if x <= 0.05 else "Unsafe")

        # 👉 FIX: RESULT
        def classify(row):
            ratio = row["residue_mg_per_kg"] / row["mrl_limit_mg_per_kg"]

            if ratio <= 1:
                return "Safe"
            elif ratio <= 1.5:
                return "Warning"
            else:
                return "Critical"

        df["risk_level"] = df.apply(classify, axis=1)

        # 👉 FIX: OTHER COLUMNS
        if "confidence" not in df.columns:
            df["confidence"] = 100

        if "timestamp" not in df.columns:
            df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df))

        return df

    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()
    
    

# ===============================
# DASHBOARD
# ===============================
if page == "Dashboard":

    df = get_data()
    df.columns = df.columns.str.lower()

    # ===============================
    # CREATE PREDICTION COLUMN (FIX)
    # ===============================
    if "prediction" not in df.columns:
        
        df["prediction"] = df.apply(
            lambda row: "Unsafe"
            if row["residue_mg_per_kg"] > row["mrl_limit_mg_per_kg"]
            else "Safe",
            axis=1
        )

    # ================= FILTER =================
    
    if "farm" in df.columns:
        farm_list = df["farm"].unique()
        selected_farm = st.selectbox("Select Farm", ["All"] + list(farm_list))
        
        if selected_farm != "All":
            df = df[df["farm"] == selected_farm]
    else:
        st.warning("⚠️ No farm column found in dataset")

    st.title("📊 Dashboard Overview")

    # ===============================
    # MODEL ACCURACY DISPLAY
    # ===============================
    accuracy = load_accuracy()

    if accuracy:
        st.info(f"🤖 Model Accuracy: {accuracy * 100:.2f}%")

    if df.empty:
        st.warning("No data available")

    else:

        total_animals = len(df)
        total_records = len(df)

        df["result"] = df["result"].astype(str).str.strip().str.lower()

        safe_count = (df["result"] == "safe").sum()
        unsafe_count = (df["result"] == "unsafe").sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Animals", total_animals)
        col2.metric("Records", total_records)
        col3.metric("Safe", safe_count)
        col4.metric("Unsafe", unsafe_count)

        if unsafe_count > 0:
            st.error(f"⚠️ {unsafe_count} unsafe records detected! Immediate action required.")
            
        else:
            st.success("✅ All livestock products are within safe MRL limits.")

        # ================= OPTIMIZED CHART =================
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        if df["timestamp"].isnull().all():
            df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df))

        # Aggregate for better visualization
        trend_df = df.copy()
    
        trend_df["month"] = trend_df["timestamp"].dt.to_period("M").astype(str)
        
        trend_df = trend_df.groupby("month")["mrl"].mean().reset_index()

        trend_df = trend_df.sort_values("month")
        
        trend_df = trend_df.tail(12)


        fig_line = px.line(
            trend_df,
            x="month",
            y="mrl",
            title="Average Monthly MRL Trend",
            markers=True
        )

        st.plotly_chart(fig_line, use_container_width=True)

        fig_pie = px.pie(
            names=["Safe", "Unsafe"],
            values=[safe_count, unsafe_count],
            title="MRL Compliance Distribution",
            hole=0.5
        )

        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📅 Risk Trend Over Time")
        
        trend = df.groupby("test_date")["risk_level"].apply(
            lambda x: (x == "Critical").sum()
        ).reset_index()
        
        fig_trend = px.line(
            trend,
            x="test_date",
            y="risk_level",
            title="Critical Risk Trend"
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)

        # ================= FARM ANALYSIS =================
        st.subheader("🏭 Farm-wise Risk Analysis")

        farm_summary = df.groupby("farm_id")["mrl"].mean().reset_index()

        fig_bar = px.bar(
            farm_summary,
            x="farm_id",
            y="mrl",
            title="Average Residue Level per Farm",
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

        # ================= AI INSIGHT =================
        max_farm = farm_summary.loc[farm_summary["mrl"].idxmax(), "farm_id"]

        st.warning(f"⚠️ Farm {max_farm} shows highest residue levels. Inspection required.")

# ===============================
# AMU RECORDS
# ===============================
elif page == "AMU Records":
    df = get_data()

    csv = df.to_csv(index=False)

    st.download_button(
        label="📥 Download Data",
        data=csv,
        file_name="amu_records.csv",
        mime="text/csv"
    )

    search = st.text_input("Search by Drug Name")

    if search:
        df = df[df["drug_name"].str.contains(search, case=False)]

    st.dataframe(df, use_container_width=True)


# ===============================
# ANALYTICS
# ===============================
elif page == "Analytics":

    import plotly.express as px
    import pandas as pd

    st.title("📊 Advanced Analytics")

    df = get_data()

    # Normalize column names
    df.columns = df.columns.str.lower()

    # CREATE prediction column if missing
    if "prediction" not in df.columns:
        if "residue_mg_per_kg" in df.columns and "mrl_limit_mg_per_kg" in df.columns:
            df["prediction"] = df.apply(
                lambda row: "Unsafe"
                if row["residue_mg_per_kg"] > row["mrl_limit_mg_per_kg"]
                else "Safe",
                axis=1
            )
        else:
            st.error("Required columns not found: residue_mg_per_kg or mrl_limit_mg_per_kg")
            st.stop()


    if df.empty:
        st.warning("No data available")
        st.stop()

    # ===============================
    # BASIC STATS
    # ===============================
    total = len(df)

    safe_count = len(df[df["prediction"] == "Safe"])
    unsafe_count = len(df[df["prediction"] == "Unsafe"])

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Records", total)
    col2.metric("Safe", safe_count)
    col3.metric("Unsafe", unsafe_count)

    # ===============================
    # SAFETY DISTRIBUTION
    # ===============================
    st.subheader("📌 Safety Distribution")

    fig = px.pie(
        df,
        names="prediction",
        title="Safe vs Unsafe",
        hole=0.4
    )

    st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # DOSE vs SAFETY
    # ===============================
    st.subheader("💊 Dose vs Safety")

    fig = px.scatter(
        df,
        x="dose_mg",
        y="treatment_days",
        color="prediction",
        size_max=10,
        title="Dose vs Treatment Duration"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # HIGH RISK DRUGS
    # ===============================
    if "drug_name" in df.columns:

        st.subheader("🚨 High Risk Drugs")

        drug_counts = (
            df[df["prediction"] == "Unsafe"]
            .groupby("drug_name")
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        fig = px.bar(
            drug_counts.head(10),
            x="drug_name",
            y="count",
            title="Top Unsafe Drugs",
            color="count"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # TIME TREND (if date exists)
    # ===============================
    if "test_date" in df.columns:

        st.subheader("📅 Trend Over Time")

        df["test_date"] = pd.to_datetime(df["test_date"])

        trend = (
            df.groupby("test_date")["prediction"]
            .count()
            .reset_index()
        )

        fig = px.line(
            trend,
            x="test_date",
            y="prediction",
            title="Records Over Time"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # RISK SCORE (OPTIONAL)
    # ===============================
    st.subheader("⚠️ Risk Level Summary")

    df["risk_flag"] = df["prediction"].apply(
        lambda x: "High Risk" if x == "Unsafe" else "Low Risk"
    )

    risk_counts = df["risk_flag"].value_counts().reset_index()
    risk_counts.columns = ["Risk Level", "Count"]

    fig = px.bar(
        risk_counts,
        x="Risk Level",
        y="Count",
        color="Risk Level",
        title="Risk Summary"
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# AI PREDICTION
# ===============================
elif page == "AI Prediction":

    from datetime import datetime
    import time
    import requests
    

    st.title("🤖 AI Prediction")

    st.subheader("🔮 AI Residue Prediction")

    dose = st.number_input("Dose (mg)", value=500.0)
    days = st.number_input("Days", value=5)
    mrl = st.number_input("MRL", value=0.01)

    if st.button("Predict Safety"):

        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                json={"dose": dose, "days": days, "mrl": mrl}
            )

            data = response.json()

            result = data.get("prediction")
            risk_score = float(data.get("risk_score", 0))
            confidence = float(data.get("confidence", 0))

            st.progress(risk_score / 100)

            st.metric("📊 Risk Score", f"{round(risk_score, 2)}%")
            st.write(f"Confidence: {round(confidence, 2)}%")

        except:
            st.error("Backend error")
            st.stop()

        import sqlite3
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create table (safe)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dose_mg REAL,
            treatment_days INTEGER,
            days_after_treatment INTEGER,
            prediction TEXT
        )
        """)

        # Insert prediction
        cursor.execute("""
        INSERT INTO predictions (dose_mg, treatment_days, days_after_treatment, prediction)
        VALUES (?, ?, ?, ?)
        """, (dose, days, days, result))
        
        conn.commit()
        conn.close()

        if result == "Unsafe":
            st.error(result)
        else:
            st.success(result)

        if risk_score < 30:
            st.success("🟢 Low Risk")
        elif risk_score < 70:
            st.warning("🟡 Medium Risk")
        else:
            st.error("🔴 High Risk")

        st.write("Confidence:", confidence)

        # 🔽 ADD HERE
        st.subheader("📋 Input Summary")

        st.write({
            "Dose": dose,
            "Days": days,
            "MRL": mrl,
            "Prediction": result,
            "Confidence": confidence
        })

        from datetime import datetime
        
        st.caption(f"Predicted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # ===============================
        # 🤖 AI EXPLANATION
        # ===============================
        st.subheader("🤖 AI Explanation")
        
        if dose > 400 and days > 4:
            st.warning("⚠️ High dose and long duration increase residue risk.")
        elif dose > 400:
            st.warning("⚠️ Dose is high — may lead to unsafe residue.")
        elif days > 4:
            st.warning("⚠️ Long treatment duration increases risk.")
        else:
            st.success("✅ Safe usage pattern.")
       

        # ===============================
        # 🚨 REAL-TIME ALERT
        # ===============================
        if risk_score > 80:
            st.error("🚨 CRITICAL ALERT: Immediate action required!")

# ===============================
# HISTORY
# ===============================
elif page == "Prediction History":

    st.title("📜 Prediction History")

    try:
        conn = sqlite3.connect(DB_PATH)

        df = pd.read_sql_query(
            "SELECT * FROM predictions ORDER BY id DESC", conn
        )

        conn.close()

        if df.empty:
            st.warning("No prediction history available")
        else:
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"History error: {e}")
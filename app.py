import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os
from dotenv import load_dotenv

st.set_page_config(
    page_title="📦 AI Inventory Control & Cost Tracking",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 AI Inventory Control & Cost Tracking")
st.caption("Prototype v1.0 - Auto Analysis + AI Insight + Chat Mode")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

def generate_ai_commentary(df: pd.DataFrame) -> str:
    if not client:
        return "⚠ AI Commentary tidak aktif (API Key belum diatur)."

    text_summary = df.to_string(index=False)
    prompt = f"""
    Berikut adalah data inventory beserta stok dan biaya per unit:
    {text_summary}

    Buat analisis singkat dalam bahasa Indonesia:
    - Barang mana yang paling kritis stoknya
    - Barang mana yang menghabiskan biaya terbesar
    - Rekomendasi strategi pengendalian stok
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error AI Commentary: {e}"

uploaded_file = st.file_uploader("📂 Upload data Inventory (Excel/CSV)",
                                 type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📑 Data Preview")
    st.dataframe(df.head())

    if not all(col in df.columns for col in ["Item", "Stock", "Unit_Cost"]):
        st.warning("⚠ Data harus memiliki kolom: Item, Stock, Unit_Cost")
    else:
        df["Total_Cost"] = df["Stock"] * df["Unit_Cost"]

        st.subheader("📊 Inventory Dashboard")

        query = """
        SELECT Item, Stock, Unit_Cost, Total_Cost
        FROM df
        ORDER BY Total_Cost DESC
        """
        inventory = duckdb.sql(query).df()

        fig = px.bar(inventory, x="Item", y="Total_Cost",
                     title="Inventory Cost by Item", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📝 Auto Rule-based Insight")

        highest_cost = inventory.iloc[0]
        lowest_stock = inventory.sort_values("Stock").iloc[0]

        rule_text = f"""
        🔍 *Insights*:
        - Barang dengan biaya terbesar: *{highest_cost['Item']}* total biaya *Rp {highest_cost['Total_Cost']:,.0f}*
        - Barang dengan stok paling kritis: *{lowest_stock['Item']}* hanya *{lowest_stock['Stock']} unit*
        """
        st.markdown(rule_text)

        st.subheader("🤖 AI Commentary")
        st.write(generate_ai_commentary(inventory))

        st.subheader("💬 Chat dengan AI Inventory Analyst")

else:
    st.info("⬆ Upload file Excel/CSV untuk memulai.")

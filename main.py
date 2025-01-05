import streamlit as st
import os
import logging
import google.generativeai as genai
from Analysis import StockAnalysisPipeline
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(page_title="Stock Analysis App", layout="wide")
    st.title("📈 Stock Analysis App")
    st.subheader("Analyze stock data and generate detailed insights.")
    
    st.sidebar.title("🔍 Company Symbol")
    stock_data = pd.read_csv("stock.csv")
    suggestions = sorted(stock_data["Symbol"].unique())
    company_symbol = st.sidebar.selectbox("Enter company symbol", suggestions)

    if st.sidebar.button("Run Analysis"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current_step, total_steps):
            progress = current_step / total_steps
            progress_bar.progress(progress)
            status_text.text(f"Processing... {int(progress * 100)}%")

        with st.spinner("🔄 Analyzing... Average wait time: 01 Min"):
            pipeline = StockAnalysisPipeline(
                company=company_symbol,
                genai=genai,
                api_key = os.getenv('GENAI_API_KEY'),
                exchange="NSE"
            )
            pipeline.run_pipeline(progress_callback=update_progress)
        
        st.success(f"✅ Analysis completed for {company_symbol}")
        
        try:
            with open(f"C{company_symbol}_analysis.md", "r", encoding="utf-8") as md_file:
                st.markdown(md_file.read())

        except FileNotFoundError:
            st.error("Markdown file not found. Please check if the pipeline generated it.")

if __name__ == "__main__":
    main()
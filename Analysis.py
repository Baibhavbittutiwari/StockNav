import logging
from Scraper import StockScraper
from Content import ContentGenerator
import time

logger = logging.getLogger(__name__)

class StockAnalysisPipeline:
    """
    Orchestrates the entire process:
      1. Scrape stock data
      2. Generate analysis
      3. Display or return results
    """

    def __init__(self, company, genai, api_key, exchange="NSE"):
        """
        :param genai: The generative AI module to be used in content generation.
        :param api_key: The API key required by the generative AI service.
        :param exchange: The stock exchange symbol.
        """
        self.stock = company.upper()
        self.scraper = StockScraper(company=self.stock, exchange=exchange)
        self.generator = ContentGenerator(genai=genai, api_key=api_key)

    def run_pipeline(self, progress_callback=None):
        """
        Execute the pipeline with a given company stock ticker or symbol and optional progress callback.
        """
        logger.info("Starting stock analysis pipeline...")
        steps = 3

        # Step 1: Scrape stock properties
        stock_data = self.scraper.get_stock_properties()
        if "error" in stock_data:
            logger.error("Error scraping stock data. Pipeline will stop.")
            return

        if progress_callback:
            progress_callback(1, steps)

        # Step 2: Generate analysis content
        try:
            prompt = (
                "Generate an in-depth and actionable stock analysis report covering the following sections:\n\n"
                "1. **Company Overview**: Provide a concise description of the company, its industry, and its current stock price, including a brief note on recent performance trends.\n"
                "2. **Key Metrics**: Highlight essential financial metrics (e.g., P/E ratio, Industry P/E ratio, EPS, ROE) and discuss significant observations or anomalies.\n"
                "3. **SWOT Analysis**: Identify and elaborate on the company's Strengths, Weaknesses, Opportunities, and Threats, emphasizing factors that influence stock performance. Please not consider book value vs stock value.\n"
                "4. **Recent News Highlights**: Summarize key news or events affecting the company, focusing on their potential impact on stock performance.\n"
                "5. **Technical Analysis**: provide a visual rating based on voting given in technical analysis(e.g., in star format).\n"
                "6. **Investment Recommendation**: Offer a clear recommendation (Buy, Sell, or Hold) for the next 3-6 months, supported by both technical and fundamental analysis insights.\n\n"
                "Ensure the report is well-structured, jargon-free, and focuses on delivering actionable insights over raw data. Use the provided data as the basis for your analysis:\n"
                f"**Company**: {stock_data}\n"
            )
            logger.info("Creating prompt for generative model.")
        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            return
        analysis_result = self.generator.generate_content(prompt)

        if progress_callback:
            progress_callback(2, steps)

        # Step 3: Save markdown file
        file_path = f"{self.stock}_analysis.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)
        
        if progress_callback:
            progress_callback(3, steps)
        
        if analysis_result:
            logger.info("Analysis successfully generated.")
        else:
            logger.error("Stock analysis failed to generate content.")

# Example usage
# if __name__ == "__main__":
#     genai = None  # Your generative AI module
#     api_key = # your api key
#     pipeline = StockAnalysisPipeline(company="RELIANCE", genai=genai, api_key=api_key)
#     pipeline.run_pipeline()
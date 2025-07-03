import argparse
import subprocess
import sys
import os
import pandas as pd

from src.crawler.coupang_crawler import CoupangCrawler
from src.etl.transformer import ReviewTransformer
from src.db.database_handler import DatabaseHandler
from src.ml.review_model import SentimentAnalyzer
from src.report.report_generator import ReportGenerator
from src.utils.logger import logger

def run_pipeline(keyword, pages):
    logger.info(f"Starting full pipeline for keyword: {keyword} (pages: {pages})")
    
    db_handler = DatabaseHandler()
    db_handler.create_tables()

    # 1. Crawling
    crawler = CoupangCrawler()
    raw_reviews = crawler.search_products_and_crawl_reviews(keyword, pages=pages)
    logger.info(f"Finished crawling. Collected {len(raw_reviews)} raw reviews.")

    if not raw_reviews:
        logger.warning("No reviews collected. Skipping ETL, ML, and Reporting.")
        return

    # 2. ETL
    transformer = ReviewTransformer()
    transformed_reviews = transformer.transform(raw_reviews)
    logger.info(f"Finished ETL. Transformed {len(transformed_reviews)} reviews.")

    # 3. Save to DB
    db_handler.insert_reviews(transformed_reviews)
    logger.info("Reviews inserted into database.")

    # 4. ML Analysis
    all_reviews_df = transformer.to_dataframe(db_handler.get_all_reviews())
    if not all_reviews_df.empty and '리뷰본문' in all_reviews_df.columns:
        sentiment_analyzer = SentimentAnalyzer()
        # Filter out empty review content before sending to ML model
        non_empty_reviews = all_reviews_df[all_reviews_df['리뷰본문'].astype(bool)]['리뷰본문'].tolist()
        if non_empty_reviews:
            sentiments = sentiment_analyzer.analyze_sentiment(non_empty_reviews)
            # Add sentiment labels to the DataFrame
            sentiment_map = {text: s['label'] for text, s in zip(non_empty_reviews, sentiments)}
            all_reviews_df['sentiment_label'] = all_reviews_df['리뷰본문'].map(sentiment_map)
            logger.info("ML sentiment analysis completed and added to DataFrame.")
        else:
            logger.info("No review content to analyze sentiment.")
    else:
        logger.info("No review content column found or DataFrame is empty for ML analysis.")

    # 5. Report Generation
    report_generator = ReportGenerator()
    summary_report = report_generator.generate_summary_report(all_reviews_df)
    logger.info("\n" + "="*50 + "\nSummary Report:\n" + summary_report + "\n" + "="*50)

    logger.info("Full pipeline execution completed successfully.")

def start_web_ui():
    logger.info("Starting Flask Web UI...")
    project_root = os.path.dirname(os.path.abspath(__file__))
    api_main_path = os.path.join(project_root, 'src', 'api', 'main.py')

    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = project_root + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = project_root

    try:
        process = subprocess.Popen([sys.executable, api_main_path], env=env)
        logger.info(f"Flask Web UI started on http://127.0.0.1:5000. PID: {process.pid}")
        logger.info("Press Ctrl+C to stop the Flask server.")
        process.wait() # Wait for the process to terminate
    except Exception as e:
        logger.error(f"Failed to start Flask Web UI: {e}")

def start_dashboard():
    logger.info("Starting Streamlit Dashboard...")
    project_root = os.path.dirname(os.path.abspath(__file__))
    dashboard_app_path = os.path.join(project_root, 'src', 'dashboard', 'app.py')

    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = project_root + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = project_root

    try:
        process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', dashboard_app_path], env=env)
        logger.info(f"Streamlit Dashboard started. Check your browser for http://localhost:8501. PID: {process.pid}")
        logger.info("Press Ctrl+C to stop the Streamlit server.")
        process.wait() # Wait for the process to terminate
    except Exception as e:
        logger.error(f"Failed to start Streamlit Dashboard: {e}")

def import_csv_to_db(csv_file_path):
    logger.info(f"Importing data from CSV: {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path)
        # Convert DataFrame to list of dictionaries for transformer
        raw_reviews = df.to_dict(orient='records')

        db_handler = DatabaseHandler()
        db_handler.create_tables()

        transformer = ReviewTransformer()
        transformed_reviews = transformer.transform(raw_reviews)

        db_handler.insert_reviews(transformed_reviews)
        logger.info(f"Successfully imported {len(transformed_reviews)} reviews from CSV to database.")

        # Optionally run ML analysis and report generation after import
        all_reviews_df = transformer.to_dataframe(db_handler.get_all_reviews())
        if not all_reviews_df.empty and '리뷰본문' in all_reviews_df.columns:
            sentiment_analyzer = SentimentAnalyzer()
            non_empty_reviews = all_reviews_df[all_reviews_df['리뷰본문'].astype(bool)]['리뷰본문'].tolist()
            if non_empty_reviews:
                sentiments = sentiment_analyzer.analyze_sentiment(non_empty_reviews)
                if sentiments: # Check if sentiments is not None or empty
                    # Add sentiment labels to the DataFrame, filtering out None sentiments
                    sentiment_map = {text: s['label'] for text, s in zip(non_empty_reviews, sentiments) if s is not None and 'label' in s}
                    all_reviews_df['sentiment_label'] = all_reviews_df['리뷰본문'].map(sentiment_map)
                    logger.info("ML sentiment analysis completed and added to DataFrame.")
                else:
                    logger.warning("Sentiment analysis returned no valid results.")
            else:
                logger.info("No review content to analyze sentiment.")
        else:
            logger.info("No review content column found or DataFrame is empty for ML analysis.")

        report_generator = ReportGenerator()
        summary_report = report_generator.generate_summary_report(all_reviews_df)
        logger.info("\n" + "="*50 + "\nSummary Report:\n" + summary_report + "\n" + "="*50)

    except FileNotFoundError:
        logger.error(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        logger.error(f"Error importing CSV to DB: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coupang Review Analysis System")
    parser.add_argument('--crawl', action='store_true', help='Run the full crawling, ETL, ML, and reporting pipeline.')
    parser.add_argument('--keyword', type=str, help='Keyword to search for (required with --crawl).')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to crawl (default: 1).')
    parser.add_argument('--web-ui', action='store_true', help='Start the Flask web UI.')
    parser.add_argument('--dashboard', action='store_true', help='Start the Streamlit dashboard.')
    parser.add_argument('--import-csv', type=str, help='Path to a CSV file to import into the database.')

    args = parser.parse_args()

    if args.crawl:
        if not args.keyword:
            parser.error("--keyword is required when --crawl is used.")
        run_pipeline(args.keyword, args.pages)
    elif args.import_csv:
        import_csv_to_db(args.import_csv)
    elif args.web_ui:
        start_web_ui()
    elif args.dashboard:
        start_dashboard()
    else:
        print("Please specify an action: --crawl, --import-csv, --web-ui, or --dashboard.")
        parser.print_help()
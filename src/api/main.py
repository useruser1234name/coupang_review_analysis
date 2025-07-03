from flask import Flask, request, jsonify, render_template
from src.crawler.coupang_crawler import CoupangCrawler
from src.etl.transformer import ReviewTransformer
from src.db.database_handler import DatabaseHandler
from src.ml.review_model import SentimentAnalyzer
from src.utils.logger import logger
import threading
import os

app = Flask(__name__)

crawler = CoupangCrawler()
transformer = ReviewTransformer()
db_handler = DatabaseHandler()
sentiment_analyzer = SentimentAnalyzer() # Initialize sentiment analyzer

# Ensure database tables exist on startup
try:
    db_handler.create_tables()
except Exception as e:
    logger.error(f"Failed to create database tables on app startup: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl_and_analyze():
    keyword = request.json.get('keyword')
    pages = request.json.get('pages', 1) # Default to 1 page if not specified

    if not keyword:
        return jsonify({'status': 'error', 'message': 'Keyword is required.'}), 400

    logger.info(f"Received request to crawl for keyword: {keyword} (pages: {pages})")

    def run_pipeline():
        try:
            logger.info(f"Starting crawling for '{keyword}'...")
            raw_reviews = crawler.search_products_and_crawl_reviews(keyword, pages=pages)
            logger.info(f"Finished crawling. Collected {len(raw_reviews)} raw reviews.")

            if not raw_reviews:
                logger.warning("No reviews collected. Skipping ETL and ML.")
                return

            logger.info("Starting ETL process...")
            transformed_reviews = transformer.transform(raw_reviews)
            logger.info(f"Finished ETL. Transformed {len(transformed_reviews)} reviews.")

            logger.info("Inserting reviews into database...")
            db_handler.insert_reviews(transformed_reviews)
            logger.info("Reviews inserted into database.")

            # Fetch reviews from DB for ML analysis (including newly added ones)
            all_reviews_df = transformer.to_dataframe(db_handler.get_all_reviews())
            
            if not all_reviews_df.empty and '리뷰본문' in all_reviews_df.columns:
                logger.info("Starting ML sentiment analysis...")
                # Only analyze reviews that don't have sentiment yet or re-analyze all
                reviews_to_analyze = all_reviews_df[all_reviews_df['리뷰본문'].astype(bool)]['리뷰본문'].tolist()
                if reviews_to_analyze:
                    sentiments = sentiment_analyzer.analyze_sentiment(reviews_to_analyze)
                    # Update sentiment in DataFrame (this part needs to be handled carefully if updating DB)
                    # For simplicity, we'll assume sentiment is added to the DataFrame for dashboard use
                    # and not persisted back to DB in this basic setup.
                    # In a real app, you'd update the DB with sentiment results.
                    logger.info("ML sentiment analysis completed.")
                else:
                    logger.info("No review content to analyze sentiment.")
            else:
                logger.info("No review content column found or DataFrame is empty for ML analysis.")

            logger.info("Pipeline execution completed successfully.")

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")

    # Run the pipeline in a separate thread to avoid blocking the Flask response
    thread = threading.Thread(target=run_pipeline)
    thread.start()

    return jsonify({'status': 'success', 'message': 'Crawling and analysis started in background.'}), 202

if __name__ == '__main__':
    # Create a templates directory for Flask
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
        
    # Create a simple index.html
    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coupang Review Crawler</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
        .container { background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; }
        input[type="text"], input[type="number"] { width: calc(100% - 22px); padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; }
        button:hover { background-color: #0056b3; }
        #status { margin-top: 20px; padding: 10px; border-radius: 4px; background-color: #e9ecef; color: #333; }
        .dashboard-link { display: block; text-align: center; margin-top: 20px; }
        .dashboard-link a { color: #007bff; text-decoration: none; font-weight: bold; }
        .dashboard-link a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Coupang Review Crawler & Analyzer</h1>
        <label for="keyword">Product Keyword:</label>
        <input type="text" id="keyword" placeholder="e.g., 아이폰">
        
        <label for="pages">Number of Pages to Crawl (max 5):</label>
        <input type="number" id="pages" value="1" min="1" max="5">

        <button onclick="startCrawl()">Start Crawling & Analysis</button>
        <div id="status"></div>
        <div class="dashboard-link">
            <p>View Analysis Dashboard:</p>
            <a href="http://localhost:8501" target="_blank">Open Streamlit Dashboard</a>
        </div>
    </div>

    <script>
        function startCrawl() {
            const keyword = document.getElementById('keyword').value;
            const pages = document.getElementById('pages').value;
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = 'Starting...';

            fetch('/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keyword: keyword, pages: parseInt(pages) }),
            })
            .then(response => response.json())
            .then(data => {
                statusDiv.textContent = data.message;
                if (data.status === 'success') {
                    statusDiv.style.backgroundColor = '#d4edda';
                    statusDiv.style.color = '#155724';
                } else {
                    statusDiv.style.backgroundColor = '#f8d7da';
                    statusDiv.style.color = '#721c24';
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                statusDiv.textContent = 'Error starting crawl.';
                statusDiv.style.backgroundColor = '#f8d7da';
                statusDiv.style.color = '#721c24';
            });
        }
    </script>
</body>
</html>
""")

    app.run(debug=True, port=5000)

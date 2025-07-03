import pandas as pd
from src.utils.logger import logger

class ReportGenerator:
    def __init__(self):
        logger.info("ReportGenerator initialized.")

    def generate_summary_report(self, df: pd.DataFrame):
        """
        Generates a summary report from the review DataFrame.
        """
        if df.empty:
            logger.warning("DataFrame is empty, cannot generate report.")
            return "No data available for reporting."

        report_lines = []
        report_lines.append("--- Review Analysis Report ---")
        report_lines.append(f"Total Reviews: {len(df)}")
        report_lines.append(f"Unique Products: {df['상품명'].nunique()}")
        report_lines.append(f"Average Rating: {df['평점'].mean():.2f} / 5.0")

        # Sentiment distribution (if sentiment analysis was performed)
        if 'sentiment_label' in df.columns:
            sentiment_counts = df['sentiment_label'].value_counts(normalize=True) * 100
            report_lines.append("\nSentiment Distribution:")
            for sentiment, percentage in sentiment_counts.items():
                report_lines.append(f"  - {sentiment.capitalize()}: {percentage:.2f}%")

        # Top N products by review count
        top_products = df['상품명'].value_counts().head(5)
        report_lines.append("\nTop 5 Products by Review Count:")
        for product, count in top_products.items():
            report_lines.append(f"  - {product}: {count} reviews")

        # Top N products by average rating
        avg_ratings = df.groupby('상품명')['평점'].mean().sort_values(ascending=False).head(5)
        report_lines.append("\nTop 5 Products by Average Rating:")
        for product, rating in avg_ratings.items():
            report_lines.append(f"  - {product}: {rating:.2f}")

        # Reviews over time (simple count per day/month)
        if 'created_at' in df.columns and not df['created_at'].isnull().all():
            df['review_date'] = pd.to_datetime(df['created_at']).dt.date
            reviews_per_date = df['review_date'].value_counts().sort_index()
            report_lines.append("\nReviews per Date (Top 5 recent):")
            for date, count in reviews_per_date.tail(5).items():
                report_lines.append(f"  - {date}: {count} reviews")

        logger.info("Summary report generated.")
        return "\n".join(report_lines)

    def get_product_review_stats(self, df: pd.DataFrame):
        """
        Returns product-wise review statistics.
        """
        if df.empty:
            return pd.DataFrame()
        
        product_stats = df.groupby('상품명').agg(
            total_reviews=('리뷰제목', 'count'),
            average_rating=('평점', 'mean')
        ).reset_index()
        product_stats['average_rating'] = product_stats['average_rating'].round(2)
        return product_stats

    def get_sentiment_distribution(self, df: pd.DataFrame):
        """
        Returns the distribution of sentiments.
        """
        if df.empty or 'sentiment_label' not in df.columns:
            return pd.Series()
        return df['sentiment_label'].value_counts(normalize=True)

    def get_reviews_over_time(self, df: pd.DataFrame):
        """
        Returns review counts over time.
        """
        if df.empty or 'created_at' not in df.columns or df['created_at'].isnull().all():
            return pd.Series()
        df['review_date'] = pd.to_datetime(df['created_at']).dt.date
        return df['review_date'].value_counts().sort_index()


if __name__ == "__main__":
    # Example usage for testing
    data = {
        '상품명': ['A', 'A', 'B', 'A', 'B', 'C'],
        '평점': [5, 4, 3, 5, 2, 5],
        '리뷰본문': ['Good', 'Okay', 'Bad', 'Great', 'Terrible', 'Excellent'],
        'sentiment_label': ['positive', 'positive', 'negative', 'positive', 'negative', 'positive'],
        'created_at': ['2023.01.01', '2023.01.02', '2023.01.01', '2023.01.03', '2023.01.02', '2023.01.03']
    }
    sample_df = pd.DataFrame(data)
    sample_df['created_at'] = pd.to_datetime(sample_df['created_at'])

    generator = ReportGenerator()
    report = generator.generate_summary_report(sample_df)
    logger.info(report)

    product_stats = generator.get_product_review_stats(sample_df)
    logger.info(f"\nProduct Stats:\n{product_stats}")

    sentiment_dist = generator.get_sentiment_distribution(sample_df)
    logger.info(f"\nSentiment Distribution:\n{sentiment_dist}")

    reviews_over_time = generator.get_reviews_over_time(sample_df)
    logger.info(f"\nReviews Over Time:\n{reviews_over_time}")
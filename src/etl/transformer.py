import pandas as pd
from src.utils.logger import logger
import re # Import re module

class ReviewTransformer:
    def __init__(self):
        logger.info("ReviewTransformer initialized.")

    def transform(self, raw_reviews):
        """
        Transforms raw review data into a structured format suitable for database insertion.
        This can include data cleaning, type conversion, normalization, etc.
        """
        if not raw_reviews:
            logger.warning("No raw reviews to transform.")
            return []

        transformed_reviews = []
        for review_dict in raw_reviews:
            processed_review = review_dict.copy()

            # Handle NaN for string fields by converting to empty string
            string_fields = [
                "상품명", "브랜드", "가격", "쿠팡상품번호", "옵션",
                "리뷰제목", "리뷰본문", "작성자", "판매자",
                "실제구매상품명", "이미지들", "설문응답"
            ]
            for field in string_fields:
                if pd.isna(processed_review.get(field)):
                    processed_review[field] = ""
                elif not isinstance(processed_review[field], str):
                    processed_review[field] = str(processed_review[field]) # Ensure it's a string

            # Convert '평점' to float
            try:
                processed_review['평점'] = float(processed_review.get('평점', 0)) if processed_review.get('평점') else 0.0
            except ValueError:
                logger.warning(f"Could not convert rating '{processed_review.get('평점')}' to float. Setting to 0.0.")
                processed_review['평점'] = 0.0

            # Convert '도움수' to int, extracting number from string like '48 명에게 도움 됨'
            try:
                helpful_text = str(processed_review.get('도움수', '0'))
                match = re.search(r'(\d+)', helpful_text)
                if match:
                    processed_review['도움수'] = int(match.group(1))
                else:
                    processed_review['도움수'] = 0
            except ValueError:
                logger.warning(f"Could not convert helpful_count '{processed_review.get('도움수')}' to int. Setting to 0.")
                processed_review['도움수'] = 0

            # Clean up string fields (strip whitespace) - apply after NaN handling
            for key, value in processed_review.items():
                if isinstance(value, str):
                    processed_review[key] = value.strip()

            transformed_reviews.append(processed_review)

        logger.info(f"Transformed {len(transformed_reviews)} reviews.")
        return transformed_reviews

    def to_dataframe(self, reviews_data):
        """
        Converts a list of review dictionaries into a pandas DataFrame.
        Useful for ML processing and dashboard visualization.
        """
        if not reviews_data:
            logger.warning("No review data to convert to DataFrame.")
            return pd.DataFrame()
        
        df = pd.DataFrame(reviews_data)

        # Map SQLAlchemy column names to Korean names for consistency with dashboard/report
        column_mapping = {
            'product_name': '상품명',
            'brand': '브랜드',
            'price': '가격',
            'coupang_product_id': '쿠팡상품번호',
            'option': '옵션',
            'review_title': '리뷰제목',
            'review_content': '리뷰본문',
            'review_page': '리뷰페이지',
            'author': '작성자',
            'rating': '평점',
            'created_at': '작성일',
            'seller': '판매자',
            'actual_purchase_product_name': '실제구매상품명',
            'images': '이미지들',
            'survey_response': '설문응답',
            'helpful_count': '도움수'
        }
        # Apply mapping only if the column exists in the DataFrame
        df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)

        logger.info(f"Converted {len(reviews_data)} reviews to DataFrame with shape {df.shape}.")
        return df

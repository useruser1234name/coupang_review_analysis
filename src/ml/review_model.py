from transformers import pipeline
from src.utils.logger import logger
import pandas as pd

class SentimentAnalyzer:
    def __init__(self, model_name="snunlp/KR-FinBert-SC"): # A more suitable sentiment model
        self.model_name = model_name
        self.sentiment_pipeline = None
        try:
            # Attempt to load a sentiment analysis pipeline. 
            # Note: A specific sentiment analysis model might be needed, 
            # this is a general Korean ELECTRA model.
            # For actual sentiment analysis, you might need a model fine-tuned for sentiment.
            # Example: 'snunlp/KR-FinBert-SC'
            self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
            logger.info(f"Sentiment analysis pipeline loaded with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentiment analysis model {model_name}: {e}")
            logger.warning("Sentiment analysis will not be available.")

    def analyze_sentiment(self, texts):
        if not self.sentiment_pipeline:
            logger.warning("Sentiment analysis pipeline not loaded. Returning empty results.")
            return [None] * len(texts)
        
        logger.info(f"Analyzing sentiment for {len(texts)} texts...")
        try:
            results = self.sentiment_pipeline(texts)
            # The output format might vary based on the model. 
            # Assuming it returns a list of dicts like [{'label': 'LABEL_0', 'score': 0.99}]
            # We'll map labels to 'positive', 'negative', or 'neutral' and return scores.
            sentiments = []
            for res in results:
                label = res['label']
                score = res['score']
                if "positive" in label.lower() or "pos" in label.lower() or label == "LABEL_1": # Adjust based on model's actual labels
                    sentiments.append({"label": "positive", "score": score})
                elif "negative" in label.lower() or "neg" in label.lower() or label == "LABEL_0": # Adjust based on model's actual labels
                    sentiments.append({"label": "negative", "score": score})
                else:
                    sentiments.append({"label": "neutral", "score": score})
            logger.info("Sentiment analysis completed.")
            return sentiments
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {e}")
            return [None] * len(texts)

class ReviewSummarizer:
    def __init__(self, model_name="gogamza/kobart-base-v2"): # Example Korean summarization model
        self.model_name = model_name
        self.summarization_pipeline = None
        try:
            self.summarization_pipeline = pipeline("summarization", model=model_name)
            logger.info(f"Summarization pipeline loaded with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load summarization model {model_name}: {e}")
            logger.warning("Review summarization will not be available.")

    def summarize_reviews(self, texts, max_length=150, min_length=30):
        if not self.summarization_pipeline:
            logger.warning("Summarization pipeline not loaded. Returning empty results.")
            return [None] * len(texts)

        logger.info(f"Summarizing {len(texts)} reviews...")
        try:
            summaries = self.summarization_pipeline(texts, max_length=max_length, min_length=min_length, do_sample=False)
            logger.info("Review summarization completed.")
            return [s['summary_text'] for s in summaries]
        except Exception as e:
            logger.error(f"Error during review summarization: {e}")
            return [None] * len(texts)

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Ensure you have the necessary models downloaded or internet access
    # For sentiment analysis, a model specifically fine-tuned for sentiment is recommended.
    # For example, you might need to search for a Korean sentiment model on Hugging Face.
    # If you encounter issues, try a simpler model or ensure your environment is set up for large model downloads.

    # Sentiment Analysis Example
    sentiment_analyzer = SentimentAnalyzer(model_name="snunlp/KR-FinBert-SC") # A more suitable sentiment model
    sample_texts = [
        "이 제품 정말 좋아요! 강력 추천합니다.",
        "배송이 너무 느리고 제품도 기대 이하였어요.",
        "그냥 그래요. 나쁘지도 좋지도 않아요."
    ]
    sentiments = sentiment_analyzer.analyze_sentiment(sample_texts)
    for text, sentiment in zip(sample_texts, sentiments):
        logger.info(f"Text: {text} -> Sentiment: {sentiment}")

    # Review Summarization Example
    summarizer = ReviewSummarizer()
    long_review = """
    이 노트북은 정말 최고입니다. 디자인도 너무 예쁘고, 성능도 뛰어나서 게임이나 영상 편집 작업도 문제없이 할 수 있어요. 
    배터리도 오래가서 외부에서 작업할 때도 걱정 없습니다. 다만, 가격이 조금 비싸다는 점이 아쉽지만, 
    그만큼의 가치를 충분히 한다고 생각합니다. 키보드 타건감도 좋고, 화면도 선명해서 눈이 편안합니다. 
    전반적으로 매우 만족스러운 구매였습니다. 다음에도 이 브랜드 제품을 구매할 것 같아요.
    """
    summaries = summarizer.summarize_reviews([long_review])
    for summary in summaries:
        logger.info(f"Original: {long_review}\nSummary: {summary}")

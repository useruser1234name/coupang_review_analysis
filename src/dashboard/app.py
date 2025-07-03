import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from src.db.database_handler import DatabaseHandler
from src.ml.review_model import SentimentAnalyzer
from src.etl.transformer import ReviewTransformer
from src.utils.logger import logger

# Initialize components
db_handler = DatabaseHandler()
sentiment_analyzer = SentimentAnalyzer() # This will load the model
transformer = ReviewTransformer()

st.set_page_config(layout="wide", page_title="Coupang Review Analysis Dashboard")

st.title("📊 Coupang Review Analysis Dashboard")

@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data():
    logger.info("Loading data from database...")
    reviews_raw = db_handler.get_all_reviews()
    df = transformer.to_dataframe(reviews_raw)
    
    if not df.empty and '리뷰본문' in df.columns:
        # Perform sentiment analysis if not already done or if you want to re-run
        # Check if sentiment_label column exists and is populated
        if 'sentiment_label' not in df.columns or df['sentiment_label'].isnull().all():
            logger.info("Performing sentiment analysis on review content...")
            # Filter out empty review content before sending to ML model
            non_empty_reviews = df[df['리뷰본문'].astype(bool)]['리뷰본문'].tolist()
            if non_empty_reviews:
                sentiments = sentiment_analyzer.analyze_sentiment(non_empty_reviews)
                if sentiments: # Check if sentiments is not None or empty
                    # Map sentiments back to the original DataFrame, filtering out None sentiments
                    sentiment_map = {text: s['label'] for text, s in zip(non_empty_reviews, sentiments) if s is not None and 'label' in s}
                    df['sentiment_label'] = df['리뷰본문'].map(sentiment_map)
                else:
                    logger.warning("Sentiment analysis returned no valid results.")
            else:
                df['sentiment_label'] = None
        else:
            logger.info("Sentiment analysis already present in data.")

    # Ensure 'created_at' is datetime type for time series analysis
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    
    logger.info(f"Data loaded. DataFrame shape: {df.shape}")
    return df

df = load_data()

if df.empty:
    st.warning("No review data available. Please run the crawler and ETL process first.")
else:
    st.sidebar.header("Filter Options")
    selected_product = st.sidebar.selectbox(
        "Select Product:",
        ["All Products"] + sorted(df['상품명'].unique().tolist())
    )

    filtered_df = df.copy()
    if selected_product != "All Products":
        filtered_df = df[df['상품명'] == selected_product]

    st.subheader(f"Analysis for: {selected_product}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total Reviews", value=len(filtered_df))
    with col2:
        avg_rating = filtered_df['평점'].mean()
        st.metric(label="Average Rating", value=f"{avg_rating:.2f} / 5.0")
    with col3:
        if 'sentiment_label' in filtered_df.columns and not filtered_df['sentiment_label'].isnull().all():
            positive_count = filtered_df[filtered_df['sentiment_label'] == 'positive'].shape[0]
            st.metric(label="Positive Reviews", value=positive_count)
        else:
            st.metric(label="Positive Reviews", value="N/A")

    st.markdown("--- ")

    # Product-wise Review Count and Average Rating
    if selected_product == "All Products":
        st.subheader("Product Overview: Review Count and Average Rating")
        product_stats = filtered_df.groupby('상품명').agg(
            total_reviews=('리뷰제목', 'count'),
            average_rating=('평점', 'mean')
        ).reset_index().sort_values(by='total_reviews', ascending=False)
        
        fig_product_stats = px.bar(product_stats, x='상품명', y='total_reviews',
                                   color='average_rating', title='Reviews per Product by Average Rating',
                                   hover_data=['average_rating'],
                                   labels={'total_reviews': 'Total Reviews', 'average_rating': 'Average Rating'})
        st.plotly_chart(fig_product_stats, use_container_width=True)

    # Sentiment Distribution
    if 'sentiment_label' in filtered_df.columns and not filtered_df['sentiment_label'].isnull().all():
        st.subheader("Sentiment Distribution")
        sentiment_counts = filtered_df['sentiment_label'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        fig_sentiment = px.pie(sentiment_counts, values='Count', names='Sentiment',
                               title='Distribution of Review Sentiments',
                               color_discrete_map={'positive':'green', 'negative':'red', 'neutral':'blue'})
        st.plotly_chart(fig_sentiment, use_container_width=True)

    # Reviews Over Time
    if 'created_at' in filtered_df.columns and not filtered_df['created_at'].isnull().all():
        st.subheader("Reviews Over Time")
        reviews_over_time = filtered_df.set_index('created_at').resample('D').size().reset_index(name='count')
        fig_time = px.line(reviews_over_time, x='created_at', y='count', title='Number of Reviews Over Time')
        st.plotly_chart(fig_time, use_container_width=True)

    # Word Cloud of Review Content
    st.subheader("Word Cloud of Review Content")
    text_content = " ".join(filtered_df['리뷰본문'].dropna().tolist())
    if text_content:
        wordcloud = WordCloud(width=800, height=400, background_color='white', font_path='malgun.ttf').generate(text_content)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.info("No review content to generate word cloud.")

    # Display Sample Reviews by Sentiment
    if 'sentiment_label' in filtered_df.columns and not filtered_df['sentiment_label'].isnull().all():
        st.subheader("Sample Reviews by Sentiment")
        sentiment_options = filtered_df['sentiment_label'].dropna().unique().tolist()
        if sentiment_options:
            selected_sentiment = st.selectbox("Select Sentiment to View:", sentiment_options)
            sample_reviews = filtered_df[filtered_df['sentiment_label'] == selected_sentiment][['리뷰제목', '리뷰본문', '평점', '작성자']].sample(min(5, len(filtered_df[filtered_df['sentiment_label'] == selected_sentiment])))
            st.dataframe(sample_reviews, use_container_width=True)
        else:
            st.info("No sentiments to display sample reviews.")

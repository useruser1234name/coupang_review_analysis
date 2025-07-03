from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import Config
from src.utils.logger import logger
import datetime

Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False)
    brand = Column(String(255))
    price = Column(String(50))
    coupang_product_id = Column(String(255))
    option = Column(Text)
    review_title = Column(String(500))
    review_content = Column(Text)
    review_page = Column(Integer)
    author = Column(String(255))
    rating = Column(Float) # 평점은 숫자로 저장
    created_at = Column(DateTime) # 작성일은 날짜/시간으로 저장
    seller = Column(String(255))
    actual_purchase_product_name = Column(String(255))
    images = Column(Text) # 이미지 URL들은 세미콜론으로 구분된 문자열로 저장
    survey_response = Column(Text)
    helpful_count = Column(Integer) # 도움수는 숫자로 저장

    def __repr__(self):
        return f"<Review(product_name='{self.product_name}', review_title='{self.review_title}')>"

class DatabaseHandler:
    def __init__(self):
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)

    def _create_engine(self):
        db_url = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}"
        try:
            engine = create_engine(db_url, echo=False) # echo=True for SQL logging
            logger.info("Database engine created successfully.")
            return engine
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created or already exist.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def insert_reviews(self, reviews_data):
        session = self.Session()
        try:
            for review_dict in reviews_data:
                # Convert '평점' to float, '도움수' to int, '작성일' to datetime
                try:
                    review_dict['평점'] = float(review_dict.get('평점', 0)) if review_dict.get('평점') else 0.0
                except ValueError: review_dict['평점'] = 0.0
                try:
                    review_dict['도움수'] = int(review_dict.get('도움수', 0)) if review_dict.get('도움수') else 0
                except ValueError: review_dict['도움수'] = 0
                try:
                    # Assuming '작성일' is in 'YYYY.MM.DD' format
                    review_dict['작성일'] = datetime.datetime.strptime(review_dict.get('작성일', ''), '%Y.%m.%d') if review_dict.get('작성일') else None
                except ValueError: review_dict['작성일'] = None

                review = Review(
                    product_name=review_dict.get('상품명', ''),
                    brand=review_dict.get('브랜드', ''),
                    price=review_dict.get('가격', ''),
                    coupang_product_id=review_dict.get('쿠팡상품번호', ''),
                    option=review_dict.get('옵션', ''),
                    review_title=review_dict.get('리뷰제목', ''),
                    review_content=review_dict.get('리뷰본문', ''),
                    review_page=review_dict.get('리뷰페이지', 0),
                    author=review_dict.get('작성자', ''),
                    rating=review_dict.get('평점', 0.0),
                    created_at=review_dict.get('작성일'),
                    seller=review_dict.get('판매자', ''),
                    actual_purchase_product_name=review_dict.get('실제구매상품명', ''),
                    images=review_dict.get('이미지들', ''),
                    survey_response=review_dict.get('설문응답', ''),
                    helpful_count=review_dict.get('도움수', 0)
                )
                session.add(review)
            session.commit()
            logger.info(f"Successfully inserted {len(reviews_data)} reviews into the database.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert reviews: {e}")
            raise
        finally:
            session.close()

    def get_all_reviews(self):
        session = self.Session()
        try:
            reviews = session.query(Review).all()
            return [review.__dict__ for review in reviews] # Return as list of dictionaries
        except Exception as e:
            logger.error(f"Failed to retrieve reviews: {e}")
            return []
        finally:
            session.close()

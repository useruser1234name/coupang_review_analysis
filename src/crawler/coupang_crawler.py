from bs4 import BeautifulSoup
import requests
import warnings
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
import time
import random
import re
from src.utils.logger import logger
from src.config import Config

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

class CoupangCrawler:
    def __init__(self):
        self.proxies = self._setup_proxies()
        self.sbr_webdriver_url = self._setup_sbr_webdriver_url()

    def _setup_proxies(self):
        if not all([Config.PROXY_HOST, Config.PROXY_USERNAME, Config.PROXY_PASSWORD]):
            logger.warning("Proxy configuration incomplete. Proceeding without proxy.")
            return None
        proxy_url = f"https://{Config.PROXY_USERNAME}:{Config.PROXY_PASSWORD}@{Config.PROXY_HOST}"
        return {"http": proxy_url, "https": proxy_url}

    def _setup_sbr_webdriver_url(self):
        if not Config.SBR_WEBDRIVER_AUTH:
            logger.warning("Scraping Browser WebDriver authentication incomplete. Selenium may not work.")
            return None
        return f"https://{Config.SBR_WEBDRIVER_AUTH}@brd.superproxy.io:9515"

    def _get_driver(self):
        if not self.sbr_webdriver_url:
            logger.error("SBR WebDriver URL is not configured. Cannot create Selenium driver.")
            return None
        try:
            sbr_connection = ChromiumRemoteConnection(self.sbr_webdriver_url, 'goog', 'chrome')
            driver = Remote(sbr_connection, options=ChromeOptions())
            logger.info("Selenium driver connected successfully.")
            return driver
        except Exception as e:
            logger.error(f"Failed to connect Selenium driver: {e}")
            return None

    def collect_review(self, driver, link, product_info):
        logger.info(f"[리뷰 수집 시작] {link}")
        reviews_data = []
        try:
            driver.get(link)
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            logger.error(f"페이지 로드 실패: {e}")
            return reviews_data

        try:
            review_tab = driver.find_element(By.XPATH, "//a[contains(text(),'상품평')]")
            review_text = review_tab.text.strip()
            match = re.search(r'\((\d+)\)', review_text)
            review_count = int(match.group(1)) if match else 0
            logger.info(f"상품평 총 {review_count}개")
            review_tab.click()
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            logger.warning(f"상품평 탭 클릭 실패 또는 상품평 없음: {e}")
            return reviews_data

        try:
            empty_text_elements = driver.find_elements(By.CSS_SELECTOR, ".sdp-review__article__no-review")
            if empty_text_elements and "등록된 상품평이 없습니다" in empty_text_elements[0].text:
                logger.info("등록된 상품평이 없습니다.")
                return reviews_data
        except:
            pass

        try:
            total_pages = len(driver.find_elements(By.CSS_SELECTOR, ".js_reviewArticlePageBtn"))
            if total_pages == 0: # Handle case where there's only one page and no page buttons
                total_pages = 1
        except:
            total_pages = 1

        page_num = 1
        review_index = 1

        while page_num <= total_pages:
            time.sleep(random.uniform(1.5, 2.5))
            reviews = driver.find_elements(By.CSS_SELECTOR, "article.sdp-review__article__list.js_reviewArticleReviewList")

            if not reviews:
                logger.info(f"No reviews found on page {page_num}. Breaking loop.")
                break

            for review in reviews:
                try:
                    headline = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__headline").text.strip()
                except: headline = ""
                try:
                    content = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__review__content.js_reviewArticleContent").text.strip()
                except: content = ""
                try:
                    author = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__user__name").text.strip()
                except: author = ""
                try:
                    rating = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__star-orange").get_attribute("data-rating")
                except: rating = ""
                try:
                    date = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__reg-date").text.strip()
                except: date = ""
                try:
                    seller = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__seller_name").text.strip()
                except: seller = ""
                try:
                    real_product = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__info__product-info__name").text.strip()
                except: real_product = ""
                try:
                    img_tags = review.find_elements(By.CSS_SELECTOR, ".sdp-review__article__list__attachment__img")
                    image_urls = [img.get_attribute("data-origin-path") for img in img_tags]
                    images = "; ".join(image_urls)
                except: images = ""
                try:
                    survey_blocks = review.find_elements(By.CSS_SELECTOR, ".sdp-review__article__list__survey__row")
                    surveys = [f"{b.find_element(By.CLASS_NAME, 'sdp-review__article__list__survey__row__question').text.strip()}: {b.find_element(By.CLASS_NAME, 'sdp-review__article__list__survey__row__answer').text.strip()}" for b in survey_blocks]
                    survey_text = "; ".join(surveys)
                except: survey_text = ""
                try:
                    helpful_text = review.find_element(By.CSS_SELECTOR, ".sdp-review__article__list__help__count").text.strip()
                except: helpful_text = ""

                review_data = {
                    "상품명": product_info[0],
                    "브랜드": product_info[1],
                    "가격": product_info[2],
                    "쿠팡상품번호": product_info[3],
                    "옵션": product_info[4],
                    "리뷰제목": headline,
                    "리뷰본문": content,
                    "리뷰페이지": page_num,
                    "작성자": author,
                    "평점": rating,
                    "작성일": date,
                    "판매자": seller,
                    "실제구매상품명": real_product,
                    "이미지들": images,
                    "설문응답": survey_text,
                    "도움수": helpful_text
                }
                reviews_data.append(review_data)
                logger.info(f"[{review_index}] {headline} / {content}")
                review_index += 1

            page_num += 1
            if page_num > total_pages:
                break

            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, f".js_reviewArticlePageBtn[data-page='{page_num}']")
                driver.execute_script("arguments[0].click();", next_btn)
            except Exception as e:
                logger.info(f"{page_num} 페이지 버튼 클릭 실패 또는 마지막 페이지: {e}")
                break
        return reviews_data

    def search_products_and_crawl_reviews(self, keyword, pages=1):
        all_reviews = []
        product_links = []

        for page_num in range(1, pages + 1):
            logger.info(f"{page_num}페이지 상품 검색 중...")
            url = f"https://www.coupang.com/np/search?component=&q={keyword}&page={page_num}&listSize=36"
            try:
                response = requests.get(url, proxies=self.proxies, verify=False)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            except requests.exceptions.RequestException as e:
                logger.error(f"상품 검색 요청 실패: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("[class = ProductUnit_productUnit__Qd6sv]")

            if not items:
                logger.info(f"No products found on page {page_num}. Stopping search.")
                break

            for item in items:
                name_tag = item.select_one(".ProductUnit_productName__gre7e")
                price_tag = item.select_one(".Price_priceValue__A4KOr")
                if not (name_tag and price_tag and item.a and 'href' in item.a.attrs):
                    continue
                name_text = name_tag.text.strip()
                price_text = price_tag.text.strip()
                link = f"https://www.coupang.com{item.a['href']}"
                product_links.append((name_text, price_text, link))
        
        logger.info(f"총 {len(product_links)}개 상품 링크 수집 완료")

        driver = self._get_driver()
        if not driver:
            logger.error("Failed to get Selenium driver. Cannot proceed with review collection.")
            return []

        try:
            for name, price, link in product_links:
                logger.info("=" * 80)
                logger.info(f"상품명: {name}")
                logger.info(f"가격: {price}")
                logger.info(f"링크: {link}")

                try:
                    response = requests.get(link, proxies=self.proxies, verify=False)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                except requests.exceptions.RequestException as e:
                    logger.error(f"상세 페이지 요청 실패: {e}")
                    continue

                brand_tag = soup.select_one("div.twc-text-sm.twc-text-blue-600")
                brand = brand_tag.text.strip() if brand_tag else "브랜드 정보 없음"

                product_id = "없음"
                option_list = []
                spec_section = soup.select_one("div.product-description ul")
                if spec_section:
                    for li in spec_section.select("li"):
                        text = li.text.strip()
                        if ":" in text:
                            key, value = text.split(":", 1)
                            key, value = key.strip(), value.strip()
                            if "쿠팡상품번호" in key:
                                product_id = value
                            else:
                                option_list.append(f"{key}: {value}")
                        else:
                            option_list.append(text)

                option_str = "; ".join(option_list)
                product_info = [name, brand, price, product_id, option_str]

                product_reviews = self.collect_review(driver, link, product_info)
                all_reviews.extend(product_reviews)
        finally:
            driver.quit()
            logger.info("Selenium driver closed.")

        return all_reviews

if __name__ == "__main__":
    # This block is for testing the crawler independently
    crawler = CoupangCrawler()
    # Example usage: crawl reviews for '노트북' for 2 pages
    # Make sure your .env is configured with Bright Data credentials
    # reviews = crawler.search_products_and_crawl_reviews("노트북", pages=2)
    # logger.info(f"Total reviews collected: {len(reviews)}")
    # for review in reviews[:5]: # Print first 5 reviews
    #     logger.info(review)
    logger.info("CoupangCrawler module ready. Run main.py or web UI to use.")

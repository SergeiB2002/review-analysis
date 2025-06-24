from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from dateutil.relativedelta import relativedelta
import emoji
import time
from db import db

class Parser:
    
    @classmethod
    def date_from_sentence(cls, date):
        current_date = datetime.now()
        
        parts = date.split(' ')
        if(parts[0].isdigit()):
            amount = int(parts[0])
            unit = parts[1].lower()
        else:
            amount = 1
            unit = parts[0].lower()
            
        if unit.startswith('д'):
            past_date = current_date - relativedelta(days=amount)
        elif unit.startswith('недел'):
            past_date = current_date - relativedelta(weeks=amount)
        elif unit.startswith('час'):
            past_date = current_date - relativedelta(hours=amount)
        elif unit.startswith('месяц'):
            past_date = current_date - relativedelta(months=amount)
        elif unit.startswith('год'):
            past_date = current_date - relativedelta(years=amount)
        elif unit == 'позавчера':
            past_date = current_date - relativedelta(days=2)
        elif unit == 'вчера':
            past_date = current_date - relativedelta(days=1)
            
        return str(past_date).split(' ')[0]
    
    @classmethod
    def parse_ym(cls, url):
        result = []
        init_page = 1
        cur_page = 1
        
        classes = db.select_classes(1)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.get(url)
        
        
        while True:
            time.sleep(5)
            reviews =  driver.find_elements(By.CLASS_NAME, classes['reviewClass'])
            
            for review in reviews:
                fb = {}
            
                date = review.find_element(By.CLASS_NAME, classes['dateClass']).text.split(',')[0]
                fb['date'] = cls.date_from_sentence(date)
            
                stars = int(review.find_element(By.CLASS_NAME, classes['starsClass']).get_attribute('data-rate'))
                fb['stars'] = stars
            
                comments = review.find_elements(By.CLASS_NAME, classes['textClass'])
                text = ""
                for comment in comments:
                    text += emoji.replace_emoji(comment.text, replace="") + ';'
                fb['text'] = text
            
                usefullness = review.find_elements(By.CSS_SELECTOR, "span[data-auto='count']")
                fb['likes'] = int(usefullness[0].text)
                fb['disslikes'] = int(usefullness[1].text)

                result.append(fb)
                
            page_btns = driver.find_elements(By.CLASS_NAME, classes['pgBtnClass'])
            has_next_page = False
            for btn in page_btns:
                if(not btn.text.isnumeric()):
                    continue
                if(int(btn.text) > cur_page):
                    btn.click()
                    cur_page += 1
                    has_next_page = True
                    break
            if not has_next_page or cur_page - 10 >= init_page:
                break
        
        driver.quit()
        return result

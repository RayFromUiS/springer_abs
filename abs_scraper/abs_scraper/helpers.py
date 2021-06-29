import easyocr
from selenium.webdriver import Firefox
import random

def get_text(url):
    '''get verification code  for next step of crawling'''
    reader = easyocr.Reader(['en'], gpu=False)
    with  Firefox() as driver:
        driver.get(url)
        driver.maximize_window()
        img_eles = driver.find_elements_by_tag_name('img')
        img_tag = img_eles[-1]
        # img_name = random.randint()
        img_tag.screenshot('test.png')
        text = reader.readtext('test.png', detail=0)
        text = ''.join(text)
        print('the verification text is ',text)
    return text


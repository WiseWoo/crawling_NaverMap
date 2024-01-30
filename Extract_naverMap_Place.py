from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import re

from bs4 import BeautifulSoup
import requests

def read_menus(address):
    print("address", address)
    options = Options()
    options.headless = False
    driver = webdriver.Chrome(options=options)

    driver.get(address)
    time.sleep(10)
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')

    driver.quit()
#     selector = soup.select("#app-root > div > div > div > div:nth-child(5) > div > div.place_section.no_margin > div.place_section_content > ul")
    
    selector = soup.select("#app-root > div > div > div > div:nth-child(5) > div > div.place_section.no_margin > div.place_section_content > ul ")
    
    try:
        elements = str(selector[0]).split("<li ")[1:]


        menus = []
        for element in elements:
            menu = {}

            # Extract menu img URL
            img_url_pattern = r'url\("([^"]+)"\)' if "background-image" in element else r'src="([^"]+)"'
            img_url = re.findall(img_url_pattern, element)[0]
            menu["img_url"] = img_url


            # Extract menu name 
            name_pattern = r'<span class="lPzHi">(.*?)</span>'
            match1 = re.search(name_pattern, element)
            menu["menu_name"] = match1.group(1) if match1 else "NoName"


            # Extract menu price
            price_pattern = r'<em>(.*?)</em>'
            matched_price = re.search(price_pattern, element)
            menu["menu_price"] = matched_price.group(1) if matched_price else "NoPrice"


            # Extract menu info
            info_pattern = r'<div class="kPogF">(.*?)</div>'
            matched_info = re.search(info_pattern, element)
            menu["menu_info"] = matched_info.group(1) if matched_info else "NoInfo"

            menus.append(menu)


        return menus
    except:
        print("Error")
        return None



def read_operation(soup):
    selector = soup.select("#app-root > div > div > div > div:nth-child(5) > div > div:nth-child(2) > div.place_section_content > div > div.O8qbU.pSavy > div")
    pattern = r'<span class="i8cJw">(.*?)</span><div class="H3ua4">(.*?)</div>'
    matches = re.findall(pattern, str(selector[0]))

    operations = []
    for day, operation_time in matches:
        operation = {}
        operation[day] = operation_time
        operations.append(operation)
    
    return operations

def read_realaddress(soup):    
    selector = soup.select("#app-root > div > div > div > div:nth-child(5) > div > div:nth-child(2) > div.place_section_content > div > div.O8qbU.tQY7D > div > a > span.LDgIH")
    pattern = r'<span class="LDgIH">(.*?)</span>'
    match = re.search(pattern, str(selector[0]))
    address = match.group(1)
    return address
    
    
def read_coordinate(real_address):
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    
    ###################################### 보안
    headers = {
        "X-NCP-APIGW-API-KEY-ID": "",
        "X-NCP-APIGW-API-KEY": ""
    }
    ###################################### 보안
    
    params = { "query": real_address }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result["addresses"]:
            latitude = result["addresses"][0]["y"]
            longitude = result["addresses"][0]["x"]
            return f"{latitude}, {longitude}"
        else:
            return f"00, 00"
    else:
        return f"00, 00"
    
def read_name_category(soup):
    selector = soup.select("#_title > div")
    pattern = r'<span class="[^"]*">(.*?)</span>'
    
    name, category = re.findall(pattern, str(selector[0]))[:2]
    return name, category
    
def read_first_picture(soup):
    selector = soup.select("#app-root > div > div > div > div.CB8aP > div > div:nth-child(1) > div")
    pattern = r'background-image: url\("([^"]+)"\)'
    try:
        match = re.search(pattern, str(selector[0]))
        if match:
            image_url = match.group(1)
        else:
            # 사진이 비어있을 경우 아무 이미지나 불러오게 하는게 좋을듯함
            # 추후 아무 사진의 링크를 넣을 것
            image_url = "https://vos.line-scdn.net/landpress-content-v2_1761/1666859717053.jpg?updatedAt=1666859717000"
    except:
        image_url = "https://vos.line-scdn.net/landpress-content-v2_1761/1666859717053.jpg?updatedAt=1666859717000"
    return image_url

def read_store(address):
    options = Options()
    options.headless = False
    driver = webdriver.Chrome()
    driver.get(address)

    expand_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'w9QyJ.vI8SM')) 
    )

    expand_button.click()
    time.sleep(5)
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    driver.quit()
    
    # read_operation
    operations = read_operation(soup)
    
    # read coordinate
    real_address = read_realaddress(soup)
    coordinate = read_coordinate(real_address)
    
    # read name and category
    name, category = read_name_category(soup)
    
    # read first picture
    picture_url = read_first_picture(soup)
    
    # read menus
    prefix = 'menu/list' if address[-1] == '/' else '/menu/list'
    menus = read_menus(address+prefix)
    
    store_infos = {}
    store_infos["photo"] = picture_url
    store_infos["name"] = name
    store_infos["category"] = category
    store_infos["coodinate"] = coordinate
    store_infos["operation"] = operations
    store_infos["menus"] = menus
    
    return store_infos
    
    

for restaurant_name in tqdm(list(restaurants_num.keys())[37:]):
    my_store = read_store(restaurants_num[restaurant_name])
    with open(restaurant_name+'.json', 'w', encoding='utf-8') as file:
        json.dump(my_store, file, ensure_ascii=False, indent=4)
    

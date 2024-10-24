from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re
import csv
import json  # Import the json module

# Set up Chrome options
options = Options()
options.add_argument('start-maximized')
options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
options.add_argument('--no-sandbox')  # Bypass OS security model
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

# Initialize the first browser instance for collecting URLs
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# Open the Wildberries website and search for books
driver.get('https://www.wildberries.ru')
time.sleep(4)
search_input = wait.until(EC.presence_of_element_located((By.ID, "searchInput")))
search_input.send_keys('книги фридрих дюрренматт')
search_input.send_keys(Keys.ENTER)

# Collect book URLs
url_list = []
while True:
    count = None
    while True:
        time.sleep(4)
        try:
            cards = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//article[@id]')))
            if len(cards) == count:
                break
            count = len(cards)
            driver.execute_script('window.scrollBy(0, 1800)')
            time.sleep(2)
        except Exception as e:
            print(f"Error while waiting for cards: {e}")
            break

    if cards:
        url_list.extend([card.find_element(By.XPATH, './div/a').get_attribute('href') for card in cards])
    else:
        print("No cards found on the page.")

    try:
        next_button = driver.find_element(By.CLASS_NAME, 'pagination-next')
        next_button.click()
    except Exception:
        print("No more pages to navigate.")
        break

print(f'Всего получено: {len(url_list)} ссылок на книги')

# Initialize the second browser instance for scraping book details
driver2 = webdriver.Chrome(options=options)
wait2 = WebDriverWait(driver2, 10)
books_list = []

# Scrape details for each book
for url_item in url_list:
    books_dict = {}
    driver2.get(url_item)

    try:
        # Extract book name
        books_dict['name'] = wait2.until(EC.presence_of_element_located((By.XPATH, "//h1"))).text
        
        # Extract price
        price_elements = wait2.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'price-block__wallet-price')))
        
        # Check if the price element exists and is not empty
        if len(price_elements) > 1 and price_elements[1].text.strip():
            price_str = price_elements[1].text
            books_dict['price'] = float(re.sub(r'[^\d.]+', '', price_str))
        else:
            books_dict['price'] = None  # Set to None if price is not available
        
        # Extract brand (publisher)
        books_dict['brend'] = wait2.until(EC.presence_of_element_located((By.CLASS_NAME, "product-page__header-brand"))).text
        
        # Store the book URL
        books_dict['url'] = url_item
        
        # Extract additional attributes from the table
        labels = wait2.until(EC.presence_of_all_elements_located((By.XPATH, '//th')))
        params = wait2.until(EC.presence_of_all_elements_located((By.XPATH, '//td')))
        description = {label.text: param.text for label, param in zip(labels, params)}
        
        # Map extracted data to predefined fields
        fields = {
            'Артикул': 'article',
            'Автор': 'author',
            'Жанры/тематика': 'genre',
            'Языки': 'language',
            'Год выпуска': 'year',
            'Обложка': 'cover'
        }
        for label, field in fields.items():
            books_dict[field] = description.get(label)

        # Append the book dictionary to the list
        books_list.append(books_dict)

    except Exception as e:
        print(f"Error processing {url_item}: {e}")

# Save the collected data to a CSV file
with open('c:/GB/wb/data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, dialect='excel', delimiter=';')
    writer.writerow(['name', 'price', 'brend', 'url', 'article', 'author', 'genre', 'language', 'year', 'cover'])
    writer.writerows([[book['name'], book['price'], book['brend'], book['url'], book.get('article'), 
                       book.get('author'), book.get('genre'), book.get('language'), 
                       book.get('year'), book.get('cover')] for book in books_list])

# Save the collected data to a JSON file
with open('c:/GB/wb/data.json', 'w', encoding='utf-8') as json_file:
    json.dump(books_list, json_file, ensure_ascii=False, indent=4)

# Close the browser instances
driver.quit()
driver2.quit()
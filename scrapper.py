from functions import to_datetime, get_soup, stripd_txt, get_full_url, get_time_period, maxWaitTime
import re, requests, asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait # driver explicit wait
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


# %% Configure WebDriver
class NewsScrapper: 
    import requests, os

    API_KEY = os.getenv('SCRAPERAPI_KEY')

    payload = {'api_key': API_KEY, 'url': 'https://httpbin.org/ip'}
    
    timezone = None
    
    headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.6",
    "Connection":"close",
    "DNT": "1",
    "Referer": "https://www.google.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Upgrade-Insecure-Requests": "1",
    }
    
    options = Options()
    # options.add_argument("--incognito")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--headless")


    # Use Brave Browser if available
    if os.path.exists('C:/Program Files/BraveSoftware/Brave-Browser/'):
        options.binary_location = 'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'

    # Get Links for News Pages
    @staticmethod
    async def getNewsLinks(pageurl, from_ = '', to_ = ''):
        urls = []
        
        try:
            # Time Period for Artical filtering
            [time_from, time_to] = await get_time_period(from_time=from_, to_time=to_, tz=NewsScrapper.timezone)
            
            print(f'\t\t***** Getting Articals Between Time Period  [{time_from} - {time_to}] *****')
            
            # Class name for artical row card
            articalCardClassName = 'listCard-rows__content'
            
            driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=NewsScrapper.options)
            driver.maximize_window()

            # Go To Webpage
            driver.get(pageurl)
            
            # Click 'Accept Cookie Button' (if available)
            acceptCoockieBtn = driver.find_element(By.CLASS_NAME, 'js-cookies-button')
            if (acceptCoockieBtn):
                acceptCoockieBtn.click()
            
            card = WebDriverWait(driver, maxWaitTime).until(EC.presence_of_element_located((By.CLASS_NAME, articalCardClassName)))
            
            # Click 'MORE' if the the last Artical Card is published between the given time period
            lastArtical = driver.find_elements(By.CLASS_NAME, articalCardClassName)[-1]
            lastArticalTime = to_datetime(lastArtical.find_element(By.XPATH, './/div/div[2]/div[3]').text.strip(), tz=NewsScrapper.timezone)
            
            while (time_from <= lastArticalTime <= time_to) or (time_from >= lastArticalTime >= time_to):
                try:
                    loadMoreBtn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "listingBtn"))).click()
                    
                    lastArtical = driver.find_elements(By.CLASS_NAME, articalCardClassName)[-1]
                    lastArticalTime = to_datetime(lastArtical.find_element(By.XPATH, './/div/div[2]/div[3]').text.strip(), tz=NewsScrapper.timezone)
                    print(f'lastArticalTime = {lastArticalTime}', end = "\n\n")
                except TimeoutException:
                    break
            
            
            
            soup = await get_soup(driver.page_source)
            cards = soup.select('div.' + articalCardClassName)
            
            # Get news link from every Artical Cards
            
            def get_card_link(card):
                articalTime = to_datetime(stripd_txt(card.find('div', class_='card__date')), tz=NewsScrapper.timezone)
                
                # Check if Artical is Between The Given Time Period
                if (time_from <= articalTime <= time_to) or (time_from >= articalTime >= time_to):
                    print(f'articalTime = {articalTime}', end = "\n\n")
                    
                    articalUrl = get_full_url(pageurl, card.find('a', attrs={'class': 'link link_hover'})['href'])
                    return articalUrl
                
            urls = await asyncio.gather(*[asyncio.to_thread(get_card_link, card) for card in cards])
            urls = list(set(urls))
            
            driver.quit()
            
        except:
            print("Error occurred while Getting Articals links. Troubleshoot by: \n\t1. Check Your internet connection.")
            
        finally:
            return urls


    # Get Data from News Pages
    @staticmethod
    async def getNewsData(url):
        
        na = 'Not Available'
        data = {'Title': na, 'Headline': na, 'Link': na, 'Text': na, 'Time - date': na}
        
        try:
            # Make Get Request to get Webpage Content
            res = requests.get(url, headers=NewsScrapper.headers)
            
            soup = await get_soup(res.content)
            
            [title, headline, text, time] = [soup.find('h1', class_='article__heading'), soup.find('div', class_='article__summary'), soup.find('div', class_='article__text'), soup.find('span', class_='date_article-header')]
            
            print(stripd_txt(title))
            
            data['Title'] = stripd_txt(title) if title else na
            data['Headline'] = stripd_txt(headline) if headline else na
            data['Link'] = url if url else na
            
            if text:
                # Check for "Read More" Extras from Articals
                query = re.compile(r"read-more|Read-more-text-only|read-more__text")
                
                # Remove "Read More" Extras from Articals
                for readOnly in text.find_all('div', class_=query):
                    readOnly.decompose()
                
                data['Text'] = stripd_txt(text)
                data['Text'] = re.sub(r'\n+','\n', data['Text'])
                data['Text'] = re.sub(r' +|\s+|\xa0+',' ', data['Text'])
            else:
                data['Text'] = na
                
            data['Time - date'] = to_datetime(stripd_txt(time), tz=NewsScrapper.timezone) if time else na
            
        except requests.exceptions.MissingSchema as err:
            print(f"Error Occurred while Getting Data From '{url}'\n\nError: {err}")
            
        finally:
            return data
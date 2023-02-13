import pytz
from datetime import datetime
from urllib.parse import urlparse
from concurrent import futures
from bs4 import BeautifulSoup


maxWaitTime = 20

# Function to create BeautifulSoup from given url 
async def get_soup(html):
    # Create BS object from response
    soup = BeautifulSoup(html, 'html.parser')
    return soup

# Function to perorm Multiple Data Srcapings in paralle
def executor(func, list_):
    with futures.ThreadPoolExecutor() as exec:
        results = exec.map(func, list_, timeout=9000)
        try:
            results = list(results) 
        except futures._base.TimeoutError:
            print("Timeout for ThreadPoolExecutor")
        finally:
            return results

# Get stripped text from soup 'Tag' object
def stripd_txt(soup_obj):
    txt = soup_obj.get_text().strip() if soup_obj else soup_obj
    return txt

# Function to get needed part of the url
def get_url(url: str, _get='host') -> str:
    
    parsed_uri = urlparse(url)
    
    if parsed_uri.netloc != '':
        if _get == 'host':
            url = parsed_uri.netloc
        elif _get == 'origin':
            url = f'{parsed_uri.scheme if parsed_uri.scheme != "" else "https"}://{parsed_uri.netloc}'
        elif _get == 'd_name':
            url = parsed_uri.netloc.replace('www.','')
        elif _get == 'site_name':
            url = parsed_uri.netloc.replace('www.','').split('.')[0].capitalize()
    else:
        url = ''
    return url

# Function to get full url (url with hostname)
def get_full_url(page_url: str, short_url: str) -> str:
    url_origin = get_url(page_url, 'origin')
    url = (url_origin + ('' if short_url.startswith('/') else '/')+ short_url) if not (url_origin in short_url) else short_url
    
    print(f"Converted '{short_url}' to '{url}'")
    
    return url

# Function to convert string to datetime
def to_datetime(date_time_str, tz=None):
    tz  = pytz.timezone(tz) if not tz is None else tz # Timezone
    
    try:
        format_ = '%d %b, %Y %H:%M'  # The format
        timestamp = datetime.strptime(date_time_str, format_).replace(tzinfo=tz)
    except ValueError:
        try:
            format_ = '%b %d, %Y %H:%M'  # The format
            timestamp = datetime.strptime(date_time_str, format_).replace(tzinfo=tz)
        except ValueError:
            print(f"Time '{date_time_str}' is not valid format.")
            timestamp = datetime.now().replace(tzinfo=tz)
 
    return timestamp

# Get Time Period to Filter News Articals
async def get_time_period(from_time='', to_time='', tz=None):
    tz  = pytz.timezone(tz) if not tz is None else tz # Timezone
    
    # Get the start and end datetime as strings in the format 'dd MMM, yyyy HH:mm'
    time_from = from_time or input("Select Articals from date [format = 'dd-MM-yyyy HH:mm'] [Default = Today 12AM]: ")
    time_to = to_time or input("To date [format = 'dd-MM-yyyy HH:mm'] [Default = Now]: ")

    # Get the current time in the Russian timezone
    now = datetime.now(tz)

    # Set the start datetime as 12:00 AM of the current day in the given timezone
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Set the end datetime as the current time in the given timezone
    curr_time = now
    
    # Format for Date Input
    format_ = "%d-%m-%Y %H:%M"
    
    # Start Time
    try:
        time_from = datetime.strptime(time_from, format_).replace(tzinfo=tz)
    except ValueError:
        time_from = start_time
        
    # End Time
    try:
        time_to = datetime.strptime(time_to, format_).replace(tzinfo=tz)
    except ValueError:
        time_to = curr_time
        
    return [time_from, time_to]

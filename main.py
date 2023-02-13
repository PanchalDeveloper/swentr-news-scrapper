# %% Import Required Libs
import os, asyncio
from time import perf_counter
from scrapper import NewsScrapper
import pandas as pd

# Output location
data_folder = './output'
file_name = 'Businesses Information.xlsx'

# Page URL
url = 'https://swentr.site/russia/'

# Get Article Data
async def getNewsArticalData(url):
    newsData = await NewsScrapper.getNewsData(url)
    return newsData

# %% Extract Multiple Article's Data at once
async def main(page_url):
    # Extract Article Links
    newsArticleUrls = await NewsScrapper.getNewsLinks(page_url)

    start_time = perf_counter() # Time when Process Started

    # Extract Article Data
    tasks = [asyncio.create_task(getNewsArticalData(url)) for url in newsArticleUrls]
    results = await asyncio.gather(*tasks)

    print(f" The Process took {perf_counter() - start_time}s") # Print Total Time The Process Took
    return results

# %% Write Article Data to A Text File
articalData = asyncio.run(main(url))
    
print('loop completed', articalData)

# %% Saving The Data to CSV/Excel File

# Create Output folder if it doesn't exist
if not os.path.exists(data_folder):
    os.mkdir(data_folder)

# %% Save data inside DataFrame
df = pd.DataFrame(articalData)

# %% Group the data by same headings of every articles
grouped_data = df.groupby(['Title', 'Headline', 'Link', 'Text', 'Time - date']).apply(lambda x: x.to_dict(orient='records'))

# %% Convert the grouped data into a dictionary
result = grouped_data.to_dict()
df.to_excel(os.path.join(data_folder, file_name), index=False)

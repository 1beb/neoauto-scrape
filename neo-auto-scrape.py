from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import re
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')  

# 1. Collect "brands"
# 2. Recreate link https://neoauto.com/venta-de-autos-<brand>
# 3. Find maximum page link https://neoauto.com/venta-de-autos-<brand>?page=XX
# 4. Loop over pages from no page to page=XX as found in page 3
# 5. Capture data from squares


def collect_brands():
    driver = webdriver.Chrome(options=options)
    driver.get('https://neoauto.com/')
    r = driver.page_source
    r = BeautifulSoup(r, features="lxml")
    brands = r.select('div > div > select.select_brand > option')
    brands = [brand.get('value') for brand in brands]
    brands = [brand for brand in brands if brand != '']
    return brands


def link_to_brands(brands):
    links = ['https://neoauto.com/venta-de-autos-' + brand for brand in brands]
    return links


def generate_links(link):
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    r = driver.page_source
    r = BeautifulSoup(r, features="lxml")

    links = r.select('div.c-pagination > ul > li > a')
    links = [x.get('href') for x in links] 
    links = [x for x in links if 'page' in x]
    nums = [re.search(r'(\d+)$', x).group(0) for x in links]
    nums = [int(x) for x in nums]

    links = []
    links.append(link)

    try:
        maxima = max(nums)
        for i in range(1,maxima+1):
            links.append(link + '?page=' + str(i))
    except ValueError:
        print("No depth at: " + link)

    return links

def generate_links_list(links):
    all_links = []

    for link in links:
        print("Preparing for: " + link)
        all_links.extend(generate_links(link))
    
    return all_links


def get_car_page_data(link):
    print('Processing data for: ' + link)
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    r = driver.page_source
    r = BeautifulSoup(r, features="lxml")
    selector = 'article.c-results-used'
    r = r.select(selector)

    listings = []

    for i in range(0,len(r)):
        title = r[i].find('h2').getText()
        maker = title.split(' ')[0]
        year = re.search(r'(\d+)$', title).group(0)
        model = re.sub(maker, '', title)
        model = re.sub(year, '', model).strip()

        res = [x.getText() for x in r[i].findAll('p')]
        energy = res[0].split('|')[0]
        trans = res[0].split('|')[1]
        kms = ''.join(re.findall(r'(\d+)', res[1]))
        loc = res[2]
        description = res[3]
        usd_price = ''.join(re.findall(r'(\d+)', res[4]))

        listings.append(
            dict({
                'title': title.lower(), 
                'make': maker.lower(),
                'model': model.lower(),
                'year': year,
                'kms': kms,
                'energy': energy.lower(),
                'transmission': trans.lower(),
                'location': loc,
                'description': description.lower(),
                'price': usd_price,
            })
        )

    return listings 

def get_car_links(links):
    listings = []
    i = 0
    for link in links:
        i = i+1
        print(str(i) + ' of ' + str(len(links)))
        listings.extend(
            get_car_page_data(link)
        )
    
    return listings
    

brands = collect_brands()
links = link_to_brands(brands)
all_links = generate_links_list(links)
results = get_car_links(all_links)
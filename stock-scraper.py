#! /usr/bin/env python3

# -----------------------------------------------------------------------------------------
# Simple script for scraping images from Getty Images, iStock, Adobe Stock and ShutterStock
# Edit configuration variables below according to instructions and examples
# 
# André Mintz, 2019
# -----------------------------------------------------------------------------------------

import csv
import hashlib
import os
import requests
import sys
import time
from bs4 import BeautifulSoup


# -----------------------------------------------------------------------------------------
# CONFIGURATION VARIABLES
# -----------------------------------------------------------------------------------------

# Query term (can be overriden by command line parameters)
query = "american"

# Total number of images to download
max_images     = 2000

# Choose which stock sites to scrape (set to 'True' or 'False')
stocksites = {
    "gettyimages"  : True   ,
    "shutterstock" : True   ,
    "adobestock"   : True   ,
    "istock"       : False 
}

# ----------------------------------------------------------------------------------------

if len(sys.argv) > 1:
    query = sys.argv[1]

output_folder = ""
output_csv = ""

def scrape_images(stock, page):
    # Extract image elements
    if stock in ["gettyimages", "istock"]:
        elements = page.find_all("article", attrs={"class": "mosaic-asset"})
    elif stock == "shutterstock":
        elements = page.find_all("li", attrs={"class": "li"})
    elif stock == "adobestock":
        elements = page.find_all("div", attrs={"class": "search-result-cell"})
        
    # Get image urls and image information page url from each element
    images_list = []
    for element in elements:
        if stock in ["gettyimages", "istock"]:
            image_url = element["data-thumb-url"]
            image_info_url = element.a['href']
        elif stock == "shutterstock":
            image_url = element.div.img['src']
            image_info_url = element.a['href']
        elif stock == "adobestock":
            image_url = element.div.a.img['src']
            image_info_url = element.find_all('div')[0].a['href']
        
        image = {
            'image_url': image_url,
            'image_info_url': image_info_url
        }
        images_list.append(image)
    
    return images_list

# Query url schema for each stock site
def query_url(website, term):
    if website == "gettyimages":
        url = "https://www.gettyimages.com/photos/" + term + "?alloweduse=availableforalluses&family=creative&license=rf&mediatype=photography&phrase=" + term + "&sort=best#license"
        print(url)
        return url
    elif website == "shutterstock":
        url = "https://www.shutterstock.com/search?searchterm=" + term + "&search_source=base_search_form&language=en&page=1&sort=popular&image_type=photo&commercial=true&measurement=px&safe=true"
        print(url)
        return url
    elif website == "adobestock":
        url = "https://stock.adobe.com/search?filters%5Bcontent_type%3Aphoto%5D=1&filters%5Bcontent_type%3Aillustration%5D=0&filters%5Bcontent_type%3Azip_vector%5D=0&filters%5Bcontent_type%3Avideo%5D=0&filters%5Bcontent_type%3Atemplate%5D=0&filters%5Bcontent_type%3A3d%5D=0&filters%5Binclude_stock_enterprise%5D=0&filters%5Bis_editorial%5D=0&filters%5Bcontent_type%3Aimage%5D=1&k=" + term + "&order=relevance&safe_search=1&limit=100&search_page=1&get_facets=1"
        print(url)
        return url
    elif website == "istock":
        url = "https://www.istockphoto.com/photos/" + term + "?alloweduse=availableforalluses&autocorrect=none&mediatype=photography&phrase=brazilian&sort=best"
        print(url)
        return url
    else:
        raise ValueError

# Next page schema for each supported stock site
def scrape_next_link(stock, page, url, pagination_index):
    if stock == "gettyimages":
        next_url = "https://www.gettyimages.com" + page.find(id = "next-gallery-page")['href']
        print("\n" + next_url)
        return next_url
    elif stock == "istock":
        next_url = "https://www.istockphoto.com" + page.find(id = "next-gallery-page")['href']
        print("\n" + next_url)
        return next_url
    # TODO
    elif stock == "shutterstock":
        next_url = "https://www.shutterstock.com" + page.find(id = "mosaic-next-button")['href']
        print("\n" + next_url)
        return next_url
    elif stock == "adobestock":
        args = url.split('&')
        for i, arg in enumerate(args):
            if "search_page" in arg:
                args[i] = "search_page=" + str(pagination_index+1)
        next_url = "&".join(args)
        print("\n" + next_url)
        return next_url

def scrape_stock(stock, term):
    global output_csv

    # Get query URL
    url = query_url(stock, term)

    # Create stocksite folder
    folderp = os.path.join(output_folder, stock)
    if not os.path.exists(folderp):
        os.makedirs(folderp)
    
    # Keep track of processed images and pagination of the stock site
    num_images = 0
    cur_page = 1

    # Loop through the stocksite pages until finished
    while num_images < max_images:

        # Download page
        try:
            r = requests.get(url, allow_redirects=True, timeout=100)
        
        # In case of error, try 5 more times and if persistent, move on the next page
        except Exception:
            success = False
            for i in range(5):
                print("\nConnection problem. Sleeping to try again.")
                time.sleep(5)
                try:
                    r = requests.get(url, allow_redirects=True, timeout=100)
                    success = True
                    break
                except Exception:
                    pass
            if not success:
                print("\nUnresolved connection problem. Moving on")
                print("** Next page **", end=" ")
                sys.stdout.flush()
                url = scrape_next_link(stock, soup, url, cur_page)
                cur_page += 1
                continue

        # Parse with BeautifulSoup
        page = r.content
        soup = BeautifulSoup(page, "html.parser")

        # Get an image list from the page
        image_list = scrape_images(stock, soup)
        
        # For each imag
        for image in image_list:
            num_images += 1
            print(num_images, end=" ")
            sys.stdout.flush()

            # Set image metadata
            image_url = image['image_url']
            image_info_url = image['image_info_url']

            # Get hash of url, form image file path
            hash_url = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
            image_fn = hash_url + '.jpg'
            image_fp = os.path.join(folderp, image_fn)

            # Create CSV row
            row = {"rank_pos": num_images, "image_url": image_url, "image_info_url": image_info_url, "download_file":image_fp, "stock": stock}
            output_csv.writerow(row)

            # If image has not been downloaded yet, download it
            if not os.path.isfile(image_fp):
                r = requests.get(image_url,allow_redirects=True,timeout=100)

                if len(r.content) > 0:
                    image_f = open(image_fp, "wb").write(r.content)
                else:
                    print("[/]", end=" ")
                    sys.stdout.flush()

        # After downloading all images in page, move on to the next
        print("** Next page **", end=" ")
        sys.stdout.flush()

        # Scrape next page's url
        url = scrape_next_link(stock, soup, url, cur_page)
        cur_page += 1

def main():
    global output_csv
    global output_folder

    # If query container directory does not exist, create it
    output_folder = query

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    # Create CSV file
    output_csv_fn       = query + "_image_list.csv"
    output_csv_fp       = os.path.join(output_folder, output_csv_fn)

    if not os.path.isfile(output_csv_fp):
        output_csv_f = open(output_csv_fp, 'w', encoding="utf-8")
        output_csv_fields = ["rank_pos", "image_url", "image_info_url", "download_file", "stock"]
        output_csv = csv.DictWriter(output_csv_f, fieldnames=output_csv_fields)
        output_csv.writeheader()

    else:
        print("Output CSV file '_image_list.csv' already exists in specified folder. Rename it or delete it before continuing.")
        sys.exit()

    # For each supported stock site, check whether they are enabled and scrape each of them
    for stock, enabled in stocksites.items():
        if enabled==True:
            print("\n**", stock, "**")            
            scrape_stock(stock, query)
        else:
            continue
    print("\nFinished.")


# Execute
main()
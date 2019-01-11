#! /usr/bin/env python3

# -----------------------------------------------------------------------------------------
# Simple script for scraping images from Getty Images and iStock
# Edit configuration variables below according to instructions and examples
# 
# André Mintz, 2019
# -----------------------------------------------------------------------------------------

import csv
import hashlib
import os
import requests
import sys
from bs4 import BeautifulSoup


# -----------------------------------------------------------------------------------------
# CONFIGURATION VARIABLES
# -----------------------------------------------------------------------------------------

# URL for query result page
initial_url    = "https://www.gettyimages.pt/fotos/brasileiro?alloweduse=availableforalluses&family=creative&license=rf&phrase=brasileiro&sort=best#license"

# Total number of images to download
max_images     = 5000

# Images download folder name or path
output_folder  = "gettyimages-pt-brasileiro"

# ----------------------------------------------------------------------------------------


image_element       = "article"
image_class         = "mosaic-asset"
image_url_attr      = "data-thumb-url"
next_page_link_id   = "next-gallery-page"
num_images          = 0

split_url            = initial_url.split("/")
base_url             = split_url[0] + "//" + split_url[2]

url = initial_url

# If output folder does not exist, create it
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# If CSV file does not exist, create it. Otherwise, append results.
output_csv_fn       = "_image_list.csv"
output_csv_fp       = os.path.join(output_folder, output_csv_fn)

if not os.path.isfile(output_csv_fp):
    output_csv_f = open(output_csv_fp, 'w', encoding="utf-8")
    output_csv_fields = ["rank_pos", "image_url", "download_file"]
    output_csv = csv.DictWriter(output_csv_f, fieldnames=output_csv_fields)
    output_csv.writeheader()
else:
    print("Output CSV file '_image_list.csv' already exists in specified folder. Rename it or delete it before continuing.")
    sys.exit()

# Loop through result pages
while num_images < max_images:

    # Download page
    r = requests.get(url, allow_redirects=True, timeout=100)
    page = r.content
    soup = BeautifulSoup(page, "html.parser")

    # Extract image elements
    elements = soup.find_all(image_element, attrs={"class": image_class})
    
    # Get image urls from each element
    image_url_list = []
    for element in elements:
        if not element[image_url_attr] in image_url_list:
            image_url_list.append(element[image_url_attr])

    # For each image url
    for image_url in image_url_list:
        num_images += 1
        print(num_images, end=" ")
        sys.stdout.flush()

        # Get hash of url, form image file path
        hash_url = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
        image_fn = hash_url + '.jpg'
        image_fp = os.path.join(output_folder, image_fn)

        # Create CSV row
        row = {"rank_pos": num_images, "image_url": image_url, "download_file":image_fn}
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
    url = base_url + soup.find(id = next_page_link_id)["href"]
print("\nFinished.")
 
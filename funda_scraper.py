import requests
from bs4 import BeautifulSoup
import re
import csv
import os
import sys
import random
'''
https://www.funda.nl/zoeken/koop/?selected_area=["rotterdam,10km"]&search_result=1

'''
def get_search_page(page_number=1, area='rotterdam', radius=0):
    # Headers are needed, otherwise funda will block you for botting
    headers_list = [
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'},
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'},
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0'},
            {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'},
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}]
    header = random.choice(headers_list)
    page_request = requests.get(f'https://www.funda.nl/zoeken/koop/?selected_area=["{area},{radius}km"]&search_result={page_number}', headers=header).text
    search_page = BeautifulSoup(page_request, 'html.parser')
    return search_page

def get_numbers_search_pages(search_page):
    search_page = search_page.find_all('a', attrs={'tabindex': '0'})
    tmp_numbers = []
    for string in search_page:
        if string.get_text().isdecimal():
            tmp_numbers.append(string.get_text())
    return int(max(tmp_numbers))

def get_page(href):
    headers_list = [
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'},
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'},
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0'},
            {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'},
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}]
    header = random.choice(headers_list)
    page_request = requests.get(href, headers=header).text
    page = BeautifulSoup(page_request, 'html.parser')
    return page


def get_href_houses_on_page(search_page):
    # Get all the links for the pages of the houses
    houses_href = set()
    for link in search_page.find_all(href=re.compile(r"www.funda.nl(\/detail|)\/koop\/(?!heel-nederland)")):
        # Funda has 2 types of links, for the new and old version of the site, we change all to the old version
        link = link.get('href')
        if 'detail' in link:
            link = link.replace('detail/koop', 'koop')
            house_number_data = re.findall(r'\/[0-9]{5,}\/', link)[0][1:-1]
            house_type = re.findall(r'\/\w+-', link)[0]
            link = re.sub(r'\/\w+-', house_type+house_number_data+'-', link, 1)
        houses_href.add(link)
    return list(houses_href)


def scrape_house(house_page, href):
    kenmerk_types = house_page.find_all('dl', 'object-kenmerken-list')
    info = []
    total_info_dict = {}
    for kenmerk_type in kenmerk_types:
        for kenmerk in kenmerk_type.contents:
            if kenmerk.get_text() != "\n":
                info.append(kenmerk.get_text().replace('\n', "").replace('\r', "").strip())
    for index in range(1, len(info), 2):
        total_info_dict[info[index-1]] = info[index]
    total_info_dict['Link'] = href
    # Now remove/change unnecessary info from dict if there
    if 'Vraagprijs' in total_info_dict:
        total_info_dict['Vraagprijs'] = total_info_dict['Vraagprijs'].replace('kosten koper', '').strip()
    if 'Vraagprijs per m²' in total_info_dict.keys():
        total_info_dict['Vraagprijs per m²'] = total_info_dict['Vraagprijs per m²'][:10].strip()
    if 'Bouwperiode' in total_info_dict:
        total_info_dict['Bouwjaar'] = total_info_dict.pop('Bouwperiode')
    total_info_dict['Energielabel'] = total_info_dict['Energielabel'][0]
    total_info_dict['m²'] = re.findall(r"[0-9]+ m²", total_info_dict.pop('Gebruiksoppervlakten'))[0]
    return total_info_dict

def output_csv(total_info_dict):
    fieldnames = ['Link', 'Vraagprijs', 'Vraagprijs per m²', 'm²', 'Status', 'Aantal kamers', 'Aantal badkamers','Aanvaarding', 'Soort bouw']
    for house_info in total_info_dict:
        del_list = []
        index = total_info_dict.index(house_info)
        for key in house_info.keys():
            if key not in fieldnames:
                del_list.append(key)
        for key in del_list:
            del total_info_dict[index][key]
    with open(os.path.join(sys.path[0], 'housedata.csv'), 'w', encoding='utf-8') as file:
        writer = csv.DictWriter(file, delimiter=';', fieldnames=fieldnames, newline="")
        writer.writeheader()
        writer.writerows(total_info_dict)
        


def main():
    # to demonstrate the flow of the script
    search_page = get_search_page()
    number_search_pages = get_numbers_search_pages(search_page)
    print("Got the total number of pages")
    href_houses = []
    for search_page_number in range(number_search_pages):
        href_houses.extend(get_href_houses_on_page(get_search_page(page_number=search_page_number, area='rotterdam', radius=0)))
    print("Got all the links to the houses")
    total_info = []
    for href_house in href_houses:
        total_info.append(scrape_house(get_page(href_house), href_house))
    print("Scraping Done")
    output_csv(total_info)
if __name__ == "__main__":
    main()


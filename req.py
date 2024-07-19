import requests
import csv
import os
from lxml import html
import random
import time
URL = "https://www.carjam.co.nz/car/?plate={}"

class Scraper():
    def __init__(self):
        self.proxies = []
        self.session = requests.Session()
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'set-cookie': 'pc=NWVmZjM3ZTMyMzc2ZWMwYzQwNzJkMjVmYzcyYzBiOWZjNGU4M2RiNjU4ZDE0YWI5MWFjOTY4ZjFkYWE1MjRhZHw5OWZkNTQ4MmQ3YmQ1MDYzfDE3MjExMjg3NDg%3D; expires=Tue, 16 Jul 2024 11:19:08 GMT; Max-Age=300; path=/; domain=carjam.co.nz; secure; HttpOnly; SameSite=Lax'
        }
        self.productMap = dict()
        self.skipProductMap = dict()
        if os.path.exists('result.csv'):
            with open('result.csv', 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                  if row.get("plate", None) is not None:
                     self.productMap[row["plate"]] = True

        if os.path.exists('skip.csv'):
            with open('skip.csv', 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    if row.get("plate", None) is not None:
                        self.skipProductMap[row["plate"]] = True

        self.plates = self.read_excel('plates.csv')
    def start(self):
        self.read_proxies()
        for plate in self.plates:
            if self.skipProductMap.get(plate, None) is None and self.productMap.get(plate, None) is None:
                print(f'<<<<<<<<<<<<Scraping {plate}')
                content = self.get_response(URL.format(plate))
                tree = html.fromstring(content)
                temp = dict()
                temp['plate'] = plate
                try:
                    temp['url'] = URL.format(plate)
                    temp['year']= self.get_text_from_row(tree, 'Year:')
                    temp['make']= self.get_text_from_row(tree, 'Make:')
                    temp['model']= self.get_text_from_row(tree, 'Model:')
                    temp['submodel']= self.get_text_from_row(tree, 'Submodel:')
                    temp['power']= self.get_text_from_row(tree, 'Power:')
                    temp['cc_rating']= self.get_text_from_row(tree, 'CC rating:')
                    temp['fuel_type']= self.get_text_from_row(tree, 'Fuel Type:')
                    temp['vin']= self.get_text_from_row(tree, 'VIN:')
                    temp['chassis']= self.get_text_from_row(tree, 'Chassis:')
                    temp['engine_no']= self.get_text_from_row(tree, 'Engine No:')
                    temp['vehicle_equipment_class']=self.get_text_from_row(tree, 'Vehicle Equipment Class:')
                    temp['mvma_model_code']=self.get_text_from_row(tree, 'MVMA Model Code:')
                    temp['registered_previously_in']=self.get_text_from_row(tree, 'Registered previously in:')
                    
                    self.save_csv(temp, 'result.csv')
                    print(f'Added {plate}')
                except:
                    self.save_csv(temp, 'skip.csv')
                    print(f'>>>>>>>>>>>Skipped {plate}')
                    continue
            else:
                print(f'>>>>>>>>>>>Skipped {plate}')
    def get_text_from_row(self, tree, title):
        try:
            partial_text = title
            ele = tree.xpath(f'//span[contains(text(), "{partial_text}")]')[0]
            value = ele.getparent().xpath('span')[1].text_content()
        except:
            value = ''
        return value

    def get_plate_history(self, tree):
        value = ''
        partial_text = 'Plates History'
        title = tree.xpath(f'//h4[contains(text(), "{partial_text}")]')[0]
        table = title.getnext()
        tbody = table.xpath('tbody')[0]
        rows = tbody.xpath('tr')
        for index, row in enumerate(rows):
            if(index > 0):
                if (index == 1):
                    value = value + str(row.xpath('td')[0].text)
                else:
                    value = value + ' - ' + str(row.xpath('td')[0].text)
        value = str(value).replace('\n', '').strip()
        return value 
    
    def get_response(self, url):
        time.sleep(3)
        proxy = random.choice(self.proxies)
        print(f'Using proxy: {proxy}')
        # response = self.session.get(url, proxies=proxy, headers=self.headers)
        response = self.session.get(url, headers=self.headers)
        self.write_file(response.text)
        return response.content
    
    def write_file(self, content):
        with open('temp.html', 'w', encoding='utf-8') as file:
            file.write(content)

    def read_excel(self, filepath: str):
        data = []
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            render = csv.DictReader(csvfile)
            for row in render:
                value = dict(row)
                data.append(str(value['param']).replace('|0', ''))
        return data
    
    def save_csv(self, row, file_path):
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row.keys())
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(row)
   
    def read_proxies(self):
        with open('proxies.txt', 'r') as file:
            line = file.readline()
            while line:
                print(line.strip())
                line = file.readline()
                try:
                    temp = dict()
                    temp['http'] = f'http://{line.split(':')[2]}:{line.split(':')[3].replace('\n','')}@{line.split(':')[0]}:{line.split(':')[1]}'
                    # temp['https'] = f'http://{line.split(':')[2]}:{line.split(':')[3].replace('\n','')}@{line.split(':')[0]}:{line.split(':')[1]}'
                    self.proxies.append(temp)
                except:
                    pass

def main():
    scraper = Scraper()
    scraper.start()

if __name__ == "__main__":
    main()
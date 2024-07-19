import asyncio
import nodriver as uc
import pyautogui
import time
import csv
from lxml import html
import random
import os
URL = "https://www.carjam.co.nz/car/?plate=UA100/" 

class Scraper:
   main_tab: uc.tab
   def __init__(self):
         self.proxies = []
         self.hostname = ''
         self.username = ''
         self.pwd = ''
         self.productMap = dict()
         self.skipProductMap = dict()
         if os.path.exists('result.csv'):
               temp=[]
               with open('result.csv', 'r', newline='', encoding='utf-8') as csvfile:
                  for row in csv.DictReader(csvfile):
                     if row.get("plate", None) is not None:
                        self.productMap[row["plate"]] = True

         if os.path.exists('skip.csv'):
               with open('skip.csv', 'r', newline='', encoding='utf-8') as csvfile:
                  for row in csv.DictReader(csvfile):
                     if row.get("plate", None) is not None:
                           self.skipProductMap[row["plate"]] = True
            
         uc.loop().run_until_complete(self.main())

   def read_excel(self, filepath: str):
      data = []
      with open(filepath, newline='', encoding='utf-8') as csvfile:
         render = csv.DictReader(csvfile)
         for row in render:
            value = dict(row)
            data.append(str(value['param']).replace('|0', ''))
      
      if os.path.exists('result.csv'):
         temp=[]
         for item in data:
            if self.productMap.get(item, None) is None:
               temp.append(item)
         data = temp
      else:
         pass
      
      if os.path.exists('skip.csv'):
         temp=[]
         for item in data:
            if self.skipProductMap.get(item, None) is None:
               temp.append(item)
         data = temp
      else:
         pass
      return data

   def save_csv(self, row, file_path):
      with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
         writer = csv.DictWriter(csvfile, fieldnames=row.keys())
         if csvfile.tell() == 0:
               writer.writeheader()
         writer.writerow(row)
   
   def write_file(self, content):
      with open('temp.html', 'w', encoding='utf-8') as file:
         file.write(content)

   async def press_login_btn(self):
      location = pyautogui.locateOnScreen('login_btn.png', confidence=0.8)
      if location:
         center = pyautogui.center(location)
         pyautogui.click(center)
      else:
         print("Can't find location")
      time.sleep(10)

   async def bypass_cloudflare(self):
      location = pyautogui.locateOnScreen('checkbox.png', confidence=0.8)
      if location:
         center = pyautogui.center(location)
         pyautogui.click(center)
      else:
         print("Can't find location")
      time.sleep(10)

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
   async def auth_challenge_handler(self, event: uc.cdp.fetch.AuthRequired):
      asyncio.create_task(
         self.main_tab.send(
            uc.cdp.fetch.continue_with_auth(
               request_id=event.request_id,
               auth_challenge_response=uc.cdp.fetch.AuthChallengeResponse(
                  response="ProvideCredentials",
                  username=self.username,
                  password=self.pwd
               )
            )
         )
      )

   async def req_paused(self, event: uc.cdp.fetch.RequestPaused):
      asyncio.create_task(
         self.main_tab.send(
            uc.cdp.fetch.continue_request(request_id=event.request_id)
         )
      )

   async def main(self):
      plates = self.read_excel('plates.csv')
      self.read_proxies()

      await self.create_browser()
      print (f'Current port: {self.port}')
      init_page = await self.browser.get(URL)
      time.sleep(1)
      page = await self.browser.get(URL, new_tab=True)
      time.sleep(5)
      try:
         ele = await page.select(".vehicle-section", timeout=25)
      except:
         while True:
            try:
               await self.bypass_cloudflare()
               break
            except Exception as e:
               print(f'Error : {e}. Retrying ...')
               time.sleep(5)

      for index, plate in enumerate(plates):
         if self.productMap.get(plate, None) is None:
            print(f"<<<<<<<<<<<< {plate}")
            try:
               if index > 0 and index % 10 == 0:
                     self.browser.stop()
                     await self.create_browser()
                     print (f'Current port: {self.port}')
                     new_url = f"https://www.carjam.co.nz/car/?plate={plate}"
                     init_page = await self.browser.get(new_url)
                     time.sleep(1)
                     page = await self.browser.get(new_url, new_tab = True)
                     await page.sleep(5)
                     try:
                        ele = await page.select(".vehicle-section", timeout=25)
                     except:
                        while True:
                           try:
                              await self.bypass_cloudflare()
                              break
                           except Exception as e:
                              print(f'Error : {e}. Retrying ...')
                              time.sleep(5)

               print(f"Processing {index+1}/{len(plates)} plate: {plate} Current Proxy is {self.hostname} : {self.port} : {self.username} : {self.pwd}")
               temp = {}
               ele = None
               new_url = f"https://www.carjam.co.nz/car/?plate={plate}"
               await page.get(new_url)
               try:
                     ele = await page.select(".vehicle-section", timeout=25)
               except Exception as e:
                     print(f'>>>>>>>>>> Skipped : {plate}')
                     self.save_csv({'plate':plate}, 'skip.csv')
                     continue
               
               html_content = await page.get_content()
               tree = html.fromstring(html_content)

               temp['plate']= plate
               temp['url'] = new_url
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
               # temp['plate_history']=get_plate_history(tree)
               self.save_csv(temp, 'result.csv')
               print(plate + " is done.")
            except Exception as e:
                  continue
         else:
               print(f">>>>>>>>> Skipped : {plate}")
      
   async def create_browser(self):
      self.get_random_proxy()
      self.browser = await uc.start(
         browser_args=[f"--proxy-server={self.hostname}:{self.port}"],
      )
      self.main_tab = await self.browser.get("draft:,")
      self.main_tab.add_handler(uc.cdp.fetch.RequestPaused, self.req_paused)
      self.main_tab.add_handler(uc.cdp.fetch.AuthRequired, self.auth_challenge_handler)
      await self.main_tab.send(uc.cdp.fetch.enable(handle_auth_requests=True))
      time.sleep(5)

   def get_random_proxy(self):
      proxy = random.choice(self.proxies)
      self.username = proxy['user'].strip()
      self.pwd = proxy['password'].strip()
      self.hostname = proxy['hostname'].strip()
      self.port = proxy['port'].strip()

   def read_proxies(self):
      with open('proxies.txt', 'r') as file:
         line = file.readline()
         while line:
            print(line.strip())
            line = file.readline()
            try:
               temp = dict()
               temp['hostname'] = line.split(':')[0]
               temp['port'] = line.split(':')[1]
               temp['user'] = line.split(':')[2]
               temp['password'] = line.split(':')[3]
               self.proxies.append(temp)
            except:
               pass

if __name__ == '__main__':
   Scraper()

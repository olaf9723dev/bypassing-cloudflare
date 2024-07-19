import asyncio
import nodriver as uc
import pyautogui
import time
import csv
from lxml import html
URL = "https://www.carjam.co.nz" 
PWD = ""
USER = ""
class Scraper:
   main_tab: uc.tab
   def __init__(self):
        uc.loop().run_until_complete(self.main())

   def read_excel(self, filepath: str):
      data = []
      with open(filepath, newline='', encoding='utf-8') as csvfile:
         render = csv.DictReader(csvfile)
         for row in render:
            value = dict(row)
            data.append(str(value['param']).replace('|0', ''))
      return data

   def save_csv(self, row):
      with open('result.csv', 'a', newline='', encoding='utf-8') as csvfile:
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
                  username='',
                  password=''
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
      browser = await uc.start(
         browser_args=[f"--proxy-server="],
      )
      self.main_tab = await browser.get("draft:,")
      self.main_tab.add_handler(uc.cdp.fetch.RequestPaused, self.req_paused)
      self.main_tab.add_handler(uc.cdp.fetch.AuthRequired, self.auth_challenge_handler)
      await self.main_tab.send(uc.cdp.fetch.enable(handle_auth_requests=True))
      time.sleep(10)
      page = await browser.get(URL)
      time.sleep(45)
      
      await self.bypass_cloudflare()
      await self.press_login_btn() 
      # page.wait_for('.login-panel', timeout=10)
      email_input = await page.select("input[type=email]")
      await email_input.send_keys(USER)
      pwd_input = await page.select("input[type=password]")
      await pwd_input.send_keys(PWD)
      sign_btn = await page.select("button[name=login]")
      await sign_btn.click()
      time.sleep(10)

      for plate in plates:
         temp = {}
         ele = None
         new_url = f"https://www.carjam.co.nz/car/?plate={plate}"
         await page.get(new_url)
         try:
            ele = await page.select(".vehicle-section", timeout=25)
         except Exception as e:
            print(e)
            continue
         # await page.reload()
         html_content = await page.get_content()
         # write_file(html_content)
         tree = html.fromstring(html_content)

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
         temp['plate']= self.get_text_from_row(tree, 'Plate:')
         temp['engine_no']= self.get_text_from_row(tree, 'Engine No:')
         temp['vehicle_equipment_class']=self.get_text_from_row(tree, 'Vehicle Equipment Class:')
         temp['mvma_model_code']=self.get_text_from_row(tree, 'MVMA Model Code:')
         temp['registered_previously_in']=self.get_text_from_row(tree, 'Registered previously in:')
         # temp['plate_history']=get_plate_history(tree)
         self.save_csv(temp)
         print(plate + " is done.")

if __name__ == '__main__':
    Scraper()

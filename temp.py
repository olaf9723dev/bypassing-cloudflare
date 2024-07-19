import asyncio
import nodriver as uc
import json

class Scraper:
    main_tab: uc.tab

    def __init__(self):
        uc.loop().run_until_complete(self.run())

    async def run(self):
        browser = await uc.start(
            browser_args=[f"--proxy-server="],
        )
        self.main_tab = await browser.get("draft:,")
        self.main_tab.add_handler(uc.cdp.fetch.RequestPaused, self.req_paused)
        self.main_tab.add_handler(uc.cdp.fetch.AuthRequired, self.auth_challenge_handler)
        await self.main_tab.send(uc.cdp.fetch.enable(handle_auth_requests=True))
        page = await browser.get('https://ip.me')

        await page.wait(3000000)
        # await asyncio.sleep(6000)


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
            ))
        )

    async def req_paused(self, event: uc.cdp.fetch.RequestPaused):
        asyncio.create_task(
            self.main_tab.send(
                uc.cdp.fetch.continue_request(request_id=event.request_id)
            )
        )

if __name__ == '__main__':
    Scraper()
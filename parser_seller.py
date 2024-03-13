
import asyncio
import requests
from fake_headers import Headers
from loguru import logger
import socket


from dotenv import dotenv_values
from logger_own_settings import mylogger

# Connecting the logger with settings in the environment.
mylogger() 

def check_proxy_connection(proxy):
    try:
        host, port = proxy['http'].split(':')[1][2:], int(proxy['http'].split(':')[2])
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return True
    except Exception as e:
        print(f"Proxy connection failed: {e}")
        return False

class DownloaderDataSG:
    def __init__(self):
        """Load variables from .env without updating the environment"""

        env_vars = dotenv_values(".env")
        
        self.URL_START = env_vars.get("URL_START")
        self.URL_GEO = env_vars.get("URL_GEO")
        self.URL_SELLERS = env_vars.get("URL_SELLERS")
        self.URL_GOODS = env_vars.get("URL_GOODS")

    async def get_goods_inf(self, number):
        headers = Headers().generate()
        response_geo_inf = requests.get(url=self.URL_GEO, headers=headers, proxies=self.proxies)
        response_geo_inf_json = response_geo_inf.json()
        logger.debug(response_geo_inf_json)
        
        response_xinfo = response_geo_inf_json['xinfo']
        logger.debug(response_xinfo)

        # GOODS INFO
        response_filter_goods = requests.get(f'{self.URL_GOODS}{response_xinfo}&supplier={number}')
        response_filter_goods_json = response_filter_goods.json()
        logger.debug(response_filter_goods_json)
        return response_filter_goods_json

    async def get_quickly_inf_seller(self, number):
        response_seller_inf = requests.get(f'{self.URL_SELLERS}{number}.json', proxies=self.proxies)
        response_seller_inf_json= response_seller_inf.json()
        logger.debug(response_seller_inf.json())
        return response_seller_inf_json
    
    @logger.catch
    async def get_info_seller_goods(self, number, proxies=None, max_retries=1):
        """
        Get information about the seller and their goods.
        Number is the ID number of the owner on the marketplace.
        Proxies is the proxy address for the work.
        Code example:
        download = DownloaderDataSG(number=number, proxies=proxyDict)
        asyncio.run(download.get_info_seller_goods())
        
        Return a dictionary with information about the seller and goods. The information is to be transmitted and recorded in the database.
        """
        self.number = number
        self.proxies = proxies
        logger.debug(f"{self.proxies} - proxies")

        for attempt in range(max_retries):
            try:
                seller = await self.get_quickly_inf_seller(number=number)
                logger.info(f'{seller}')
                await asyncio.sleep(1)
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"An error occurred while receiving a response, the data is not available. Details: {e}")
                seller = None
            except Exception as e:
                logger.error(f"Error while getting seller information: {e}")
                seller = None

            if seller is not None:
                try:
                    goods = await self.get_goods_inf(number=number)
                    logger.debug(f'{goods}')
                    logger.info(f"The data about the goods has been received.")
                    await asyncio.sleep(1)
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"An error occurred while receiving a response, the data is not available. Details: {e}")
                    goods = None
                except Exception as e:
                    logger.error(f"Error while getting goods information: {e}")
                    goods = None

                logger.debug(f"SELLER_INFORMATION GOT:  {True if seller is not None else 'Information didn`t get.'}")
                logger.debug(seller)
                logger.debug(f"GOODS_INFORMATION GOT: {True if goods is not None else 'Information didn`t get.'}")
                logger.debug(goods)

                if seller is not None and goods is not None:
                    # Both seller and goods information obtained successfully
                    return (seller, goods)

            logger.warning(f"Retry attempt {attempt + 1}/{max_retries}")
            await asyncio.sleep(2)  # Adjust the sleep duration between retries

        logger.error("Max retries reached. Unable to obtain information.")
        return (None, None)


if __name__ == '__main__':
    # number = 104452

    proxy_http = {'http': 'http://139.99.148.90:3128'}
    # proxy = '192.111.135.17'
    # port='18302'
    # proxy_socks4 = {'http': f'Socks4://{proxy}:{port}'}
    # http_proxy  = 'https://139.99.148.90:3128'
    # proxyDict = { 
    #     'http': http_proxy, 
    #     'http': proxy_socks4,
    # }
    
    number = 99999
    download = DownloaderDataSG()
    asyncio.run(download.get_info_seller_goods(number=number, proxies=proxy_http))
    pass

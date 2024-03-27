
import asyncio
import requests
from fake_headers import Headers # type: ignore
from loguru import logger
import socket
from typing import Dict, Any, Union

from dotenv import dotenv_values
from logger_own_settings import mylogger

# Connecting the logger with settings in the environment ().
mylogger() 

def check_proxy_connection(proxy: dict) -> bool:
    """
    Check the connection status of the provided proxy.

    Keyword arguments:
    proxy -- A dictionary containing the proxy information, expected keys are 'http' or 'https'.
             e.g., {'http': 'https://139.99.148.90:3128'}

    Returns:
    bool -- True if the proxy connection is successful, False otherwise.
    """
    try:
        host, port = proxy['http'].split(':')[1][2:], int(proxy['http'].split(':')[2])
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        return True
    except Exception as e:
        logger.warning(f"Proxy connection failed: {e}")
        return False

class DownloaderDataSG:
    def __init__(self):
        """
        Load variables from .env without updating the environment.

        Example:
        downloader = DownloaderDataSG()
        print(downloader.URL_START)  # Output: The value of URL_START loaded from .env file
        """

        env_vars = dotenv_values(".env")
        
        self.URL_START = env_vars.get("URL_START")
        self.URL_GEO = env_vars.get("URL_GEO")
        self.URL_SELLERS = env_vars.get("URL_SELLERS")
        self.URL_GOODS = env_vars.get("URL_GOODS")

    async def get_goods_inf(self, number: int) -> Dict[str, Any]:
        """
        Get information about goods from a web service.

        Args:
        - number (int): The ID number of the seller on the marketplace.
        - proxies (Optional[Dict[str, str]]): A dictionary containing proxy information for the request. 
                                                Keys represent the protocol (e.g., 'http', 'https') and values 
                                                represent the proxy address. Default is None.

        Returns:
        - Dict[str, Any]: A dictionary containing information about the goods received from the web service.

        Description:
        This method sends HTTP requests to retrieve information about goods associated with a particular seller 
        identified by the given number. It first generates headers using an instance of the Headers class. 
        Then, it sends a GET request to the URL_GEO endpoint with the generated headers and provided proxies, 
        extracts information from the response JSON, and logs the information. Subsequently, it uses the extracted 
        information ('xinfo') to construct another GET request to the URL_GOODS endpoint to retrieve specific goods 
        information. Finally, it returns a dictionary containing the information about the goods received 
        from the web service.
        """
        headers = Headers().generate()
        response_geo_inf = requests.get(url=self.URL_GEO, headers=headers, proxies=self.proxies)
        response_geo_inf_json = response_geo_inf.json()
        logger.info(response_geo_inf_json)
        logger.debug(response_geo_inf_json)
        response_xinfo = response_geo_inf_json['xinfo']
        logger.debug(response_xinfo)

        # GOODS INFO
        response_filter_goods = requests.get(f'{self.URL_GOODS}{response_xinfo}&supplier={number}')
        response_filter_goods_json = response_filter_goods.json()
        logger.debug(response_filter_goods_json)
        return response_filter_goods_json        

    async def get_quickly_inf_seller(self, number: int) -> Dict[str, Any]:
        """
        Get information about a seller quickly from a web service.

        Args:
            number (int): The ID number of the seller on the marketplace.
            proxies (Optional[Dict[str, str]]): A dictionary containing proxy information for the request. 
                                                Keys represent the protocol (e.g., 'http', 'https') and values 
                                                represent the proxy address. Default is None.

        Returns:
            Dict[str, Any]: A dictionary containing information about the seller received from the web service.

        Description:
            This method sends a GET request to the URL_SELLERS endpoint with the provided seller number to quickly 
            retrieve information about the seller from the web service. It optionally accepts proxy information in 
            the 'proxies' parameter. The response JSON is logged, and the parsed JSON data is returned as a dictionary 
            containing information about the seller.
        """
        response_seller_inf = requests.get(f'{self.URL_SELLERS}{number}.json', proxies=self.proxies)
        response_seller_inf_json= response_seller_inf.json()
        logger.debug(response_seller_inf.json())
        return response_seller_inf_json
    
    @logger.catch
    async def get_info_seller_goods(self, number: int, proxies: Union[Dict[str, str], None] = None, max_retries: int = 1) -> tuple:
        """
        Get information about the seller and their goods.

        Args:
            number (int): The ID number of the seller on the marketplace.
            proxies (Optional[Dict[str, str]]): A dictionary containing proxy information for the request. 
                                                 Keys represent the protocol (e.g., 'http', 'https') and values 
                                                 represent the proxy address. Default is None.
            max_retries (Optional[int]): The maximum number of retries for obtaining information. Default is None.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]: A tuple containing dictionaries with information 
                                                                       about the seller and goods. The information 
                                                                       is to be transmitted and recorded in the database.

        Description:
            This method retrieves information about the seller and their goods from a web service. It sends HTTP 
            requests to obtain the information, with optional proxy settings and retry mechanism. If successful, 
            it returns a tuple containing dictionaries with the retrieved information. Otherwise, it returns 
            (None, None) if the maximum number of retries is reached or if any error occurs during the process.
        """
        self.number = number
        self.proxies = proxies
        logger.debug(f"{self.proxies} - proxies")

        for attempt in range(max_retries):
            try:
                seller = await self.get_quickly_inf_seller(number=number)
                logger.info(f'{seller}')
                await asyncio.sleep(0.6)
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
                    await asyncio.sleep(0.75)
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
            await asyncio.sleep(1)  # Adjust the sleep duration between retries

        logger.error("Max retries reached. Unable to obtain information.")
        return (None, None)


if __name__ == '__main__':
    # number = 104452

    proxy_http = {'http': 'http://162.223.91.11:80'}
    # proxy_http = {'http': 'https://139.99.148.90:10'}
    # proxy_http = {'http': 'https://139.99.148.90:3128'}
    # proxy_http = '192.111.135.17'
    # port='18302'
    # proxy_socks4 = {'http': f'Socks4://{proxy}:{port}'}
    # http_proxy  = 'https://139.99.148.90:3128'
    # proxyDict = { 
    #     'http': http_proxy, 
    #     'http': proxy_socks4,
    # }
    print(check_proxy_connection(proxy_http))
    downloader = DownloaderDataSG()
    result = asyncio.run(downloader.get_goods_inf(1))
    print(result)
    print(downloader.URL_START)

    result_info_seller_goods = asyncio.run(downloader.get_info_seller_goods(-1))
    print(type(result_info_seller_goods))
    print(result_info_seller_goods)
    print(list.__dict__)
    # number = 99999
    # download = DownloaderDataSG()
    # asyncio.run(download.get_info_seller_goods(number=number, proxies=proxy_http))
    pass

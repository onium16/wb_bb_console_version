import asyncio

from loguru import logger
import requests
from parser_seller import DownloaderDataSG
from db_worker import main_db, DbSellersGoods

from dotenv import dotenv_values
from loguru import logger
from logger_own_settings import mylogger

# Connecting the logger with settings in the environment.
mylogger() 

class WorkerDBtoDB:
    """
    Class that includes a series of methods such as:
    - preparation_dbs(): Creates databases and tables with the required columns.
    - get_save_data(number, data_s=None, data_g=None, proxies=None): Retrieves new data from the dictionary (data_s for Seller or data_g for Goods) and passes it for storage in the database.
    - delete_data_seller(number): Deletes all data from all tables based on the user ID.
    - get_update_data(number, proxies=None): Updates seller data by their ID (number).
    - scan_get_save_data(start_number, end_number): Retrieves new dictionary data from the merchant range (data_s for Seller or data_g for Goods) and stores it in the database.
    """
    def __init__(self) -> None:
        self.downloader = DownloaderDataSG()


    def preparation_dbs(self):
        """"Сreates bases and table with the required columns."""
        # main_db(method_db="DELETE-ALL")
        main_db(method_db="CREATE-ALL", method_table="TABLE-CREATE-ALL")

    def get_save_data(self, number, proxies=None):
        """
        Retrieving new data from the dictionary (data_s or data_g | data_s and data_g) and passing it for storage in the database. 
        Provide the customer number (ID) and the data in the form of a dictionary (data_s for Seller or data_g for Goods) to the method.
        """
        number = number

        # Load variables from .env without updating the environment
        env_vars = dotenv_values(".env")
        logger.debug(env_vars)
        # Access the variables in the dictionary
        DB_USER = env_vars.get("USER_PSQL")
        DB_PASSWORD = env_vars.get("PASSWORD_PSQL")
        HOST_PSQL = env_vars.get("HOST_PSQL")
        PORT_PSQL = env_vars.get("PORT_PSQL")
        DBSEL_NAME = env_vars.get("DBSEL_NAME")
        
        logger.debug(HOST_PSQL, PORT_PSQL)
        #Check data in DB
        dbSellerGoods = DbSellersGoods(user=DB_USER,password=DB_PASSWORD,host=HOST_PSQL,port=PORT_PSQL,dbname=DBSEL_NAME)
        check_result = dbSellerGoods.check_seller_inf(number)
        if check_result == True:
            message_warning = f"Seller number {number} found in the database"
            logger.error(f'{message_warning}')
            return message_warning

        # Get data
        else:
            try:
                seller_inf, goods_inf = asyncio.run(self.downloader.get_info_seller_goods(number=number, proxies=proxies))
                logger.debug(f"'Get_save' function is working. ")
            except requests.exceptions.JSONDecodeError as error_json:
                logger.error(error_json)


            logger.debug(f'Result  in time had receiving data: seller_inf:{bool(seller_inf)},  goods_inf:{bool(goods_inf)}')

            if seller_inf:
                main_db(method_table="DATA-SAVE", data_s=seller_inf)
            else:
                logger.error("Data for 'seller_inf' was not received.")
            if goods_inf and not None:
                main_db(method_table="DATA-SAVE", data_g=goods_inf)
            else:
                logger.error("Data for 'goods_inf' was not received.")
            return logger.info(f"The processing of receiving and saving data for the seller with number '{number}' is complete.")

    def scan_get_save_data(self, start_number, end_number, proxies=None):
        """
        Retrieves new dictionary data from the merchant range (data_s for Seller or data_g for Goods) and stores it in the database.
        """
        for number in range(start_number, end_number):
            logger.warning(f"{number} - number seller")
            worker.get_save_data(number=number, proxies=proxies)

    def get_update_data(self, number, proxies=None):
        """
        Updating seller data by their ID (number).
        Provide the customer number (ID).
        """
        seller_inf, goods_inf = asyncio.run(self.downloader.get_info_seller_goods(number=number, proxies=proxies))
        logger.debug(f'{seller_inf} \n {goods_inf}')
        main_db(method_table="DATA-UPD", data_s=seller_inf)
        main_db(method_table="DATA-UPD", data_g=goods_inf)
        return print(f"Updated seller data with {number} is completed.")
    
    def delete_data_seller(self, number):
        """
        Deletion of all data from all tables based on the user ID.
        Provide the customer number (ID).
        """
        main_db(method_table="DATA-DELETE",supplier_id=number)
        return print(f"Deleting data of seller with {number} is completed.")
    
    def read_data_seller_goods(self, number_text, id_name=None):
        logger.debug(number_text, id_name)
        try:
            seller_inf, goods_inf = main_db(method_table="DATA-READ", supplier_id=number_text, id_name=id_name)
            return seller_inf, goods_inf
        except TypeError as e:
            logger.error(e)
    
if __name__ == '__main__':
 
#WORK METHODS
    # proxy_http = {'http': 'http://139.99.148.90:3128'}
    proxy_http = {'http': 'http://162.223.91.11:80'}
    # http_proxy  = 'https://139.99.148.90:3128'
    # http_proxy  = 'https://162.223.91.11:80'
    worker = WorkerDBtoDB()

    # start_number = 88000
    start_number = 220000
    end_number = 230000 #195000

    worker.scan_get_save_data( start_number=start_number, end_number=end_number, proxies=proxy_http)

    # # UPPER LIMIT 104000-104473
    # number=104475,

    # # worker.preparation_dbs()
    
    # DELETE NUMBER 

    # try:
    #     for number in range (194760, 194780):
    #         worker.delete_data_seller(number=number)
    # except Exception as e:
    #     print("Error. not found number") 

    # for number in range(102413, 102999):
    #     logger.warning(number)
    #     worker.get_save_data(number=number, proxies=proxy_http)
    
    # for number in range(101000, 101999):
    #     logger.warning(number)
    #     worker.get_save_data(number=number, proxies=proxy_http)

    # # worker.get_update_data(number=number, proxies=None)

    # # seller, goods = worker.read_data_seller_goods(number=number)
    # # print(seller, goods)
 
    # for number in range(100000, 100999):
    #     logger.warning(number)
    #     worker.get_save_data(number=number, proxies=proxy_http)

# JUNK
    # env_vars = dotenv_values(".env")

    # DB_USER = env_vars.get("USER_PSQL")
    # DB_PASSWORD = env_vars.get("PASSWORD_PSQL")
    # HOST_PSQL = env_vars.get("HOST_PSQL")
    # PORT_PSQL = env_vars.get("PORT_PSQL")
    # DBSEL_NAME = env_vars.get("DBSEL_NAME")
    # DBGOOD_NAME = env_vars.get("DBGOOD_NAME")
    # table_name_sellers = env_vars.get("TABLE_SEL_NAME")
    # table_name_goods = env_vars.get("TABLE_GOOD_NAME")

    # # from test_inf import seller_inf, goods_inf

    # number = 104452
    # # number = 104452
    # proxy_http = {'http': 'http://139.99.148.90:3128'}
    # proxy = '192.111.135.17'
    # port='18302'
    # proxy_socks4 = {'http': f'Socks4://{proxy}:{port}'}
    # http_proxy  = 'https://139.99.148.90:3128'
    # proxyDict = { 
    #     'http': http_proxy, 
    #     'http': proxy_socks4,
    # }
    
    # worker = WorkerDBtoDB()
    # # worker.preparation_dbs()
    # # worker.get_save_data( number, proxies=proxyDict)
    # worker.get_update_data(number=number, proxies=proxy_http)
    # #Access the variables in the dictionary
    # # db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
    # # db.update_data(data_s=seller_inf, data_g=goods_inf)
    pass
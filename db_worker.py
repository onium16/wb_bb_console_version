import json
import psycopg2

from setting_db import columns_goods, columns_sellers

from dotenv import dotenv_values
from loguru import logger
# Load variables from .env without updating the environment
env_vars = dotenv_values(".env")

# Access the variables in the dictionary
DB_USER = env_vars.get("USER_PSQL")
DB_PASSWORD = env_vars.get("PASSWORD_PSQL")
HOST_PSQL = env_vars.get("HOST_PSQL")
PORT_PSQL = env_vars.get("PORT_PSQL")
DBSEL_NAME = env_vars.get("DBSEL_NAME")
DBGOOD_NAME = env_vars.get("DBGOOD_NAME")
table_name_sellers = env_vars.get("TABLE_SEL_NAME")
table_name_goods = env_vars.get("TABLE_GOOD_NAME")

from logger_own_settings import mylogger

# Connecting the logger with settings in the environment.
mylogger()

class DbMethods:
    """CREATE & DELETE DB_USERS"""
    def __init__(self):
        pass

    def create_database(self, dbname, user, password, host, port):
        """
        CREATE DB
        
        """
        
        try:
            temp_conn = psycopg2.connect(user=user, password=password, host=host, port=port)
            temp_conn.autocommit = True
            temp_cur = temp_conn.cursor()
            temp_cur.execute(f"""CREATE DATABASE {dbname}
                                    WITH
                                    OWNER = postgres
                                    ENCODING = 'UTF8'
                                    LOCALE_PROVIDER = 'libc'
                                    TABLESPACE = pg_default
                                    CONNECTION LIMIT = -1
                                    IS_TEMPLATE = False;""")
            # Close the temporary cursor and connection
            temp_cur.close()
            temp_conn.close()
            logger.info(f"Database {dbname} was created successfully.")
        except psycopg2.errors.DuplicateDatabase as edb:
            logger.info(f"Database {dbname} already exists.")
        except psycopg2.Error as e:
            logger.error(f"Error creating the database: {e}")

    def delete_database(self, dbname, user, password, host, port):
        """
        DELETE DB
        
        """
        try:
            # Connect to the default 'postgres' database to terminate connections
            temp_conn = psycopg2.connect(user=user, password=password, host=host, port=port)
            temp_conn.autocommit = True
            temp_cur = temp_conn.cursor()

            # Terminate all connections to the target database
            temp_cur.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{dbname}' AND pid <> pg_backend_pid();
            """)

            # Close the temporary cursor and connection
            temp_cur.close()
            temp_conn.close()

            temp_conn = psycopg2.connect(user=user, password=password, host=host, port=port)
            temp_conn.autocommit = True
            temp_cur = temp_conn.cursor()
            temp_cur.execute(f"""DROP DATABASE {dbname};""")
            temp_cur.close()
            temp_conn.close()
            logger.info(f"Database {dbname} has been successfully deleted.")
        except psycopg2.Error as e:
            logger.error(f"Error deleting the database: {e}")
    
class DbSellersGoods:
    def __init__(self, user, password, host, port, dbname=None):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        self.conn = self._connect()

    def _connect(self):
        return psycopg2.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            dbname=self.dbname
        )

    def table_exists(self, table_name, dbname=None):
        """Method waiting for table_name and DBname for checking if they exist together."""
        try:
            if dbname:
                self.dbname = dbname
                self.conn.close()
                self.conn = self._connect()
                logger.info(f'Connecting to the {dbname} database.')

            with self.conn.cursor() as cur:
                # Checking the existence of a table in the current database
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table_name,))
                table_exists = cur.fetchone()[0]

                # If the table exists, make a note
                if table_exists:
                    logger.info(f"Table {table_name} found in the {dbname} database")
                    return True
                else:
                    logger.info(f"Table {table_name} not found in the {dbname} database. It should be created before starting work.")
                    return False

        except NameError as e:
            logger.error(f"Error checking table existence: {e}")

    def create_table(self, table_name, columns, database=None):
        try:
            # If a specific database is specified, create a new connection
            if database:
                self.dbname = database
                self.conn.close()
                self.conn = self._connect()

            # Create cursor
            with self.conn.cursor() as cur:
                # Create a table if it does not exist.
                cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} ({columns});""")
                self.conn.commit()
                logger.info(f"The table {table_name} has been successfully created for the {database} database.")
        except NameError as e:
            logger.error(f"Error creating the table: {e}")

    def drop_table(self, table_name, database=None):

        """If a specific database is specified, create a new connection."""
        if database:
            self.dbname = database
            self.conn.close()
            self.conn = self._connect()
        # Remove try-except block temporarily
        with self.conn.cursor() as cur:
            # Construct the DROP TABLE query
            query = f"DROP TABLE IF EXISTS {table_name};"
            # Execute the query
            cur.execute(query)
            # Commit the changes
            self.conn.commit()
            logger.info(f"Table {table_name} successfully dropped.")

    def check__seller_inf(self, number):
        self.dbname = DBSEL_NAME
        self.conn = self._connect()
        table = table_name_sellers
        number = number
        try:
            with self.conn, self.conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {table} WHERE supplierid = %s", (number,))
                current_data = cur.fetchall()
                # update current_data for next data processing
                logger.debug((current_data))

                if current_data:
                    logger.info("Seller information found in the database.")
                    return True
                else:
                    logger.info("No seller information found in the database.")
                    return False
                
        except NameError as e:
            massage_error = f"Error when retrieving seller ({number})  data from the database in {table}."
            logger.warning(f"{massage_error}. Details: {e}")
            return False

        
    def save_new_inf(self, database, data_s=None, data_g=None):
        """
        The method expects an indication of the data database (database) and a dictionary of new data (new_inf ('seller_inf' or 'goods_inf')) for sellers and goods.
        """
        try:
            if None in (DBSEL_NAME, DBGOOD_NAME, table_name_sellers, table_name_goods):
                raise ValueError("One or more environment variables are not defined. Please check the information.")
            else:
                logger.debug(f'Environment variable data has been received.')

        except ValueError as e:
            message_error = "Not all data of the variables (DBSEL_NAME, DBGOOD_NAME, table_name_sellers, table_name_goods) is provided in the virtual environment. Please check the information."
            logger.error(f'{message_error} \nDetails: {e}')
            return message_error

        def save_one_inf(new_inf_keys, new_inf_values,number=None):
            try:
                # Execute the query
                with self.conn, self.conn.cursor() as cur:
                    # Reserve places in tuples for values
                    placeholders = ', '.join(['%s' for _ in new_inf_keys])
                    cur.execute(f"INSERT INTO {self.table_name} ({', '.join(new_inf_keys)}) VALUES ({placeholders})", tuple(new_inf_values))
                    
                    if data_s:
                        supplier_id = data_s.get('supplierId')
                        message_result = f"Data added about sellers '{supplier_id}' in the table database - '{database}'"
                        return message_result, supplier_id
                    elif data_g:
                        supplier_id = data_g.get('data', {}).get('products', [])[number].get('supplierId')
                        id_goods = data_g.get('data', {}).get('products', [])[number].get('id')
                        return id_goods, supplier_id
                    else:
                        message_error = f"Error in time receving data about 'ID' supplier or goods"
                        return message_error

            except psycopg2.errors.UniqueViolation as e:
                # Check if 'supplierId' key exists in new_inf
                if data_s:
                    supplier_id = data_s.get('supplierId')
                    message_result = f"Information already exists for sellers '{supplier_id}' in the table database - '{database}'"
                    return message_result
                elif data_g:
                    supplier_id = data_g.get('data', {}).get('products', [])[number].get('supplierId')
                    id_goods = data_g.get('data', {}).get('products', [])[number].get('id')
                    message_result = f"Information already exists about goods('{id_goods}') for sellers '{supplier_id}' in the table database - '{database}'"
                    return message_result
                else:
                    message_error = f"Error in time receving data about 'ID' supplier or goods"
                    return message_error
            except psycopg2.errors.UndefinedColumn as e:
                """
                Adding new columns that were not originally included in the table. and retrying to add data to the table.
                """
                # Handle the case when a column is not defined in the table
                logger.error(f"Column not defined in the table: {e}")
                message_error = f"Error: Column not defined in the table - {e}"

                try:
                    with self.conn, self.conn.cursor() as cur:
                        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (self.table_name,))
                        existing_columns = [row[0] for row in cur.fetchall()]

                        for column in new_inf_keys:
                            if column not in existing_columns:
                                # Adjust the data type according to your requirements
                                cur.execute(f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS {column} VARCHAR(255)")
                    
                    self.save_one_inf()

                except psycopg2.Error as e:
                    logger.error(f"Error adding columns to the table: {e}")

            except Exception as e:
                logger.error(f"An error occurred: {e}")

        # logger.info(f"{new_inf}")
        # If a specific database is specified, create a new connection
        if data_s:
            self.dbname = DBSEL_NAME
            self.conn.close()
            self.conn = self._connect()
            self.table_name = table_name_sellers
            new_inf_keys = data_s.keys()
            new_inf_values = [json.dumps(value) if isinstance(value, (dict, list)) else (value if value != '' else None) for value in data_s.values()]

            result = save_one_inf(new_inf_keys, new_inf_values)
            logger.info(result)
        else:
            logger.debug("Data_s data not received.")
            pass

        if data_g:
            self.dbname = DBGOOD_NAME
            self.conn.close()
            self.conn = self._connect()
            self.table_name = table_name_goods

            logger.debug(data_g['data']['products'])
            numbers = len(data_g['data']['products'])
            logger.info(f"Number of seller's products - {numbers}")

            if numbers == 0:
                logger.info("Products for saving not found.")
            else:
                list_idgoods =[]
                for number in range(0, len(data_g['data']['products'])):
                    new_inf_keys = data_g['data']['products'][number].keys()
                    value = (data_g['data']['products'][number])
                    new_inf_values = [json.dumps(value) if isinstance(value, (dict, list)) else (value if value != '' else None) for value in value.values()]
                    logger.debug(new_inf_keys)
                    logger.debug(new_inf_values)

                    id_goods, supplier_id = save_one_inf(new_inf_keys, new_inf_values, number=number)
                    list_idgoods.append(id_goods)  
                logger.info(f"Information already exists about goods('{list_idgoods}') for sellers '{supplier_id}' in the table database - '{database}'.")
        else:
            logger.debug("Data_s data not received.")
            pass

    def update_data(self, data_s=None, data_g=None):
        """
        Main method for UPDATing data in SELLERS and GOODS tables.
        The method takes dictionaries "data_s" or "data_g" as input. Subsequently, based on the "supplierId" or "id" selector, the method locates corresponding records in the tables. It retrieves the data and column names, packs them into a dictionary using the zip function. Then, it compares values by keys between the previously obtained dictionary (user's dictionary) and the created dictionary (table's dictionary). If the values differ, a database UPDATE query is executed to modify the table data in the database.
        """
        try:
            if None in (DBSEL_NAME, DBGOOD_NAME, table_name_sellers, table_name_goods):
                raise ValueError("One or more environment variables are not defined. Please check the information.")
            else:
                logger.debug(f'Environment variable data has been received.')

        except ValueError as e:
            massage_error = "Not all data of the variables (DBSEL_NAME, DBGOOD_NAME, table_name_sellers, table_name_goods) is provided in the virtual environment. Please check the information."
            logger.error(f'{massage_error} \nDetails: {e}')
            return logger.error(massage_error)

        def update_one_dict(data_id, id_name, dbname, table, data):
            """
            data_id - the selector by which we will reference entries in the database table. It is represented by a numerical value in the table "supplierId" (in table sellers) or "id" (in table goods) .
            id_name - the NAME selector by which we will reference entries in the database table. It is represented by "supplierId" (in table sellers) or "id" (in table goods) 
            dbname - the name of the database to which we connect. Automatically determined based on the data parameter name: data_s (DBSEL_NAME(in Virtual environment)) or data_g (DBGOOD_NAME Virtual environment).
            table - the name of the table to which we work. Automatically determined based on the data parameter name: data_s ("table_name_sellers "(in Virtual environment)) or data_g ("table_name_goods" (in Virtual environment).
            data - the combining variable for passing data, either 'data_s' or 'data_g,' for further processing.
            """
            try:
                with self.conn, self.conn.cursor() as cur:
                            cur.execute(f"SELECT * FROM {table} WHERE {id_name} = %s", (data_id,))
                            current_data = cur.fetchone()
                            logger.debug(current_data)
            except NameError as e:
                massage_error = f"Information about {data_id} not found in {dbname} {table}."
                logger.warning(massage_error, e)

            if current_data or current_data!=None:
                columns = [desc[0] for desc in cur.description]
                current_data_dict = dict(zip(columns, current_data))
                logger.debug(f'\n Current_data_dict \n {current_data_dict}')
            else:
                return logger.error("""
                                   During the data check using the seller's ID number.
                                   No data found in the table. Please verify the input data.
                                   Use the save_new_inf method to store the initial information.
                                   """
                                   )
            
            for key, new_value in data.items():
                if key.lower() in current_data_dict.keys():
                    """ Converting a variable with a value of '' (incorrect data type for an int-type table) to None (the correct data type)."""
                    new_value = None if new_value=='' else new_value
                    if str(new_value) != str(current_data_dict[key.lower()]):
                        
                        try:
                            logger.debug("____________________________________________")
                            logger.debug(f"{key} | {current_data_dict[key.lower()]} -> {new_value}")
                            
                            with self.conn, self.conn.cursor() as cur:
                                
                                cur.execute(f"UPDATE {table} SET {key} = %s WHERE supplierId = %s",
                                            (json.dumps(new_value) if isinstance(new_value, (dict, list)) else new_value, data_id))

                            logger.debug(f"Column {key} for the record with id {data_id} has been updated in the {table}  table")
                            logger.debug("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                        except psycopg2.errors.InvalidTextRepresentation as e:
                            massage_error = f"An error occurred while updating the data.\n Details: The data in the column '{key}' in table '{table}', DB - '{dbname}' does not match the data type specified in the table."
                            logger.error(massage_error)
                            return print(massage_error)

                    else:
                        logger.debug(f"Column '{key}' for the record with id '{data_id}' does not require updating.")
                else:
                    logger.info(f'Record has been found for which there is no column with the name {key.lower()}')

        if data_s ==None and data_g ==None:
            massage_error = "Parameters 'data_s' and 'data_g' are not specified correctly or are not specified. pass the dictionary to at least one parameter."
            logger.error(massage_error)
            return massage_error

        if data_s !=None:
            dbname = DBSEL_NAME
            table = table_name_sellers
            data = data_s
            # Getting the value supplierId in data_s
            data_id = data_s['supplierid']
            logger.info(data_id)
            id_name = "supplierId"
            self.dbname = dbname
            self.conn.close()
            self.conn = self._connect()
            
            update_one_dict(data_id, id_name, dbname, table, data)

        if data_g !=None:
            dbname = DBGOOD_NAME
            table = table_name_goods
            data = data_g
            # Getting the value supplierId in data_g (ID PRODUCT)
            data_id = None
            id_name = "id"
            logger.info(data_id)

            self.dbname = dbname
            self.conn.close()
            self.conn = self._connect()

            numbers = len(data['data']['products'])
            logger.info(f"Number of seller's products - {numbers}")

            if number==0:
                logger.info("Poducts for updating not found.")
            else:
                for number in range(0, len(data['data']['products'])):
                    update_good_inf = data['data']['products'][number]
                    logger.debug(update_good_inf)
                    data_id = update_good_inf['id']
                    logger.debug(data_id)
                    update_one_dict(data_id, id_name, dbname, table, data=update_good_inf)

    def read_inf(self, number, id_name=None):
        """
        Works with two databases simultaneously, returning information based on supplierId (ID). Return dictinary data seller, goods.
        Parameters:
        number - the NAME selector by which we will reference entries in the database table. It is represented by "supplierId" or text (%text%).
        id_name - this is name column 
        """
        logger.debug(f'{number}, {id_name}')
        try:
            if None in (DBSEL_NAME, DBGOOD_NAME, table_name_sellers, table_name_goods):
                error_message = "One or more environment variables are not defined. Please check the information."
                logger.error(f'{error_message}')
                logger.exception(ValueError(error_message))
                return error_message

        except ValueError as e:
            massage_error = "Not all data of the variables (DBSEL_NAME, DBGOOD_NAME, table_name_sellers, table_name_goods) is provided in the virtual environment. Please check the information."
            logger.error(f'{massage_error} \nDetails: {e}')
            logger.exception(e)
            return massage_error

        def read_one_dict(data_id, id_name, dbname, table):
            try:
                id_name = id_name.lower()
                equality = '='  # Initialize equality variable here
                if id_name != "supplierid":
                    try:
                        request_type_column_query = f"""
                            SELECT data_type
                            FROM information_schema.columns
                            WHERE table_name = '{table}' AND column_name = '{id_name}';
                        """
                        logger.debug(request_type_column_query)

                        with self.conn, self.conn.cursor() as cur:
                            cur.execute(request_type_column_query)
                            request_type_column = cur.fetchone()
                            if request_type_column:
                                request_type_column = request_type_column[0]
                                logger.debug(request_type_column)

                                equality = 'LIKE' if request_type_column == 'character varying' else '='
                    except psycopg2.Error as pg_error:
                        logger.error(f"PostgreSQL error while fetching data type: {pg_error}")
                    except Exception as e:
                        logger.error(f"An error occurred: {e}")
                        pass

                # Rest of the function remains the same
                with self.conn, self.conn.cursor() as cur:
                    try:
                        cur.execute(f"SELECT * FROM {table} WHERE {id_name} {equality} %s", (data_id,))
                        current_data = cur.fetchall()
                        # update current_data for next data processing
                        logger.debug(current_data)

                        columns = [desc[0] for desc in cur.description]
                        # logger.debug(columns)
                        list_inf = []
                        for row in current_data:
                            logger.debug(row)
                            current_data_dict = dict(zip(columns, row))
                            list_inf.append(current_data_dict)
                    except psycopg2.errors.UndefinedColumn as e:
                        logger.info(f"Undefined Column: {id_name} in table {table}.")
                        list_inf = []
                        pass
                    except psycopg2.errors.InvalidTextRepresentation as e:
                        logger.info(f"Error in the query, as the entered data does not match the data in the specified column {id_name} in table {table}.")
                        list_inf = []
                        pass

                    except Exception as e:
                        logger.error(f"An error occurred: {e}")
                        list_inf = []
                        pass
            except NameError as e:
                message_error = f"Information about {data_id} not found in {dbname} {table}."
                logger.warning(f"{message_error}. Details: {e}")
                # logger.exception(e)
                list_inf = []
            return list_inf
      

        dbname = DBSEL_NAME
        table = table_name_sellers
        # Getting the value supplierId in data_s
        data_id = number
        logger.info(f"'{data_id}' - data_id, {id_name} - id_name")
        if id_name is None:
            logger.info(f"'{data_id}' - seller number")
            logger.info(f"The process of reading information for the seller with number - '{data_id}' has been initiated.")

        id_name = id_name or "supplierId"
        self.dbname = dbname
        self.conn.close()
        self.conn = self._connect()
        
        seller_inf = read_one_dict(data_id, id_name, dbname, table)

        dbname = DBGOOD_NAME
        table = table_name_goods
        # Getting the value supplierId in data_g (ID PRODUCT)
        self.dbname = dbname
        self.conn.close()
        self.conn = self._connect()

        goods_inf = read_one_dict(data_id, id_name, dbname, table)

        logger.debug(f'\nseller_inf \n {seller_inf} \ngoods_inf \n {goods_inf}')
        logger.info(f'Reading done.')
        return seller_inf, goods_inf

    def delete_inf(self, 
                supplier_id, 
                table_name_sellers=table_name_sellers, 
                table_name_goods=table_name_goods, 
                database_sellers=DBSEL_NAME, 
                database_goods=DBGOOD_NAME):
        """Deletes all information from the table based on supplierId (ID)."""
        try:
            def delete_data(database, table_name, supplier_id):
                self.dbname = database
                self.conn.close()
                self.conn = self._connect()

                with self.conn, self.conn.cursor() as cur:
                    logger.info(f"Connect to {database} table {table_name}")

                    # Delete all records from the table based on supplier_id
                    cur.execute(f"DELETE FROM {table_name} WHERE supplierId = %s", (supplier_id,))
                    self.conn.commit()

                    logger.info(f"All records for supplier_id {supplier_id} have been deleted from the {table_name} table.")

            if database_sellers and table_name_sellers:
                delete_data(database_sellers, table_name_sellers, supplier_id)

            if database_goods and table_name_goods:
                delete_data(database_goods, table_name_goods, supplier_id)

        except psycopg2.errors.UndefinedTable as e_table:
            logger.error(f"Error deleting data from tables: {e_table}")

        except Exception as e:
            logger.error(f"Error deleting data from tables: {e}")

# @logger.catch
def main_db(method_db=None, method_table=None, database=None, data_s=None, data_g=None, supplier_id=None, id_name=None):
    """
    METHODS DB (CREATE&DELETE):
    - "CREATE": 
    ("CREATE-ALL", "CREATE-S", "CREATE-G"): 
    Create two databases using the "CREATE-ALL" command or separately (CREATE-S - 'Sellers' and CREATE-G - 'Goods')
    - "DELETE": 
    ("DELETE-ALL", "DELETE-S", "DELETE-G"): 
    Delete two databases using the "DELETE-ALL" command or separately (DELETE-S - 'Sellers' and DELETE-G - 'Goods')
    
    METHODS for working with DB's:
    - "TABLE-CREATE": ("TABLE-CREATE-ALL", "TABLE-CREATE-S", "TABLE-CREATE-G"): 
    Create two tables using the "TABLE-CREATE-ALL" command or separately (TABLE-CREATE-S - 'Sellers' and TABLE-CREATE-G - 'Goods')
    - "TABLE-DELETE": ("TABLE-DELETE-ALL", "TABLE-DELETE-S", "TABLE-DELETE-G"): 
    Delete two databases using the "DELETE-ALL" command or separately (TABLE-DELETE-S - 'Sellers' and TABLE-DELETE-G - 'Goods')
    - "DATA-SAVE" (seller_inf or goods_inf): method for save data to table DB (exp. method_table="DATA-SAVE", data=data (SECOND_variable: data for save for table Sellers and Goods))
    - "DATA-UPD"  (seller_inf or goods_inf): method for update data in the table DB (exp. method_table="DATA-UPD", data=seller_inf or data=goods_inf (SECOND_variable: data for save for table Sellers and Goods))
    - "DATA-READ": method for read data in the table DB using ID Seller (exp. method_table="DATA-READ", data=data, supplier_id=supplier_id  (SECOND_variable: data for save for table Sellers and Goods))
    - "DATA-DELETE" method for drop data in the table DB using ID Seller (exp. method_table="DATA-DELETE", data=data, supplier_id=supplier_id  (SECOND_variable: data for delete for table Sellers and Goods))
    
    supplier_id - number or text. supplier_id may be change to another value for another name columns(must write id_name) 
    id_name - column name, default None
    """

    if method_db == None and method_table == None:
        massage_error = "Set one of the options (method_db or method_table) to interact with the database."
        logger.error(massage_error)
        return print (massage_error)
    else:
        pass

    # Check method_db
    if method_db in ["CREATE-ALL", "CREATE-S", "CREATE-G", "DELETE-ALL", "DELETE-S", "DELETE-G"]:
        if method_db == "CREATE-ALL":
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                # CREATE db
                db_methods = DbMethods()

                if method_db == "CREATE-ALL" or method_db == "CREATE-S":
                    # CREATE DB_SELLERS
                    db_methods.create_database(dbname=DBSEL_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                else:
                    logger.warning("Something went wrong while creating the database")
                    pass
                if method_db == "CREATE-ALL" or method_db == "CREATE-G":
                    # CREATE DB_GOODS
                    db_methods.create_database(dbname=DBGOOD_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                else:
                    logger.warning("Something went wrong while creating the database")
                    pass
            else:
                logger.error("One of the values for these METHODS DB (CREATE&DELETE) to work is missing")
        else:
            pass

        if method_db == "DELETE-ALL":
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                # DELETE db
                db_methods = DbMethods()

                if method_db == "DELETE-ALL" or method_db == "DELETE-S":
                    # DELETE DB_SELLERS
                    db_methods.delete_database(dbname=DBSEL_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                else:
                    logger.warning("Something went wrong while deleting the database")
                    pass
                if method_db == "DELETE-ALL" or method_db == "DELETE-G":
                    # DELETE DB_GOODS
                    db_methods.delete_database(dbname=DBGOOD_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                else:
                    logger.warning("Something went wrong while deleting the database")
                    pass
            else:
                logger.error("One of the values for these METHODS DB (CREATE&DELETE) to work is missing")
        else:
            pass
    elif method_db == None:
        pass
    else:
        message_error = "ERROR method_db. Check the method_db name!"
        logger.error(message_error)
      

    # Check method_table
    if method_table in ["TABLE-CREATE-ALL", "TABLE-CREATE-S", "TABLE-CREATE-G", "TABLE-DELETE-ALL", "TABLE-DELETE-S", "TABLE-DELETE-G", "DATA-SAVE", "DATA-UPD", "DATA-READ", "DATA-DELETE"]:

        if method_table in ["TABLE-CREATE-ALL", "TABLE-CREATE-S", "TABLE-CREATE-G"]:
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
            
                if method_table=="TABLE-CREATE-ALL" or method_table=="TABLE-CREATE-S":
                    # CREAT TABLE (TABLE_SEL_NAME) FOR DB_SELLERS
                    if not db.table_exists(table_name=table_name_sellers, dbname=DBSEL_NAME):
                        db.create_table(table_name=table_name_sellers, columns=columns_sellers, database=DBSEL_NAME)
                    else:
                        logger.info(f'The table {table_name_sellers} is working')
                else:
                    # logger.warning("Something went wrong while creating the database")
                    pass

                if method_table=="TABLE-CREATE-ALL" or method_table=="TABLE-CREATE-G":
                    # CREAT TABLE (TABLE_GOOD_NAME) FOR DB_GOODS
                    if not db.table_exists(table_name=table_name_goods, dbname=DBGOOD_NAME):
                        db.create_table(table_name=table_name_goods, columns=columns_goods, database=DBGOOD_NAME)
                    else:
                        logger.info(f'The table {table_name_goods} is working')
                else:
                    # logger.warning("Something went wrong while creating the database")
                    pass
            else:
                logger.error("One of the values for this method to work is missing")
        else: pass

        if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
            db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
        
            if method_table=="TABLE-DELETE-ALL" or method_table=="TABLE-DELETE-S":
                # CREAT TABLE (TABLE_SEL_NAME) FOR DB_SELLERS
                if db.table_exists(table_name=table_name_sellers, dbname=DBSEL_NAME):
                    db.drop_table(table_name=table_name_sellers, database=DBSEL_NAME)
                    logger.info("Table sellers was drop")
                else:
                    logger.warning(f'The table {table_name_sellers} not found')
            else:
                # logger.warning("Something went wrong while creating the database")
                pass

            if method_table=="TABLE-DELETE-ALL" or method_table=="TABLE-DELETE-G":
                logger.info("Start droping table goods.")
                # CREAT TABLE (TABLE_GOOD_NAME) FOR DB_GOODS
                if db.table_exists(table_name=table_name_goods, dbname=DBGOOD_NAME):
                    db.drop_table(table_name=table_name_goods, database=DBGOOD_NAME)
                    logger.info("Table goods was drop")
                else:
                    logger.warning(f'The table {table_name_sellers} not found')
            else:
                # logger.warning("Something went wrong while creating the database")
                pass
        else:
            logger.error("One of the values for this method to work is missing")

        if method_table=="DATA-SAVE":
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                if data_s:
                    db.save_new_inf(database=DBSEL_NAME, data_s=data_s)
                elif data_g:
                    db.save_new_inf(database=DBGOOD_NAME, data_g=data_g)
                else:
                    logger.warning("The module could not recognize the data")
        else: pass

        if method_table=="DATA-UPD":
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                if data_s:
                    db.update_data(data_s=data_s)
                if data_g:
                    db.update_data(data_g=data_g)
        else: pass

        if method_table=="DATA-READ":
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                if supplier_id:
                    seller_inf, goods_inf = db.read_inf(number=supplier_id, id_name=id_name)
                    return seller_inf, goods_inf 
                else:
                    logger.warning("Error supplier_id and reading data")
        else: pass

        if method_table=="DATA-DELETE":
            if DB_USER and DB_PASSWORD and HOST_PSQL and PORT_PSQL:
                db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
                if supplier_id:
                    db.delete_inf(supplier_id=supplier_id)
                else:
                    logger.warning("Error supplier_id and deleting data")
        else: pass
            
    elif method_table == None:
        pass
    else:
        message_error = "ERROR method_table. Check the method_table name!"
        logger.error(message_error)


if __name__=="__main__":

    # from test_inf import seller_inf, goods_inf 

    # main_db(method_db="DELETE-ALL")
    # main_db(method_table="TABLE-DELETE-G")
    # main_db(method_db="CREATE-ALL", method_table="TABLE-CREATE-ALL")
    # main_db(method_table="TABLE-CREATE-G")
    # main_db(method_table="DATA-SAVE", data_s=seller_inf)
    # main_db(method_table="DATA-SAVE", data_g=goods_inf)
    # main_db(method_table ="DATA-DELETE", data=seller_inf, supplier_id=104452)
    # main_db(method_table ="DATA-READ", supplier_id=104452)
    data = main_db(method_table ="DATA-READ", supplier_id=104452) 
    print(data[0]) 

    # main_db(method_table="DATA-UPD", data_s=seller_inf)


    # TEST BLOCK
    # db = DbSellersGoods(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
    # db.save_new_inf(database=DBSEL_NAME, new_inf=seller_inf)
    # db.save_new_inf(database=DBSEL_NAME, new_inf=goods_inf)
    # db.read_inf(number=104452)
    # db.update_data( data_g=goods_inf)
    # db.update_data( data_s=seller_inf)
    # db.update_data(data_s=seller_inf, data_g=goods_inf)

    # db.save_new_inf(database=DBSEL_NAME, new_inf=seller_inf)
    # db.save_new_inf(database=DBGOOD_NAME, new_inf=goods_inf)
    # db.read_inf(supplier_id=104452, database_sellers=DBSEL_NAME, table_name_sellers=table_name_sellers)
    # db.read_inf(supplier_id=104452, database_sellers=DBSEL_NAME, table_name_sellers=table_name_sellers)
    # db.read_inf(supplier_id=104452, database_goods=DBGOOD_NAME, table_name_goods=table_name_goods)
    pass


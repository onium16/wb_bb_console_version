# wbbase\wbbase_app\dbworker\db_manager.py

from dotenv import dotenv_values
from loguru import logger
import psycopg2
import hashlib
from logger_own_settings import mylogger

# Connecting the logger with settings in the environment.
mylogger()

class DatabaseManager:
    def __init__(self, user, password, host, port, dbname, table_name):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        self.conn = self._connect()
        self.table_name = table_name


    def _connect(self):
        return psycopg2.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            dbname=self.dbname
        )

    def create_database(self, dbase, user, password, host, port):
        """
        CREATE DB
        """
        try:
            temp_conn = psycopg2.connect(user=user, password=password, host=host, port=port)
            temp_conn.autocommit = True
            temp_cur = temp_conn.cursor()
            temp_cur.execute(f"""CREATE DATABASE {dbase}
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
            logger.info(f"Database {dbase} was created successfully.")
        except psycopg2.errors.DuplicateDatabase as edb:
            logger.info(f"Database {dbase} already exists.")
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

    def create_user_table(self, dbase, table_name):
        """
        CREATE TABLE _USERS IN DB USERS
        """
        # Create the users table if it does not exist with additional fields (email and company_name)
        try:
            # If a specific database is specified, create a new connection
            if dbase:
                self.dbname = dbase
                self.conn = self._connect()

            # Create cursor
            with self.conn.cursor() as cur:
                # Create a table if it does not exist.
                cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(64) NOT NULL,
                            company_name VARCHAR(100)
                            );""")
                self.conn.commit()
                logger.info(f"The table {table_name} has been successfully created for the {dbase} database.")
        except NameError as e:
            logger.error(f"Error creating the table: {e}")

    def add_user(self, username, password, email, company_name=None):
        # Hash the password using SHA-2
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            # Add the user to the database
            with self.conn, self.conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {self.table_name} (username, password_hash, email, company_name) VALUES (%s,%s,%s,%s);", (username, password_hash, email, company_name)
                )
                logger.info(f"User '{username}' successfully added.")
        except psycopg2.errors.UniqueViolation as eunique:
            error_code = eunique.pgcode
            logger.error(error_code)
            if 'email' in str(eunique):
                logger.warning(f"A user with this email ('{email}') already exists.")
            else:
                logger.warning(f"A user with this name ('{username}') already exists.")

    def read_users(self):
        # Read the list of users from the database
        read_users_query = 'SELECT id, username FROM {};'.format(self.table_name)
        with self.conn, self.conn.cursor() as cur:
            cur.execute(read_users_query)
            users = cur.fetchall()
        return users

    def read_users_with_details(self):
        # Read the list of users from the database, including email and company_name
        read_users_query = 'SELECT id, username, email, company_name FROM {};'.format(self.table_name)
        with self.conn, self.conn.cursor() as cur:
            cur.execute(read_users_query)
            users = cur.fetchall()
        return users
    
    def authenticate_user(self,  username, password):
        # Check user and password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        authenticate_user_query = f"SELECT * FROM {self.table_name} WHERE username = %s AND password_hash = %s;"
        with self.conn, self.conn.cursor() as cur:
            cur.execute(authenticate_user_query, (username, password_hash,))
            user = cur.fetchone()
            return user is not None
        
    def change_password(self, username, old_password, new_password):
        # Authenticate user with the old password
        if self.authenticate_user(username, old_password):
            # Hash the new password using SHA-2
            new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()

            try:
                # Update the user's password in the database
                with self.conn, self.conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {self.table_name} SET password_hash = %s WHERE username = %s;",
                        (new_password_hash, username)
                    )
                    logger.info(f"Password for user '{username}' has been successfully changed.")
                    return True
            except Exception as e:
                logger.error(f"Error changing password: {e}")
                return False
        else:
            logger.error("Authentication failed. Unable to change the password.")
        
    def remove_user(self, username, password):
        # Remove the user from the database
        authenticate_query =self.authenticate_user(self.table_name, username, password)
        remove_user_query = 'DELETE FROM {} WHERE username = %s;'.format(self.table_name)
        if authenticate_query:
            try:
                with self.conn, self.conn.cursor() as cur:
                    cur.execute(remove_user_query, (username,))
                    self._connect().commit()
                    logger.info(f"The user '{username}' has been deleted.")
            except Exception as e:
                logger.error(f"{e}")
        else:
            logger.error("Authorization to delete the user failed.")

    def get_user_details(self, username):
        """
        Fetching additional user data (email and company_name) based on the username.
        """
        try:
            with self.conn, self.conn.cursor() as cur:
                cur.execute(f"SELECT email, company_name FROM {self.table_name} WHERE username = %s;", (username,))
                user_details = cur.fetchone()
                return {'email': user_details[0], 'company_name': user_details[1]} if user_details else {}
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return {}
        
if __name__ == "__main__":
    env_vars = dotenv_values(".env")
    # Access the variables in the dictionary
    DB_USER = env_vars.get("USER_PSQL")
    DB_PASSWORD = env_vars.get("PASSWORD_PSQL")
    HOST_PSQL = env_vars.get("HOST_PSQL")
    PORT_PSQL = env_vars.get("PORT_PSQL")
    DBUSER_NAME = env_vars.get("DBUSER")
    TABLE_USERS_NAME = env_vars.get("TABLE_USERS_NAME")
    DBSEL_NAME = env_vars.get("DBSEL_NAME")
    DBGOOD_NAME = env_vars.get("DBGOOD_NAME")
    table_name_sellers = env_vars.get("TABLE_SEL_NAME")
    table_name_goods = env_vars.get("TABLE_GOOD_NAME")

    # Replace connection parameters with your own
    db_manager = DatabaseManager(user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL, dbname=DBUSER_NAME, table_name=TABLE_USERS_NAME)
    # db_manager.delete_database(dbname=DBUSER_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
    # db_manager.create_database(dbase=DBUSER_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)
    # db_manager.create_user_table(dbase=DBUSER_NAME, table_name=TABLE_USERS_NAME)

    # # Add a user
    # db_manager.add_user(username='leo', password='password123', email='leo@example.com', company_name='Company ABC')

    # # db_manager.remove_user(username='leo', password='password123')

    # # Read users
    # users = db_manager.read_users()
    # print("Users in the database:", users)
    # # Read users
    # users = db_manager.read_users_with_details()
    # print("Users in the database:", users)

    # # Authenticate user
    # # Note: You need to implement the authenticate_user method
    # is_authenticated = db_manager.authenticate_user(username='leo', password='password123')
    # print("User authentication:", is_authenticated)

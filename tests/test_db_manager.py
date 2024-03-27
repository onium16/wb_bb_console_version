import pytest
import psycopg2
from dotenv import dotenv_values
from db_manager import DatabaseManager
from loguru import logger

from logger_own_settings import test_logger

test_logger()

env_vars = dotenv_values(".env")
DB_USER = env_vars.get("USER_PSQL")
DB_PASSWORD = env_vars.get("PASSWORD_PSQL")
HOST_PSQL = env_vars.get("HOST_PSQL")
PORT_PSQL = env_vars.get("PORT_PSQL")
DB_TEST_NAME = "db_test"
DB_TEST_TABLE_NAME = "table_test"


@pytest.fixture
def db_manager():
    return DatabaseManager(
                           user=DB_USER, 
                           password=DB_PASSWORD, 
                           host=HOST_PSQL, 
                           port=PORT_PSQL, 
                           dbname=DB_TEST_NAME, 
                           table_name=DB_TEST_TABLE_NAME
                           )

@pytest.fixture
def connect_SQL():
    try:
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=HOST_PSQL,
            port=PORT_PSQL,
        )
        yield connection
    finally:
        if connection:
            connection.close()

def test_database_connection(connect_SQL):
    assert connect_SQL is not None

def test_create_database():
    """
    Test to ensure the creation of a database.
    """
    db_manager = DatabaseManager(
                           user=DB_USER, 
                           password=DB_PASSWORD, 
                           host=HOST_PSQL, 
                           port=PORT_PSQL, 
                           )
    db_manager.create_database(dbase=DB_TEST_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)

def test_create_user_table(db_manager):
    """
    Test to verify the creation of a user table within the database.
    """
    db_manager.create_user_table(dbase=DB_TEST_NAME, table_name=DB_TEST_TABLE_NAME)

@pytest.mark.parametrize("username, password, email, company_name", [
    ("Alice", "alice123", "alice@example.com", "Wonderland Inc."),
    ("Bob", "bob456", "bob@example.com", "Bob's Burgers"),
    ("Charlie", "charlie789", "charlie@example.com", "Chocolate Factory"),
    ("Diana", "diana101", "diana@example.com", "Diana's Designs"),
    ("Eve", "eve2022", "eve@example.com", "Eve's Events")
])
def test_add_user(db_manager, username, password, email, company_name):
    """
    Test to add a user to the database.
    """
    db_manager.add_user(username, password, email, company_name)
    # Optionally, add assertions to check if the user was added successfully

def test_read_users(db_manager):
    """
    Test to read users from the database.
    """
    result = db_manager.read_users()
    logger.info(result)

def test_read_users_with_details(db_manager):
    """
    Test to read users with their details from the database.
    """
    result = db_manager.read_users_with_details()
    logger.info(result)

@pytest.mark.parametrize("username, old_password, new_password", [
    ("Alice", "alice123",  "alice222"),
    ("Bob", "bob456", "bob222"),
    ("Charlie", "charlie789","charlie222"),
    ("Diana", "diana101", "diana222"),
    ("Eve", "eve2022", "eve2222"),
])
def test_change_password(db_manager, username, old_password, new_password):
    """
    Test to change a user's password in the database.
    """
    result = db_manager.change_password(username, old_password, new_password)
    logger.info(result)

@pytest.mark.parametrize("username, password", [
    ("Alice", "alice222"),
    ("Bob", "bob222"),
    ("Charlie", "charlie222"),
    ("Diana", "diana222"),
    ("Eve", "eve2222"),
])
def test_authenticate_user(db_manager, username, password):
    """
    Test to authenticate a user with their credentials.
    """
    result = db_manager.authenticate_user( username, password)
    logger.info(result)

@pytest.mark.parametrize("username, password", [
    ("Alice", "alice222"),
    ("Bob", "bob222"),
])
def test_remove_user_correct_password(db_manager,  username, password):
    """
    Test to remove a user from the database with the correct password.
    """
    result = db_manager.remove_user( username, password)
    logger.info(result)
    assert result == True, "Correct password for deleting user."

@pytest.mark.parametrize("username, password", [
    ("Charlie", "charlie789"),
    ("Diana", "diana101"),
    ("Eve", "eve2022")
])
def test_remove_user_incorrect_password(db_manager, username, password):
    """
    Test to remove a user from the database with an incorrect password.
    """
    result = db_manager.remove_user( username, password)
    logger.info(result)
    assert result == False, "Incorrect password for deleting user."

@pytest.mark.parametrize("username", [
    ("Charlie"),
    ("Diana"),
    ("Eve")
])
def test_get_user_details_existing_user(db_manager, username):
    """
    Test to get details of an existing user from the database.
    """
    result = db_manager.get_user_details(username)
    assert result != None, "This user name is in the list."

@pytest.mark.parametrize("username", [
    ("Salma"),
    ("Moby"),
])
def test_get_user_details_non_existing_user(db_manager, username):
    """
    Test to get details of a non-existing user from the database.
    """
    result = db_manager.get_user_details(username)
    assert result != None, "This user name isn't in the list."

def test_delete_database(db_manager):
    """
    Test to delete a database.
    """
    db_manager.delete_database(dbname=DB_TEST_NAME, user=DB_USER, password=DB_PASSWORD, host=HOST_PSQL, port=PORT_PSQL)

if __name__ == "__main__":
    pass

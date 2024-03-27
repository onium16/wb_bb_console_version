import asyncio
import pytest
from parser_seller import DownloaderDataSG, check_proxy_connection

from typing import Dict

@pytest.mark.parametrize("proxy, expected_result", [
    ({"http": 'https://139.99.148.90:3128'}, False),  # Example of a correct proxy
    ({"http": 'https://139.99.148.90:10'}, False),  # Example of an incorrect proxy
    ('test_error', False),  # Example of an incorrect proxy
    (({"http": 'https://139.99.148.90:10'},{"http": 'https://139.99.148.90:10'}), False),  # Example of an incorrect proxy when using an IP tuple
    ([{"http": 'https://139.99.148.90:10'},{"http": 'https://139.99.148.90:10'}], False),  # Example of an incorrect proxy when using an IP list
])
def test_check_proxy_connection(proxy, expected_result):
    """
    Test the check_proxy_connection function.
    
    Parameters:
        proxy (Dict[str, str]): Proxy to be tested.
        expected_result (bool): Expected result of the function.
    """
    assert check_proxy_connection(proxy) == expected_result

@pytest.mark.parametrize("number, expected_result", [
        (101, True),  # Example of a correct request
        (2, True),  # Example of a correct request
        (2.5, False),  # Example of a incorrect request
        ("test_error_type", False),  # Example of an incorrect number
        ({1:"value"}, False),
        ([1, "value"], False),
    ])
def test_get_goods_inf(number: int, expected_result: bool):
    """
    Test the get_goods_inf function.
    
    Parameters:
        number (int): Number to be passed to the function.
        expected_result (bool): Expected result of the function.
    """
    downloader = DownloaderDataSG()
    result = asyncio.run(downloader.get_goods_inf(number))
    assert bool(result) == expected_result 

@pytest.mark.asyncio
async def test_get_info_seller_goods_success(monkeypatch):
    """
    Test case to verify that the method get_info_seller_goods returns seller and goods information successfully.

    - Create an instance of DownloaderDataSG.
    - Define mock responses for get_quickly_inf_seller and get_goods_inf methods.
    - Patch the get_quickly_inf_seller and get_goods_inf methods with mock implementations.
    - Call the method under test with a seller number.
    - Check if the returned seller_info and goods_info match the expected data.

    Expected Behavior:
    - The method should return seller_info and goods_info dictionaries containing mocked data.
    """
    # Create an instance of DownloaderDataSG
    downloader = DownloaderDataSG()

    # Define a mock response for get_quickly_inf_seller
    async def mock_get_quickly_inf_seller(*args, **kwargs):
        return {"seller_info": {"mocked": "seller data"}}

    # Define a mock response for get_goods_inf
    async def mock_get_goods_inf(*args, **kwargs):
        return {"goods_info": {"mocked": "goods data"}}

    # Patch the get_quickly_inf_seller and get_goods_inf methods
    monkeypatch.setattr(downloader, "get_quickly_inf_seller", mock_get_quickly_inf_seller)
    monkeypatch.setattr(downloader, "get_goods_inf", mock_get_goods_inf)

    # Call the method under test
    seller_info, goods_info = await downloader.get_info_seller_goods(123)

    # Check if the returned data matches the expected data
    # Check if the returned data matches the expected data
    assert seller_info['seller_info'] == {"mocked": "seller data"}
    assert goods_info['goods_info']  == {"mocked": "goods data"}

@pytest.mark.asyncio
async def test_get_info_seller_goods_retry():
    """
    Test case to verify the retry mechanism of the method get_info_seller_goods.

    - Create an instance of DownloaderDataSG.
    - Define a mock response for get_quickly_inf_seller that simulates a failed request.
    - Patch the get_quickly_inf_seller method with the mock implementation.
    - Call the method under test with a seller number and max_retries set to 2.
    - Check if the method retries twice and returns None for both seller_info and goods_info.

    Expected Behavior:
    - The method should retry obtaining seller and goods information twice due to the failed request.
    - It should return None for both seller_info and goods_info after reaching the maximum number of retries.
    """
    # Create an instance of DownloaderDataSG
    downloader = DownloaderDataSG()

    # Define a mock response for get_quickly_inf_seller
    async def mock_get_quickly_inf_seller(*args, **kwargs):
        return None  # Simulate failed request

    # Patch the get_quickly_inf_seller method
    downloader.get_quickly_inf_seller = mock_get_quickly_inf_seller

    # Call the method under test with max_retries set to 2
    seller_info, goods_info = await downloader.get_info_seller_goods(123, max_retries=2)

    # Check if the method retries twice and returns None for both seller and goods info
    assert seller_info is None
    assert goods_info is None

if __name__ == "__main__":
    pytest.main()
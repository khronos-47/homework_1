from uuid import uuid4

from shortener.utils import check_website_exist


class TestFunctionCheckWebsiteExist:
    async def test_non_existing_service(self, client):
        url = f"https://{uuid4().hex}.com"
        verdict, message = await check_website_exist(url)
        assert verdict is False

    async def test_existing_service(self):
        url = "https://yandex.ru"
        verdict, message = await check_website_exist(url)
        assert verdict is True

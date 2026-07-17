import requests

class LisskinsAPIError(Exception):
    pass

class SearchParams:
    def __init__(self, game, per_page=50, cursor=None, sort_by="newest", price_to=None):
        self.game = game
        self.per_page = per_page
        self.cursor = cursor
        self.sort_by = sort_by
        self.price_to = price_to

    def to_query(self):
        query = {
            "game": self.game,
            "per_page": self.per_page,
            "sort_by": self.sort_by
        }
        if self.cursor:
            query["cursor"] = self.cursor
        if self.price_to:
            query["price_to"] = self.price_to
        return query

class LisskinsClient:
    BASE_URL = "https://api.lis-skins.com/v1"

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    def _request(self, method, endpoint, params=None):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"X-Api-Key": self.api_key}

        resp = self.session.request(method, url, headers=headers, params=params)

        if resp.status_code != 200:
            raise LisskinsAPIError(f"HTTP {resp.status_code}: {resp.text}")

        return resp.json()

    def search_items(self, search_params: SearchParams):
        query = search_params.to_query()
        return self._request("GET", "/market/search", params=query)

    def close(self):
        self.session.close()

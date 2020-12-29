import requests
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from ..settings import USER_AGENT, BRANDS, STORES, BASE_URL
from ..items import ProductItem


class ProductsSpider(CrawlSpider):
    """
    Spider for crawling through homedepot.com
    It crawls starting from pages specified in start_urls through specific brand pages specified in data.brands
    """

    name = 'products'
    allowed_domains = ['homedepot.com']
    start_urls = [f"{BASE_URL}/{b['base_path']}/{b['nav_param']}" for b in BRANDS.values()]

    # Rules for crawling are dynamically created from specified brands for each sub department
    rule_paths = [f"{b['base_path']}/{brand}/" for b in BRANDS.values() for brand in b['brands']]
    rules = (Rule(LinkExtractor(allow=tuple(rule_paths)),
                  callback="parse_item",
                  follow=False),)

    with open("home_depot/query_string.txt", "r") as f:
        query_string = f.read()

    def parse_item(self, response):
        """
        Main parsing function. Splits url in order to extract nav_param and sub_department for /model request.
        Then performs the request for each store and extracts products from the response.

        :param response: scrapy.Response object - response of a brand page
        :return: yields a product list
        """
        sub_department = response.url.split("/")[-3].split("-")[-1]
        brand = response.url.split("/")[-2].split("-")[-1]
        nav_param = response.url.split("N-")[-1]

        for store_loc, store_id in STORES.items():
            for product_data in self.fetch_products(nav_param, store_id, sub_department):
                product = self.load_product(product_data)
                yield {'product': product,
                       'store_loc': store_loc,
                       'sub_department': sub_department,
                       'brand': brand}

    def fetch_products(self, nav_param, store_id, sub_department, page_size=48):
        """
        Fetches products list using /model request. As maximum value for pageSize is 48 request is executed as long as
        resulting list isn't shorter than page_size.
        Solved with requests as scrapy.Request object with configuration loaded from exported CURL request only
        returned 400 error code.

        :param nav_param: str - parameter used for specifying department and brand
        :param store_id: str - id of the store for which to fetch data
        :param sub_department: str - name of the sub_department, possible values: Dishwashers, Refrigerators, Mattresses
        :param page_size: int - number of results; maximum value is 48
        :return: list[dict] - list of products' data
        """
        start_index, current_size = 0, page_size
        while current_size >= page_size:
            req = requests.post(
                f'{BASE_URL}/product-information/model',
                headers={
                    'user-agent': USER_AGENT,
                    'x-experience-name': 'major-appliances' if sub_department in {"Dishwashers",
                                                                                  "Refrigerators"} else 'hd-home'
                },
                json={
                    "operationName": "searchModel",
                    "query": self.query_string,
                    "variables": {
                        "navParam": nav_param,
                        "storeId": store_id,
                        "pageSize": page_size,
                        "startIndex": start_index
                    }
                }
            )
            current_products = req.json()['data']['searchModel']['products']
            for product in current_products:
                yield product

            current_size = len(current_products)
            start_index += page_size

    def load_product(self, product_data):
        """
        Extracts specific data from API result and creates ProductItem object with it.

        :param product_data: dict - product data fetched from API (/model)
        :return: ProductItem - object created with extracted data
        """
        loader = ItemLoader(item=ProductItem())

        loader.add_value('url', f"{BASE_URL}{product_data['identifiers']['canonicalUrl']}")
        loader.add_value('brand', product_data['identifiers']['brandName'])
        loader.add_value('model_number', product_data['identifiers']['modelNumber'])
        loader.add_value('product_type', product_data['identifiers']['productType'])
        loader.add_value('product_label', product_data['identifiers']['productLabel'])
        loader.add_value('item_id', product_data['itemId'])
        loader.add_value('availability',
                         None if product_data['availabilityType']['discontinued'] else product_data['availabilityType'][
                             'type'])
        loader.add_value('average_rating', product_data['reviews']['ratingsReviews']['averageRating'])
        loader.add_value('reviews_count', product_data['reviews']['ratingsReviews']['totalReviews'])
        loader.add_value('price', product_data['pricing']['value'] if product_data['pricing'] else None)
        loader.add_value('features', product_data['keyProductFeatures'])

        return loader.load_item()

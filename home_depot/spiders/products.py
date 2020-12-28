import os
import json
import requests
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ..items import ProductItem
from ..data import stores, brands, query_string


class ProductsSpider(CrawlSpider):
    """
    Spider for crawling through homedepot.com
    It crawls starting from pages specified in start_urls through specific brand pages specified in data.brands
    """

    base_url = "https://www.homedepot.com"

    name = 'products'
    allowed_domains = ['homedepot.com']
    start_urls = [
        f'{base_url}/b/Appliances-Dishwashers/N-5yc1vZc3po',
        f'{base_url}/b/Appliances-Refrigerators/N-5yc1vZc3pi',
        f'{base_url}/b/Furniture-Bedroom-Furniture-Mattresses/N-5yc1vZc7oe'
    ]

    # Rules for crawling are dynamically created from specified brands for each sub department
    rules = (
        Rule(
            LinkExtractor(
                allow=tuple([f"{b['base_url']}/{brand}/" for b in brands.BRANDS.values() for brand in b['brands']])
            ),
            callback="parse_item",
            follow=False),
    )

    result_dir = os.path.join("results")
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)

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

        for store_loc, store_id in stores.STORES.items():
            prdcts = [self.transform_product(prod)
                      for prod in self.fetch_products(nav_param, store_id, sub_department)
                      if prod]

            with open(os.path.join(self.result_dir, f"{store_loc}_{sub_department}_{brand}.json"), "w") as f:
                json.dump([dict(p) for p in prdcts], f)

            yield {'products': prdcts}

    def fetch_products(self, nav_param, store_id, sub_department, page_size=48):
        """
        Fetches products list using /model request. As maximum value for pageSize is 48 request is executed as long as
        resulting list isn't shorter than page_size.

        :param nav_param: str - parameter used for specifying department and brand
        :param store_id: str - id of the store for which to fetch data
        :param sub_department: str - name of the sub_department, possible values: Dishwashers, Refrigerators, Mattresses
        :param page_size: int - number of results; maximum value is 48
        :return: list[dict] - list of products' data
        """
        prdcts, start_index, current_size = list(), 0, page_size
        while current_size >= page_size:
            req = requests.post(
                f'{self.base_url}/product-information/model',
                headers={
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'x-experience-name': 'major-appliances' if sub_department in {"Dishwashers",
                                                                                  "Refrigerators"} else 'hd-home'
                },
                json={
                    "operationName": "searchModel",
                    "query": query_string.QUERY_STRING,
                    "variables": {
                        "navParam": nav_param,
                        "storeId": store_id,
                        "pageSize": page_size,
                        "startIndex": start_index
                    }
                }
            )
            current_products = req.json()['data']['searchModel']['products']
            current_size = len(current_products)
            prdcts.extend(current_products)
            start_index += page_size
        return prdcts

    @staticmethod
    def transform_product(product_data):
        """
        Extracts specific data from API result and creates ProductItem object with it.

        :param product_data: dict - product data fetched from API (/model)
        :return: ProductItem - object created with extracted data
        """
        product = ProductItem()

        product['url'] = product_data['identifiers']['canonicalUrl'],
        product['brand'] = product_data['identifiers']['brandName'],
        product['model_number'] = product_data['identifiers']['modelNumber'],
        product['product_type'] = product_data['identifiers']['productType'],
        product['product_label'] = product_data['identifiers']['productLabel'],
        product['item_id'] = int(product_data['itemId']),
        product['availability'] = None if product_data['availabilityType']['discontinued'] else \
                                      product_data['availabilityType']['type'],
        product['average_rating'] = float(product_data['reviews']['ratingsReviews']['averageRating']),
        product['reviews_number'] = int(product_data['reviews']['ratingsReviews']['totalReviews']),
        product['price'] = float(product_data['pricing']['value']) if product_data['pricing'] else None,
        product['features'] = {"_".join(f['name'].lower().split()): f['value'] for f in
                               product_data['keyProductFeatures']['keyProductFeaturesItems'][0]['features']}

        return product

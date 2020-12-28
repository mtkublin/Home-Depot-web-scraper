# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from typing import Dict


class ProductItem(scrapy.Item):
    """
    Product item with all fields to extract from API
    """
    # define the fields for your item here like:
    url: str = scrapy.Field()
    brand: str = scrapy.Field()
    model_number: str = scrapy.Field()
    product_type: str = scrapy.Field()
    product_label: str = scrapy.Field()
    item_id: int = scrapy.Field()
    availability: str = scrapy.Field()
    average_rating: float = scrapy.Field()
    reviews_number: int = scrapy.Field()
    price: float = scrapy.Field()
    features: Dict[str, str] = scrapy.Field()

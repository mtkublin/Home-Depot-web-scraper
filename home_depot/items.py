# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from typing import Dict
import scrapy
from itemloaders.processors import MapCompose, TakeFirst


def parse_features(feature_data):
    """
    Parses passed feature data to dict
    :param feature_data: dict - original feature data object from API
    :return: dict - parsed feature data
    """
    return {"_".join(f['name'].lower().split()): f['value']
            for f in feature_data['keyProductFeaturesItems'][0]['features']}


class ProductItem(scrapy.item.Item):
    """
    Product item with all fields to extract from API
    """
    # define the fields for your item here like:
    url: str = scrapy.item.Field(
        input_processor=MapCompose(lambda x: x.strip()),
        output_processor=TakeFirst()
    )
    brand: str = scrapy.item.Field(
        input_processor=MapCompose(lambda x: x.strip()),
        output_processor=TakeFirst()
    )
    model_number: str = scrapy.item.Field(
        input_processor=MapCompose(lambda x: x.strip()),
        output_processor=TakeFirst()
    )
    product_type: str = scrapy.item.Field(
        input_processor=MapCompose(lambda x: x.strip()),
        output_processor=TakeFirst()
    )
    product_label: str = scrapy.item.Field(
        input_processor=MapCompose(lambda x: x.strip()),
        output_processor=TakeFirst()
    )
    item_id: int = scrapy.item.Field(
        input_processor=MapCompose(lambda x: int(x)),
        output_processor=TakeFirst()
    )
    availability: str = scrapy.item.Field(
        input_processor=MapCompose(lambda x: x.strip()),
        output_processor=TakeFirst()
    )
    average_rating: float = scrapy.item.Field(
        input_processor=MapCompose(lambda x: float(x)),
        output_processor=TakeFirst()
    )
    reviews_count: int = scrapy.item.Field(
        input_processor=MapCompose(lambda x: int(x)),
        output_processor=TakeFirst()
    )
    price: float = scrapy.item.Field(
        input_processor=MapCompose(lambda x: float(x)),
        output_processor=TakeFirst()
    )
    features: Dict[str, str] = scrapy.item.Field(
        input_processor=MapCompose(parse_features),
        output_processor=TakeFirst()
    )

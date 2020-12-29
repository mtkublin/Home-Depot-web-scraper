# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import json
from itemadapter import ItemAdapter


class SaveProductsPipeline:
    """
    Saves products to json files
    """
    result_dir = os.path.join("results")
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)

    def process_item(self, item, spider):
        """
        Saves each yielded product to a json file, named with store location, sub department, brand and item id

        :param item: dict - item yielded by spider, contains ProductItem and 2 additional string fields
                            (store_loc, sub_department)
        :param spider: scrapy.Spider - spider object
        :return: ProductItem - product item object
        """
        product = item['product']
        product_dict = ItemAdapter(product).asdict()

        file_name = f"{item['store_loc']}_{item['sub_department']}_{product['brand']}_{product['item_id']}.json"

        with open(os.path.join(self.result_dir, file_name), "w") as f:
            json.dump(product_dict, f)

        return product

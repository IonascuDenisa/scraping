# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from scrapy.exceptions import DropItem


class Sys2Pipeline:
    def process_item(self, item, spider):
        return item


class RequiredFieldPipeline:
    def process_item(self, item, spider):
        required_fields = ['time_slots', 'available_slots_count', 'date']

        for field in required_fields:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field}")

        return item
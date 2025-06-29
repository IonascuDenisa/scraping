# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class AppointmentItem(scrapy.Item):
    address = scrapy.Field()
    available_slots_count = scrapy.Field()
    appointment_type = scrapy.Field()
    doctor_name = scrapy.Field()
    date = scrapy.Field()
    location = scrapy.Field()
    time_slots = scrapy.Field()
    link = scrapy.Field()


class Sys2Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


import json
from copy import deepcopy

import scrapy
import jmespath
from ..items import AppointmentItem
from urllib.parse import quote_plus

class ThrivepetcareComSpider(scrapy.Spider):
    name = "thrivepetcare.com"
    allowed_domains = ["thrivepetcare.com"]
    start_urls = ["https://www.thrivepetcare.com/all-locations"]

    appointment_types_url_pattern = "https://www.thrivepetcare.com/api/booking/v1/appointments/{location_id}/types-statuses?showOnlyForOnlineBooking=true"

    available_dates_url_pattern = "https://www.thrivepetcare.com/api/booking/v1/locations/{location_id}/available-dates?appointmentTypeId={appointment_type_id}"

    providers_url_pattern = "https://www.thrivepetcare.com/api/booking/v1/locations/{location_id}/providers-schedule?selectedDate={date}&onlyActive=true&vetOnly=true&&appointmentTypeId={appointment_type_id}"

    time_slots_url_pattern = "https://www.thrivepetcare.com/api/booking/v2/{location_id}/availabletimes/{appointment_type_id}/{date}?providerId={provider_id}"

    item_url_pattern = "https://www.thrivepetcare.com/unified-website-booking?locationId={location_id}&appointmentType={appointment_type}&appointmentTypeId={appointment_type_id}&date={date}&step=selectAppointmentTime"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response, **kwargs):
        script = response.xpath("//script[contains(.,'city')]/text()").get()
        jmes = json.loads(script)

        locations = jmespath.search('props.pageProps.groupedLocations[].locationByStateAndCity[].locations[]', jmes)

        for location in locations:
            item = AppointmentItem()

            address = ', '.join(filter(None, [
                location.get('addressLine1'),
                location.get('addressLine2'),
                location.get('city'),
                location.get('state')
            ]))

            item['address'] = address
            item['location'] = location['locationName']

            yield scrapy.Request(url=self.appointment_types_url_pattern.format(location_id=location['locationId']),
                                 callback=self.parse_appointment_types,
                                 headers=self.headers,
                                 meta={'item': deepcopy(item)})

    def parse_appointment_types(self, response, **kwargs):
        jmes = response.json()
        item = response.meta['item']

        appointments = jmespath.search(
            'appointmentTypes[?enabledForOnlineBooking ==`true`].[locationId, id, name]', jmes)

        for location_id, appointment_type_id, appointment_type_name in appointments:
            item['appointment_type'] = appointment_type_name

            url = self.available_dates_url_pattern.format(location_id=location_id,
                                                          appointment_type_id=appointment_type_id)
            yield scrapy.Request(
                url=url,
                callback=self.parse_available_dates,
                headers=self.headers,
                meta={'location_id': location_id, 'appointment_type_id': appointment_type_id, 'item': deepcopy(item)})

    def parse_available_dates(self, response):
        jmes = response.json()
        item = response.meta['item']

        available_dates = jmespath.search('data[?hasAvailableTime == `true`].date', jmes)

        if available_dates:
            for date in available_dates:
                item['date'] = date

                url = self.providers_url_pattern.format(location_id=response.meta['location_id'], date=date,
                                                        appointment_type_id=response.meta['appointment_type_id'])
                yield scrapy.Request(url=url,
                                     callback=self.parse_providers,
                                     headers=self.headers,
                                     meta={'location_id': response.meta['location_id'],
                                           'appointment_type_id': response.meta['appointment_type_id'],
                                           'item': deepcopy(item)})

    def parse_providers(self, response):
        jmes = response.json()
        item = response.meta['item']

        providers = jmespath.search('providers[]', jmes)

        for provider in providers:
            item['doctor_name'] = provider["name"]
            item['link'] = self.item_url_pattern.format(location_id=response.meta['location_id'],
                                                        appointment_type=quote_plus(item['appointment_type']),
                                                        appointment_type_id=response.meta['appointment_type_id'],
                                                        date=item['date'])

            url = self.time_slots_url_pattern.format(location_id=response.meta['location_id'],
                                                     appointment_type_id=response.meta['appointment_type_id'],
                                                     date=item['date'], provider_id=provider['id'])
            yield scrapy.Request(url=url,
                                 callback=self.parse_times,
                                 headers=self.headers,
                                 meta={'item': deepcopy(item)})

    def parse_times(self, response):
        jmes = response.json()
        item = response.meta['item']

        times = jmespath.search('[?status==`Available`].time', jmes)
        for time in times:
            item['time_slots'] = time
            yield item

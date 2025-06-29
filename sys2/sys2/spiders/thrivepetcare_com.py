import json
import scrapy
import jmespath


class ThrivepetcareComSpider(scrapy.Spider):
    name = "thrivepetcare.com"
    allowed_domains = ["thrivepetcare.com"]
    start_urls = ["https://www.thrivepetcare.com/all-locations"]

    appointment_types_url_pattern = "https://www.thrivepetcare.com/api/booking/v1/appointments/{id}/types-statuses?showOnlyForOnlineBooking=true"

    available_dates_url_pattern = "https://www.thrivepetcare.com/api/booking/v1/locations/{location}/available-dates?appointmentTypeId={typeId}"

    get_times_url_pattern = "https://www.thrivepetcare.com/unified-website-booking?locationId={location}&appointmentType={type}&appointmentTypeId={type_id}"

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

        location_ids = jmespath.search(
            'props.pageProps.groupedLocations[].locationByStateAndCity[].locations[].locationId', jmes)

        for location in location_ids:
            yield scrapy.Request(url=self.appointment_types_url_pattern.format(id=location),
                                 callback=self.parse_location_types, headers=self.headers,
                                 meta={'location_id': location}, )

    def parse_location_types(self, response, **kwargs):
        jmes = response.json()
        appointments = jmespath.search(
            'appointmentTypes[?enabledForOnlineBooking ==`true`].[id, name, locationId]', jmes)

        for appointment_type, name, location_id in appointments:
            url = self.available_dates_url_pattern.format(location=location_id, typeId=appointment_type)
            yield scrapy.Request(
                url=url,
                callback=self.parse_available_dates, headers=self.headers,
                meta={ 'location_id': response.meta['location_id'],
                      "appointment_type": appointment_type}, )

    def parse_available_dates(self, response):
        jmes = response.json()

        available_dates = jmespath.search('data[?hasAvailableTime == `true`].date', jmes)

        if available_dates:
            for date in available_dates:
                url = "https://www.thrivepetcare.com/api/booking/v1/locations/{location}/providers-schedule?selectedDate={date}&onlyActive=true&vetOnly=true".format(
                    location=response.meta['location_id'], date=date)
                yield scrapy.Request(url=url,
                                     callback=self.parse_providers, headers=self.headers,
                                     meta={'location_id': response.meta['location_id'],
                                           'appointment_type': response.meta['appointment_type'], 'date': date})

    def parse_providers(self, response):
        jmes = response.json()

        providers_id = jmespath.search('providers[].id', jmes)

        if providers_id:
            for provider in providers_id:
                url = "https://www.thrivepetcare.com/api/booking/v2/{location_id}/availabletimes/{ap_type}/{date}?providerId={provider_id}".format(
                    location_id=response.meta['location_id'], ap_type=response.meta['appointment_type'],
                    date=response.meta['date'], provider_id=provider)
                yield scrapy.Request(url=url,
                                     callback=self.parse_times, headers=self.headers,)

    def parse_times(self, response):
        jmes = response.json()
        times = jmespath.search('[?status==`Available`].time', jmes)


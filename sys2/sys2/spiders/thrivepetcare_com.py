import json
import scrapy
import jmespath


class ThrivepetcareComSpider(scrapy.Spider):
    name = "thrivepetcare.com"
    allowed_domains = ["thrivepetcare.com"]
    start_urls = ["https://www.thrivepetcare.com/all-locations"]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            headers=self.headers,
            meta={'proxy': 'https://161.35.98.111:8080'},
            callback=self.parse
        )

    def parse(self, response, **kwargs):
        script = response.xpath("//script[contains(.,'city')]/text()").get()
        jmes = json.loads(script)

        locations = jmespath.search('props.pageProps.groupedLocations[].locationByStateAndCity[].locations[].url', jmes)

        for url in locations:
            yield scrapy.Request(url=url, callback=self.parse_location, headers=self.headers,
            meta={'proxy': 'https://161.35.98.111:8080'},)


    def parse_location(self, response, **kwargs):
        pass
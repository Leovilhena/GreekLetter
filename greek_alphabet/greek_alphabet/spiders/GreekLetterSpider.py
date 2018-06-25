# -*- coding: utf-8 -*-

import json
import scrapy
import logging
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from fake_useragent import UserAgent


class GreekletterSpider(scrapy.Spider):
    name = 'GreekLetterSpider'
    allowed_domains = ['wikipedia.org']
    start_urls = ['https://en.wikipedia.org/wiki/Greek_alphabet']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        dispatcher.connect(self.quit, signals.spider_closed)
        self.results = {}

    def parse(self, response):
        """Parse the main letters from Greek Alphabet"""

        xpath_letters = response.xpath(
            '//table[@class="wikitable"][1]/tr/td/span[@title="Greek language text"]/text()'
        )

        letters = []
        for letter in xpath_letters:
            upper_lower_letter = tuple(letter.get().split(' '))
            if upper_lower_letter not in letters:
                letters.append(upper_lower_letter)

        xpath_links = response.xpath(
            '//table[@class="wikitable"][1]/tr/td//span[@title="Greek language text"]/../../td/a'
        )

        self.results = [{
            'title': a.xpath('@title').get(),
            'url': 'https://en.wikipedia.org{}'.format(a.xpath('@href').get()),
            'letter': {
                'uppercase': letters[i][0],
                'lowercase': letters[i][1]
            }
        } for i, a in enumerate(xpath_links)]

        ua = UserAgent()

        for result in self.results:
            request = scrapy.Request(
                callback=self.parse_letter,
                meta={'name': result['title'].replace('(letter)', '').strip()},
                url=result['url'],
                headers={'User-Agent': ua.random}
            )

            request.meta['result'] = result
            yield request

    def parse_letter(self, response):
        """Parse description and image from each letter"""

        result = response.meta['result']

        result['image_url'] = ''.join([
            'https:',
            response.xpath('//a[@class="image"]/img[contains(@alt, "{}")]/@src'
                           .format(response.meta['name'])).get()
            ])
        result['description'] = ''.join(
            response.xpath('//div[@class="mw-parser-output"]/p[1]//text()[preceding-sibling::h2]').getall()
                )

        return result

    def quit(self):
        logging.info(json.dumps(self.results, indent=4))

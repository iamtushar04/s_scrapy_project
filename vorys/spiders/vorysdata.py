import scrapy
import random

class VorysdataSpider(scrapy.Spider):
    name = "vorysdata"
    allowed_domains = ["vorys.com"]
    start_urls = ["https://www.vorys.com/professionals-leadership"]

    def parse(self, response):
        
        members = response.css('ul.results_list li')

        for member in members:
            try:
                email = member.css("div.email a::attr('href')").get().replace("mailto:","")
            except:
                email = None
            yield{
                'name' : member.css('div.title a::text').get(),
                'position' : member.css("div.position ::text").get(),
                'location' : member.css("div.office a::text").get(),
                'email' : email,
            }
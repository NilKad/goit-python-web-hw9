import json
import scrapy

from itemadapter import ItemAdapter

from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field


class QuoteItem(Item):
    quote = Field()
    author = Field()
    tags = Field()


class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class DataPiplines:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if "fullname" in adapter.keys():
            self.authors.append(dict(adapter))
        if "quote" in adapter.keys():
            self.quotes.append(dict(adapter))

    def close_spider(self, spider):
        with open("quotes.json", "w", encoding="utf-8") as fd:
            json.dump(self.quotes, fd, ensure_ascii=False, indent=2)

        with open("authors.json", "w", encoding="utf-8") as fd:
            json.dump(self.authors, fd, ensure_ascii=False, indent=2)


class QuotesSpider(scrapy.Spider):
    name = "get_quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]
    custom_settings = {"ITEM_PIPELINES": {DataPiplines: 300}}

    def parse(self, response, **kwargs):
        for quote in response.xpath("/html//div[@class='quote']"):
            quote_item = QuoteItem()
            quote_item["quote"] = (
                quote.xpath(".//span[@class='text']/text()").get().strip()
            )
            quote_item["author"] = (
                quote.xpath(".//small[@class='author']/text()").get().strip()
            )
            quote_item["tags"] = quote.xpath(".//div[@class='tags']/a/text()").getall()
            # TODO: clear text
            yield quote_item
            yield response.follow(
                url=self.start_urls[0] + quote.xpath("span/a/@href").get(),
                callback=self.parse_author,
            )

        print("---------------------------------------------------------")
        next_link = response.xpath("/html//li[@class='next']/a/@href").get()
        print(f"----------next link : {next_link}")
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    def parse_author(self, response, **kwargs):
        content = response.xpath("/html//div[@class='author-details']")
        fullname = content.xpath("h3[@class='author-title']/text()").get().strip()
        born_date = (
            content.xpath("p/span[@class='author-born-date']/text()").get().strip()
        )
        born_location = (
            content.xpath("p/span[@class='author-born-location']/text()").get().strip()
        )
        description = (
            content.xpath("div[@class='author-description']/text()").get().strip()
        )
        yield AuthorItem(
            fullname=fullname,
            born_date=born_date,
            born_location=born_location,
            description=description,
        )


if __name__ == "__main__":
    process = CrawlerProcess()

    # 'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    # })
    process.crawl(QuotesSpider)
    process.start()

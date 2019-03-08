import scrapy


class PaktSpider(scrapy.Spider):
    name = "packt"

    start_urls = [
        'https://www.packtpub.com/all-books/'
    ]

    def parse(self, response):
        for book_block in response.css('div.book-block'):
            overlay = book_block.css('div.book-block-overlay').xpath(".//button").attrib
            book_page = "https://www.packtpub.com" + overlay['action']
            packt_record = {
                'title': book_block.css('div.book-block-title::text').getall()[-1].strip(),
                'price_full': book_block.css("div.book-block-price-full::text").getall()[-1].strip(),
                'price_discounted': book_block.css("div.book-block-price-discounted::text").getall()[-1].strip(),
                'length': book_block.css('div.book-block-overlay-product-length::text').getall()[-1],
                'book_page': book_page,
            }
            yield scrapy.Request(url=book_page, callback=self.parse_book_page, meta={"packt_record": packt_record})

    def parse_book_page(self, response):
        packt_record = response.meta.get("packt_record")
        packt_record["author"] = response.css(
            'div.book-info-bottom-author-title').xpath(".//h3/text()").extract_first().strip()
        packt_record["description"] = response.xpath("//meta[@name='description']/@content")[0].extract().strip()
        packt_record["datePublished"] = response.xpath(
            "//time[@itemprop='datePublished']/@datetime")[0].extract().strip()
        packt_record["bookDescription"] = response.xpath(
            "//div[@class='book-info-bottom-indetail-text']//p//node()").extract()
        yield packt_record

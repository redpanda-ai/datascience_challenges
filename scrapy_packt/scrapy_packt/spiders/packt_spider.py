import scrapy


class PaktSpider(scrapy.Spider):
    name = "packt"

    start_urls = [
        'https://www.packtpub.com/all-books/'
    ]

    def parse_second_page(self, response):
        bonus = response.meta.get("bonus")
        bonus["author"] = response.css('div.book-info-bottom-author-title').xpath(".//h3/text()").extract_first().strip()
        bonus["description"] = response.xpath("//meta[@name='description']/@content")[0].extract().strip()
        bonus["datePublished"] = response.xpath("//time[@itemprop='datePublished']/@datetime")[0].extract().strip()
        bonus["bookDescription"] = response.xpath("//div[@class='book-info-bottom-indetail-text']//p//node()").extract()
        yield bonus

    def parse(self, response):
        for book_block in response.css('div.book-block'):
            overlay = book_block.css('div.book-block-overlay').xpath(".//button").attrib
            next_page = "https://www.packtpub.com" + overlay['action']
            bonus = {
                'title': book_block.css('div.book-block-title::text').getall()[-1].strip(),
                'price_full': book_block.css("div.book-block-price-full::text").getall()[-1].strip(),
                'price_discounted': book_block.css("div.book-block-price-discounted::text").getall()[-1].strip(),
                'release_date': book_block.css('div.book-block-overlay-release-date::text').getall()[-1].strip(),
                'length': book_block.css('div.book-block-overlay-product-length::text').getall()[-1],
                'nid': overlay['nid'],
                'action': overlay['action'],
                'class': overlay['class'],
            }
            yield scrapy.Request(url=next_page, callback=self.parse_second_page, meta={"bonus": bonus})
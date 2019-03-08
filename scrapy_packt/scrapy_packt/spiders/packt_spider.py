import scrapy


def helper(my_selector):
    """This function processes the output from a Selector to give the last item"""
    my_list = my_selector.getall()
    if my_list:
        return my_list[-1].strip()
    return None

def get_page(data_offset=0, rows=12):
    page = f"https://www.packtpub.com/all-books?" \
        f"search=&availability_list%5BAvailable%5D=Available&offset={data_offset}&rows={rows}&sort="
    return page


class PacktSpider(scrapy.Spider):
    """This spider crawls the Pack Publishing website for book information"""
    name = "packt"
    custom_settings = {
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32
    }

    data_offset = 0
    rows = 50

    start_urls = [
        get_page(data_offset=data_offset, rows=rows)
    ]

    def get_next_page(self, response, data_offset):
        """Parses the 'Next' all-books page, if one is available"""
        if data_offset:
            next_page = f"https://www.packtpub.com/all-books?" \
                f"search=&availability_list%5BAvailable%5D=Available&offset={data_offset}&rows=&sort="
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            return

    def parse(self, response):
        """Parses the html for a Packt all-books page"""
        paginator = response.xpath(
            f"//div[@class='paginator_top']//a[contains(@class,'solr-page-page-selector-page next')]" \
            f"[contains(text(),'Next')]").attrib
        if paginator:
            data_offset = paginator['data-offset']
        else:
            data_offset = None

        for book_block in response.css('div.book-block'):
            overlay = book_block.css('div.book-block-overlay').xpath(".//button").attrib
            book_page = "https://www.packtpub.com" + overlay['action']
            packt_record = {
                'title': helper(book_block.css('div.book-block-title::text')),
                'price_full': helper(book_block.css('div.book-block-price-full::text')),
                'price_discounted': helper(book_block.css("div.book-block-price-discounted::text")),
                'length': helper(book_block.css('div.book-block-overlay-product-length::text')),
                'book_page': book_page,
                'data_offset': data_offset
            }
            yield scrapy.Request(url=book_page, callback=self.parse_book_page, meta={"packt_record": packt_record})

        rows=50
        if data_offset:
            yield scrapy.Request(get_page(data_offset=data_offset, rows=rows), callback=self.parse)
        else:
            return

    def parse_book_page(self, response):
        """Parses the html for a Packt book page"""
        packt_record = response.meta.get("packt_record")
        packt_record['isbn'] = response.xpath(
            "//div[@class='book-info-details onlyDesktop']//div[@class='book-info-isbn13']//span[@itemprop='isbn']/text()").extract()
        packt_record["author"] = response.css(
            'div.book-info-bottom-author-title').xpath(".//h3/text()").extract_first().strip()
        packt_record["description"] = response.xpath("//meta[@name='description']/@content")[0].extract().strip()
        packt_record["date_published"] = response.xpath(
            "//time[@itemprop='datePublished']/@datetime")[0].extract().strip()
        packt_record["book_description"] = response.xpath(
            "//div[@class='book-info-bottom-indetail-text']//p//node()").extract()
        yield packt_record

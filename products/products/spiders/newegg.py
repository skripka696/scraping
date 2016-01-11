import math
from scrapy.spider import Spider
from products.items import SiteProductItem
from scrapy.http import Request
from scrapy.log import INFO
import itertools
import re

is_empty = lambda x, y=None: x[0] if x else y


class NeweggProductSpider(Spider):
    name = 'newegg_products'
    allowed_domains = ['www.newegg.com']

    start_urls = ["http://www.newegg.com/Product/ProductList.aspx" \
                  "?Submit=ENE&DEPA=0&Order=BESTMATCH" \
                  "&Description={search_term}&N=-1&isNodeId=1", ]

    PAGINATE_URL = 'http://www.newegg.com/Product/ProductList.aspx?' \
                   'Submit=ENE&DEPA=0&Order=BESTMATCH&Description={search_term}' \
                   '&N=-1&isNodeId=1&Page={index}'


    def __init__(self,
                 searchterms=None,
                 product_url=None,
                 *args, **kwargs):

        super(NeweggProductSpider, self).__init__(*args, **kwargs)

        self.searchterms = searchterms
        self.product_url = product_url
        self.index = 0

    def start_requests(self):
        """Generate Requests from the SEARCH_URL and the search terms."""

        # scraping by searchterms
        if self.searchterms:
            url = "http://www.newegg.com/Product/ProductList.aspx" \
                  "?Submit=ENE&DEPA=0&Order=BESTMATCH" \
                  "&Description={search_term}&N=-1&isNodeId=1"

            yield Request(url.format(search_term=self.searchterms),
                          callback=self.parse_product_link)
        # scraping by product_url
        if self.product_url:
            yield Request(self.product_url,
                          callback=self.parse)

    def parse(self, response):
        item = SiteProductItem()

        # Parse url
        item['url'] = response.url

        # Parse title
        item['title'] = self.parse_title(response)

        # Set locale
        item['locale'] = 'en_US'

        # Parse brand
        item['brand'] = self.parse_brand(response)

        # Parse model
        item['model'] = self.parse_model(response)

        # Parse image url
        item['image_url'] = self.parse_image_url(response)

        # Parse description
        item['description'] = self.parse_description(response)

        # Parse variants
        # item['variants'] = self.parse_variant(response)

        return item

    def parse_title(self, response):
        title = is_empty(
            response.xpath('//h1/span[@itemprop="name"]/text()').extract())

        if title:
            return title

    def parse_brand(self, response):
        brand = is_empty(response.xpath(
            '//dl/dt[contains(text(), "Brand")]/following-sibling::*/text()').extract())

        if brand:
            return brand

    def parse_model(self, response):
        model = is_empty(response.xpath(
            '//dl/dt[contains(text(), "Model")]/following-sibling::*/text()').extract())

        if model:
            return model

    def parse_image_url(self, response):
        image = is_empty(response.xpath('//div[@class="objImages"]/'
                                        'a[@name="gallery"]/'
                                        'span[@class="mainSlide"]'
                                        '/img/@src').extract())
        if image:
            return image

        return None

    def parse_description(self, response):
        description = response.xpath('//div[@class="grpBullet"]').extract()
        description = [i.strip() for i in description]
        if description:
            return description

    def parse_variant(self, response):
        variants = []

        vars = is_empty(response.xpath(
            '//script[contains(text(), "Biz.Product.GroupItemSwitcher")]').extract())
        try:
            properties_vars = re.findall(r'properties:(\[.*\]\}])', vars)
            availableMap = re.findall(r'availableMap:(\[.*\]\}])', vars)
            if properties_vars:
                data = json.loads(properties_vars[0])
            else:
                return
            price_js = json.loads(availableMap[0])
        except Exception as e:
            print e

        all = list()
        for group in data:
            group_variants = list()
            for prop in group['data']:
                if prop['displayInfo']:
                    group_variants.append([prop['description'], prop['value'], group['name'], group['description']])
            if group_variants:
                all.append(group_variants)
        result = list(itertools.product(*all))

        price_all = list()
        for group in price_js:
            group_variants = list()
            for prop in group['map']:
                group_variants.append(prop['value'])
                group_variants.append(prop['name'])
            group_variants.append(group['info']['price'])
            price_all.append(group_variants)
        for r in result:
            id_result = []
            properties = {}
            variant = {}
            for item in r:
                id_result.append(item[1])
                id_result.append(item[2])
                properties[str(item[3])] = item[0]
            for price_item in price_all:
                rez = list(set(id_result) - set(price_item))
                if not rez:
                    price = price_item[-1]
                    in_stock = True
                    break
                else:
                    price = None
                    in_stock = False

            if price:
                variant['price'] = price
            else:
                variant['price'] = None
            variant['in_stock'] = in_stock
            variant['properties'] = properties
            variants.append(variant)

        return variants

    def _scrape_total_matches(self, response):
        """
        Scraping number of resulted product links
        """
        total_matches = is_empty(
            response.xpath(
                '//div[@class="recordCount"]/span[@id="RecordCount_1"]/text()').extract())
        if total_matches:
            return int(total_matches)
        else:
            return 0

    def parse_product_link(self, response):
        """
        Scraping product links from search page
        """

        links = response.xpath(
            '//div[@class="itemCell itemCell-ProductList itemCell-ProductGridList"]/'
            'div[@class="itemText"]/div/a/@href|//div[contains(@class,"comboCell itemCell")]/div[@class="itemText "]/a/@href'
        ).extract()
        # print response.xpath('//div[contains(@class,"comboCell itemCell")]/div[@class="itemText "]/a/@href').extract()
        if links:
            for link in links:
                yield Request(link,
                              callback=self.parse)
        else:
            self.log("Found no product links in {url}".format(url=response.url),
                     INFO)

        total = self._scrape_total_matches(response)
        size = self._scrape_results_per_page(response)
        pages = int(math.ceil(total/size))
        # print 'total', total, 'size', size, 'pages', pages, 'index', self.index
        self.index += 1

        if self.index != int(pages) + 1:
            yield Request(self.PAGINATE_URL.format(
                search_term=self.searchterms,
                index=self.index,
                meta=response.meta.copy(),),
                callback=self.parse_product_link)

    def _scrape_results_per_page(self, response):
        """
        Number of results on page
        """
        links = response.xpath(
            '//div[@class="itemCell itemCell-ProductList itemCell-ProductGridList"]/'
            'div[@class="itemText"]/div/a/@href'
        ).extract()
        if links:
            per_page = int(len(links))

        if per_page:
            return per_page


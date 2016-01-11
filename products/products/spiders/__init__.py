# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from scrapy.http import Request
from scrapy.spider import Spider

from products.items import SiteProductItem
import urllib


class BaseProductsSpider(Spider):

    def __init__(self,
                 searchterms=None,
                 product_url=None,
                 *args,
                 **kwargs):

        super(BaseProductsSpider, self).__init__(*args, **kwargs)

    def start_request(self):
        """Generate Requests from the SEARCH_URL and the search terms."""

        for st in self.searchterms:
            yield Request(
                self.url_formatter.format(
                    self.SEARCH_URL,
                    search_term=urllib.quote_plus(st.encode('utf-8')),
                ),
                meta={'search_term': st, 'remaining': self.quantity},
            )

        if self.product_url:
            prod = SiteProductItem()
            prod['is_single_result'] = True
            prod['url'] = self.product_url
            prod['search_term'] = ''
            yield Request(self.product_url,
                          self._parse_single_product,
                          meta={'product': prod})


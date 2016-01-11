# -*- coding: utf-8 -*-

from scrapy.item import Item, Field

class SiteProductItem(Item):
    # Search metadata.
    site = Field()  # String.
    search_term = Field()  # String.
    ranking = Field()  # Integer.
    total_matches = Field()  # Integer.
    results_per_page = Field()  # Integer.
    scraped_results_per_page = Field()  # Integer.
    # Indicates whether this Item comes from scraping single product url
    is_single_result = Field()  # Bool

    # Product data.
    title = Field()  # String.
    upc = Field()  # Integer.
    model = Field()  # String, alphanumeric code.
    sku = Field()  # product SKU, if any
    url = Field()  # String, URL.
    image_url = Field()  # String, URL.
    description = Field()  # String with HTML tags.
    brand = Field()  # String.
    price = Field()  # see Price obj
    marketplace = Field()  # see marketplace obj
    locale = Field()  # String.
    # Dict of RelatedProducts. The key is the relation name.
    related_products = Field()
    # Dict of SponsoredLinks. The key is the relation name.
    sponsored_links = Field()
    # Available in-store only
    is_in_store_only = Field()
    # Out of stock
    is_out_of_stock = Field()
    # Feedback from the buyers (with ratings etc.)
    buyer_reviews = Field()  # see BuyerReviews obj

    bestseller_rank = Field()
    variants = Field()

import os
import json
import requests
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ..items import ProductItem
from ..settings import USER_AGENT, BRANDS, STORES


class ProductsSpider(CrawlSpider):
    """
    Spider for crawling through homedepot.com
    It crawls starting from pages specified in start_urls through specific brand pages specified in data.brands
    """

    base_url = "https://www.homedepot.com"

    name = 'products'
    allowed_domains = ['homedepot.com']
    start_urls = [
        f'{base_url}/b/Appliances-Dishwashers/N-5yc1vZc3po',
        f'{base_url}/b/Appliances-Refrigerators/N-5yc1vZc3pi',
        f'{base_url}/b/Furniture-Bedroom-Furniture-Mattresses/N-5yc1vZc7oe'
    ]

    # Rules for crawling are dynamically created from specified brands for each sub department
    rules = (
        Rule(
            LinkExtractor(
                allow=tuple([f"{b['base_url']}/{brand}/" for b in BRANDS.values() for brand in b['brands']])
            ),
            callback="parse_item",
            follow=False),
    )

    result_dir = os.path.join("results")
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)

    def parse_item(self, response):
        """
        Main parsing function. Splits url in order to extract nav_param and sub_department for /model request.
        Then performs the request for each store and extracts products from the response.

        :param response: scrapy.Response object - response of a brand page
        :return: yields a product list
        """
        sub_department = response.url.split("/")[-3].split("-")[-1]
        brand = response.url.split("/")[-2].split("-")[-1]
        nav_param = response.url.split("N-")[-1]

        for store_loc, store_id in STORES.items():
            prdcts = [self.transform_product(prod)
                      for prod in self.fetch_products(nav_param, store_id, sub_department)
                      if prod]

            with open(os.path.join(self.result_dir, f"{store_loc}_{sub_department}_{brand}.json"), "w") as f:
                json.dump([dict(p) for p in prdcts], f)

            yield {'products': prdcts}

    def fetch_products(self, nav_param, store_id, sub_department, page_size=48):
        """
        Fetches products list using /model request. As maximum value for pageSize is 48 request is executed as long as
        resulting list isn't shorter than page_size.

        :param nav_param: str - parameter used for specifying department and brand
        :param store_id: str - id of the store for which to fetch data
        :param sub_department: str - name of the sub_department, possible values: Dishwashers, Refrigerators, Mattresses
        :param page_size: int - number of results; maximum value is 48
        :return: list[dict] - list of products' data
        """
        prdcts, start_index, current_size = list(), 0, page_size
        while current_size >= page_size:
            req = requests.post(
                f'{self.base_url}/product-information/model',
                headers={
                    'user-agent': USER_AGENT,
                    'x-experience-name': 'major-appliances' if sub_department in {"Dishwashers",
                                                                                  "Refrigerators"} else 'hd-home'
                },
                json={
                    "operationName": "searchModel",
                    "query": 'query searchModel($pageSize: Int, $startIndex: Int, $orderBy: ProductSort, $filter: ProductFilter, $storeId: String, $zipCode: String, $skipInstallServices: Boolean = true, $skipSpecificationGroup: Boolean = false, $keyword: String, $navParam: String, $storefilter: StoreFilter = ALL, $channel: Channel = DESKTOP, $additionalSearchParams: AdditionalParams) { searchModel(keyword: $keyword, navParam: $navParam, storefilter: $storefilter, storeId: $storeId, channel: $channel, additionalSearchParams: $additionalSearchParams) { metadata { categoryID analytics { semanticTokens dynamicLCA __typename } canonicalUrl searchRedirect clearAllRefinementsURL contentType cpoData { cpoCount cpoOnly totalCount __typename } isStoreDisplay productCount { inStore __typename } stores { storeId storeName address { postalCode __typename } nearByStores { storeId storeName distance address { postalCode __typename } __typename } __typename } __typename } products(pageSize: $pageSize, startIndex: $startIndex, orderBy: $orderBy, filter: $filter) { identifiers { storeSkuNumber canonicalUrl brandName modelNumber productType productLabel itemId parentId isSuperSku __typename } itemId dataSources availabilityType { discontinued type __typename } badges(storeId: $storeId) { name __typename } details { collection { collectionId name url __typename } __typename } favoriteDetail { count __typename } fulfillment(storeId: $storeId, zipCode: $zipCode) { fulfillmentOptions { type fulfillable services { type locations { inventory { isInStock isLimitedQuantity isOutOfStock isUnavailable quantity maxAllowedBopisQty minAllowedBopisQty __typename } curbsidePickupFlag isBuyInStoreCheckNearBy distance isAnchor locationId state storeName storePhone type __typename } deliveryTimeline deliveryDates { startDate endDate __typename } deliveryCharge dynamicEta { hours minutes __typename } hasFreeShipping freeDeliveryThreshold totalCharge __typename } __typename } anchorStoreStatus anchorStoreStatusType backordered backorderedShipDate bossExcludedShipStates excludedShipStates seasonStatusEligible onlineStoreStatus onlineStoreStatusType __typename } info { isBuryProduct isSponsored isGenericProduct isLiveGoodsProduct sponsoredBeacon { onClickBeacon onViewBeacon __typename } sponsoredMetadata { campaignId placementId slotId __typename } globalCustomConfigurator { customExperience __typename } returnable hidePrice productSubType { name link __typename } categoryHierarchy ecoRebate quantityLimit sskMin sskMax unitOfMeasureCoverage wasMaxPriceRange wasMinPriceRange swatches { isSelected itemId label swatchImgUrl url value __typename } totalNumberOfOptions __typename } installServices @skip(if: $skipInstallServices) { scheduleAMeasure __typename } media { images { url type subType sizes __typename } __typename } reviews { ratingsReviews { averageRating totalReviews __typename } __typename } pricing(storeId: $storeId) { value alternatePriceDisplay alternate { bulk { pricePerUnit thresholdQuantity value __typename } unit { caseUnitOfMeasure unitsOriginalPrice unitsPerCase value __typename } __typename } original mapAboveOriginalPrice message promotion { type description { shortDesc longDesc __typename } dollarOff percentageOff savingsCenter savingsCenterPromos specialBuySavings specialBuyDollarOff specialBuyPercentageOff dates { start end __typename } experienceTag __typename } specialBuy unitOfMeasure __typename } keyProductFeatures { keyProductFeaturesItems { features { name refinementId refinementUrl value __typename } __typename } __typename } specificationGroup @skip(if: $skipSpecificationGroup) { specifications { specName specValue __typename } specTitle __typename } sizeAndFitDetail { attributeGroups { attributes { attributeName dimensions __typename } dimensionLabel productType __typename } __typename } __typename } searchReport { totalProducts didYouMean correctedKeyword keyword pageSize searchUrl sortBy sortOrder startIndex __typename } relatedResults { universalSearch { title __typename } relatedServices { label __typename } visualNavs { label imageId webUrl categoryId imageURL __typename } visualNavContainsEvents relatedKeywords { keyword __typename } __typename } taxonomy { brandLinkUrl breadCrumbs { browseUrl creativeIconUrl deselectUrl dimensionId dimensionName label refinementKey url __typename } __typename } templates partialTemplates dimensions { label refinements { refinementKey label recordCount selected imgUrl url nestedRefinements { label url recordCount refinementKey __typename } __typename } collapse dimensionId isVisualNav nestedRefinementsLimit visualNavSequence __typename } orangeGraph { universalSearchArray { pods { title description imageUrl link __typename } info { title __typename } __typename } __typename } id appliedDimensions { label refinements { label refinementKey url __typename } __typename } __typename }}',
                    "variables": {
                        "navParam": nav_param,
                        "storeId": store_id,
                        "pageSize": page_size,
                        "startIndex": start_index
                    }
                }
            )
            current_products = req.json()['data']['searchModel']['products']
            current_size = len(current_products)
            prdcts.extend(current_products)
            start_index += page_size
        return prdcts

    @staticmethod
    def transform_product(product_data):
        """
        Extracts specific data from API result and creates ProductItem object with it.

        :param product_data: dict - product data fetched from API (/model)
        :return: ProductItem - object created with extracted data
        """
        product = ProductItem()

        product['url'] = product_data['identifiers']['canonicalUrl'],
        product['brand'] = product_data['identifiers']['brandName'],
        product['model_number'] = product_data['identifiers']['modelNumber'],
        product['product_type'] = product_data['identifiers']['productType'],
        product['product_label'] = product_data['identifiers']['productLabel'],
        product['item_id'] = int(product_data['itemId']),
        product['availability'] = None if product_data['availabilityType']['discontinued'] else \
                                      product_data['availabilityType']['type'],
        product['average_rating'] = float(product_data['reviews']['ratingsReviews']['averageRating']),
        product['reviews_number'] = int(product_data['reviews']['ratingsReviews']['totalReviews']),
        product['price'] = float(product_data['pricing']['value']) if product_data['pricing'] else None,
        product['features'] = {"_".join(f['name'].lower().split()): f['value'] for f in
                               product_data['keyProductFeatures']['keyProductFeaturesItems'][0]['features']}

        return product

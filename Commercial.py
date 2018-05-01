import requests
# import certifi
from bs4 import BeautifulSoup, SoupStrainer
import json
import logging


logger = logging.getLogger(__name__)

class CommListings:
    host_name = 'www.cityfeet.com'
    path = '/partner/cleveland'
    #logger = logging.getLogger(__name__)

    def __init__(self, city_name, proxy):
        self.city = city_name
        #self.logger = logging.getLogger(__name__)
        if proxy == "No":
            self.proxies = {}
        else:
            self.proxies = {
                'http': 'http://127.0.0.1:8888'}
            # For Fiddler HTTP debugger when enabled
        self.cookies = []
        lat_lng = self.geocode()
        # Get lat/lng values from the same mapquest api
        # used by the target site
        self.lat = lat_lng['lat']
        self.lng = lat_lng['lng']
        self.combined_prop_list = []

    def init_search(self):
        # method that queries the real estate listings and loops
        # through pages of results
        resp = requests.get('http://' + self.host_name + self.path)
        logger.debug('response headers:' + str(resp.headers))
        cookies = resp.cookies

        headers = {
            'Host':'www.cityfeet.com',
            'Pragma':'no-cache',
            'Referer':'http://www.cityfeet.com/partner/cleveland',
            'Upgrade-Insecure-Requests':'1',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'en-US,en;q=0.9',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'DNT':'1'
        }
        resp = requests.get('http://' + self.host_name
                          + '/cont/cleveland/brook-park-oh/commercial-real-estate-for-lease?l=3-1413&partner=y',
                            cookies=cookies, headers=headers)
        logger.debug('response headers: ' + str(resp.headers))
        # logger.debug(str(resp.text))
        cookies = resp.cookies
        headers['Referer'] = ('http://www.cityfeet.com/cont/cleveland/brook-park-oh/' +
                              'commercial-real-estate-for-lease?l=3-1413&partner=y')
        headers['Content-Type'] = 'application/json'
        headers['X-Requested-With'] = 'XMLHttpRequest'
        payload = '{"location":{"name":"Brook Park, OH","bb":[41.386401,-81.885798,41.421759,-81.780314],"lat":41.40408,"lng":-81.833056,"state":"OH","city":"Brook Park","id":"3-1413","level":3},"lt":1,"pt":0,"sort":null,"partnerId":"cleveland","lc":[],"mode":2,"portfolio":-1,"tt":0,"ignoreLocation":false,"rent":{"type":1,"basis":0},"term":"Brook Park, OH","PageNum":1,"state":null}'
        resp = requests.post('http://' + self.host_name + '/cont/api/search/listings-classic',
                             cookies=cookies, headers=headers, data=payload)
        logger.debug('response headers: ' + str(resp.headers))

        resptext = json.JSONDecoder().decode(resp.text)
        page_num = resptext['PageNum']
        page_size = resptext['PageSize']
        total = resptext['Total']
        if page_size > total:
            print('One page - ok')
        # add multi-page handling, like for the res listings

        lease_list = resptext['Data']
        logger.debug(str(lease_list))

        headers2 = {
            'Host': 'www.cityfeet.com',
            'Pragma': 'no-cache',
            'Referer': 'http://www.cityfeet.com/partner/cleveland',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'DNT': '1'
        }

        resp = requests.get('http://' + self.host_name
                            + '/cont/cleveland/brook-park-oh/commercial-property-for-sale?l=3-1413&partner=y',
                            cookies=cookies, headers = headers2)
        cookies = resp.cookies
        headers2['Referer'] = ('http://www.cityfeet.com/cont/cleveland/brook-park-oh/' +
                              'commercial-real-estate-for-lease?l=3-1413&partner=y')
        headers2['Content-Type'] = 'application/json'
        headers2['X-Requested-With'] = 'XMLHttpRequest'
        payload = '{"location":{"name":"Brook Park, OH","bb":[41.386401,-81.885798,41.421759,-81.780314],"lat":41.40408,"lng":-81.833056,"state":"OH","city":"Brook Park","id":"3-1413","level":3},"lt":2,"pt":0,"sort":null,"partnerId":"cleveland","lc":[],"mode":2,"portfolio":-1,"tt":0,"ignoreLocation":false,"rent":{"type":1,"basis":0},"term":"Brook Park, OH","PageNum":1,"state":null}'
        resp = requests.post('http://' + self.host_name + '/cont/api/search/listings-classic',
                             cookies=cookies, headers=headers2, data=payload)
        logger.debug('response headers: ' + str(resp.headers))

        resptext = json.JSONDecoder().decode(resp.text)
        page_num = resptext['PageNum']
        page_size = resptext['PageSize']
        total = resptext['Total']
        if page_size > total:
            print('One page - ok')
        # add multi-page handling, like for the res listings
        sale_list = resptext['Data']
        logger.debug(str(sale_list))

        self.combined_prop_list = lease_list + sale_list
        # Now parse the JSON. Use Total to tell if paged (will be total result size).
        # If Total is greater than PageSize there will be more than one page.

        return self.combined_prop_list

    def process_addresses(self, prop_list):
        processed = []
        for p in prop_list:
                prop = {}
                prop['address'] = p['Location']['ListingAddress']['Address']
                if 'LeaseListingTerm' in p['Offer']['$type']:
                    prop['type'] = 'lease'
                elif 'SaleListingTerm' in p['Offer']['$type']:
                    prop['type'] = 'sale'
                prop['link'] = 'http://' + self.host_name + p['Url']
                prop['headline'] = p['Offer']['Headline']
                prop['pitch'] = p['Offer']['SalesPitch']
                prop['details'] = str(p)
                processed.append(prop)
        self.combined_prop_list = processed
        return self.combined_prop_list

    def geocode(self):
        # cleveland.com uses the mapquestapi for this, so I do too
        # https should be secured (certificate verify) below, but
        # having trouble validating cert - I *think* has something
        # to do w/ Baker network https interception config
        # but not sure
        key = 'RjBzYpkkF3LrEVpJnVEy0G2q7rruYZgA'
        qparams = {
            'key': key,
            'thumbMaps': 'false',
            'maxResults': '1',
            'boundingBox': '41.59080,-82.92480,40.19566,-80.92529',
            'location': self.city
        }
        resp = requests.get("https://" + "www.mapquestapi.com/geocoding/v1/address",
                            params=qparams, proxies=self.proxies, verify='certs/BHcerts.cer')

        j_resp = json.loads(resp.text)
        locs = j_resp['results'][0]['locations']
        lat_lng = locs[0]['latLng']
        logger.info('Geocoding acquired')
        return lat_lng

    def run_and_report(self):
        all_properties = self.process_addresses(self.init_search())

        return all_properties

# logging.basicConfig(level=logging.INFO)
# #
# test = CommListings("Brook Park", "No")
# # #print(test.proxies)
# #results = test.init_search()
# results = test.run_and_report()
# logger.info(results)
#results = test.add_addresses(results)
#results = test.run_and_report()
#print(results)
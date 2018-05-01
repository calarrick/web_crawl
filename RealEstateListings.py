import requests
# import certifi
from bs4 import BeautifulSoup, SoupStrainer
import json
import logging

logging = logging.getLogger(__name__)

class REListings:
    host_name = 'realestate.cleveland.com'
    path = '/homes-for-sale'
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
        logging.debug('response headers:' + str(resp.headers))
        cookies = resp.cookies
        req_from = 0
        req_size = 0
        # 'from' is the starting number of the paged results, 'size' is the number included
        # in that page
        just_listed = 1
        # this will store reported count of 'newly listed' properties per our request
        # Is written to stop the query at end of the page that includes the last 'just_listed' result
        # so overruns it a bit by design.
        # If this is a problem the solution would be to implement counter logic within the pages and
        # either flag or omit the last few results that are outside the 'just_listed' count
        page = 0

        # Repeats requests for the ids and the result batches, until we are past the number of 'new listings'
        while just_listed > req_from + req_size:
            page = page + 1
            params1 = {
                'category': 'elastic',
                'tp': 'RealEstateCore2007',
                'name': 'controller',
                'affiliate': 'RE_cleve',
                'just_listed': 'on',
                'location': self.city,
                'geo_city': self.city,
                'geo_st': 'OH',
                'geo_quality': 'CITY',
                'distance': '10',
                'lat': self.lat,
                'lng': self.lng,
                'list_type': 'resale'
            }
            if page > 1:
                params1['page'] = page
            headers = {
                'Host': 'realestate.cleveland.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'
                + 'AppleWebKit/5537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.8',
                'Proxy-Connection': 'keep-alive',
                # 'Referer':'http://realestate.cleveland.com/?classification=real+estate&temp_type='
                # + 'browse&finder=buy&list_type=resale&tp=RE_cleve&property=cleveland.com&location='
                # + self.city + '&lat=41.366288&lng=-81.853772&geo_quality=CITY&geo_city='
                # + self.city + '&geo_st=OH'
                # + '&just_listed=on',
                'X-Requested-With': 'XMLHttpRequest'
            }
            # Each batch of results requires two GET requests. The first one gets result
            # information as a large JSON object that includes result IDs along with much
            # else about the request, response, state
            resp = requests.get('http://' + self.host_name + '/RealEstate', params = params1,
                                cookies = cookies, headers = headers, proxies=self.proxies)
            cookies = resp.cookies
            # resp.text here is JSON that includes result ids as '_id':'#######'
            logging.debug(resp.text)
            parsed = json.loads(resp.text)
            logging.info('Query ids of next page of results...')
            logging.debug(parsed)
            request = parsed['_discovery']['request']
            req_from = request['from']
            req_size = request['size']
            resp = parsed['_discovery']['response']
            hits = resp['hits']
            total = hits['total']
            just_listed = \
                resp['aggregations']['all_listings']['filtered_results']\
            ['filtered_justlisted']['num_justlisted']['doc_count']
            # Count of results that I want is buried pretty deep in JSON object
            props = hits['hits']
            logging.info('ids for ' + str(req_from) + ' to ' + str(req_size + req_from)
                         + ' of ' + str(just_listed) + ' (' + str(total) + ')')
            # We should have narrowed down to list of next ten results here

            # Preparing parameters for the second request for this page, which will retrieve the actual
            # listing content.
            prop_id_list = []
            t_list = []
            for prop in props:
                _id = prop['_id']
                prop_id_list.append(_id)
                t_list.append('T')
                # pulls ID from response JSON. Not sure why it uses the list of 'T's... perhaps
                # for string formatting/substitution on server side?
            params2 = {
                'category': 'transparensee',
                'tp': 'RealEstateCore2007',
                'aff_tp': 'RE_cleve',
                'finder': 'buy',
                'name': 'results',
                'itemIds': prop_id_list,
                'exactMatches': t_list,
                'exactSize': just_listed,
                'totalSize': total,
                'property': 'cleveland.com'
            }
            if page > 1:
                params2['tps_page'] = page
            # this second GET request sends the server the next batch of result IDs in its params,
            # listing info is returned
            resp = requests.get('http://' + self.host_name, cookies=cookies, params=params2,
                                headers=headers, proxies=self.proxies)
            logging.debug(resp.headers)
            logging.info('http response: ' + str(resp.status_code))
            logging.info('Retrieving actual contents of listings...')
            cookies = resp.cookies
            self.cookies = cookies
            listing_chunks = resp.text.partition('<!-- START: Listed Row -->')
            listing_text = listing_chunks[2]
            listing_chunks = listing_text.rpartition('<!-- Start: Paginator Top -->')
            listing_text = listing_chunks[0]
            page_props_listings = listing_text.split('<!-- START: Listed Row -->')
            logging.debug(page_props_listings)
            properties = []
            whole_soup = BeautifulSoup(listing_text, 'lxml')
            list_num = 0
            for prop in page_props_listings:
                soup = BeautifulSoup(prop, 'lxml')
                list_num = list_num + 1
                prop = {'list_num': list_num}
                address = soup.find('a', class_='addy')
                if address is not None:
                    prop['address'] = address.string
                    prop['url'] = address.get('href')
                new_listing = soup.find('span', class_='new_listing')
                if new_listing is not None:
                    prop['new_listing'] = new_listing.string
                reglisting = soup.find('div', class_="reglisting ")
                if reglisting is not None:
                    next_listing = reglisting.find('div')
                    det_link = next_listing.find('a')
                    prop['reglisting_title'] = det_link['title']
                    prop['reglisting_url'] = det_link['href']
                listing_info = soup.find('div', class_='listingInfo')
                if listing_info is not None:
                    prop['list_info_link'] = listing_info.find('a')['href']
                    prop['list_info_city'] = listing_info.find('span', class_='city').string
                    prop['list_info_zip'] = listing_info.find('span', class_='zip').string
                    prop['list_info_price'] = listing_info.find('span', class_='price').string
                    source = soup.find('div', class_='realtorInfo')
                    if source is not None:
                        realtor_url = source.find('a')
                        if realtor_url is not None:
                            prop['realtor_url'] = realtor_url['href']
                prop['popup_teaser'] = whole_soup.find('div', id='data' + str(list_num)).string
                properties.append(prop)
                # add this property to the list kept for this response

            self.combined_prop_list.extend(properties)
            # add properties from this paged response to the overall list
            logging.info('Adding page ' + str(page) + ' of results to list')
            logging.info('Results ' + str(req_from) + ' to ' + str(req_size + req_from)
                         + ' of ' + str(just_listed) + ' (' + str(total) + ')')
        return self.combined_prop_list

    def add_addresses(self, prop_list):
        # attempts to add an address field for any properties
        # from which the basic info on the results page didn't have it
        props_length = len(prop_list)
        if prop_list is None or props_length == 0:
            prop_list = self.combined_prop_list
        # Loop through listings. Replace those without addresses with
        # the new entry that has fields from the 'detail' query
        for i, prop in enumerate(prop_list):
            try:
                prop['address']
            except KeyError as key_e:
                # missing address. will have to request the
                # details page for this property
                try:
                    prop_list[i] = self.query_for_details(prop, i, props_length)
                except ConnectionError:
                    # needs testing
                    prop_list.append(prop_list[i])
                    del(prop_list[i])
                logging.debug(str(key_e) + ' Need to fetch address from detail query')
        return prop_list

    def query_for_details(self, prop, i, props_length):
        # Several fields might have the URL query strings needed
        # to request details on this property.
        # Find one, then make request and update the the prop dict with
        # new address info.
        try:
            url = prop['reglisting_url']
        except KeyError:
            try:
                url = prop['list_info_link']
            except KeyError:
                try:
                    url = prop['realtor_url']
                except KeyError as key_e:
                    url = ''
                    logging.error(str(key_e) + ': ' + str(i) + ': no url found', exc_info=True)
        logging.info('Extracted url query from listing ' + str(i) + ' of ' + str(props_length)
                     + ' (' + str(prop['list_num']) + '): ' + url)
        if url == '':
            prop['address'] = ''
        elif url[0:4] == 'http':
            # Spotting it here avoids extra query that will 404 anyway
            prop['address'] = ''
            logging.warning('Link info not query/param string. Skipping ' + url)
        else:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.8',
                'Host': 'realestate.cleveland.com',
                'Proxy-Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                + 'Chrome/60.0.3112.90 Safari/537.36'
            }
            resp = requests.get('http://' + self.host_name + '/' + url, cookies=self.cookies,
                                headers=headers, proxies=self.proxies)
            logging.info('http response: ' + str(resp.status_code))
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logging.error('Failed to connect with URL for detail record: ' + str(err), exc_info=True)
                prop['address'] = ''
            else:
                data_set = SoupStrainer('div', class_='m_dataset')
                parse = BeautifulSoup(resp.text, 'lxml', parse_only=data_set)
                prop['address'] = parse.find('p', class_='name').string
                try:
                    home_details = ''
                    dets = parse.find('div', class_='data').stripped_strings
                    for i, desc in enumerate(dets):
                        logging.debug(desc)
                        home_details = home_details + desc
                        if i % 2 == 1:
                            home_details = home_details + ' '
                    prop['home_details'] = home_details
                except AttributeError as err:
                    prop['home_details'] = ''
                    logging.error('Unable to process home details' + str(err), exc_info=True)
                prop['city_zip'] = parse.find('p', class_='address').string
                prop['listed'] = parse.find('span', class_='value').string
                prop['url'] = url
                prop['detail_url'] = self.host_name + '/' + url
        return prop

    def geocode(self):
        # cleveland.com uses the mapquestapi for this, so I do too
        # https should be secured (certificate verify) below, but
        # having trouble validating cert - I *think* has something
        # to do w/ Baker network https interception config
        # but not sure
        # am now verifying a copy of the Baker internal CA cert

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

        # resp = requests.get("https://" + "www.mapquestapi.com/geocoding/v1/address",
        #                     params=qparams, proxies=self.proxies, verify=False)

        j_resp = json.loads(resp.text)
        locs = j_resp['results'][0]['locations']
        lat_lng = locs[0]['latLng']
        logging.info('Geocoding acquired')
        return lat_lng

    def raw_file(self, res_list):
        with open('workfile' + self.city, 'w') as f:
            f.write(str(res_list))
        logging.info('output written to workfile')

    def run_and_report(self):
        all_properties = self.add_addresses(self.init_search())
        self.raw_file(all_properties)
        logging.debug(all_properties)
        return all_properties

#logging.basicConfig(level=logging.INFO)
#
#test = REListings("Berea", "No")
# #print(test.proxies)
#results = test.init_search()
#results = test.add_addresses(results)
#results = test.run_and_report()
#print(results)



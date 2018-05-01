import requests
from bs4 import BeautifulSoup, SoupStrainer
import logging

logging = logging.getLogger(__name__)


class CourtForeclosureSearch:
    
    def __init__(self, city, proxy):
        self.cityName = city
        if proxy == "No":
            self.proxies = {}
        else:
            self.proxies = {'https': 'https://127.0.0.1:8888'}

    def get_data(self):

        cCountyHost = "cpdocket.cp.cuyahogacounty.us/"
        searchPage = "Search.aspx"
        headers = {'Accept-Encoding': 'gzip, deflate',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                   #           'Proxy-Connection':'keep-alive',
                   'Upgrade-Insecure-Requests': '1',
                   'Host': 'cpdocket.cp.cuyahogacounty.us',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
                   }
        resp = requests.get("https://" + cCountyHost, headers=headers, proxies=self.proxies)
        # grab session cookie
        cookies = resp.cookies
        for c in resp.cookies:
            logging.debug(c)
        # need to grab viewstate and related
        formFields = SoupStrainer("input")
        parsed = BeautifulSoup(resp.text, "lxml", parse_only=formFields)
        # viewstate = parsed.find(id="__VIEWSTATE")
        vState = parsed.find(id="__VIEWSTATE").get("value")
        # print(vState)
        vStateGen = parsed.find(id="__VIEWSTATEGENERATOR").get("value")
        eventVal = parsed.find(id="__EVENTVALIDATION").get("value")
        # print(eventVal)
        # print(resp.text)
    
        formData = {'ctl00$SheetContentPlaceHolder$btnYes': 'Yes',
                    '__VIEWSTATE': vState,
                    '__VIEWSTATEGENERATOR': vStateGen,
                    '__EVENTVALIDATION': eventVal,
                    '__EVENTARGUMENT': '',
                    '__EVENTTARGET': ''
    
                    }
        headers['Referer'] = 'https://cpdocket.cp.cuyahogacounty.us/'
        headers['Origin'] = 'https://cpdocket.cp.cuyahogacounty.us'
        headers['Host'] = 'cpdocket.cp.cuyahogacounty.us'
        # headers['Proxy-Connection'] = 'keep-alive'
        # omit, Requests auto-handles content-type header ok for this
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Cache-Control'] = 'max-age=0'
        # del headers['Upgrade-Insecure-Requests']
    

        resp = requests.post("https://" + cCountyHost, data=formData, headers=headers, cookies=cookies)
        # emulates post w tos button click
        # print(resp.status_code)
        # print(resp.request.headers)
        del headers['Content-Type']
        logging.info(resp.status_code)
        logging.debug(resp.headers)
        logging.debug(resp.text)
    
        resp = requests.get("https://" + cCountyHost + searchPage, headers=headers, cookies=cookies)
    
        # brings the main search page
        # good so far
        # print(resp.text)
        logging.info(resp.status_code)
        logging.info('docket search page')
        logging.debug(resp.headers)
        logging.debug(resp.request.headers)

        formFields = SoupStrainer("input")
        parsed = BeautifulSoup(resp.text, "lxml", parse_only=formFields)
        # viewstate = parsed.find(id="__VIEWSTATE")
        vState = parsed.find(id="__VIEWSTATE").get("value")
        vStateGen = parsed.find(id="__VIEWSTATEGENERATOR").get("value")
        eventVal = parsed.find(id="__EVENTVALIDATION").get("value")

        # print(eventVal)
    
        formData = {
            'ctl00$ScriptManager1':
                'ctl00$SheetContentPlaceHolder$UpdatePanel1|ctl00$SheetContentPlaceHolder$rbCivilForeclosure',
            '__VIEWSTATE': vState,
            '__VIEWSTATEGENERATOR': vStateGen,
            '__EVENTVALIDATION': eventVal,
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': 'ctl00$SheetContentPlaceHolder$rbCivilForeclosure',
            'ctl00$SheetContentPlaceHolder$rbSearches': 'forcl',
            '__ASYNCPOST': 'true',
            '__LASTFOCUS': ''
        }
        headers['Origin'] = 'https://cpdocket.cp.cuyahogacounty.us'
        headers['Referer'] = 'https://cpdocket.cp.cuyahogacounty.us/Search.aspx'
        headers['X-MicrosoftAjax'] = 'Delta=true'
        headers['X-Requested-With'] = 'XMLHttpRequest'
        headers['Cache-Control'] = 'no-cache'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    
        # headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    
        # select foreclosure button
    
        resp = requests.post("https://" + cCountyHost + searchPage, data=formData, headers=headers, cookies=cookies)
        logging.info(resp.request.headers)
        # print(resp.text)
        # no html 'soup' parsing this time, 'oddball' formatting of these asp replacement panel responses calls
        # for different approach,
        # splitting tokens on the pipe character delimiter
        aspAjaxResponse = resp.text.split('|')
        # print(aspAjaxResponse.index('__VIEWSTATE'))
        vState = aspAjaxResponse[aspAjaxResponse.index('__VIEWSTATE') + 1]
        # print(vState)
        eventVal = aspAjaxResponse[aspAjaxResponse.index('__EVENTVALIDATION') + 1]
    
        formData = {
            'ctl00$ScriptManager1':
                'ctl00$SheetContentPlaceHolder$UpdatePanel1|ctl00$SheetContentPlaceHolder$foreclosureSearch$btnSubmit',
            'ctl00$SheetContentPlaceHolder$rbSearches': 'forcl',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtParcelNbr': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$meeParcelNbr_ClientState': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtStreetNbr': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$ddlCaseYear': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtCaseSequence': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtStreetName': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$ddlFilingType': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtCity': self.cityName,
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtFromDate': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$FRMaskedEditExtender_ClientState': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtToDate': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$TOMaskedEditExtender_ClientState': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$txtZip': '',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$meeZip_ClientState': '',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': vState,
            '__VIEWSTATEGENERATOR': vStateGen,
            '__EVENTVALIDATION': eventVal,
            '__ASYNCPOST': 'true',
            'ctl00$SheetContentPlaceHolder$foreclosureSearch$btnSubmit': 'Submit'}
    
        headers['Origin'] = 'https://cpdocket.cp.cuyahogacounty.us'
        headers['Referer'] = 'https://cpdocket.cp.cuyahogacounty.us/Search.aspx'
        headers['X-MicrosoftAjax'] = 'Delta=true'
        headers['X-Requested-With'] = 'XMLHttpRequest'
    
        resp = requests.post("https://" + cCountyHost + searchPage, data=formData, headers=headers, cookies=cookies)
    
        logging.info(resp.status_code)
        logging.debug(resp.request.headers)
        # print(resp.text)
    
        del headers['X-MicrosoftAjax']
        del headers['X-Requested-With']
    
        resp = requests.get("https://" + cCountyHost + "ForeclosureSearchResults.aspx", headers=headers, cookies=cookies)
        resultsRaw = resp.text
        # print(resultsRaw)
        # 
        #with open('rawForcResultest', 'w') as f:
        #     f.write(resultsRaw)
        return resultsRaw

    def zipClean(self, rawzip):
        return rawzip[0:5]

    def streetNum(self, address):
        sp = address.find(' ')
        maybe = address[0:sp]
        if maybe.isdigit():
            return maybe
        else:
            return ''

    def streetName(self, address):
        return address.lstrip('0123456789 ')

    def extractAddresses(self, resultsRaw):
        strainer = SoupStrainer(id = "SheetContentPlaceHolder_ctl00_gvForeclosureResults")
        soup = BeautifulSoup(resultsRaw, "lxml", parse_only=strainer)
        #table = soup.find(id = "SheetContentPlaceHolder_ctl00_gvForeclosureResults")
        logging.debug(soup)
        entries = soup.find_all('tr')
        logging.debug(entries)
        addressList = []

        for e in entries:
            chunks = e.find_all('td')
            address = {}
            #chunks = BeautifulSoup(chunks, "lxml")
            if len(chunks) > 7:
                address["defendant"] = str(chunks[0].string)
                address["address"] = str(chunks[1].string)
                address["streetNum"] = self.streetNum(str(chunks[1].string))
                address["streetName"] = self.streetName(str(chunks[1].string))
                address["city"] = str(chunks[2].string)
                address["zip"] = self.zipClean(str(chunks[3].string))
                address["case number"] = str(chunks[4].a.string)
                address["parcel"] = str(chunks[5].string)
                address["active"] = str(chunks[6].string)
                address["filed"] = str(chunks[7].string)
                addressList.append(address)
                #print(address)
                #print(type(address["city"]))
                #print(chunks)

        return addressList

    def run_and_report(self):
        return self.extractAddresses(self.get_data())

# newRequest = CourtForeclosureSearch("Berea", "yes")
# result = newRequest.getData
# newRequest.extractAddresses(result)


# with open('rawForcResultest', 'r') as f:
#     resultsRaw = f.read()
#
# req = CourtForeclosureSearch("Berea", "no")
# addressList = CourtForeclosureSearch.extractAddresses(req, resultsRaw)
# print(addressList)

# query = CourtForeclosureSearch('Berea','yes')
# print(query.getData())
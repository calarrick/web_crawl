import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import urllib
from datetime import date
import logging

logging = logging.getLogger(__name__)

class SheriffForeclosureSearch:
    # logger = logging.getLogger(__name__)
    def __init__(self, city, proxy):
        self.cityName = city
        if proxy == "No":
            self.proxies = {}
        else:
            self.proxies = {
                'http': 'http://127.0.0.1:8888'}
        self.start_date = ''
        self.end_date = ''
        self.address_list = []
        self.smMain = ""
        self.result_list = []

    def get_data(self, start_date, end_date):

        # This and the (related) court docket site ultimately produce
        # all of the results in one page. But getting to them requires
        # emulating several GET and POST queries, passing aspx
        # VIEWSTATE, etc., back and forth
        # So this resulting method is basically just a linear
        # recitation of how to do enough to emulate the client-side of the
        # browser navigation path to get these results
        self.start_date = start_date
        self.end_date = end_date

        host = "cpdocket.cp.cuyahogacounty.us/"
        path = "SheriffSearch/"

        headers = {'Accept-Encoding': 'gzip, deflate',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                   #           'Proxy-Connection':'keep-alive',
                   'Upgrade-Insecure-Requests': '1',
                   'Host': 'cpdocket.cp.cuyahogacounty.us',
                   'Referer':'http://sheriff.cuyahogacounty.us/en-US/Foreclosure-Sales.aspx',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
                   }

#initial GET
        resp = requests.get("https://" + host + path, headers=headers, proxies=self.proxies)
        # grab session cookie
        cookies = resp.cookies
        for c in resp.cookies:
            logging.debug(c)
        # need to grab viewstate and related
        logging.info(resp.status_code)
        logging.debug(resp.text)

        form_fields = SoupStrainer("input")
        parsed = BeautifulSoup(resp.text, "lxml", parse_only=form_fields)
        vState = parsed.find(id="__VIEWSTATE").get("value")
        vStateGen = parsed.find(id="__VIEWSTATEGENERATOR").get("value")
        eventVal = parsed.find(id="__EVENTVALIDATION").get("value")

        scriptFields = SoupStrainer("script")
        parsed = BeautifulSoup(resp.text, "lxml", parse_only=scriptFields)
        rawFieldText = str(parsed.find(src=re.compile('TSM_Hidden')))
        field_text_split = rawFieldText.rpartition('_TSM_CombinedScripts_=')
        q_string_contents = field_text_split[2]
        logging.debug(rawFieldText)
        logging.debug(q_string_contents)
        field_text_split = q_string_contents.partition('"')
        q_string_contents = field_text_split[0]
        #string contents including key values, in url-encoded form
        logging.debug(q_string_contents)
        # 'unquote' replaces url encoded %xx escapes to single-character equivalent and plusses to spaces
        self.smMain = urllib.parse.unquote_plus(q_string_contents)
        logging.info(vState)
#building POST request on 'City' click button
        formData = {
            'ctl00$smMain': 'ctl00$SheetContentPlaceHolder$c_search1$updatePanel '
                            + '| ctl00$SheetContentPlaceHolder$c_search1$btnSearch',
            'smMain_HiddenField':self.smMain,
            '__LASTFOCUS': '',
            '__EVENTTARGET': 'ctl00$SheetContentPlaceHolder$c_search1$rblSrchOptions$4',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': vState,
            '__VIEWSTATEGENERATOR': vStateGen,
            '__EVENTVALIDATION': eventVal,
            'ctl00$SheetContentPlaceHolder$c_search1$ddlSaleDate':'',
            'ctl00$SheetContentPlaceHolder$c_search1$rblSrchOptions':'City',
            'ctl00$SheetContentPlaceHolder$c_search1$SrchSearchString':'',
            'ctl00$SheetContentPlaceHolder$c_search1$TBWE1_ClientState':'',
            'ctl00$SheetContentPlaceHolder$c_search1$SearchStringDateFrom':start_date,
            'ctl00$SheetContentPlaceHolder$c_search1$FromMaskedEditExtender_ClientState':'',
            'ctl00$SheetContentPlaceHolder$c_search1$SearchStringDateTo':end_date,
            'ctl00$SheetContentPlaceHolder$c_search1$TOMaskedEditExtender_ClientState':'',
            '__ASYNCPOST':'true'
        }

        headers['Referer'] = 'https://cpdocket.cp.cuyahogacounty.us/SheriffSearch/'
        headers['X-MicrosoftAjax'] = 'Delta=true'
        headers['X-Requested-With'] = 'XMLHttpRequest'

        logging.info(headers)

#post to set 'City' search criterion
        resp = requests.post("https://" + host + path, data=formData, headers=headers, cookies=cookies)
        logging.info(resp.status_code)
        logging.debug(resp.request.headers)
        logging.debug(resp.text)
#prep to post form filled in

        # will need to parse hidden field data
        # splitting tokens on the pipe character delimiter
        aspAjaxResponse = resp.text.split('|')
        logging.debug(aspAjaxResponse)
        vState = aspAjaxResponse[aspAjaxResponse.index('__VIEWSTATE') + 1]
        eventVal = aspAjaxResponse[aspAjaxResponse.index('__EVENTVALIDATION') + 1]
        eventTarget = aspAjaxResponse[aspAjaxResponse.index('__EVENTTARGET') + 1]
        vStateGen = aspAjaxResponse[aspAjaxResponse.index('__VIEWSTATEGENERATOR') + 1]

        formData['__VIEWSTATE'] = vState
        formData['__EVENTVALIDATION'] = eventVal
        formData['__EVENTTARGET'] = eventTarget
        formData['__VIEWSTATEGENERATOR'] = vStateGen


        formData['ctl00$SheetContentPlaceHolder$c_search1$SrchSearchString'] = self.cityName
        formData['ctl00$SheetContentPlaceHolder$c_search1$btnSearch'] = 'Start Search'
        formData['smMain_HiddenField'] = self.smMain + ';'

        resp = requests.post("https://" + host + path, data=formData, headers=headers, cookies=cookies)
        logging.info(resp.status_code)
        logging.debug(resp.request.headers)
        logging.debug(resp.text)

        payload = {'q':'searchType=City&searchString=' + self.cityName.upper() + '&foreclosureType=&dateFrom='
                       + start_date + ' 12:00:00 AM&dateTo=' + end_date + ' 11:59:59 PM'}
        resp = requests.get("https://" + host + path + "results.aspx", params=payload, cookies=cookies)
# resp here is first page of results
        #print(resp.text)
        formFields = SoupStrainer("input")
        parsed = BeautifulSoup(resp.text, "lxml", parse_only=formFields)
        # viewstate = parsed.find(id="__VIEWSTATE")
        vState = parsed.find(id="__VIEWSTATE").get("value")
        # print(vState)
        vStateGen = parsed.find(id="__VIEWSTATEGENERATOR").get("value")
        eventVal = parsed.find(id="__EVENTVALIDATION").get("value")

# create structure to hold results
        result_list = []

#check pages
        # get pagination info
        parsed = BeautifulSoup(resp.text, 'lxml')
        pagination_grid = parsed.find('div', class_='datagridpager')
        page_display = str(pagination_grid.find('span', class_='pagerLabel').string)
        #print(page_display)
        start_end = page_display.partition('/')
        start = 1
        end = 1
        if len(start_end) > 2:
            try:
                start = int(start_end[0])
                end = int(start_end[2])
            except ValueError as e:
                start = 1
                end = 1
                logging.warning(e)
        current = start

        #get page results and advance
        while current <= end:
            # parse this page before advancing to next
            parsed = BeautifulSoup(resp.text, 'lxml')
            outer_table = parsed.find('table', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary')

            results = outer_table.find_all('table', width='100%')

            for i in range(len(results)):
                listing = {}
                res = results[i]
                listing['address'] = str(res.find('span',
                                                  id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblAddress_'
                                                     + str(i)).string)
                listing['address'] = listing['address'].replace('  ', ' ').strip()
                listing['parcel'] = str(res.find('a', href='#').string.strip())
                listing['sale #'] = str(res.find('span',
                                                 id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblSaleNumber_'
                                                    + str(i)).string)
                listing['sale date'] = str(res.find('span',
                                                    id = 'SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblSaleDate2_'
                                                         + str(i)).string)
                listing['case number'] = \
                    str(res.find('a', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lnkCaseNum_'
                                         + str(i)).string)
                listing['plaintiff'] = \
                    str(res.find('span', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblPlaintiffName_'
                                            + str(i)).string)
                listing['defendant'] = \
                    str(res.find('span', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblDefendant_'
                                            + str(i)).string)
                listing['plaintiffAtty'] = \
                    str(res.find('span', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblPlaintiffAtty_'
                                            + str(i)).string)
                listing['saleSummary'] = \
                    str(res.find('span', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblResidentialText_'
                                            + str(i)).string)
                listing['description'] = \
                    str(res.find('span', id='SheetContentPlaceHolder_C_searchresults_gvSaleSummary_lblDescription_'
                                            + str(i)).string)
                result_list.append(listing)
            # prepare to advance to next page
            current = current + 1

            if current <= end:
                formData = {
                     'ctl00$smMain': 'ctl00$SheetContentPlaceHolder$C_searchresults$updatePanel1 '
                                     + '| ctl00$SheetContentPlaceHolder$C_searchresults$btnNext',
                     'smMain_HiddenField':'',
                     '__EVENTTARGET':'',
                     '__EVENTARGUMENT':'',
                     '__VIEWSTATE':vState,
                     '__VIEWSTATEGENERATOR':vStateGen,
                     '__EVENTVALIDATION':eventVal,
                     '__ASYNCPOST':'true',
                     'ctl00$SheetContentPlaceHolder$C_searchresults$btnNext':'>'
                }

                headers['X-MicrosoftAjax'] = 'Delta=true'
                headers['X-Requested-With'] = 'XMLHttpRequest'
                #advance to next page
                resp = requests.post("https://" + host + path + 'results.aspx', data=formData,
                                     params=payload, headers=headers, cookies=cookies)
                logging.info(resp.status_code)
                #print(resp.text)

                aspAjaxResponse = resp.text.split('|')
                vState = aspAjaxResponse[aspAjaxResponse.index('__VIEWSTATE') + 1]
                eventVal = aspAjaxResponse[aspAjaxResponse.index('__EVENTVALIDATION') + 1]
                eventTarget = aspAjaxResponse[aspAjaxResponse.index('__EVENTTARGET') + 1]
                vStateGen = aspAjaxResponse[aspAjaxResponse.index('__VIEWSTATEGENERATOR') + 1]

                formData['__VIEWSTATE'] = vState
                formData['__EVENTVALIDATION'] = eventVal
                formData['__EVENTTARGET'] = eventTarget
                formData['__VIEWSTATEGENERATOR'] = vStateGen

        logging.debug(len(result_list))
        logging.debug(result_list)
        self.result_list = result_list
        return result_list

    def run_and_report(self, start_date='', end_date=''):

        try:
            start_split = start_date.split('/')
            if start_split[0] == '2' and int(start_split[1]) > 28:
                start_split[1] = '28'
            start_as_date = date(int(start_split[2]), int(start_split[0]), int(start_split[1]))
            start = start_as_date.isoformat()
        except (AttributeError, TypeError, ValueError, IndexError):
            curr_date = date.today()
            raw_month_num = curr_date.month - 6
            real_month_num = raw_month_num % 12
            raw_month_day = curr_date.day
            real_month_day = raw_month_day
            year_num = curr_date.year
            if raw_month_num < 7:
                year_num = curr_date.year - 1
            if real_month_num == 2 and raw_month_day > 28:
                real_month_day = 28
            if real_month_day == 31:
                real_month_day = 30
            start_as_date = curr_date.replace(month=real_month_num, year=year_num, day=real_month_day)
            logging.info(start_as_date.isoformat())
            start = start_as_date.isoformat()

        try:
            end_split = end_date.split('/')
            if end_split[0] == '2' and int(end_split[1]) > 28:
                end_split[1] = '28'
            end_as_date = date(int(end_split[2]), int(end_split[0]), int(end_split[1]))
            end = end_as_date.isoformat()
        except (AttributeError, TypeError, ValueError, IndexError):
            curr_date = date.today()
            raw_month_num = curr_date.month + 6
            real_month_num = raw_month_num % 12
            raw_month_day = curr_date.day
            real_month_day = raw_month_day
            year_num = curr_date.year
            if raw_month_num > 12:
            #     real_month_num = raw_month_num - 12
                 year_num = curr_date.year + 1
            if real_month_num == 2 and raw_month_day > 28:
                real_month_num = 3
                real_month_day = raw_month_day % 28
            if real_month_day == 31:
                real_month_day = 30
            end_as_date = curr_date.replace(month=real_month_num, year=year_num, day=real_month_day)
            logging.info(end_as_date.isoformat())
            end = end_as_date.isoformat()

        result_list = self.get_data(start_date=start, end_date=end)
        return result_list






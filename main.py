import pickle, requests, os, spacy, time, datefinder, datetime, dateutil, re, urllib.parse, sys
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from dateutil.parser import parse
from tqdm import tqdm
from word2number import w2n

class Config:
    """
    date
        -> date to scrape ('yymmdd')

    selenium_path
        -> path to selenium Edge drivers

    categories_dict
    -> a dictionary which contains the categories used in The Register of Members' Financial Interests
        -> e.g. {'c1':'1. Employment and earnings'}
    """ 

    selenium_path = r"C:/selenium_drivers/edgedriver_win64_101"
    selenium_options = Options()
    selenium_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32")

    categories_dict = {
        'c1': '1. Employment and earnings',
        'c2a': '2. (a) Support linked to an MP but received by a local party organisation or indirectly via a central party organisation',
        'c2b': '2. (b) Any other support not included in Category 2(a)',
        'c3': '3. Gifts, benefits and hospitality from UK sources',
        'c4': '4. Visits outside the UK',
        'c5': '5. Gifts and benefits from sources outside the UK',
        'c6': '6. Land and property portfolio: (i) value over £100,000 and/or (ii) giving rental income of over £10,000 a year',
        'c7i': '7. (i) Shareholdings: over 15% of issued share capital',
        'c7ii': '7. (ii) Other shareholdings, valued at more than £70,000',
        'c8': '8. Miscellaneous',
        'c9': '9. Family members employed and paid from parliamentary expenses',
        'c10': '10. Family members engaged in lobbying the public sector on behalf of a third party or client'
    }

class Scrape:
    """
    The Scraper class contains the individual scrapers used to populate the MP class instances and create the final spreadsheets

    constituencies() -> None
        -> scrapes parliament.uk to create a pkl file which stores geography information
        -> creates ./pkl/dict_constituencies.pkl
        -> only needs to be run once (this information won't change)
        -> saved as a dictionary in the format: {'constituency1': ('region', 'country'), 'constituency2': ('region', 'country'), ...}
    
    links(date) -> None
        -> scrapes indexes from all web sources (parluk, pp, wiki, ipsa, db) to create a dict of all the individual mp urls needed
        -> creates ./pkl/dict_name_urls.pkl
        -> run it every time there's a new update on The Register (bi-weekly)
        -> saved as a dict with structure: {
                                            'mp1url':{'name': name,
                                                    'parlukurl': parlukurl,
                                                    'ppurl':ppurl,
                                                    'wikiurl':wikiurl,
                                                    'ipsaurl':ipsaurl,
                                                    'dburl':dburl
                                                    },
                                            'mp2url':{
                                                    ...
                                                    },
                                            ...
                                            }
    mpfi(mpurl) -> None:
        -> scrapes latest update of The Register once and stores it in a pkl to avoid repeat scraping
            -> if mpurl=None: runs for all mps
            -> if mpurl: only runs and updates for the individual mpurl
        -> creates ./pkl/dict_mpfi.pkl
        -> run it every time there's a new update on The Register (bi-weekly)
        -> pkl is structured according to category and with indent information (useful when parsing later)
        -> saved as a dict with structure: {
                                            'mp1url':{
                                                    '1. Employment and earnings': [('i','line'),('i2','line'), ...],
                                                    '4. Visits outside the UK': [('i','line'),('i2','line'), ...],
                                                    'x. ...': [(i,),(i,),(i,),...],
                                                    },
                                            'mp2url':{
                                                    ...
                                                    },
                                            ...
                                            }

    """

    def constituencies() -> None:
        os.environ['PATH'] = Config.selenium_path

        filter_list = ['Conservative','Labour','Green Party','Liberal Democrat',
            'Independent','Speaker','Plaid Cymru','Democratic Unionist Party',
            'Sinn Féin','Social Democratic & Labour Party','Alliance'] 
            ## need to filter out elements picked up by scraper which aren't constituencies

        dict_constituencies = {}

        # get england regions
        england_url = 'https://members.parliament.uk/region/Region/'
        england_regions = ['South East','West Midlands','North West','East Midlands','London',
        'Yorkshire and The Humber','East of England', 'South West', 'North East']

        for region in england_regions:
            driver = webdriver.Edge(options=Config.selenium_options) ## Slow, I know, but I get CAPTCHA'd if I don't open/close the browser every time
            driver.get(england_url+region)

            elements = driver.find_elements(By.CLASS_NAME,'primary-info')
            for item in elements:
                if item.text not in filter_list:
                    dict_constituencies[item.text] = (region,'England')        

            driver.close()

        #s,w,ni regions
        other_url = 'https://members.parliament.uk/region/Country/'
        other_regions = ['Scotland', 'Northern Ireland', 'Wales']

        for region in other_regions:
            driver = webdriver.Edge()
            driver.get(other_url+region)

            elements = driver.find_elements(By.CLASS_NAME,'primary-info')
            for item in elements:
                if item.text not in filter_list:
                    dict_constituencies[item.text] = (region,region)

            driver.close()
        
        # write dict_constituencies to pkl file
        dict_constituencies_file = open('./pkl/dict_constituencies.pkl', 'wb')
        pickle.dump(dict_constituencies, dict_constituencies_file)
        dict_constituencies_file.close()

    def links(date: str) -> None:

        def parluk(date) -> dict: # -> {'mpurl':('name','parlukurl'), ...}
            url = 'https://publications.parliament.uk/pa/cm/cmregmem/'+date+'/contents.htm'
            os.environ['PATH'] = Config.selenium_path
            driver = webdriver.Edge(options=Config.selenium_options)

            driver.get(url)
            time.sleep(5)

            p_tags = driver.find_elements(By.TAG_NAME, 'p')

            # delete p's which are headers etc
            i = 0
            while i <= 7:
                del p_tags[0]
                i += 1
            time.sleep(5)

            # capture parlukurl / name in dict
            dict_parlukurl_name = {}
            for p_tag in tqdm(p_tags, desc="Parliament.uk"):
                a_tags = p_tag.find_elements(By.TAG_NAME, 'a')
                if len(a_tags) == 1:
                    parlukurl = a_tags[0].get_attribute('href')
                    name = a_tags[0].text.strip()
                if len(a_tags) == 2:
                    parlukurl = a_tags[1].get_attribute('href')
                    name = a_tags[1].text.strip()
                mpurl = urllib.parse.unquote(parlukurl.replace('https://publications.parliament.uk/pa/cm/cmregmem/'+date+'/','').replace('.htm',''))
                dict_parlukurl_name[mpurl] = (urllib.parse.unquote(name),urllib.parse.unquote(parlukurl))
            
            driver.close()

            return dict_parlukurl_name

        def pp(dict) -> dict: # -> {'mpurl':'ppurl', ...}
            dict_url_nameparlukurl = dict

            dict_ppurl = {}
            for mpurl in tqdm(dict_url_nameparlukurl.keys(), desc="ParallelParliament"):
                pp_url = str(mpurl.split('_')[1]+'-'+mpurl.split('_')[0])
                dict_ppurl[mpurl] = urllib.parse.unquote('https://www.parallelparliament.co.uk/mp/'+pp_url)
            
            dict_ppurl['dines_sarah'] = 'https://www.parallelparliament.co.uk/mp/miss-sarah-dines'
            dict_ppurl['qaisar_anum'] = 'https://www.parallelparliament.co.uk/mp/anum-qaisar-javed'
            dict_ppurl['davey_ed'] = 'https://www.parallelparliament.co.uk/mp/edward-davey'

            return dict_ppurl

        def wiki(dict) -> dict: # -> {'mpurl':'wikiurl', ...}
            dict_wikiurls = {}
            dict_url_nameparlukurl = dict

            os.environ['PATH'] = Config.selenium_path
            driver = webdriver.Edge(options=Config.selenium_options)

            for mpurl in tqdm(dict_url_nameparlukurl.keys(), desc="Wikipedia.org"):
                wiki_url = 'https://en.wikipedia.org/wiki/'+str(mpurl.replace('.htm','').split('_')[1]+'_'+mpurl.replace('.htm','').split('_')[0]).title()
                driver.get(wiki_url)
                page = driver.page_source
                wiki_soup = BeautifulSoup(page, 'html.parser')

                if wiki_soup.find('a', title='Member of Parliament (United Kingdom)'): ## ensures it's the right page - i.e. it's the MP, not someone else by the same name
                    dict_wikiurls[mpurl] = urllib.parse.unquote(wiki_url)
                else:
                    for _link in ['_(MP)','_(British_politician)','_(politician)','_(English_politician)','_(London_politician)','_(Scottish_politician)','_(Labour_politician)','_(Conservative_politician)']: 
                        wiki_url = 'https://en.wikipedia.org/wiki/'+str(mpurl.replace('.htm','').split('_')[1]+'_'+mpurl.replace('.htm','').split('_')[0]).title()+_link
                        wiki_page = requests.get(wiki_url)
                        wiki_soup = BeautifulSoup(wiki_page.content, 'html.parser')
                        if wiki_soup.find('a', title='Member of Parliament (United Kingdom)'):
                            dict_wikiurls[mpurl] = urllib.parse.unquote(wiki_url)
                            break
                        else:
                            if _link == '_(Conservative_politician)':
                                dict_wikiurls[mpurl] = ''
                                break
                            else:
                                pass
            
            driver.close()
                
            dict_wikiurls['bailey_shaun'] = 'https://en.wikipedia.org/wiki/Shaun_Bailey_(West_Bromwich_MP)'
            dict_wikiurls['begley_órfhlaith'] = urllib.parse.unquote('https://en.wikipedia.org/wiki/Órfhlaith_Begley')
            dict_wikiurls['brown_nicholas'] = 'https://en.wikipedia.org/wiki/Nick_Brown'
            dict_wikiurls['davies_david-t-c'] = 'https://en.wikipedia.org/wiki/David_T._C._Davies'
            dict_wikiurls['de-cordova_marsha'] = 'https://en.wikipedia.org/wiki/Marsha_de_Cordova'
            dict_wikiurls['dhesi_tanmanjeet-singh'] = 'https://en.wikipedia.org/wiki/Tanmanjeet_Singh_Dhesi'
            dict_wikiurls['donaldson_jeffrey-m'] = 'https://en.wikipedia.org/wiki/Jeffrey_Donaldson'
            dict_wikiurls['dunne_philip'] = 'https://en.wikipedia.org/wiki/Philip_Dunne_(Ludlow_MP)'
            dict_wikiurls['foy_mary-kelly'] = 'https://en.wikipedia.org/wiki/Mary_Foy_(politician)'
            dict_wikiurls['gill_preet-kaur'] = 'https://en.wikipedia.org/wiki/Preet_Gill'
            dict_wikiurls['holmes_paul'] = 'https://en.wikipedia.org/wiki/Paul_Holmes_(Eastleigh_MP)'
            dict_wikiurls['howell_paul'] = 'https://en.wikipedia.org/wiki/Paul_Howell_(MP)'
            dict_wikiurls['jones_david'] = 'https://en.wikipedia.org/wiki/David_Jones_(Clwyd_West_MP)'
            dict_wikiurls['macneil_angus-brendan'] = 'https://en.wikipedia.org/wiki/Angus_MacNeil'
            dict_wikiurls['mccabe_steve'] = 'https://en.wikipedia.org/wiki/Steve_McCabe'
            dict_wikiurls['mccarthy_kerry'] = 'https://en.wikipedia.org/wiki/Kerry_McCarthy'
            dict_wikiurls['mccartney_jason'] = 'https://en.wikipedia.org/wiki/Jason_McCartney_(politician)'
            dict_wikiurls['mccartney_karl'] = 'https://en.wikipedia.org/wiki/Karl_McCartney'
            dict_wikiurls['mcdonagh_siobhain'] = 'https://en.wikipedia.org/wiki/Siobhain_McDonagh'
            dict_wikiurls['mcdonald_andy'] = 'https://en.wikipedia.org/wiki/Andy_McDonald_(politician)'
            dict_wikiurls['mcdonald_stewart-malcolm'] = 'https://en.wikipedia.org/wiki/Stewart_McDonald_(politician)'
            dict_wikiurls['mcdonald_stuart-c'] = 'https://en.wikipedia.org/wiki/Stuart_McDonald_(Scottish_politician)'
            dict_wikiurls['mcdonnell_john'] = 'https://en.wikipedia.org/wiki/John_McDonnell'
            dict_wikiurls['mcfadden_pat'] = 'https://en.wikipedia.org/wiki/Pat_McFadden'
            dict_wikiurls['mcginn_conor'] = 'https://en.wikipedia.org/wiki/Conor_McGinn'
            dict_wikiurls['mcgovern_alison'] = 'https://en.wikipedia.org/wiki/Alison_McGovern'
            dict_wikiurls['mckinnell_catherine'] = 'https://en.wikipedia.org/wiki/Catherine_McKinnell'
            dict_wikiurls['mclaughlin_anne'] = 'https://en.wikipedia.org/wiki/Anne_McLaughlin'
            dict_wikiurls['mcmahon_jim'] = 'https://en.wikipedia.org/wiki/Jim_McMahon_(politician)'
            dict_wikiurls['mcmorrin_anna'] = 'https://en.wikipedia.org/wiki/Anna_McMorrin'
            dict_wikiurls['mcnally_john'] = 'https://en.wikipedia.org/wiki/John_McNally_(politician)'
            dict_wikiurls['mcpartland_stephen'] = 'https://en.wikipedia.org/wiki/Stephen_McPartland'
            dict_wikiurls['moore_robbie'] = 'https://en.wikipedia.org/wiki/Robbie_Moore_(MP)'
            dict_wikiurls['neill_robert'] = 'https://en.wikipedia.org/wiki/Bob_Neill'
            dict_wikiurls['obrien_neil'] = urllib.parse.unquote('https://en.wikipedia.org/wiki/Neil_O%27Brien')
            dict_wikiurls['ohara_brendan'] = urllib.parse.unquote('https://en.wikipedia.org/wiki/Brendan_O%27Hara')
            dict_wikiurls['paisley_ian'] = 'https://en.wikipedia.org/wiki/Ian_Paisley_Jr'
            dict_wikiurls['wood_mike'] = 'https://en.wikipedia.org/wiki/Mike_Wood_(Conservative_politician)'

            return dict_wikiurls

        def ipsa() -> dict: # -> {'mpurl':'ipsaurl', ...}
            url = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp'
            os.environ['PATH'] = Config.selenium_path
            driver = webdriver.Edge(options=Config.selenium_options)

            driver.get(url)

            buttons = driver.find_elements_by_class_name('govuk-accordion__section-button')
            for button in tqdm(buttons, desc="theIPSA.org.uk"):
                time.sleep(2)
                button.click()
            time.sleep(10)
            
            links = driver.find_elements_by_class_name('govuk-link')
            ipsaurls = []
            for link in links:
                try:
                    if '/mp-staffing-business-costs/your-mp/' in link.get_attribute('href'):
                        ipsaurls.append(link.get_attribute('href'))
                    else:
                        pass
                except:
                    pass
            
            dict_ipsaurls = {}
            for link in ipsaurls:
                ipsa_name = ''.join([i for i in link.replace('https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/','').replace('/','') if not i.isdigit()])
                dict_ipsaurls[urllib.parse.unquote(ipsa_name.split('-')[1]+'_'+ipsa_name.split('-')[0])] = urllib.parse.unquote(link)
            time.sleep(1)

            driver.close()

            ## manual entries
            dict_ipsaurls['ahmad-khan_imran'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/imran-ahmad-khan/4841'
            dict_ipsaurls['allin-khan_rosena'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/rosena-allin-khan/4573'
            dict_ipsaurls['begley_órfhlaith'] = urllib.parse.unquote('https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/%C3%B3rfhlaith-begley/4697')
            dict_ipsaurls['clarke-smith_brendan'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/brendan-clarke-smith/4756'
            dict_ipsaurls['clifton-brown_geoffrey'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/geoffrey-clifton-brown/249'
            dict_ipsaurls['coffey_therese'] = urllib.parse.unquote('https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/th%C3%A9r%C3%A8se-coffey/4098')
            dict_ipsaurls['davies-jones_alex'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/alex-davies-jones/4849'
            dict_ipsaurls['davies_david-t-c'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/david-t-c-davies/1545'
            dict_ipsaurls['de-cordova_marsha'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/marsha-de-cordova/4676'
            dict_ipsaurls['dhesi_tanmanjeet-singh'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/tanmanjeet-singh-dhesi/4638'
            dict_ipsaurls['docherty-hughes_martin'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/martin-docherty-hughes/4374'
            dict_ipsaurls['donaldson_jeffrey-m'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/jeffrey-m-donaldson/650'
            dict_ipsaurls['doyle-price_jackie'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/jackie-doyle-price/4065'
            dict_ipsaurls['duncan-smith_iain'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/iain-duncan-smith/152'
            dict_ipsaurls['foy_mary-kelly'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/mary-kelly-foy/4753'
            dict_ipsaurls['gill_preet-kaur'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/preet-kaur-gill/4603'
            dict_ipsaurls['hart_sally-ann'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/sally-ann-hart/4842'
            dict_ipsaurls['heaton-harris_chris'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/chris-heaton-harris/3977'
            dict_ipsaurls['lewell-buck_emma'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/emma-lewell-buck/4277'
            dict_ipsaurls['liddell-grainger_ian'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/ian-liddell-grainger/1396'
            dict_ipsaurls['long-bailey_rebecca'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/rebecca-long-bailey/4396'
            dict_ipsaurls['macneil_angus-brendan'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/angus-brendan-macneil/1546'
            dict_ipsaurls['mcdonald_stewart-malcolm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/stewart-malcolm-mcdonald/4461'
            dict_ipsaurls['mcdonald_stuart-c'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/stuart-c-mcdonald/4393'
            dict_ipsaurls['morris_anne-marie'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/anne-marie-morris/4249'
            dict_ipsaurls['mumby-croft_holly'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/holly-mumby-croft/4867'
            dict_ipsaurls['obrien_neil'] = "https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/neil-o'brien/4679"
            dict_ipsaurls['ohara_brendan'] = "https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/brendan-o'hara/4371"
            dict_ipsaurls['oppong-asare_abena'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/abena-oppong-asare/4820'
            dict_ipsaurls['rees-mogg_jacob'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/jacob-rees-mogg/4099'
            dict_ipsaurls['ribeiro-addy_bell'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/bell-ribeiro-addy/4764'
            dict_ipsaurls['russell-moyle_lloyd'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/lloyd-russell-moyle/4615'
            dict_ipsaurls['vara_shailesh'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/shailesh-vara/1496'
            dict_ipsaurls['saville-roberts_liz'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/liz-saville-roberts/4521'
            dict_ipsaurls['thomas-symonds_nick'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/nick-thomas-symonds/4479'
            dict_ipsaurls['trevelyan_anne-marie'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/anne-marie-trevelyan/4531'
            dict_ipsaurls['zahawi_nadhim'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/nadhim-zahawi/4113'
            dict_ipsaurls['zeichner_daniel'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/daniel-zeichner/4382'

            return dict_ipsaurls

        def db(dict1,dict2) -> dict: # -> {'mpurl':'dburl', ...}
            dict_parlukurl_name = dict1
            dict_wikiurls = dict2

            dict_dburls = {}
            for mpurl in tqdm(dict_parlukurl_name.keys(), desc="DBpedia.org"):
                dict_dburls[mpurl] = urllib.parse.unquote(dict_wikiurls[mpurl].replace('https://en.wikipedia.org/wiki/','https://dbpedia.org/page/'))

            return dict_dburls

        dict_url_nameparlukurl = parluk('220228')
        dict_ppurl = pp(dict_url_nameparlukurl)
        dict_wikiurl = wiki(dict_url_nameparlukurl)
        dict_dburl = db(dict_url_nameparlukurl,dict_wikiurl)
        dict_ipsaurl = ipsa()

        failed_urls = []
        dict_name_urls = {}
        for mpurl, name_parlukurl in tqdm(list(dict_url_nameparlukurl.items()),desc="Compiling dict..."):
            try:
                name = name_parlukurl[0]
                parlukurl = urllib.parse.unquote(name_parlukurl[1])

                dict_name_urls[mpurl] = {
                    'name':name,
                    'parlukurl':parlukurl,
                    'ppurl':dict_ppurl[mpurl],
                    'wikiurl':dict_wikiurl[mpurl],
                    'ipsaurl':dict_ipsaurl[mpurl],
                    'dburl':dict_dburl[mpurl]
                }
                #print(mpurl,' SUCCESS')
            except Exception as e:
                failed_urls.append((mpurl,e))
                #print(mpurl,' FAILED')

        # save to pkl
        dict_name_urls_file = open('./pkl/dict_name_urls.pkl', 'wb')
        pickle.dump(dict_name_urls, dict_name_urls_file)
        dict_name_urls_file.close()

        return failed_urls

    def mpfi(mpurl: str = None) -> None:
            os.environ['PATH'] = Config.selenium_path
            dict_name_urls = pickle.load(open('./pkl/dict_name_urls.pkl','rb'))

            def get_indv_dict(parlukurl: str) -> dict:
                # option to add headers back in if I start getting blocked (False by default)
                driver = webdriver.Edge(options=Config.selenium_options) ## yes it's slow to open/close every time but otherwise you get CAPTCHA'd
                
                driver.get(parlukurl)

                content = driver.page_source
                soup = BeautifulSoup(content, 'html.parser')

                dict_indv_mpfi = {}
                all_text = soup.find('div', id='mainTextBlock').find_all('p')[1:]

                if all_text[0].text == 'Nil':
                    dict_indv_mpfi = None
                else:
                    for p in all_text:
                        if p.text in Config.categories_dict.values():
                            h = p.text
                            h_list = []
                        else:
                            try:
                                if p['class'][0] == 'indent':
                                    h_list.append(('i', p.text))
                                elif p['class'][0] == 'indent2':
                                    h_list.append(('i2', p.text))
                            except:
                                pass
                        dict_indv_mpfi[h] = h_list
                
                driver.close()

                return dict_indv_mpfi
            
            failed_urls = []
            if mpurl is None:
                dict_mpfi = {}
                for mpurl, name_urls in tqdm(dict_name_urls.items(), desc=mpurl):
                    parlukurl = name_urls['parlukurl']
                    try:
                        dict_indv_mpfi = get_indv_dict(parlukurl)
                        dict_mpfi[mpurl] = dict_indv_mpfi
                        #print(mpurl,' SUCCESS')
                    except Exception as e:
                        failed_urls.append((mpurl,e))
                        #print(mpurl,' FAIL')
            else:
                dict_mpfi = pickle.load(open('./pkl/dict_mpfi.pkl','rb'))
                parlukurl = dict_name_urls[mpurl]['parlukurl']
                dict_indv_mpfi = get_indv_dict(parlukurl)
                dict_mpfi[mpurl] = dict_indv_mpfi

            dict_mpfi_file = open('./pkl/dict_mpfi.pkl', 'wb')
            pickle.dump(dict_mpfi, dict_mpfi_file)
            dict_mpfi_file.close()

            # save backup
            dict_mpfi_backup_file = open('./pkl/mpfi_by_date/'+date+'.pkl', 'wb')
            pickle.dump(dict_mpfi, dict_mpfi_backup_file)
            dict_mpfi_backup_file.close()

            return failed_urls

    def other_info(mpurl: str = None) -> None:
            dict_name_urls = pickle.load(open('./pkl/dict_name_urls.pkl','rb'))
            dict_constituencies = pickle.load(open('./pkl/dict_constituencies.pkl','rb'))

            def get_indv_dict(mpurl):
                # DICTIONARY
                dict_indv_mp = {
                    'name': dict_name_urls[mpurl]['name'],
                    'party': '',
                    'constituency': '',
                    'region': '',
                    'country': '',
                    'assumed_office': '',
                    'years_in_office': '',
                    'majority': '',
                    'basic_salary': '',
                    'lalp_payment': '',
                }

                os.environ['PATH'] = Config.selenium_path
                driver = webdriver.Edge(options=Config.selenium_options)

                # SCRAPE PARALLELPARLIAMENT.CO.UK FOR PARTY
                ppurl = dict_name_urls[mpurl]['ppurl']
                driver.get(ppurl)

                try:
                    dict_indv_mp['party'] = driver.find_element(By.CLASS_NAME, 'card-header.text-center').find_element(By.TAG_NAME, 'h4').text.replace('\n','').split(' - ')[0].strip()
                except Exception as e:
                    #print('ppurl party failed:',e)
                    pass
                
                try:
                    dict_indv_mp['constituency'] = driver.find_element(By.CLASS_NAME, 'card-header.text-center').find_element(By.TAG_NAME, 'h4').text.replace('\n','').split(' - ')[1].strip()
                    dict_indv_mp['region'], dict_indv_mp['country'] = dict_constituencies[dict_indv_mp['constituency']]
                except Exception as e:
                    dict_indv_mp['constituency'] = driver.find_element(By.CLASS_NAME, 'card-header.text-center').find_element(By.TAG_NAME, 'h4').text
                    #print('ppurl constituency failed:',e)

                # SCRAPE THEIPSA.ORG.UK/MP-STAFFING-BUSINESS-COSTS/YOUR-MP/ FOR ASSUMED_OFFICE, YEARS_IN_OFFICE, BASIC_SALARY, LALP_PAYMENT
                ipsaurl = dict_name_urls[mpurl]['ipsaurl']
                driver.get(ipsaurl)

                try:
                    dict_indv_mp['assumed_office'] = parse(driver.find_element(By.CLASS_NAME,'govuk-body-l').text, fuzzy=True).date()
                    dict_indv_mp['years_in_office'] = datetime.datetime.now().year - dict_indv_mp['assumed_office'].year
                except Exception as e:
                    #print('ipsaurl assumed_office failed:',e)
                    pass
                
                try:
                    buttons = driver.find_elements(By.CLASS_NAME,'govuk-accordion__section-button')
                    for button in buttons:
                        if button.text == '2020 to 2021':
                            button.click()
                    time.sleep(2)

                    buttons = driver.find_elements(By.TAG_NAME, 'button')
                    for button in buttons:
                        if button.text == 'MP Payroll information':
                            button.click()
                    time.sleep(2)

                    tables = driver.find_elements(By.TAG_NAME,'table')
                    for table in tables:
                        if 'Basic salary received during 2020 - 2021' in table.text:
                            payroll_table = table
                    for row in payroll_table.find_elements(By.TAG_NAME,'tr'):
                        if 'Basic salary received during 2020 - 2021' in row.text:
                            basic_salary = row.text.replace('Basic salary received during 2020 - 2021','').strip()
                            dict_indv_mp['basic_salary'] = float(basic_salary.replace('£','').replace(',','').strip())
                        elif 'Amount paid to MP as LALP during 2020 to 2021' in row.text:
                            lalp_payment = row.text.replace('Amount paid to MP as LALP during 2020 to 2021','').strip()
                            dict_indv_mp['lalp_payment'] = float(lalp_payment.replace('£','').replace(',','').strip())
                except Exception as e:
                    dict_indv_mp['basic_salary'] = 'Not available'
                    dict_indv_mp['lalp_payment'] = 'Not available'
                    #print('ipsaurl basic salary or lalp_payment failed',e)

                # SCRAPE WIKIPEDIA FOR MAJORITY
                try:
                    wikiurl = dict_name_urls[mpurl]['wikiurl']
                    driver.get(wikiurl)

                    for row in driver.find_elements(By.TAG_NAME,'tr'):
                        if 'Majority' in row.text:
                            dict_indv_mp['majority'] = row.text.replace('Majority','').strip().split(' ')[1].replace('(','').replace('%)','')
                except Exception as e:
                    #print('wikiurl failed',e)
                    pass

                # Close driver
                driver.close()

                #print('dict_indv_mp: ',dict_indv_mp)

                return dict_indv_mp

            if mpurl == None:
                # if there is already a dict_other_info file then load that / else create a blank one
                if os.path.isfile('./pkl/dict_other_info.pkl'):
                    dict_other_info = pickle.load(open('./pkl/dict_other_info.pkl','rb'))
                    start_index = len(dict_other_info)-1 # repeats the last scraped mp in case the scrape was terminated part-way through
                else:
                    dict_other_info = {}
                    start_index = 0
                
                failed_urls = []
                for mpurl, name_urls in tqdm(list(dict_name_urls.items())[start_index:]):
                    try:
                        dict_other_info = pickle.load(open('./pkl/dict_other_info.pkl','rb'))
                        dict_other_info[mpurl] = get_indv_dict(mpurl) # not very efficient to open/close but this allows for doing this scrape in bursts as it takes a long time (~3-4 hours)
                        
                        dict_other_info_file = open('./pkl/dict_other_info.pkl', 'wb')
                        pickle.dump(dict_other_info, dict_other_info_file)
                        dict_other_info_file.close()
                    except Exception as e:
                        #print('*** FAILED ***',mpurl,e)
                        failed_urls.append((mpurl,e))
                
                # MANUAL ADD-INS
                dict_other_info['mortimer_jill']['party'] = 'Conservative'
                dict_other_info['mortimer_jill']['constituency'] = 'Hartlepool'
                dict_other_info['mortimer_jill']['region'], dict_other_info['mortimer_jill']['country'] = dict_constituencies[dict_other_info['mortimer_jill']['constituency']]
                
                dict_other_info['wilson_sammy']['party'] = 'Democratic Unionist Party'
                dict_other_info['wilson_sammy']['constituency'] = 'East Antrim'
                dict_other_info['wilson_sammy']['region'], dict_other_info['wilson_sammy']['country'] = dict_constituencies[dict_other_info['wilson_sammy']['constituency']]

                dict_other_info['leadbeater_kim']['party'] = 'Labour'
                dict_other_info['leadbeater_kim']['constituency'] = 'Batley and Spen'
                dict_other_info['leadbeater_kim']['region'], dict_other_info['leadbeater_kim']['country'] = dict_constituencies[dict_other_info['leadbeater_kim']['constituency']]

                dict_other_info['green_sarah']['party'] = 'Liberal Democrat'
                dict_other_info['green_sarah']['constituency'] = 'Chesham and Amersham'
                dict_other_info['green_sarah']['region'], dict_other_info['green_sarah']['country'] = dict_constituencies[dict_other_info['green_sarah']['constituency']]

                # SAVE TO PKL
                dict_other_info_file = open('./pkl/dict_other_info.pkl', 'wb')
                pickle.dump(dict_other_info, dict_other_info_file)
                dict_other_info_file.close()

                #print('\n\n*** FAILED URLS ***\n\n',failed_urls,'\n\n *** \n\n')

            else:
                dict_other_info = pickle.load(open('./pkl/dict_other_info.pkl','rb'))
                try:
                    dict_other_info[mpurl] = get_indv_dict(mpurl)
                except Exception as e:
                    #print('get_indv_mp failed:',e)
                    pass

                dict_other_info_file = open('./pkl/dict_other_info.pkl', 'wb')
                pickle.dump(dict_other_info, dict_other_info_file)
                dict_other_info_file.close()

class Extract:
    """
    The Extract class contains the functions required to turn dict_mpfi into the final data needed
    for the spreadsheet. It uses custom-trained named entity recognition models (spaCy) to extract entities.

    mpfi() -> None
        -> This function turns the lines stored in dict_mpfi into a long list of dicts where each dict represents a line. 
        -> The dict contains all of the final data required for the spreadsheet and is structured like this: 
            [
                {
                    'name': 'Abbott, Ms Diane', 
                    'full_text': 'Payments from the Guardian, Kings Place, 90 York Way, London N1 9GU, for articles:', 
                    'parlukurl': 'https://publications.parliament.uk/pa/cm/cmregmem/220419/abbott_diane.htm', 
                    'date': '', 'orgs': 'the Guardian', 
                    'money': '', 'time': '', 
                    'role': 'for articles', 
                    'total_money_ytd': None, 
                    'total_time_ytd': None
                },
                {
                    ...
                },
                ...
            ]
    
    """

    def date_processor(dict_line: str) -> datetime: #dict_line['date'] -> start_date_ytd, end_date_ytd

        def ytd(date: datetime) -> datetime: # date -> date_ytd
            if date <= mpfi_date_minus_one_year:
                date_ytd = mpfi_date_minus_one_year
            elif date >= mpfi_date_minus_one_year and date <= mpfi_date:
                date_ytd = date
            elif date >= mpfi_date:
                date_ytd = mpfi_date
            
            return date_ytd

        date_raw = dict_line['date']

        # filter out any date lists with more than 1 element / choose longest date / make lowercase for processing
        if len(date_raw) > 1: date_raw = max(date_raw, key=len).lower()     # takes longest item in dict_date as new dict_date                    
        else: date_raw = date_raw[0].lower()

        date_raw = date_raw.replace('further notice',date_words).replace('election to parliament',election_date_words)

        # datefinder is very buggy - it works best if I take out keywords such as from and until and replace them with hashes
        date_keywords = ['from','since','onwards','until','between',' and ',' to ']

        datefinder_raw = date_raw
        for keyword in date_keywords:
            if keyword in datefinder_raw:
                datefinder_raw = datefinder_raw.replace(keyword,'#')

        dates = [i for i in datefinder.find_dates(datefinder_raw)]
        # get start_date and end_date
        if len(dates) == 2:
            start_date = ytd(dates[0])
            end_date = ytd(dates[1])

        elif len(dates) == 1:
            if any([i for i in ['from','since','onwards'] if i in date_raw]):
                start_date = ytd(dates[0])
                end_date = mpfi_date
            elif 'until' in date_raw:
                end_date = ytd(dates[0])
                start_date = ytd(end_date+datetime.timedelta(-365))
            else:
                start_date = ytd(dates[0])
                end_date = ytd(dates[0])

        return start_date, end_date

    def total_money_ytd(dict_line: str) -> int: ## dict_line => total_money_ytd
        # if date or money is missing, return none
        if len(dict_line['date']) == 0:
            total_money_ytd = None
        elif len(dict_line['money']) == 0:
            total_money_ytd = None
        else:
            # for dict_line['total_money_ytd']: find money_period and money_raw_value
            period_dict = {
                '1': 1,
                'D': 365,
                'W': 52,
                '2W': 26,
                'M': 12,
                'Q': 4,
                'Y': 1,
                'NA': 1
            }
            if len(dict_line['money']) > 1:
                total_money_ytd = 'MANUAL_CHECK'
            else:
                try:
                    money_raw_value = float(''.join([i for i in dict_line['money'][0] if i.isdigit() is True or i == '.']))
                except:
                    total_money_ytd = 'MANUAL_CHECK'
                    return total_money_ytd
                money_period = nlp_money(dict_line['money'][0]).ents[0].label_

                # for dict_line['total_money_ytd']: calculate total_money_ytd
                if money_period == '1':                                         # for non-recurring sums, check if the sum is in date
                    try:
                        date_parsed = dateutil.parser.parse(dict_line['date'][0])
                        if date_parsed < mpfi_date_minus_one_year:
                            total_money_ytd = float(0)
                        else:
                            total_money_ytd = money_raw_value
                    except:
                        start_date_ytd, end_date_ytd = Extract.date_processor(dict_line)
                        total_money_for_one_year = money_raw_value*period_dict[money_period]
                        try:
                            percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                            if percentage_of_year_elapsed == 0.0:                    # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                                total_money_ytd = float(0)
                            else:
                                total_money_ytd = round(total_money_for_one_year*percentage_of_year_elapsed)
                        except:                                                       # if date_processor returns None's
                            total_money_ytd = 'MANUAL_CHECK'
                else:                                                                 # for recurring sums (i.e. D, W, 2W, M, Q, Y)
                    start_date_ytd, end_date_ytd = Extract.date_processor(dict_line)
                    total_money_for_one_year = money_raw_value*period_dict[money_period]
                    try:
                        percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                        if percentage_of_year_elapsed == 0.0:                         # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                            total_money_ytd = float(0)
                        else:
                            total_money_ytd = round(total_money_for_one_year*percentage_of_year_elapsed)
                    except:                                                          # if date_processor returns None's
                        total_money_ytd = None

        try:
            if total_money_ytd > 500000:
                total_money_ytd = 'MANUAL_CHECK'
            else:
                pass
        except:
            pass

        return total_money_ytd                    
    
    def total_time_ytd(dict_line: str) -> int: ## dict_line => total_money_ytd

        ##################################
        ## TOTAL_TIME_YTD SUB-FUNCTIONS ##
        ##################################

        def numwords(text):
            list_text = text.split(' ')
            #print(list_text)
            list_new_text = []
            for item in list_text:
                try:
                    list_new_text.append(w2n.word_to_num(item))
                except:
                    list_new_text.append(item)
            #print(list_new_text)

            new_text = ' '.join([str(item) for item in list_new_text])
            
            if 'a year' in new_text:                                                    
                new_text = new_text.replace('a year', 'per year')       # nlp_trf doesn't like 'a year' for some reason...
            #print(new_text)
            return new_text

        def time_processor(text): # dict_line['time'] > time_raw_value
            
            # replace any word-nums with nums
            text = numwords(text)
            #print(text)

            # extract date and remove 'per month' etc
            doc_time = nlp_trf(text)
            try:                                                                       
                time = [i for i in doc_time.ents if i.label_ == 'TIME'][0].text
            except:
                try:                                                                    # times given in days (e.g. '8 days per month') are recognised as 'DATE' ents by nlp_trf
                    time = [i for i in doc_time.ents if i.label_ == 'DATE'][0].text
                except:                                     
                    time = 'MANUAL_CHECK'
                    return time

            # REMOVE MISLEADING WORDS
            time = time.replace('non-consecutive','')

            # PROCESS FOR RANGES
            if '-' in time:
                time_raw_value = time.rsplit('-')[1].strip() #strip out hyphens (and non-numerics) and use higher bound figure (e.g. 80-100 hours)
            elif ' and ' in time:
                time_raw_value = time.rsplit(' and ')[1].strip() #strip out ' and ' (and non-numerics) and use higher bound figure (e.g. 80 and 100 hours)
            elif 'approx.' in time:
                time_raw_value = time.replace('approx.','')[1].strip() #strip out 'approx' (and non-numerics) and use higher bound figure (e.g. 80-100 hours)
            else:
                time_raw_value = time
            
            # PROCESS FOR MINS/HOURS
            m_keywords = ['mins','min']
            h_keywords = ['hrs','hours','hr']
            d_keywords = ['day']

            list_mhd = []
            for item in m_keywords:
                if item in time_raw_value: list_mhd.append('m')
            for item in h_keywords:
                if item in time_raw_value: list_mhd.append('h')  
            for item in d_keywords:
                if item in time_raw_value: list_mhd.append('d')  

            if 'm' in list_mhd and 'h' in list_mhd:
                list_time_values = [float(s) for s in re.findall(r'-?\d+\.?\d*', time_raw_value)]
                hrs = list_time_values[0]
                mins = list_time_values[1]
            elif 'h' in list_mhd and 'm' not in list_mhd:
                try:
                    hrs = float(re.findall(r'-?\d+\.?\d*', time_raw_value)[0])
                except:                                                         # PROCESS FOR WORD-NUMBERS (E.G.'SIX HOURS')
                    pass
                mins = float(0)
            elif 'm' in list_mhd and 'h' not in list_mhd:
                try: 
                    mins = float(re.findall(r'-?\d+\.?\d*', time_raw_value)[0])
                except:                                                         # PROCESS FOR WORD-NUMBERS (E.G.'THIRTY MINUTES')
                    pass
                hrs = float(0)
            elif 'd' in list_mhd:
                days = float(re.findall(r'-?\d+\.?\d*', time_raw_value)[0])
                hrs = days*8                                                     # ASSUMING 8-HOUR WORKING DAY
                mins = float(0)                                                 

            time_raw_value = round(hrs+(mins/60), 2)                             # TIME_RAW_VALUE IN HOURS

            return time_raw_value

        ##################################
        ## TOTAL_TIME_YTD MAIN FUNCTION ##
        ##################################

        # if date or money is missing, return none
        if len(dict_line['date']) == 0:
            total_time_ytd = None
        elif len(dict_line['time']) == 0:
            total_time_ytd = None
        else:
            # for dict_line['total_money_ytd']: find money_period and money_raw_value
            period_dict = {
                '1': 1,
                'D': 365,
                'W': 52,
                '2W': 26,
                'M': 12,
                'Q': 4,
                'Y': 1,
                'NA': 1
            }
            if len(dict_line['time']) > 1:
                total_time_ytd = 'MANUAL_CHECK'
            else:
                time_raw_value = time_processor(dict_line['time'][0])
                if time_raw_value == 'MANUAL_CHECK':
                    total_time_ytd = 'MANUAL_CHECK'
                    return total_time_ytd
                time_period = nlp_time(dict_line['time'][0]).ents[0].label_

                # for dict_line['total_money_ytd']: calculate total_money_ytd
                if time_period == '1':                                         # for non-recurring sums, check if the sum is in date
                    try:
                        date_parsed = [i for i in datefinder.find_dates(dict_line['date'][0])][0]
                        if date_parsed < mpfi_date_minus_one_year:
                            total_time_ytd = float(0)
                        else:
                            total_time_ytd = time_raw_value
                    except:
                        start_date_ytd, end_date_ytd = Extract.date_processor(dict_line)
                        total_time_for_one_year = time_raw_value*period_dict[time_period]
                        try:
                            percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                            if percentage_of_year_elapsed == 0.0:                    # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                                total_time_ytd = float(0)
                            else:
                                total_time_ytd = round(total_time_for_one_year*percentage_of_year_elapsed, 2)
                        except:                                                       # if date_processor returns None's
                            total_time_ytd = None
                else:                                                                 # for recurring sums (i.e. D, W, 2W, M, Q, Y)
                    start_date_ytd, end_date_ytd = Extract.date_processor(dict_line)
                    total_time_for_one_year = time_raw_value*period_dict[time_period]
                    try:
                        percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                        if percentage_of_year_elapsed == 0.0:                         # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                            total_time_ytd = float(0)
                        else:
                            total_time_ytd = round(total_time_for_one_year*percentage_of_year_elapsed, 2)
                    except:                                                          # if date_processor returns None's
                        total_time_ytd = None

        return total_time_ytd  

    def parse_lines_mp(mpurl: str, category: str = 'c1') -> list: ## mpurl => parsed_lines_mp
        dict_name_urls = pickle.load(open('./pkl/dict_name_urls.pkl','rb'))
        dict_mpfi = pickle.load(open('./pkl/dict_mpfi.pkl','rb'))
        
        mpfi = dict_mpfi[mpurl]
        cat = Config.categories_dict[category]

        """
        try to unpack lines (('i','line'),...) from dict_mpfi into list_lines 
        but if there are no lines then just return a list with the below dict as the only dict
        """

        try:
            mpfi_lines = mpfi[cat]
        except Exception as e:
            parsed_lines_mp = [{
                            'name':dict_name_urls[mpurl]['name'],
                            'full_text':'N/A',
                            'date':'N/A',
                            'orgs':'N/A',
                            'money':float(0),
                            'time':float(0),
                            'role':'N/A',
                            'total_money_ytd':float(0),
                            'total_time_ytd':float(0),
                            'parlukurl':dict_name_urls[mpurl]['parlukurl']
                            }]
            
            try:
                dict_parsed_lines_all = pickle.load(open('./pkl/dict_parsed_lines.pkl','rb'))
                dict_parsed_lines_all[mpurl] = parsed_lines_mp
            except Exception as e:
                dict_parsed_lines_all = {}
                dict_parsed_lines_all[mpurl] = parsed_lines_mp

            dict_parsed_lines_file = open('./pkl/dict_parsed_lines.pkl', 'wb')
            pickle.dump(dict_parsed_lines_all, dict_parsed_lines_file)
            dict_parsed_lines_file.close()    
            
            return parsed_lines_mp

        parsed_lines_mp = []
        i_list = []
        for line in mpfi_lines:
            try:
                indent = line[0]
                full_text = line[1]

                dict_line = {}
                doc = nlp_all_ents(full_text)
                dict_line['name'] = dict_name_urls[mpurl]['name']
                dict_line['full_text'] = full_text
                dict_line['parlukurl'] = dict_name_urls[mpurl]['parlukurl']
                dict_line['date'] = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
                dict_line['orgs'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
                dict_line['money'] = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
                dict_line['time'] = [ent.text for ent in doc.ents if ent.label_ == 'TIME']
                dict_line['role'] = [ent.text for ent in doc.ents if ent.label_ == 'ROLE']

                #print(dict_line)

                dict_line['total_money_ytd'] = Extract.total_money_ytd(dict_line)
                dict_line['total_time_ytd'] = Extract.total_time_ytd(dict_line)

                if dict_line['total_money_ytd'] == 'MANUAL_CHECK' or dict_line['total_time_ytd'] == 'MANUAL_CHECK':
                    del dict_line['total_money_ytd']
                    del dict_line['total_time_ytd']

                    print('\n')
                    print(dict_line['full_text'],'\n')
                    new_date = input('Enter correct date: ')
                    print('\n')
                    new_money = input('Enter correct sum: ')
                    print('\n')
                    new_time = input('Enter correct time: ')
                    print('\n')

                    dict_line['date'] = [new_date]
                    dict_line['money'] = [new_money]
                    dict_line['time'] = [new_time]

                    dict_line['total_money_ytd'] = Extract.total_money_ytd(dict_line)
                    dict_line['total_time_ytd'] = Extract.total_time_ytd(dict_line)

                if indent == 'i':
                    i_fulltext = dict_line['full_text']
                    i_orgs = dict_line['orgs']
                    i_role = dict_line['role']
                    i_list.append('i')

                if indent == 'i2':
                    dict_line['full_text'] = i_fulltext+dict_line['full_text']
                    dict_line['orgs'] = i_orgs+dict_line['orgs']
                    dict_line['role'] = i_role+dict_line['role']
                    i_list.append('i2')

                # formatting date and money fields back to strings (from lists) to export to DataFrame
                dict_line['orgs'] = ', '.join(dict_line['orgs'])
                dict_line['date'] = ', '.join(dict_line['date'])
                dict_line['money'] = ', '.join(dict_line['money'])  
                dict_line['time'] = ', '.join(dict_line['time']) 
                dict_line['role'] = ', '.join(dict_line['role'])

                # finally, append dict_line to list_mpdata
                parsed_lines_mp.append(dict_line)
            except Exception as e:
                #print(line,e)
                pass
        try:
            dict_parsed_lines_all = pickle.load(open('./pkl/dict_parsed_lines.pkl','rb'))
            dict_parsed_lines_all[mpurl] = parsed_lines_mp
        except Exception as e:
            dict_parsed_lines_all = {}
            dict_parsed_lines_all[mpurl] = parsed_lines_mp

        dict_parsed_lines_file = open('./pkl/dict_parsed_lines.pkl', 'wb')
        pickle.dump(dict_parsed_lines_all, dict_parsed_lines_file)
        dict_parsed_lines_file.close()    

    def parse_lines_all(category: str = 'c1') -> None:
        # dicts
        dict_mpfi = pickle.load(open('./pkl/dict_mpfi.pkl','rb'))

        # main logic - if no mpurl is entered then all mpurls in dict_mpfi will be processed
        failed_urls = []
        for mpurl, mpfi in tqdm(dict_mpfi.items(), desc='Extracting'):
            try:
                Extract.parse_lines_mp(mpurl, category)
                #print(mpurl,' SUCCESS')
            except Exception as e:
                failed_urls.append((mpurl,e))
                #print(mpurl,' FAIL')

        return failed_urls

    def manual(mpurl: str, category: str = 'c1') -> None:
        dict_name_urls = pickle.load(open('./pkl/dict_name_urls.pkl','rb'))
        dict_mpfi = pickle.load(open('./pkl/dict_mpfi.pkl'))

        mpfi = dict_mpfi[mpurl]
        cat = Config.categories_dict[category]

        try:
            mpfi_lines = mpfi[cat]
        except Exception as e:
            parsed_lines_mp = [{
                            'name':dict_name_urls[mpurl]['name'],
                            'full_text':'N/A',
                            'date':'N/A',
                            'orgs':'N/A',
                            'money':float(0),
                            'time':float(0),
                            'role':'N/A',
                            'total_money_ytd':float(0),
                            'total_time_ytd':float(0),
                            'parlukurl':dict_name_urls[mpurl]['parlukurl']
                            }]
            #print(mpurl,e)
            return parsed_lines_mp
        
        parsed_lines_mp = []
        failed_lines = []
        i_list = []
        for line in mpfi_lines:
            try:
                indent = line[0]
                full_text = line[1]

                #print('\n')
                #print('line: ',line)
                dict_line = {}
                doc = nlp_all_ents(full_text)
                dict_line['name'] = dict_name_urls[mpurl]['name']
                dict_line['full_text'] = full_text
                dict_line['parlukurl'] = dict_name_urls[mpurl]['parlukurl']
                dict_line['date'] = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
                dict_line['orgs'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
                dict_line['money'] = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
                dict_line['time'] = [ent.text for ent in doc.ents if ent.label_ == 'TIME']
                dict_line['role'] = [ent.text for ent in doc.ents if ent.label_ == 'ROLE']

                #print(dict_line)

                dict_line['total_money_ytd'] = Extract.total_money_ytd(dict_line)
                dict_line['total_time_ytd'] = Extract.total_time_ytd(dict_line)

                if indent == 'i':
                    i_fulltext = dict_line['full_text']
                    i_orgs = dict_line['orgs']
                    i_role = dict_line['role']
                    i_list.append('i')

                if indent == 'i2':
                    dict_line['full_text'] = i_fulltext+dict_line['full_text']
                    dict_line['orgs'] = i_orgs+dict_line['orgs']
                    dict_line['role'] = i_role+dict_line['role']
                    i_list.append('i2')

                # formatting date and money fields back to strings (from lists) to export to DataFrame
                dict_line['orgs'] = ', '.join(dict_line['orgs'])
                dict_line['date'] = ', '.join(dict_line['date'])
                dict_line['money'] = ', '.join(dict_line['money'])  
                dict_line['time'] = ', '.join(dict_line['time']) 
                dict_line['role'] = ', '.join(dict_line['role'])

                # finally, append dict_line to list_mpdata
                parsed_lines_mp.append(dict_line)

            except Exception as e:
                failed_lines.append(line)
        
        for line in failed_lines:
            #print('\n',line,'\n')

            input_org = input('Enter organizations:').split('#')
            input_money = input('Enter money:').split('#')
            input_time = input('Enter hours:').split('#')
            input_date = input('Enter dates:').split('#')
            input_role = input('Enter roles:').split('#')

            dict_line = {}
            dict_line['name'] = dict_name_urls[mpurl]['name']
            dict_line['full_text'] = [line]
            dict_line['parlukurl'] = dict_name_urls[mpurl]['parlukurl']
            dict_line['date'] = input_date
            dict_line['orgs'] = input_org
            dict_line['money'] = input_money
            dict_line['time'] = input_time
            dict_line['role'] = input_role

            dict_line['total_money_ytd'] = Extract.total_money_ytd(dict_line)
            dict_line['total_time_ytd'] = Extract.total_time_ytd(dict_line)

            if indent == 'i':
                i_fulltext = dict_line['full_text']
                i_orgs = dict_line['orgs']
                i_role = dict_line['role']
                i_list.append('i')
            
            if indent == 'i2':
                dict_line['full_text'] = i_fulltext+dict_line['full_text']
                dict_line['orgs'] = i_orgs+dict_line['orgs']
                dict_line['role'] = i_role+dict_line['role']
                i_list.append('i2')
            
            # formatting date and money fields back to strings (from lists) to export to DataFrame
            dict_line['orgs'] = ', '.join(dict_line['orgs'])
            dict_line['date'] = ', '.join(dict_line['date'])
            dict_line['money'] = ', '.join(dict_line['money'])  
            dict_line['time'] = ', '.join(dict_line['time']) 
            dict_line['role'] = ', '.join(dict_line['role'])

            parsed_lines_mp.append(dict_line)
        
        parsed_lines_all = pickle.load(open('./pkl/dict_parsed_lines.pkl','rb'))
        if mpurl in parsed_lines_all.keys():
            del parsed_lines_all[mpurl]
        parsed_lines_all[mpurl] = parsed_lines_mp

        parsed_lines_file = open('./pkl/dict_parsed_lines.pkl', 'wb')
        pickle.dump(parsed_lines_all, parsed_lines_file)
        parsed_lines_file.close()

        # return failed_lines if wanted for additional NER training
        return failed_lines

class Export:
    """
    The Export class contains the functions used to turn parsed_lines into pandas DataFrames and then Excel spreadsheets.
    """    

    def df() -> pd.DataFrame:
        dict_other_info = pickle.load(open('./pkl/dict_other_info.pkl','rb'))
        dict_parsed_lines = pickle.load(open('./pkl/dict_parsed_lines.pkl','rb'))

        # SHEET 1 - MP OVERVIEW
        df_other_info = pd.DataFrame(dict_other_info).transpose()

        # Calculate sum_money_ytd and sum_time_ytd for MP Overview sheet and then add to dict_sum_moneytime { 'mpurl':{'sum_money_ytd':VALUE, 'sum_time_ytd':VALUE}, ...
        dict_sum_moneytime = {}
        for mpurl, parsed_lines in tqdm(dict_parsed_lines.items(), desc="Calculating Total £/hours"):
            list_total_money_ytd = []
            list_total_time_ytd = []
            for line in parsed_lines:
                list_total_money_ytd.append(line['total_money_ytd'])
                list_total_time_ytd.append(line['total_time_ytd'])
            dict_sum_moneytime[mpurl] = {
                'sum_money_ytd': sum([i for i in list_total_money_ytd if type(i) is float or type(i) is int]),
                'sum_time_ytd': sum([i for i in list_total_time_ytd if type(i) is float or type(i) is int])
            }

        df_sum_moneytime = pd.DataFrame(dict_sum_moneytime).transpose()

        df_mp_overview = pd.concat([df_sum_moneytime, df_other_info], axis=1)
        df_mp_overview = df_mp_overview[["name", "sum_money_ytd","sum_time_ytd","basic_salary","lalp_payment","party","constituency","region","country","assumed_office","years_in_office","majority"]]
        df_mp_overview = df_mp_overview.rename(columns = {
            'name':'Name',
            'sum_money_ytd':'Total Earnings YTD (£)',
            'sum_time_ytd': 'Total Hours Worked YTD',
            'basic_salary': 'Basic MP Salary (2020-21)',
            'lalp_payment': 'LALP (2020-21)',
            'party':'Political Party',
            'constituency':'Constituency',
            'region':'Region',
            'country':'Country',
            'assumed_office':'Date Assumed Office',
            'years_in_office': 'Years in Office',
            'majority': 'Majority (%)'
        })
        df_mp_overview = df_mp_overview.set_index('Name')
        df_mp_overview = df_mp_overview.sort_index(ascending=True)
        df_mp_overview = df_mp_overview.fillna(0)

        # SHEET 2 - EARNINGS BREAKDOWN - create df from list_lines and re-name columns
        list_lines = []
        for mplist in tqdm(list(dict_parsed_lines.values()), desc="Adding parsed lines to DataFrame"):
            for line in mplist:
                list_lines.append(line)    

        df_mpfi = pd.DataFrame(list_lines)
        df_earnings_breakdown = df_mpfi[["name","orgs","role","money","time","date","total_money_ytd","total_time_ytd","full_text","parlukurl"]]
        df_earnings_breakdown = df_earnings_breakdown.rename(columns={
            'name':'Name',
            'money':'Earnings (RAW)',
            'time':'Hours worked (RAW)',
            'date':'Date of Earnings',
            'orgs':'Client/Organisation',
            'role':'Role',
            'total_money_ytd':'Earnings YTD (£)',
            'total_time_ytd':'Hours worked YTD',
            'full_text':'Original text',
            'parlukurl':'Source'
        })
        df_earnings_breakdown = df_earnings_breakdown.set_index('Name')
        df_earnings_breakdown = df_earnings_breakdown.sort_index(ascending=True)
        df_earnings_breakdown = df_earnings_breakdown.fillna(0)

        return df_mp_overview, df_earnings_breakdown

    def xlsx(workbook_name: str, func) -> None:
        
        df1, df2 = func()

        writer = pd.ExcelWriter(workbook_name, engine='xlsxwriter')

        workbook = writer.book
        worksheet0 = workbook.add_worksheet('Intro')
        df1.to_excel(writer, sheet_name='MP overview')
        df2.to_excel(writer, sheet_name='Earnings breakdown')

        # Sheet 0
        worksheet0.set_column('A:A', 110)

        title = workbook.add_format({'bold': True})
        sub_title = workbook.add_format({'italic': True})

        worksheet0.write('A1','MP FINANCIAL INTERESTS DATA - STRUCTURED',title)
        worksheet0.write('A2','by Andrew Kyriacos-Messios',sub_title)
        worksheet0.write('A4','Sheet 1: MP Overview - Totals of second job MP earnings and hours worked for the year-to-date',title)
        worksheet0.write('A5','Total Earnings YTD (£) - Total declared employment earnings outside of MP work in the last year',sub_title)
        worksheet0.write('A6','Total Hours Worked YTD - Total declared hours spent working outside of MP work in the last year',sub_title)
        worksheet0.write('A7','Basic MP Salary (2020-21) - Salary received as a Member of Parliament in 2020-21 (not included in Total Earnings YTD)',sub_title)
        worksheet0.write('A8','LALP (2020-21) - Sum received as a London Area Living Payment adjustment in 2020-21',sub_title)
        worksheet0.write('A9','Political Party',sub_title)
        worksheet0.write('A10','Constituency, Region, Country',sub_title)
        worksheet0.write('A11','Date Assumed Office and Years in Office',sub_title)
        worksheet0.write('A12','Majority - % majority won in last election',sub_title)  
        
        worksheet0.write('A14','Sheet 2: Earnings breakdown - A line-by-line breakdown for sources of earnings for each MP',title)
        worksheet0.write('A15','Client, Role',sub_title)
        worksheet0.write('A16','Earnings (RAW) - Payment amount declared by MP (e.g. £150, £2,000 per month)',sub_title)
        worksheet0.write('A17','Hours Worked (RAW) - hours worked declared by MP (e.g. 30 mins, 10 hrs per month)',sub_title)
        worksheet0.write('A18','Date of Earnings - Date on which payment was received or dates between which ongoing work occurred',sub_title)
        worksheet0.write('A19','Earnings YTD (£) - Approximation of % of payment received in the last year (e.g. annual salary * % of year elapsed)',sub_title)
        worksheet0.write('A20','Hours Worked YTD - Approximation of % of hours worked in the last year (e.g. annual time commitment * % of year elapsed)',sub_title)
        worksheet0.write('A21','Original text - Original text from the Register of MP Financial Interests',sub_title)
        worksheet0.write('A22','Source - Hyperlink to the corresponding record in the Register of MP Financial Interests',sub_title)

        worksheet0.write('A24','Journalists and researchers: please double-check data and cross-reference against the original material before publishing.',title)
        worksheet0.write('A26','Questions or feedback? :-) Contact me andrew@andrewkmessios.com',title)

        worksheet0.write('A28','Sources:',title)
        worksheet0.write('A29','https://www.parliament.uk/mps-lords-and-offices/standards-and-financial-interests/parliamentary-commissioner-for-standards/registers-of-interests/register-of-members-financial-interests/')
        worksheet0.write('A30','https://www.parallelparliament.co.uk/')
        worksheet0.write('A31','https://theipsa.org.uk/')
        worksheet0.write('A32','https://en.wikipedia.org/wiki/Diane_Abbott')
        worksheet0.write('A33','https://dbpedia.org/page/')

        # Sheet 1 - MP Overview
        format_all_columns = workbook.add_format({'align':'center'})
        format_currency = workbook.add_format({'align':'center', 'num_format': "£#,##0.00", 'bold': True})
        format_time = workbook.add_format({'align':'center', 'bold': True})
        format_timedate = workbook.add_format({'align':'center', 'num_format': 'dd mmmm yyyy'})

        worksheet1 = writer.sheets['MP overview']

        worksheet1.set_column(0, 0, 25, format_all_columns) # name
        worksheet1.set_column(1, 1, 20, format_currency) # sum_money_ytd
        worksheet1.set_column(2, 2, 20, format_time) # sum_time_ytd
        worksheet1.set_column(3, 3, 22.5, format_currency) # basic_salary
        worksheet1.set_column(4, 4, 15, format_currency) # lalp_payment
        worksheet1.set_column(5, 5, 15, format_all_columns) # party
        worksheet1.set_column(6, 6, 40, format_all_columns) # constituency
        worksheet1.set_column(7, 7, 25, format_all_columns) # region
        worksheet1.set_column(8, 8, 15, format_all_columns) # country
        worksheet1.set_column(9, 9, 20, format_timedate) # assumed_office
        worksheet1.set_column(10, 10, 15, format_all_columns) # years_in_office
        worksheet1.set_column(11, 11, 15, format_all_columns) # majority

        # Sheet 2 - Earnings breakdown
        worksheet2 = writer.sheets['Earnings breakdown']
        worksheet2.set_column(0, 0, 25, format_all_columns) # name
        worksheet2.set_column(1, 1, 40, format_all_columns) # organisation
        worksheet2.set_column(2, 2, 40, format_all_columns) # role
        worksheet2.set_column(3, 3, 20, format_all_columns) # earnings_raw
        worksheet2.set_column(4, 4, 20, format_all_columns) # hours_raw
        worksheet2.set_column(5, 5, 40, format_all_columns) # date
        worksheet2.set_column(6, 6, 20, format_currency) # total_money_ytd
        worksheet2.set_column(7, 7, 20, format_time) # total_time_ytd
        worksheet2.set_column(8, 8, 100, format_all_columns) # full_text
        worksheet2.set_column(9, 9, 100, format_all_columns) # source

        # save and close
        writer.save()

# exec
if __name__ == "__main__":
    # variables
    print('loading dates...')
    date = sys.argv[1]
    date_words = sys.argv[2]
    election_date = '191212'
    election_date_words = '12 December 19'
    mpfi_date = dateutil.parser.parse(date, yearfirst=True)
    mpfi_date_minus_one_year = mpfi_date+datetime.timedelta(-365)

    # spaCy models
    print('loading spaCy models...')
    nlp_trf = spacy.load('en_core_web_trf')
    nlp_time = spacy.load('./ner_models/time/model-best/')
    nlp_money = spacy.load("./ner_models/money/model-best")
    nlp_all_ents = spacy.load("./ner_models/all_ents/model-best")

    # delete old dicts
    print('removing old dicts...')
    for pklpath in ['./pkl/dict_name_urls.pkl','./pkl/dict_mpfi.pkl','./pkl/dict_parsed_lines.pkl']:
        if os.path.isfile(pklpath): os.remove(pklpath)
        else: pass

    print('Scraping links...')
    failed_urls_links = Scrape.links(date)

    print('Scraping MPFI...')
    failed_urls_mpfi = Scrape.mpfi()

    print('Extracting...')
    failed_urls_parse = Extract.parse_lines_all()

    print('Exporting...')
    filename = './excel/'+date+'.xlsx'
    Export.xlsx(filename,Export.df)

    print('\n','*********************************')
    print('failed_urls_links: ',failed_urls_links)
    print('failed_urls_mpfi: ',failed_urls_mpfi)
    print('failed_urls_parse: ',failed_urls_parse)
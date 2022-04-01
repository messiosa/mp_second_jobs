import pickle, requests, os, spacy, time, datefinder, datetime, dateutil, re, num2words
import pandas as pd, numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dateutil.parser import parse
from tqdm import tqdm
from word2number import w2n

#########################
## 1. SCRAPE AND STORE ##
#########################

# Link scrapers
def get_mp_urls_and_names(date): ## {'abbott_diane.htm':'Abbot, Ms Diane', 'abrahams_debbie.htm':'Abrahams, Debbie', ...}
    url = 'https://publications.parliament.uk/pa/cm/cmregmem/'+date+'/contents.htm'

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "lxml")

    p_tags = soup.find_all('p', attrs={'class':None, 'xmlns':'http://www.w3.org/1999/xhtml'})

    dict_mplink_name = {}
    for tag in p_tags:
        try:
            dict_mplink_name[tag.a['href']] = tag.get_text().strip()
        except:
            pass 

    dict_mplink_name_file = open('./pkl/dict_mplink_name.pkl', 'wb')
    pickle.dump(dict_mplink_name, dict_mplink_name_file)
    dict_mplink_name_file.close()

    return dict_mplink_name

def get_pplinks(): ## dict_mplink_pplink {'abbott_diane.htm':'www.parallelparliament.co.uk/mp/diane-abbott', ...}
    dict_mplink_pplink = {}
    dict_mplink_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))

    pp_url = 'https://www.parallelparliament.co.uk/mp/'

    for mplink in tqdm(list(dict_mplink_name.keys())):
        pp_mplink = str(mplink.replace('.htm','').split('_')[1]+'-'+mplink.replace('.htm','').split('_')[0])
        dict_mplink_pplink[mplink] = pp_url+pp_mplink
    
    dict_mplink_pplink['dines_sarah.htm'] = 'https://www.parallelparliament.co.uk/mp/miss-sarah-dines'
    dict_mplink_pplink['qaisar_anum.htm'] = 'https://www.parallelparliament.co.uk/mp/anum-qaisar-javed'
    dict_mplink_pplink['davey_ed.htm'] = 'https://www.parallelparliament.co.uk/mp/edward-davey'

    ## save dict_mplink_pplink to file so I don't have to scrape every time.
    dict_mplink_pplink_file = open('./pkl/dict_mplink_pplink.pkl', 'wb')
    pickle.dump(dict_mplink_pplink, dict_mplink_pplink_file)
    dict_mplink_pplink_file.close()

def get_wikilinks(): ## dict_mplink_wikilink {'abbott_diane.htm':'www.wikipedia.org/Diane_Abbott', ...}
    dict_mplink_wikilink = {}
    dict_mplink_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))

    os.environ['PATH'] = r"C:/selenium_drivers/edgedriver_win64_99"
    driver = webdriver.Edge()

    for mplink in tqdm(list(dict_mplink_name.keys())):
        wiki_url = 'https://en.wikipedia.org/wiki/'+str(mplink.replace('.htm','').split('_')[1]+'_'+mplink.replace('.htm','').split('_')[0]).title()
        driver.get(wiki_url)
        page = driver.page_source
        wiki_soup = BeautifulSoup(page, 'html.parser')

        if wiki_soup.find('a', title='Member of Parliament (United Kingdom)'): ## ensures it's the right page - i.e. it's the MP, not someone else by the same name
            dict_mplink_wikilink[mplink] = wiki_url
        else:
            for _link in ['_(MP)','_(British_politician)','_(politician)','_(English_politician)','_(London_politician)','_(Scottish_politician)','_(Labour_politician)','_(Conservative_politician)']: 
                wiki_url = 'https://en.wikipedia.org/wiki/'+str(mplink.replace('.htm','').split('_')[1]+'_'+mplink.replace('.htm','').split('_')[0]).title()+_link
                wiki_page = requests.get(wiki_url)
                wiki_soup = BeautifulSoup(wiki_page.content, 'html.parser')
                if wiki_soup.find('a', title='Member of Parliament (United Kingdom)'):
                    dict_mplink_wikilink[mplink] = wiki_url
                    break
                else:
                    if _link == '_(Conservative_politician)':
                        dict_mplink_wikilink[mplink] = ''
                        break
                    else:
                        pass
    
    driver.close()
        
    dict_mplink_wikilink['bailey_shaun.htm'] = 'https://en.wikipedia.org/wiki/Shaun_Bailey_(West_Bromwich_MP)'
    dict_mplink_wikilink['brown_nicholas.htm'] = 'https://en.wikipedia.org/wiki/Nick_Brown'
    dict_mplink_wikilink['davies_david-t-c.htm'] = 'https://en.wikipedia.org/wiki/David_T._C._Davies'
    dict_mplink_wikilink['de-cordova_marsha.htm'] = 'https://en.wikipedia.org/wiki/Marsha_de_Cordova'
    dict_mplink_wikilink['dhesi_tanmanjeet-singh.htm'] = 'https://en.wikipedia.org/wiki/Tanmanjeet_Singh_Dhesi'
    dict_mplink_wikilink['donaldson_jeffrey-m.htm'] = 'https://en.wikipedia.org/wiki/Jeffrey_Donaldson'
    dict_mplink_wikilink['dunne_philip.htm'] = 'https://en.wikipedia.org/wiki/Philip_Dunne_(Ludlow_MP)'
    dict_mplink_wikilink['foy_mary-kelly.htm'] = 'https://en.wikipedia.org/wiki/Mary_Foy_(politician)'
    dict_mplink_wikilink['gill_preet-kaur.htm'] = 'https://en.wikipedia.org/wiki/Preet_Gill'
    dict_mplink_wikilink['holmes_paul.htm'] = 'https://en.wikipedia.org/wiki/Paul_Holmes_(Eastleigh_MP)'
    dict_mplink_wikilink['howell_paul.htm'] = 'https://en.wikipedia.org/wiki/Paul_Howell_(MP)'
    dict_mplink_wikilink['jones_david.htm'] = 'https://en.wikipedia.org/wiki/David_Jones_(Clwyd_West_MP)'
    dict_mplink_wikilink['macneil_angus-brendan.htm'] = 'https://en.wikipedia.org/wiki/Angus_MacNeil'
    dict_mplink_wikilink['mccabe_steve.htm'] = 'https://en.wikipedia.org/wiki/Steve_McCabe'
    dict_mplink_wikilink['mccarthy_kerry.htm'] = 'https://en.wikipedia.org/wiki/Kerry_McCarthy'
    dict_mplink_wikilink['mccartney_jason.htm'] = 'https://en.wikipedia.org/wiki/Jason_McCartney_(politician)'
    dict_mplink_wikilink['mccartney_karl.htm'] = 'https://en.wikipedia.org/wiki/Karl_McCartney'
    dict_mplink_wikilink['mcdonagh_siobhain.htm'] = 'https://en.wikipedia.org/wiki/Siobhain_McDonagh'
    dict_mplink_wikilink['mcdonald_andy.htm'] = 'https://en.wikipedia.org/wiki/Andy_McDonald_(politician)'
    dict_mplink_wikilink['mcdonald_stewart-malcolm.htm'] = 'https://en.wikipedia.org/wiki/Stewart_McDonald_(politician)'
    dict_mplink_wikilink['mcdonald_stuart-c.htm'] = 'https://en.wikipedia.org/wiki/Stuart_McDonald_(Scottish_politician)'
    dict_mplink_wikilink['mcdonnell_john.htm'] = 'https://en.wikipedia.org/wiki/John_McDonnell'
    dict_mplink_wikilink['mcfadden_pat.htm'] = 'https://en.wikipedia.org/wiki/Pat_McFadden'
    dict_mplink_wikilink['mcginn_conor.htm'] = 'https://en.wikipedia.org/wiki/Conor_McGinn'
    dict_mplink_wikilink['mcgovern_alison.htm'] = 'https://en.wikipedia.org/wiki/Alison_McGovern'
    dict_mplink_wikilink['mckinnell_catherine.htm'] = 'https://en.wikipedia.org/wiki/Catherine_McKinnell'
    dict_mplink_wikilink['mclaughlin_anne.htm'] = 'https://en.wikipedia.org/wiki/Anne_McLaughlin'
    dict_mplink_wikilink['mcmahon_jim.htm'] = 'https://en.wikipedia.org/wiki/Jim_McMahon_(politician)'
    dict_mplink_wikilink['mcmorrin_anna.htm'] = 'https://en.wikipedia.org/wiki/Anna_McMorrin'
    dict_mplink_wikilink['mcnally_john.htm'] = 'https://en.wikipedia.org/wiki/John_McNally_(politician)'
    dict_mplink_wikilink['mcpartland_stephen.htm'] = 'https://en.wikipedia.org/wiki/Stephen_McPartland'
    dict_mplink_wikilink['moore_robbie.htm'] = 'https://en.wikipedia.org/wiki/Robbie_Moore_(MP)'
    dict_mplink_wikilink['neill_robert.htm'] = 'https://en.wikipedia.org/wiki/Bob_Neill'
    dict_mplink_wikilink['obrien_neil.htm'] = 'https://en.wikipedia.org/wiki/Neil_O%27Brien'
    dict_mplink_wikilink['ohara_brendan.htm'] = 'https://en.wikipedia.org/wiki/Brendan_O%27Hara'
    dict_mplink_wikilink['paisley_ian.htm'] = 'https://en.wikipedia.org/wiki/Ian_Paisley_Jr'
    dict_mplink_wikilink['wood_mike.htm'] = 'https://en.wikipedia.org/wiki/Mike_Wood_(Conservative_politician)'

    ## save dict_mplink_wikilink to file so I don't have to scrape every time.
    dict_mplink_wikilink_file = open('./pkl/dict_mplink_wikilink.pkl', 'wb')
    pickle.dump(dict_mplink_wikilink, dict_mplink_wikilink_file)
    dict_mplink_wikilink_file.close()

def get_ipsalinks(): ## dict_mplink_ipsalink {'abbott_diane.htm':'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/diane-abbott/172', ...}
    url = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp'
    os.environ['PATH'] = r"C:/selenium_drivers/chromedriver_win32"

    driver = webdriver.Chrome()
    driver.get(url)

    buttons = driver.find_elements_by_class_name('govuk-accordion__section-button')
    for button in buttons:
        driver.implicitly_wait(30)
        button.click()
    
    driver.implicitly_wait(30)
    links = driver.find_elements_by_class_name('govuk-link')
    ipsalinks = []
    for link in links:
        try:
            if '/mp-staffing-business-costs/your-mp/' in link.get_attribute('href'):
                ipsalinks.append(link.get_attribute('href'))
            else:
                pass
        except:
            pass
    
    driver.implicitly_wait(30)
    dict_mplink_ipsalink = {}
    for link in ipsalinks:
        ipsa_name = ''.join([i for i in link.replace('https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/','').replace('/','') if not i.isdigit()])
        dict_mplink_ipsalink[ipsa_name.split('-')[1]+'_'+ipsa_name.split('-')[0]+'.htm'] = link

    ## delete old mps from dict_mplink_ipsalink
    driver.implicitly_wait(30)
    dict_mplink_wikilink = pickle.load(open('./pkl/dict_mplink_wikilink.pkl','rb'))
    new_links = list(set(list(dict_mplink_ipsalink.keys()))-set(list(dict_mplink_wikilink.keys())))
    for link in list(dict_mplink_ipsalink.keys()):
        if link in new_links:
            del dict_mplink_ipsalink[link]

    ## append correct ipsa links
    driver.implicitly_wait(30)
    dict_mplink_ipsalink['ahmad-khan_imran.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/imran-ahmad-khan/4841'
    dict_mplink_ipsalink['allin-khan_rosena.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/rosena-allin-khan/4573'
    dict_mplink_ipsalink['begley_órfhlaith.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/%C3%B3rfhlaith-begley/4697'
    dict_mplink_ipsalink['clarke-smith_brendan.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/brendan-clarke-smith/4756'
    dict_mplink_ipsalink['clifton-brown_geoffrey.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/geoffrey-clifton-brown/249'
    dict_mplink_ipsalink['coffey_therese.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/th%C3%A9r%C3%A8se-coffey/4098'
    dict_mplink_ipsalink['davies-jones_alex.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/alex-davies-jones/4849'
    dict_mplink_ipsalink['davies_david-t-c.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/david-t-c-davies/1545'
    dict_mplink_ipsalink['de-cordova_marsha.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/marsha-de-cordova/4676'
    dict_mplink_ipsalink['dhesi_tanmanjeet-singh.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/tanmanjeet-singh-dhesi/4638'
    dict_mplink_ipsalink['docherty-hughes_martin.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/martin-docherty-hughes/4374'
    dict_mplink_ipsalink['donaldson_jeffrey-m.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/jeffrey-m-donaldson/650'
    dict_mplink_ipsalink['doyle-price_jackie.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/jackie-doyle-price/4065'
    dict_mplink_ipsalink['duncan-smith_iain.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/iain-duncan-smith/152'
    dict_mplink_ipsalink['foy_mary-kelly.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/mary-kelly-foy/4753'
    dict_mplink_ipsalink['gill_preet-kaur.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/preet-kaur-gill/4603'
    dict_mplink_ipsalink['hart_sally-ann.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/sally-ann-hart/4842'
    dict_mplink_ipsalink['heaton-harris_chris.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/chris-heaton-harris/3977'
    dict_mplink_ipsalink['lewell-buck_emma.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/emma-lewell-buck/4277'
    dict_mplink_ipsalink['liddell-grainger_ian.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/ian-liddell-grainger/1396'
    dict_mplink_ipsalink['long-bailey_rebecca.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/rebecca-long-bailey/4396'
    dict_mplink_ipsalink['macneil_angus-brendan.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/angus-brendan-macneil/1546'
    dict_mplink_ipsalink['mcdonald_stewart-malcolm.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/stewart-malcolm-mcdonald/4461'
    dict_mplink_ipsalink['mcdonald_stuart-c.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/stuart-c-mcdonald/4393'
    dict_mplink_ipsalink['morris_anne-marie.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/anne-marie-morris/4249'
    dict_mplink_ipsalink['mumby-croft_holly.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/holly-mumby-croft/4867'
    dict_mplink_ipsalink['obrien_neil.htm'] = "https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/neil-o'brien/4679"
    dict_mplink_ipsalink['ohara_brendan.htm'] = "https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/brendan-o'hara/4371"
    dict_mplink_ipsalink['oppong-asare_abena.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/abena-oppong-asare/4820'
    dict_mplink_ipsalink['rees-mogg_jacob.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/jacob-rees-mogg/4099'
    dict_mplink_ipsalink['ribeiro-addy_bell.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/bell-ribeiro-addy/4764'
    dict_mplink_ipsalink['russell-moyle_lloyd.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/lloyd-russell-moyle/4615'
    dict_mplink_ipsalink['saville-roberts_liz.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/liz-saville-roberts/4521'
    dict_mplink_ipsalink['thomas-symonds_nick.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/nick-thomas-symonds/4479'
    dict_mplink_ipsalink['trevelyan_anne-marie.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/anne-marie-trevelyan/4531'
    dict_mplink_ipsalink['zahawi_nadhim.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/nadhim-zahawi/4113'
    dict_mplink_ipsalink['zeichner_daniel.htm'] = 'https://www.theipsa.org.uk/mp-staffing-business-costs/your-mp/daniel-zeichner/4382'

    ## save dict_mplink_pplink to file so I don't have to scrape every time.
    driver.implicitly_wait(30)
    dict_mplink_ipsalink_file = open('./pkl/dict_mplink_ipsalink.pkl', 'wb')
    pickle.dump(dict_mplink_ipsalink, dict_mplink_ipsalink_file)
    dict_mplink_ipsalink_file.close()

    driver.close()
    return dict_mplink_ipsalink

def get_dblinks(): ## dict_mplink_dblink {'abbott_diane.htm':'https://dbpedia.org/page/Diane_Abbott', ...}
    dict_mplink_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))
    dict_mplink_wikilink = pickle.load(open('./pkl/dict_mplink_wikilink.pkl','rb'))

    dict_mplink_dblink = {}
    for mplink in dict_mplink_name.keys():
        dict_mplink_dblink[mplink] = dict_mplink_wikilink[mplink].replace('https://en.wikipedia.org/wiki/','https://dbpedia.org/page/')
    
    ## save dict_mplink_pplink to file so I don't have to scrape every time.
    dict_mplink_dblink_file = open('./pkl/dict_mplink_dblink.pkl', 'wb')
    pickle.dump(dict_mplink_dblink, dict_mplink_dblink_file)
    dict_mplink_dblink_file.close()

    return dict_mplink_dblink

# Main scrapers
date = '220228'
headings_dict = {
    'h1': '1. Employment and earnings',
    'h2a': '2. (a) Support linked to an MP but received by a local party organisation or indirectly via a central party organisation',
    'h2b': '2. (b) Any other support not included in Category 2(a)',
    'h3': '3. Gifts, benefits and hospitality from UK sources',
    'h4': '4. Visits outside the UK',
    'h5': '5. Gifts and benefits from sources outside the UK',
    'h6': '6. Land and property portfolio: (i) value over £100,000 and/or (ii) giving rental income of over £10,000 a year',
    'h7i': '7. (i) Shareholdings: over 15% of issued share capital',
    'h7ii': '7. (ii) Other shareholdings, valued at more than £70,000',
    'h8': '8. Miscellaneous',
    'h9': '9. Family members employed and paid from parliamentary expenses',
    'h10': '10. Family members engaged in lobbying the public sector on behalf of a third party or client'
}

def scrape_mpinfo_political(indv_mplink=None): ## dict_mpinfo_political
    dict_mplink_name = pickle.load(open("./pkl/dict_mplink_name.pkl", "rb"))
    dict_mplink_wikilink = pickle.load(open("./pkl/dict_mplink_wikilink.pkl", "rb"))
    dict_mplink_pplink = pickle.load(open("./pkl/dict_mplink_pplink.pkl", "rb"))
    dict_mplink_ipsalink = pickle.load(open('./pkl/dict_mplink_ipsalink.pkl','rb'))
    dict_constituencies = pickle.load(open('./pkl/dict_constituencies.pkl','rb'))

    def indv_mp(mplink):        
        # SCRAPE PARALLELPARLIAMENT.CO.UK
        os.environ['PATH'] = r"C:/selenium_drivers/edgedriver_win64_99"
        driver = webdriver.Edge()

        pp_url = dict_mplink_pplink[mplink]
        driver.get(pp_url)
        party = driver.find_element(By.CLASS_NAME, 'card-header.text-center').find_element(By.TAG_NAME, 'h4').text.replace('\n','').split(' - ')[0].strip()
        constituency = driver.find_element(By.CLASS_NAME, 'card-header.text-center').find_element(By.TAG_NAME, 'h4').text.replace('\n','').split(' - ')[1].strip()
        region, country = dict_constituencies[constituency]

        print('pp links: ',party,constituency,region,country)

        # SCRAPE THEIPSA.ORG.UK/MP-STAFFING-BUSINESS-COSTS/YOUR-MP/
        ipsa_url = dict_mplink_ipsalink[mplink]
        driver.get(ipsa_url)

        assumed_office = parse(driver.find_element(By.CLASS_NAME,'govuk-body-l').text, fuzzy=True).date()
        years_in_office = datetime.datetime.now().year - assumed_office.year

        buttons = driver.find_elements(By.CLASS_NAME,'govuk-accordion__section-button')
        for button in buttons:
            if button.text == '2020 to 2021':
                button.click()

        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for button in buttons:
            if button.text == 'MP Payroll information':
                button.click()

        tables = driver.find_elements(By.TAG_NAME,'table')
        for table in tables:
            if 'Basic salary received during 2020 - 2021' in table.text:
                payroll_table = table
        for row in payroll_table.find_elements(By.TAG_NAME,'tr'):
            if 'Basic salary received during 2020 - 2021' in row.text:
                basic_salary = row.text.replace('Basic salary received during 2020 - 2021','').strip()
            elif 'Amount paid to MP as LALP during 2020 to 2021' in row.text:
                lalp_payment = row.text.replace('Amount paid to MP as LALP during 2020 to 2021','').strip()
        
        # SCRAPE WIKIPEDIA
        wiki_url = dict_mplink_wikilink[mplink]
        driver.get(wiki_url)

        for row in driver.find_elements(By.TAG_NAME,'tr'):
            if 'Majority' in row.text:
                majority = row.text.replace('Majority','').strip().split(' ')[1].replace('(','').replace('%)','')
        
        print('wiki: ',majority)

        # Close driver
        driver.close()

        #3 ADD TO DICTIONARY
        dict_indv_mp = {
            'party': party,
            'constituency': constituency,
            'region': region,
            'country': country,
            'assumed_office': assumed_office,
            'years_in_office': years_in_office,
            'majority': majority,
            'basic_salary': float(basic_salary.replace('£','').replace(',','').strip()),
            'lalp_payment': float(lalp_payment.replace('£','').replace(',','').strip())
        }

        print('dict_indv_mp: ',dict_indv_mp)

        return dict_indv_mp

    if indv_mplink == None:
        dict_mpinfo_political = {} # {'name from link_name_dict': {...}}
        failed_urls = []
        for mplink in tqdm(list(dict_mplink_name.keys())):
            try:
                dict_mpinfo_political[dict_mplink_name[mplink]] = indv_mp(mplink)
            except Exception as e:
                failed_urls.append((mplink,e))
        
        dict_mpinfo_political_file = open('./pkl/dict_mpinfo_political.pkl', 'wb')
        pickle.dump(dict_mpinfo_political, dict_mpinfo_political_file)
        dict_mpinfo_political_file.close()

    else:
        dict_mpinfo_political = pickle.load(open('./pkl/dict_mpinfo_political.pkl','rb'))
        failed_urls = []
        try:
            dict_mpinfo_political[dict_mplink_name[indv_mplink]] = indv_mp(indv_mplink)
        except Exception as e:
            failed_urls.append((indv_mplink,e))

        dict_mpinfo_political_file = open('./pkl/dict_mpinfo_political.pkl', 'wb')
        pickle.dump(dict_mpinfo_political, dict_mpinfo_political_file)
        dict_mpinfo_political_file.close()  

    return dict_mpinfo_political, failed_urls

def scrape_parluk_for_mpfi(date, parluk_url): ## {'1. Employment and earnings': [('i', 'line'), ('i2', 'line), ...], '2. xyz': [(),()], ...}
    os.environ['PATH'] = r"C:/selenium_drivers/edgedriver_win64_99"

    driver = webdriver.Edge()
    driver.get('https://publications.parliament.uk/pa/cm/cmregmem/'+date+'/'+parluk_url)
    content = driver.page_source
    soup = BeautifulSoup(content, 'html.parser')

    dict_mpfi = {}
    all_text = soup.find('div', id='mainTextBlock').find_all('p')[1:]
    if all_text[0].text == 'Nil':
        dict_mpfi = None
    else:
        for p in all_text:
            if p.text in headings_dict.values():
                h = p.text
                h_list = []
            else:
                try:
                    if p['class'][0] == 'indent':
                        h_list.append(('i', p.text))
                    elif p['class'][0] == 'indent2':
                        h_list.append(('i2', p.text))
                    elif p['class'][0] == 'indent3':
                        h_list.append(('i3', p.text))
                except:
                    pass
            dict_mpfi[h] = h_list
    
    mp_file_name = parluk_url.replace('.htm','')

    if os.path.exists('./pkl/mpfi/'+date):
        pass
    else: 
        os.makedirs('./pkl/mpfi/'+date)
    
    dict_mpfi_file = open('./pkl/mpfi/'+date+'/'+mp_file_name+'.pkl', 'wb')
    pickle.dump(dict_mpfi, dict_mpfi_file)
    dict_mpfi_file.close()

def scrape_for_all_mpfi(date):
    dict_parlurl_mpname = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))

    for url in tqdm(dict_parlurl_mpname.keys()):
        pklpath = './pkl/mpfi/'+date+'/'+url.replace('.htm','')+'.pkl'
        if os.path.exists(pklpath): ## check if url has already been scraped
            pass
        else:
            print(url)
            try:
                scrape_parluk_for_mpfi(date, url)
            except:
                pass
            time.sleep(15) ## wait 15 seconds to avoid getting blocked

#scrape_for_all_mpfi(date)
dict_mpinfo_poltical, failed_urls = scrape_mpinfo_political()

##############
## 2. PARSE ##
##############

# Main parsers
def parse_mpfi_pkl(date, parluk_url, heading_ref): # returns list of dicts (dict for each line) for a single MP

    #################################
    ## PARSE_MPFIPKL SUB-FUNCTIONS ##
    #################################

    def date_processor(dict_line): ## dict_line => start_date_ytd and end_date_ytd

        # filter out any date lists with more than 1 element
        if len(dict_line['date']) > 1:
            print('len dict_date: > 1')    
            dict_date = max(dict_line['date'], key=len).lower()     # takes longest item in dict_date as new dict_date                    
        else:
            print('len dict_date: <= 1')
            dict_date = dict_line['date'][0].lower()

        print('dict_date: ',dict_date)
        
        # figure out structure of date (e.g. single date or 'from until', 'until', 'from', 'to') and find start_date_ytd/end_date_ytd
        if 'from' in dict_date or 'until' in dict_date or ' to ' in dict_date or 'onwards' in dict_date or 'between' in dict_date:
            print('single date: false')        
            
            keyword_list = []
            for keyword in ['from', 'until', ' to ', 'onwards', 'between', ' and ', 'since']:
                if keyword in dict_date:
                    keyword_list.append(keyword)
                else:
                    pass
            
            print('keyword_list: ',keyword_list)
            
            # create start_date and end_date
            if len(keyword_list) == 1:
                if 'from' in keyword_list:
                    print('1 / from: true')
                    start_date = [i for i in datefinder.find_dates(dict_date.replace('from',''))][0]
                    end_date = mpfi_date
                if 'since' in keyword_list:
                    print('1 / from: true')
                    start_date = [i for i in datefinder.find_dates(dict_date.replace('since',''))][0]
                    end_date = mpfi_date                
                elif 'onwards' in keyword_list:
                    print('1 / onwards: true')
                    start_date = [i for i in datefinder.find_dates(dict_date.replace('onwards',''))][0]
                    end_date = mpfi_date            
                elif 'until' in keyword_list:
                    print('1 / until: true')
                    split_dates = [i for i in re.split('until', dict_date) if i != '']
                    if len(split_dates) == 1:
                        if 'further notice' in dict_date:
                            print('1 / further notice: true')
                            start_date = mpfi_date_minus_one_year
                            end_date = mpfi_date
                        else:
                            if [i for i in datefinder.find_dates(split_dates[0])][0] < mpfi_date_minus_one_year:
                                start_date = [i for i in datefinder.find_dates(split_dates[0])][0]
                                end_date = [i for i in datefinder.find_dates(split_dates[0])][0]
                            else:
                                start_date = mpfi_date_minus_one_year
                                end_date = [i for i in datefinder.find_dates(split_dates[0])][0]
                    if len(split_dates) == 2:
                        start_date = [i for i in datefinder.find_dates(split_dates[0])][0]
                        if 'further notice' in dict_date:
                            print('1 / further notice: true')
                            end_date = mpfi_date
                        else:
                            end_date = [i for i in datefinder.find_dates(split_dates[1])][0]
                elif ' to ' in keyword_list:
                    print('1 / to: true')
                    split_dates = re.split('to', dict_date)
                    start_date = [i for i in datefinder.find_dates(split_dates[0])][0]
                    end_date = [i for i in datefinder.find_dates(split_dates[1])][0]
                elif 'between' in keyword_list:
                    print('1 / between: true')
                    start_date = [i for i in datefinder.find_dates(dict_date)][0]
                    end_date = [i for i in datefinder.find_dates(dict_date)][0]
            elif len(keyword_list) == 2:
                if 'from' and 'until' in keyword_list:
                    print('2 / from and until: true')
                    split_dates = re.split('until', dict_date)
                    start_date = [i for i in datefinder.find_dates(split_dates[0].replace('from',''))][0]
                    if 'further notice' in split_dates[1]:
                        print('2 / further notice: true')
                        end_date = mpfi_date
                    else:
                        end_date = [i for i in datefinder.find_dates(split_dates[1])][0]
                elif 'from' and ' to ' in keyword_list:
                    print('2 / from and to: true')
                    split_dates = re.split(' to ', dict_date)
                    start_date = [i for i in datefinder.find_dates(split_dates[0].replace('from',''))][0]
                    end_date = [i for i in datefinder.find_dates(split_dates[1])][0]
                elif 'from' and 'onwards' in keyword_list:
                    print('2 / from and onwards: true')
                    start_date = [i for i in datefinder.find_dates(dict_date.replace('from','').replace('onwards',''))][0]
                    end_date = mpfi_date
                elif 'between' and ' and ' in keyword_list:
                    print('2 / between and and: true')
                    split_dates = re.split(' and ', dict_date)
                    try:
                        start_date = [i for i in datefinder.find_dates(split_dates[0].replace('between',''))][0]
                        end_date = [i for i in datefinder.find_dates(split_dates[1])][0]        
                    except:
                        end_date = [i for i in datefinder.find_dates(split_dates[1])][0]   
                        start_date = end_date                 
            else:
                print('0 / other: true')
                start_date_ytd = None
                end_date_ytd = None
                return start_date_ytd, end_date_ytd

            # calculate start_date_ytd and end_date_ytd
            print('start_date / end_date:',start_date,end_date)
            if start_date <= mpfi_date_minus_one_year and end_date <= mpfi_date_minus_one_year:
                print('1')
                start_date_ytd = mpfi_date_minus_one_year
                end_date_ytd = mpfi_date_minus_one_year
            elif start_date <= mpfi_date_minus_one_year and end_date >= mpfi_date_minus_one_year and end_date <= mpfi_date:
                print('2')
                start_date_ytd = mpfi_date_minus_one_year
                end_date_ytd = end_date
            elif start_date <= mpfi_date_minus_one_year and end_date > mpfi_date:
                print('3')
                start_date_ytd = mpfi_date_minus_one_year
                end_date_ytd = mpfi_date
            elif start_date >= mpfi_date_minus_one_year and start_date <= mpfi_date and end_date >= mpfi_date_minus_one_year and end_date <= mpfi_date:
                print('4')
                start_date_ytd = start_date
                end_date_ytd = end_date              
            elif start_date >= mpfi_date_minus_one_year and start_date <= mpfi_date and end_date > mpfi_date:
                print('5')
                start_date_ytd = start_date
                end_date_ytd = mpfi_date
            elif start_date > mpfi_date and end_date > mpfi_date:
                print('6')
                start_date_ytd = mpfi_date
                end_date_ytd = mpfi_date

            print('start_date_ytd / end_date_ytd:',start_date_ytd,end_date_ytd)
            return start_date_ytd, end_date_ytd
        else:
            print('single date: true')
            start_date = [i for i in datefinder.find_dates(dict_date)][0]
            end_date = [i for i in datefinder.find_dates(dict_date)][0]
            print('start_date / end_date:',start_date,end_date)

            # calculate start_date_ytd and end_date_ytd
            if start_date < mpfi_date_minus_one_year:
                start_date_ytd = None
            else:
                start_date_ytd = start_date
            
            if end_date > mpfi_date:
                end_date_ytd = None
            else:
                end_date_ytd = end_date

            print('start_date_ytd / end_date_ytd:',start_date_ytd,end_date_ytd)
            return start_date_ytd, end_date_ytd

    def total_money_ytd(dict_line): ## dict_line => total_money_ytd
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
                print("len dict_line['money']: > 1")
                total_money_ytd = 'MANUAL_CHECK'
            else:
                print("len dict_line['money']: <= 1")
                try:
                    money_raw_value = float(''.join([i for i in dict_line['money'][0] if i.isdigit() is True or i == '.']))
                except:
                    total_money_ytd = 'MANUAL_CHECK'
                    return total_money_ytd
                print('money_raw_value:',money_raw_value)
                money_period = nlp_money(dict_line['money'][0]).ents[0].label_
                print('money_period:',money_period)

                # for dict_line['total_money_ytd']: calculate total_money_ytd
                if money_period == '1':                                         # for non-recurring sums, check if the sum is in date
                    print('money_period: 1')
                    try:
                        date_parsed = dateutil.parser.parse(dict_line['date'][0])
                        if date_parsed < mpfi_date_minus_one_year:
                            total_money_ytd = float(0)
                        else:
                            total_money_ytd = money_raw_value
                    except:
                        print('money_period: not 1')
                        start_date_ytd, end_date_ytd = date_processor(dict_line)
                        total_money_for_one_year = money_raw_value*period_dict[money_period]
                        print('start_date_ytd, end_date_ytd: ',start_date_ytd, end_date_ytd)
                        try:
                            percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                            if percentage_of_year_elapsed == 0.0:                    # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                                print('percentage_of_year_elapsed: 0')
                                total_money_ytd = float(0)
                            else:
                                print('percentage_of_year_elapsed: not 0')
                                total_money_ytd = round(total_money_for_one_year*percentage_of_year_elapsed)
                        except:                                                       # if date_processor returns None's
                            total_money_ytd = 'MANUAL_CHECK'
                else:                                                                 # for recurring sums (i.e. D, W, 2W, M, Q, Y)
                    print('money_period: not 1')
                    start_date_ytd, end_date_ytd = date_processor(dict_line)
                    total_money_for_one_year = money_raw_value*period_dict[money_period]
                    try:
                        percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                        print('percentage_of_year_elapsed:',percentage_of_year_elapsed)
                        if percentage_of_year_elapsed == 0.0:                         # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                            print('percentage_of_year_elapsed == 0')
                            total_money_ytd = float(0)
                        else:
                            print('percentage_of_year_elapsed != 0')
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
    
    def total_time_ytd(dict_line): ## dict_line => total_money_ytd

        ##################################
        ## TOTAL_TIME_YTD SUB-FUNCTIONS ##
        ##################################

        def numwords(text):
            try: 
                float(re.findall(r'-?\d+\.?\d*', text)[0])
            except:
                try:
                    word_num = num2words(w2n.word_to_num(text))
                    print(word_num)
                    text = text.replace(word_num,str(w2n.word_to_num(word_num)))      # turning 'two days ...' into '2 days...'
                    print(text)
                except:
                    pass
            
            if 'a year' in text:                                                    
                text = text.replace('a year', 'per year')       # nlp_trf doesn't like 'a year' for some reason...

            return text

        def time_processor(text): # dict_line['time'] > time_raw_value
            # replace any word-nums with nums
            text = numwords(text)

            # extract date and remove 'per month' etc
            doc_time = nlp_trf(text)
            print('doc_time: ',doc_time)
            try:                                                                       
                time = [i for i in doc_time.ents if i.label_ == 'TIME'][0].text
            except:
                try:                                                                    # times given in days (e.g. '8 days per month') are recognised as 'DATE' ents by nlp_trf
                    time = [i for i in doc_time.ents if i.label_ == 'DATE'][0].text
                except:                                     
                    time = 'MANUAL_CHECK'
                    print('time (MANUAL_CHECK): ',time)
                    return time
            print('time:',time)   

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
            print('time_raw_value:',time_raw_value)
            
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
            print('list_mhd:',list_mhd)

            if 'm' in list_mhd and 'h' in list_mhd:
                print('m and h: true')
                list_time_values = [float(s) for s in re.findall(r'-?\d+\.?\d*', time_raw_value)]
                hrs = list_time_values[0]
                mins = list_time_values[1]
            elif 'h' in list_mhd and 'm' not in list_mhd:
                print('h: true')
                try:
                    hrs = float(re.findall(r'-?\d+\.?\d*', time_raw_value)[0])
                except:                                                         # PROCESS FOR WORD-NUMBERS (E.G.'SIX HOURS')
                    pass
                mins = float(0)
            elif 'm' in list_mhd and 'h' not in list_mhd:
                print('m: true')
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
            print(time_raw_value)

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
                print("len dict_line['time']: > 1")
                total_time_ytd = 'MANUAL_CHECK'
            else:
                print("len dict_line['time']: <= 1")
                time_raw_value = time_processor(dict_line['time'][0])
                print('time_raw_value:',time_raw_value)
                if time_raw_value == 'MANUAL_CHECK':
                    total_time_ytd = 'MANUAL_CHECK'
                    return total_time_ytd
                time_period = nlp_time(dict_line['time'][0]).ents[0].label_
                print('time_period:',time_period)

                # for dict_line['total_money_ytd']: calculate total_money_ytd
                if time_period == '1':                                         # for non-recurring sums, check if the sum is in date
                    print('time_period: 1')
                    try:
                        date_parsed = [i for i in datefinder.find_dates(dict_line['date'][0])][0]
                        print('date_parsed:',date_parsed)
                        if date_parsed < mpfi_date_minus_one_year:
                            total_time_ytd = float(0)
                        else:
                            total_time_ytd = time_raw_value
                    except:
                        print('time_period: not 1')
                        start_date_ytd, end_date_ytd = date_processor(dict_line)
                        total_time_for_one_year = time_raw_value*period_dict[time_period]
                        print('start_date_ytd, end_date_ytd: ',start_date_ytd, end_date_ytd)
                        try:
                            percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                            if percentage_of_year_elapsed == 0.0:                    # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                                print('percentage_of_year_elapsed: 0')
                                total_time_ytd = float(0)
                            else:
                                print('percentage_of_year_elapsed: not 0')
                                total_time_ytd = round(total_time_for_one_year*percentage_of_year_elapsed, 2)
                        except:                                                       # if date_processor returns None's
                            total_time_ytd = None
                else:                                                                 # for recurring sums (i.e. D, W, 2W, M, Q, Y)
                    print('money_period: not 1')
                    start_date_ytd, end_date_ytd = date_processor(dict_line)
                    total_time_for_one_year = time_raw_value*period_dict[time_period]
                    try:
                        percentage_of_year_elapsed = (end_date_ytd-start_date_ytd).days/365
                        print('percentage_of_year_elapsed:',percentage_of_year_elapsed)
                        if percentage_of_year_elapsed == 0.0:                         # for a single date, start_date_ytd = end_date_ytd and percentage_.. = 0
                            print('percentage_of_year_elapsed == 0')
                            total_time_ytd = float(0)
                        else:
                            print('percentage_of_year_elapsed != 0')
                            total_time_ytd = round(total_time_for_one_year*percentage_of_year_elapsed, 2)
                    except:                                                          # if date_processor returns None's
                        total_time_ytd = None

        return total_time_ytd  

    #################################
    ## PARSE_MPFIPKL MAIN FUNCTION ##
    #################################

    # turn parluk_url into pkl and save in variable
    dict_parlukurl_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))
    pklpath = './pkl/mpfi/'+date+'/'+parluk_url.replace('.htm','')+'.pkl'
    dict_pkl = pickle.load(open(pklpath, 'rb'))
    try:
        lines = dict_pkl[heading_ref] ## list of tuples from pkl [('i', 'line'), ('i', 'line'), ...]
    except:
        list_mpdata = [{'name':dict_parlukurl_name[parluk_url],
                        'full_text':'N/A',
                        'date':'N/A',
                        'orgs':'N/A',
                        'money':float(0),
                        'time':float(0),
                        'role':'N/A',
                        'total_money_ytd':float(0),
                        'total_time_ytd':float(0)
                        }]
        return list_mpdata
    
    # set up variables needed for dict_line
    nlp = spacy.load("./ner_models/all_ents/model-best")
    nlp_money = spacy.load('./ner_models/money/model-best')
    nlp_time = spacy.load('./ner_models/time/model-best')
    nlp_trf = spacy.load('en_core_web_trf')
    dict_parlukurl_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb')) # needed for dict_line['name']
    mpfi_date = dateutil.parser.parse(date, yearfirst=True)
    mpfi_date_minus_one_year = mpfi_date+datetime.timedelta(-365)

    # begin creating dict_line
    list_mpdata = []
    i_list = []
    for line in lines:
        print('\n')
        print('line: ',line)
        dict_line = {}
        doc = nlp(line[1])
        dict_line['name'] = dict_parlukurl_name[parluk_url]
        dict_line['full_text'] = [line[1]]
        dict_line['date'] = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        dict_line['orgs'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        dict_line['money'] = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
        dict_line['time'] = [ent.text for ent in doc.ents if ent.label_ == 'TIME']
        dict_line['role'] = [ent.text for ent in doc.ents if ent.label_ == 'ROLE']

        print(dict_line)

        dict_line['total_money_ytd'] = total_money_ytd(dict_line)
        dict_line['total_time_ytd'] = total_time_ytd(dict_line)

        print("dict_line['total_money_ytd']",dict_line['total_money_ytd'])
        print("dict_line['total_time_ytd']",dict_line['total_time_ytd'])

        if line[0] == 'i':
            i_fulltext = dict_line['full_text']
            i_orgs = dict_line['orgs']
            i_role = dict_line['role']
            i_list.append('i')
    
        if line[0] == 'i2':
            dict_line['full_text'] = i_fulltext+dict_line['full_text']
            dict_line['orgs'] = i_orgs+dict_line['orgs']
            dict_line['role'] = i_role+dict_line['role']
            i_list.append('i2')

        # formatting date and money fields back to strings (from lists) to export to DataFrame
        dict_line['full_text'] = ', '.join(dict_line['full_text'])
        dict_line['orgs'] = ', '.join(dict_line['orgs'])
        dict_line['date'] = ', '.join(dict_line['date'])
        dict_line['money'] = ', '.join(dict_line['money'])  
        dict_line['time'] = ', '.join(dict_line['time']) 
        dict_line['role'] = ', '.join(dict_line['role'])

        # finally, append dict_line to list_mpdata
        list_mpdata.append(dict_line)
    
    # # filter out all 'i' indented lines
    # for i in i_index:
    #     try:
    #         if i+1 != i_index[i+1]:
    #             del list_mpdata[i]
    #     except:
    #         pass

    ## filter out all 'i' indented lines
    # print('i_list: ',i_list)
    # i_count = []
    # for count, i in enumerate(i_list):
    #     if i == 'i':
    #         i2_check = False
    #     elif i == 'i2' and i2_check == False:
    #         i_count.append(count-1)
    #         i2_check = True
    #     else:
    #         pass
    # print('i_count: ',i_count)
    # for i in i_count:
    #     del list_mpdata[i]

    return list_mpdata

def parse_all_mpfi_pkl(date, heading_ref):
    dict_parlurl_mpname = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))

    list_all_mpdata = []
    failed_urls = []

    for url in tqdm(dict_parlurl_mpname.keys()):
        print(url,'\n')
        try:
            list_mpdata = parse_mpfi_pkl(date, url, heading_ref)
            if list_mpdata is None:
                pass
            else:
                list_all_mpdata = list_all_mpdata + list_mpdata
        except:
            failed_urls.append(url)
    
    ## save list_allmpdata to a pkl
    dict_df_file = open('./pkl/dict_df.pkl', 'wb')
    pickle.dump(list_all_mpdata, dict_df_file)
    dict_df_file.close()

    dict_failed_urls_file = open('./pkl/dict_failed_urls.pkl','wb')
    pickle.dump(failed_urls, dict_failed_urls_file)
    dict_failed_urls_file.close()
    
    return list_all_mpdata, failed_urls

#list_all_mpdata, failed_urls = parse_all_mpfi_pkl(date, headings_dict['h1'])

## Manual checks
def manual_checks():
    list_all_mpdata = pickle.load(open('./pkl/dict_df.pkl','rb'))

    for item in list_all_mpdata:
        if item['total_money_ytd'] == 'MANUAL_CHECK' and item['total_time_ytd'] == 'MANUAL_CHECK':
            print('\n',item)
            new_money_ytd = float(input('Enter total_money_ytd: '))
            new_time_ytd = float(input('Enter total_time_ytd: '))
            item['total_money_ytd'] = new_money_ytd
            item['total_time_ytd'] = new_time_ytd
        elif item['total_money_ytd'] == 'MANUAL_CHECK':
            print('\n',item)
            new_money_ytd = float(input('Enter total_money_ytd: '))
            item['total_money_ytd'] = new_money_ytd
        elif item['total_time_ytd'] == 'MANUAL_CHECK':
            print('\n',item)
            new_time_ytd = float(input('Enter total_time_ytd: '))
            item['total_time_ytd'] = new_time_ytd
        else:
            pass

        dict_df_file = open('./pkl/dict_df.pkl', 'wb')
        pickle.dump(list_all_mpdata, dict_df_file)
        dict_df_file.close()

    return list_all_mpdata

#list_all_mpdata = manual_checks()

##########################
## 3. CREATE DATAFRAMES ##
##########################

# MAIN SHEET - EARNINGS BREAKDOWN
def create_dataframes():
    df_mpfi = pd.DataFrame(pickle.load(open('./pkl/dict_df.pkl','rb')))
    df_earnings_breakdown = df_mpfi[["name","orgs","role","money","time","date","total_money_ytd","total_time_ytd","full_text"]]
    df_earnings_breakdown = df_earnings_breakdown.rename(columns={
        'name':'Name',
        'money':'Earnings (RAW)',
        'time':'Hours worked (RAW)',
        'date':'Date of Earnings',
        'orgs':'Client/Organisation',
        'role':'Role',
        'total_money_ytd':'Earnings YTD (£)',
        'total_time_ytd':'Hours worked YTD',
        'full_text':'Original text (from source)'
    })

    # TOTAL MONEY/TIME YTD SHEET
    def sum_timemoney(dataframe):
        dict_parlukurl_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))
        df = dataframe

        list_totals = []
        for url, mp_name in dict_parlukurl_name.items():
            print('mp_name: ',mp_name)
            sm_list = [item for item in df.loc[df['Name'] == dict_parlukurl_name[url], 'Earnings YTD (£)'].to_list() if type(item) is float or type(item) is int]
            print('sm_list: ',sm_list)
            st_list = [item for item in df.loc[df['Name'] == dict_parlukurl_name[url], 'Hours worked YTD'].to_list() if type(item) is float or type(item) is int]
            print('st_list: ',st_list)

            dict_totals = {}
            dict_totals['name'] = dict_parlukurl_name[url]
            dict_totals['sum_money_ytd'] = sum(sm_list)
            print('sum_money_ytd: ',dict_totals['sum_money_ytd'])
            dict_totals['sum_time_ytd'] = sum(st_list)
            print('sum_time_ytd: ',dict_totals['sum_time_ytd'])
            print('\n')

            list_totals.append(dict_totals)

            # print('name:',mp_name)
            # print('sum_money:',sum(sm_list))
            # print('sum_time:',sum(st_list))
            # print('\n')
        
        return list_totals

    list_totals = sum_timemoney(df_earnings_breakdown)
    df_totals = pd.DataFrame(list_totals).set_index('name')

    dict_mpinfo_political = pickle.load(open('./pkl/dict_mpinfo_political.pkl','rb'))
    df_mpinfo_political = pd.DataFrame(dict_mpinfo_political).transpose()
    df_mpinfo_political

    df_mp_overview = pd.concat([df_totals, df_mpinfo_political], axis=1)
    df_mp_overview = df_mp_overview[["sum_money_ytd","sum_time_ytd","basic_salary","lalp_payment","party","constituency","region","country","assumed_office","years_in_office","majority"]]
    df_mp_overview = df_mp_overview.rename(columns = {
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

    return df_mp_overview, df_earnings_breakdown

#df_mp_overview, df_earnings_breakdown = create_dataframes()

###############
## 4. EXPORT ##
###############

def export_xlsx(workbook_name, df1, df2):
    writer = pd.ExcelWriter(workbook_name, engine='xlsxwriter')

    workbook = writer.book
    worksheet0 = workbook.add_worksheet('Intro')

    df1.to_excel(writer, sheet_name='MP overview')
    df2.to_excel(writer, sheet_name='Earnings breakdown')

    format_all_columns = workbook.add_format({'align':'left'})
    format_currency = workbook.add_format({'align':'left', 'num_format': "£#,##0.00", 'bold': True})
    format_time = workbook.add_format({'align':'left', 'bold': True})
    format_timedate = workbook.add_format({'align':'left', 'num_format': 'dd mmmm yyyy'})

    # Sheet 0
    worksheet0.set_column('A:A', 100)
    worksheet0.set_row(3, 200)

    title = workbook.add_format({'bold': True})
    sub_title = workbook.add_format({'italic': True})

    worksheet0.write('A1','MP FINANCIAL INTERESTS DATA - STRUCTURED', title)
    worksheet0.write('A2','by Andrew Kyriacos-Messios', sub_title)

    # Sheet 1
    worksheet1 = writer.sheets['MP overview']
    worksheet1.set_column(0, 0, 25, format_all_columns) # name
    worksheet1.set_column(1, 1, 20, format_currency) # sum_money_ytd
    worksheet1.set_column(2, 2, 20, format_time) # sum_time_ytd
    worksheet1.set_column(3, 3, 20, format_currency) # basic_salary
    worksheet1.set_column(4, 4, 20, format_currency) # lalp_payment
    worksheet1.set_column(5, 5, 25, format_all_columns) # party
    worksheet1.set_column(6, 6, 15, format_all_columns) # constituency
    worksheet1.set_column(7, 7, 25, format_all_columns) # region
    worksheet1.set_column(8, 8, 15, format_all_columns) # country
    worksheet1.set_column(9, 9, 15, format_timedate) # assumed_office
    worksheet1.set_column(10, 10, 15, format_all_columns) # years_in_office
    worksheet1.set_column(11, 11, 15, format_all_columns) # majority

    # Sheet 2
    worksheet2 = writer.sheets['Earnings breakdown']
    worksheet2.set_column(0, 0, 5, format_all_columns) # index
    worksheet2.set_column(1, 1, 25, format_all_columns) # name
    worksheet2.set_column(2, 2, 25, format_all_columns) # money
    worksheet2.set_column(3, 3, 25, format_all_columns) # time
    worksheet2.set_column(4, 4, 40, format_all_columns) # date
    worksheet2.set_column(5, 5, 40, format_all_columns) # orgs
    worksheet2.set_column(6, 6, 40, format_all_columns) # role
    worksheet2.set_column(7, 7, 20, format_currency) # total_money_ytd
    worksheet2.set_column(8, 8, 20, format_time) # total_time_ytd
    worksheet2.set_column(9, 9, 250, format_all_columns) # full_text

    # save and close
    writer.save()

#xlsx_filename = './excel/'+date+'.xlsx'
#export_xlsx(xlsx_filename, df_mp_overview, df_earnings_breakdown)
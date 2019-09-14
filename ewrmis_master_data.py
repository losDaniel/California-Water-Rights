import pip._internal

try:
    from bs4 import BeautifulSoup
except:
    import pip
    pip._internal.main(['install', 'bs4'])
    from bs4 import BeautifulSoup

try:
    from selenium import webdriver
except:
    import pip
    pip._internal.main(['install', 'selenium'])
    from selenium import webdriver 

try:
    import pandas as pd 
except:
    import pip
    pip._internal.main(['install', 'pandas'])
    import pandas as pd 

import os, re
import bear_necessities as bn

try:
    assert os.path.exists(os.getcwd() + '/chromedriver.exe')
    cdir = os.getcwd() + '/chromedriver.exe'
except:
    raise ValueError('chomedriver.exe not found in main directory')
    
def launch_driver(wait=10):
    driver = webdriver.Chrome(executable_path=cdir)       # launch the driver 
    driver.implicitly_wait(wait)                          # tell the driver to wait at least `wait` seconds before throwing up an error
    return driver 

def navigate_to_database():
    driver = launch_driver()
    driver.get('https://ciwqs.waterboards.ca.gov/ciwqs/ewrims/EWServlet?Redirect_Page=EWWaterRightPublicSearch.jsp&Purpose=getEWAppSearchPage')
    driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td/table/tbody/tr[16]/td/table/tbody/tr/td/input[1]').click()
    return driver 

def get_headers(rows): 
    headers= [] 
    header = rows[0].find_all('th')                  # for each column in the header 
    for th in header: 
        headers.append(th.text)                      # get the text for the column 

    return [h.replace('\xa0', '') for h in headers]  # remove unicode characters 
   
def get_applications(rows, headers):
    data = rows[1:-2]                   # get the rows with dat a
    dataset = {}                        # create a placeholder for the data 
    for h in headers: 
        dataset[h] = []                 # create an empty list for each header 

    for row in data: 
        column = 0                      # we'll keep track of the headers...
        for td in row.find_all('td'):   # ...for each column
            
            if column>=10: 
                # if we're in the View Reports, View Documents, Open in GIS or Export to Excel columns 
                links = td.findAll('a')
                if len(links)>0:                    
                     # we retrieve the link 
                    dataset[headers[column]].append(links[0]['href'])     
                else:
                    # if now link is available we fill the slot with a blank 
                    dataset[headers[column]].append('')
            else: 
                # otherwise we get the data 
                dataset[headers[column]].append(td.text.replace('\n','').strip())            
            column+=1

    return pd.DataFrame(dataset)        # return a pandas dataframe with the application data 

def set_current_page(driver):
    '''Record the current page in the runtime folder'''
    
    current_page = int(re.findall('curPage=([0-9]*)',driver.current_url)[0])
    with open(os.getcwd()+'/runtime/current_page.txt','w') as f: 
        f.write(str(current_page))
        f.close()
    
def last_page_url():
    '''Retrieve the last page recorded in the runtime folder'''
    
    with open(os.getcwd()+'/runtime/current_page.txt','r') as f: 
        current_page = f.read() 
    page_url = 'https://ciwqs.waterboards.ca.gov/ciwqs/ewrims/EWServlet?Page_From=EWWaterRightPublicSearch.jsp&Redirect_Page=EWWaterRightPublicSearchResults.jsp&Object_Expected=EwrimsSearchResult&Object_Created=EwrimsSearch&Object_Criteria=&Purpose=&appNumber=&watershed=&waterHolderName=&curPage='+str(current_page)+'&sortBy=&sortDir=ASC&pagination=true'
    return page_url, current_page

def page_url(page): 
    return 'https://ciwqs.waterboards.ca.gov/ciwqs/ewrims/EWServlet?Page_From=EWWaterRightPublicSearch.jsp&Redirect_Page=EWWaterRightPublicSearchResults.jsp&Object_Expected=EwrimsSearchResult&Object_Created=EwrimsSearch&Object_Criteria=&Purpose=&appNumber=&watershed=&waterHolderName=&curPage='+str(page)+'&sortBy=&sortDir=ASC&pagination=true'

def get_applications(rows, headers):
    data = rows[1:-1]                   # get the rows with dat a
    dataset = {}                        # create a placeholder for the data 
    dataset['RightID'] = []             # the first element of the placeholder is the waterright and application number 
    dataset['ApplNum'] = []             # the first element of the placeholder is the waterright and application number 
    for h in headers: 
        dataset[h] = []                 # create an empty list for each header 

    for row in data: 
        column = 0                      # we'll keep track of the headers...
        for td in row.find_all('td'):   # ...for each column
            
            if column>=10: 
                # if we're in the View Reports, View Documents, Open in GIS or Export to Excel columns 
                links = td.findAll('a')
                if len(links)>0:                    
                     # we retrieve the link 
                    dataset[headers[column]].append(links[0]['href'])     
                else:
                    # if now link is available we fill the slot with a blank 
                    dataset[headers[column]].append('')
            elif column == 0: 
                # if there is a link with the application data
                links = td.findAll('a')
                if len(links)>0: 
                    link = links[0]['href']
                    dataset['RightID'].append(re.findall('wrWaterRightID=(.*)&',link)[0])
                    dataset['ApplNum'].append(re.findall('applicationID=(.*)',link)[0])
                else: 
                    # else fill it in with a blank 
                    dataset['RightID'].append('')
                    dataset['ApplNum'].append('')
                # record the application ID
                dataset[headers[column]].append(td.text.replace('\n','').strip())
                
            else: 
                # otherwise we get the data 
                dataset[headers[column]].append(td.text.replace('\n','').strip())            
            column+=1

    listlen = min([len(dataset[key]) for key in dataset])
    for key in dataset:
    	dataset[key] = dataset[key][:listlen]

    return pd.DataFrame(dataset)        # return a pandas dataframe with the application data
    
def scrape_applications():
    driver = navigate_to_database()
    
    page, current_page = last_page_url()                # pick up where you left off 
    current_page = int(current_page)
    page_data = 99                                      # set a positive ammount of data on the page 
    
    try: 
	     # load existing data if we need to pick up where we left off 
	     application_data = bn.loosen(os.getcwd()+'/data/database/database/master_data.pickle')
    except: 
 	     # otherwise start a new dataset 
 	     application_data = pd.DataFrame() 

	 # while we're still retrieving data 
    while page_data > 0: 
        page = page_url(current_page)
        
        driver.get(page)
        source = driver.page_source                                # get the page source
        soup = BeautifulSoup(source, 'lxml')                       # read it into beautifulsoup 
        table = soup.find_all('table',{'class':'dataentry'})[0]    # find the table holding all the data 
        rows = table.find_all('tr')                                # get all the rows for a table
        headers = get_headers(rows)                             # find the headers
        applications = get_applications(rows, headers)             # get all the application data
        
        page_data = len(applications)                              # check that we're still gettin g data  
        
        current_page+=1                                            # get the next page  
        
        application_data = application_data.append(applications, ignore_index=True)    
	#     try: 
	#         driver.find_element_by_xpath('/html/body/form/table[1]/tbody/tr/td/a').click()
	#     except: 
	#         page_data = 0
        if current_page%20==0:                                     # save the data every 20 pages 
            set_current_page(driver)                               # record the scraper's current page in the application data
            bn.full_pickle(os.getcwd()+'/data/database/database/master_data', application_data)
            
	# once its all been scraped
    set_current_page(driver)
    
    bn.full_pickle(os.getcwd()+'/data/database/database/master_data', application_data)
    driver.quit()
    
    return application_data

def application_url(wrid, apid):
    return 'https://ciwqs.waterboards.ca.gov/ciwqs/ewrims/EWServlet?Page_From=EWWaterRightSearchResults.jsp&Redirect_Page=EWPublicAppSummary.jsp&Purpose=getEwrimsPublicSummary&wrWaterRightID='+str(wrid)+'&applicationID='+str(apid)

def set_current_application(ca): 
    with open(os.getcwd()+'/runtime/current_application.txt','w') as f: 
        f.write(str(ca))
        f.close() 
            
def get_apptable_f1(soup, applid): 
    
    tables = soup.find_all('table')           # retrieve the table with general information 

    headers = []
    for tr in tables[0].find_all('tr')[1].find_all('tr'):
        headers.append(tr.text.replace(' ','').replace('\n','').split(':')[0].strip())

    summary_data = {} 
    for h in headers: 
        summary_data[h]=[]

    column = 0 
    for tr in tables[0].find_all('tr')[1].find_all('tr'):
        summary_data[headers[column]].append(tr.text.replace(' ','').replace('\n','').split(':')[1].strip())
        column+=1

    summary_data = pd.DataFrame(summary_data)
    summary_data['Appl ID'] = applid

    return summary_data 

def get_apptable_f2(table, applid):
    rows = table.find_all('tr')

    if len(rows)>2:
        headers = []
        for tr in rows[0].find_all('td'):
            headers.append(tr.text.replace(' ','').replace('\n','').split(':')[0].strip())

        current_parties = {} 
        for h in headers: 
            current_parties[h]=[]

        for tr in rows[1:-1]:
            column = 0 
            for td in tr.find_all('td',{'class','data'}):
                current_parties[headers[column]].append(td.text.replace(' ','').replace('\n','').strip())
                column+=1 

        current_parties = pd.DataFrame(current_parties)
        current_parties['ApplID'] = applid
        return current_parties
    else: 
        return pd.DataFrame()
    
def get_apptable_f3(table, applid, rowstart=0): 
	rows = table.find_all('tr')[rowstart:]
	    
	if len(rows)>1: 
	    headers = []
	    for tr in rows[0].find_all('td'):
	        headers.append(tr.text.replace(' ','').replace('\n','').split(':')[0].strip())

	    histparties = {} 
	    for h in headers: 
	        histparties[h]=[]

	    for tr in rows[1:]:
	        column = 0 
	        cols = tr.find_all('td')
	        if len(cols) == len(headers):
	            for td in cols:
	                value = td.text.replace(' ','').replace('\n','').strip()

	                if value=='View' or value=='Document':
	                    try:
	                        val = td.find_all('a')[0]['href']
	                    except: 
	                        val = value
	                    histparties[headers[column]].append(val)
	                else:
	                    histparties[headers[column]].append(value)

	                column+=1 

	    histparties = pd.DataFrame(histparties)
	    histparties['ApplID'] = applid
	    return histparties
	else: 
	    return pd.DataFrame()

def get_apptable_f4(table, applid):
    rows = table.find_all('tr')

    rows = rows[1:]
    record = {} 
    for tr in rows: 
        record[tr.find_all('td')[0].text.strip()] = tr.find_all('td')[1].text.replace('\n','').strip()
        
    return pd.DataFrame(record, index = [applid])


def scrape_application_details(applications):
    
    applications = applications.reset_index(drop=True)
    with open(os.getcwd()+'/runtime/current_application.txt','r') as f: 
        ca = int(f.read())
    
    try: 
        summary_data = bn.loosen(os.getcwd()+'/data/database/database/summary_data.pickle')
    except: 
        summary_data = pd.DataFrame()
    try: 
        current_parties = bn.loosen(os.getcwd()+'/data/database/database/current_parties.pickle')
    except: 
        current_parties = pd.DataFrame()
    try: 
        histparties = bn.loosen(os.getcwd()+'/data/database/database/historic_parties.pickle')
    except: 
        histparties = pd.DataFrame()
    try: 
        record_summary = bn.loosen(os.getcwd()+'/data/database/database/record_summary.pickle')
    except: 
        record_summary = pd.DataFrame()
    try: 
        sources = bn.loosen(os.getcwd()+'/data/database/database/water_sources.pickle')
    except: 
        sources = pd.DataFrame()
    try: 
        uses = bn.loosen(os.getcwd()+'/data/database/database/beneficial_uses.pickle')
    except: 
        uses = pd.DataFrame()
    try: 
        report = bn.loosen(os.getcwd()+'/data/database/database/electronic_reports.pickle')
    except: 
        report = pd.DataFrame()
    try: 
        decisions = bn.loosen(os.getcwd()+'/data/database/database/decisions_data.pickle')
    except: 
        decisions = pd.DataFrame()

    driver = navigate_to_database()
        
    rownum = ca
    for idx, row in applications[ca:].iterrows():
        try:
        	appurl = row['appl_id_link']
        except:
        	appurl = application_url(row['RightID'],row['ApplNum'])
        driver.get(appurl)
    
        source = driver.page_source                                # get the page source 
        soup = BeautifulSoup(source, 'lxml')                       # read it into beautifulsoup 
        
        tables = soup.find_all('table',{'class':'dataentry'})
        applid = row['ApplID']

        summary_data = summary_data.append(get_apptable_f1(soup, applid),ignore_index=True,sort=False)                 # get the summary data
        current_parties = current_parties.append(get_apptable_f2(tables[0], applid),ignore_index=True,sort=False) # current parties associated 
        histparties = histparties.append(get_apptable_f3(tables[1], applid),ignore_index=True, sort=False)    # historical parties associated 
        record_summary = record_summary.append(get_apptable_f4(tables[2], applid),ignore_index=True, sort=False) # get the summary of the record 
        sources = sources.append(get_apptable_f2(tables[3], applid),ignore_index=True, sort=False)        # water sources 
        uses = uses.append(get_apptable_f3(tables[4], applid),ignore_index=True, sort=False)                # beneficial uses of the water 
        report = report.append(get_apptable_f3(tables[5], applid, rowstart=1),ignore_index=True, sort=False)  # reports associated with the record 
        decisions = decisions.append(get_apptable_f3(tables[8], applid, rowstart=1),ignore_index=True, sort=False)    # court decisions associated with the right 

        set_current_application(rownum)  # set the current application number
        rownum+=1 
    
        if rownum%100==0:             
            bn.full_pickle(os.getcwd()+'/data/database/database/summary_data', summary_data)
            bn.full_pickle(os.getcwd()+'/data/database/database/current_parties', current_parties)
            bn.full_pickle(os.getcwd()+'/data/database/database/historic_parties', histparties)
            bn.full_pickle(os.getcwd()+'/data/database/database/record_summary', record_summary)
            bn.full_pickle(os.getcwd()+'/data/database/database/water_sources', sources)
            bn.full_pickle(os.getcwd()+'/data/database/database/beneficial_uses', uses)
            bn.full_pickle(os.getcwd()+'/data/database/database/electronic_reports', report)
            bn.full_pickle(os.getcwd()+'/data/database/database/decisions_data', decisions)

    bn.full_pickle(os.getcwd()+'/data/database/database/summary_data', summary_data)
    bn.full_pickle(os.getcwd()+'/data/database/database/current_parties', current_parties)
    bn.full_pickle(os.getcwd()+'/data/database/database/historic_parties', histparties)
    bn.full_pickle(os.getcwd()+'/data/database/database/record_summary', record_summary)
    bn.full_pickle(os.getcwd()+'/data/database/database/water_sources', sources)
    bn.full_pickle(os.getcwd()+'/data/database/database/beneficial_uses', uses)
    bn.full_pickle(os.getcwd()+'/data/database/database/electronic_reports', report)
    bn.full_pickle(os.getcwd()+'/data/database/database/decisions_data', decisions)

    driver.quit()
    return summary_data, current_parties, histparties, record_summary, sources, uses, report, decisions


def scrape_reports(links, ids):

    driver = navigate_to_database()

    with open(os.getcwd()+'/runtime/current_report.txt','r') as f:
        current_report = int(f.read()) 
        count = current_report       

    try:
        datasets = bn.loosen(os.getcwd()+'/data/database/database/raw_reports.pickle')
    except:
        datasets = {}

    for link in links[current_report:]:
        if 'https' in link:         
            driver.get(link)
            source = driver.page_source                                # get the page source 
            soup = BeautifulSoup(source, 'lxml')                       # read it into beautifulsoup 
            tables = soup.find_all('table')                            # find all table elements 
            for table in tables: 
                head = table.find_all('th')                            # is this a table with a sub-table
                rows = table.find_all('tr')                            # find all the rows, the top one will have the title 
                if len(rows)>1:
                    title = rows[0].text.replace('\n','').strip()
                    headers = [h.text.replace('\n','').strip() for h in rows[1].find_all('th')]
                    if len(headers)==0:
                        data = {} 
                        rows = rows[1:]
                        for row in rows: 
                            val = row.find_all('td')
                            if len(val)>=2:
                                data[val[-2].text.replace('\n','').strip()] = [val[-1].text.replace('\n','').strip()]
                            elif len(val)==1:
                                data["TEXTVALUE"]= [val[-1].text.replace('\n','').strip()]
                    else:
                        data = {} 
                        for h in headers:
                            data[h]=[]
                        rows = rows[2:]
                        for row in rows: 
                            val = row.find_all('td')
                            i=0 
                            for v in val:
                                try: 
                                    m = int(v['colspan'])
                                    data[headers[i]].append(v.text.replace('\n',''))
                                    i+=1
                                    m-=1
                                    while m > 0 and i <len(headers): 
                                        data[headers[i]].append(v.text.replace('\n',''))
                                        i+=1
                                        m-=1
                                except: 
                                    data[headers[i]].append(v.text.replace('\n',''))
                                    i+=1

                # make sure all the table columns have the same size 
                assert all([len(data[key])==len(data[list(data.keys())[0]]) for key in data])

                if len(data.keys())>0:
                    # create an index with the applids necessary 
                    indices = len(data[list(data.keys())[0]])
                    indices = indices * [ids[count]]
                    if title in datasets: 
                        datasets[title].append(pd.DataFrame(data, index=indices), ignore_index=True, sort=False)
                    else: 
                        datasets[title] = pd.DataFrame(data, index=indices) 

            with open(os.getcwd()+'/runtime/current_report.txt','w') as f:
                f.write(str(count))        
                f.close()

            count+=1 

            if count%100==0:
                bn.full_pickle(os.getcwd()+'/data/database/database/raw_reports', datasets)

    
    return datasets 

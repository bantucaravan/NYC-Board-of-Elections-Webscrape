#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 16:26:19 2018

@author: admin
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# page of all nyc races for state senate on sept 13
url_all_races = "https://enrweb.boenyc.us/OF7AD0PY1.html"
base_url = 'https://enrweb.boenyc.us'


# get page contenst from url
r = requests.get(url_all_races)
# create bs4 parser
soup = BeautifulSoup(r.text, 'html.parser')

# get individual race urls
links = soup.select('td a')
race_urls = [(link.get('title'), link.get('href')) for link in links if link.get('href').startswith('CD')]


# for testing
#race_name = 'TEST'
#url = 'CD21804ADI0.html'

path = '/Users/admin/Desktop/Data Projects/Election Analysis/Sep 13 NY state senate primary ED level results'

# ONE ITER -->  CPU times: user 728 ms, sys: 111 ms, total: 839 ms; Wall time: 1.22 s
# ALL ITERS --> CPU times: user 5.44 s, sys: 174 ms, total: 5.61 s; Wall time: 9.97 s
%%time
for race_name, url in race_urls:
    
    ## open race page
    url_race =  '/'.join([base_url, url])
    # get page contenst from url
    r2 = requests.get(url_race)
    # create bs4 parser
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    
    ## open AD breakdown page for race
    # Get link to AD breakdown for race
    # Note: "Total" link includes ADs from all NYC counties in given district
    # assumes there is only one total in the page
    Total_url = soup2.find_all(title= 'Total')[0].get('href')
    Total_url =  '/'.join([base_url, Total_url])
    # get page contents from url
    r3 = requests.get(Total_url)
    # create bs4 parser
    soup3 = BeautifulSoup(r3.text, 'html.parser')
    
    # Note: alternate approach would be to enumerate the AD_urls iteration 
    # below and extract race_header if iter == 1
    tables = soup3.select('table')
    rows = tables[2].find_all('tr')
    race_header = [cell.get_text() for cell in rows[0].find_all('td') if cell.get_text() != '\xa0']
    race_header = ['AD_name', 'ED_name', 'pct_scanners_reported'] + race_header
    
    # extract links to ED breakdown pages 
    links = soup3.select('td a')
    AD_urls = [(link.get('title'), link.get('href')) for link in links if link.get('title').startswith('AD')]
    
    # create dict of dfs of ED level data from each AD (in given race)
    race_AD_dfs = {}
    for AD_name, url2 in AD_urls:
        url_AD =  '/'.join([base_url, url2])
        # get page contents from url
        r4 = requests.get(url_AD)
        # create bs4 parser
        soup4 = BeautifulSoup(r4.text, 'html.parser')
        
        tables = soup4.select('table')
        
        # pd.read_html returns a list with the df as the sole element, strange...
        ED_level_data = pd.read_html(str(tables[2]))[0]
        
        # create mask for removing null cols
        mask_cols = [~col.isnull().all() for idx, col in ED_level_data.iteritems()]
        # create mask for removing top 2 rows and bottom row as headers 
        mask_rows = ED_level_data.iloc[:,0].str.startswith('ED', na = False)
        ED_level_data = ED_level_data.loc[mask_rows, mask_cols]
        
        # add col with AD name
        #ED_level_data['AD_name'] = AD_name
        
        race_AD_dfs[AD_name] = ED_level_data
    
    # concat all ED level dfs using AD name as heirarchical index key
    race_data = pd.concat(race_AD_dfs)
    # turn default AD_name hierarchical index into col
    race_data = race_data.reset_index(level = 0)
    # reset index to integer series
    race_data = race_data.reset_index(drop = True)
    race_data.columns = race_header
    race_data.to_csv(os.path.join(path, 'Sep 13 2018 NY {} ED Level Results.csv'.format(race_name)))
    


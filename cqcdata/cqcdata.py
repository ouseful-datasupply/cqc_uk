import pandas as pd
import sqlite3

from bs4 import BeautifulSoup 
import requests

from pandas import read_csv, read_excel, melt
from pandas.compat import string_types

from urllib.request import urlretrieve

_URL = 'http://www.cqc.org.uk/about-us/transparency/using-cqc-data'

_reps = {'care_directory':{'crib':'csv format', 'filetype':'csv'},
	'active_locations':{'crib':'with filters', 'filetype':'xlsx'}, 
	'ratings':{'crib':'with ratings', 'filetype':'xlsx'}}


def setdb(name='default.sqlite'):
	if isinstance(name, string_types):
		return sqlite3.connect(name)
	return None
			   
def _getLinksFromPage(url=None):
	url = url if url else _URL
	page = requests.get(url)

	#The file we have grabbed in this case is a web page - that is, an HTML file
	#We can get the content of the page and parse it
	soup=BeautifulSoup(page.content, "html5lib")
	#BeautifulSoup has a routine - find_all() - that will find all the HTML tags of a particular sort
	#Links are represented in HTML pages in the form <a href="http//example.com/page.html">link text</a>
	#Grab all the <a> (anchor) tags...
	souplinks=soup.find_all('a')
	#links=[link.get('href') for link in souplinks]
	return souplinks
	
	
def _get_cqc_dataURL(typ, links=None):
	if links is None:
		links = [] #add default get links

	#This calls out to global _reps
	if typ not in _reps:
		print("I don't recognise that type: {}".format(typ))
		return None, None

	for link in [l for l in links if l.has_attr('href')]:
		if link['href'].endswith('.{filetype}'.format(filetype= _reps[typ]['filetype'])):
			if hasattr(link,'text') and link.text and 'CQC care directory'.lower() in link.text.lower() and _reps[typ]['crib'].lower() in link.text.lower():
				print('Identifying data for {}: {}'.format(link.text, link['href']))
				return(link.text, link['href'])
				
	return None, None


def _list_normality(data, typ, uid='CQC Location'):
	normaliser=data[[uid, typ]]
	normalised=normaliser[typ].str.split('|', expand=True).stack().str.strip().reset_index(level=1, drop=True)
	normalised.name=typ
	normaliser=normaliser.drop(typ, axis=1).join(normalised).reset_index(drop=True)
	return normaliser
	

def _get_care_directory(con, exists='replace'):
	def mktable(con, table, data, index='CQC Location',exists='replace'):
		data = data.set_index(['CQC Location'])
		data.to_sql(con=con, name=table,if_exists=exists)
	
	print('Getting location directory data...')
	
	url = _reps['care_directory']['url']
	locations=read_csv(url,skiprows=4, dtype={'Phone number':str})
	locations.rename(columns={'CQC Location (for office use only':'CQC Location',
						  'CQC Provider ID (for office use only)':'CQC Provider ID'}, inplace=True)
						  
	typ='Service types'
	tmp=_list_normality(locations, typ)
	mktable(con, 'location_service_type', tmp, exists=exists)
	
	typ='Specialisms/services'
	tmp=_list_normality(locations, typ)
	mktable(con, 'location_specialism', tmp)
	
	tmp=locations.drop(['Service types','Specialisms/services'], axis=1)
	mktable(con, 'locations', tmp, exists=exists)	
	
	
def _get_active_locations(con, exists='replace'):

	def resplit(x):
		xs=x.split(' - ')
		return ' - '.join([xs[0],'-'.join(xs[1:])])

	print('Getting active locations data...')
	url = _reps['active_locations']['url']
	directory=pd.read_excel(url,sheet_name='HSCA Active Locations',skiprows=6)
	
	itemcolroots = ["Regulated activity", "Service type", "Service user band"]
	corecols=[c for c in directory.columns if not c.startswith( tuple(itemcolroots) )]
	k=itemcolroots[1]
	groupcols=[c for c in directory.columns if c.startswith(tuple(itemcolroots))]

	#If we're going to melt, we should probably try to normalise the data a bit
	directory[corecols].to_sql(con=con, name='active_locations',if_exists=exists, index=False)
	
	d2=melt(directory, id_vars=corecols, value_vars=groupcols)
	d2 = d2[pd.notnull(d2['value'])]

	d2['variable'] = d2['variable'].apply(resplit)

	d2[['Type', 'Measure' ]] = d2['variable'].str.split(' - ', expand=True)
	d2 = d2.drop('variable', axis=1)
	d2[['Location ID', 'Type', 'Measure', 'value' ]].to_sql(con=con, name='active_location_measures',if_exists='replace', index=False)
	
def _get_ratings(con, exists='replace'):
	print('Getting ratings data...')
	url = _reps['ratings']['url']
	local_file, headers = urlretrieve(url)

	#Try to normalise the data a bit
	print("Normalising *Locations* a bit...")
	ratings_locations=pd.read_excel(local_file,sheet_name='Locations',skiprows=0)
	tmpcols=['Service / Population Group','Key Question','Latest Rating', 'Publication Date','Report Type']
	basecols=[c for c in ratings_locations.columns if c not in tmpcols]
	ratings_locations[basecols].drop_duplicates().to_sql(con=con, name='ratings_locations',if_exists=exists, index=False)
	ratings_locations[['Location ID']+tmpcols].to_sql(con=con, name='rated_locations',if_exists=exists, index=False)
	ratings_locations = None
	
	print("Normalising *Providers* a bit...")
	ratings_providers=pd.read_excel(local_file,sheet_name='Providers',skiprows=0)
	basecols=[c for c in ratings_providers.columns if c not in tmpcols]
	ratings_providers[basecols].drop_duplicates().to_sql(con=con, name='ratings_providers',if_exists=exists, index=False)
	ratings_providers[['Provider ID']+tmpcols].to_sql(con=con, name='rated_providers',if_exists=exists, index=False)
	ratings_providers = None

def _getDatasetURLs(url=None):
	links =  _getLinksFromPage(url)
	for k in _reps:
		_reps[k]['linktext'], _reps[k]['url'] = _get_cqc_dataURL(k, links)

def _create_index(con, table, cols, idx=None, unique=False):
	idx = idx if idx else 'idx_{table}'.format(table)
	unique = 'UNIQUE' if unique else ''
	cols = cols if isinstance(cols,list) else [cols] 

	cursor = con.cursor()
	#Not secure - subject to SQL injection attack
	q = '''CREATE {unique} INDEX "{idx}" ON "{table}" ({cols});'''.format(table=table, idx=idx, cols=','.join(['"{}"'.format(c) for c in cols]), unique=unique)
	cursor.execute(q, cols)

	


#dbname = 'test1.db'
#con = setdb(dbname)
#_getDatasetURLs() 
#_get_care_directory(con)
#_get_active_locations(con)
#_get_ratings(con)
#print("Data saved to {}".format(dbname))
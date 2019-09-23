import httplib
from requests import session
from requests.auth import HTTPBasicAuth
import base64  
import string  
import xml.etree.ElementTree as ET
import datetime
import sys
from operator import itemgetter
from urlparse import urlparse
#-----------------------------------------------------------------------
#
#Maarten Smeets, 23-09-2019
#This script determines Nexus dependencies of a specific artifact
#
#-----------------------------------------------------------------------

DEBUG='false'

#logs messages to the console. uses DEBUG flag
def log(severity,msg):
    if severity != 'DEBUG' or DEBUG == 'true':
        curtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print curtime+' '+str(severity)+' : '+str(msg)

log('DEBUG','Parameters: '+str(sys.argv))
NEXUS_HOST='nexus.somedomain'
NEXUS_PORT=int('8080')
NEXUS_SEARCH_BASE='/nexus/service/local/repositories/releases/content/'
NEXUS_USERNAME='whatever'
NEXUS_PASSWORD='whatever'

def do_nexus_login(user,passw):
  s = session()
  resp = s.get('http://'+NEXUS_HOST+':'+str(NEXUS_PORT)+'/nexus/service/local/authentication/login', auth=HTTPBasicAuth(user, passw))
  log('DEBUG','do_nexus_login: '+str(resp))
  return s

s=do_nexus_login(NEXUS_USERNAME,NEXUS_PASSWORD)

def elementToString(element):
	return ET.tostring(element, encoding='utf8', method='xml')
  
#used for all HTTP calls
def do_http_request(url):  
  myURL='http://'+str(NEXUS_HOST)+':'+str(NEXUS_PORT)+url
  log('DEBUG','do_http_request: '+str(myURL)) 
  headers = {"Content-type": 'application/xml'}
  resp=s.get(myURL,headers=headers)
  return resp.status_code,resp.headers,resp.text  
  
#gets nodes based on xpath from elementtree
def get_xpath_nodes_from_tree(element,xpath):
    return element.findall(xpath)

#prints an elementtree
def print_et(et):
    log('DEBUG','print_et')
    print ET.tostring(et, encoding='utf8')

#gets contentitems from url and returns elementtree array of content-items
def get_content_items(url):
    log('DEBUG','get_content_items from: '+str(url))
    statuscode,header,res = do_http_request(url)
    if statuscode != 200:
        raise Exception('Failed HTTP call','Was expecting code 200 and received '+str(statuscode))
    #log('DEBUG','get_content_items: '+str(statuscode)+' '+str(statusmessage)+' '+str(header)+' '+str(res) )
    try:
        tree = ET.fromstring(res)
    except:
        log('DEBUG',"String no valid XML: "+str(res))
        raise
    return get_xpath_nodes_from_tree(tree,'./data/content-item')

#for node in get_content_items(NEXUS_SEARCH_BASE):
#	print(elementToString(node))
pomslist_g=[]
#gets pom files starting with path. returns array of dictionaries, keys url,date
def get_pomurls(starturl):
	pomslist=[]
	starturl = urlparse(starturl).path
	log('DEBUG','get_release_pomurls: '+str(starturl))
	resources = get_content_items(starturl)
	#print 'get_release_poms called with: '+str(starturl)+' resources found: '+str(len(resources))
		
	for item in resources:
		if(item.find('leaf').text=='false'):
			pomslist_g.extend(get_pomurls(item.find('resourceURI').text))
		else:
			if (item.find('resourceURI').text.endswith('.pom')):
				pomslist.append({'url':item.find('resourceURI').text})
	return pomslist

#gets dependencies from pom url. uses only the path of the url. returns array of elementtrees
def get_pom_dependencies(pomurl):
    url = urlparse(pomurl).path
    log('DEBUG','get_pom_dependencies from: '+str(url))
    statuscode,header,res = do_http_request(url)
    if statuscode != 200:
        raise Exception('Failed HTTP call','Was expecting code 200 and received '+str(statuscode))
    try:
        tree = ET.fromstring(res)
    except:
        log('DEBUG',"String no valid XML: "+str(res))
        raise
    return get_xpath_nodes_from_tree(tree,'.//{http://maven.apache.org/POM/4.0.0}dependency/{http://maven.apache.org/POM/4.0.0}artifactId')    

print ('Searching for pom.xml files in Nexus')
get_pomurls(NEXUS_SEARCH_BASE)
print ('Found: '+str(len(pomslist_g)))

print ('Determining dependencies in poms')
for pomurl in pomslist_g:
    url=pomurl['url']
    try:
	    artifactids=get_pom_dependencies(url)
    except:
      log('ERROR',"Error parsing: "+url)
    
    for artifactid in artifactids:
        if artifactid.text == 'ARTIFACT_TO_SEARCH_FOR':
            print ('artifact: '+url)

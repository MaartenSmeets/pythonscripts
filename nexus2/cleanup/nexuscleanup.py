import httplib  
import base64  
import string  
import xml.etree.ElementTree as ET
import datetime
import sys
from operator import itemgetter
from urlparse import urlparse
#-----------------------------------------------------------------------
#
#Maarten Smeets, 28-10-2016
#This script removes artifacts from Nexus which satisfy certain criteria.
#
#-----------------------------------------------------------------------
#
#pom files below NEXUS_BASE_RELEASE_SEARCH are considered releases
#  the lastModifiedDate as visible in Nexus is used to check weither they are relevant for removal
#  if the lastModifiedDate is less than REMOVEBEFOREDATE than the release is removed
#for every release which is not removed, the dependencies from the pom file are determined
#  NEXUS_BASE_CONTENT is used to determine the url of the artifact
#  pom files below the artifact location are determined
#  the artifact, group, version are added to the global release_dependencies list
#  for these pom files, dependencies are determined. these dependencies are used to get their pom files, etc (all artifacts in the dependency tree are added recursively)
#  MINRELEASESTOKEEP is the number of releases which are kept. releases are sorted by date descending. releases which have a number in the array > MINRELEASESTOKEEP and older than REMOVEBEFOREDATE are removed
#artifacts are determined. NEXUS_BASE_ARTIFACT_SEARCH is used as base path.
#  if an artifact is not in the release dependencies list and is older than REMOVEBEFOREDATE, it is removed
#
#for every request to the Nexus API, NEXUS_HOST, NEXUS_PORT, NEXUS_USERNAME, NEXUS_PASSWORD are used
#if DUMMYRUN is set to true, no artifacts/releases are actually deleted. the logging and everything else is exactly the same

#parameters:
#NEXUS_HOST is the hostname of the NEXUS machine. When running this script on the same machine as Nexus, this can be localhost
#NEXUS_PORT is the port used by Nexus on NEXUS_HOST
#NEXUS_USERNAME is a Nexus username which is allowed to query and delete artifacts (builduser, admin)
#NEXUS_PASSWORD is the password of NEXUS_USERNAME
#NEXUS_BASE_CONTENT is the base path of the Nexus API. usually /nexus/service/local/repositories/releases/content
#NEXUS_BASE_RELEASE_SEARCH is the path after NEXUS_BASE_CONTENT where releases can be found to be deleted. releases (artifacts themselves) have dependencies to other artifacts. dependencies do not need to be in this path
#NEXUS_BASE_ARTIFACT_SEARCH is the path after NEXUS_BASE_CONTENT where artifacts can be found to be deleted
#DUMMYRUN if true, no actual artifacts/releases are deleted. if not true, they are
#REMOVEBEFOREDATE if the date as a string. formatted like 'YYYY-MM-DD HH24:mi:ss' for example 2016-12-27 14:30:01
#MINRELEASESTOKEEP is the number of releases not to remove

#NEXUS_HOST="localhost"
#NEXUS_PORT="8081"
#NEXUS_BASE_CONTENT="/nexus/service/local/repositories/releases/content"
#NEXUS_BASE_RELEASE_SEARCH=NEXUS_BASE_CONTENT+"/nl/amis/smeetsm/releases/"
#NEXUS_BASE_ARTIFACT_SEARCH=NEXUS_BASE_CONTENT+"/nl/amis/smeetsm/applications/"
#NEXUS_USERNAME="admin"  
#NEXUS_PASSWORD="admin123"  
#DUMMYRUN='true'
#REMOVEBEFOREDATE=datetime.datetime(2016, 10, 27, 9, 00)
#MINRELEASESTOKEEP=1

#example commandline (does dummy run, keeps 1 release): python ./nexuscleanup.py localhost 8081 /nexus/service/local/repositories/releases/content /nl/amis/smeetsm/releases/ /nl/amis/smeetsm/applications/ admin admin123 true '2016-01-01 01:01:01' 1

DEBUG='false'

#logs messages to the console. uses DEBUG flag
def log(severity,msg):
    if severity != 'DEBUG' or DEBUG == 'true':
        curtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print curtime+' '+str(severity)+' : '+str(msg)

#checks the commandline arguments
def check_args():
    numargs=len(sys.argv)
    log('DEBUG','Number of arguments:'+str(numargs)+'arguments')
    if numargs<11:
        raise Exception('Argument error','Expected 10 arguments but got '+str(numargs-1))
    if sys.argv[1].startswith('http'):
        raise Exception('Invalid NEXUS_HOST', 'A hostname does not start with http like: '+sys.argv[1])
    if not sys.argv[2].isdigit():
        raise Exception('Invalid NEXUS_PORT', 'NEXUS_PORT should be a number. Not like: '+sys.argv[2])
    if not sys.argv[3].startswith('/'):
        raise Exception('Invalid NEXUS_BASE_CONTENT', 'NEXUS_BASE_CONTENT should start with / and not like: '+sys.argv[3])
    if sys.argv[3].endswith('/'):
        raise Exception('Invalid NEXUS_BASE_CONTENT', 'NEXUS_BASE_CONTENT should not end with /. Not like: '+sys.argv[3])
    if not sys.argv[4].startswith('/'):
        raise Exception('Invalid NEXUS_BASE_RELEASE_SEARCH', 'NEXUS_BASE_RELEASE_SEARCH should start with / and not like: '+sys.argv[4])
    if not sys.argv[4].endswith('/'):
        raise Exception('Invalid NEXUS_BASE_RELEASE_SEARCH', 'NEXUS_BASE_RELEASE_SEARCH should end with /. Not like: '+sys.argv[4])
    if not sys.argv[5].startswith('/'):
        raise Exception('Invalid NEXUS_BASE_ARTIFACT_SEARCH', 'NEXUS_BASE_ARTIFACT_SEARCH should start with / and not like: '+sys.argv[5])
    if not sys.argv[5].endswith('/'):
        raise Exception('Invalid NEXUS_BASE_ARTIFACT_SEARCH', 'NEXUS_BASE_ARTIFACT_SEARCH should end with /. Not like: '+sys.argv[5])
    if not sys.argv[8] in ['true','false']:
        raise Exception('Invalid DUMMYRUN', 'DUMMYRUN should be either true or false. Not like: '+sys.argv[8])
    try:
        dateval=datetime.datetime.strptime(sys.argv[9],'%Y-%m-%d %H:%M:%S')
    except:
        raise Exception('Invalid date', 'Expected date in format: YYYY-MM-DD HH24:mi:ss such as 2016-12-24 14:01:01 but got: '+sys.argv[9])
    if not sys.argv[10].isdigit():
        raise Exception('Invalid MINRELEASESTOKEEP', 'MINRELEASESTOKEEP should be a number. Not like: '+sys.argv[10])

#checks parameters and sets variables to parameters
check_args()
log('DEBUG','Parameters: '+str(sys.argv))
NEXUS_HOST=sys.argv[1]
NEXUS_PORT=int(sys.argv[2])
NEXUS_BASE_CONTENT=sys.argv[3]
NEXUS_BASE_RELEASE_SEARCH=NEXUS_BASE_CONTENT+sys.argv[4]
NEXUS_BASE_ARTIFACT_SEARCH=NEXUS_BASE_CONTENT+sys.argv[5]
NEXUS_USERNAME=sys.argv[6]
NEXUS_PASSWORD=sys.argv[7]
DUMMYRUN=sys.argv[8]
REMOVEBEFOREDATE=datetime.datetime.strptime(sys.argv[9],'%Y-%m-%d %H:%M:%S')
MINRELEASESTOKEEP=int(sys.argv[10])

#used for all HTTP calls
def do_http_request(host,port,url,verb,contenttype,username,password,body):  
  # from http://mozgovipc.blogspot.nl/2012/06/python-http-basic-authentication-with.html  
  # base64 encode the username and password  
  auth = string.strip(base64.encodestring(username + ':' + password))  
  #log('DEBUG','do_http_request: '+' '+str(host)+' '+str(port))
  service = httplib.HTTP(host,port)  
     
  # write your headers  
  #completeurl='http://'+host+':'+port+url
  service.putrequest(verb, url)
  log('DEBUG','do_http_request: '+' '+verb+' '+str(url))  
  #service.putheader("Host", host)  
  #service.putheader("User-Agent", "Python http auth")  
  service.putheader("Content-type", contenttype)  
  service.putheader("Authorization", "Basic %s" % auth)  
  service.endheaders()  
  service.send(body)  
  # get the response  
  statuscode, statusmessage, header = service.getreply()  
  log('DEBUG','do_http_request: '+' '+str(statuscode)+' '+str(statusmessage))
  #print "Headers: ", header  
  res = service.getfile().read()  
  #print 'Content: ', res  
  return statuscode,statusmessage,header,res  

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
    statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,url,'GET','application/xml',NEXUS_USERNAME,NEXUS_PASSWORD,'')
    if statuscode != 200:
        raise Exception('Failed HTTP call','Was expecting code 200 and received '+str(statuscode))
    #log('DEBUG','get_content_items: '+str(statuscode)+' '+str(statusmessage)+' '+str(header)+' '+str(res) )
    try:
        tree = ET.fromstring(res)
    except:
        log('DEBUG',"String no valid XML: "+str(res))
        raise
    return get_xpath_nodes_from_tree(tree,'./data/content-item')

#gets release pom url's as array of dictionaries with url,date keys
def get_release_poms():
    log('DEBUG','get_release_poms: '+NEXUS_BASE_RELEASE_SEARCH)
    release_poms = get_pomurls(NEXUS_BASE_RELEASE_SEARCH)
    return release_poms

#gets pom files starting with path. returns array of dictionaries, keys url,date
def get_pomurls(starturl):
    starturl = urlparse(starturl).path
    log('DEBUG','get_release_pomurls: '+str(starturl))
    resources = get_content_items(starturl)
    #print 'get_release_poms called with: '+str(starturl)+' resources found: '+str(len(resources))
    releaselist=[]
    for item in resources:
        if(item.find('leaf').text=='false'):
            releaselist.extend(get_pomurls(item.find('resourceURI').text))
        else:
            if (item.find('resourceURI').text.endswith('.pom')):
                dateval=datetime.datetime.strptime(item.find('lastModified').text,'%Y-%m-%d %H:%M:%S.0 %Z')
                releaselist.append({'url':item.find('resourceURI').text,'date':dateval})
    return releaselist

#gets dependencies from pom url. uses only the path of the url. returns array of elementtrees
def get_pom_dependencies(pomurl):
    url = urlparse(pomurl).path
    log('DEBUG','get_pom_dependencies from: '+str(url))
    statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,url,'GET','application/xml',NEXUS_USERNAME,NEXUS_PASSWORD,'')
    if statuscode != 200:
        raise Exception('Failed HTTP call','Was expecting code 200 and received '+str(statuscode))
    try:
        tree = ET.fromstring(res)
    except:
        log('DEBUG',"String no valid XML: "+str(res))
        raise
    return get_xpath_nodes_from_tree(tree,'./{http://maven.apache.org/POM/4.0.0}dependencies/{http://maven.apache.org/POM/4.0.0}dependency')    

#gets artifact poms as array of dict keys url,date
def get_artifact_poms():
    log('DEBUG','get_artifact_poms: '+NEXUS_BASE_ARTIFACT_SEARCH)
    artifact_poms = get_pomurls(NEXUS_BASE_ARTIFACT_SEARCH)
    return artifact_poms

#converts pom at url to dict, keys url,artifactid,groupid,version
def artifactpom_to_dict(pomurl):
    url = urlparse(pomurl).path
    result = {}
    log('DEBUG','artifactpom_to_dict from: '+str(url))
    statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,url,'GET','application/xml',NEXUS_USERNAME,NEXUS_PASSWORD,'')
    if statuscode != 200:
        raise Exception('Failed HTTP call','Was expecting code 200 and received '+str(statuscode))
    pom_el=''
    try:
        pom_el = ET.fromstring(res)
    except:
        log('DEBUG',"String no valid XML: "+str(res))
        raise
    result['url']=pomurl
    result['artifactid']=pom_el.find('./{http://maven.apache.org/POM/4.0.0}artifactId').text
    result['groupid']=pom_el.find('./{http://maven.apache.org/POM/4.0.0}groupId').text
    result['version']=pom_el.find('./{http://maven.apache.org/POM/4.0.0}version').text
    return result

#converts dependency elementtree to dict keys groupid,artifactid,version    
def dep_el_to_dict(dep_el):
    res = {}
    res['groupid']=dep_el.find('./{http://maven.apache.org/POM/4.0.0}groupId').text
    res['artifactid']=dep_el.find('./{http://maven.apache.org/POM/4.0.0}artifactId').text
    res['version']=dep_el.find('./{http://maven.apache.org/POM/4.0.0}version').text
    return res

#converts dependency dict to URL
def dep_dict_to_path(dep_dict):
    return NEXUS_BASE_CONTENT+'/'+dep_dict['groupid'].replace('.','/')+'/'+dep_dict['artifactid']+'/'+dep_dict['version']+'/'

#determine release dependencies. returns array of dependency dict keys groupid, artifactid, version, date (of the origin pom)
def get_release_depends(releasepoms):
    alldeps=[]
    for pom in releasepoms:
        nodes = get_pom_dependencies(pom['url'])
        for node in nodes:
            depdict=dep_el_to_dict(node)
            depdict['date']=pom['date']
            depdict['pom']=pom['url']
            alldeps.append(depdict)
            log('DEBUG','get_release_depends adding: '+str(depdict))
            deppomurl=dep_dict_to_path(depdict)
            log('DEBUG','get_release_depends looking for dependencies of dependencies')
            additionaldepends=get_pom_dependencies(deppomurl)
            log('DEBUG','get_release_depends found additional dependencies: '+str(len(additionaldepends)))
            alldeps.extend(additionaldepends)
    return alldeps

#converts array of pom dicts (keys url,date) to artifact dicts (keys artifactid,version,groupid)
def get_artifacts(artifactpoms):
    allartifacts=[]
    for pom in artifactpoms:
        artifactdict=artifactpom_to_dict(pom['url'])
        artifactdict['date']=pom['date']
        allartifacts.append(artifactdict)
        log('DEBUG','get_artifacts adding: '+str(artifactdict))
    return allartifacts

#remove artifact at url. used for artifacts such as war's but also releases. also removes subtree. this does the actual delete!
def delete_artifact(artifact):
    log('INFO','delete_artifact '+artifact['url'])
    if (artifact['url'].endswith('.pom')):
        delpath=artifact['url'].rsplit('/', 1)[0]
        log('INFO','delete_artifact path: '+delpath)
        if (DUMMYRUN != 'true'):
            statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,delpath,'DELETE','application/xml',NEXUS_USERNAME,NEXUS_PASSWORD,'')
            log('INFO','delete_artifact result: '+str(statuscode)+' '+str(statusmessage))
            if statuscode != 204:
                raise Exception('Failed HTTP call','Was expecting code 204 and received '+str(statuscode))

if DUMMYRUN == 'true':
    log('INFO','Executing dummy run')
else:
    log('INFO','Not executing dummy run!')

release_poms=get_release_poms()
log('INFO','Found '+str(len(release_poms))+' releases')

release_poms=sorted(release_poms, key=itemgetter('date'), reverse=True) 

def remove_old_releases(release_poms,beforedate,releasestokeep):
    releasesremoved=0
    releasesnotremoved=0
    releasecounter=0;
    newreleasepoms=[]
    for release_pom in release_poms:
        releasecounter=releasecounter+1
        if release_pom['date']<beforedate:
            if releasecounter>MINRELEASESTOKEEP:
                log('INFO','Removing old release: '+str(release_pom)+' because: '+str(release_pom['date'])+'<'+str(beforedate))
                delete_artifact(release_pom)
                releasesremoved=releasesremoved+1
            else:
                log('INFO','Not removing old release: '+str(release_pom)+' because keeping '+str(releasestokeep)+' releases')
                releasesnotremoved=releasesnotremoved+1
                newreleasepoms.append(release_pom)
        else:
            log('INFO','Not removing release: '+str(release_pom)+' because not old enough: '+str(release_pom['date'])+'>='+str(beforedate))
            releasesnotremoved=releasesnotremoved+1
            newreleasepoms.append(release_pom)    
    return newreleasepoms,releasesremoved,releasesnotremoved

log('INFO','Removing old releases (before: '+str(REMOVEBEFOREDATE)+') but keeping: '+str(MINRELEASESTOKEEP))
release_poms,releasesremoved,releasesnotremoved=remove_old_releases(release_poms,REMOVEBEFOREDATE,MINRELEASESTOKEEP)
log('INFO','Releases removed: '+str(releasesremoved))
log('INFO','Releases not removed: '+str(releasesnotremoved))
log('INFO','New number of releases: '+str(len(release_poms)))

release_depends=get_release_depends(release_poms)
log('INFO','Found '+str(len(release_depends))+' release dependencies')

#log('DEBUG',get_artifacts(get_artifact_poms()))
artifacts=get_artifacts(get_artifact_poms())
log('INFO','Found '+str(len(artifacts))+' artifacts')

def remove_old_artifacts(artifacts,beforedate):
    artifactsremoved=0
    artifactsnotremoved=0
    for artifact in artifacts:
        if artifact['date']<beforedate:
            for release_depend in release_depends:
                if release_depend['artifactid']==artifact['artifactid'] and release_depend['groupid']==artifact['groupid'] and release_depend['version']==artifact['version']:
                    log('INFO','Artifact found as dependency in release. Do not touch!: Artifact: '+str(artifact)+' Release: '+str(release_depend)) 
                    artifactsnotremoved=artifactsnotremoved+1
                    break;
            else:
                log('INFO','Artifact not found as dependency and old so remove: '+str(artifact))
                delete_artifact(artifact)
                artifactsremoved=artifactsremoved+1
        else:
            log('INFO','Artifact not older then oldest release. Do not touch!: '+str(artifact))
            artifactsnotremoved=artifactsnotremoved+1
    return artifactsremoved,artifactsnotremoved

artifactsremoved,artifactsnotremoved=remove_old_artifacts(artifacts,REMOVEBEFOREDATE)
log('INFO','Artifacts removed: '+str(artifactsremoved))
log('INFO','Artifacts not removed: '+str(artifactsnotremoved))


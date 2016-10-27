import json  
import httplib  
import base64  
import string 
import re 
import datetime
from urlparse import urlparse  
   
NEXUS_HOST = "localhost"  
NEXUS_PORT = "8081"  
NEXUS_USERNAME = "admin"  
NEXUS_PASSWORD = "admin123"  
scriptname = 'listrepo'
scriptlocation = 'IdeaProjects/NexusProject/src/main/groovy/testscript.groovy'
DEBUG='true'

def log(severity,msg):
    if severity is not 'DEBUG' or DEBUG is 'true':
        curtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print curtime+' '+str(severity)+' : '+str(msg)
   
def do_http_request(host,port,url,verb,contenttype,username,password,body):  
    # from http://mozgovipc.blogspot.nl/2012/06/python-http-basic-authentication-with.html  
    # base64 encode the username and password  
    auth = string.strip(base64.encodestring(username + ':' + password))  
    service = httplib.HTTP(host,port)  
       
    # write your headers  
    service.putrequest(verb, url)  
    service.putheader("Host", host)  
    service.putheader("User-Agent", "Python http auth")  
    service.putheader("Content-type", contenttype)  
    service.putheader("Authorization", "Basic %s" % auth)  
    service.putheader("Content-Length",str(len(body)))
    service.endheaders()  
    service.send(body)  
    # get the response  
    statuscode, statusmessage, header = service.getreply()  
    #print "Headers: ", header  
    res = service.getfile().read()  
    #print 'Content: ', res  
    return statuscode,statusmessage,header,res  

def process_file_to_single_line(filename):
    with open(filename, 'rt') as sourceFile:
        res = sourceFile.read()
        #remove package
        res=re.sub(r'^package.*?\n','',res)
        #remove comments
        res=re.sub(r'/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/','',res)
        #remove all newlines making it a single line
        res=re.sub(r'\n', '', res)
        return res

#below lines show currently loaded scripts
#statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,'/service/siesta/rest/v1/script/','GET','application/json',NEXUS_USERNAME,NEXUS_PASSWORD,'')
#log('DEBUG',str(statuscode)+" "+str(statusmessage)+" "+str(header)+" "+str(res))

#first remove the script if it is already there
statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,'/service/siesta/rest/v1/script/'+scriptname,'DELETE','application/json',NEXUS_USERNAME,NEXUS_PASSWORD,'')
if statuscode not in [204,404]:
    raise Exception('HTTP request failed','Expected HTTP status 204 or 404 as response to DELETE request to remove current script. Got: '+str(statuscode))
log('DEBUG','Deleted current script: '+str(scriptname))

#create a JSON request for the API
request='{"name": "'+str(scriptname)+'","type": "groovy","content": "'+process_file_to_single_line(scriptlocation)+'"}'
log('DEBUG','Request: '+str(request))

#upload a new version of the script
statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,'/service/siesta/rest/v1/script/','POST','application/json',NEXUS_USERNAME,NEXUS_PASSWORD,request)
if statuscode is not 204:
    raise Exception('HTTP request failed','Expected HTTP status 204 as response to POST request to upload new script. Got: '+str(statuscode))
log('DEBUG','Uploaded new version of script')

#execute the script
statuscode,statusmessage,header,res = do_http_request(NEXUS_HOST,NEXUS_PORT,'/service/siesta/rest/v1/script/'+scriptname+'/run','POST','text/plain',NEXUS_USERNAME,NEXUS_PASSWORD,'')
if statuscode is not 200:
    raise Exception('HTTP request failed','Expected HTTP status 200 as response to POST request to call the new script. Got: '+str(statuscode))
log('DEBUG','Script called. Response: '+str(res))


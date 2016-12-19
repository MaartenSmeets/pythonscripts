from requests import session 
import string  
import xml.etree.ElementTree as ET

WEBLOGIC_HOST="hostname"
WEBLOGIC_PORT="port"  
WEBLOGIC_USERNAME="username"  
WEBLOGIC_PASSWORD="password"  

payload = {
     'j_username': WEBLOGIC_USERNAME,
     'j_password': WEBLOGIC_PASSWORD
}

s = session()
baseurl = 'http://'+WEBLOGIC_HOST+':'+WEBLOGIC_PORT
s.post(baseurl+'/dms/j_security_check', data=payload)

response = s.get(baseurl+'/dms/Spy?operation=reset&format=raw&cache=refreshall&name=/&recurse=all')

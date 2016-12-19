from requests import session 
from operator import itemgetter
import string 
import os 
import re
import argparse
import xml.etree.ElementTree as ET

global args

WEBLOGIC_HOST="hostname"
WEBLOGIC_PORT="port"  
WEBLOGIC_USERNAME="username"  
WEBLOGIC_PASSWORD="password"  

def get_xpath_nodes_from_tree(element,xpath):
    return element.findall(xpath)

def print_et(et):
    print ET.tostring(et, encoding='utf8')

def get_et_from_string(res):
    return ET.fromstring(res)

def get_rows_from_tbml(tbml_et):
    return get_xpath_nodes_from_tree(tbml_et,'./table/row')
    
def get_columns_from_row(row_et):
    return get_xpath_nodes_from_tree(row_et,'./column')

def get_name_value_from_column(column_et):
    return column_et.get('name'),column_et.text
	
def exceldecimal(s):                   # voor de excel gebruikers
  return(re.sub('\.',',',s))          # decimale . naar ,
  
payload = {
     'j_username': WEBLOGIC_USERNAME,
     'j_password': WEBLOGIC_PASSWORD
}

s = session()
baseurl = 'http://'+WEBLOGIC_HOST+':'+WEBLOGIC_PORT
s.post(baseurl+'/dms/j_security_check', data=payload)

response = s.get(baseurl+'/dms/index.html?format=xml&cache=false&prefetch=false&table=wls_webservice_operation&orderby=Name')
tbml_et = get_et_from_string(response.text)
rows = get_rows_from_tbml(tbml_et)
result=[]

for row in rows:
  columns = get_columns_from_row(row)
  h,n,s,mint,maxt,avgt,comp='','','',0,0,0,0
  for column in columns:
    k,v = get_name_value_from_column(column)
    if k == 'Host':                 h    = v
    if k == 'Name':                 n    = v
    if k == 'wls_ear':              s    = v  
    if k == 'Invoke.minTime':       mint = exceldecimal(v)
    if k == 'Invoke.maxTime':       maxt = exceldecimal(v)
    if k == 'Invoke.avg':           avgt = exceldecimal(v)
    if k == 'Invoke.completed':     comp = int(v)

  if comp > 0:
    result.append([h,n,s,mint,maxt,avgt,comp])

result.sort(key=itemgetter(0))  #sorteren op wls_ear,name,host
result.sort(key=itemgetter(1))
result.sort(key=itemgetter(2))

result.insert(0, ['Host','Operation','Service','MinTime','MaxTime','AvgTime','Calls'])
for x in result:
  print(';'.join(map(str,x)))

from requests import session 
import string  
import xml.etree.ElementTree as ET

WEBLOGIC_HOST="localhost"
WEBLOGIC_PORT="7101"  
WEBLOGIC_USERNAME="weblogic"  
WEBLOGIC_PASSWORD="Welcome01"  
DEBUG='true'

def get_xpath_nodes_from_tree(element,xpath):
    return element.findall(xpath)

def print_et(et):
    print ET.tostring(et, encoding='utf8')

def get_et_from_string(res):
    return ET.fromstring(res)

def get_rows_from_tbml(tbml_et):
    return get_xpath_nodes_from_tree(tbml_et,'./{http://www.oracle.com/AS/collector}table/{http://www.oracle.com/AS/collector}row')
    
def get_columns_from_row(row_et):
    return get_xpath_nodes_from_tree(row_et,'./{http://www.oracle.com/AS/collector}column')

def get_name_value_from_column(column_et):
    return column_et.get('name'),column_et.text

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
firstrow='true'
for row in rows:
    columns = get_columns_from_row(row)
    if firstrow=='true':
        firstrow='false'
        firstcolumn='true'
        for column in columns:
            name,value = get_name_value_from_column(column)
            if firstcolumn == 'true':
                resstr = name
                firstcolumn='false'
            else:
                resstr = resstr+';'+name
        print resstr
    firstcolumn='true'
    resstr=''
    for column in columns:
        name,value = get_name_value_from_column(column)
        if firstcolumn == 'true':
            resstr = value
            firstcolumn='false'
        else:
            resstr = resstr+';'+value
    print resstr




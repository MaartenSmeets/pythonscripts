import concurrent.futures
import requests
from string import Template
import time
import xml.etree.ElementTree as ET

max_workers=20
inputfile='input.txt'
outputokfile='outputok.txt'
outputerrorfile='outputerror.txt'

url = 'http://localhost:7101/soa-infra/services/default/HelloWorld/helloworldprocess_client_ep'

messagetemplate=Template(r"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:hel="http://xmlns.oracle.com/Application1/HelloWorld/HelloWorldProcess">
   <soapenv:Header/>
   <soapenv:Body>
      <hel:process>
         <hel:input>$name</hel:input>
      </hel:process>
   </soapenv:Body>
</soapenv:Envelope>""")

headers = {'SOAPAction': 'process','Content-Type':'text/xml;charset=UTF-8'}

# Retrieve a single page and report the URL and contents
def fire_post_request(url, data,timeout):
    start_time = time.time()
    response=requests.post(url, data=data,timeout=timeout,headers=headers)
    end_time=time.time() - start_time
    return {'responsetime':end_time,'response':response}

def write(text,filename):
    file = open(filename, 'a')
    file.write(text)
    file.close()

# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    with open(inputfile) as f:
        future_to_line={}
        for line in f:
            process_name=line.rstrip('\n')
            data = messagetemplate.substitute(name=process_name)
            future_to_line[executor.submit(fire_post_request,url, data,60)]=process_name
        for future in concurrent.futures.as_completed(future_to_line):
            process_name_from_future = future_to_line[future]
            try:
                data = future.result()['response']
            except Exception as exc:
                write(process_name_from_future+' : '+str(exc)+"\n",outputerrorfile)
            else:
                try:
                    xml=ET.fromstring(data.text)
                    write(process_name_from_future+" : "+str(xml[1][0][0].text)+"\n",outputokfile)
                except Exception as exc:
                    write(process_name_from_future + ' : ' + str(exc) + "\n",outputerrorfile)
import concurrent.futures
import requests
from string import Template
import time
import xml.etree.ElementTree as ET

max_workers=20
inputfile='input.txt'
outputokfile='outputok.txt'
outputerrorfile='outputerror.txt'

urlTemplate = Template('https://zoeken.kvk.nl/search.ashx?handelsnaam=&kvknummer=$kvk_number&straat=&postcode=&huisnummer=&plaats=&hoofdvestiging=true&rechtspersoon=true&nevenvestiging=true&zoekvervallen=0&zoekuitgeschreven=0&start=0&initial=0&searchfield=uitgebreidzoeken')

headers = {'Content-Type':'text/xml;charset=UTF-8'}

# Retrieve a single page and report the URL and contents
def fire_get_request(url, timeout):
    start_time = time.time()
    response=requests.get(url, timeout=timeout,headers=headers)
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
            kvk_number=line.rstrip('\n')
            url =urlTemplate.substitute(kvk_number=kvk_number)
            future_to_line[executor.submit(fire_get_request,url,60)]=kvk_number
        for future in concurrent.futures.as_completed(future_to_line):
            kvk_number_from_future = future_to_line[future]
            try:
                data = future.result()['response']
            except Exception as exc:
                write(kvk_number_from_future+' : '+str(exc)+"\n",outputerrorfile)
            else:
                try:
                    if "Nevenvestiging" in str(data.text):
                        write(kvk_number_from_future + ' : ' + "Has branch offices\n", outputerrorfile)
                    elif "Helaas, er zijn geen resultaten voor uw zoekopdracht" in str(data.text):
                        write(kvk_number_from_future + ' : ' + "Not found\n", outputerrorfile)
                    else:
                        write(kvk_number_from_future+" : "+"One location found\n",outputokfile)
                except Exception as exc:
                    write(kvk_number_from_future + ' : ' + str(exc) + "\n",outputerrorfile)
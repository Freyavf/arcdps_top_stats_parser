import requests
import json

# Test function to send a request with links to the json page
# You can run this file to send the request
def get_raid_json():
    #url = 'http://127.0.0.1:5000/json'
    url = 'http://192.168.2.11:5678/json'
    #url = 'https://arc-parser-api.herokuapp.com/json'

    data = {'links':[
        {'href': 'https://dps.report/getJson?id=y0LO-20220127-203541'},
        {'href': 'https://dps.report/getJson?id=y0LO-20220127-203541'},
    ]}
    headers = {'Content-Type':'application/json'}

    r = requests.post(url, data=json.dumps(data), headers=headers)
    print(r.status_code)
    if r.status_code == 200:
        print(r.json())
    pass

get_raid_json()
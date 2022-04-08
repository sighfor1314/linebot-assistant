import requests
import json

class Weather:
    def __init__(self,config,msg):

        self.config= config
        self.msg=msg

    def get_info(self,city):

        cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園市', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣',
                  '臺中市', '宜蘭縣', '彰化縣', '澎湖縣', '南投縣', '金門縣', '雲林縣', '連江縣']

        city = self.msg[3:]
        city = city.replace('台', '臺')
        if city in cities:
            url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001'
            params = {
                "Authorization": self.config.get('Weather', 'authorization'),
                "locationName": city,
            }
            Data = requests.get(url, params=params)
            Data = json.loads(Data.text)
            return Data


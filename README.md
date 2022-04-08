## linebot-assistant
### 功能說明
<li>串接中央氣象局API查詢台灣6小時縣市天氣</li>
<li>透過Azure QnA Maker雲端式自然語言處理(NLP)，實現問答機器人</li>
<li>透過公共運輸整合資訊API查詢火車時刻表</li>

### 建立config.ini
建立建立config.ini 儲存各個API authorization
```
[line-bot]
channel_access_token=<channel_access_token>
channel_secret=<channel_secret>

[Transportation]
app_id = <app_id>
app_key = <app_key>

[Weather]
authorization=<authorization>

[QnAMaker]
url=<url>
authorization = <authorization>
```
### Heroku 部署必需檔案
####Procfile
告訴 Heroku 應用程式是哪種類型以及需要執行哪個檔案，Procfile是一個沒有副檔名的檔案
####requirements.txt
告訴 Heroku 需要安裝那些套件。
#####runtime.txt
告訴 Heroku 我們要用哪種版本的 Python 來執行應用程式。沒有設定會選擇預設的版本

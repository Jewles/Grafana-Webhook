from flask import request
from flask import Flask
import re
import urllib.request
import json
import os
import wechat_work_webhook


def Open(s):
    Path = '/home/we/temp.json'
    if os.path.exists(Path):
        os.remove(Path)
    f = open(Path, 'w')
    print(s, file = f)
    f.close()


def GetData():
    PostData = request.get_data()
    Data = json.loads(PostData)
    JsonData = json.dumps(Data, ensure_ascii=False, indent=4)
    return Data

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/wechat', methods=['POST'])
def IssueCreate():
    des = GetData()['commonAnnotations']['description']
    title =GetData()['commonLabels']['alertname']
    state = GetData()['status']
    time = GetData()['alerts'][0]['startsAt']
    t1 = str(re.findall(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", time))
    t2 = str(re.sub("T", " ", t1))
    wechat = wechat_work_webhook.connect(
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=You Token")
    wechat.markdown('告警主题: ' + '['+ state +']' + title +'\n'
                    '告警信息: '+ des +'\n'
                    '告警时间： ' + t2
                    )
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)

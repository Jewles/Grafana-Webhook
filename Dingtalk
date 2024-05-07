#!/usr/bin/python
# -*- coding: utf-8 -*-
#此代码更新了钉钉加签模式，可使用加签告警，无需设置相关词

from flask import Flask, request
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime

app = Flask(__name__)

def generate_dingtalk_signature(timestamp, secret):
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code)
    return urllib.parse.quote_plus(sign.decode('utf-8'))

@app.route('/dingtalk', methods=['POST'])
def webhook():
    data = json.loads(request.get_data())

    alert = data['alerts'][0]
    status = alert['status']
    labels = alert['labels']
    annotations = alert['annotations']
    print(alert)

    alertname = labels['alertname']
    #instance = labels['instance']
    summary = annotations['summary']
    description = annotations['description']


    if alertname == 'DatasourceError':
        return 'Filtered out'

    if status == "firing":
        start_time = datetime.strptime(alert['startsAt'][:19], '%Y-%m-%dT%H:%M:%S')
        alert_time = start_time
    elif status == "resolved":
        end_time = datetime.strptime(alert['endsAt'][:19], '%Y-%m-%dT%H:%M:%S')
        alert_time = end_time

    dingtalk_msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": "告警通知",
            "text": f"### {alertname}\n\n**告警状态**: {status}\n\n**告警级别**: {summary}\n\n**告警详情**: {description}\n\n**触发时间**: {alert_time}\n\n"
        },
        "at": {
            "isAtAll": False
        }
    }

    timestamp = str(round(time.time() * 1000))
    secret = '你的签'
    signature = generate_dingtalk_signature(timestamp, secret)
    access_token = '你的token'

    # 发送钉钉告警消息
    dingtalk_url = f'https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={signature}'
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    r = requests.post(dingtalk_url, headers=headers, data=json.dumps(dingtalk_msg))

    if r.status_code == 200:
        return 'ok'
    else:
        return 'error'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2222)

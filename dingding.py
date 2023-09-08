#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, request
import requests
import json
import time
from datetime import datetime

app = Flask(__name__)

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
            "atMobiles": [
                "180xxxxxxx"
            ],
            "isAtAll": False
        }
    }

    # 发送钉钉告警消息
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    dingtalk_url = 'https://oapi.dingtalk.com/robot/send?access_token=your-token'
    r = requests.post(dingtalk_url, headers=headers, data=json.dumps(dingtalk_msg))

    if r.status_code == 200:
        return 'ok'
    else:
        return 'error'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2222)

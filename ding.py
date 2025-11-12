#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
import pytz

#初始化flask应用实例
app = Flask(__name__)

#钉钉机器人 access_token
ACCESS_TOKEN = "986036cfcd1e5fe7fdcd601f531a6b6aa3fcc1f8840dd6c7a86e5dacc2726e82"
#钉钉 webhook 加签密钥（可选安全验证）
SECRET = "SEC067d355ecc2bd01700bf673b8f09d0aad3d3a690ce3d0c408f3afea77262bc32"
#设置本地时区为中国标准时间（UTC+8)
LOCAL_TZ = pytz.timezone('Asia/Shanghai')


def generate_dingtalk_signature(timestamp, secret):
    """
    生成钉钉 webhook 加签签名（sign）
    官方要求：HMAC-SHA256(timestamp + "\n" + secret)
    :param timestamp: 当前时间戳（毫秒）
    :param secret: 加签密钥
    :return: URL 编码后的签名字符串
    """
    if not secret:
        return ""  #没启用加签 → 不生成签名，直接反回空
    #把密钥转成字节（HMAC 需要 bytes）
    secret_enc = secret.encode('utf-8')

    #拼接：时间戳 + 换行 + 密钥
    string_to_sign = f'{timestamp}\n{secret}'

    #用 SHA256 对字符串做 HMAC 加密 → 得到二进制签名
    hmac_code = hmac.new(secret_enc, string_to_sign.encode('utf-8'), hashlib.sha256).digest()

    #base64.b64encode(hmac_code).decode()把二进制转成 Base64 字符串,urllib.parse.quote_plus(...)URL 编码
    return urllib.parse.quote_plus(base64.b64encode(hmac_code).decode())

def utc_to_local(iso_str):
    """
    将 Grafana 发送的 UTC 时间字符串转换为北京时间（UTC+8）
    :param iso_str: Grafana 发送的 ISO 时间字符串（如 2025-11-05T07:32:07.350Z）
    :return:格式化后的北京时间字符串，如 "2025-11-05 15:32:07"
    """
    try:
        #去掉毫秒和 'Z'，并补上 UTC 时区（+00:00）
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00').split('.')[0])
        #明确指定这是 UTC 时间
        dt_utc = dt.replace(tzinfo=pytz.UTC)
        #将 UTC 时间转换为本地时区（北京时间）
        dt_local = dt_utc.astimezone(LOCAL_TZ)
        #格式化输出
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"时间转换失败: {e}，原始: {iso_str}")
        # 降级处理：直接截取前19位并替换 T 为空格
        return iso_str[:19].replace('T', ' ')


@app.route('/go2', methods=['POST'])
def webhook():
    """
    Grafana 告警 Webhook 接收接口

    - 路径：/go2
    - 方法：POST
    - 功能：接收 Grafana 推送的告警数据，转换为钉钉 Markdown 消息
    - 请求格式：application/json
    :return:'ok' 或错误信息
    """
    try:
        #解析请求体中的 JSON 数据
        data = request.get_json()
        if not data:
            return 'no json', 400   #请求体为空或格式错误

        print("收到 Grafana 告警:", json.dumps(data, indent=2, ensure_ascii=False))

        # 如果 alerts 存在，且是 list 类型，且长度 > 0 → 取第一个告警：alert = data['alerts'][0]，否则：alert = data（直接用整个 JSON）
        if 'alerts' in data and isinstance(data['alerts'], list) and len(data['alerts']) > 0:
            alert = data['alerts'][0]
        else:
            alert = data

        status = alert.get('status', 'unknown')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})

        # 修复：用圆括号！
        alertname = labels.get('alertname', '未知告警')
        summary = annotations.get('summary', '无摘要')
        description = annotations.get('description', '无详情')

        start_time_local = utc_to_local(alert.get('startsAt', ''))
        end_time_local = utc_to_local(alert.get('endsAt', '')) if status == 'resolved' and not alert.get('endsAt', '').startswith('0001') else "进行中"

        print(f"告警名称: {alertname}")
        print(f"告警状态: {status}")
        print(f"告警级别: {summary}")
        print(f"告警详情: {description}")
        print(f"开始时间: {start_time_local}")
        if status == 'resolved':
            print(f"结束时间: {end_time_local}")

        status_emoji = "告警" if status == "firing" else "恢复"
        time_info = f"**开始时间**: `{start_time_local}`\n"
        if status == 'resolved' and end_time_local != "进行中":
            time_info += f"**结束时间**: `{end_time_local}`\n"

        dingtalk_msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{status_emoji} {alertname}",
                "text": f"###[{status_emoji}] {alertname}\n\n"
                        f"**告警状态**: {status_emoji} `{status}`\n\n"
                        f"**告警级别**: {summary}\n\n"
                        f"**告警详情**: {description}\n\n"
                        f"{time_info}\n"
                        f">海创网络监控"
            },
            "at": {"atMobiles": [], "isAtAll": False}
        }

        timestamp = str(round(time.time() * 1000))
        sign = generate_dingtalk_signature(timestamp, SECRET)
        # 修复：用 ACCESS_TOKEN！
        url = f"https://oapi.dingtalk.com/robot/send?access_token={ACCESS_TOKEN}"
        if sign:
            url += f"&timestamp={timestamp}&sign={sign}"

        r = requests.post(url, json=dingtalk_msg, headers={'Content-Type': 'application/json'}, timeout=10)
        result = r.json()

        if result.get('errcode') == 0:
            print("钉钉推送成功")
            return 'ok', 200
        else:
            print(f"钉钉推送失败: {result}")
            return 'error', 500

    except Exception as e:
        print(f"处理告警失败: {e}")
        return 'error', 500

if __name__ == '__main__':
    print("Grafana → 钉钉告警服务已启动")
    print(f"监听地址: http://0.0.0.0:6666/go2")
    print("时区: 北京时间 (UTC+8)")
    app.run(host='0.0.0.0', port=6666, debug=True, use_reloader=True)
import os
import requests
import random
from datetime import date, datetime
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage

# ==========================================================
# 1. 配置读取 (从环境变量获取，保护隐私)
# ==========================================================
# 微信配置
app_id = os.environ.get("APP_ID")
app_secret = os.environ.get("APP_SECRET")
user_id = os.environ.get("USER_ID")
template_id = os.environ.get("TEMPLATE_ID")

# 个人配置
start_date = os.environ.get("START_DATE") # 格式: 2023-01-01
birthday = os.environ.get("BIRTHDAY")     # 格式: 05-20

# 彩云天气配置
caiyun_token = os.environ.get("CAIYUN_TOKEN")
longitude = "112.51"  # 经度 (太原)
latitude = "37.83"   # 纬度 (太原)

# ==========================================================
# 2. 功能函数
# ==========================================================

def get_weather():
    """获取彩云天气数据"""
    url = f"https://api.caiyunapp.com/v2.6/{caiyun_token}/{longitude},{latitude}/weather?dailysteps=3&hourlysteps=48"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("status") != "ok":
            return "获取失败", "获取失败", "获取失败", "获取失败"
        
        result = res["result"]
        # 1. 温度与体感
        t = result["realtime"]["temperature"]
        at = result["realtime"]["apparent_temperature"]
        temp_info = f"{t}℃ (体感{at}℃)"
        
        # 2. 紫外线
        uv = result["realtime"]["life_index"]["ultraviolet"]["desc"]
        
        # 3. 穿衣指数
        dress = result["daily"]["dressing"][0]["desc"]
        
        # 4. 明天天气预报
        tom_sky = result["daily"]["skycon"][1]["value"]
        tom_max = result["daily"]["temperature"][1]["max"]
        tom_min = result["daily"]["temperature"][1]["min"]
        
        weather_map = {
            "CLEAR_DAY": "晴", "CLEAR_NIGHT": "晴", "PARTLY_CLOUDY_DAY": "多云",
            "PARTLY_CLOUDY_NIGHT": "多云", "CLOUDY": "阴", "LIGHT_RAIN": "小雨",
            "MODERATE_RAIN": "中雨", "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨",
            "LIGHT_SNOW": "小雪", "MODERATE_SNOW": "中雪", "HEAVY_SNOW": "大雪",
            "DUST": "浮尘", "SAND": "沙尘", "WIND": "大风"
        }
        tomorrow = f"{weather_map.get(tom_sky, '多云')} ({tom_min}~{tom_max}℃)"
        
        return temp_info, uv, dress, tomorrow
    except Exception as e:
        print(f"天气获取异常: {e}")
        return "数据出错", "查看预报", "查看建议", "数据出错"

def get_count():
    """计算纪念日天数"""
    today = datetime.now()
    delta = today - datetime.strptime(start_date, "%Y-%m-%d")
    return delta.days

def get_birthday():
    """计算生日倒计时"""
    today = datetime.now()
    next_bday = datetime.strptime(str(date.today().year) + "-" + birthday, "%Y-%m-%d")
    if next_bday < today:
        next_bday = next_bday.替换(year=next_bday.year + 1)
    return (next_bday - today).days

def get_words():
    """获取彩虹屁/情话"""
    for _ in range(3):
        try:
            r = requests.get("https://api.shadiao.pro/chp", timeout=5)
            if r.status_code == 200:
                return r.json()['data']['text']
        except:
            continue
    return "遇见你，是我生命中最美好的意外。"

def get_random_color():
    """生成随机颜色"""
    return "#%06x" % random.randint(0, 0xFFFFFF)

# ==========================================================
# 3. 主程序执行
# ==========================================================

if __name__ == "__main__":
    # 初始化微信客户端
    client = WeChatClient(app_id, app_secret)
    wm = WeChatMessage(client)
    
    # 获取所有数据
    temp_info, uv, dress, tomorrow = get_weather()
    love_days = get_count()
    birthday_left = get_birthday()
    words = get_words()
    
    # 构造模板数据
    data = {
        "temp_info": {"value": temp_info, "color": "#FF8C00"},
        "uv": {"value": uv, "color": "#FF4500"},
        "dressing": {"value": dress, "color": "#00BFFF"},
        "tomorrow": {"value": tomorrow, "color": "#1E90FF"},
        "love_days": {"value": love_days, "color": "#FFC0CB"},
        "birthday_left": {"value": birthday_left, "color": "#FFA500"},
        "words": {"value": words, "color": get_random_color()}
    }
    
    # 发送推送
    try:
        res = wm.send_template(user_id, template_id, data)
        print("推送成功结果:", res)
    except Exception as e:
        print("推送失败，请检查环境变量配置:", e)

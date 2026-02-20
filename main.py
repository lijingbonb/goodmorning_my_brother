import os
import requests
import random
import traceback
from datetime import date, datetime
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage

# ==========================================================
# 1. 配置读取
# ==========================================================
# 微信配置
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
    """获取并解析天气数据，带详细日志捕捉"""
    # 使用 dailysteps=2 确保能拿到明天的数据
    url = f"https://api.caiyunapp.com/v2.6/{caiyun_token}/{longitude},{latitude}/weather?dailysteps=2"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        r = response.json()
        
        if r.get("status") != "ok":
            print(f"❌ 彩云API返回状态异常: {r.get('status')}")
            return "状态异常", "N/A", "N/A", "N/A"
        
        res = r["result"]
        
        # 天气现象映射表
        weather_map = {
            "CLEAR_DAY": "晴天", "CLEAR_NIGHT": "晴天", 
            "PARTLY_CLOUDY_DAY": "多云", "PARTLY_CLOUDY_NIGHT": "多云", 
            "CLOUDY": "阴天", "LIGHT_RAIN": "小雨", "MODERATE_RAIN": "中雨",
            "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨", "LIGHT_SNOW": "小雪",
            "MODERATE_SNOW": "中雪", "HEAVY_SNOW": "大雪", "WIND": "大风",
            "DUST": "浮尘", "SAND": "沙尘", "FOG": "雾", "HAZE": "霾"
        }

        # --- 1. 当前气温解析 ---
        skycon_now = weather_map.get(res["realtime"]["skycon"], "晴天")
        atemp = res["realtime"]["apparent_temperature"] # 体感温度
        t_max = res["daily"]["temperature"][0]["max"]   # 今日最高
        t_min = res["daily"]["temperature"][0]["min"]   # 今日最低
        
        # 格式：晴天 1°-13° (体感温度5°)
        temp_info = f"{skycon_now} {int(t_min)}°-{int(t_max)}° (体感温度{int(atemp)}°)"

        # --- 2. 紫外线强度 ---
        uv = res["realtime"]["life_index"]["ultraviolet"]["index"]

        # --- 3. 穿衣建议 ---
        # 路径: daily -> life_index -> dressing[0] -> desc
        dress = res["daily"]["life_index"]["dressing"][0]["desc"]

        # --- 4. 明日天气解析 ---
        skycon_tom_key = res["daily"]["skycon"][1]["value"]
        skycon_tom = weather_map.get(skycon_tom_key, "多云")
        tom_max = res["daily"]["temperature"][1]["max"]
        tom_min = res["daily"]["temperature"][1]["min"]
        
        # 格式：多云 1°-13°
        tomorrow = f"{skycon_tom} {int(tom_min)}°-{int(tom_max)}°"

        print("✅ 天气数据解析成功")
        return temp_info, uv, dress, tomorrow

    except Exception as e:
        print("❌ 天气解析发生严重错误，详细堆栈如下：")
        traceback.print_exc() 
        return "数据获取异常", "查看详情", "查看详情", "查看详情"

def get_count():
    """计算纪念日天数"""
    try:
        today = datetime.now()
        delta = today - datetime.strptime(start_date, "%Y-%m-%d")
        return delta.days
    except:
        return 0

def get_birthday():
    """计算生日倒计时"""
    try:
        today = datetime.now()
        # 构造当年的生日日期
        next_bday = datetime.strptime(str(date.today().year) + "-" + birthday, "%Y-%m-%d")
        if next_bday < today:
            next_bday = next_bday.replace(year=next_bday.year + 1)
        return (next_bday - today).days
    except:
        return 0

def get_words():
    """获取情话，带多重保底"""
    try:
        r = requests.get("https://api.shadiao.pro/chp", timeout=5)
        if r.status_code == 200:
            return r.json()['data']['text']
    except:
        pass
    
    # 保底情话池
    words_list = [
        "遇见你，是我生命中最美好的意外。",
        "要把所有的温柔和可爱，都藏起来留给你。",
        "你是我这一生，等了半世的未完待续。",
        "想和你虚度时光，比如低头看鱼，比如抬头看你。"
    ]
    return random.choice(words_list)

# ==========================================================
# 3. 主程序执行
# ==========================================================

if __name__ == "__main__":
    print(f"🚀 程序启动... 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 初始化微信客户端
    try:
        client = WeChatClient(app_id, app_secret)
        wm = WeChatMessage(client)
    except Exception as e:
        print(f"❌ 微信客户端初始化失败: {e}")
        exit(1)
    
    # 2. 获取所有数据
    temp_info, uv, dressing, tomorrow = get_weather()
    love_days = get_count()
    birthday_left = get_birthday()
    words = get_words()
    
    # 3. 构造模板数据 (对应你之前的微信模板)
    data = {
        "temp_info": {"value": temp_info},
        "uv": {"value": str(uv)},
        "dressing": {"value": dressing},
        "tomorrow": {"value": tomorrow},
        "love_days": {"value": str(love_days)},
        "birthday_left": {"value": str(birthday_left)},
        "words": {"value": words}
    }
    
    # 4. 发送推送
    try:
        res = wm.send_template(user_id, template_id, data)
        print("🎉 推送成功结果:", res)
    except Exception as e:
        print("❌ 推送失败，堆栈如下:")
        traceback.print_exc()
        
        
        

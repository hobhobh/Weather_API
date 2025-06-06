from flask import Flask, jsonify, request
import requests
import sqlite3
import time

app = Flask(__name__)

# 配置天气API的URL和API密钥
API_KEY = '8969c22e1429653ea26b1fb4c1a48232'  # 替换为你的API密钥
API_URL = 'http://api.openweathermap.org/data/2.5/weather'

def create_table():
    """确保数据库中有 weather_cache 表"""
    conn = sqlite3.connect('weather_cache.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS weather_cache 
                       (city TEXT, temperature REAL, humidity REAL, windspeed REAL, description TEXT, timestamp INTEGER)''')
    conn.commit()
    conn.close()

def fetch_weather_from_api(city):
    """调用外部API获取天气数据"""
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'  # 获取以摄氏度为单位的温度
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def cache_weather_data(city, weather_data):
    """将天气数据缓存到本地数据库"""
    conn = sqlite3.connect('weather_cache.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO weather_cache (city, temperature, humidity, windspeed, description, timestamp) 
                       VALUES (?, ?, ?, ?, ?, ?)''', 
                   (city, weather_data['main']['temp'], weather_data['main']['humidity'], weather_data['wind']['speed'], 
                    weather_data['weather'][0]['description'], int(time.time())))
    conn.commit()
    conn.close()

@app.route('/api/v1/weather/<city>', methods=['GET'])
def get_weather(city):
    """查询指定城市的天气"""
    # 查询缓存
    conn = sqlite3.connect('weather_cache.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM weather_cache WHERE city = ? AND timestamp > ? ORDER BY timestamp DESC LIMIT 1''', 
                   (city, int(time.time()) - 3600))  # 缓存有效期：1小时
    result = cursor.fetchone()
    
    if result:
        return jsonify({
            'status': 'success',
            'data': {
                'temperature': result[1],
                'humidity': result[2],
                'windspeed': result[3],
                'description': result[4]
            }
        })
    else:
        # 如果缓存没有，调用外部API
        weather_data = fetch_weather_from_api(city)
        if weather_data:
            cache_weather_data(city, weather_data)
            return jsonify({
                'status': 'success',
                'data': {
                    'temperature': weather_data['main']['temp'],
                    'humidity': weather_data['main']['humidity'],
                    'windspeed': weather_data['wind']['speed'],
                    'description': weather_data['weather'][0]['description']
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'City not found or API error.'
            })

if __name__ == '__main__':
    create_table()  # 在启动应用之前确保表已经创建
    app.run(debug=True)

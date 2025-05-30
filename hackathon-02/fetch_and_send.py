import requests
import json
import time

API_KEY = "<not entering API Key since committing to git>"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
CITY_NAME = "trivandrum"
PI_IP_ADDRESS = "192.168.250.169"
PI_PORT = 5000
FETCH_INTERVAL = 1

def get_weather_data(city_name):
    try:
        params = {
            "appid": API_KEY,
            "q": city_name,
            "units": "metric"
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding weather JSON: {e}")
        return None

def send_data_to_pi(data):
    if data is None:
        return False
    try:
        pi_url = f"http://{PI_IP_ADDRESS}:{PI_PORT}/update_weather" # Flask endpoint
        headers = {'Content-Type': 'application/json'}
        response = requests.post(pi_url, data=json.dumps(data), headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Successfully sent data to Pi. Response: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Pi: {e}")
        return False

if __name__ == "__main__":
    if API_KEY == "YOUR_OPENWEATHERMAP_API_KEY" or PI_IP_ADDRESS == "YOUR_RASPBERRY_PI_IP_ADDRESS":
        print("CRITICAL: Please update API_KEY and PI_IP_ADDRESS in fetch_and_send.py")
        exit()

    print(f"Starting weather fetcher for {CITY_NAME}.")
    print(f"Will send data to Raspberry Pi at {PI_IP_ADDRESS}:{PI_PORT}")
    print(f"Fetching every {FETCH_INTERVAL} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            print(f"\nFetching weather for {CITY_NAME}...")
            weather_json = get_weather_data(CITY_NAME)
            if weather_json:
                print("Weather data fetched.")
                send_data_to_pi(weather_json)
            else:
                print("Failed to fetch or send weather data.")
            
            print(f"Waiting for {FETCH_INTERVAL} seconds...")
            time.sleep(FETCH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping weather fetcher.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
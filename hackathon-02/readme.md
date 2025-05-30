# Weather Display System
 
Real-time weather datat fetched at an interval of 60 seconds from **OpenWeatherMap API** on a PC and sends it to a **Raspberry Pi 4** over Wi-Fi. The **OLED screen (Pioneer600 HAT)** and controls the **LED** on the Pioneer600 when crossing a temperature threshold.
 
## Components Used
 
- Raspberry Pi 4 with Pioneer600 HAT
- SSD1306 OLED Display (via the Pioneer600
- LED connected to GPIO26
- Laptop (acts as the server fetching the weather data)
 
## How It Works
 
1. **Client Side (Laptop):**
   - Fetches the following(from the OpenWeather API) for Trivandrum location: Temperature, Pressure, Condition.
   - The JSON data is sent to the Raspberry Pi's IP Address over TCP.
 
2. **Server Side (Raspberry Pi):**
   - Listens on port `5000` for incoming weather data.
   - Weather condition is displayed on the OLED screen.
   - **LED** switched **ON** or **OFF** if temperature treshhold **exceeds** or **falls below** 30°C.
 
---

## Instructions
 
### Run the server
  - python fetch_and_send.py
### Run the client(application on the Raspberry Pi)
  - python main.py
  
---
 
### Example output at Client Side
  -> Temp: 24.5°C
  -> Pressure: 1013 hPa
  -> Condition: Heavy intensity rain
  
  
### Example output at Server side
  -> Fetching weather for trivandrum...
  -> Weather data fetched.
  -> Successfully sent data to Pi. Response: {"message":"Weather data processed successfully"}

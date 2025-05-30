# main_app.py
from flask import Flask, request, jsonify
import oled_driver
import led_controller
import signal
import sys
import time

# --- Configuration ---
# For Pioneer 600 integrated OLED, typical pins are:
# OLED_RST_PIN = 27
# OLED_DC_PIN = 22
# If using other pins with a standalone OLED, adjust accordingly.
OLED_RST_PIN = 19  # As per your initial code
OLED_DC_PIN = 16   # As per your initial code
OLED_SPI_BUS = 0
OLED_SPI_DEVICE = 0

LED_GPIO_PIN = 26  # BCM pin for the LED
TEMPERATURE_THRESHOLD = 30.0  # Celsius

# --- Global objects ---
app = Flask(__name__)
disp = None
oled_font = None # Using default font from oled_driver

# --- Flask Route ---
@app.route('/update_weather', methods=['POST'])
def update_weather():
    global disp, oled_font
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    print(f"Received data: {data}")

    try:
        # Extract relevant weather details
        # Adjust keys based on OpenWeatherMap JSON structure
        main_data = data.get('main', {})
        temperature = main_data.get('temp')
        pressure = main_data.get('pressure')
        
        weather_list = data.get('weather', [])
        condition = "N/A"
        if weather_list:
            condition = weather_list[0].get('description', "N/A").capitalize()

        # Update OLED display
        if disp:
            oled_driver.draw_weather_on_oled(disp, temperature, pressure, condition, font=oled_font)
            print("OLED Updated.")
        else:
            print("OLED display not initialized.")

        # Control LED based on temperature
        if temperature is not None:
            if temperature > TEMPERATURE_THRESHOLD:
                led_controller.led_on()
                print(f"Temp {temperature}°C > {TEMPERATURE_THRESHOLD}°C. LED ON.")
            else:
                led_controller.led_off()
                print(f"Temp {temperature}°C <= {TEMPERATURE_THRESHOLD}°C. LED OFF.")
        else:
            led_controller.led_off() # Turn off if no temp data
            print("No temperature data, LED OFF.")

        return jsonify({"message": "Weather data processed successfully"}), 200

    except Exception as e:
        print(f"Error processing weather data: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500

# --- Cleanup Function ---
def signal_handler(sig, frame):
    print('\nCtrl+C detected. Shutting down gracefully...')
    if disp:
        disp.cleanup()
    led_controller.cleanup_led()
    # Give Flask a moment to finish current requests if any, then exit.
    # For a more robust shutdown, you might need to stop the dev server differently.
    sys.exit(0)

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Weather Display Application on Raspberry Pi...")

    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize OLED
    try:
        disp = oled_driver.SSD1306(
            rst_pin=OLED_RST_PIN,
            dc_pin=OLED_DC_PIN,
            spi_bus=OLED_SPI_BUS,
            spi_device=OLED_SPI_DEVICE
        )
        # You can load a custom font here if needed for oled_driver.draw_weather_on_oled
        # from PIL import ImageFont
        # oled_font = ImageFont.truetype("path/to/your/font.ttf", 10)
        print("OLED initialized. Displaying initial message.")
        oled_driver.draw_weather_on_oled(disp, None, None, "Waiting...", font=oled_font)

    except Exception as e:
        print(f"Failed to initialize OLED: {e}. Exiting.")
        sys.exit(1)

    # Initialize LED
    if not led_controller.setup_led(LED_GPIO_PIN):
        print(f"Failed to initialize LED on pin {LED_GPIO_PIN}. Check GPIO setup. LED functionality will be disabled.")
        # Continue without LED if setup fails, or sys.exit(1) if critical


    # Run Flask app
    # For production, use a proper WSGI server like Gunicorn or uWSGI
    # Example: gunicorn -w 4 -b 0.0.0.0:5000 main_app:app
    print("Starting Flask server on port 5000...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False) # debug=False for less console output
    except Exception as e:
        print(f"Flask server failed to start: {e}")
    finally:
        # This finally block might not always be reached if Flask's internal
        # shutdown doesn't propagate KeyboardInterrupt well, hence signal_handler
        print("Flask server stopped. Performing final cleanup.")
        if disp: # Ensure cleanup if not caught by signal handler
            disp.cleanup()
        led_controller.cleanup_led()
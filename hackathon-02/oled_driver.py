import spidev
import lgpio
import time
from PIL import Image, ImageDraw, ImageFont

class SSD1306:
    def __init__(self, rst_pin, dc_pin, spi_bus=0, spi_device=0, width=128, height=64):
        self.rst_pin = rst_pin
        self.dc_pin = dc_pin
        self.width = width
        self.height = height
        self.pages = height // 8
        self.buffer = [0x00] * (self.width * self.pages)
        
        self.spi = None
        self.chip_handle = -1

        try:
            self.spi = spidev.SpiDev()
            self.spi.open(spi_bus, spi_device)
            self.spi.max_speed_hz = 8000000
            self.spi.mode = 0b00

            self.chip_handle = lgpio.gpiochip_open(0)
            if self.chip_handle < 0:
                raise RuntimeError(f"Failed to open gpiochip0: {lgpio.lasterror(self.chip_handle)}")

            res = lgpio.gpio_claim_output(self.chip_handle, self.dc_pin, 0)
            if res < 0: raise RuntimeError(f"Failed to claim DC pin {self.dc_pin}: {lgpio.lasterror(res)}")
            
            res = lgpio.gpio_claim_output(self.chip_handle, self.rst_pin, 0)
            if res < 0: raise RuntimeError(f"Failed to claim RST pin {self.rst_pin}: {lgpio.lasterror(res)}")

            self._reset()
            self._initialize_display()
            self.clear()
            self.show()
            print("SSD1306 Initialized")

        except Exception as e:
            print(f"SSD1306 Init Error: {e}")
            self.cleanup()
            raise

    def _reset(self):
        if self.chip_handle < 0: return
        lgpio.gpio_write(self.chip_handle, self.rst_pin, 0)
        time.sleep(0.01)
        lgpio.gpio_write(self.chip_handle, self.rst_pin, 1)
        time.sleep(0.1)

    def _command(self, cmd):
        if self.chip_handle < 0: return
        lgpio.gpio_write(self.chip_handle, self.dc_pin, 0)  # D/C# low for command
        self.spi.writebytes([cmd])

    def _data(self, data):
        if self.chip_handle < 0: return
        lgpio.gpio_write(self.chip_handle, self.dc_pin, 1)  # D/C# high for data
        self.spi.writebytes(data if isinstance(data, list) else [data])

    def _initialize_display(self):
        # Initialization sequence for SSD1306
        self._command(0xAE)  # Display OFF
        self._command(0xD5)  # Set Display Clock Divide Ratio/Oscillator Frequency
        self._command(0x80)  # Default Ratio
        self._command(0xA8)  # Set Multiplex Ratio
        self._command(self.height - 1)
        self._command(0xD3)  # Set Display Offset
        self._command(0x00)  # No offset
        self._command(0x40 | 0x0)  # Set Display Start Line (0)
        self._command(0x8D)  # Charge Pump Setting
        self._command(0x14)  # Enable Charge Pump
        self._command(0x20)  # Memory Addressing Mode
        self._command(0x00)  # Horizontal Addressing Mode
        self._command(0xA0 | 0x1)  # Set Segment Re-map (A0: normal, A1: remapped)
        self._command(0xC0 | 0x8)  # Set COM Output Scan Direction (C0: normal, C8: remapped)
        self._command(0xDA)  # Set COM Pins Hardware Configuration
        self._command(0x12 if self.height == 64 else 0x02) # Check height for 0x12 or 0x02
        self._command(0x81)  # Set Contrast Control
        self._command(0xCF)  # Default Contrast
        self._command(0xD9)  # Set Pre-charge Period
        self._command(0xF1)
        self._command(0xDB)  # Set VCOMH Deselect Level
        self._command(0x40)
        self._command(0xA4)  # Entire Display ON (resume to RAM content display)
        self._command(0xA6)  # Normal Display (not inverted)
        self._command(0xAF)  # Display ON

    def clear(self):
        self.buffer = [0x00] * (self.width * self.pages)
        # self.show() # Optionally show cleared screen immediately

    def show(self):
        self._command(0x21)  # Set Column Address
        self._command(0)     # Column Start Address (0)
        self._command(self.width - 1)  # Column End Address (127)
        self._command(0x22)  # Set Page Address
        self._command(0)     # Page Start Address (0)
        self._command(self.pages - 1) # Page End Address (N-1)
        self._data(self.buffer)

    def process_image_to_buffer(self, image):
        if image.width != self.width or image.height != self.height:
            image = image.resize((self.width, self.height))
        image = image.convert('1')  # Convert to monochrome
        
        pixels = image.load()
        self.buffer = [0x00] * (self.width * self.pages) # Clear buffer

        for page in range(self.pages):
            for x_coord in range(self.width):
                byte = 0
                for bit_idx in range(8): # 8 bits per byte, for 8 rows in a page
                    y_coord = (page * 8) + bit_idx
                    if pixels[x_coord, y_coord] > 0: # if pixel is white
                        byte |= (1 << bit_idx)
                self.buffer[x_coord + page * self.width] = byte

    def cleanup(self):
        print("Cleaning up OLED resources...")
        try:
            if self.spi: # Check if spi was initialized
                self.clear()
                self.show()
                self._command(0xAE)  # Display OFF
        except Exception as e:
            print(f"Error during OLED off: {e}")
        
        if self.chip_handle >= 0:
            # Attempt to free GPIOs if claimed, lgpio might auto-free on close
            # For explicit freeing:
            # lgpio.gpio_free(self.chip_handle, self.rst_pin)
            # lgpio.gpio_free(self.chip_handle, self.dc_pin)
            lgpio.gpiochip_close(self.chip_handle)
            self.chip_handle = -1
            print("lgpio chip closed.")
        if self.spi:
            self.spi.close()
            self.spi = None
            print("SPI closed.")
        print("OLED cleanup finished.")

# --- Drawing Helper Function ---
DEFAULT_FONT = ImageFont.load_default()

def draw_weather_on_oled(disp_obj, temp, pressure, condition, font=None):
    if not disp_obj:
        print("Error: Display object not initialized.")
        return

    if font is None:
        font = DEFAULT_FONT
    
    image = Image.new('1', (disp_obj.width, disp_obj.height))
    draw = ImageDraw.Draw(image)

    # Clear background (fill with black)
    draw.rectangle((0, 0, disp_obj.width, disp_obj.height), outline=0, fill=0)

    # Prepare text (handle None values gracefully)
    temp_str = f"Temp: {temp:.1f}C" if temp is not None else "Temp: N/A"
    press_str = f"Pres: {pressure:.0f}hPa" if pressure is not None else "Pres: N/A"
    cond_str = f"Cond: {condition}" if condition else "Cond: N/A"
    
    # Truncate condition if too long for one line
    # A more sophisticated approach would be text wrapping
    max_cond_len = disp_obj.width // 6 # Rough estimate for default font char width
    if len(cond_str) > len("Cond: ") + max_cond_len :
        cond_str = cond_str[:len("Cond: ") + max_cond_len -3] + "..."


    line_height = 10 # Approximate for default font
    padding = 2

    draw.text((padding, padding), temp_str, font=font, fill=255)
    draw.text((padding, padding + line_height), press_str, font=font, fill=255)
    draw.text((padding, padding + line_height * 2), cond_str, font=font, fill=255)

    disp_obj.process_image_to_buffer(image)
    disp_obj.show()
# main.py
import sys
from PyQt5 import QtCore, QtGui, QtWidgets # QtWidgets needed for QApplication
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog # Keep QFileDialog
from PyQt5.QtGui import QImage, QPixmap # Keep these for conversion

from gui import Ui_ImageEditorGUI # Your generated UI class
from logic import ImageLogic      # Your image processing logic class

class ImageEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ImageEditorGUI()
        self.ui.setupUi(self)

        self.image_logic = ImageLogic(
            gui_update_callback=self.display_pil_image_in_gui,
            gui_history_callback=self.update_history_buttons_state,
            gui_status_callback=self.ui.statusbar.showMessage,
            gui_reset_sliders_callback=self.reset_all_sliders_to_default
        )

        # self.current_processed_pil_image_for_preview = None # This might not be needed if previews are simple

        # --- Connect UI signals to slots ---
        # Top Controls
        self.ui.uploadButton.clicked.connect(self.upload_image)
        self.ui.saveButton.clicked.connect(self.save_image)
        self.ui.undoButton.clicked.connect(self.image_logic.undo_last_change)
        self.ui.revertButton.clicked.connect(self.image_logic.revert_all_changes)

        # Transform Tab
        # self.ui.rotateSlider.valueChanged.connect(self.rotate_image_preview) # REMOVE THIS
        # Make sure your .ui file has rotateLeftButton and rotateRightButton
        # and you have regenerated gui.py
        if hasattr(self.ui, 'rotateLeftButton'): # Check if buttons exist
            self.ui.rotateLeftButton.clicked.connect(lambda: self.image_logic.apply_operation("rotate_left", 90, is_preview=False))
            self.ui.rotateRightButton.clicked.connect(lambda: self.image_logic.apply_operation("rotate_right", -90, is_preview=False))
        else:
            print("WARNING: rotateLeftButton or rotateRightButton not found in UI. Did you update .ui and regenerate gui.py?")

        self.ui.flipHorizontalButton.clicked.connect(lambda: self.image_logic.apply_operation("flip_horizontal", None, is_preview=False))
        self.ui.flipVerticalButton.clicked.connect(lambda: self.image_logic.apply_operation("flip_vertical", None, is_preview=False))
        self.ui.resizeSlider.valueChanged.connect(self.resize_image_preview)
        self.ui.applyResizeButton.clicked.connect(self.apply_current_resize)

        # Filter Tab
        self.ui.grayscaleButton.clicked.connect(lambda: self.image_logic.apply_operation("grayscale", None, is_preview=False))
        self.ui.gaussianBlurSlider.valueChanged.connect(self.gaussian_blur_preview)
        # Consider adding apply button for blurs or connect to sliderReleased
        # For simplicity, let's make blurs definitive on slider change for now, or add apply buttons later
        # self.ui.gaussianBlurSlider.sliderReleased.connect(lambda: self.image_logic.apply_operation("gaussian_blur", self.ui.gaussianBlurSlider.value(), is_preview=False))


        self.ui.medianBlurSlider.valueChanged.connect(self.median_blur_preview)
        # self.ui.medianBlurSlider.sliderReleased.connect(lambda: self.image_logic.apply_operation("median_blur", self.ui.medianBlurSlider.value(), is_preview=False))


        # Edge Detection Tab
        self.ui.sobelButton.clicked.connect(lambda: self.image_logic.apply_operation("sobel", None, is_preview=False))
        self.ui.cannyThresh1Slider.valueChanged.connect(self.canny_preview)
        self.ui.cannyThresh2Slider.valueChanged.connect(self.canny_preview)
        self.ui.applyCannyButton.clicked.connect(self.apply_current_canny)

        # Morphology Tab
        self.ui.thresholdSlider.valueChanged.connect(self.threshold_preview)
        self.ui.erosionSlider.valueChanged.connect(self.erosion_preview)
        self.ui.dilationSlider.valueChanged.connect(self.dilation_preview)
        # Consider making these definitive or add apply buttons


        # Adjustment Tab
        self.ui.brightnessSlider.valueChanged.connect(self.brightness_preview)
        self.ui.contrastSlider.valueChanged.connect(self.contrast_preview)
        self.ui.applyAdjustmentsButton.clicked.connect(self.apply_current_adjustments)

        # Initial UI state
        self.update_history_buttons_state(False, False)
        self.ui.saveButton.setEnabled(False)


    def display_pil_image_in_gui(self, pil_image, panel_name):
        label_to_update = None
        if panel_name == "original":
            label_to_update = self.ui.originalImageLabel
        elif panel_name == "processed":
            label_to_update = self.ui.processedImageLabel
        else:
            self.ui.statusbar.showMessage(f"Error: Unknown panel '{panel_name}'"); return

        if pil_image is None:
            label_to_update.clear(); label_to_update.setText("No image"); return

        try:
            q_image = None
            if pil_image.mode == 'RGB':
                q_image = QImage(pil_image.tobytes("raw", "RGB"), pil_image.width, pil_image.height, QImage.Format_RGB888)
            elif pil_image.mode == 'RGBA':
                q_image = QImage(pil_image.tobytes("raw", "RGBA"), pil_image.width, pil_image.height, QImage.Format_RGBA8888)
            elif pil_image.mode == 'L':
                q_image = QImage(pil_image.tobytes("raw", "L"), pil_image.width, pil_image.height, QImage.Format_Grayscale8)
            elif pil_image.mode == '1':
                pil_gray = pil_image.convert('L')
                q_image = QImage(pil_gray.tobytes("raw", "L"), pil_gray.width, pil_gray.height, QImage.Format_Grayscale8)
            else:
                pil_rgba = pil_image.convert('RGBA')
                q_image = QImage(pil_rgba.tobytes("raw", "RGBA"), pil_rgba.width, pil_rgba.height, QImage.Format_RGBA8888)
                # self.ui.statusbar.showMessage(f"Displaying mode '{pil_image.mode}' as RGBA.") # Less noisy

            if q_image is None or q_image.isNull(): # Check if q_image was successfully created
                label_to_update.setText("Error: QImage conversion failed."); return

            pixmap = QPixmap.fromImage(q_image)
            if label_to_update.width() > 1 and label_to_update.height() > 1: # Ensure label has size
                 scaled_pixmap = pixmap.scaled(label_to_update.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                 label_to_update.setPixmap(scaled_pixmap)
            else:
                 label_to_update.setPixmap(pixmap) # Set unscaled if label size not determined

        except Exception as e:
            label_to_update.setText(f"Display Error");
            self.ui.statusbar.showMessage(f"Error displaying image: {e}")
            print(f"Error in display_pil_image_in_gui for {panel_name}: {e}")


    def update_history_buttons_state(self, can_undo, can_revert):
        self.ui.undoButton.setEnabled(can_undo)
        self.ui.revertButton.setEnabled(can_revert and bool(self.image_logic.original_pil_image)) # Revert needs original
        self.ui.saveButton.setEnabled(bool(self.image_logic.current_pil_image))

    def reset_all_sliders_to_default(self):
        sliders_to_reset = [
            (self.ui.resizeSlider, 100),
            (self.ui.gaussianBlurSlider, 1), (self.ui.medianBlurSlider, 1),
            (self.ui.cannyThresh1Slider, 50), (self.ui.cannyThresh2Slider, 150),
            (self.ui.thresholdSlider, 127),
            (self.ui.erosionSlider, 1), (self.ui.dilationSlider, 1),
            (self.ui.brightnessSlider, 100), (self.ui.contrastSlider, 100)
        ]
        # Remove rotateSlider if it's gone from UI
        if hasattr(self.ui, 'rotateSlider'):
            sliders_to_reset.insert(0, (self.ui.rotateSlider, 0))


        for slider, default_value in sliders_to_reset:
            if hasattr(self, 'ui') and hasattr(self.ui, slider.objectName()): # Check if slider exists
                slider.blockSignals(True)
                slider.setValue(default_value)
                slider.blockSignals(False)
        # self.current_processed_pil_image_for_preview = None # If you were using this

    def upload_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)")
        if filepath:
            self.image_logic.load_image(filepath)
            # update_history_buttons_state and saveButton state handled by logic via callbacks

    def save_image(self):
        if not self.image_logic.current_pil_image:
            self.ui.statusbar.showMessage("No image to save."); return
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Image As", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tiff)")
        if filepath:
            self.image_logic.save_image(filepath)

    # --- Preview and Apply Methods for Sliders ---
    def rotate_image_preview(self, value): # This will be removed if rotate slider is removed
        if hasattr(self.ui, 'rotateSlider'): # Safety check
            self.image_logic.apply_operation("rotate", value, is_preview=True)

    def resize_image_preview(self, value):
        scale_factor = value / 100.0
        self.image_logic.apply_operation("resize_preview", scale_factor, is_preview=True)
        # self.ui.statusbar.showMessage(f"Preview: Resize to {value}%") # Logic can handle status

    def apply_current_resize(self):
        scale_factor = self.ui.resizeSlider.value() / 100.0
        self.image_logic.apply_operation("resize", scale_factor, is_preview=False)
        # self.reset_all_sliders_to_default() # Let logic trigger this if needed via callback on load/revert

    def gaussian_blur_preview(self, value):
        self.image_logic.apply_operation("gaussian_blur", value, is_preview=True)

    def median_blur_preview(self, value):
        self.image_logic.apply_operation("median_blur", value, is_preview=True)
        
    def canny_preview(self):
        t1 = self.ui.cannyThresh1Slider.value()
        t2 = self.ui.cannyThresh2Slider.value()
        if t1 >= t2: t1 = max(0, t2 - 1)
        self.image_logic.apply_operation("canny_preview", (t1, t2), is_preview=True)

    def apply_current_canny(self):
        t1 = self.ui.cannyThresh1Slider.value()
        t2 = self.ui.cannyThresh2Slider.value()
        if t1 >= t2: t1 = max(0, t2-1)
        self.image_logic.apply_operation("canny", (t1, t2), is_preview=False)
        # self.reset_all_sliders_to_default()

    def threshold_preview(self, value):
        self.image_logic.apply_operation("threshold", value, is_preview=True)

    def erosion_preview(self, value):
        self.image_logic.apply_operation("erosion", value, is_preview=True)

    def dilation_preview(self, value):
        self.image_logic.apply_operation("dilation", value, is_preview=True)

    def brightness_preview(self, value):
        factor = value / 100.0
        self.image_logic.apply_operation("brightness_preview", factor, is_preview=True)

    def contrast_preview(self, value):
        factor = value / 100.0
        self.image_logic.apply_operation("contrast_preview", factor, is_preview=True)

    def apply_current_adjustments(self):
        brightness_factor = self.ui.brightnessSlider.value() / 100.0
        # Only apply if significantly different from 1.0
        if abs(brightness_factor - 1.0) > 0.001: # Allow for float inaccuracies
            self.image_logic.apply_operation("brightness", brightness_factor, is_preview=False)
        
        contrast_factor = self.ui.contrastSlider.value() / 100.0
        if abs(contrast_factor - 1.0) > 0.001:
            self.image_logic.apply_operation("contrast", contrast_factor, is_preview=False)
        
        # self.reset_all_sliders_to_default() # Let logic trigger this via callback on load/revert/undo

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Rescale original image if it exists
        if self.image_logic and self.image_logic.original_pil_image:
             # Use the stored original PIL image from logic for rescaling
            self.display_pil_image_in_gui(self.image_logic.original_pil_image, "original")
        # Rescale processed image if it exists
        if self.image_logic and self.image_logic.current_pil_image:
            # Use the stored current PIL image from logic for rescaling
            self.display_pil_image_in_gui(self.image_logic.current_pil_image, "processed")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEditorApp()
    window.show()
    sys.exit(app.exec_())
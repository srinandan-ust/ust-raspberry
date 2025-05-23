# logic.py
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter # Removed ImageTk as it's GUI specific

class ImageLogic:
    def __init__(self, gui_update_callback, gui_history_callback, gui_status_callback, gui_reset_sliders_callback):
        self.original_pil_image = None
        self.current_pil_image = None
        # self.preview_pil_image = None # Not strictly needed if previews always generate from current_pil_image
        self.history = []
        self.max_history_size = 10

        self.update_gui_image = gui_update_callback
        self.update_gui_history_buttons = gui_history_callback
        self.update_gui_status = gui_status_callback
        self.reset_gui_sliders = gui_reset_sliders_callback

    def _add_to_history(self, image_to_add):
        if self.current_pil_image: # Only add if there's a valid current image
            if len(self.history) >= self.max_history_size:
                self.history.pop(0)
            self.history.append(image_to_add.copy()) # Store a copy
        self.update_gui_history_buttons(bool(self.history), bool(self.original_pil_image))


    def load_image(self, filepath):
        try:
            img = Image.open(filepath)
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGBA') if 'A' in img.mode else img.convert('RGB')

            self.original_pil_image = img.copy()
            self.current_pil_image = img.copy()
            self.history = []
            self.update_gui_image(self.original_pil_image, "original")
            self.update_gui_image(self.current_pil_image, "processed")
            self.update_gui_history_buttons(False, True)
            self.update_gui_status(f"Image '{filepath.split('/')[-1]}' loaded.")
            self.reset_gui_sliders()
            return True
        except Exception as e:
            self.update_gui_status(f"Error loading image: {e}")
            self.original_pil_image = None
            self.current_pil_image = None
            self.update_gui_image(None, "original")
            self.update_gui_image(None, "processed")
            self.update_gui_history_buttons(False, False)
            return False

    def get_current_processed_pil_image(self):
        return self.current_pil_image

    def save_image(self, filepath):
        if self.current_pil_image:
            try:
                img_to_save = self.current_pil_image
                if (filepath.lower().endswith(".jpg") or filepath.lower().endswith(".jpeg")) and img_to_save.mode == 'RGBA':
                    img_to_save = img_to_save.convert('RGB')
                img_to_save.save(filepath)
                self.update_gui_status(f"Image saved to '{filepath}'.")
            except Exception as e:
                self.update_gui_status(f"Error saving image: {e}")
        else:
            self.update_gui_status("No processed image to save.")

    def undo_last_change(self):
        if self.history:
            self.current_pil_image = self.history.pop()
            self.update_gui_image(self.current_pil_image, "processed")
            self.update_gui_history_buttons(bool(self.history), bool(self.original_pil_image))
            self.update_gui_status("Last change undone.")
            self.reset_gui_sliders()
        else:
            self.update_gui_status("No more changes to undo.")

    def revert_all_changes(self):
        if self.original_pil_image:
            self.current_pil_image = self.original_pil_image.copy()
            self.history = []
            self.update_gui_image(self.current_pil_image, "processed")
            self.update_gui_history_buttons(False, True)
            self.update_gui_status("All changes reverted.")
            self.reset_gui_sliders()
        else:
            self.update_gui_status("No image loaded.")

    def _apply_and_update(self, new_pil_image, operation_description, is_preview):
        if is_preview:
            # For previews, just update the GUI display
            self.update_gui_image(new_pil_image, "processed")
            # Optionally, update status for preview, or let main.py handle that
            # self.update_gui_status(f"Preview: {operation_description}")
        else: # Definitive operation
            self._add_to_history(self.current_pil_image) # Add *current state before change* to history
            self.current_pil_image = new_pil_image     # Update current state
            self.update_gui_image(self.current_pil_image, "processed")
            self.update_gui_history_buttons(bool(self.history), bool(self.original_pil_image))
            self.update_gui_status(f"{operation_description} applied.")

    def apply_operation(self, operation_name, value, is_preview=False):
        if not self.current_pil_image:
            self.update_gui_status("Load an image first.")
            return

        # Always operate on a copy of the current_pil_image
        # This ensures that if an operation fails, current_pil_image is not corrupted.
        # And for previews, they don't alter current_pil_image.
        # For definitive ops, current_pil_image will be updated in _apply_and_update.
        image_to_operate_on = self.current_pil_image.copy()
        
        processed_image = None
        description = ""

        try:
            # --- Transform Operations ---
            if operation_name == "rotate_left": # New
                processed_image = image_to_operate_on.rotate(90, expand=True, fillcolor='white' if image_to_operate_on.mode == 'RGB' else (0,0,0,0))
                description = "Rotated 90° Left"
            elif operation_name == "rotate_right": # New
                processed_image = image_to_operate_on.rotate(-90, expand=True, fillcolor='white' if image_to_operate_on.mode == 'RGB' else (0,0,0,0))
                description = "Rotated 90° Right"
            elif operation_name == "rotate": # Old slider version, keep for reference if needed by main.py for a bit
                processed_image = image_to_operate_on.rotate(int(value), expand=True, fillcolor='white' if image_to_operate_on.mode == 'RGB' else (0,0,0,0))
                description = f"Rotated by {int(value)} degrees" # This is likely a preview op if called "rotate"
            elif operation_name == "flip_horizontal":
                processed_image = ImageOps.mirror(image_to_operate_on)
                description = "Flipped horizontally"
            elif operation_name == "flip_vertical":
                processed_image = ImageOps.flip(image_to_operate_on)
                description = "Flipped vertically"
            elif operation_name == "resize_preview" or operation_name == "resize":
                if value is None or not (0.01 <= value <= 5.0):
                    self.update_gui_status("Invalid resize scale.")
                    return
                width, height = image_to_operate_on.size
                new_width, new_height = int(width * value), int(height * value)
                if new_width > 0 and new_height > 0:
                    processed_image = image_to_operate_on.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    description = f"Resized to {value*100:.0f}%"
                else:
                    self.update_gui_status("Resize resulted in zero dimension."); return

            # --- Filter Operations ---
            elif operation_name == "grayscale":
                img_to_gray = image_to_operate_on.convert('RGB') if image_to_operate_on.mode == 'RGBA' else image_to_operate_on
                processed_image = img_to_gray.convert('L')
                description = "Converted to Grayscale"
            elif operation_name == "gaussian_blur":
                ksize = int(value); ksize = ksize + 1 if ksize % 2 == 0 else ksize
                if ksize > 0:
                    processed_image = image_to_operate_on.filter(ImageFilter.GaussianBlur(radius=ksize // 2))
                    description = f"Gaussian Blur (kernel: {ksize})"
            elif operation_name == "median_blur":
                ksize = int(value); ksize = ksize + 1 if ksize % 2 == 0 else ksize
                if ksize > 0:
                    cv_img = self.pil_to_cv2(image_to_operate_on)
                    blurred_cv_img = cv2.medianBlur(cv_img, ksize)
                    processed_image = self.cv2_to_pil(blurred_cv_img)
                    description = f"Median Blur (kernel: {ksize})"

            # --- Edge Detection ---
            elif operation_name == "sobel":
                cv_img = self.pil_to_cv2(image_to_operate_on)
                gray_cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY) if len(cv_img.shape) == 3 else cv_img
                sobelx = cv2.Sobel(gray_cv_img, cv2.CV_64F, 1, 0, ksize=3)
                sobely = cv2.Sobel(gray_cv_img, cv2.CV_64F, 0, 1, ksize=3)
                sobel_combined = cv2.convertScaleAbs(cv2.magnitude(sobelx, sobely))
                processed_image = self.cv2_to_pil(sobel_combined)
                description = "Sobel Edge Detection"
            elif operation_name == "canny_preview" or operation_name == "canny":
                t1, t2 = int(value[0]), int(value[1])
                cv_img = self.pil_to_cv2(image_to_operate_on)
                gray_cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY) if len(cv_img.shape) == 3 else cv_img
                edges = cv2.Canny(gray_cv_img, t1, t2)
                processed_image = self.cv2_to_pil(edges)
                description = f"Canny Edge (T1:{t1}, T2:{t2})"

            # --- Morphology & Threshold ---
            elif operation_name == "threshold":
                thresh_val = int(value)
                gray_pil = image_to_operate_on.convert('L') if image_to_operate_on.mode != 'L' else image_to_operate_on
                processed_image = gray_pil.point(lambda p: 255 if p > thresh_val else 0, '1').convert('L')
                description = f"Binary Threshold at {thresh_val}"
            elif operation_name == "erosion":
                ksize = int(value); ksize = ksize + 1 if ksize % 2 == 0 else ksize
                if ksize > 0:
                    cv_img = self.pil_to_cv2(image_to_operate_on)
                    kernel = np.ones((ksize, ksize), np.uint8)
                    processed_image = self.cv2_to_pil(cv2.erode(cv_img, kernel, iterations=1))
                    description = f"Erosion (kernel: {ksize})"
            elif operation_name == "dilation":
                ksize = int(value); ksize = ksize + 1 if ksize % 2 == 0 else ksize
                if ksize > 0:
                    cv_img = self.pil_to_cv2(image_to_operate_on)
                    kernel = np.ones((ksize, ksize), np.uint8)
                    processed_image = self.cv2_to_pil(cv2.dilate(cv_img, kernel, iterations=1))
                    description = f"Dilation (kernel: {ksize})"

            # --- Adjustments ---
            elif operation_name == "brightness_preview" or operation_name == "brightness":
                enhancer = ImageEnhance.Brightness(image_to_operate_on)
                processed_image = enhancer.enhance(float(value))
                description = f"Brightness: {value:.2f}"
            elif operation_name == "contrast_preview" or operation_name == "contrast":
                enhancer = ImageEnhance.Contrast(image_to_operate_on)
                processed_image = enhancer.enhance(float(value))
                description = f"Contrast: {value:.2f}"
            else:
                self.update_gui_status(f"Unknown operation: {operation_name}"); return

            if processed_image:
                self._apply_and_update(processed_image, description, is_preview)
            elif not is_preview:
                self.update_gui_status(f"Op '{description}' no result.")

        except Exception as e:
            error_msg = f"Error in '{operation_name}': {e}"
            self.update_gui_status(error_msg)
            print(error_msg)
            if is_preview: # If preview fails, show current committed image
                self.update_gui_image(self.current_pil_image, "processed")

    def pil_to_cv2(self, pil_image):
        numpy_image = np.array(pil_image)
        if pil_image.mode == 'RGB': return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        if pil_image.mode == 'RGBA': return cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)
        if pil_image.mode == 'L': return numpy_image
        if pil_image.mode == '1': return (numpy_image * 255).astype(np.uint8)
        pil_rgb = pil_image.convert('RGB')
        self.update_gui_status(f"PIL mode {pil_image.mode} converted to RGB for CV2.")
        return cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2BGR)

    def cv2_to_pil(self, cv2_image):
        if len(cv2_image.shape) == 2: return Image.fromarray(cv2_image, mode='L')
        if cv2_image.shape[2] == 3: return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB), mode='RGB')
        if cv2_image.shape[2] == 4: return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA), mode='RGBA')
        raise ValueError(f"Unsupported cv2_image channels: {cv2_image.shape}")
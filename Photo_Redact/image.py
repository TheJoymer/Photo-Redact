import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageDraw
import numpy as np

class PhotoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Фото-редактор")
        self.root.geometry("1000x700")

        self.image = None
        self.displayed_img = None
        self.img_history = []
        self.scale = 1.0
        self.offset = (0, 0)
        self.drawing = False
        self.crop_mode = False
        self.draw_mode = False
        self.brush_color = "black"
        self.brush_size = 5
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.draw_layer = None

        self.setup_ui()

    def setup_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_load = tk.Button(toolbar, text="Загрузить", command=self.load_image)
        btn_load.pack(side=tk.LEFT)
        btn_save = tk.Button(toolbar, text="Сохранить", command=self.save_image)
        btn_save.pack(side=tk.LEFT)
        btn_undo = tk.Button(toolbar, text="Отмена", command=self.undo)
        btn_undo.pack(side=tk.LEFT)

        btn_draw = tk.Button(toolbar, text="Рисование", command=self.toggle_draw)
        btn_draw.pack(side=tk.LEFT)
        btn_crop = tk.Button(toolbar, text="Обрезать", command=self.toggle_crop)
        btn_crop.pack(side=tk.LEFT)

        btn_brightness = tk.Button(toolbar, text="Яркость/Контраст", command=self.adjust_brightness_contrast)
        btn_brightness.pack(side=tk.LEFT)

        btn_grayscale = tk.Button(toolbar, text="Ч/Б", command=self.apply_grayscale)
        btn_grayscale.pack(side=tk.LEFT)
        btn_sepia = tk.Button(toolbar, text="Сепия", command=self.apply_sepia)
        btn_sepia.pack(side=tk.LEFT)
        btn_blur = tk.Button(toolbar, text="Размытие", command=self.apply_blur)
        btn_blur.pack(side=tk.LEFT)
        btn_sharpen = tk.Button(toolbar, text="Резкость", command=self.apply_sharpen)
        btn_sharpen.pack(side=tk.LEFT)

        btn_rotate_left = tk.Button(toolbar, text="⟲ Поворот -90°", command=lambda: self.rotate_image(-90))
        btn_rotate_left.pack(side=tk.LEFT)
        btn_rotate_right = tk.Button(toolbar, text="⟳ Поворот +90°", command=lambda: self.rotate_image(90))
        btn_rotate_right.pack(side=tk.LEFT)

        btn_color = tk.Button(toolbar, text="Цвет кисти", command=self.set_brush_color)
        btn_color.pack(side=tk.LEFT)
        btn_brush_size = tk.Button(toolbar, text="Размер кисти", command=self.set_brush_size)
        btn_brush_size.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self.root, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_crop_or_draw)
        self.canvas.bind("<B1-Motion>", self.update_crop_or_draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop_or_draw)
        self.canvas.bind("<MouseWheel>", self.zoom_image)  # Windows
        self.canvas.bind("<Button-4>", self.zoom_image)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom_image)    # Linux scroll down

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if not path:
            return
        self.image = Image.open(path).convert("RGBA")
        self.scale = 1.0
        self.img_history = []
        self.add_to_history()
        self.display_image()

    def save_image(self):
        if self.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения для сохранения")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")])
        if not path:
            return
        self.image.save(path)

    def display_image(self, img=None):
        if img is None:
            img = self.image
        if img is None:
            return

        w, h = img.size
        w_scaled = int(w * self.scale)
        h_scaled = int(h * self.scale)
        resized = img.resize((w_scaled, h_scaled), Image.LANCZOS)
        self.displayed_img = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, w_scaled, h_scaled))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.displayed_img)

    def add_to_history(self):
        if self.image:
            self.img_history.append(self.image.copy())
            if len(self.img_history) > 20:
                self.img_history.pop(0)

    def undo(self):
        if len(self.img_history) < 2:
            messagebox.showinfo("Инфо", "Нет действий для отмены")
            return
        self.img_history.pop()
        self.image = self.img_history[-1].copy()
        self.display_image()

    def zoom_image(self, event):
        if self.image is None:
            return
        if event.delta > 0 or event.num == 4:
            self.scale *= 1.1
        elif event.delta < 0 or event.num == 5:
            self.scale /= 1.1
        self.scale = max(0.1, min(self.scale, 10))
        self.display_image()

    def toggle_draw(self):
        if self.image is None:
            messagebox.showwarning("Предупреждение", "Загрузите изображение")
            return
        self.draw_mode = not self.draw_mode
        if self.draw_mode:
            self.crop_mode = False
            messagebox.showinfo("Рисование", "Режим рисования включен")
            self.draw_layer = ImageDraw.Draw(self.image)
        else:
            messagebox.showinfo("Рисование", "Режим рисования выключен")
            self.draw_layer = None

    def toggle_crop(self):
        if self.image is None:
            messagebox.showwarning("Предупреждение", "Загрузите изображение")
            return
        self.crop_mode = not self.crop_mode
        if self.crop_mode:
            self.draw_mode = False
            messagebox.showinfo("Обрезка", "Режим обрезки включен")
        else:
            self.rect_id = None
            self.canvas.delete("crop_rect")
            messagebox.showinfo("Обрезка", "Режим обрезки выключен")

    def start_crop_or_draw(self, event):
        if self.image is None:
            return
        self.start_x = int(event.x / self.scale)
        self.start_y = int(event.y / self.scale)
        if self.crop_mode:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                self.rect_id = None
        elif self.draw_mode:
            x, y = int(event.x / self.scale), int(event.y / self.scale)
            self.draw_layer.ellipse([x - self.brush_size // 2, y - self.brush_size // 2,
                                     x + self.brush_size // 2, y + self.brush_size // 2], fill=self.brush_color)
            self.display_image()
            self.add_to_history()

    def update_crop_or_draw(self, event):
        if self.image is None or self.start_x is None or self.start_y is None:
            return
        cur_x = int(event.x / self.scale)
        cur_y = int(event.y / self.scale)
        if self.crop_mode:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(
                self.start_x * self.scale, self.start_y * self.scale,
                cur_x * self.scale, cur_y * self.scale,
                outline='red', width=2, tags="crop_rect"
            )
        elif self.draw_mode:
            self.draw_layer.line([self.start_x, self.start_y, cur_x, cur_y],
                                 fill=self.brush_color, width=self.brush_size)
            self.start_x, self.start_y = cur_x, cur_y
            self.display_image()

    def end_crop_or_draw(self, event):
        if self.image is None:
            return
        if self.crop_mode:
            self.crop_image()
            self.rect_id = None
            self.canvas.delete("crop_rect")
            self.crop_mode = False
            messagebox.showinfo("Обрезка", "Обрезка выполнена")
        elif self.draw_mode:
            self.add_to_history()

        self.start_x = None
        self.start_y = None

    def crop_image(self):
        if self.rect_id is None:
            return
        coords = self.canvas.coords(self.rect_id)
        if len(coords) != 4:
            return
        x1, y1, x2, y2 = [int(c / self.scale) for c in coords]
        x1, x2 = sorted((max(x1,0), max(x2,0)))
        y1, y2 = sorted((max(y1,0), max(y2,0)))
        if x2 - x1 <= 0 or y2 - y1 <= 0:
            messagebox.showwarning("Обрезка", "Неверная область обрезки")
            return
        self.image = self.image.crop((x1, y1, x2, y2))
        self.add_to_history()
        self.display_image()

    def set_brush_color(self):
        color = colorchooser.askcolor(title="Выберите цвет кисти")
        if color[1]:
            self.brush_color = color[1]

    def set_brush_size(self):
        size = simpledialog.askinteger("Размер кисти", "Введите размер кисти (1-50):", minvalue=1, maxvalue=50)
        if size:
            self.brush_size = size

    def adjust_brightness_contrast(self):
        if self.image is None:
            return
        # Запрос яркости (-100..100) и контраста (-100..100)
        brightness = simpledialog.askinteger("Яркость", "Введите яркость (-100..100):", minvalue=-100, maxvalue=100)
        if brightness is None:
            return
        contrast = simpledialog.askinteger("Контраст", "Введите контраст (-100..100):", minvalue=-100, maxvalue=100)
        if contrast is None:
            return

        img = self.image.convert("RGB")
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.0 + brightness / 100)

        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.0 + contrast / 100)

        self.image = img.convert("RGBA")
        self.add_to_history()
        self.display_image()

    def apply_grayscale(self):
        if self.image is None:
            return
        img = self.image.convert("L").convert("RGBA")
        self.image = img
        self.add_to_history()
        self.display_image()

    def apply_sepia(self):
        if self.image is None:
            return
        img = self.image.convert("RGB")
        np_img = np.array(img)
        tr = (np_img[:, :, 0] * 0.393 + np_img[:, :, 1] * 0.769 + np_img[:, :, 2] * 0.189)
        tg = (np_img[:, :, 0] * 0.349 + np_img[:, :, 1] * 0.686 + np_img[:, :, 2] * 0.168)
        tb = (np_img[:, :, 0] * 0.272 + np_img[:, :, 1] * 0.534 + np_img[:, :, 2] * 0.131)
        tr[tr > 255] = 255
        tg[tg > 255] = 255
        tb[tb > 255] = 255
        sepia_img = np.stack([tr, tg, tb], axis=2).astype(np.uint8)
        self.image = Image.fromarray(sepia_img).convert("RGBA")
        self.add_to_history()
        self.display_image()

    def apply_blur(self):
        if self.image is None:
            return
        img = self.image.filter(ImageFilter.GaussianBlur(radius=2))
        self.image = img
        self.add_to_history()
        self.display_image()

    def apply_sharpen(self):
        if self.image is None:
            return
        img = self.image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        self.image = img
        self.add_to_history()
        self.display_image()

    def rotate_image(self, angle):
        if self.image is None:
            return
        self.image = self.image.rotate(angle, expand=True)
        self.add_to_history()
        self.display_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditor(root)
    root.mainloop()

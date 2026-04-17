# -*- coding: utf-8 -*-
"""
تطبيق ورشة السيارات - النسخة النهائية مع خادم تنزيل APK
"""

import threading
import requests
import arabic_reshaper
from bidi.algorithm import get_display
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.popup import Popup
from kivy.metrics import dp
import webbrowser
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading as th
import socket

# ------------------------------
# 1. تهيئة الخط العربي
# ------------------------------
LabelBase.register(name='Arabic', fn_regular='C:/Windows/Fonts/arial.ttf')
LabelBase.register(name='ArabicBold', fn_regular='C:/Windows/Fonts/arialbd.ttf')

def fix_ar(text):
    if not text:
        return ''
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)

# ------------------------------
# 2. ألوان التصميم الحديث
# ------------------------------
COLORS = {
    'primary': (0.05, 0.55, 0.85, 1),
    'secondary': (0.95, 0.45, 0.2, 1),
    'success': (0.1, 0.75, 0.4, 1),
    'warning': (0.95, 0.75, 0.1, 1),
    'danger': (0.9, 0.2, 0.3, 1),
    'purple': (0.6, 0.3, 0.85, 1),
    'teal': (0.0, 0.7, 0.7, 1),
    'pink': (0.95, 0.4, 0.65, 1),
    'dark': (0.15, 0.15, 0.2, 1),
    'light': (0.96, 0.96, 0.98, 1),
    'card_bg': (1, 1, 1, 1),
}
Window.clearcolor = (0.93, 0.95, 0.98, 1)

# ------------------------------
# 3. زر عصري مخصص
# ------------------------------
class ModernButton(Button):
    def __init__(self, text='', bg_color=COLORS['primary'], font_size='18sp', icon='', radius=25, shadow=True, **kwargs):
        super().__init__(**kwargs)
        self.text = fix_ar(f"{icon} {text}" if icon else text)
        self.font_name = 'ArabicBold'
        self.font_size = font_size
        self.background_color = bg_color
        self.background_normal = ''
        self.color = (1, 1, 1, 1)
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = (20, 10)
        self._radius = radius
        self._shadow = shadow
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        Clock.schedule_once(lambda dt: self._update_graphics(), 0)

    def _update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self._shadow:
                Color(0, 0, 0, 0.15)
                RoundedRectangle(pos=(self.x + 2, self.y - 5), size=self.size, radius=[self._radius + 2])
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])

# ------------------------------
# 4. شاشة حالة المرايب
# ------------------------------
class GarageStatusCard(BoxLayout):
    def __init__(self, data, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=dp(200), padding=dp(15), spacing=dp(10), **kwargs)

        status = data.get("Status", "")
        if status == "Available":
            status_text = fix_ar("🟢 شاغر")
            status_color = COLORS['success']
        elif status == "Partial":
            status_text = fix_ar("🟡 جزئي")
            status_color = COLORS['warning']
        else:
            status_text = fix_ar("🔴 مشغول")
            status_color = COLORS['danger']

        name_label = Label(text=fix_ar(f"🏭 {data.get('Name', '')}"), font_name='ArabicBold', font_size='20sp',
                           color=(0.1, 0.1, 0.15, 1), size_hint_y=None, height=dp(40))
        self.add_widget(name_label)

        desc_label = Label(text=fix_ar(data.get('Description', '')), font_name='Arabic', font_size='14sp',
                           color=(0.4, 0.4, 0.5, 1), size_hint_y=None, height=dp(35))
        self.add_widget(desc_label)

        status_container = BoxLayout(size_hint_y=None, height=dp(45))
        status_label = Label(text=status_text, font_name='ArabicBold', font_size='22sp', color=status_color)
        status_container.add_widget(status_label)
        self.add_widget(status_container)

        time_label = Label(text=fix_ar(f"⏱️ الوقت المتوقع: {data.get('EstimatedMinutes', 0)} دقيقة"),
                           font_name='Arabic', font_size='15sp', color=(0.3, 0.3, 0.4, 1),
                           size_hint_y=None, height=dp(30))
        self.add_widget(time_label)

# ------------------------------
# 5. بطاقة المنشورات
# ------------------------------
class PostCard(BoxLayout):
    def __init__(self, data, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, padding=dp(15), spacing=dp(12), **kwargs)

        icon = "🎬" if data.get("Type") == "Video" else "🖼️" if data.get("Type") == "Image" else "📝"
        title_label = Label(text=fix_ar(f"{icon} {data.get('Title', '')}"), font_name='ArabicBold',
                            font_size='18sp', color=(0.1, 0.1, 0.2, 1), size_hint_y=None, height=dp(45))
        self.add_widget(title_label)

        if data.get("Text"):
            text_label = Label(text=fix_ar(data.get("Text")), font_name='Arabic', font_size='14sp',
                               color=(0.35, 0.35, 0.45, 1), size_hint_y=None, height=dp(80))
            self.add_widget(text_label)

        if data.get("ImagePath"):
            img = AsyncImage(source=data.get("ImagePath"), size_hint_y=None, height=dp(200), allow_stretch=True)
            self.add_widget(img)

        video_url = data.get("VideoUrl")
        if video_url:
            video_btn = ModernButton('تشغيل الفيديو', icon='🎥', bg_color=COLORS['danger'], height=dp(50), font_size='15sp')
            video_btn.bind(on_release=lambda x: webbrowser.open(video_url))
            self.add_widget(video_btn)

        self.height = dp(100) + (dp(80) if data.get("Text") else 0) + (dp(200) if data.get("ImagePath") else 0) + (dp(60) if video_url else 0)

# ------------------------------
# 6. بطاقة المنتجات
# ------------------------------
class ProductCard(BoxLayout):
    def __init__(self, data, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(130), padding=dp(12), spacing=dp(15), **kwargs)

        if data.get("ImagePath"):
            img_container = BoxLayout(size_hint_x=None, width=dp(100))
            img = AsyncImage(source=data.get("ImagePath"), allow_stretch=True)
            img_container.add_widget(img)
            self.add_widget(img_container)

        info = BoxLayout(orientation='vertical', spacing=dp(8))
        name_label = Label(text=fix_ar(f"🛢️ {data.get('Name', '')}"), font_name='ArabicBold', font_size='17sp',
                           color=(0.1, 0.1, 0.2, 1), size_hint_y=None, height=dp(45))
        info.add_widget(name_label)

        price_label = Label(text=fix_ar(f"💰 {data.get('Price', 0)} دج"), font_name='ArabicBold', font_size='18sp',
                            color=COLORS['success'], size_hint_y=None, height=dp(40))
        info.add_widget(price_label)

        status_text = fix_ar("✅ متوفر") if data.get("IsAvailable", True) else fix_ar("❌ غير متوفر")
        status_color = COLORS['success'] if data.get("IsAvailable", True) else COLORS['danger']
        avail_label = Label(text=status_text, font_name='Arabic', font_size='14sp', color=status_color,
                            size_hint_y=None, height=dp(30))
        info.add_widget(avail_label)

        self.add_widget(info)

# ------------------------------
# 7. شاشة الحجز
# ------------------------------
API_URL = "http://localhost:5001/api"

class BookingScreen(BoxLayout):
    def __init__(self, app, back_callback, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(15), padding=dp(20), **kwargs)
        self.app = app
        self.back_callback = back_callback
        self.selected_date = None
        self.selected_time = None

        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70), spacing=dp(10))
        back_btn = ModernButton('رجوع', icon='↩️', bg_color=(0.5, 0.5, 0.6, 1), size_hint_x=0.3, height=dp(55), font_size='14sp', shadow=False)
        back_btn.bind(on_release=lambda x: self.go_back())
        title_label = Label(text=fix_ar('📅 حجز موعد جديد'), font_name='ArabicBold', font_size='22sp', color=COLORS['primary'], size_hint_x=0.7)
        top_bar.add_widget(back_btn)
        top_bar.add_widget(title_label)
        self.add_widget(top_bar)

        scroll = ScrollView()
        self.form_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(20), padding=dp(10))
        self.form_container.bind(minimum_height=self.form_container.setter('height'))
        scroll.add_widget(self.form_container)
        self.add_widget(scroll)

        self.add_input_card("👤 الاسم الكامل", "أدخل اسمك الكامل")
        self.add_input_card("📱 رقم الهاتف", "05XXXXXXXX")

        services_label = Label(text=fix_ar('🔧 اختر الخدمة'), font_name='ArabicBold', font_size='16sp', color=(0.2, 0.2, 0.3, 1), size_hint_y=None, height=dp(40))
        self.form_container.add_widget(services_label)

        service_options = ["تغيير زيت", "ميكانيك عام", "فحص كمبيوتر", "إصلاح فرامل"]
        self.service_spinner = Spinner(
            text=service_options[0],
            values=service_options,
            font_name='Arabic',
            font_size='16sp',
            size_hint_y=None,
            height=dp(55),
            background_color=(1, 1, 1, 1),
            color=COLORS['dark']
        )
        self.form_container.add_widget(self.service_spinner)

        datetime_layout = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=None, height=dp(55))
        self.date_btn = ModernButton('📅 اختر التاريخ', bg_color=COLORS['purple'], height=dp(55), font_size='14sp')
        self.time_btn = ModernButton('⏰ اختر الوقت', bg_color=COLORS['teal'], height=dp(55), font_size='14sp')
        self.date_btn.bind(on_release=self.show_date_picker)
        self.time_btn.bind(on_release=self.show_time_picker)
        datetime_layout.add_widget(self.date_btn)
        datetime_layout.add_widget(self.time_btn)
        self.form_container.add_widget(datetime_layout)

        self.confirm_btn = ModernButton('✅ تأكيد الحجز', bg_color=COLORS['success'], height=dp(65), font_size='20sp')
        self.confirm_btn.bind(on_release=self.submit_booking)
        self.form_container.add_widget(self.confirm_btn)

    def add_input_card(self, label_text, hint):
        label = Label(text=fix_ar(label_text), font_name='ArabicBold', font_size='16sp', color=(0.2, 0.2, 0.3, 1), size_hint_y=None, height=dp(40))
        self.form_container.add_widget(label)
        text_input = TextInput(
            hint_text=fix_ar(hint),
            multiline=False,
            font_name='Arabic',
            font_size='17sp',
            size_hint_y=None,
            height=dp(55),
            padding=(15, 12),
            background_color=(1, 1, 1, 1),
            foreground_color=(0.1, 0.1, 0.2, 1)
        )
        self.form_container.add_widget(text_input)
        if "الاسم" in label_text:
            self.name_input = text_input
        elif "الهاتف" in label_text:
            self.phone_input = text_input

    def show_date_picker(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        year = Spinner(text='2025', values=[str(y) for y in range(2024, 2031)], font_name='Arabic', size_hint_y=None, height=dp(50))
        month = Spinner(text='1', values=[str(m) for m in range(1, 13)], font_name='Arabic', size_hint_y=None, height=dp(50))
        day = Spinner(text='1', values=[str(d) for d in range(1, 32)], font_name='Arabic', size_hint_y=None, height=dp(50))
        btn_ok = ModernButton('تأكيد', bg_color=COLORS['success'], height=dp(50), font_size='16sp')
        popup = Popup(title=fix_ar("📅 اختر التاريخ"), content=content, size_hint=(0.9, 0.7))
        def on_ok(inst):
            self.selected_date = f"{year.text}-{month.text.zfill(2)}-{day.text.zfill(2)}"
            self.date_btn.text = fix_ar(f"📅 {self.selected_date}")
            popup.dismiss()
        btn_ok.bind(on_release=on_ok)
        content.add_widget(year)
        content.add_widget(month)
        content.add_widget(day)
        content.add_widget(btn_ok)
        popup.open()

    def show_time_picker(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        hour = Spinner(text='10', values=[f"{h:02d}" for h in range(7, 20)], font_name='Arabic', size_hint_y=None, height=dp(50))
        minute = Spinner(text='00', values=[f"{m:02d}" for m in range(0, 60, 15)], font_name='Arabic', size_hint_y=None, height=dp(50))
        btn_ok = ModernButton('تأكيد', bg_color=COLORS['success'], height=dp(50), font_size='16sp')
        popup = Popup(title=fix_ar("⏰ اختر الوقت"), content=content, size_hint=(0.9, 0.6))
        def on_ok(inst):
            self.selected_time = f"{hour.text}:{minute.text}"
            self.time_btn.text = fix_ar(f"⏰ {self.selected_time}")
            popup.dismiss()
        btn_ok.bind(on_release=on_ok)
        content.add_widget(hour)
        content.add_widget(minute)
        content.add_widget(btn_ok)
        popup.open()

    def submit_booking(self, instance):
        name = self.name_input.text.strip()
        phone = self.phone_input.text.strip()
        service = self.service_spinner.text
        if not all([name, phone, self.selected_date, self.selected_time]):
            self.show_message("⚠️ تنبيه", "يرجى ملء جميع الحقول المطلوبة")
            return
        loading = Popup(title=fix_ar("⏳ جاري الحجز..."), content=Label(text=fix_ar("يرجى الانتظار..."), font_name='Arabic', font_size='16sp'), size_hint=(0.7, 0.3))
        loading.open()
        def send():
            try:
                response = requests.post(f"{API_URL}/Booking/create", json={"customerName": name, "customerPhone": phone, "service": service, "date": self.selected_date, "time": self.selected_time}, timeout=10)
                Clock.schedule_once(lambda dt: self._on_response(response, loading), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_error(e, loading), 0)
        threading.Thread(target=send, daemon=True).start()

    def _on_response(self, response, loading):
        loading.dismiss()
        if response.status_code == 200:
            data = response.json()
            msg = f"✅ {data.get('Message', 'تم الحجز بنجاح')}\n\n📍 رقم الانتظار: {data.get('WaitingNumber', '---')}\n👥 امامك: {data.get('PeopleAhead', '0')} اشخاص\n⏱️ الوقت المتوقع: {data.get('EstimatedTime', '---')}"
            self.show_message("🎉 تأكيد الحجز", msg)
        else:
            self.show_message("❌ خطأ", f"حدث خطأ: {response.status_code}")

    def _on_error(self, e, loading):
        loading.dismiss()
        self.show_message("❌ خطأ", f"فشل الاتصال بالخادم\nتأكد من تشغيل API")

    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        lbl = Label(text=fix_ar(message), font_name='Arabic', font_size='17sp', size_hint_y=None, height=dp(150))
        btn = ModernButton('حسناً', bg_color=COLORS['primary'], height=dp(50), font_size='16sp')
        popup = Popup(title=fix_ar(title), content=content, size_hint=(0.9, 0.6))
        btn.bind(on_release=lambda x: popup.dismiss())
        content.add_widget(lbl)
        content.add_widget(btn)
        popup.open()

    def go_back(self):
        self.back_callback()

# ------------------------------
# 8. الشاشة الرئيسية
# ------------------------------
class MainScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(25), padding=dp(40), **kwargs)
        self.app = app
        logo_label = Label(text=fix_ar('🔧 ورشة السيارات'), font_name='ArabicBold', font_size='32sp', color=COLORS['primary'], size_hint_y=None, height=dp(80))
        self.add_widget(logo_label)
        desc_label = Label(text=fix_ar('خدمات صيانة احترافية'), font_name='Arabic', font_size='16sp', color=(0.5, 0.5, 0.6, 1), size_hint_y=None, height=dp(40))
        self.add_widget(desc_label)

        buttons = [
            ('المرايب', COLORS['success'], '🏭'),
            ('المنشورات', COLORS['primary'], '📢'),
            ('المنتجات', COLORS['secondary'], '🛒'),
            ('مواعيد', COLORS['purple'], '📅')
        ]
        for text, color, icon in buttons:
            btn = ModernButton(text, icon=icon, bg_color=color, font_size='20sp', height=dp(70))
            if 'المرايب' in text:
                btn.bind(on_release=lambda x: self.app.show_garages())
            elif 'المنشورات' in text:
                btn.bind(on_release=lambda x: self.app.show_posts())
            elif 'المنتجات' in text:
                btn.bind(on_release=lambda x: self.app.show_products())
            elif 'مواعيد' in text:
                btn.bind(on_release=lambda x: self.app.show_booking())
            self.add_widget(btn)

# ------------------------------
# 9. شاشة عرض البيانات العامة
# ------------------------------
class DataScreen(BoxLayout):
    def __init__(self, app, title, back_callback, accent_color=COLORS['primary'], **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10), padding=dp(10), **kwargs)
        self.app = app
        self.accent_color = accent_color

        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70), spacing=dp(10))
        back_btn = ModernButton('رجوع', icon='↩️', bg_color=(0.5, 0.5, 0.6, 1), size_hint_x=0.28, height=dp(55), font_size='14sp', shadow=False)
        back_btn.bind(on_release=lambda x: back_callback())
        title_label = Label(text=fix_ar(f'⚡ {title}'), font_name='ArabicBold', font_size='24sp', color=accent_color, size_hint_x=0.72)
        top_bar.add_widget(back_btn)
        top_bar.add_widget(title_label)
        self.add_widget(top_bar)

        self.scroll = ScrollView()
        self.container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15), padding=dp(15))
        self.container.bind(minimum_height=self.container.setter('height'))
        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def add_card(self, card_widget):
        self.container.add_widget(card_widget)

    def clear(self):
        self.container.clear_widgets()

    def add_loading(self):
        self.clear()
        self.container.add_widget(Label(text=fix_ar("⏳ جاري التحميل..."), font_name='Arabic', font_size='18sp', size_hint_y=None, height=dp(80), color=(0.5, 0.5, 0.6, 1)))

    def add_refresh_button(self, callback):
        btn = ModernButton('🔄 تحديث', bg_color=self.accent_color, height=dp(50), font_size='16sp')
        btn.bind(on_release=lambda x: callback())
        self.container.add_widget(btn)

# ------------------------------
# 10. خادم لتنزيل APK
# ------------------------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_download_server(port=8080):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(('0.0.0.0', port), handler)
    print(f"🌐 خادم التحميل يعمل على: http://{get_local_ip()}:{port}")
    httpd.serve_forever()

# ------------------------------
# 11. التطبيق الرئيسي
# ------------------------------
class WorkshopApp(App):
    def build(self):
        Window.size = (400, 750)
        self.main_screen = MainScreen(self)
        
        # إضافة زر لبدء خادم التحميل
        server_btn = ModernButton('📱 تنزيل التطبيق', icon='', bg_color=COLORS['success'], height=dp(50), font_size='16sp')
        server_btn.bind(on_release=self.start_download_server)
        self.main_screen.add_widget(server_btn)
        
        return self.main_screen
    
    def start_download_server(self, instance):
        ip = get_local_ip()
        port = 8080
        self.show_message("🌐 خادم التحميل", 
                          f"التطبيق متاح للتحميل على:\n\n"
                          f"http://{ip}:{port}\n\n"
                          f"⚠️ تأكد أن جهازك والهاتف على نفس شبكة WiFi\n"
                          f"افتح الرابط على هاتفك لتحميل التطبيق")
        th.Thread(target=start_download_server, daemon=True).start()
    
    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        lbl = Label(text=fix_ar(message), font_name='Arabic', font_size='16sp', size_hint_y=None, height=dp(200))
        btn = ModernButton('حسناً', bg_color=COLORS['primary'], height=dp(50), font_size='16sp')
        popup = Popup(title=fix_ar(title), content=content, size_hint=(0.9, 0.6))
        btn.bind(on_release=lambda x: popup.dismiss())
        content.add_widget(lbl)
        content.add_widget(btn)
        popup.open()

    def show_garages(self):
        self.data_screen = DataScreen(self, 'المرايب', self.back_to_main, COLORS['success'])
        self.root.clear_widgets()
        self.root.add_widget(self.data_screen)
        self.load_garages()

    def load_garages(self):
        self.data_screen.add_loading()
        threading.Thread(target=self._fetch_garages, daemon=True).start()

    def _fetch_garages(self):
        try:
            r = requests.get(f"{API_URL}/Garage/status", timeout=10)
            if r.status_code == 200:
                data = r.json()
                Clock.schedule_once(lambda dt: self._display_garages(data))
        except Exception as e:
            print(f"Error: {e}")

    def _display_garages(self, data):
        self.data_screen.clear()
        for g in data:
            self.data_screen.add_card(GarageStatusCard(g))
        self.data_screen.add_refresh_button(self.load_garages)

    def show_posts(self):
        self.data_screen = DataScreen(self, 'المنشورات', self.back_to_main, COLORS['primary'])
        self.root.clear_widgets()
        self.root.add_widget(self.data_screen)
        self.load_posts()

    def load_posts(self):
        self.data_screen.add_loading()
        threading.Thread(target=self._fetch_posts, daemon=True).start()

    def _fetch_posts(self):
        try:
            r = requests.get(f"{API_URL}/Post", timeout=10)
            if r.status_code == 200:
                data = r.json()
                Clock.schedule_once(lambda dt: self._display_posts(data))
        except Exception as e:
            print(f"Error: {e}")

    def _display_posts(self, data):
        self.data_screen.clear()
        for p in data:
            self.data_screen.add_card(PostCard(p))
        self.data_screen.add_refresh_button(self.load_posts)

    def show_products(self):
        self.data_screen = DataScreen(self, 'المنتجات', self.back_to_main, COLORS['secondary'])
        self.root.clear_widgets()
        self.root.add_widget(self.data_screen)
        self.load_products()

    def load_products(self):
        self.data_screen.add_loading()
        threading.Thread(target=self._fetch_products, daemon=True).start()

    def _fetch_products(self):
        try:
            r = requests.get(f"{API_URL}/Product", timeout=10)
            if r.status_code == 200:
                data = r.json()
                Clock.schedule_once(lambda dt: self._display_products(data))
        except Exception as e:
            print(f"Error: {e}")

    def _display_products(self, data):
        self.data_screen.clear()
        for p in data:
            self.data_screen.add_card(ProductCard(p))
        self.data_screen.add_refresh_button(self.load_products)

    def show_booking(self):
        self.booking_screen = BookingScreen(self, self.back_to_main)
        self.root.clear_widgets()
        self.root.add_widget(self.booking_screen)

    def back_to_main(self):
        self.root.clear_widgets()
        self.root.add_widget(MainScreen(self))

# ------------------------------
# 12. تشغيل التطبيق
# ------------------------------
if __name__ == '__main__':
    WorkshopApp().run()
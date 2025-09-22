import datetime
import os, sys, time

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

logger_name = f'app.log'
logger_dir = os.path.join(application_path, "logs")

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system')

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivymd.toast import toast
from kivymd.app import MDApp
import numpy as np
import configparser, hashlib, mysql.connector
from pymodbus.client import ModbusTcpClient
from fpdf import FPDF
from fpdf.enums import MethodReturnValue
from escpos.printer import Serial
import requests

colors = {
    "Red"   : {"A200": "#FF2A2A","A500": "#FF8080","A700": "#FFD5D5",},
    "Gray"  : {"200": "#CCCCCC","500": "#ECECEC","700": "#F9F9F9",},
    "Blue"  : {"200": "#4471C4","500": "#5885D8","700": "#6C99EC",},
    "Green" : {"200": "#2CA02C","500": "#2DB97F", "700": "#D5FFD5",},
    "Yellow": {"200": "#ffD42A","500": "#ffE680","700": "#fff6D5",},

    "Light" : {"StatusBar": "E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC",},
    "Dark"  : {"StatusBar": "101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#222222","FlatButtonDown": "#DDDDDD",},
}

config_name = 'config.ini'
config_full_path = os.path.join(application_path, config_name)
config = configparser.ConfigParser()
config.read(config_full_path)

## App Setting
APP_TITLE = config['app']['APP_TITLE']
APP_SUBTITLE = config['app']['APP_SUBTITLE']
IMG_LOGO_PEMKAB = config['app']['IMG_LOGO_PEMKAB']
IMG_LOGO_DISHUB = config['app']['IMG_LOGO_DISHUB']
LB_PEMKAB = config['app']['LB_PEMKAB']
LB_DISHUB = config['app']['LB_DISHUB']
LB_UNIT = config['app']['LB_UNIT']
LB_UNIT_ADDRESS = config['app']['LB_UNIT_ADDRESS']

# SQL setting
DB_HOST = "194.31.53.37"
DB_USER = "Pndujikir2022!"
DB_PASSWORD = "@Kirpnd2022!"

DB_NAME = "pkbpandeglang"
TB_DATA = "tb_cekident"
TB_USER = "users"
TB_MERK = "merk"
TB_BAHAN_BAKAR = "bahanbakar"
TB_WARNA = "warna"
TB_DATA_MASTER = "identkendaraan"
TB_SKUJI = "subkomponen_uji"
TB_IMAGE = "image_kendaraan"
TB_TEMP_IMAGE = "temp_image_kendaraanbr"
TB_DATA_KENDARAAN = "jeniskendaraan"
TB_UJI = "uji"
TB_UJI_DETAIL = "uji_detail"

FTP_HOST = "194.31.53.37"
FTP_USER = "root"
FTP_PASS = "@D15HUBp2022!"

# system setting
TIME_OUT = int(config['setting']['TIME_OUT'])
COUNT_STARTING = int(config['setting']['COUNT_STARTING'])
COUNT_ACQUISITION = int(config['setting']['COUNT_ACQUISITION'])
UPDATE_CAROUSEL_INTERVAL = float(config['setting']['UPDATE_CAROUSEL_INTERVAL'])
UPDATE_CONNECTION_INTERVAL = float(config['setting']['UPDATE_CONNECTION_INTERVAL'])
GET_DATA_INTERVAL = float(config['setting']['GET_DATA_INTERVAL'])

PRINTER_THERM_COM = str(config['setting']['PRINTER_THERM_COM'])
PRINTER_THERM_BAUD = int(config['setting']['PRINTER_THERM_BAUD'])
PRINTER_THERM_BYTESIZE = int(config['setting']['PRINTER_THERM_BYTESIZE'])
PRINTER_THERM_PARITY = str(config['setting']['PRINTER_THERM_PARITY'])
PRINTER_THERM_STOPBITS = int(config['setting']['PRINTER_THERM_STOPBITS'])
PRINTER_THERM_TIMEOUT = float(config['setting']['PRINTER_THERM_TIMEOUT'])
PRINTER_THERM_DSRDTR = bool(config['setting']['PRINTER_THERM_DSRDTR'])

class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        Clock.schedule_interval(self.regular_update_carousel, 3)

    def on_leave(self):
        Clock.unschedule(self.regular_update_carousel)

    def regular_update_carousel(self, dt):
        try:
            self.ids.carousel.index += 1
            
        except Exception as e:
            toast_msg = f'Gagal Memperbaharui Tampilan Carousel'
            toast(toast_msg)                
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global dt_user, dt_foto_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji, dt_nama
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_warna, dt_chasis, dt_no_mesin    
        global dt_id_user    
        global dt_visual_flag, dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_sideslip_flag, dt_speed_flag
        global dt_dash_antri, dt_dash_belum_uji, dt_dash_sudah_uji
        global db_brake_total_value

        dt_user = "Operator"
        dt_foto_user = "" 
        dt_no_antri = dt_no_pol = dt_no_uji = dt_sts_uji = dt_nama = ""
        dt_merk = dt_type = dt_jns_kend = dt_jbb = dt_brt_ksg = dt_warna = dt_chasis = dt_no_mesin = ""
        dt_id_user = 1
        dt_visual_flag = dt_load_flag = dt_brake_flag = dt_handbrake_flag = dt_sideslip_flag = dt_speed_flag = 0
        dt_dash_antri = dt_dash_belum_uji = dt_dash_sudah_uji = 0

        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS
        
        Clock.schedule_interval(self.regular_update_display, 1)

    def on_enter(self):
        self.exec_reload_database()
        self.exec_reload_table()

    def regular_update_display(self, dt):
        global dt_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_visual_flag, dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_sideslip_flag, dt_speed_flag
        
        try:
            screen_home = self.screen_manager.get_screen('screen_home')
            screen_printer = self.screen_manager.get_screen('screen_printer')
            
            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_home.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_home.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_printer.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_printer.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_dash_antri.text = str(dt_dash_antri)
            self.ids.lb_dash_belum_uji.text = str(dt_dash_belum_uji)
            self.ids.lb_dash_sudah_uji.text = str(dt_dash_sudah_uji)

        except Exception as e:
            toast_msg = f'Gagal Memperbaharui Tampilan'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def unsigned_to_signed(self, val):
        if val >= 32768:
            return val - 65536
        return val

    def exec_reload_database(self):
        global mydb
        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD,database = DB_NAME)
        except Exception as e:
            toast_msg = f'Gagal Menginisiasi Database'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_reload_table(self):
        global mydb, db_antrian
        global db_merk, db_bahan_bakar, db_warna
        global dt_dash_antri, dt_dash_belum_uji, dt_dash_sudah_uji
        global window_size_x, window_size_y

        try:
            cursor = mydb.cursor()
            today = str(time.strftime("%Y-%m-%d", time.localtime()))
            delete_query = f"DELETE FROM {TB_DATA} WHERE DATE(tgl_daftar) != %s"
            cursor.execute(delete_query, (today,))
            mydb.commit()
            toast_msg = f'Berhasil menghapus data kemarin'
        except Exception as e:
            toast_msg = f'Gagal menghapus data kemarin'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

        try:
            cursor = mydb.cursor()
            cursor.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            result_tb_merk = cursor.fetchall()
            db_merk = np.array(result_tb_merk)

            cursor.execute(f"SELECT ID, DESCRIPTION FROM {TB_BAHAN_BAKAR}")
            result_tb_bahan_bakar = cursor.fetchall()
            db_bahan_bakar = np.array(result_tb_bahan_bakar)

            cursor.execute(f"SELECT id_warna, nama FROM {TB_WARNA}")
            result_tb_warna = cursor.fetchall()
            db_warna = np.array(result_tb_warna)

            cursor.execute(f"SELECT COUNT(*) FROM {TB_DATA}")
            result = cursor.fetchone() 

            if result is None:
                dt_dash_antri = 0
                toast('Data Tabel cekident kosong')
            else:
                dt_dash_antri = result[0]
                query = f"""SELECT noantrian, nopol, nouji, statusuji, merk, type, idjeniskendaraan, jbb, berat_kosong, bahan_bakar, warna, 
                            check_flag, load_flag, brake_flag, handbrake_flag, sideslip_flag, speed_flag 
                            FROM {TB_DATA} WHERE print_flag = 0"""
                cursor.execute(query)
                result_tb_antrian = cursor.fetchall()
                db_antrian = np.array(result_tb_antrian).T

                db_pendaftaran = np.array(result_tb_antrian)
                dt_dash_belum_uji = db_pendaftaran[:,0].size
                dt_dash_sudah_uji = dt_dash_antri - dt_dash_belum_uji
            
            cursor.close()

        except Exception as e:
            toast_msg = f'Gagal mengambil data antrian harian'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

        try:            
            layout_list = self.ids.layout_list
            layout_list.clear_widgets(children=None)
        except Exception as e:
            toast_msg = f'Gagal menghapus widget tabel'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")   
        
        try:           
            layout_list = self.ids.layout_list
            for i in range(db_antrian[0,:].size):
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.07),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.08),
                        MDLabel(text='Berkala' if db_antrian[3, i] == 'B' else 'Uji Ulang' if (db_antrian[3, i]) == 'U' else 'Baru' if (db_antrian[3, i]) == 'BR' else 'Numpang Uji' if (db_antrian[3, i]) == 'NB' else 'Mutasi', size_hint_x= 0.07),
                        MDLabel(text='-' if db_antrian[4, i] == None else f"{db_merk[np.where(db_merk == db_antrian[4, i])[0][0],1]}" , size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[5, i]}", size_hint_x= 0.10),
                        MDLabel(text='Lulus' if (int(db_antrian[11, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[11, i]) == 1) else 'Belum Diuji', size_hint_x= 0.05),
                        MDLabel(text='Lulus' if (int(db_antrian[12, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[12, i]) == 1) else 'Belum Diuji', size_hint_x= 0.05),
                        MDLabel(text='Lulus' if (int(db_antrian[13, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[13, i]) == 1) else 'Belum Diuji', size_hint_x= 0.05),
                        MDLabel(text='Lulus' if (int(db_antrian[14, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[13, i]) == 1) else 'Belum Diuji', size_hint_x= 0.05),
                        MDLabel(text='Lulus' if (int(db_antrian[15, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[13, i]) == 1) else 'Belum Diuji', size_hint_x= 0.05),
                        MDLabel(text='Lulus' if (int(db_antrian[16, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[13, i]) == 1) else 'Belum Diuji', size_hint_x= 0.05),

                        ripple_behavior = True,
                        on_press = self.on_antrian_row_press,
                        padding = 20,
                        id=f"card_antrian{i}",
                        size_hint_y=None,
                        height=dp(int(60 * 800 / window_size_y)),
                        )
                    )
        except Exception as e:
            toast_msg = f'Gagal reload tabel'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")   

    def on_antrian_row_press(self, instance):
        global mydb, db_antrian, db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna
        global dt_visual_flag, dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_sideslip_flag, dt_speed_flag
        global dt_id_user, dt_foto_user

        try:
            row = int(str(instance.id).replace("card_antrian",""))
            dt_no_antri             = db_antrian[0, row]
            dt_no_pol               = db_antrian[1, row]
            dt_no_uji               = db_antrian[2, row]
            dt_sts_uji              = db_antrian[3, row]
            dt_merk                 = db_antrian[4, row]
            dt_type                 = db_antrian[5, row]
            dt_jns_kend             = db_antrian[6, row]
            dt_jbb                  = db_antrian[7, row]
            dt_brt_ksg              = db_antrian[8, row]
            dt_bhn_bkr              = db_antrian[9, row]
            dt_warna                = db_antrian[10, row]
            dt_visual_flag          = db_antrian[11, row]            
            dt_load_flag            = db_antrian[12, row]
            dt_brake_flag           = db_antrian[13, row]
            dt_handbrake_flag       = db_antrian[14, row]
            dt_sideslip_flag        = db_antrian[15, row]
            dt_speed_flag           = db_antrian[16, row]
                                    
            self.exec_navigate_menu()

        except Exception as e:
            toast_msg = f'Gagal mengeksekusi perintah dari baris tabel'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_menu(self):

        self.screen_manager.current = 'screen_printer'

    def exec_navigate_calibration(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_calibration'

        except Exception as e:
            toast_msg = f'Error Navigate to Calibration Screen: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_add_data(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_add_data'

        except Exception as e:
            toast_msg = f'Error Navigate to Add Data Screen: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_add_queue(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_add_queue'

        except Exception as e:
            toast_msg = f'Error Navigate to Add Queue Screen: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenAddData(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenAddData, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def exec_cancel(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def on_enter(self):
        """Called when screen is entered — safe to initialize dropdowns here."""
        Clock.schedule_once(self.load_dropdowns, 0.1)  

    def on_leave(self):
        """Clean up menus to avoid memory leaks or errors."""
        if hasattr(self, 'menu_merk') and self.menu_merk:
            self.menu_merk.dismiss()
            self.menu_merk = None
        if hasattr(self, 'menu_bahan_bakar') and self.menu_bahan_bakar:
            self.menu_bahan_bakar.dismiss()
            self.menu_bahan_bakar = None
        if hasattr(self, 'menu_warna') and self.menu_warna:
            self.menu_warna.dismiss()
            self.menu_warna = None

    def load_dropdowns(self, dt=None):
        """Initialize dropdown menus for Merk, Bahan Bakar, Warna."""
        try:
            tb_merk = mydb.cursor()
            tb_merk.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            result_tb_merk = tb_merk.fetchall()
            if result_tb_merk:
                self.merk_items = [
                    {
                        "viewclass": "OneLineListItem",
                        "text": row[1],
                        "on_release": lambda x=row[1], id=row[0]: self.set_merk(x, id),
                    } for row in result_tb_merk
                ]
                self.menu_merk = MDDropdownMenu(
                    caller=self.ids.drop_merk,
                    items=self.merk_items,
                    width_mult=4,  # You can adjust this
                )
            else:
                self.menu_merk = None
            tb_bahan_bakar = mydb.cursor()
            tb_bahan_bakar.execute(f"SELECT ID, DESCRIPTION FROM {TB_BAHAN_BAKAR}")
            result_tb_bahan_bakar = tb_bahan_bakar.fetchall()
            if result_tb_bahan_bakar:
                self.bahan_bakar_items = [
                    {
                        "viewclass": "OneLineListItem",
                        "text": row[1],
                        "on_release": lambda x=row[1], id=row[0]: self.set_bahan_bakar(x, id),
                    } for row in result_tb_bahan_bakar
                ]
                self.menu_bahan_bakar = MDDropdownMenu(
                    caller=self.ids.drop_bahan_bakar,
                    items=self.bahan_bakar_items,
                    width_mult=4,
                )
            else:
                self.menu_bahan_bakar = None

            tb_warna = mydb.cursor()
            tb_warna.execute(f"SELECT id_warna, nama FROM {TB_WARNA}")
            result_tb_warna = tb_warna.fetchall()
            if result_tb_warna:
                self.warna_items = [
                    {
                        "viewclass": "OneLineListItem",
                        "text": row[1],
                        "on_release": lambda x=row[1], id=row[0]: self.set_warna(x, id),
                    } for row in result_tb_warna
                ]
                self.menu_warna = MDDropdownMenu(
                    caller=self.ids.drop_warna,
                    items=self.warna_items,
                    width_mult=4,
                )
            else:
                self.menu_warna = None

        except Exception as e:
            toast(f"Error loading dropdowns: {str(e)}")
            Logger.error(f"ScreenAddData: Failed to load dropdowns - {e}")

    def set_merk(self, text_item, id_item):
        self.ids.drop_merk.text = text_item
        self.ids.drop_merk.merk_id = id_item
        if self.menu_merk:
            self.menu_merk.dismiss()

    def set_bahan_bakar(self, text_item, id_item):
        self.ids.drop_bahan_bakar.text = text_item
        self.ids.drop_bahan_bakar.bahan_bakar_id = id_item
        if self.menu_bahan_bakar:
            self.menu_bahan_bakar.dismiss()

    def set_warna(self, text_item, id_item):
        self.ids.drop_warna.text = text_item
        self.ids.drop_warna.warna_id = id_item
        if self.menu_warna:
            self.menu_warna.dismiss()
        
    def exec_register(self):
        try:
            dt_no_uji = self.ids.tx_nouji.text.strip()
            dt_no_pol = self.ids.tx_nopol.text.strip()

            if not dt_no_uji or not dt_no_pol:
                toast("Nomor Uji dan Nomor Regristasi tidak boleh kosong!")
                return

            mycursor = mydb.cursor()

            check_nouji_sql = f"SELECT COUNT(*) FROM {TB_DATA_MASTER} WHERE NOUJI = %s"
            mycursor.execute(check_nouji_sql, (dt_no_uji,))
            result_nouji = mycursor.fetchone()
            
            if result_nouji and result_nouji[0] > 0:
                toast("Nomor Uji ini sudah terdaftar!")
                Logger.warning(f"{self.name}: Upaya menambahkan duplikat NOUJI: {dt_no_uji}")
                return 

            check_nopol_sql = f"SELECT COUNT(*) FROM {TB_DATA_MASTER} WHERE NOPOL = %s"
            mycursor.execute(check_nopol_sql, (dt_no_pol,))
            result_nopol = mycursor.fetchone()

            if result_nopol and result_nopol[0] > 0:
                toast("Nomor Polisi ini sudah terdaftar!")
                Logger.warning(f"{self.name}: Upaya menambahkan duplikat NOPOL: {dt_no_pol}")
                return 

            dt_no_uji_new = self.ids.tx_nouji.text.strip()
            dt_nama = self.ids.tx_nama.text.strip()
            dt_alamat = self.ids.tx_alamat.text.strip()
            dt_type = self.ids.tx_type.text.strip()
            dt_jenis_kendaraan = self.ids.tx_jeniskendaraan.text.strip()
            dt_jbb = self.ids.tx_jbb.text.strip()
            dt_brt_ksg = self.ids.tx_beratkosong.text.strip()
            dt_tgl_uji_terakhir = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            if not hasattr(self.ids.drop_merk, 'merk_id'):
                toast("Pilih Merk!")
                return
            if not hasattr(self.ids.drop_bahan_bakar, 'bahan_bakar_id'):
                toast("Pilih Bahan Bakar!")
                return
            if not hasattr(self.ids.drop_warna, 'warna_id'):
                toast("Pilih Warna!")
                return

            dt_id_merk = self.ids.drop_merk.merk_id
            dt_bhn_bkr = self.ids.drop_bahan_bakar.bahan_bakar_id
            dt_warna = self.ids.drop_warna.warna_id

            # Insert into database
            mycursor = mydb.cursor()
            sql = f"""
                INSERT INTO {TB_DATA_MASTER} 
                (NOUJI, NEW_NOUJI, NOPOL, NAMA, ALAMAT, MERK_ID, TYPE, idjeniskendaraan, BHN_BAKAR, JBB, BERATKOSONG, WARNA_KEND, TGL_UJI_PERDANA, TGL_UJI_TERAKHIR) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                dt_no_uji,
                dt_no_uji_new,
                dt_no_pol,
                dt_nama,
                dt_alamat,
                dt_id_merk,
                dt_type,
                dt_jenis_kendaraan,
                dt_bhn_bkr,
                dt_jbb,
                dt_brt_ksg,
                dt_warna,
                dt_tgl_uji_terakhir,
                dt_tgl_uji_terakhir
            )
            mycursor.execute(sql, values)
            mydb.commit()

            toast("Data berhasil didaftarkan")
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat mendaftarkan data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

class ScreenAddQueue(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenAddQueue, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    def exec_cancel(self):
        global dt_no_uji, dt_no_uji_new, dt_no_wilayah, dt_no_kendaraan, dt_no_plat, dt_no_pol
        global dt_nama, dt_no_hp, dt_alamat, dt_id_izin, dt_wilayah, dt_provinsi, dt_kabupaten_kota, dt_kecamatan
        global dt_id_merk, dt_id_subjenis, dt_type, dt_tahun_buat, dt_silinder, dt_warna, dt_chasis, dt_mesin, dt_warna_plat
        global dt_bhn_bkr, dt_jbb, dt_daya_motor, dt_tgl_uji_terakhir, dt_tgl_uji_habis, dt_status_uji, dt_status_penerbitan, dt_jenis_kendaraan, dt_kode_jenis_kendaraan, dt_kode_wilayah

        try:
            dt_no_uji = dt_no_uji_new = dt_no_wilayah = dt_no_kendaraan = dt_no_plat = dt_no_pol = ""
            dt_nama = dt_no_hp = dt_alamat = dt_id_izin = dt_wilayah = dt_provinsi = dt_kabupaten_kota = dt_kecamatan = ""
            dt_id_merk = dt_id_subjenis = dt_type = dt_tahun_buat = dt_silinder = dt_warna = dt_chasis = dt_mesin = dt_warna_plat = ""
            dt_bhn_bkr = dt_jbb = dt_daya_motor = dt_tgl_uji_terakhir = dt_tgl_uji_habis = dt_status_uji = dt_status_penerbitan = dt_jenis_kendaraan = dt_kode_jenis_kendaraan = dt_kode_wilayah = ""

            self.ids.tx_nopol.text = "" 
            self.ids.tx_nouji.text = "" 
            self.ids.lb_nama.text = self.ids.lb_alamat.text = ""
            self.ids.lb_no_uji.text = self.ids.lb_no_pol.text = self.ids.lb_status_uji.text = self.ids.lb_tgl_uji_terakhir.text = self.ids.lb_tgl_uji_habis.text = ""
            self.ids.lb_merk.text = self.ids.lb_type.text = self.ids.lb_jenis_kendaraan.text = self.ids.lb_warna.text = ""
            self.ids.lb_chasis.text = self.ids.lb_mesin.text = self.ids.lb_bahan_bakar.text = self.ids.lb_jbb.text = ""
            self.ids.bt_register.disabled = True

            self.exec_navigate_main()
            
        except Exception as e:
            toast_msg = f'Gagal Memuat Data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_find(self):
        global mydb, db_users, db_merk, db_bahan_bakar, db_warna
        global dt_id_user, dt_user, dt_foto_user
        global dt_no_uji, dt_no_uji_new, dt_no_wilayah, dt_no_kendaraan, dt_no_plat, dt_no_pol
        global dt_nama, dt_no_hp, dt_alamat, dt_id_izin, dt_wilayah, dt_provinsi, dt_kabupaten_kota, dt_kecamatan
        global dt_id_merk, dt_id_subjenis, dt_type, dt_tahun_buat, dt_silinder, dt_warna, dt_chasis, dt_mesin, dt_warna_plat
        global dt_bhn_bkr, dt_jbb, dt_daya_motor, dt_tgl_uji_terakhir, dt_tgl_uji_habis, dt_status_uji, dt_status_penerbitan, dt_jenis_kendaraan, dt_kode_jenis_kendaraan, dt_kode_wilayah

        try:
            dt_find_no_pol = self.ids.tx_nopol.text
            dt_find_no_uji = self.ids.tx_nouji.text
            self.exec_fetch_master_data(dt_find_no_pol, dt_find_no_uji)

            self.ids.lb_nama.text = f'{dt_nama}'
            self.ids.lb_alamat.text = f'{dt_alamat}'
            self.ids.lb_no_uji.text = f'{dt_no_uji}'
            self.ids.lb_no_pol.text = f'{dt_no_pol}'
            self.ids.lb_status_uji.text = 'Berkala' if dt_status_uji == 'B' else 'Uji Ulang' if dt_status_uji == 'U' else 'Baru' if dt_status_uji == 'BR' else 'Numpang Uji' if dt_status_uji == 'NB' else 'Mutasi'
            self.ids.lb_tgl_uji_terakhir.text = f'{dt_tgl_uji_terakhir}'
            self.ids.lb_tgl_uji_habis.text = f'{dt_tgl_uji_habis}'
            self.ids.lb_merk.text = '-' if dt_id_merk == None else f"{db_merk[np.where(db_merk == dt_id_merk)[0][0],1]}"
            self.ids.lb_type.text = f'{dt_type}'
            self.ids.lb_jenis_kendaraan.text = f'{dt_jenis_kendaraan}'
            self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"
            self.ids.lb_chasis.text = f'{dt_chasis}'
            self.ids.lb_mesin.text = f'{dt_mesin}'
            self.ids.lb_bahan_bakar.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
            self.ids.lb_jbb.text = f'{dt_jbb}'
            self.ids.lb_berat_kosong.text = f'{dt_brt_ksg}'
            self.ids.bt_register.disabled = False
            
        except Exception as e:
            toast_msg = f'Gagal Menemukan Data, Silahkan Isi Nomor Uji atau Nomor Polisi dengan Benar'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_fetch_master_data(self, dt_find_no_pol, dt_find_no_uji):
        global mydb, db_users, db_merk, db_bahan_bakar, db_warna
        global dt_id_user, dt_user, dt_foto_user
        global dt_no_uji, dt_no_uji_new, dt_no_wilayah, dt_no_kendaraan, dt_no_plat, dt_no_pol
        global dt_nama, dt_no_hp, dt_alamat, dt_id_izin, dt_wilayah, dt_provinsi, dt_kabupaten_kota, dt_kecamatan
        global dt_id_merk, dt_id_subjenis, dt_type, dt_tahun_buat, dt_silinder, dt_warna, dt_chasis, dt_mesin, dt_warna_plat
        global dt_bhn_bkr, dt_jbb, dt_brt_ksg, dt_daya_motor, dt_tgl_uji_terakhir, dt_tgl_uji_habis, dt_status_uji, dt_status_penerbitan, dt_jenis_kendaraan, dt_kode_jenis_kendaraan, dt_kode_wilayah

        try:
            mycursor = mydb.cursor()
            if dt_find_no_pol != "" and dt_find_no_uji == "":
                mycursor.execute(f"SELECT NOUJI, NEW_NOUJI, NOWIL, NOKDR, PLAT, NOPOL, NAMA, NOHP, ALAMAT, ID_IZIN, WLY, PROP, KABKOT, KEC, MERK_ID, idjeniskendaraan, TYPE, TH_BUAT, SILINDER, WARNA_KEND, CHASIS, MESIN, WARNA_PLAT, BHN_BAKAR, JBB, BERATKOSONG, DAYAMOTOR, TGL_UJI_TERAKHIR, STATUSUJI, statuspenerbitan, idjeniskendaraan, kd_jnskendaraan, kodewilayah FROM {TB_DATA_MASTER} WHERE NOPOL = '{dt_find_no_pol}' ")
            elif dt_find_no_uji != "":
                mycursor.execute(f"SELECT NOUJI, NEW_NOUJI, NOWIL, NOKDR, PLAT, NOPOL, NAMA, NOHP, ALAMAT, ID_IZIN, WLY, PROP, KABKOT, KEC, MERK_ID, idjeniskendaraan, TYPE, TH_BUAT, SILINDER, WARNA_KEND, CHASIS, MESIN, WARNA_PLAT, BHN_BAKAR, JBB, BERATKOSONG, DAYAMOTOR, TGL_UJI_TERAKHIR, STATUSUJI, statuspenerbitan, idjeniskendaraan, kd_jnskendaraan, kodewilayah FROM {TB_DATA_MASTER} WHERE NOUJI = '{dt_find_no_uji}' ")
            elif dt_find_no_uji == "" and dt_find_no_pol == "":
                toast("Silahkan Isi Nomor Uji atau Nomor Polisi dengan Benar")
            myresult = mycursor.fetchone()
            mydb.commit()
            db_master_data = np.array(myresult).T

            if myresult is None:
                toast('Data Tidak Ditemukan di Database, Silahkan Ajukan Pengujian Baru')
                self.exec_cancel()
            else:
                dt_no_uji = db_master_data[0]
                dt_no_uji_new = db_master_data[1]
                dt_no_wilayah = db_master_data[2]
                dt_no_kendaraan = db_master_data[3]
                dt_no_plat = db_master_data[4]
                dt_no_pol = db_master_data[5]
                dt_nama = db_master_data[6]
                dt_no_hp = db_master_data[7]
                dt_alamat = db_master_data[8]
                dt_id_izin = db_master_data[9]
                dt_wilayah = db_master_data[10]
                dt_provinsi = db_master_data[11]
                dt_kabupaten_kota = db_master_data[12]
                dt_kecamatan = db_master_data[13]
                dt_id_merk = db_master_data[14]
                dt_id_subjenis = db_master_data[15]
                dt_type = db_master_data[16]
                dt_tahun_buat = db_master_data[17]
                dt_silinder = db_master_data[18]
                dt_warna = db_master_data[19]
                dt_chasis = db_master_data[20]
                dt_mesin = db_master_data[21]
                dt_warna_plat = db_master_data[22]
                dt_bhn_bkr = db_master_data[23]
                dt_jbb = db_master_data[24]
                dt_brt_ksg = db_master_data[25]
                dt_daya_motor = db_master_data[26]
                
                dt_status_uji = db_master_data[28]
                dt_status_penerbitan = db_master_data[29]
                dt_jenis_kendaraan = db_master_data[30]
                dt_kode_jenis_kendaraan = db_master_data[31]
                dt_kode_wilayah = db_master_data[32]

                if(db_master_data[26] is not None):
                    last_uji_date = db_master_data[27]
                else:
                    last_uji_date = datetime.datetime(1900, 1, 1)

                if(last_uji_date.month <= 6):
                    year_replaced = last_uji_date.year
                    month_replaced = last_uji_date.month + 6
                    day_replaced = last_uji_date.day
                else:
                    year_replaced = last_uji_date.year + 1
                    month_replaced = last_uji_date.month - 6
                    day_replaced = last_uji_date.day
                
                if(last_uji_date.day > 29):
                    if month_replaced == 2:
                        day_replaced = 29
                    if month_replaced == 4 or month_replaced == 6 or month_replaced == 9 or month_replaced == 11:
                        day_replaced = 30
                    
                dt_tgl_uji_terakhir = str(last_uji_date.strftime('%d-%m-%Y'))
                dt_tgl_uji_habis = str(last_uji_date.replace(month=month_replaced, year=year_replaced, day=day_replaced).strftime('%d-%m-%Y'))
                
        except Exception as e:
            toast_msg = f'Gagal Menemukan Data dari Database Master'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_register(self):
        global mydb, db_users, db_merk, db_bahan_bakar, db_warna
        global dt_id_user, dt_user, dt_foto_user
        global dt_no_uji, dt_no_uji_new, dt_no_wilayah, dt_no_kendaraan, dt_no_plat, dt_no_pol
        global dt_nama, dt_no_hp, dt_alamat, dt_id_izin, dt_wilayah, dt_provinsi, dt_kabupaten_kota, dt_kecamatan
        global dt_id_merk, dt_id_subjenis, dt_type, dt_tahun_buat, dt_silinder, dt_warna, dt_chasis, dt_mesin, dt_warna_plat
        global dt_bhn_bkr, dt_jbb, dt_brt_ksg, dt_daya_motor, dt_tgl_uji_terakhir, dt_tgl_uji_habis, dt_status_uji, dt_status_penerbitan, dt_jenis_kendaraan, dt_kode_jenis_kendaraan, dt_kode_wilayah

        try:
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT MAX(noantrian) FROM {TB_DATA}")
            result = mycursor.fetchone()
            last_noantrian = int(result[0]) if result[0] is not None else 0
            noantrian = f"{last_noantrian + 1:04d}"

            mycursor = mydb.cursor()
            sql = f"INSERT INTO {TB_DATA} (noantrian, nopol, nouji, NEW_NOUJI, merk, type, idjeniskendaraan, jbb, berat_kosong, warna) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (noantrian, dt_no_pol, dt_no_uji, dt_no_uji_new, dt_id_merk, dt_type, dt_id_subjenis, dt_jbb, dt_brt_ksg, dt_warna)
            mycursor.execute(sql, values)
            mydb.commit()

        except Exception as e:
            toast_msg = f'Gagal menambah data antrian baru'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

        self.exec_cancel()

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Awal'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

class ScreenPrinter(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenPrinter, self).__init__(**kwargs)
        self.db_subkomponen = {}
        self.current_vehicle_data = {}
        self.current_test_results = {}
        self.visual_components = {'V1': [], 'V2': []}
        self.visual_sub_mapping = {}
        self.failed_notes = []
        Clock.schedule_once(self.delayed_init, 1)        

    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna
        global dt_visual_flag, dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_sideslip_flag, dt_speed_flag

        self.ids.lb_no_antri.text = str(dt_no_antri)
        self.ids.lb_no_pol.text = str(dt_no_pol)
        self.ids.lb_no_uji.text = str(dt_no_uji)
        self.ids.lb_sts_uji.text = 'Berkala' if dt_sts_uji == 'B' else 'Uji Ulang' if dt_sts_uji == 'U' else 'Baru' if dt_sts_uji == 'BR' else 'Numpang Uji' if dt_sts_uji == 'NB' else 'Mutasi'
        self.ids.lb_merk.text = '-' if dt_merk == None else f"{db_merk[np.where(db_merk == dt_merk)[0][0],1]}"
        self.ids.lb_type.text = str(dt_type)
        self.ids.lb_jns_kend.text = str(dt_jns_kend)
        self.ids.lb_jbb.text = str(dt_jbb)
        self.ids.lb_brt_ksg.text = str(dt_brt_ksg)
        self.ids.lb_bhn_bkr.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
        self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"

        self.load_data()
        self.update_summary_labels()

    def load_data(self):
            global mydb, dt_no_pol, dt_no_antri
            
            self.db_subkomponen = {}
            self.current_vehicle_data = {}
            self.current_test_results = {}
            self.visual_components = {'V1': [], 'V2': []}
            self.visual_sub_mapping = {}
            self.failed_notes = []

            try:
                mydb.ping(reconnect=True)
                cursor = mydb.cursor(dictionary=True)
                
                query_latest_date = f"SELECT MAX(tanggal) as latest_date FROM {TB_UJI} WHERE nopol = %s"
                cursor.execute(query_latest_date, (dt_no_pol,))
                latest_date_result = cursor.fetchone()

                if not latest_date_result or not latest_date_result['latest_date']:
                    Logger.warning(f"No test history found in '{TB_UJI}' for NOPOL {dt_no_pol}.")
                    query_main = f"SELECT * FROM {TB_IMAGE} WHERE nopol = %s AND noantrian = %s AND DATE(tgl_capture) = CURDATE() ORDER BY tgl_capture DESC LIMIT 1"
                    cursor.execute(query_main, (dt_no_pol, dt_no_antri))
                    self.current_vehicle_data = cursor.fetchone() or {}
                    cursor.close()
                    return

                latest_test_timestamp = latest_date_result['latest_date']
                
                id_uji_list = []
                query_get_ids = f"SELECT id_uji FROM {TB_UJI} WHERE nopol = %s AND DATE(tanggal) = DATE(%s)"
                cursor.execute(query_get_ids, (dt_no_pol, latest_test_timestamp))
                id_rows = cursor.fetchall()
                
                if id_rows:
                    id_uji_list = [row['id_uji'] for row in id_rows]
                
                if id_uji_list:
                    id_placeholders = ', '.join(['%s'] * len(id_uji_list))
                    query_results = f"SELECT kode_subkomponen_uji, hasil, keterangan FROM {TB_UJI_DETAIL} WHERE id_uji IN ({id_placeholders})"
                    cursor.execute(query_results, tuple(id_uji_list))
                    result_rows = cursor.fetchall()
                    for row in result_rows:
                        self.current_test_results[row['kode_subkomponen_uji']] = row['hasil']
                        if str(row['hasil']) == '0' and row.get('keterangan'):
                            if row['keterangan'] not in self.failed_notes:
                                self.failed_notes.append(row['keterangan'])

                komponen_mekanis = ('M01', 'M02', 'M04', 'M05', 'K18', 'K20', 'K21', 'M06', 'M07', 'M08')
                placeholders_mekanis = ', '.join(['%s'] * len(komponen_mekanis))
                query_subkomponen = f"SELECT kode_komponen_uji, kode_subkomponen_uji, string, satuan FROM {TB_SKUJI} WHERE kode_komponen_uji IN ({placeholders_mekanis}) ORDER BY urut"
                cursor.execute(query_subkomponen, komponen_mekanis)
                subkomponen_rows = cursor.fetchall()
                for row in subkomponen_rows:
                    kode_komponen = row['kode_komponen_uji']
                    if kode_komponen not in self.db_subkomponen: self.db_subkomponen[kode_komponen] = []
                    self.db_subkomponen[kode_komponen].append(row)

                query_main = f"SELECT * FROM {TB_IMAGE} WHERE nopol = %s AND noantrian = %s AND DATE(tgl_capture) = CURDATE() ORDER BY tgl_capture DESC LIMIT 1"
                cursor.execute(query_main, (dt_no_pol, dt_no_antri))
                self.current_vehicle_data = cursor.fetchone() or {}

                cursor.execute(f"SELECT kode_komponen_uji, kode_kelompok_uji, nama FROM komponen_uji WHERE kode_kelompok_uji IN ('V1', 'V2') ORDER BY nama")
                visual_rows = cursor.fetchall()
                visual_komponen_kodes = [row['kode_komponen_uji'] for row in visual_rows]
                for row in visual_rows:
                    self.visual_components[row['kode_kelompok_uji']].append(row)
                
                if visual_komponen_kodes:
                    placeholders_visual = ', '.join(['%s'] * len(visual_komponen_kodes))
                    query_mapping = f"SELECT kode_komponen_uji, kode_subkomponen_uji FROM {TB_SKUJI} WHERE kode_komponen_uji IN ({placeholders_visual})"
                    cursor.execute(query_mapping, tuple(visual_komponen_kodes))
                    mapping_rows = cursor.fetchall()
                    for row in mapping_rows:
                        kode_komp = row['kode_komponen_uji']
                        if kode_komp not in self.visual_sub_mapping: self.visual_sub_mapping[kode_komp] = []
                        self.visual_sub_mapping[kode_komp].append(row['kode_subkomponen_uji'])

                cursor.close()
                Logger.info(f"Dynamic data loaded for NOPOL {dt_no_pol}")
                self.update_summary_labels()

            except mysql.connector.Error as err:
                toast(f"Database Error: {err}")
                Logger.error(f"{self.name}: load_data DB error: {err}", exc_info=True)
            except Exception as e:
                toast("Gagal memuat data pengujian dinamis")
                Logger.error(f"{self.name}: load_data error: {e}", exc_info=True)

    def format_number(self, value):
            if value is None or str(value).strip() == '':
                return "-"
                
            try:
                num = float(value)
                if num == int(num):
                    return str(int(num))
                else:
                    return f"{num:.2f}" 
            except (ValueError, TypeError):
                return str(value)
            
    def update_summary_labels(self):
            """Menganalisis hasil tes dan memperbarui label kesimpulan di layar."""
            global db_bahan_bakar, dt_bhn_bkr

            def get_status(is_lulus):
                if is_lulus is None:
                    return "Belum Uji", (0.5, 0.5, 0.5, 1) 
                elif is_lulus:
                    return "Lulus", (0.17, 0.63, 0.17, 1) 
                else:
                    return "Tidak Lulus", (1, 0.16, 0.16, 1)  
            
            def check_all_pass(codes_to_check):
                if not codes_to_check:
                    return None
                
                results = [self.current_test_results.get(code) for code in codes_to_check]
                
                if any(res is None for res in results):
                    return None

                return all(str(res) == '1' for res in results)

            visual_codes_to_check = []
            codes_to_exclude = {'SK127', 'SK96', 'SK163'}
            for komp_code, sub_komp_list in self.visual_sub_mapping.items():
                for sk_code in sub_komp_list:
                    if sk_code not in codes_to_exclude:
                        visual_codes_to_check.append(sk_code)
            
            status_visual = check_all_pass(visual_codes_to_check)
            self.ids.visual_result_label.text, self.ids.visual_result_label.color = get_status(status_visual)

            # B. Analisis Emisi
            bahan_bakar_text = ""
            try:
                if dt_bhn_bkr:
                    bahan_bakar_text = db_bahan_bakar[np.where(db_bahan_bakar == str(dt_bhn_bkr))[0][0], 1]
            except (IndexError, TypeError):
                bahan_bakar_text = ""
            
            emisi_codes = ['SK93', 'SK94'] if 'solar' not in bahan_bakar_text.lower() else ['SK122']
            status_emisi = check_all_pass(emisi_codes)
            self.ids.emisi_result_label.text, self.ids.emisi_result_label.color = get_status(status_emisi)
            
            # C. Analisis Lampu Utama
            lampu_codes = ['SK97', 'SK128', 'SK99', 'SK98']
            status_lampu = check_all_pass(lampu_codes)
            self.ids.lampu_result_label.text, self.ids.lampu_result_label.color = get_status(status_lampu)

            # D. Tingkat Kebisingan
            kebisingan_codes = ['SK96']
            status_kebisingan = check_all_pass(kebisingan_codes)
            self.ids.kebisingan_result_label.text, self.ids.kebisingan_result_label.color = get_status(status_kebisingan)
            
            # E. Kedalaman Alur Ban
            ban_codes = ['SK163']
            status_ban = check_all_pass(ban_codes)
            self.ids.ban_result_label.text, self.ids.ban_result_label.color = get_status(status_ban)
            
            # F. Kegelapan Kaca
            kaca_codes = ['SK127']
            status_kaca = check_all_pass(kaca_codes)
            self.ids.kaca_result_label.text, self.ids.kaca_result_label.color = get_status(status_kaca)

            # G. Uji Rem (Axle Load & Brake Meter)
            brake_codes = ['SK529', 'SK716']
            status_rem = check_all_pass(brake_codes)
            self.ids.axle_brake_result_label.text, self.ids.axle_brake_result_label.color = get_status(status_rem)

            # H. Kincup Roda (Sideslip)
            sideslip_codes = ['SK100']
            status_sideslip = check_all_pass(sideslip_codes)
            self.ids.sideslip_result_label.text, self.ids.sideslip_result_label.color = get_status(status_sideslip)

            # I. Alat Petunjuk Kecepatan (Speedometer)
            speedo_codes = ['SK95']
            status_speedo = check_all_pass(speedo_codes)
            self.ids.speedo_result_label.text, self.ids.speedo_result_label.color = get_status(status_speedo)

    def generate_dynamic_test_section(self, pdf, title, kode_komponen):
            """
            VERSI FINAL: Mencetak satu bagian tabel hasil uji secara dinamis.
            """
            pdf.ln(2) 
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, title, align='L', ln=1)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 6, "Item", border=1, align='C')
            pdf.cell(55, 6, "Nilai Pengujian", border=1, align='C')
            pdf.cell(55, 6, "Hasil", border=1, align='C', ln=1)
            pdf.set_font('Arial', '', 10)

            if kode_komponen not in self.db_subkomponen:
                pdf.cell(190, 6, "Data komponen tidak terdefinisi", border=1, align='C', ln=1)
                return

            for item in self.db_subkomponen[kode_komponen]:
                sk_code = item['kode_subkomponen_uji']
                item_name = item.get('string', sk_code)
                
                value = self.current_vehicle_data.get(sk_code, None)
                satuan = item.get('satuan', '')
                
                display_value = 0 if value is None else value
                nilai_pengujian = f"{self.format_number(display_value)} {satuan}".strip()

                hasil_code = self.current_test_results.get(sk_code, -1)
                if str(hasil_code) == '1':
                    keterangan = "Lulus"
                elif str(hasil_code) == '0':
                    keterangan = "Tidak Lulus"
                else:
                    keterangan = "Belum Uji"

                pdf.cell(80, 6, item_name, border=1)
                pdf.cell(55, 6, nilai_pengujian, border=1, align='C')
                
                if keterangan == "Tidak Lulus":
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(55, 6, keterangan, border=1, align='C', ln=1)
                    pdf.set_font('Arial', '', 10) 
                else:
                    pdf.set_font('Arial', '', 10) 
                    pdf.cell(55, 6, keterangan, border=1, align='C', ln=1)

    def generate_emisi_section(self, pdf):
            global db_bahan_bakar, dt_bhn_bkr

            bahan_bakar_text = ""
            try:
                if dt_bhn_bkr:
                    bahan_bakar_text = db_bahan_bakar[np.where(db_bahan_bakar == str(dt_bhn_bkr))[0][0], 1]
            except IndexError:
                Logger.warning(f"ID Bahan Bakar {dt_bhn_bkr} tidak ditemukan.")
                bahan_bakar_text = ""

            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "B. Pengujian Emisi", align='L', ln=1)

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 6, "Item", border=1, align='C')
            pdf.cell(55, 6, "Nilai Pengujian", border=1, align='C')
            pdf.cell(55, 6, "Hasil", border=1, align='C', ln=1)
            pdf.set_font('Arial', '', 10)

            kode_komponen = 'M01'
            if kode_komponen not in self.db_subkomponen:
                pdf.cell(190, 6, "Data emisi tidak tersedia", border=1, align='C', ln=1)
                pdf.ln(5)
                return

            for item in self.db_subkomponen[kode_komponen]:
                sk_code = item['kode_subkomponen_uji']

                
                is_diesel = 'solar' in bahan_bakar_text.lower()
                is_opacity_test = (sk_code == 'SK122')

                if is_diesel and not is_opacity_test:
                    continue  
                if not is_diesel and is_opacity_test:
                    continue  
                
                item_name = item.get('string', sk_code)
                value = self.current_vehicle_data.get(sk_code, None)
                satuan = item.get('satuan', '')
                display_value = 0 if value is None else value
                nilai_pengujian = f"{self.format_number(display_value)} {satuan}".strip()
                hasil_code = self.current_test_results.get(sk_code, -1)
                keterangan = "Lulus" if str(hasil_code) == '1' else "Tidak Lulus" if str(hasil_code) == '0' else "Belum Uji"

                pdf.cell(80, 6, item_name, border=1)
                pdf.cell(55, 6, nilai_pengujian, border=1, align='C')
                
                if keterangan == "Tidak Lulus":
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(55, 6, keterangan, border=1, align='C', ln=1)
                    pdf.set_font('Arial', '', 10)
                else:
                    pdf.cell(55, 6, keterangan, border=1, align='C', ln=1)

    def generate_combined_test_section(self, pdf, title, list_of_kode_komponen):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, title, align='L', ln=1)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 6, "Item", border=1, align='C')
            pdf.cell(55, 6, "Nilai Pengujian", border=1, align='C')
            pdf.cell(55, 6, "Hasil", border=1, align='C')
            pdf.ln()

            pdf.set_font('Arial', '', 10)

            for kode_komponen in list_of_kode_komponen:
                if kode_komponen not in self.db_subkomponen:
                    continue 

                for item in self.db_subkomponen[kode_komponen]:
                    sk_code = item['kode_subkomponen_uji']
                    item_name = item.get('string', sk_code)

                    value = self.current_vehicle_data.get(sk_code, None)
                    satuan = item.get('satuan', '')
                    
                    display_value = 0 if value is None else value
                    nilai_pengujian = f"{display_value} {satuan}".strip()

                    hasil_code = self.current_test_results.get(sk_code, -1)
                    if str(hasil_code) == '1':
                        keterangan = "Lulus"
                    elif str(hasil_code) == '0':
                        keterangan = "Tidak Lulus"
                    else:
                        keterangan = "Belum Uji"

                    pdf.cell(80, 6, item_name, border=1)
                    pdf.cell(55, 6, nilai_pengujian, border=1, align='C')

                    current_font = pdf.font_style
                    if keterangan == "Tidak Lulus":
                        pdf.set_font('Arial', 'B', 10)

                    pdf.cell(55, 6, keterangan, border=1, align='C')

                    if keterangan == "Tidak Lulus":
                        pdf.set_font('Arial', current_font, 10)

                    pdf.ln()
            pdf.ln(2) 

    def print_visual_block(self, pdf, title, item_list, starting_num):
            w_no, w_item, w_ket = 8, 62, 25
            w_total_col = w_no + w_item + w_ket
            line_height = 5
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(190, 6, title, border=1, align='C', ln=1)
            y_header_start = pdf.get_y()
            x_start_v1 = pdf.get_x()
            x_start_v2 = x_start_v1 + w_total_col
            
            pdf.cell(w_no, 6, "No", border=1, align='C')
            pdf.cell(w_item, 6, "Item Komponen", border=1, align='C')
            pdf.cell(w_ket, 6, "Keterangan", border=1, align='C')
            pdf.set_xy(x_start_v2, y_header_start)
            pdf.cell(w_no, 6, "No", border=1, align='C')
            pdf.cell(w_item, 6, "Item Komponen", border=1, align='C')
            pdf.cell(w_ket, 6, "Keterangan", border=1, align='C', ln=1)

            split_point = (len(item_list) + 1) // 2
            display_left = item_list[:split_point]
            display_right = item_list[split_point:]
            max_rows = len(display_left)
            
            for i in range(max_rows):
                item_left = display_left[i]
                nama_left = item_left['nama']
                kode_komp_left = item_left['kode_komponen_uji']
                
                sub_komponen_left = self.visual_sub_mapping.get(kode_komp_left, [])
                if not sub_komponen_left:
                    keterangan_left = "Tidak Ada ID"
                else:
                    keterangan_left = "Lulus"  
                    found_result = False
                    for sk_code in sub_komponen_left:
                        hasil = self.current_test_results.get(sk_code)
                        if hasil is not None:
                            found_result = True
                            if str(hasil) == '0':
                                keterangan_left = "Tidak Lulus"
                                break
                    if not found_result:
                        keterangan_left = "Belum Uji"

                nama_right, keterangan_right = "", ""
                if i < len(display_right):
                    item_right = display_right[i]
                    nama_right = item_right['nama']
                    kode_komp_right = item_right['kode_komponen_uji']
                    
                    sub_komponen_right = self.visual_sub_mapping.get(kode_komp_right, [])
                    if not sub_komponen_right:
                        keterangan_right = "Tidak Ada ID"
                    else:
                        keterangan_right = "Lulus"
                        found_result = False
                        for sk_code in sub_komponen_right:
                            hasil = self.current_test_results.get(sk_code)
                            if hasil is not None:
                                found_result = True
                                if str(hasil) == '0':
                                    keterangan_right = "Tidak Lulus"
                                    break 
                        if not found_result:
                            keterangan_right = "Belum Uji"
                                
                start_y = pdf.get_y()
                pdf.set_font('Arial', '', 9)
                
                height_left = pdf.multi_cell(w_item, line_height, nama_left, dry_run=True, output=MethodReturnValue.HEIGHT)
                height_right = 0
                if nama_right:
                    height_right = pdf.multi_cell(w_item, line_height, nama_right, dry_run=True, output=MethodReturnValue.HEIGHT)
                
                row_height = max(height_left, height_right, line_height)

                y_pos_text = start_y + (row_height - line_height) / 2
                pdf.rect(x_start_v1, start_y, w_no, row_height)
                pdf.set_xy(x_start_v1, y_pos_text)
                pdf.cell(w_no, line_height, str(starting_num + i), align='C')
                pdf.rect(x_start_v1 + w_no, start_y, w_item, row_height)
                pdf.set_xy(x_start_v1 + w_no + 2, start_y + (row_height - height_left) / 2) # +2 untuk padding
                pdf.multi_cell(w_item - 2, line_height, nama_left, align='L') # -2 untuk padding
                pdf.rect(x_start_v1 + w_no + w_item, start_y, w_ket, row_height)
                pdf.set_xy(x_start_v1 + w_no + w_item, y_pos_text)
                if keterangan_left == "Tidak Lulus":
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(w_ket, line_height, keterangan_left.upper(), align='C')
                    pdf.set_font('Arial', '', 9)
                else:
                    pdf.cell(w_ket, line_height, keterangan_left, align='C')

                # 4. Cetak Kolom Kanan
                if i < len(display_right):
                    y_pos_text_right = start_y + (row_height - line_height) / 2
                    # Nomor
                    pdf.rect(x_start_v2, start_y, w_no, row_height)
                    pdf.set_xy(x_start_v2, y_pos_text_right)
                    pdf.cell(w_no, line_height, str(starting_num + split_point + i), align='C')
                    # Item Komponen
                    pdf.rect(x_start_v2 + w_no, start_y, w_item, row_height)
                    pdf.set_xy(x_start_v2 + w_no + 2, start_y + (row_height - height_right) / 2)
                    pdf.multi_cell(w_item - 2, line_height, nama_right, align='L')
                    # Keterangan
                    pdf.rect(x_start_v2 + w_no + w_item, start_y, w_ket, row_height)
                    pdf.set_xy(x_start_v2 + w_no + w_item, y_pos_text_right)
                    if keterangan_right == "Tidak Lulus":
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(w_ket, line_height, keterangan_right.upper(), align='C')
                        pdf.set_font('Arial', '', 9)
                    else:
                        pdf.cell(w_ket, line_height, keterangan_right, align='C')

                # Atur posisi Y untuk baris selanjutnya
                pdf.set_y(start_y + row_height)

    def generate_visual_section(self, pdf):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "A. Pemeriksaan Visual", align='L', ln=1)

            v1_items = self.visual_components.get('V1', [])
            v2_items = self.visual_components.get('V2', [])
            
            codes_to_exclude = ['K21', 'K18', 'K20']

            filtered_v1_items = [
                item for item in v1_items 
                if item['kode_komponen_uji'] not in codes_to_exclude
            ]

            self.print_visual_block(pdf, "Visual 1", filtered_v1_items, 1)
            

            self.print_visual_block(pdf, "Visual 2", v2_items, 1)
            
            pdf.ln(2)

    def generate_notes_section(self, pdf):
            if not self.failed_notes:
                return

            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "CATATAN PEMERIKSAAN", align='L', ln=1)
            
            pdf.set_font('Arial', '', 10)
            
            for i, note in enumerate(self.failed_notes):
                pdf.multi_cell(190, 5, f"{i + 1}. {note}", border=0, align='L')
                pdf.ln(1) 
            pdf.ln(5)

    def generate_identity_section(self, pdf):
            global mydb, db_merk, db_warna, db_bahan_bakar
            global dt_no_uji, dt_jns_kend

            identitas = {}
            try:
                if not mydb.is_connected():
                    self.manager.get_screen('screen_main').exec_reload_database()
                    
                cursor = mydb.cursor(dictionary=True)
                query = f"SELECT * FROM {TB_DATA_MASTER} WHERE nouji = %s LIMIT 1"
                cursor.execute(query, (dt_no_uji,))
                identitas = cursor.fetchone() or {}
                cursor.close()
            except Exception as e:
                Logger.error(f"Gagal mengambil data identitas kendaraan untuk PDF: {e}")
                identitas = {}

            def get_name_from_db(db_array, item_id):
                try:
                    return db_array[np.where(db_array == str(item_id))[0][0], 1]
                except (IndexError, TypeError):
                    return "-"
            
            def get_warna_plat(kode_plat):
                if kode_plat == 'H': return "Hitam"
                if kode_plat == 'K': return "Kuning"
                if kode_plat == 'M': return "Merah"
                if kode_plat == 'P': return "Putih"
                return str(kode_plat) if kode_plat else "-"

            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "I. IDENTITAS KENDARAAN", align='L', ln=1)
            pdf.set_font('Arial', '', 10)
            
            line_height = 5
            col_width_label = 35
            col_width_value = 60
            
            rows_data = [
                ["No Uji", identitas.get('NOUJI'), "Warna Plat", get_warna_plat(identitas.get('WARNA_PLAT'))],
                ["No. Registrasi", identitas.get('NOPOL'), "Warna Kendaraan", get_name_from_db(db_warna, identitas.get('WARNA_KEND'))],
                ["Nama", identitas.get('NAMA'), "Daya Motor", identitas.get('DAYAMOTOR')],
                ["Alamat", identitas.get('ALAMAT'), "Silinder", identitas.get('SILINDER')],
                ["Merk", get_name_from_db(db_merk, identitas.get('MERK_ID')), "Jenis Kendaraan", dt_jns_kend],
                ["Tipe", identitas.get('TYPE'), "Tahun Kendaraan", identitas.get('TH_BUAT')],
                ["No. Chasis", identitas.get('CHASIS'), "Bahan Bakar", get_name_from_db(db_bahan_bakar, identitas.get('BHN_BAKAR'))],
                ["No. Mesin", identitas.get('MESIN'), "NO HP", identitas.get('NOHP')],
            ]
            for row in rows_data:
                label_kiri, val_kiri, label_kanan, val_kanan = row
                y_pos = pdf.get_y()
                x_pos_kiri = pdf.get_x()
                x_pos_kanan = x_pos_kiri + col_width_label + col_width_value + 10

                # --- Kolom Kiri ---
                pdf.set_xy(x_pos_kiri, y_pos)
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_label, line_height, label_kiri)
                pdf.cell(3, line_height, ":")
                pdf.set_font('Arial', '', 10)

                if label_kiri == "Alamat":
                    pdf.multi_cell(col_width_value, line_height, str(val_kiri if val_kiri else "-"))
                    y_after_kiri = pdf.get_y()
                else:
                    pdf.cell(col_width_value, line_height, self.format_number(val_kiri))
                    y_after_kiri = y_pos + line_height
                
                # --- Kolom Kanan ---
                pdf.set_xy(x_pos_kanan, y_pos)
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_label, line_height, label_kanan)
                pdf.cell(3, line_height, ":")
                pdf.set_font('Arial', '', 10)

                pdf.cell(col_width_value, line_height, str(val_kanan if val_kanan else "-"))
                y_after_kanan = y_pos + line_height

                pdf.set_y(max(y_after_kiri, y_after_kanan))
            pdf.ln(3)

    def generate_dimensions_section(self, pdf):
            global mydb, dt_jns_kend, dt_no_pol, dt_no_antri, TB_IMAGE, TB_DATA_KENDARAAN
             
            stsbak = '0'
            try:
                mycursor = mydb.cursor()
                query = f"SELECT stsbak FROM {TB_DATA_KENDARAAN} WHERE namajenis = %s"
                mycursor.execute(query, (dt_jns_kend,))
                result = mycursor.fetchone()

                if result:
                    stsbak = str(result[0])
                    Logger.info(f"Ditemukan stsbak = {stsbak} untuk namajenis: {dt_jns_kend}")
                else:
                    Logger.warning(f"Tidak ditemukan stsbak untuk namajenis: {dt_jns_kend}")
                mycursor.close()
            except Exception as e:
                Logger.error(f"Gagal mengambil data stsbak untuk PDF: {e}")

            dimensi_data = {}
            try:
                cursor = mydb.cursor(dictionary=True)
                query_main = f"SELECT * FROM {TB_IMAGE} WHERE nopol = %s AND noantrian = %s AND DATE(tgl_capture) = CURDATE() ORDER BY tgl_capture DESC LIMIT 1"
                cursor.execute(query_main, (dt_no_pol, dt_no_antri))
                dimensi_data = cursor.fetchone()

                if not dimensi_data:
                    Logger.warning(f"Data dimensi tidak ditemukan di {TB_IMAGE} untuk nopol {dt_no_pol}")
                    dimensi_data = {}
                cursor.close()
            except Exception as e:
                Logger.error(f"Gagal mengambil data dimensi dari {TB_IMAGE}: {e}")
                dimensi_data = {}

            if not dimensi_data:
                pdf.ln(5)
                pdf.set_font('Arial', 'BI', 10)
                pdf.cell(0, 7, "Data Dimensi Kendaraan tidak ditemukan.", align='L', ln=1)
                return

            p_bak_tangki_label, p_bak_tangki_col = "", ""
            l_bak_tangki_label, l_bak_tangki_col = "", ""
            t_bak_tangki_label, t_bak_tangki_col = "", ""
            bhn_bak_label, bhn_bak_col = "", ""
            jns_bak_label, jns_bak_col = "", ""
            jns_muatan_label, jns_muatan_col = "", ""
            berat_jns_label, berat_jns_col = "", ""

            if stsbak == '2': 
                p_bak_tangki_label = "Panjang Tangki"
                p_bak_tangki_col = "ptang"
                l_bak_tangki_label = "Lebar Tangki"
                l_bak_tangki_col = "ltang"
                t_bak_tangki_label = "Timggi Tangki"
                t_bak_tangki_col = "ttang"
                jns_muatan_label = "Jenis Muatan"
                jns_muatan_col = "jenis_muatan"
                berat_jns_label = "Berat Jenis"
                berat_jns_col = "berat_jenis_muatan"
            elif stsbak == '1':
                p_bak_tangki_label = "Panjang Bak"
                p_bak_tangki_col = "pbak"
                l_bak_tangki_label = "Lebar Bak"
                l_bak_tangki_col = "lbak"
                t_bak_tangki_label = "Tinggi Bak"
                t_bak_tangki_col = "tbak"
                bhn_bak_label = "Bahan Bak"
                bhn_bak_col = "bhn_bak"
                jns_bak_label = "Jenis Bak"
                jns_bak_col = "jns_bak"

            jbb_value = self.format_number(dimensi_data.get('jbb'))
            jbkb_value = self.format_number(dimensi_data.get('jbkb'))
            jbb_jbkb_string = f"{jbb_value} / {jbkb_value}"

            # Ambil nilai JBI dan JBKBI, format, lalu gabungkan
            jbi_value = self.format_number(dimensi_data.get('jbi'))
            jbkbi_value = self.format_number(dimensi_data.get('jbkbi'))
            jbi_jbkbi_string = f"{jbi_value} / {jbkbi_value}"

            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "II. DIMENSI KENDARAAN", align='L', ln=1)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "A. Ukuran Kendaraan", align='L', ln=1)
            pdf.set_font('Arial', '', 10)

            line_height = 5
            col_width_label = 35
            col_width_value = 60
            
            rows_data = [
                ["Panjang Kendaraan", dimensi_data.get('P'), p_bak_tangki_label, dimensi_data.get(p_bak_tangki_col)],
                ["Lebar Kendaraan", dimensi_data.get('L'), l_bak_tangki_label, dimensi_data.get(l_bak_tangki_col)],
                ["Tinggi Kendaraan", dimensi_data.get('T'), t_bak_tangki_label, dimensi_data.get(t_bak_tangki_col)],
                ["Jumlah Sumbu", dimensi_data.get('jumlahsumbu'), bhn_bak_label, dimensi_data.get(bhn_bak_col)],
                ["FOH", dimensi_data.get('FOH'), jns_bak_label, dimensi_data.get(jns_bak_col)],
                ["ROH", dimensi_data.get('ROH'), jns_muatan_label, dimensi_data.get(jns_muatan_col)],
                ["JBB / JBKB", jbb_jbkb_string, berat_jns_label, dimensi_data.get(berat_jns_col)],       # <-- MENGGUNAKAN STRING GABUNGAN
                ["JBI / JBKBI", jbi_jbkbi_string, "Berat Kosong", dimensi_data.get('bk')],               # <-- MENGGUNAKAN STRING GABUNGAN
                ["KJT", dimensi_data.get('kjt'), "MST", dimensi_data.get('mst')],
                ["Wheel Base", dimensi_data.get('ptbp_q'), "Ground Clearance", dimensi_data.get('jt_gc')],
            ]

            for row in rows_data:
                label_kiri, val_kiri, label_kanan, val_kanan = row
                y_pos = pdf.get_y()
                x_pos_kiri = pdf.get_x()
                x_pos_kanan = x_pos_kiri + col_width_label + col_width_value + 10
                
                # Kolom Kiri
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_label, line_height, label_kiri)
                pdf.cell(3, line_height, ":" if label_kiri else "")
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_value, line_height, self.format_number(val_kiri) if label_kiri else "")
                
                # Kolom Kanan
                pdf.set_xy(x_pos_kanan, y_pos)
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_label, line_height, label_kanan)
                pdf.cell(3, line_height, ":" if label_kanan else "")
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_value, line_height, self.format_number(val_kanan) if label_kanan else "")
                pdf.ln()

    def generate_axle_tire_section(self, pdf):
            global mydb, dt_no_pol, dt_no_antri, TB_IMAGE

            data = {}
            try:
                cursor = mydb.cursor(dictionary=True)
                
                query_main = f"SELECT * FROM {TB_IMAGE} WHERE nopol = %s AND noantrian = %s AND DATE(tgl_capture) = CURDATE() ORDER BY tgl_capture DESC LIMIT 1"
                cursor.execute(query_main, (dt_no_pol, dt_no_antri))
                data = cursor.fetchone()

                if not data:
                    # Pesan toast sudah ditampilkan di load_data(), cukup log di sini
                    Logger.warning(f"Data Jarak Sumbu tidak ditemukan di {TB_IMAGE} untuk nopol {dt_no_pol}")
                    data = {}
                cursor.close()
            except Exception as e:
                Logger.error(f"Gagal mengambil data Jarak Sumbu dari {TB_IMAGE}: {e}")
                data = {}

            if not data:
                return
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "B. Jarak Sumbu dan Ukuran Ban Daya Angkut", align='L', ln=1)
            pdf.set_font('Arial', '', 10)
            
            line_height = 5
            col_width_label = 35
            col_width_value = 60

            axle_cols = {
                "Jarak Sumbu 1": "s1s2_a1", "Jarak Sumbu 2": "s2s3_a2", "Jarak Sumbu 3": "s3s4_a3",
                "Jarak Sumbu 4": "s4s5_a4", "Jarak Sumbu 5": "s5s6_a5", "Jarak Sumbu 6": "s6s7_a6",
                "Jarak Sumbu 7": "s7s8_a7", "Jarak Sumbu 8": "s8s9_a8", "Jarak Sumbu 9": "s9s10_a9",
                "Jarak Sumbu 10": "s10s11_a10", "Jarak Sumbu 11": "s11s12_a11", "Jarak Sumbu 12": "s12_s13_a12"
            }
            
            axle_data = []
            for label, col in axle_cols.items():
                value = data.get(col)
                if value and float(value) != 0:
                    axle_data.append([label, value])
            
            if axle_data:
                for i in range(0, len(axle_data), 2):
                    y_pos = pdf.get_y()
                    x_pos_kiri = pdf.get_x()
                    x_pos_kanan = x_pos_kiri + col_width_label + col_width_value + 10
                    
                    # Kolom Kiri
                    label_kiri, val_kiri = axle_data[i]
                    pdf.cell(col_width_label, line_height, label_kiri)
                    pdf.cell(3, line_height, ":")
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(col_width_value, line_height, self.format_number(val_kiri))
                    pdf.set_font('Arial', '', 10)

                    # Kolom Kanan (jika ada pasangan)
                    if i + 1 < len(axle_data):
                        label_kanan, val_kanan = axle_data[i+1]
                        pdf.set_xy(x_pos_kanan, y_pos)
                        pdf.cell(col_width_label, line_height, label_kanan)
                        pdf.cell(3, line_height, ":")
                        pdf.set_font('Arial', '', 10)
                        pdf.cell(col_width_value, line_height, self.format_number(val_kanan))
                        pdf.set_font('Arial', '', 10)
                    pdf.ln()

            pdf.ln(2) # Beri sedikit spasi
            tire_rows = [
                ["Ukuran Ban 1", data.get('ban1'), "Daya Angkut Orang", data.get('dao')],
                ["Ukuran Ban 2", data.get('ban2'), "Daya Angkut Barang", data.get('dab')],
                ["Ukuran Ban 3", data.get('ban3'), "Jumlah Tempat Duduk", data.get('jtd')],
                ["Ukuran Ban 4", data.get('ban4'), "Jumlah Tempat Berdiri", data.get('jtb')],
                ["Ukuran Ban 5", data.get('ban5'), "Jumlah Orang", data.get('jml_orang')],
            ]

            for row in tire_rows:
                label_kiri, val_kiri, label_kanan, val_kanan = row
                y_pos = pdf.get_y()
                x_pos_kiri = pdf.get_x()
                x_pos_kanan = x_pos_kiri + col_width_label + col_width_value + 10

                pdf.cell(col_width_label, line_height, label_kiri)
                pdf.cell(3, line_height, ":" if label_kiri else "")
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_value, line_height, self.format_number(val_kiri) if label_kiri else "")
                
                pdf.set_xy(x_pos_kanan, y_pos)
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_label, line_height, label_kanan)
                pdf.cell(3, line_height, ":" if label_kanan else "")
                pdf.set_font('Arial', '', 10)
                pdf.cell(col_width_value, line_height, self.format_number(val_kanan) if label_kanan else "")
                pdf.ln()

    def generate_load_brake_section(self, pdf):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "G. Pengujian Beban dan Rem", align='L', ln=1)

            axle_details = {}
            import re
            for komp_code in ['M06', 'M07', 'M08']:
                if komp_code in self.db_subkomponen:
                    for item in self.db_subkomponen[komp_code]:
                        match = re.search(r'\(S(\d+)\)|Sumbu (\d+)|S(\d+)$', item['string'])
                        if match:
                            axle_num_str = match.group(1) or match.group(2) or match.group(3)
                            axle_num = int(axle_num_str)
                            
                            if axle_num not in axle_details:
                                axle_details[axle_num] = {}
                            
                            if 'string' not in axle_details[axle_num]:
                                nama_sumbu_cleaned = re.sub(r'\(S\d+\)|Sumbu \d+|S\d+$', '', item['string']).strip()
                                nama_sumbu_cleaned = nama_sumbu_cleaned.replace('Kiri', '').replace('Kanan', '').replace('Selisih', '').strip()
                                axle_details[axle_num]['string_nama_sumbu'] = nama_sumbu_cleaned or f"Sumbu {axle_num}"

                            sk_code = item['kode_subkomponen_uji']
                            item_str = item['string'].lower()
                            
                            prefix = ""
                            if komp_code == 'M06': prefix = 'load'
                            elif komp_code == 'M07': prefix = 'brake'
                            elif komp_code == 'M08': prefix = 'park'
                            
                            if 'kiri' in item_str:
                                axle_details[axle_num][f'{prefix}_kiri'] = sk_code
                            elif 'kanan' in item_str:
                                axle_details[axle_num][f'{prefix}_kanan'] = sk_code
                            elif 'selisih' in item_str:
                                axle_details[axle_num][f'{prefix}_selisih'] = sk_code

            pdf.set_font('Arial', 'B', 10)
            pdf.ln(1)
            pdf.cell(0, 7, "Berat Kendaraan", align='L', ln=1)
            pdf.cell(95, 6, "Item", border=1, align='C')
            pdf.cell(95, 6, "Berat", border=1, align='C', ln=1)
            pdf.set_font('Arial', '', 10)
            
            active_axles = []
            for i in range(1, 13):
                axle_weight = self.current_vehicle_data.get(f's{i}')
                if axle_weight and float(axle_weight) > 0:
                    active_axles.append(i)
                    pdf.cell(95, 6, f"Sumbu {i}", border=1)
                    pdf.cell(95, 6, self.format_number(axle_weight), border=1, align='C', ln=1)

            total_weight = self.current_vehicle_data.get('bk')
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(95, 6, "Total Berat Kendaraan", border=1)
            pdf.cell(95, 6, self.format_number(total_weight) if total_weight else "-", border=1, align='C', ln=1)
            
            pdf.ln(1)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, "Rem Utama", align='L', ln=1)
            pdf.cell(35, 6, "Item", border=1, align='C')
            pdf.cell(30, 6, "Kiri (kg)", border=1, align='C')
            pdf.cell(30, 6, "Kanan (kg)", border=1, align='C')
            pdf.cell(30, 6, "Total (kg)", border=1, align='C')
            pdf.cell(30, 6, "Selisih (%)", border=1, align='C')
            pdf.cell(35, 6, "Hasil", border=1, align='C', ln=1)

            sorted_axles = sorted(list(set(active_axles) | set(axle_details.keys())))

            for i in sorted_axles:
                details = axle_details.get(i, {})
                kiri_val = float(self.current_vehicle_data.get(details.get('brake_kiri'), 0) or 0)
                kanan_val = float(self.current_vehicle_data.get(details.get('brake_kanan'), 0) or 0)

                total_val = kiri_val + kanan_val
                
                selisih_col_name = f"SELISIH_REM_S{i}"
                selisih_val = float(self.current_vehicle_data.get(selisih_col_name, 0) or 0)
                
                if kiri_val > 0 or kanan_val > 0 or selisih_val > 0:
                    

                    hasil_rem_sumbu = self.current_test_results.get(details.get('brake_selisih'), -1)

                    keterangan = "Lulus" if str(hasil_rem_sumbu) == '1' else "Tidak Lulus" if str(hasil_rem_sumbu) == '0' else "Belum Uji"
                    
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(35, 6, f"Sumbu {i}", border=1, align='C')
                    pdf.cell(30, 6, self.format_number(kiri_val), border=1, align='C')
                    pdf.cell(30, 6, self.format_number(kanan_val), border=1, align='C')
                    pdf.cell(30, 6, self.format_number(total_val), border=1, align='C')
                    pdf.cell(30, 6, self.format_number(selisih_val), border=1, align='C')
                    
                    if "Tidak Lulus" in keterangan.upper():
                        pdf.set_font('Arial', 'B', 10)
                    pdf.cell(35, 6, keterangan, border=1, align='C', ln=1)
                    pdf.set_font('Arial', '', 10)

            total_rem = float(self.current_vehicle_data.get('TOTAL_REM', 0) or 0)
            efisiensi_rem = float(self.current_vehicle_data.get('efisiensi_remutama', 0) or 0)
            hasil_rem_utama_total = self.current_test_results.get('SK529', -1)
            keterangan_rem_utama = "Lulus" if str(hasil_rem_utama_total) == '1' else "Tidak Lulus" if str(hasil_rem_utama_total) == '0' else "Belum Uji"
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(150, 6, "Total Gaya Pengereman", border=1)
            pdf.cell(40, 6, f"{self.format_number(total_rem)} kg", border=1, align='C', ln=1)
            pdf.cell(150, 6, "Efisiensi Rem Utama", border=1)
            pdf.cell(40, 6, f"{self.format_number(efisiensi_rem)} %", border=1, align='C', ln=1)
            pdf.cell(150, 6, "Hasil Pengujian", border=1)
            if "Tidak Lulus" in keterangan_rem_utama.upper():
                pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 6, keterangan_rem_utama, border=1, align='C', ln=1)
            pdf.set_font('Arial', '', 10)
            
            # Tabel Rem Parkir
            pdf.ln(1)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, "Rem Parkir", align='L', ln=1)
            pdf.cell(50, 6, "Item", border=1, align='C')
            pdf.cell(45, 6, "Kiri (kg)", border=1, align='C')
            pdf.cell(45, 6, "Kanan (kg)", border=1, align='C')
            pdf.cell(50, 6, "Total (kg)", border=1, align='C', ln=1)
            total_gaya_parkir = 0
            for i in sorted_axles:
                details = axle_details.get(i, {})
                kiri_val = float(self.current_vehicle_data.get(details.get('park_kiri'), 0) or 0)
                kanan_val = float(self.current_vehicle_data.get(details.get('park_kanan'), 0) or 0)
                total_sumbu = kiri_val + kanan_val
                if kiri_val > 0 or kanan_val > 0:
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(50, 6, f"Sumbu {i}", border=1, align='C')
                    pdf.cell(45, 6, self.format_number(kiri_val), border=1, align='C')
                    pdf.cell(45, 6, self.format_number(kanan_val), border=1, align='C')
                    pdf.cell(50, 6, self.format_number(total_sumbu), border=1, align='C', ln=1)
                    total_gaya_parkir += total_sumbu
            efisiensi_parkir = float(self.current_vehicle_data.get('efisiensi_remparkir', 0) or 0)
            hasil_rem_parkir_total = self.current_test_results.get('SK716', -1)
            keterangan_rem_parkir = "Lulus" if str(hasil_rem_parkir_total) == '1' else "Tidak Lulus" if str(hasil_rem_parkir_total) == '0' else "Belum Uji"
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(140, 6, "Total Gaya Pengereman", border=1)
            pdf.cell(50, 6, f"{self.format_number(total_gaya_parkir)} kg", border=1, align='C', ln=1)
            pdf.cell(140, 6, "Efisiensi Rem Parkir", border=1)
            pdf.cell(50, 6, f"{self.format_number(efisiensi_parkir)} %", border=1, align='C', ln=1)
            pdf.cell(140, 6, "Hasil Pengujian", border=1)
            if "Tidak Lulus" in keterangan_rem_parkir.upper():
                pdf.set_font('Arial', 'B', 10)
            pdf.cell(50, 6, keterangan_rem_parkir, border=1, align='C', ln=1)
            pdf.set_font('Arial', '', 10)

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_save(self):
            """
            Memperbarui data di tabel image_kendaraan dan uji_detail 
            berdasarkan data dari tb_cekident untuk antrian saat ini.
            """
            global mydb, dt_no_antri, dt_no_pol

            COLUMN_MAPPING = {
                'load_total_s1_value': 'SK102', 'load_total_s2_value': 'SK103', 'load_total_s3_value': 'SK104',
                'load_total_s4_value': 'SK105', 'load_total_s5_value': 'SK630', 'load_total_s6_value': 'SK631',
                'load_total_s7_value': 'SK632', 'load_total_s8_value': 'SK633', 'load_total_s9_value': 'SK634',
                'load_total_s10_value': 'SK635', 'load_total_s11_value': 'SK636', 'load_total_s12_value': 'SK637',
                'load_total_value': 'bk',
                'brake_l_s1_value' : 'SK106', 'brake_r_s1_value' : 'SK107', 'brake_l_s2_value' : 'SK108',
                'brake_r_s2_value' : 'SK109', 'brake_l_s3_value' : 'SK110', 'brake_r_s3_value' : 'SK111',
                'brake_l_s4_value' : 'SK112', 'brake_r_s4_value' : 'SK113', 'brake_l_s5_value' : 'SK500',
                'brake_r_s5_value' : 'SK501', 'brake_l_s6_value' : 'SK502', 'brake_r_s6_value' : 'SK503',
                'brake_l_s7_value' : 'SK504', 'brake_r_s7_value' : 'SK505', 'brake_l_s8_value' : 'SK506',
                'brake_r_s8_value' : 'SK507', 'brake_l_s9_value' : 'SK508', 'brake_r_s9_value' : 'SK509',
                'brake_l_s10_value': 'SK510', 'brake_r_s10_value': 'SK511', 'brake_l_s11_value': 'SK512',
                'brake_r_s11_value': 'SK513', 'brake_l_s12_value': 'SK514', 'brake_r_s12_value': 'SK515',
                'brake_difference_s1_value' : 'SELISIH_REM_S1', 'brake_difference_s2_value' : 'SELISIH_REM_S2',
                'brake_difference_s3_value' : 'SELISIH_REM_S3', 'brake_difference_s4_value' : 'SELISIH_REM_S4',
                'brake_difference_s5_value' : 'SELISIH_REM_S5', 'brake_difference_s6_value' : 'SELISIH_REM_S6',
                'brake_difference_s7_value' : 'SELISIH_REM_S7', 'brake_difference_s8_value' : 'SELISIH_REM_S8',
                'brake_difference_s9_value' : 'SELISIH_REM_S9', 'brake_difference_s10_value': 'SELISIH_REM_S10',
                'brake_difference_s11_value': 'SELISIH_REM_S11', 'brake_difference_s12_value': 'SELISIH_REM_S12',
                'brake_total_value' : 'TOTAL_REM', 'brake_efficicency_value' : 'efisiensi_remutama',
                'handbrake_l_s1_value' : 'SK114', 'handbrake_r_s1_value' : 'SK115', 'handbrake_l_s2_value' : 'SK116',
                'handbrake_r_s2_value' : 'SK117', 'handbrake_l_s3_value' : 'SK118', 'handbrake_r_s3_value' : 'SK119',
                'handbrake_l_s4_value' : 'SK120', 'handbrake_r_s4_value' : 'SK121', 'handbrake_l_s5_value' : 'SK700',
                'handbrake_r_s5_value' : 'SK701', 'handbrake_l_s6_value' : 'SK702', 'handbrake_r_s6_value' : 'SK703',
                'handbrake_l_s7_value' : 'SK704', 'handbrake_r_s7_value' : 'SK705', 'handbrake_l_s8_value' : 'SK706',
                'handbrake_r_s8_value' : 'SK707', 'handbrake_l_s9_value' : 'SK708', 'handbrake_r_s9_value' : 'SK709',
                'handbrake_l_s10_value': 'SK710', 'handbrake_r_s10_value': 'SK711', 'handbrake_l_s11_value' : 'SK712',
                'handbrake_r_s11_value': 'SK713', 'handbrake_l_s12_value': 'SK714', 'handbrake_r_s12_value': 'SK715',
                'handbrake_total_value' : 'TOTAL_REM_PARKIR', 'handbrake_efficicency_value' : 'efisiensi_remparkir',
                'handbrake_l_value' : "TOTAL_REM_PARKIR_KIRI", 'handbrake_r_value' : "TOTAL_REM_PARKIR_KANAN",
                'emission_co_value' : 'SK93', 'emission_hc_value' : 'SK94', 'emission_smoke_value': 'SK122',
                'hlm_right_value' : 'SK97', 'hlm_left_value' : 'SK128', 'hlm_diff_right_value' : 'SK99',
                'hlm_diff_left_value' : 'SK98', 'slm_value' : 'SK96', 'tread_depth_value': 'SK163',
                'wtm_flag': 'SK127', 'sideslip_value': 'SK100', 'speed_value': 'SK95'
            }

            FLAG_TO_SKCODE_MAPPING = {
                'emission_co_flag': 'SK93', 'emission_hc_flag': 'SK94', 'emission_smoke_flag': 'SK122',
                'speed_flag': 'SK95', 'slm_flag': 'SK96', 'hlm_right_flag': 'SK97',
                'hlm_diff_left_flag': 'SK98', 'hlm_diff_right_flag': 'SK99', 'sideslip_flag': 'SK100',
                'wtm_flag': 'SK127', 'hlm_left_flag': 'SK128', 'tread_depth_flag': 'SK163',
                'brake_efficiency_flag': 'SK529', 'handbrake_efficiency_flag': 'SK716',
                'brake_difference_s1_flag': 'SK516', 'brake_difference_s2_flag': 'SK517',
                'brake_difference_s3_flag': 'SK518', 'brake_difference_s4_flag': 'SK519',
                'brake_difference_s5_flag': 'SK520', 'brake_difference_s6_flag': 'SK521',
                'brake_difference_s7_flag': 'SK522', 'brake_difference_s8_flag': 'SK523',
                'brake_difference_s9_flag': 'SK524', 'brake_difference_s10_flag': 'SK525',
                'brake_difference_s11_flag': 'SK526', 'brake_difference_s12_flag': 'SK527'
            }

            cursor = None
            try:
                mydb.ping(reconnect=True)
                cursor = mydb.cursor()

                query_sumber = f"SELECT * FROM {TB_DATA} WHERE noantrian = %s AND nopol = %s LIMIT 1"
                cursor.execute(query_sumber, (dt_no_antri, dt_no_pol))
                sumber_data_row = cursor.fetchone()
                if not sumber_data_row:
                    toast("Data sumber di tb_cekident tidak ditemukan!")
                    return
                column_names = [desc[0] for desc in cursor.description]
                sumber_data = dict(zip(column_names, sumber_data_row))

                cursor.execute(f"SELECT MAX(DATE(tanggal)) FROM {TB_UJI} WHERE nopol = %s", (dt_no_pol,))
                latest_date = cursor.fetchone()[0]

                if not latest_date:
                    toast(f"Tidak ditemukan riwayat uji untuk nopol {dt_no_pol}")
                    return

                cursor.execute(f"SELECT id_uji FROM {TB_UJI} WHERE nopol = %s AND DATE(tanggal) = %s", (dt_no_pol, latest_date))
                id_uji_rows = cursor.fetchall()
                if not id_uji_rows:
                    toast(f"Tidak ditemukan ID Uji untuk sesi terakhir nopol {dt_no_pol}")
                    return
                
                id_uji_list = tuple(item[0] for item in id_uji_rows)
                
                placeholders = ', '.join(['%s'] * len(id_uji_list))

                sql_update = f"""
                    UPDATE {TB_UJI_DETAIL}
                    SET hasil = %s
                    WHERE id_uji IN ({placeholders})
                    AND kode_subkomponen_uji = %s
                """
                
                updates_to_commit = 0
                for flag_column, sk_code in FLAG_TO_SKCODE_MAPPING.items():
                    value = sumber_data.get(flag_column)
                    if value is not None:
                        try:
                            value_to_save = str(int(value))
                            params = (value_to_save,) + id_uji_list + (sk_code,)
                            cursor.execute(sql_update, params)
                            
                            if cursor.rowcount > 0:
                                updates_to_commit += cursor.rowcount
                                Logger.info(f"Berhasil UPDATE untuk {flag_column} ('{value_to_save}') -> {sk_code}. Baris terpengaruh: {cursor.rowcount}")
                        except (ValueError, TypeError):
                            Logger.warning(f"Nilai '{value}' untuk '{flag_column}' dilewati.")

                if updates_to_commit > 0:
                    mydb.commit()
                    toast(f"Update berhasil! {updates_to_commit} data hasil uji telah disimpan.")
                    Logger.info(f"COMMIT berhasil. Total {updates_to_commit} baris diubah.")
                    Logger.info("Data berhasil disimpan, otomatis memuat ulang data terbaru...")
                    self.load_data() 
                else:
                    toast("Tidak ada data hasil uji yang cocok untuk diupdate.")

            except mysql.connector.Error as err:
                toast(f"Gagal menyimpan data: {err}")
                Logger.error(f"Error DB untuk antrian {dt_no_antri}: {err}", exc_info=True)
                if mydb.in_transaction:
                    mydb.rollback()
            finally:
                if cursor:
                    cursor.close()

    def exec_print(self):
            try:
                Logger.info("Tombol Cetak ditekan. Memulai proses cetak dengan data yang ada di memori...")
                self.exec_print_pdf()
                self.exec_print_thermal()

            except Exception as e:
                toast_msg = f'Gagal Mencetak Hasil Uji'
                toast(toast_msg)
                Logger.error(f"{self.name}: {toast_msg}, Error: {e}") 

    def exec_print_pdf(self):
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_merk, dt_type, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global dt_visual_flag, dt_speed_flag, dt_speed_value, dt_sideslip_flag, dt_sideslip_value
        global db_load_left_value, db_load_right_value, db_load_total_value, dt_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value
        global dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global LB_PEMKAB, LB_DISHUB, LB_UNIT, LB_UNIT_ADDRESS
        global IMG_LOGO_DISHUB, IMG_LOGO_PEMKAB
        global dt_sideslip_flag, dt_speed_flag, dt_sideslip_value, dt_speed_value

        try:
            Logger.info(f"DEBUG: Isi self.db_subkomponen sebelum cetak PDF: {self.db_subkomponen}")

            print_datetime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            pdf = FPDF(format='A4', unit='mm')
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            # ==================================================================
            pdf.image(f"assets/images/{IMG_LOGO_DISHUB}", x=170, y=8, w=21)
            pdf.image(f"assets/images/{IMG_LOGO_PEMKAB}", x=10, y=8, w=21)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 5, LB_PEMKAB, align='C', ln=1)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 5, LB_DISHUB, align='C', ln=1)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 5, "UNIT PELAKSANA TEKNIS DAERAH", align='C', ln=1)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 5, "PENGUJIAN KENDARAAN BERMOTOR", align='C', ln=1)
            pdf.set_font('Arial', '', 8)
            pdf.cell(0, 5, LB_UNIT_ADDRESS, align='C', ln=1)
            # ==================================================================
            pdf.set_line_width(1)
            pdf.line(10, 36, 200, 36)
            pdf.set_line_width(0.2)
            pdf.line(10, 37, 200, 37)
            pdf.ln(3)
            # ==================================================================
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 5, "BERITA ACARA PEMERIKSAAN", align='C', ln=1)
            pdf.cell(0, 5, "TEKNIS UJI KENDARAAN BERMOTOR", align='C', ln=1)
            pdf.set_font('Arial', '', 9)
            pdf.cell(0, 5, f"Tanggal:{time.strftime('%d %B %Y')}", align='C', ln=1)
            # ==================================================================
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "FOTO KENDARAAN:")
            pdf.ln(8)
            y_photo = pdf.get_y()
            try:
                today = time.strftime("%Y-%m-%d")
                base_url = f"https://{FTP_HOST}/system/storage/app/capture/{today}/{dt_sts_uji}-{dt_no_antri}/{dt_no_pol}"
                documents_dir = os.path.join(os.environ["USERPROFILE"], "Pictures", "VIIS")
                os.makedirs(documents_dir, exist_ok=True)
                img_paths = []

                for i in range(1, 5):
                    url = f"{base_url}-{i}.jpg"
                    local_path = os.path.join(documents_dir, f"{dt_no_pol}_view_{i}.jpg")
                    img_paths.append(local_path)

                    try:
                        response = requests.get(url, timeout=5, stream=True, verify=False)
                        if response.status_code == 200:
                            with open(local_path, 'wb') as f:
                                f.write(response.content)
                            Logger.info(f"Downloaded: {url}")
                        else:
                            Logger.warning(f"Image not found: {url} (Status: {response.status_code})")
                            img_paths[-1] = None 
                    except Exception as e:
                        Logger.error(f"Failed to download {url}: {e}")
                        img_paths[-1] = None

                y_photo = pdf.get_y()
                x_positions = [15, 60, 110, 160]
                labels = ["Depan", "Kiri", "Kanan", "Belakang"]

                for i in range(4):
                    if img_paths[i] and os.path.exists(img_paths[i]):
                        try:
                            pdf.image(img_paths[i], x=x_positions[i], y=y_photo, w=40, h=30)

                            pdf.set_xy(x_positions[i], y_photo + 30)
                            pdf.set_font('Arial', '', 8)
                            pdf.cell(40, 5, labels[i], align='C')
                        except Exception as img_err:
                            Logger.error(f"FPDF failed to insert image {img_paths[i]}: {img_err}")

                            pdf.set_draw_color(128)
                            pdf.rect(x_positions[i], y_photo, 40, 30)
                            pdf.set_xy(x_positions[i], y_photo + 15)
                            pdf.cell(40, 10, "Foto Error", align='C')
                    else:
                        pdf.set_draw_color(128)
                        pdf.rect(x_positions[i], y_photo, 40, 30)
                        pdf.set_xy(x_positions[i], y_photo + 10)
                        pdf.cell(40, 5, "Foto Tidak", align='C')
                        pdf.set_xy(x_positions[i], y_photo + 15)
                        pdf.cell(40, 5, "Tersedia", align='C')
                        pdf.set_xy(x_positions[i], y_photo + 30)
                        pdf.set_font('Arial', 'B', 8)
                        pdf.cell(40, 5, labels[i], align='C')
                        pdf.set_font('Arial', 'B', 12)

            except Exception as e:
                Logger.error(f"{self.name}: {e}")
                pdf.ln(10)
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, "Foto kendaraan: Dynamic Gagal dimuat", align='C')
                pdf.ln(10)
            pdf.ln(5)
            self.generate_identity_section(pdf)
            self.generate_dimensions_section(pdf)
            self.generate_axle_tire_section(pdf)
            pdf.add_page()
            # HASIL PENGUJIAN
            # ==================================================================
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 5, "III. HASIL PENGUJIAN", align='L', ln=1)
            self.generate_visual_section(pdf)
            self.generate_emisi_section(pdf)
            self.generate_dynamic_test_section(pdf, "C. Pengujian Daya Pancar Lampu", "M04")
            self.generate_dynamic_test_section(pdf, "D. Tingkat Kebisingan", "K21")
            self.generate_dynamic_test_section(pdf, "E. Kedalaman Alur Ban", "K18")
            self.generate_dynamic_test_section(pdf, "F. Kegelapan Kaca", "K20")
            pdf.add_page()
            self.generate_load_brake_section(pdf)
            self.generate_dynamic_test_section(pdf, "H. Pengujian Kincup Roda Depan", "M05")
            self.generate_dynamic_test_section(pdf, "I. Pengujian Kecepatan", "M02")

            self.generate_notes_section(pdf)
            pdf.cell(0, 8, "IV. KEPUTUSAN AKHIR", align='L', ln=1)

            if self.current_test_results and all(str(hasil) == '1' for hasil in self.current_test_results.values()):
                result_text = "LULUS"
            else:
                result_text = "TIDAK LULUS"
            
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 15, result_text, border=1, align='C', ln=1)
            pdf.ln(5)
            
            # Tampilkan tanggal berlaku hanya jika LULUS
            if result_text == "LULUS":
                pdf.set_font('Arial', '', 12)
                tgl_sekarang = datetime.date.today()
                try:
                    from dateutil.relativedelta import relativedelta
                    tgl_habis = tgl_sekarang + relativedelta(months=+6)
                except ImportError:
                    tgl_habis = tgl_sekarang + datetime.timedelta(days=180)
                pdf.cell(0, 7, f"Berlaku hingga: {tgl_habis.strftime('%d %B %Y')}", align='R', ln=1)
            
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 7, "Petugas Teknis Uji", align='R', ln=1)
            
            documents_dir = os.path.join(os.environ["USERPROFILE"], "Documents")
            folder_name = f"Laporan_Akhir_VIIS_{time.strftime('%Y-%m-%d')}"
            date_folder_path = os.path.join(documents_dir, folder_name)
            os.makedirs(date_folder_path, exist_ok=True)
            pdf_filename = f"Laporan_Akhir_{dt_no_pol}_{dt_no_antri}.pdf"
            pdf_path = os.path.join(date_folder_path, pdf_filename)
            pdf.output(pdf_path, 'F')
            toast(f"Laporan Akhir disimpan: {pdf_path}")
            os.startfile(pdf_path)

        except Exception as e:
            toast_msg = f'Gagal membuat Laporan Akhir PDF'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, Detail: {e}")

    def exec_print_thermal(self):
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_jns_kend
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global db_load_left_value, db_load_right_value, db_load_total_value, dt_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, dt_brake_total_value, dt_brake_efficiency_value
        global db_handbrake_left_value, db_handbrake_right_value, dt_handbrake_total_value, dt_handbrake_efficiency_value

        try:
            printer = Serial(
                devfile=PRINTER_THERM_COM,
                baudrate=PRINTER_THERM_BAUD,
                bytesize=PRINTER_THERM_BYTESIZE,
                parity=PRINTER_THERM_PARITY,
                stopbits=PRINTER_THERM_STOPBITS,
                timeout=PRINTER_THERM_TIMEOUT,
                dsrdtr=PRINTER_THERM_DSRDTR,
            )

            print_datetime = time.strftime("%d %b %Y %H:%M", time.localtime())
            try:
                printer.image("assets/images/logo-dishub-thermal.png")
            except:
                printer.textln("DISHUB PANDEGLANG")

            printer.textln("VIIS - AXLE & BRAKE")
            printer.textln("="*32)

            # Header
            printer.text(f"Antrian: {dt_no_antri}\n")
            printer.text(f"No Pol: {dt_no_pol}\n")
            printer.text(f"No Uji: {dt_no_uji}\n")
            printer.text(f"Jenis: {dt_jns_kend}\n")
            printer.text(f"Tgl: {print_datetime}\n")
            printer.textln("-" * 32)

            # Axle Load
            printer.textln("AXLE LOAD")
            printer.text("Sb\tKiri\tKanan\tTotal\n")
            for i in range(10):
                if db_load_total_value[i] > 0:
                    printer.text(f"S{i+1}\t{int(db_load_left_value[i])}\t{int(db_load_right_value[i])}\t{int(db_load_total_value[i])}\n")
            printer.text(f"Ttl: {int(dt_load_total_value)} kg\n")
            printer.text(f"Status: {'Lulus' if dt_load_flag == 2 else 'Tdk Lulus' if dt_load_flag == 1 else 'Belum'}\n")
            printer.textln("-" * 32)

            # Brake
            printer.textln("REM UTAMA")
            printer.text("Sb\tKiri\tKanan\tSelisih\n")
            for i in range(10):
                if db_brake_total_value[i] > 0:
                    printer.text(f"S{i+1}\t{int(db_brake_left_value[i])}\t{int(db_brake_right_value[i])}\t{int(db_brake_difference_value[i])}\n")
            printer.text(f"Ttl: {int(dt_brake_total_value)} kg\n")
            printer.text(f"Efisiensi: {dt_brake_efficiency_value:.1f}%\n")
            printer.text(f"Status: {'Lulus' if dt_brake_flag == 2 else 'Tdk Lulus' if dt_brake_flag == 1 else 'Belum'}\n")
            printer.textln("-" * 32)

            # Handbrake
            printer.textln("REM PARKIR")
            printer.text("Sb\tKiri\tKanan\n")
            for i in range(10):
                if db_handbrake_left_value[i] > 0 or db_handbrake_right_value[i] > 0:
                    printer.text(f"S{i+1}\t{int(db_handbrake_left_value[i])}\t{int(db_handbrake_right_value[i])}\n")
            printer.text(f"Ttl: {int(dt_handbrake_total_value)} kg\n")
            printer.text(f"Efisiensi: {dt_handbrake_efficiency_value:.1f}%\n")
            printer.text(f"Status: {'Lulus' if dt_handbrake_flag == 2 else 'Tdk Lulus' if dt_handbrake_flag == 1 else 'Belum'}\n")
            printer.textln("=" * 32)

            # Final Result
            final_ok = (dt_brake_flag == 2) and (dt_handbrake_flag == 2)
            result = "LULUS" if final_ok else "TIDAK LULUS"
            printer.textln(f"KEPUTUSAN: {result}")

            printer.textln("Petugas:")
            printer.textln(" ") 
            printer.cut()

            toast("Thermal print berhasil")

        except Exception as e:
            toast_msg = "Gagal cetak thermal"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, Error: {e}")

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class RootScreen(ScreenManager):
    pass             

class FinalVerifierApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_resize=self.on_window_resize)

    def build(self):
        global window_size_x, window_size_y
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/images/logo-load-app.png'
        window_size_y = Window.size[0]
        window_size_x = Window.size[1]
        self.set_dynamic_fonts(Window.size)

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")
        
        LabelBase.register(
            name="Draco",
            fn_regular="assets/fonts/Draco.otf")        

        LabelBase.register(
            name="Recharge",
            fn_regular="assets/fonts/Recharge.otf") 
        
        theme_font_styles.append('H1')
        self.theme_cls.font_styles["H1"] = [
            "Orbitron-Regular", 64, False, 0.15]       

        theme_font_styles.append('H2')
        self.theme_cls.font_styles["H2"] = [
            "Orbitron-Regular", 32, False, 0.15] 
        
        theme_font_styles.append('H4')
        self.theme_cls.font_styles["H4"] = [
            "Recharge", 30, False, 0.15] 

        theme_font_styles.append('H5')
        self.theme_cls.font_styles["H5"] = [
            "Recharge", 20, False, 0.15] 

        theme_font_styles.append('H6')
        self.theme_cls.font_styles["H6"] = [
            "Recharge", 16, False, 0.15] 

        theme_font_styles.append('Subtitle1')
        self.theme_cls.font_styles["Subtitle1"] = [
            "Recharge", 11, False, 0.15] 

        theme_font_styles.append('Body1')
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", 10, False, 0.15] 
        
        theme_font_styles.append('Button')
        self.theme_cls.font_styles["Button"] = [
            "Recharge", 9, False, 0.15] 

        theme_font_styles.append('Caption')
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", 8, False, 0.15]       
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()

    def on_window_resize(self, window, width, height):
        Logger.info(f"Window size: {width}x{height}")
        self.set_dynamic_fonts((width, height))
        self.refresh_all_fonts()

    def refresh_all_fonts(self):
        if hasattr(self, 'root') and hasattr(self.root, 'screens'):
            for screen in self.root.screens:
                self.refresh_fonts(screen)

    def refresh_fonts(self, widget):
        from kivymd.uix.label import MDLabel
        if isinstance(widget, MDLabel):
            original_style = widget.font_style
            style = "Body1" if original_style != "Body1" else "H6"
            widget.font_style = style
            widget.font_style = original_style
        if hasattr(widget, 'children'):
            for child in widget.children:
                self.refresh_fonts(child)

    def set_dynamic_fonts(self, size):
        try:
            screen_size_x = Window.system_size[0]
            screen_size_y = Window.system_size[1]
        except AttributeError:
            screen_size_x = Window._get_system_size()[0]
            screen_size_y = Window._get_system_size()[1]
        font_size_l = np.array([64, 32, 30, 20, 16, 11, 10, 9, 8])
        scale = min(screen_size_x / 1920, screen_size_y / 1080)
        font_size = np.round(font_size_l * scale, 0)
        Logger.info(f"Font resized: {font_size_l} to {font_size}")
        self.theme_cls.font_styles["H1"] = [
            "Orbitron-Regular", font_size[0], False, 0.15]
        self.theme_cls.font_styles["H2"] = [
            "Orbitron-Regular", font_size[1], False, 0.15]
        self.theme_cls.font_styles["H4"] = [
            "Recharge", font_size[2], False, 0.15]
        self.theme_cls.font_styles["H5"] = [
            "Recharge", font_size[3], False, 0.15]
        self.theme_cls.font_styles["H6"] = [
            "Recharge", font_size[4], False, 0.15]
        self.theme_cls.font_styles["Subtitle1"] = [
            "Recharge", font_size[5], False, 0.15]
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", font_size[6], False, 0.15]
        self.theme_cls.font_styles["Button"] = [
            "Recharge", font_size[7], False, 0.15]
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", font_size[8], False, 0.15]       

        if hasattr(self, 'root'):
            self.refresh_fonts(self.root)

if __name__ == '__main__':
    FinalVerifierApp().run()
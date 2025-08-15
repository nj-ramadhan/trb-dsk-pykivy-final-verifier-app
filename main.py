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

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)
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
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    

        except Exception as e:
            toast_msg = f'error Login: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_login(self):
        global mydb, db_users
        global dt_id_user, dt_user, dt_foto_user

        screen_main = self.screen_manager.get_screen('screen_main')

        try:
            screen_main.exec_reload_database()
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        
            # Adding salt at the last of the password
            dataBase_password = input_password
            # Encoding the password
            hashed_password = hashlib.md5(dataBase_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, image FROM {TB_USER} WHERE username = '{input_username}' and password = '{hashed_password.hexdigest()}'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            
            if myresult is None:
                toast_msg = f'Gagal Masuk, Nama Pengguna atau Password Salah'
                toast(toast_msg) 
                Logger.warning(f"{self.name}: {toast_msg}") 
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

                dt_id_user = myresult[0]
                dt_user = myresult[1]
                dt_foto_user = myresult[4]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal masuk, silahkan isi nama user dan password yang sesuai'
            toast(toast_msg)  
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Awal'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Utama'
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

        dt_user = dt_foto_user = dt_no_antri = dt_no_pol = dt_no_uji = dt_sts_uji = dt_nama = ""
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
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_printer = self.screen_manager.get_screen('screen_printer')
            
            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_home.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_home.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_printer.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_printer.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_dash_antri.text = str(dt_dash_antri)
            self.ids.lb_dash_belum_uji.text = str(dt_dash_belum_uji)
            self.ids.lb_dash_sudah_uji.text = str(dt_dash_sudah_uji)

            # self.ids.bt_calibrate.disabled = False if dt_user != '' else True
            # self.ids.bt_add_data.disabled = False if dt_user != '' else True
            # self.ids.bt_add_queue.disabled = False if dt_user != '' else True
            self.ids.bt_logout.disabled = False if dt_user != '' else True

            self.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_home.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_printer.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'

            if dt_user != '':
                self.ids.img_user.source = f'https://{FTP_HOST}/system/storage/app/foto_user/{dt_foto_user}'
                screen_home.ids.img_user.source = f'https://{FTP_HOST}/system/storage/app/foto_user/{dt_foto_user}'
                screen_login.ids.img_user.source = f'https://{FTP_HOST}/system/storage/app/foto_user/{dt_foto_user}'
            else:
                self.ids.img_user.source = 'assets/images/icon-login.png'
                screen_home.ids.img_user.source = 'assets/images/icon-login.png'
                screen_login.ids.img_user.source = 'assets/images/icon-login.png'

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
            result = cursor.fetchone()  # Returns tuple like (123,)

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
                        # MDLabel(text=f"{db_antrian[6, i]}", size_hint_x= 0.15),
                        # MDLabel(text=f"{db_antrian[7, i]}", size_hint_x= 0.05),
                        # MDLabel(text=f"{db_antrian[8, i]}", size_hint_x= 0.05),
                        # MDLabel(text='-' if db_antrian[9, i] == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == db_antrian[9, i])[0][0],1]}" , size_hint_x= 0.08),
                        # MDLabel(text='-' if db_antrian[10, i] == None else f"{db_warna[np.where(db_warna == db_antrian[10, i])[0][0],1]}" , size_hint_x= 0.11),
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

    def exec_logout(self):
        global dt_user

        dt_user = ""
        self.screen_manager.current = 'screen_login'

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_menu(self):

        if (dt_user != ''):
            # if (int(dt_load_flag) == 0 or int(dt_brake_flag) == 0 or int(dt_handbrake_flag) == 0):
            self.screen_manager.current = 'screen_printer'
            # else:
            #     toast_msg = f'No. Antrian {dt_no_antri} Sudah Tes'
            #     toast(toast_msg)
            #     Logger.info(f"{self.name}: {toast_msg}")
        else:
            toast_msg = f'Silahkan Login Untuk Melakukan Pengujian'
            toast(toast_msg)
            Logger.info(f"{self.name}: {toast_msg}")      

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
        Clock.schedule_once(self.load_dropdowns, 0.1)  # Small delay to ensure UI is loaded

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
            # --- Merk Dropdown ---
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

            # --- Bahan Bakar Dropdown ---
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

            # --- Warna Dropdown ---
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

    # Set functions for dropdown selection
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

            # self.ids.lb_nama.text = f'{dt_nama}'
            # self.ids.lb_alamat.text = f'{dt_alamat}'
            # self.ids.lb_no_uji.text = f'{dt_no_uji}'
            # self.ids.lb_no_pol.text = f'{dt_no_pol}'
            # self.ids.lb_status_uji.text = 'Berkala' if dt_status_uji == 'B' else 'Uji Ulang' if dt_status_uji == 'U' else 'Baru' if dt_status_uji == 'BR' else 'Numpang Uji' if dt_status_uji == 'NB' else 'Mutasi'
            # self.ids.lb_tgl_uji_terakhir.text = f'{dt_tgl_uji_terakhir}'
            # self.ids.lb_tgl_uji_habis.text = f'{dt_tgl_uji_habis}'
            # self.ids.lb_merk.text = '-' if dt_id_merk == None else f"{db_merk[np.where(db_merk == dt_id_merk)[0][0],1]}"
            # self.ids.lb_type.text = f'{dt_type}'
            # self.ids.lb_jenis_kendaraan.text = f'{dt_jenis_kendaraan}'
            # self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"
            # self.ids.lb_chasis.text = f'{dt_chasis}'
            # self.ids.lb_mesin.text = f'{dt_mesin}'
            # self.ids.lb_bahan_bakar.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
            # self.ids.lb_jbb.text = f'{dt_jbb}'
            # self.ids.lb_berat_kosong.text = f'{dt_brt_ksg}'

            # Validate dropdowns have values selected
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

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast(f"Anda sudah login sebagai {dt_user}")

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Login'
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

    def load_data(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna
        global dt_visual_flag, dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_sideslip_flag, dt_speed_flag
        global db_load_left_value, db_load_right_value, db_load_total_value, dt_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_visual_flag, dt_speed_flag, dt_speed_value, dt_sideslip_flag, dt_sideslip_value
        
        try:
            # Connect to DB
            cursor = mydb.cursor()

            # Query: Get one record by noantrian (or modify to get latest)
            query = f"""
            SELECT 
                noantrian, nouji, nopol, jbb, berat_kosong,
                load_flag,
                load_l_s1_value, load_r_s1_value, load_total_s1_value,
                load_l_s2_value, load_r_s2_value, load_total_s2_value,
                load_l_s3_value, load_r_s3_value, load_total_s3_value,
                load_l_s4_value, load_r_s4_value, load_total_s4_value,
                load_l_s5_value, load_r_s5_value, load_total_s5_value,
                load_l_s6_value, load_r_s6_value, load_total_s6_value,
                load_l_s7_value, load_r_s7_value, load_total_s7_value,
                load_l_s8_value, load_r_s8_value, load_total_s8_value,
                load_l_s9_value, load_r_s9_value, load_total_s9_value,
                load_l_s10_value, load_r_s10_value, load_total_s10_value,
                load_total_value,
                brake_flag,
                brake_l_s1_value, brake_r_s1_value, brake_total_s1_value, brake_difference_s1_value,
                brake_l_s2_value, brake_r_s2_value, brake_total_s2_value, brake_difference_s2_value,
                brake_l_s3_value, brake_r_s3_value, brake_total_s3_value, brake_difference_s3_value,
                brake_l_s4_value, brake_r_s4_value, brake_total_s4_value, brake_difference_s4_value,
                brake_l_s5_value, brake_r_s5_value, brake_total_s5_value, brake_difference_s5_value,
                brake_l_s6_value, brake_r_s6_value, brake_total_s6_value, brake_difference_s6_value,
                brake_l_s7_value, brake_r_s7_value, brake_total_s7_value, brake_difference_s7_value,
                brake_l_s8_value, brake_r_s8_value, brake_total_s8_value, brake_difference_s8_value,
                brake_l_s9_value, brake_r_s9_value, brake_total_s9_value, brake_difference_s9_value,
                brake_l_s10_value, brake_r_s10_value, brake_total_s10_value, brake_difference_s10_value,
                brake_total_value, brake_efficiency_value, brake_difference_value,
                handbrake_flag,
                handbrake_l_s1_value, handbrake_r_s1_value,
                handbrake_l_s2_value, handbrake_r_s2_value,
                handbrake_l_s3_value, handbrake_r_s3_value,
                handbrake_l_s4_value, handbrake_r_s4_value,
                handbrake_l_s5_value, handbrake_r_s5_value,
                handbrake_l_s6_value, handbrake_r_s6_value,
                handbrake_l_s7_value, handbrake_r_s7_value,
                handbrake_l_s8_value, handbrake_r_s8_value,
                handbrake_l_s9_value, handbrake_r_s9_value,
                handbrake_l_s10_value, handbrake_r_s10_value,
                handbrake_total_value, handbrake_efficiency_value, handbrake_difference_value,
                check_flag, 
                speed_flag, speed_value,
                sideslip_flag, sideslip_value
            FROM {TB_DATA}
            WHERE noantrian = %s
            """

            cursor.execute(query, (dt_no_antri,))
            result = cursor.fetchone()

            if result is None:
                toast("Data tidak ditemukan untuk nomor antrian tersebut.")
                # Reset variables or exit
            else:
                # Convert to NumPy array (optional, for consistency)
                db_row = np.array(result, dtype=object)

                # === Map to your global variables used in PDF ===
                # Basic Info
                dt_no_antri = result[0]
                dt_no_uji = result[1]
                dt_no_pol = result[2]
                dt_jbb = float(result[3]) if result[3] else 0.0
                dt_brt_ksg = float(result[4]) if result[4] else 0.0

                # Axle Load
                dt_load_flag = int(result[5]) if result[5] is not None else 0

                # Initialize arrays for 10 axles (index 0 to 9)
                db_load_left_value = np.zeros(10)
                db_load_right_value = np.zeros(10)
                db_load_total_value = np.zeros(10)

                for i in range(10):
                    db_load_left_value[i] = float(result[6 + i*3]) if result[6 + i*3] else 0.0
                    db_load_right_value[i] = float(result[7 + i*3]) if result[7 + i*3] else 0.0
                    db_load_total_value[i] = float(result[8 + i*3]) if result[8 + i*3] else 0.0

                dt_load_total_value = float(result[6 + 10*3]) if result[6 + 10*3] else 0.0  # load_total_value

                # Brake
                dt_brake_flag = int(result[37]) if result[37] is not None else 0

                db_brake_left_value = np.zeros(10)
                db_brake_right_value = np.zeros(10)
                db_brake_total_value = np.zeros(10)
                db_brake_difference_value = np.zeros(10)

                brake_start_idx = 38  # First brake_l_s1_value
                for i in range(10):
                    idx = brake_start_idx + i * 4
                    db_brake_left_value[i] = float(result[idx]) if result[idx] else 0.0
                    db_brake_right_value[i] = float(result[idx + 1]) if result[idx + 1] else 0.0
                    db_brake_total_value[i] = float(result[idx + 2]) if result[idx + 2] else 0.0
                    db_brake_difference_value[i] = float(result[idx + 3]) if result[idx + 3] else 0.0

                dt_brake_total_value = float(result[38 + 10*4]) if result[38 + 10*4] else 0.0       # brake_total_value
                dt_brake_efficiency_value = float(result[38 + 10*4 + 1]) if result[38 + 10*4 + 1] else 0.0  # brake_efficiency_value
                dt_brake_difference_value = float(result[38 + 10*4 + 2]) if result[38 + 10*4 + 2] else 0.0  # brake_difference_value

                # Handbrake
                dt_handbrake_flag = int(result[81]) if result[81] is not None else 0

                db_handbrake_left_value = np.zeros(10)
                db_handbrake_right_value = np.zeros(10)

                # Handbrake values
                handbrake_start_idx = 82  # handbrake_l_s1_value starts at index 82
                for i in range(10):
                    idx = handbrake_start_idx + i * 2
                    db_handbrake_left_value[i] = float(result[idx]) if result[idx] is not None else 0.0
                    db_handbrake_right_value[i] = float(result[idx + 1]) if result[idx + 1] is not None else 0.0

                dt_handbrake_total_value = float(result[102]) if result[102] is not None else 0.0
                dt_handbrake_efficiency_value = float(result[103]) if result[103] is not None else 0.0
                dt_handbrake_difference_value = float(result[104]) if result[104] is not None else 0.0

                # Lamp / Visual Check
                dt_visual_flag = int(result[105]) == 1 if result[105] is not None else False

                # Speed
                dt_speed_flag = int(result[106]) == 1 if result[106] is not None else False
                dt_speed_value = float(result[107]) if result[107] is not None else 0.0

                # Sideslip
                dt_sideslip_flag = int(result[108]) == 1 if result[108] is not None else False
                dt_sideslip_value = float(result[109]) if result[109] is not None else 0.0

                toast(f"Data berhasil dimuat: No Antri {dt_no_antri}")

            cursor.close()
            mydb.close()

        except mysql.connector.Error as err:
            toast(f"Database error: {err}")
            Logger.error(f"MySQL Error: {err}")
                    
    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_save(self):
        global mydb, db_antrian, dt_id_user, dt_no_antri

        try:
            try:
                mycursor = mydb.cursor()
                # Build SQL query safely
                sql = f"UPDATE {TB_DATA} SET print_flag = 1"
                mycursor.execute(sql)
                mydb.commit()
                Logger.info(f"Successfully updated print flag for noantrian={dt_no_antri}")
            except Exception as e:
                toast_msg = f'Error Save Print FLag'
                toast(toast_msg)
                Logger.error(f"{self.name}: {toast_msg}, {e}")          
        except Exception as e:
            toast_msg = f'Error Save Data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print(self):
        try:           
            self.exec_print_thermal()
            self.exec_print_pdf()

        except Exception as e:
            toast_msg = f'Gagal Mencetak Hasil Uji'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print_pdf(self):
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_merk, dt_type, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global dt_visual_flag, dt_speed_flag, dt_speed_value, dt_sideslip_flag, dt_sideslip_value
        global db_load_left_value, db_load_right_value, db_load_total_value, dt_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value
        global dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value

        try:
            print_datetime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            pdf = FPDF(format='A4', unit='mm')  # Standard A4
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # --- Header: Logos & Title ---
            pdf.image(f"assets/images/{IMG_LOGO_DISHUB}", x=20, y=10, w=30)
            pdf.image(f"assets/images/{IMG_LOGO_PEMKAB}", x=160, y=10, w=30)

            pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(10, 50)
            pdf.cell(0, 10, "DINAS PERHUBUNGAN", align='C')
            pdf.set_xy(10, 58)
            pdf.cell(0, 10, "UPTD PKB KAB. PANDEGLANG", align='C')
            pdf.ln(20)

            # --- Identification ---
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "IDENTITAS KENDARAAN BERMOTOR")
            pdf.ln(10)

            pdf.set_font('Arial', '', 12)
            pdf.cell(50, 8, f"Tanggal: {print_datetime}")
            pdf.ln(8)
            pdf.cell(50, 8, f"No Reg Kend: {dt_no_pol}")
            pdf.ln(8)
            pdf.cell(50, 8, f"No Antrian: {dt_no_antri}")
            pdf.cell(0, 8, f"No Uji: {dt_no_uji}", align='R')
            pdf.ln(8)
            pdf.cell(50, 8, f"Jenis Kendaraan: {dt_jns_kend}")
            pdf.ln(8)
            pdf.cell(50, 8, f"JBB: {dt_jbb} kg")
            pdf.cell(0, 8, f"Berat Kosong: {dt_brt_ksg} kg", align='R')
            pdf.ln(15)

            # --- Vehicle Photos ---
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "Foto Kendaraan:")
            pdf.ln(10)
            y_photo = pdf.get_y()

            try:
                today = time.strftime("%Y-%m-%d")
                base_url = f"https://{FTP_HOST}/system/storage/app/capture/{today}/{dt_sts_uji}-{dt_no_antri}/{dt_no_pol}"

                # Local directory
                documents_dir = os.path.join(os.environ["USERPROFILE"], "Pictures", "VIIS")
                os.makedirs(documents_dir, exist_ok=True)

                # List to store image paths
                img_paths = []

                for i in range(1, 5):
                    url = f"{base_url}-{i}.jpg"
                    local_path = os.path.join(documents_dir, f"{dt_no_pol}_view_{i}.jpg")
                    img_paths.append(local_path)

                    try:
                        response = requests.get(url, timeout=5, stream=True)
                        if response.status_code == 200:
                            with open(local_path, 'wb') as f:
                                f.write(response.content)
                            Logger.info(f"Downloaded: {url}")
                        else:
                            Logger.warning(f"Image not found: {url} (Status: {response.status_code})")
                            img_paths[-1] = None  # Mark as missing
                    except Exception as e:
                        Logger.error(f"Failed to download {url}: {e}")
                        img_paths[-1] = None

                y_photo = pdf.get_y()
                x_positions = [15, 60, 110, 160]
                labels = ["Depan", "Belakang", "Kanan", "Kiri"]

                for i in range(4):
                    if img_paths[i] and os.path.exists(img_paths[i]):
                        try:
                            pdf.image(img_paths[i], x=x_positions[i], y=y_photo, w=40, h=30)
                            # Optional: Add label under image
                            pdf.set_xy(x_positions[i], y_photo + 30)
                            pdf.set_font('Arial', '', 8)
                            pdf.cell(40, 5, labels[i], align='C')
                        except Exception as img_err:
                            Logger.error(f"FPDF failed to insert image {img_paths[i]}: {img_err}")
                            # Optionally draw placeholder
                            pdf.set_draw_color(128)
                            pdf.rect(x_positions[i], y_photo, 40, 30)
                            pdf.set_xy(x_positions[i], y_photo + 15)
                            pdf.cell(40, 10, "Foto Error", align='C')
                    else:
                        # Draw placeholder box
                        pdf.set_draw_color(128)
                        pdf.rect(x_positions[i], y_photo, 40, 30)
                        pdf.set_xy(x_positions[i], y_photo + 10)
                        pdf.cell(40, 5, "Foto Tidak", align='C')
                        pdf.set_xy(x_positions[i], y_photo + 15)
                        pdf.cell(40, 5, "Tersedia", align='C')
                        pdf.set_xy(x_positions[i], y_photo + 30)
                        pdf.set_font('Arial', '', 8)
                        pdf.cell(40, 5, labels[i], align='C')
                        pdf.set_font('Arial', '', 12)

            except Exception as e:
                Logger.error(f"{self.name}: {e}")
                pdf.ln(10)
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, "Foto kendaraan: Gagal dimuat", align='C')
                pdf.ln(10)

            pdf.ln(20)

            # --- Technical Specs ---
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "SPESIFIKASI TEKNIS KENDARAAN")
            pdf.ln(8)

            pdf.set_font('Arial', '', 11)
            specs = [
                f"Merek: {dt_merk}",
                f"Tipe: {dt_type}",
                f"Bahan Bakar: {dt_bhn_bkr}",
                f"Warna: {dt_warna}",
                # f"Tahun: 2014",
                # f"Isi Silinder: 1,493 cc",
                # f"Daya Motor: 0.0 KW",
                # f"Ukuran Ban: 550 R13.S",
                # f"Konfigurasi Sumbu: 1.1",
                # f"Pajang: 3,750 mm",
                # f"Lebar: 1,650 mm",
                # f"Tinggi: 1,825 mm",
                # f"Jarak Sumbu: 1,970 mm",
                # f"Dimensi Muatan: (2,360x1,400x0) mm",
                # f"Daya Angkut: 3 orang / 600 kg",
                # f"Kelas Jalan: III"
            ]
            for spec in specs:
                pdf.cell(0, 7, spec)
                pdf.ln(5)

            pdf.ln(5)

            # --- Inspection Results ---
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "HASIL PENGUJIAN")
            pdf.ln(8)

            # Axle Load
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "AXLE LOAD")
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            pdf.cell(40, 8, "Sumbu")
            pdf.cell(30, 8, "Kiri (kg)")
            pdf.cell(30, 8, "Kanan (kg)")
            pdf.cell(30, 8, "Total (kg)")
            pdf.ln(8)

            for i in range(10):
                if db_load_total_value[i] > 0:
                    pdf.cell(40, 8, f"Sumbu {i+1}")
                    pdf.cell(30, 8, f"{int(db_load_left_value[i])}")
                    pdf.cell(30, 8, f"{int(db_load_right_value[i])}")
                    pdf.cell(30, 8, f"{int(db_load_total_value[i])}")
                    pdf.ln(8)

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(100, 8, "Total:")
            pdf.cell(30, 8, f"{int(dt_load_total_value)} kg")
            pdf.ln(8)

            # Brake
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "REM UTAMA")
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            pdf.cell(40, 8, "Sumbu")
            pdf.cell(30, 8, "Kiri (kg)")
            pdf.cell(30, 8, "Kanan (kg)")
            pdf.cell(30, 8, "Selisih (%)")
            pdf.ln(8)

            for i in range(10):
                if db_brake_total_value[i] > 0:
                    pdf.cell(40, 8, f"Sumbu {i+1}")
                    pdf.cell(30, 8, f"{int(db_brake_left_value[i])}")
                    pdf.cell(30, 8, f"{int(db_brake_right_value[i])}")
                    pdf.cell(30, 8, f"{int(db_brake_difference_value[i])}")
                    pdf.ln(8)

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(100, 8, "Total Rem:")
            pdf.cell(30, 8, f"{int(dt_brake_total_value)} kg")
            pdf.ln(8)
            pdf.cell(100, 8, f"Efisiensi: {np.round(dt_brake_efficiency_value, 1)} %")
            pdf.ln(8)
            result_brake = "Lulus" if dt_brake_flag == 2 else "Tidak Lulus" if dt_brake_flag == 1 else "Belum Diuji"
            pdf.cell(100, 8, f"Status: {result_brake}")
            pdf.ln(8)

            # Handbrake
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "REM PARKIR")
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            pdf.cell(40, 8, "Sumbu")
            pdf.cell(30, 8, "Kiri (kg)")
            pdf.cell(30, 8, "Kanan (kg)")
            pdf.ln(8)

            for i in range(10):
                if db_handbrake_left_value[i] > 0 or db_handbrake_right_value[i] > 0:
                    pdf.cell(40, 8, f"Sumbu {i+1}")
                    pdf.cell(30, 8, f"{int(db_handbrake_left_value[i])}")
                    pdf.cell(30, 8, f"{int(db_handbrake_right_value[i])}")
                    pdf.ln(8)

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(100, 8, "Total Rem Parkir:")
            pdf.cell(30, 8, f"{int(dt_handbrake_total_value)} kg")
            pdf.ln(8)
            pdf.cell(100, 8, f"Efisiensi: {np.round(dt_handbrake_efficiency_value, 1)} %")
            pdf.ln(8)
            result_handbrake = "Lulus" if dt_handbrake_flag == 2 else "Tidak Lulus" if dt_handbrake_flag == 1 else "Belum Diuji"
            pdf.cell(100, 8, f"Status: {result_handbrake}")
            pdf.ln(8)

            # Lamp Check
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "PENGECEKAN LAMPU")
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            lamp_status = "Lulus" if dt_visual_flag == 1 else "Belum Diperiksa"
            pdf.cell(0, 8, f"Hasil: {lamp_status}")
            pdf.ln(8)

            # Emission
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "EMISI")
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, f"CO: {getattr(self, 'emission_co_value', 0.0) or 0.0} %")
            pdf.ln(8)
            pdf.cell(0, 8, f"HC: {getattr(self, 'emission_hc_value', 0.0) or 0.0} ppm")
            pdf.ln(8)
            pdf.cell(0, 8, f"Asap: {getattr(self, 'emission_smoke_value', 0.0) or 0.0} %")
            pdf.ln(8)

            # Speed & Sideslip
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "KECEPATAN & SIDE SLIP")
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, f"Kecepatan: {dt_speed_value} rpm")
            pdf.ln(8)
            pdf.cell(0, 8, f"Side Slip: {dt_sideslip_value} mm")
            pdf.ln(10)

            # Final Result
            pdf.set_font('Arial', 'B', 16)
            final_ok = (dt_brake_flag == 2) and (dt_handbrake_flag == 2) and (dt_load_flag == 2)
            result_text = "LULUS" if final_ok else "TIDAK LULUS"
            pdf.cell(0, 10, f"KEPUTUSAN: {result_text}", align='C')
            pdf.ln(15)

            # Operator
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 8, "Petugas Penguji:")
            pdf.ln(8)
            pdf.cell(0, 8, "Nama: ")
            pdf.ln(10)
            try:
                pdf.image("assets/images/signature.png", x=20, y=pdf.get_y(), w=40)
            except:
                pdf.cell(0, 10, "Tanda Tangan: ________________")
            pdf.ln(15)

            # Save PDF
            documents_dir = os.path.join(os.environ["USERPROFILE"], "Documents")
            folder_name = f"Hasil_Uji_VIIS_Final_{time.strftime('%Y-%m-%d')}"
            date_folder_path = os.path.join(documents_dir, folder_name)
            os.makedirs(date_folder_path, exist_ok=True)

            pdf_filename = f"Hasil_Uji_No_{dt_no_antri}.pdf"
            pdf_path = os.path.join(date_folder_path, pdf_filename)

            pdf.output(pdf_path, 'F')
            toast(f"PDF saved: {pdf_path}")
            os.startfile(pdf_path)

        except Exception as e:
            toast_msg = 'Gagal menyimpan PDF'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, Error: {e}")

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

            # Logo (if supported)
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
        # Refresh fonts for all screens in the ScreenManager
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
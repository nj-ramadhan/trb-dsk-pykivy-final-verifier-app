from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.uix.screenmanager import ScreenManager
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.toast import toast
from kivymd.app import MDApp
import os, sys, time, numpy as np
import configparser, hashlib, mysql.connector
from fpdf import FPDF

colors = {
    "Red"   : {"A200": "#FF2A2A","A500": "#FF8080","A700": "#FFD5D5",},
    "Gray"  : {"200": "#CCCCCC","500": "#ECECEC","700": "#F9F9F9",},
    "Blue"  : {"200": "#4471C4","500": "#5885D8","700": "#6C99EC",},
    "Green" : {"200": "#2CA02C","500": "#2DB97F", "700": "#D5FFD5",},
    "Yellow": {"200": "#ffD42A","500": "#ffE680","700": "#fff6D5",},

    "Light" : {"StatusBar": "E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC","Text": "#000000",},
    "Dark"  : {"StatusBar": "101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#222222","FlatButtonDown": "#DDDDDD","Text": "#FFFFFF",},
}

if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(os.path.abspath(__file__))
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(app_path, 'config.ini')
print(f"Path config.ini: {config_path}")

config = configparser.ConfigParser()
config.read(config_path)
DB_HOST = config['mysql']['DB_HOST']
DB_USER = config['mysql']['DB_USER']
DB_PASSWORD = config['mysql']['DB_PASSWORD']
DB_NAME = config['mysql']['DB_NAME']
TB_DATA = config['mysql']['TB_DATA']
TB_USER = config['mysql']['TB_USER']

COUNT_STARTING = 1
COUNT_ACQUISITION = 1
TIME_OUT = 500

dt_result_flag = False
dt_result_user = 1
dt_result_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

dt_flag_playdetect = 0
dt_flag_emission = 0
dt_value_emission = 0.0
dt_flag_sideslip = 0
dt_value_sideslip = 0.0
dt_flag_load = 0
dt_value_load = 0.0
dt_flag_brake = 0
dt_value_brake = 0.0
dt_flag_speed = 0
dt_value_speed = 0.0
dt_flag_hlm = 0
dt_value_hlm = 0.0
dt_flag_slm = 0
dt_value_slm = 0.0
dt_flag_wtm = 0
dt_value_wtm = 0.0

dt_user = ""
dt_no_antrian = ""
dt_no_reg = ""
dt_no_uji = ""
dt_nama = ""
dt_jenis_kendaraan = ""
dt_flag_print = 0

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)

    def exec_cancel(self):
        try:
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    

        except Exception as e:
            toast_msg = f'Error Cancel Login: {e}'
            toast(toast_msg)

    def exec_login(self):
        global mydb, db_users
        global dt_result_user, dt_user

        try:
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        
            hashed_password = hashlib.md5(input_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, nama FROM {TB_USER} WHERE username = '"+str(input_username)+"' and password = '"+str(hashed_password.hexdigest())+"'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T

            if myresult == 0:
                toast('Gagal Masuk, Nama Pengguna atau Password Salah')
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                dt_result_user = myresult[0]
                dt_user = myresult[1]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Login: {e}'
            toast(toast_msg)        
            toast('Gagal Masuk, Nama Pengguna atau Password Salah')

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global mydb, db_antrian
        global flag_conn_stat, flag_play
        global count_starting, count_get_data

        Clock.schedule_once(self.delayed_init, 1)

        flag_conn_stat = False
        flag_play = False

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD,database = DB_NAME)

        except Exception as e:
            toast_msg = f'Error Initiate Database: {e}'
            toast(toast_msg)                      

    def delayed_init(self, dt):
        Clock.schedule_interval(self.regular_update_display, 1)
        self.exec_reload_table()

    def on_row_press(self, instance):
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan, dt_flag_print
        global dt_result_flag, dt_result_user, dt_result_post
        global db_antrian

        try:
            row = int(str(instance.id).replace("card",""))
            dt_no_antrian           = f"{db_antrian[0, row]}"
            dt_no_reg               = f"{db_antrian[1, row]}"
            dt_no_uji               = f"{db_antrian[2, row]}"
            dt_nama                 = f"{db_antrian[3, row]}"
            dt_jenis_kendaraan      = f"{db_antrian[4, row]}"
            dt_flag_print           = 'Belum Dicetak' if (int(db_antrian[5, row]) == 0) else 'Sudah Dicetak'

        except Exception as e:
            toast_msg = f'Error Update Table: {e}'
            toast(toast_msg)   

    def regular_update_display(self, dt):
        global flag_conn_stat
        global count_starting, count_get_data
        global dt_user, dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan, dt_flag_print
        global dt_result_flag, dt_result_user, dt_result_post
        global dt_flag_playdetect, dt_flag_emission, dt_value_emission, dt_flag_sideslip, dt_value_sideslip
        global dt_flag_load, dt_value_load, dt_flag_brake, dt_value_brake, dt_flag_speed, dt_value_speed
        global dt_flag_hlm, dt_value_hlm, dt_flag_slm, dt_value_slm, dt_flag_wtm, dt_value_wtm

        try:
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_printer = self.screen_manager.get_screen('screen_printer')

            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_printer.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_printer.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_no_antrian.text = str(dt_no_antrian)
            self.ids.lb_no_reg.text = str(dt_no_reg)
            self.ids.lb_no_uji.text = str(dt_no_uji)
            self.ids.lb_nama.text = str(dt_nama)
            self.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_printer.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_printer.ids.lb_no_reg.text = str(dt_no_reg)
            screen_printer.ids.lb_no_uji.text = str(dt_no_uji)
            screen_printer.ids.lb_nama.text = str(dt_nama)
            screen_printer.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            if(dt_flag_print == "Belum Dicetak"):
                self.ids.bt_start.disabled = False
            else:
                self.ids.bt_start.disabled = True

            if(not flag_play):
                screen_printer.ids.bt_print.md_bg_color = colors['Green']['200']
                screen_printer.ids.bt_print.disabled = False
                screen_printer.ids.bt_back.md_bg_color = colors['Blue']['200']
                screen_printer.ids.bt_back.disabled = False
            else:
                screen_printer.ids.bt_print.disabled = True
                screen_printer.ids.bt_back.disabled = True

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = ""
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = ""
                screen_printer.ids.lb_comm.color = colors['Red']['A200']
                screen_printer.ids.lb_comm.text = ""

            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = ""
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = ""
                screen_printer.ids.lb_comm.color = colors['Blue']['200']
                screen_printer.ids.lb_comm.text = ""

            if(count_starting <= 0):
                screen_printer.ids.lb_info.text = "Silahkan tekan tombol CETAK"
                                               
            elif(count_starting > 0):
                if(flag_play):
                    screen_printer.ids.lb_info.text = "Sedang mengambil data dari Database"
                    screen_printer.ids.lb_result_value_playdetect.text = ""
                    screen_printer.ids.lb_result_flag_playdetect.text = ""
                    screen_printer.ids.lb_result_value_emission.text = ""
                    screen_printer.ids.lb_result_flag_emission.text = ""
                    screen_printer.ids.lb_result_value_sideslip.text = ""
                    screen_printer.ids.lb_result_flag_sideslip.text = ""
                    screen_printer.ids.lb_result_value_load.text = ""
                    screen_printer.ids.lb_result_flag_load.text = ""
                    screen_printer.ids.lb_result_value_brake.text = ""
                    screen_printer.ids.lb_result_flag_brake.text = ""
                    screen_printer.ids.lb_result_value_speed.text = ""
                    screen_printer.ids.lb_result_flag_speed.text = ""
                    screen_printer.ids.lb_result_value_hlm.text = ""
                    screen_printer.ids.lb_result_flag_hlm.text = ""
                    screen_printer.ids.lb_result_value_slm.text = ""
                    screen_printer.ids.lb_result_flag_slm.text = ""
                    screen_printer.ids.lb_result_value_wtm.text = ""
                    screen_printer.ids.lb_result_flag_wtm.text = ""
            if(count_get_data <= 0):
                if(not flag_play):
                    screen_printer.ids.lb_result_value_playdetect.text = ""
                    screen_printer.ids.lb_result_flag_playdetect.text = 'Belum Tes' if (int(dt_flag_playdetect) == 0) else ('Lulus' if (int(dt_flag_playdetect) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_emission.text = str(dt_value_emission)
                    screen_printer.ids.lb_result_flag_emission.text = 'Belum Tes' if (int(dt_flag_emission) == 0) else ('Lulus' if (int(dt_flag_emission) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_sideslip.text = str(dt_value_sideslip)
                    screen_printer.ids.lb_result_flag_sideslip.text = 'Belum Tes' if (int(dt_flag_sideslip) == 0) else ('Lulus' if (int(dt_flag_sideslip) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_load.text = str(dt_value_load)
                    screen_printer.ids.lb_result_flag_load.text = 'Belum Tes' if (int(dt_flag_load) == 0) else ('Lulus' if (int(dt_flag_load) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_brake.text = str(dt_value_brake)
                    screen_printer.ids.lb_result_flag_brake.text = 'Belum Tes' if (int(dt_flag_brake) == 0) else ('Lulus' if (int(dt_flag_brake) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_speed.text = str(dt_value_speed)
                    screen_printer.ids.lb_result_flag_speed.text = 'Belum Tes' if (int(dt_flag_speed) == 0) else ('Lulus' if (int(dt_flag_speed) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_hlm.text = str(dt_value_hlm)
                    screen_printer.ids.lb_result_flag_hlm.text = 'Belum Tes' if (int(dt_flag_hlm) == 0) else ('Lulus' if (int(dt_flag_hlm) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_slm.text = str(dt_value_slm)
                    screen_printer.ids.lb_result_flag_slm.text = 'Belum Tes' if (int(dt_flag_slm) == 0) else ('Lulus' if (int(dt_flag_slm) == 1) else 'Tidak Lulus')
                    screen_printer.ids.lb_result_value_wtm.text = str(dt_value_wtm)
                    screen_printer.ids.lb_result_flag_wtm.text = 'Belum Tes' if (int(dt_flag_wtm) == 0) else ('Lulus' if (int(dt_flag_wtm) == 1) else 'Tidak Lulus')

                    if(dt_result_flag == True):
                        screen_printer.ids.lb_test_result.md_bg_color = colors['Green']['200']
                        screen_printer.ids.lb_test_result.text = "LULUS"
                        screen_printer.ids.lb_test_result.text_color = colors['Green']['700']
                    else:
                        screen_printer.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                        screen_printer.ids.lb_test_result.text = "TIDAK LULUS"
                        screen_printer.ids.lb_test_result.text_color = colors['Red']['A700']

            elif(count_get_data > 0):
                    screen_printer.ids.lb_test_result.md_bg_color = "#EEEEEE"
                    screen_printer.ids.lb_test_result.text = ""

            self.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_printer.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'

        except Exception as e:
            toast_msg = f'Error Update Display: {e}'
            toast(toast_msg)                

    def regular_get_data(self, dt):
        global flag_play
        global dt_result_flag, dt_no_antrian
        global count_starting, count_get_data
        global mydb, db_data
        global dt_flag_playdetect, dt_flag_emission, dt_value_emission, dt_flag_sideslip, dt_value_sideslip
        global dt_flag_load, dt_value_load, dt_flag_brake, dt_value_brake, dt_flag_speed, dt_value_speed
        global dt_flag_hlm, dt_value_hlm, dt_flag_slm, dt_value_slm, dt_flag_wtm, dt_value_wtm

        try:
            if(count_starting > 0):
                count_starting -= 1              

            if(count_get_data > 0):
                count_get_data -= 1
                
            elif(count_get_data <= 0):
                flag_play = False
                Clock.unschedule(self.regular_get_data)

                mycursor = mydb.cursor()
                mycursor.execute(f"SELECT check_flag, emission_flag, emission_value, sideslip_flag, sideslip_value, load_flag, load_l_value, load_r_value, brake_flag, brake_value, speed_flag, speed_value, hlm_flag, hlm_value, slm_flag, slm_value, wtm_flag, wtm_value FROM {TB_DATA} WHERE noantrian = '"+str(dt_no_antrian)+"'")
                myresult = mycursor.fetchone()
                mydb.commit()
                db_data = np.array(myresult).T

                dt_flag_playdetect = int(db_data[0])
                dt_flag_emission = int(db_data[1])
                dt_value_emission = 0.0 if db_data[2] == None else float(db_data[2])
                dt_flag_sideslip = int(db_data[3])
                dt_value_sideslip = 0.0 if db_data[4] == None else float(db_data[4])
                dt_flag_load = int(db_data[5])
                dt_value_load = 0.0 if db_data[6] == None or db_data[7] == None else float((db_data[6] + db_data[7]) / 2)
                dt_flag_brake = int(db_data[8])
                dt_value_brake = 0.0 if db_data[9] == None else float(db_data[9])
                dt_flag_speed = int(db_data[10])
                dt_value_speed = 0.0 if db_data[11] == None else float(db_data[11])
                dt_flag_hlm = int(db_data[12])
                dt_value_hlm = 0.0 if db_data[13] == None else float(db_data[13])
                dt_flag_slm = int(db_data[14])
                dt_value_slm = 0.0 if db_data[15] == None else float(db_data[15])
                dt_flag_wtm = int(db_data[16])
                dt_value_wtm = 0.0 if db_data[17] == None else float(db_data[17])

                dt_result_flag = (dt_flag_playdetect == 1) and (dt_flag_emission == 1) and (dt_flag_sideslip == 1) and (dt_flag_load == 1) and (dt_flag_brake == 1) and (dt_flag_speed == 1) and (dt_flag_hlm == 1) and (dt_flag_slm == 1) and (dt_flag_wtm == 1)

        except Exception as e:
            toast_msg = f'Error Get Data: {e}'
            print(toast_msg) 

    def exec_reload_table(self):
        global mydb, db_antrian

        try:
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT noantrian, nopol, nouji, user, idjeniskendaraan, print_flag FROM {TB_DATA}")
            myresult = mycursor.fetchall()
            mydb.commit()
            db_antrian = np.array(myresult).T

            layout_list = self.ids.layout_list
            layout_list.clear_widgets(children=None)

        except Exception as e:
            toast_msg = f'Error Remove Widget: {e}'
            print(toast_msg)
        
        try:           
            layout_list = self.ids.layout_list
            for i in range(db_antrian[0,:].size):
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{i+1}", size_hint_x= 0.1),
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.2),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.3),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.3),
                        MDLabel(text=f"{db_antrian[3, i]}", size_hint_x= 0.3),
                        MDLabel(text=f"{db_antrian[4, i]}", size_hint_x= 0.4),
                        MDLabel(text='Belum Dicetak' if (int(db_antrian[5, i]) == 0) else 'Sudah Dicetak', size_hint_x= 0.2),

                        ripple_behavior = True,
                        on_press = self.on_row_press,
                        padding = 10,
                        id=f"card{i}",
                        size_hint_y=None,
                        height="60dp",
                        )
                    )

        except Exception as e:
            toast_msg = f'Error Reload Table: {e}'
            print(toast_msg)

    def exec_start(self):
        global flag_play

        if(not flag_play):
            Clock.schedule_interval(self.regular_get_data, 1)
            self.open_screen_printer()
            flag_play = True

    def open_screen_printer(self):
        self.screen_manager.current = 'screen_printer'

    def exec_logout(self):
        global dt_user

        dt_user = ""
        self.screen_manager.current = 'screen_login'

class ScreenPrinter(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenPrinter, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)

    def delayed_init(self, dt):
        pass

    def exec_print(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan, dt_flag_print
        global dt_flag_playdetect, dt_flag_emission, dt_value_emission, dt_flag_sideslip, dt_value_sideslip
        global dt_flag_load, dt_value_load, dt_flag_brake, dt_value_brake, dt_flag_speed, dt_value_speed
        global dt_flag_hlm, dt_value_hlm, dt_flag_slm, dt_value_slm, dt_flag_wtm, dt_value_wtm

        try:
            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET print_flag = %s WHERE noantrian = %s"
            print_datetime = str(time.strftime("%d %B %Y %H:%M:%S", time.localtime()))
            sql_val = (1, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            pdf = FPDF()
            pdf.add_page()
            pdf.set_xy(0, 10)
            pdf.image("assets/logo-dishub.png", w=30.0, h=0, x=90)
            pdf.set_font('Arial', 'B', 24.0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=1, h=15.0, align='C', w=0, txt="HASIL UJI KENDARAAN", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.set_font('Arial', 'B', 14.0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"Tanggal: {print_datetime}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"No Antrian: {dt_no_antrian}", border=0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"No Reg: {dt_no_reg}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"No Uji: {dt_no_uji}", border=0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"Nama: {dt_nama}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"Jenis Kendaraan: {dt_jenis_kendaraan}", border=0)
            pdf.cell(ln=1, h=10.0, w=0)
            pdf.set_font('Arial', '', 14.0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Visual Check")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Status : {'Lulus' if dt_flag_playdetect == 1 else 'Tidak Lulus' if dt_flag_playdetect == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Emisi")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_emission == 1 else 'Tidak Lulus' if dt_flag_emission == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_emission} ", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Side Slip")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_sideslip == 1 else 'Tidak Lulus' if dt_flag_sideslip == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_sideslip} mm", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Axle Load")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_load == 1 else 'Tidak Lulus' if dt_flag_load == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_load} kg", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Rem")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_brake == 1 else 'Tidak Lulus' if dt_flag_brake == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_brake} kg", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Kecepatan")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_speed == 1 else 'Tidak Lulus' if dt_flag_speed == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_speed} m/s", border=0)
            pdf.cell(ln=1, h=5.0, w=0)              
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Lampu Depan")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_hlm == 1 else 'Tidak Lulus' if dt_flag_hlm == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_hlm} lumen", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Kebisingan")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_slm == 1 else 'Tidak Lulus' if dt_flag_slm == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_slm} dB", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Uji Kecerahan Kaca Jendela")
            pdf.cell(ln=0, h=10.0, align='L', w=60, txt=f"Status : {'Lulus' if dt_flag_wtm == 1 else 'Tidak Lulus' if dt_flag_wtm == 2 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai  : {dt_value_wtm} %", border=0)

            pdf.output(f'{os.path.join(os.path.join(os.environ["USERPROFILE"]), "Documents")}\\Hasil_Uji_VIIS_{str(time.strftime("%d_%B_%Y_%H_%M_%S", time.localtime()))}.pdf', 'F')
            self.open_screen_main()

        except Exception as e:
            toast_msg = f'Error Print Data: {e}'
            print(toast_msg)
            self.open_screen_main()

    def open_screen_main(self):
        global flag_play        
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        flag_play = False   
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

    def exec_back(self):
        self.open_screen_main()

    def exec_logout(self):
        global dt_user

        dt_user = ""
        self.screen_manager.current = 'screen_login'

class RootScreen(ScreenManager):
    pass             

class FinalVerifierApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/logo.png'

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")

        theme_font_styles.append('Display')
        self.theme_cls.font_styles["Display"] = [
            "Orbitron-Regular", 72, False, 0.15]       
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()

if __name__ == '__main__':
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        FinalVerifierApp().run()
    except Exception as e:
        print(e)
    
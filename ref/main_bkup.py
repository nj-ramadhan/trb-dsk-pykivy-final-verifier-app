from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.datatables import MDDataTable
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.toast import toast
import numpy as np
import time
import mysql.connector
from escpos.printer import Serial as printerSerial
import configparser
import serial.tools.list_ports as ports
import hashlib
import serial

colors = {
    "Red": {
        "A200": "#FF2A2A",
        "A500": "#FF8080",
        "A700": "#FFD5D5",
    },

    "Gray": {
        "200": "#CCCCCC",
        "500": "#ECECEC",
        "700": "#F9F9F9",
    },

    "Blue": {
        "200": "#4471C4",
        "500": "#5885D8",
        "700": "#6C99EC",
    },

    "Green": {
        "200": "#2CA02C", #41cd93
        "500": "#2DB97F",
        "700": "#D5FFD5",
    },

    "Yellow": {
        "200": "#ffD42A",
        "500": "#ffE680",
        "700": "#fff6D5",
    },

    "Light": {
        "StatusBar": "E0E0E0",
        "AppBar": "#202020",
        "Background": "#EEEEEE",
        "CardsDialogs": "#FFFFFF",
        "FlatButtonDown": "#CCCCCC",
    },

    "Dark": {
        "StatusBar": "101010",
        "AppBar": "#E0E0E0",
        "Background": "#111111",
        "CardsDialogs": "#222222",
        "FlatButtonDown": "#DDDDDD",
    },
}

#load credentials from config.ini
config = configparser.ConfigParser()
config.read('config.ini')
DB_HOST = config['mysql']['DB_HOST']
DB_USER = config['mysql']['DB_USER']
DB_PASSWORD = config['mysql']['DB_PASSWORD']
DB_NAME = config['mysql']['DB_NAME']
TB_DATA = config['mysql']['TB_DATA']
TB_USER = config['mysql']['TB_USER']

COM_PORT_PRINTER = config['device']['COM_PORT_PRINTER']

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

dt_user = "SILAHKAN LOGIN"
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
            toast_msg = f'error Login: {e}'

    def exec_login(self):
        global mydb, db_users
        global dt_result_user, dt_user

        try:
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        

            # Encoding the password
            hashed_password = hashlib.md5(input_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, nama FROM {TB_USER} WHERE username = '"+str(input_username)+"' and password = '"+str(hashed_password.hexdigest())+"'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            #if invalid
            if myresult == 0:
                toast('Gagal Masuk, Nama Pengguna atau Password Salah')
            #else, if valid
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                dt_result_user = myresult[0]
                dt_user = myresult[1]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'error Login: {e}'
            toast(toast_msg)        
            toast('Gagal Masuk, Nama Pengguna atau Password Salah')

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global mydb, db_antrian
        global flag_conn_stat, flag_play
        global count_starting, count_get_data

        Clock.schedule_interval(self.regular_update_connection, 5)
        Clock.schedule_once(self.delayed_init, 1)

        flag_conn_stat = False
        flag_play = False

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        try:
            mydb = mysql.connector.connect(
            host = DB_HOST,
            user = DB_USER,
            password = DB_PASSWORD,
            database = DB_NAME
            )

        except Exception as e:
            toast_msg = f'error initiate Database: {e}'
            toast(toast_msg)           

    def regular_update_connection(self, dt):
        global printer
        global flag_conn_stat

        try:
            com_ports = list(ports.comports()) # create a list of com ['COM1','COM2'] 
            for i in com_ports:
                if i.name == COM_PORT_PRINTER:
                    flag_conn_stat = True

            printer = printerSerial(devfile = COM_PORT_PRINTER,
                    baudrate = 38400,
                    bytesize = 8,
                    parity = 'N',
                    stopbits = 1,
                    timeout = 1.00,
                    dsrdtr = True)    
            
        except Exception as e:
            toast_msg = f'error initiate Printer'
            toast(toast_msg)   
            flag_conn_stat = False

    def delayed_init(self, dt): #Nampilin row (run setiap 1 detik dari __init__)
        Clock.schedule_interval(self.regular_update_display, 1)
        layout = self.ids.layout_table
        
        self.data_tables = MDDataTable(
            use_pagination=True,
            pagination_menu_pos="auto",
            rows_num=10,
            column_data=[
                ("No.", dp(10), self.sort_on_num),
                ("Antrian", dp(20)),
                ("No. Reg", dp(25)),
                ("No. Uji", dp(35)),
                ("Nama", dp(35)),
                ("Jenis", dp(50)),
                ("Status", dp(40)),
            ],
        )
        self.data_tables.bind(on_row_press=self.on_row_press)
        layout.add_widget(self.data_tables)
        self.exec_reload_table()

    def sort_on_num(self, data): #buat ngesorting data
        try:
            return zip(*sorted(enumerate(data),key=lambda l: l[0][0]))
        except:
            toast("Error sorting data")

    def on_row_press(self, table, row):
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan, dt_flag_print
        global dt_result_flag, dt_result_user, dt_result_post

        try:
            start_index, end_index  = row.table.recycle_data[row.index]["range"]
            dt_no_antrian           = row.table.recycle_data[start_index + 1]["text"]
            dt_no_reg               = row.table.recycle_data[start_index + 2]["text"]
            dt_no_uji               = row.table.recycle_data[start_index + 3]["text"]
            dt_nama                 = row.table.recycle_data[start_index + 4]["text"]
            dt_jenis_kendaraan      = row.table.recycle_data[start_index + 5]["text"]
            dt_flag_print           = row.table.recycle_data[start_index + 6]["text"]

        except Exception as e:
            toast_msg = f'error update table: {e}'
            toast(toast_msg)   

    def regular_update_display(self, dt): #Update display (run setiap 1 detik dari delayed_init)
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

            #Ngatur waktu
            #Ngatur waktu
            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_printer.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_printer.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            #Ngatur identitas kendaraan (main)
            #Ngatur identitas kendaraan (main)
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
                self.ids.lb_comm.text = 'Printer Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'Printer Tidak Terhubung'
                screen_printer.ids.lb_comm.color = colors['Red']['A200']
                screen_printer.ids.lb_comm.text = 'Printer Tidak Terhubung'

            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = 'Printer Terhubung'
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = 'Printer Terhubung'
                screen_printer.ids.lb_comm.color = colors['Blue']['200']
                screen_printer.ids.lb_comm.text = 'Printer Terhubung'

            if(count_starting <= 0):
                screen_printer.ids.lb_info.text = "Silahkan tekan tombol CETAK"
                                               
            elif(count_starting > 0):
                if(flag_play):
                    screen_printer.ids.lb_info.text = "Sedang mengambil data dari Database"

            if(count_get_data <= 0):
                if(not flag_play):
                    screen_printer.ids.lb_result_value_playdetect.text = 'Belum Tes' if (int(dt_flag_playdetect) == 0) else ('Lulus' if (int(dt_flag_playdetect) == 1) else 'Tidak Lulus')
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

            self.ids.lb_operator.text = dt_user
            screen_login.ids.lb_operator.text = dt_user
            screen_printer.ids.lb_operator.text = dt_user

        except Exception as e:
            toast_msg = f'error update display: {e}'
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
            toast_msg = f'error get data: {e}'
            print(toast_msg) 

    def exec_reload_table(self):
        global mydb, db_antrian
        try:
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT noantrian, nopol, nouji, user, idjeniskendaraan, print_flag FROM {TB_DATA}")
            myresult = mycursor.fetchall()
            mydb.commit()
            db_antrian = np.array(myresult).T

            self.data_tables.row_data=[(f"{i+1}", f"{db_antrian[0, i]}", f"{db_antrian[1, i]}", f"{db_antrian[2, i]}", f"{db_antrian[3, i]}" ,f"{db_antrian[4, i]}", 
                                        'Belum Dicetak' if (int(db_antrian[5, i]) == 0) else 'Sudah Dicetak') 
                                        for i in range(len(db_antrian[0]))]

        except Exception as e:
            toast_msg = f'error reload table: {e}'
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
        global dt_flag_wtm, dt_result_flag, dt_result_user, dt_result_post
        global printer

        try:
            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET print_flag = %s WHERE noantrian = %s"
            print_datetime = str(time.strftime("%d %B %Y %H:%M:%S", time.localtime()))
            sql_val = (dt_flag_print, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            printer.set(align="center", normal_textsize=True)
            printer.image("assets/logo-dishub-print.png")
            printer.ln()
            printer.textln("HASIL UJI TINGKAT PENERUSAN CAHAYA KACA KENDARAAN")
            printer.set(bold=True)
            printer.textln(f"Tanggal: {print_datetime}")
            printer.textln("=======================================")
            printer.set(align="left", normal_textsize=True)
            printer.textln(f"No Antrian: {dt_no_antrian}")
            printer.text(f"No Reg: {dt_no_reg}\t")
            printer.textln(f"No Uji: {dt_no_uji}")
            printer.textln(f"Nama: {dt_nama}")
            printer.textln(f"Jenis Kendaraan: {dt_jenis_kendaraan}")
            printer.textln("  ")
            printer.set(double_height=True, double_width=True)
            printer.text(f"Status:\t")
            printer.set(bold=True)
            printer.textln(f"{dt_flag_wtm}")
            printer.set(bold=False)
            printer.text(f"Nilai:\t")
            printer.set(bold=True)
            printer.textln(f"{str(np.round(dt_result_flag, 2))}")
            printer.set(align="center", normal_textsize=True)     
            printer.textln("  ")
            printer.image("assets/logo-trb-print.png")
            printer.cut()

            self.open_screen_main()

        except Exception as e:
            toast_msg = f'error print data: {e}'
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
        # Window.borderless = False
        # Window.size = 900, 1440
        # Window.size = 450, 720
        # Window.allow_screensaver = True

        Builder.load_file('main.kv')
        return RootScreen()

if __name__ == '__main__':
    FinalVerifierApp().run()
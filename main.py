import os
import sys
import json
import csv
import urllib.request
import sqlite3
import xmltodict
import calendar
# import subprocess

from dateutil.relativedelta import relativedelta
from calendar import monthrange
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QWidget
from ui_MainWindow import Ui_MainWindow


class Error_MessageBox_Window(QWidget):
    def __init__(self, text_error, is_exit=True):
        super().__init__()
        dialog = QMessageBox.critical(self, "Error", text_error, QMessageBox.StandardButton.Ok)
        if dialog == QMessageBox.StandardButton.Ok and is_exit:
            sys.exit()


##################################
# Read_curs
class Read_curs:
    def __init__(self, date_cred, curr_code):
        try:
            file_settings = 'settings_curs_nbu.json'
            if not os.path.isfile(file_settings):
                Error_MessageBox_Window(text_error="File 'settings_curs_nbu.json' not found").show()

            # Opening JSON file
            f = open(file='settings_curs_nbu.json', mode="r", encoding="utf8")
            data = json.loads(f.read())
            self.data_format = data['main']['data_format']
            if self.data_format == 'json':
                self.file_name = data['main']['curs_nbu_json']['file_name']
                self.url = data['main']['curs_nbu_json']['url']
                self.char_curr_code = data['main']['curs_nbu_json']['char_curr_code']
                self.char_curs = data['main']['curs_nbu_json']['char_curs']
                self.char_format_date = data['main']['curs_nbu_json']['char_format_date']
            elif self.data_format == 'xml':
                self.file_name = data['main']['curs_nbu_xml']['file_name']
                self.url = data['main']['curs_nbu_xml']['url']
                self.char_curr_code = data['main']['curs_nbu_xml']['char_curr_code']
                self.char_curs = data['main']['curs_nbu_xml']['char_curs']
                self.char_format_date = data['main']['curs_nbu_xml']['char_format_date']
            else:
                Error_MessageBox_Window(text_error="File 'settings_curs_nbu.json' -> parameter 'data_format' not in "
                                                   "'xml' or 'json'").show()

            # Closing file
            f.close()

            # connect sqlite3
            con = sqlite3.connect("curs.db")
            cursor = con.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS CURS
                            (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,  
                             CURS_DATE INTEGER NOT NULL, 
                             CURR_CODE TEXT NOT NULL,
                             RATE REAL NOT NULL CHECK(RATE > 0),
                             FORC INTEGER NOT NULL CHECK(FORC > 0)
                             )
                        """)
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS UK_CURS ON CURS (CURS_DATE, CURR_CODE)")

            # check curs
            is_request_curs = True
            params = (date_cred.strftime("%Y-%m-%d"), curr_code)
            cursor.execute("SELECT RATE/FORC AS CURS_AMOUNT FROM CURS WHERE CURS_DATE = ? AND CURR_CODE = ?", params)
            rows = cursor.fetchall()
            for row in rows:
                self.curs_amount = float(row[0])
                is_request_curs = False

            if is_request_curs:
                # Read url
                url = self.url.replace("%MDATE%", date_cred.strftime(self.char_format_date)).replace("%CURRCODE%",
                                                                                                     curr_code)
                webURL = urllib.request.urlopen(url)
                data = webURL.read()

                if self.data_format == 'json':
                    JSON_object = json.loads(data.decode('utf-8'))
                    # write data
                    for json_line in JSON_object:
                        params = (date_cred.strftime("%Y-%m-%d"),
                                  json_line[self.char_curr_code],
                                  json_line[self.char_curs],
                                  1)
                        cursor.execute(
                            "INSERT OR IGNORE INTO CURS(curs_date, curr_code, rate, forc) VALUES(?, ?, ?, ?)",
                            params)
                elif self.data_format == 'xml':
                    JSON_object = xmltodict.parse(data.decode('utf-8'))
                    # write data
                    json_line = JSON_object["exchange"]["currency"]
                    params = (date_cred.strftime("%Y-%m-%d"),
                              json_line[self.char_curr_code],
                              json_line[self.char_curs],
                              1)
                    cursor.execute("INSERT OR IGNORE INTO CURS(curs_date, curr_code, rate, forc) VALUES(?, ?, ?, ?)",
                                   params)

                # read new curs
                params = (date_cred.strftime("%Y-%m-%d"), curr_code)
                cursor.execute("SELECT RATE/FORC AS CURS_AMOUNT FROM CURS WHERE CURS_DATE = ? AND CURR_CODE = ?",
                               params)
                rows = cursor.fetchall()
                for row in rows:
                    self.curs_amount = float(row[0])

            con.commit()
            con.close()
        except Exception as err:
            print(err)


##################################
# Read_type_calc
class Read_type_calc:
    def __init__(self):
        try:
            dir_ini = os.getcwd() + "\\ini"
            if not os.path.isdir(dir_ini):
                Error_MessageBox_Window(text_error=dir_ini + " directory not found").show()

            filenames = [fn for fn in os.listdir(dir_ini) if fn.split(".")[-1] in ["json"]]
            self.list_type_calc = []
            self.list_type_calc_file = []
            for idx, file in enumerate(filenames):
                # Save path file
                self.list_type_calc_file.insert(idx, dir_ini + '\\' + file)
                # Opening JSON file
                f = open(file=dir_ini + '\\' + file, mode="r", encoding="utf8")
                data = json.loads(f.read())
                self.list_type_calc.insert(idx, data['primary']['global']['name'])

        except Exception as err:
            print(err)


##################################
# Update_type_calc
class Update_type_calc:
    def __init__(self, type_calc_file):
        try:
            if not os.path.isfile(type_calc_file):
                Error_MessageBox_Window(type_calc_file + " file not found").show()

            # Opening JSON file
            f = open(file=type_calc_file, mode="r", encoding="utf8")
            data = json.loads(f.read())
            self.param_global_name = data['primary']['global']['name']
            self.param_global_type = data['primary']['global']['type']
            self.param_main_proc_stavka = float(data['primary']['main']['proc_stavka'])
            self.param_main_curr_code = data['primary']['main']['curr_code']
            self.param_main_summa = float(data['primary']['main']['summa'])
            self.param_main_curs = float(
                1 if data['primary']['main']['curs'] is None else data['primary']['main'][
                    'curs'])
            self.param_main_perv_vznos_proc = float(
                -1 if data['primary']['main']['perv_vznos_proc'] is None else data['primary']['main'][
                    'perv_vznos_proc'])
            self.param_main_perv_vznos = float(
                -1 if data['primary']['main']['perv_vznos'] is None else data['primary']['main'][
                    'perv_vznos'])
            self.param_main_priv_proc_stavka = float(
                0 if data['primary']['main']['priv_proc_stavka'] is None else data['primary']['main'][
                    'priv_proc_stavka'])
            self.param_main_priv_srok = int(
                0 if data['primary']['main']['priv_srok'] is None else data['primary']['main'][
                    'priv_srok'])
            self.param_main_priv_proc_stavka_2 = float(
                0 if data['primary']['main']['priv_proc_stavka_2'] is None else data['primary']['main'][
                    'priv_proc_stavka_2'])
            self.param_main_priv_srok_2 = int(
                0 if data['primary']['main']['priv_srok_2'] is None else data['primary']['main'][
                    'priv_srok_2'])
            self.param_main_priv_proc_stavka_3 = float(
                0 if data['primary']['main']['priv_proc_stavka_3'] is None else data['primary']['main'][
                    'priv_proc_stavka_3'])
            self.param_main_priv_srok_3 = int(
                0 if data['primary']['main']['priv_srok_3'] is None else data['primary']['main'][
                    'priv_srok_3'])

            self.param_main_srok = int(data['primary']['main']['srok'])
            self.param_main_type_proc = data['primary']['main']['type_proc']
            self.param_main_type_proc_n = data['primary']['main']['type_proc_n']

            self.param_bank_comiss_1 = (data['primary']['dopoln']['bank_comiss_1'],
                                        data['primary']['dopoln']['bank_comiss_1c'],
                                        data['primary']['dopoln']['bank_comiss_1_text'])

            self.param_bank_comiss_2 = (data['primary']['dopoln']['bank_comiss_2'],
                                        data['primary']['dopoln']['bank_comiss_2c'],
                                        data['primary']['dopoln']['bank_comiss_2_text'])

            self.param_stra_comiss_1 = (data['primary']['dopoln']['stra_comiss_1'],
                                        data['primary']['dopoln']['stra_comiss_1c'],
                                        data['primary']['dopoln']['stra_comiss_1_text'])

            self.param_stra_comiss_2 = (data['primary']['dopoln']['stra_comiss_2'],
                                        data['primary']['dopoln']['stra_comiss_2c'],
                                        data['primary']['dopoln']['stra_comiss_2_text'])

            self.param_stra_comiss_3 = (data['primary']['dopoln']['stra_comiss_3'],
                                        data['primary']['dopoln']['stra_comiss_3c'],
                                        data['primary']['dopoln']['stra_comiss_3_text'])

            self.param_nota_comiss_1 = (data['primary']['dopoln']['nota_comiss_1'],
                                        data['primary']['dopoln']['nota_comiss_1c'],
                                        data['primary']['dopoln']['nota_comiss_1_text'])

            self.param_nota_comiss_2 = (data['primary']['dopoln']['nota_comiss_2'],
                                        data['primary']['dopoln']['nota_comiss_2c'],
                                        data['primary']['dopoln']['nota_comiss_2_text'])

            self.param_nota_comiss_3 = (data['primary']['dopoln']['nota_comiss_3'],
                                        data['primary']['dopoln']['nota_comiss_3c'],
                                        data['primary']['dopoln']['nota_comiss_3_text'])

            self.param_nota_comiss_4 = (data['primary']['dopoln']['nota_comiss_4'],
                                        data['primary']['dopoln']['nota_comiss_4c'],
                                        data['primary']['dopoln']['nota_comiss_4_text'])

            self.param_nota_comiss_5 = (data['primary']['dopoln']['nota_comiss_5'],
                                        data['primary']['dopoln']['nota_comiss_5c'],
                                        data['primary']['dopoln']['nota_comiss_5_text'])

            self.param_riel_comiss_1 = (data['primary']['dopoln']['riel_comiss_1'],
                                        data['primary']['dopoln']['riel_comiss_1c'],
                                        data['primary']['dopoln']['riel_comiss_1_text'])

            self.param_riel_comiss_2 = (data['primary']['dopoln']['riel_comiss_2'],
                                        data['primary']['dopoln']['riel_comiss_2c'],
                                        data['primary']['dopoln']['riel_comiss_2_text'])

            self.param_riel_comiss_3 = (data['primary']['dopoln']['riel_comiss_3'],
                                        data['primary']['dopoln']['riel_comiss_3c'],
                                        data['primary']['dopoln']['riel_comiss_3_text'])

            self.param_rasrochka_curs = (data['primary']['rasrochka']['curs'],
                                         data['primary']['rasrochka']['curs_year_0'],
                                         data['primary']['rasrochka']['curs_year_1'],
                                         data['primary']['rasrochka']['curs_year_2'],
                                         data['primary']['rasrochka']['curs_year_3'],
                                         data['primary']['rasrochka']['curs_year_4'],
                                         data['primary']['rasrochka']['coef_otsech'])
        except Exception as err:
            print(err)


##################################
# MainWindow
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.buff_sum_dop_k = None
        self.buff_sum_dop_m = None
        self.buff_sum_dop_y = None
        self.sum_dop_m_count = None
        self._datarow = []
        self._amount_dop_b = None
        self._amount_dop_y = None
        self._amount_dop_k = None
        self._amount_dop_m = None
        self._amount_dop_e = None
        self.sum_dop_y = None
        self.sum_dop_k = None
        self.sum_dop_m = None
        self.sum_dop_e = None
        self.sum_dop_b = None
        self.sum_dop = None
        self._amount_dop = None
        self._comiss_type = None
        self._kvartal = None
        self._riel_comiss_text = None
        self._nota_comiss_text = None
        self._stra_comiss_text = None
        self._bank_comiss_text = None
        self._index_comiss = None
        self.is_exists_perv_vznos = None
        self.is_exists_perv_vznos_proc = None
        self.setupUi(self)

        # begin add connect
        self.srok_kred.valueChanged.connect(self.on_srok_cred_value_changed)
        self.priv_srok_kred.valueChanged.connect(self.on_priv_srok_cred_value_changed)
        self.priv_srok_kred2.valueChanged.connect(self.on_priv_srok_cred2_value_changed)
        self.priv_srok_kred3.valueChanged.connect(self.on_priv_srok_cred3_value_changed)
        self.srok_kred_new.valueChanged.connect(self.on_srok_cred_new_value_changed)

        # init
        self.date_cred.setDateTime(QtCore.QDateTime(QtCore.QDate.currentDate(), QtCore.QTime.currentTime()))

        # read type calc
        tc = Read_type_calc()
        self._list_type_calc_file = tc.list_type_calc_file
        self.type_calc.addItems(tc.list_type_calc)

        # read type calc params
        self.read_type_calc_params(self._list_type_calc_file[self.type_calc.currentIndex()])

        # end add connect
        self.date_cred.dateChanged.connect(self.on_date_cred_changed)
        self.curr_code.currentTextChanged.connect(self.on_curr_code_changed)
        self.summa.valueChanged.connect(self.on_summa_value_changed)
        self.curs.valueChanged.connect(self.on_curs_value_changed)
        self.proc_perv_vznos.valueChanged.connect(self.on_proc_perv_vznos_value_changed)
        self.perv_vznos.valueChanged.connect(self.on_perv_vznos_value_changed)
        self.check_recalc.stateChanged.connect(self.on_check_recalc_state_changed)
        self.type_calc.currentIndexChanged.connect(self.on_type_calc_index_changed)
        self.type_proc.currentTextChanged.connect(self.on_type_proc_value_changed)
        self.button_calc.pressed.connect(self.on_button_calc_clicked)
        self.button_update.clicked.connect(self.on_button_update_clicked)
        self.button_json_file.clicked.connect(self.on_button_json_file_clicked)
        self.button_export_csv.pressed.connect(self.on_button_export_csv_clicked)

    ######################################
    # get index comiss text
    def get_index_comiss_text(self, param_comiss):
        match param_comiss:
            case "BA":
                self._index_comiss = 0
            case "BS":
                self._index_comiss = 1
            case "BF":
                self._index_comiss = 2
            case "EA":
                self._index_comiss = 3
            case "ES":
                self._index_comiss = 4
            case "EF":
                self._index_comiss = 5
            case "MA":
                self._index_comiss = 6
            case "MS":
                self._index_comiss = 7
            case "MF":
                self._index_comiss = 8
            case "MZ":
                self._index_comiss = 9
            case "KA":
                self._index_comiss = 10
            case "KS":
                self._index_comiss = 11
            case "KF":
                self._index_comiss = 12
            case "KZ":
                self._index_comiss = 13
            case "YA":
                self._index_comiss = 14
            case "YS":
                self._index_comiss = 15
            case "YF":
                self._index_comiss = 16
            case "YZ":
                self._index_comiss = 17
            case _:
                self._index_comiss = 0

    ######################################
    # read type calc params
    def read_type_calc_params(self, list_type_calc_file):
        # read type calc params
        update_tc = Update_type_calc(list_type_calc_file)
        #
        self.priv_proc_stavka.setProperty("value", update_tc.param_main_priv_proc_stavka)
        self.priv_srok_kred.setProperty("value", update_tc.param_main_priv_srok)
        self.priv_proc_stavka2.setProperty("value", update_tc.param_main_priv_proc_stavka_2)
        self.priv_srok_kred2.setProperty("value", update_tc.param_main_priv_srok_2)
        self.priv_proc_stavka3.setProperty("value", update_tc.param_main_priv_proc_stavka_2)
        self.priv_srok_kred3.setProperty("value", update_tc.param_main_priv_srok_3)
        #
        self.curs.setProperty("value", update_tc.param_main_curs)
        self.proc_stavka.setProperty("value", update_tc.param_main_proc_stavka)
        self.summa.setProperty("value", update_tc.param_main_summa)
        self.srok_kred.setProperty("value", update_tc.param_main_srok)
        #
        self._bank_comiss_text = "Банк - "
        self.comiss_amount_1.setProperty("value", update_tc.param_bank_comiss_1[0])
        self.comiss_text_1.setText(self._bank_comiss_text + update_tc.param_bank_comiss_1[2])
        self.get_index_comiss_text(update_tc.param_bank_comiss_1[1])
        self.comiss_type_1.setCurrentIndex(self._index_comiss)
        self.comiss_amount_2.setProperty("value", update_tc.param_bank_comiss_2[0])
        self.comiss_text_2.setText(self._bank_comiss_text + update_tc.param_bank_comiss_2[2])
        self.get_index_comiss_text(update_tc.param_bank_comiss_2[1])
        self.comiss_type_2.setCurrentIndex(self._index_comiss)
        #
        self._stra_comiss_text = 'Страхование - '
        self.comiss_amount_3.setProperty("value", update_tc.param_stra_comiss_1[0])
        self.comiss_text_3.setText(self._stra_comiss_text + update_tc.param_stra_comiss_1[2])
        self.get_index_comiss_text(update_tc.param_stra_comiss_1[1])
        self.comiss_type_3.setCurrentIndex(self._index_comiss)
        self.comiss_amount_4.setProperty("value", update_tc.param_stra_comiss_2[0])
        self.comiss_text_4.setText(self._stra_comiss_text + update_tc.param_stra_comiss_2[2])
        self.get_index_comiss_text(update_tc.param_stra_comiss_2[1])
        self.comiss_type_4.setCurrentIndex(self._index_comiss)
        self.comiss_amount_5.setProperty("value", update_tc.param_stra_comiss_3[0])
        self.comiss_text_5.setText(self._stra_comiss_text + update_tc.param_stra_comiss_3[2])
        self.get_index_comiss_text(update_tc.param_stra_comiss_3[1])
        self.comiss_type_5.setCurrentIndex(self._index_comiss)
        #
        self._nota_comiss_text = 'Оформление - '
        self.comiss_amount_6.setProperty("value", update_tc.param_nota_comiss_1[0])
        self.comiss_text_6.setText(self._nota_comiss_text + update_tc.param_nota_comiss_1[2])
        self.get_index_comiss_text(update_tc.param_nota_comiss_1[1])
        self.comiss_type_6.setCurrentIndex(self._index_comiss)
        self.comiss_amount_7.setProperty("value", update_tc.param_nota_comiss_2[0])
        self.comiss_text_7.setText(self._nota_comiss_text + update_tc.param_nota_comiss_2[2])
        self.get_index_comiss_text(update_tc.param_nota_comiss_2[1])
        self.comiss_type_7.setCurrentIndex(self._index_comiss)
        self.comiss_amount_8.setProperty("value", update_tc.param_nota_comiss_3[0])
        self.comiss_text_8.setText(self._nota_comiss_text + update_tc.param_nota_comiss_3[2])
        self.get_index_comiss_text(update_tc.param_nota_comiss_3[1])
        self.comiss_type_8.setCurrentIndex(self._index_comiss)
        self.comiss_amount_9.setProperty("value", update_tc.param_nota_comiss_4[0])
        self.comiss_text_9.setText(self._nota_comiss_text + update_tc.param_nota_comiss_4[2])
        self.get_index_comiss_text(update_tc.param_nota_comiss_4[1])
        self.comiss_type_9.setCurrentIndex(self._index_comiss)
        self.comiss_amount_10.setProperty("value", update_tc.param_nota_comiss_5[0])
        self.comiss_text_10.setText(self._nota_comiss_text + update_tc.param_nota_comiss_5[2])
        self.get_index_comiss_text(update_tc.param_nota_comiss_5[1])
        self.comiss_type_10.setCurrentIndex(self._index_comiss)
        #
        self._riel_comiss_text = 'Прочие - '
        self.comiss_amount_11.setProperty("value", update_tc.param_riel_comiss_1[0])
        self.comiss_text_11.setText(self._riel_comiss_text + update_tc.param_riel_comiss_1[2])
        self.get_index_comiss_text(update_tc.param_riel_comiss_1[1])
        self.comiss_type_11.setCurrentIndex(self._index_comiss)
        self.comiss_amount_12.setProperty("value", update_tc.param_riel_comiss_2[0])
        self.comiss_text_12.setText(self._riel_comiss_text + update_tc.param_riel_comiss_2[2])
        self.get_index_comiss_text(update_tc.param_riel_comiss_2[1])
        self.comiss_type_12.setCurrentIndex(self._index_comiss)
        self.comiss_amount_13.setProperty("value", update_tc.param_riel_comiss_3[0])
        self.comiss_text_13.setText(self._riel_comiss_text + update_tc.param_riel_comiss_3[2])
        self.get_index_comiss_text(update_tc.param_riel_comiss_3[1])
        self.comiss_type_13.setCurrentIndex(self._index_comiss)
        #
        self.curs_start.setProperty("value", update_tc.param_rasrochka_curs[0])
        self.curs_year_0.setProperty("value", update_tc.param_rasrochka_curs[1])
        self.curs_year_1.setProperty("value", update_tc.param_rasrochka_curs[2])
        self.curs_year_2.setProperty("value", update_tc.param_rasrochka_curs[3])
        self.curs_year_3.setProperty("value", update_tc.param_rasrochka_curs[4])
        self.curs_year_4.setProperty("value", update_tc.param_rasrochka_curs[5])
        self.coef_otsech.setProperty("value", update_tc.param_rasrochka_curs[6])
        #
        self.type_annuitet.setCurrentText(update_tc.param_main_type_proc_n)
        self.type_annuitet.setEnabled(False if update_tc.param_main_type_proc_n is None else True)

        if update_tc.param_main_curr_code == "":
            pass
        else:
            self.curr_code.setCurrentText(update_tc.param_main_curr_code)

        if update_tc.param_main_perv_vznos_proc < 0:
            self.is_exists_perv_vznos_proc = False
            self.proc_perv_vznos.setEnabled(False)
        else:
            self.is_exists_perv_vznos_proc = True
            self.proc_perv_vznos.setEnabled(True)
            self.check_recalc.setChecked(False)
            self.proc_perv_vznos.setProperty("value", update_tc.param_main_perv_vznos_proc)

        if update_tc.param_main_perv_vznos < 0:
            self.is_exists_perv_vznos = False
            self.perv_vznos.setEnabled(False)
        else:
            self.is_exists_perv_vznos = True
            self.perv_vznos.setEnabled(True)
            self.check_recalc.setChecked(True)
            self.perv_vznos.setProperty("value", update_tc.param_main_perv_vznos)

        match update_tc.param_main_type_proc:
            case "K":
                self.type_proc.setCurrentText("классика")
            case "A":
                self.type_proc.setCurrentText("аннуитетная")
            case "R":
                self.type_proc.setCurrentText("рассрочка")
            case _:
                self.type_proc.setCurrentText("классика")

        if self.type_proc.currentText() == "классика":
            self.groupBox_rasrochka.setEnabled(False)
            self.priv_proc_stavka.setEnabled(True)
            self.priv_proc_stavka2.setEnabled(True)
            self.priv_proc_stavka3.setEnabled(True)
            self.priv_srok_kred.setEnabled(True)
            self.priv_srok_kred2.setEnabled(True)
            self.priv_srok_kred3.setEnabled(True)
            self.check_recalc_graf.setEnabled(False)
        elif self.type_proc.currentText() == "аннуитетная":
            self.groupBox_rasrochka.setEnabled(False)
            self.priv_proc_stavka.setEnabled(True)
            self.priv_proc_stavka2.setEnabled(False)
            self.priv_proc_stavka3.setEnabled(False)
            self.priv_srok_kred.setEnabled(True)
            self.priv_srok_kred2.setEnabled(False)
            self.priv_srok_kred3.setEnabled(False)
            self.check_recalc_graf.setEnabled(True)
        elif self.type_proc.currentText() == "рассрочка":
            self.groupBox_rasrochka.setEnabled(True)
            self.priv_proc_stavka.setEnabled(False)
            self.priv_proc_stavka2.setEnabled(False)
            self.priv_proc_stavka3.setEnabled(False)
            self.priv_srok_kred.setEnabled(False)
            self.priv_srok_kred2.setEnabled(False)
            self.priv_srok_kred3.setEnabled(False)
            self.check_recalc_graf.setEnabled(False)

        # calc
        if self.is_exists_perv_vznos_proc:
            self.perv_vznos.setProperty("value",
                                        self.proc_perv_vznos.value() * self.summa.value() * self.curs.value() / 100)

        self.summa_ekv.setProperty("value", self.summa.value() * self.curs.value())
        calc_sum_cred = self.summa_ekv.value() - self.perv_vznos.value()
        self.sum_kred.setProperty("value", 0 if calc_sum_cred <= 0 else calc_sum_cred)

        # calc dop
        self.sum_dop = 0
        self.sum_dop_b = 0
        self.sum_dop_e = 0
        self.sum_dop_m = 0
        self.sum_dop_k = 0
        self.sum_dop_y = 0
        m_date_start = self.date_cred.date().toPyDate()
        m_date_end = m_date_start + relativedelta(months=self.srok_kred.value())
        m_date_temp = m_date_start
        while m_date_temp <= m_date_end:
            self.calc_dop(_date=m_date_temp, _date_end=m_date_end)
            m_date_temp = m_date_temp + relativedelta(months=1)

        self.start_itog.setProperty("value", self.sum_dop_b)
        self.end_itog.setProperty("value", self.sum_dop_e)
        self.month_itog.setProperty("value", self.sum_dop_m)
        self.kvart_itog.setProperty("value", self.sum_dop_k)
        self.year_itog.setProperty("value", self.sum_dop_y)
        pereplata = self.sum_dop_b + self.sum_dop_e + self.sum_dop_m + self.sum_dop_k + self.sum_dop_y
        self.pereplata.setProperty("value", pereplata)

        self.paint_table_column()

    ######################################
    # calc params
    def calc_param(self, is_perv_vznos_proc=True):
        if self.is_exists_perv_vznos_proc and is_perv_vznos_proc:
            self.perv_vznos.setProperty("value",
                                        self.proc_perv_vznos.value() * self.summa.value() * self.curs.value() / 100)

        self.summa_ekv.setProperty("value", self.summa.value() * self.curs.value())
        calc_sum_cred = self.summa_ekv.value() - self.perv_vznos.value()
        self.sum_kred.setProperty("value", 0 if calc_sum_cred <= 0 else calc_sum_cred)

    ######################################
    # calc dop
    def calc_dop(self, _date, _sum_ost=0, _date_end=None):
        _amount = self.comiss_amount_1.value()
        _index_dop = self.comiss_type_1.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_2.value()
        _index_dop = self.comiss_type_2.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_3.value()
        _index_dop = self.comiss_type_3.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_4.value()
        _index_dop = self.comiss_type_4.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_5.value()
        _index_dop = self.comiss_type_5.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_6.value()
        _index_dop = self.comiss_type_6.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_7.value()
        _index_dop = self.comiss_type_7.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_8.value()
        _index_dop = self.comiss_type_8.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_9.value()
        _index_dop = self.comiss_type_9.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_10.value()
        _index_dop = self.comiss_type_10.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_11.value()
        _index_dop = self.comiss_type_11.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_12.value()
        _index_dop = self.comiss_type_12.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y
        #
        _amount = self.comiss_amount_13.value()
        _index_dop = self.comiss_type_13.currentIndex()
        self.calc_sum_dop(_index_dop, _date, _amount, _sum_ost, _date_end)
        self.sum_dop += self._amount_dop
        self.sum_dop_b += self._amount_dop_b
        self.sum_dop_e += self._amount_dop_e
        self.sum_dop_m += self._amount_dop_m
        self.sum_dop_k += self._amount_dop_k
        self.sum_dop_y += self._amount_dop_y

    def calc_sum_dop(self, _index_dop, _date, _amount, _sum_ost, _date_end):

        _summa_ekv = self.summa_ekv.value()
        _sum_cred = self.sum_kred.value()
        _date_start = self.date_cred.date().toPyDate()

        if _date_start.strftime('%m') in ('01', '04', '07', '10'):
            self._kvartal = ('01', '04', '07', '10')
        elif _date_start.strftime('%m') in ('02', '05', '08', '11'):
            self._kvartal = ('02', '05', '08', '11')
        elif _date_start.strftime('%m') in ('03', '06', '09', '12'):
            self._kvartal = ('03', '06', '09', '12')

        self._amount_dop = 0
        self._amount_dop_b = 0
        self._amount_dop_e = 0
        self._amount_dop_m = 0
        self._amount_dop_k = 0
        self._amount_dop_y = 0

        match _index_dop:
            case 0:
                self._comiss_type = "BA"  # BA - При выдаче (сумма)
                self._amount_dop = _amount if _date_start == _date else 0
                self._amount_dop_b = self._amount_dop
            case 1:
                self._comiss_type = "BS"  # BS - При выдаче (% с суммы кредита)
                self._amount_dop = (_sum_cred * _amount / 100) if _date_start == _date else 0
                self._amount_dop_b = self._amount_dop
            case 2:
                self._comiss_type = "BF"  # BF - При выдаче (% от стоимости)
                self._amount_dop = (_summa_ekv * _amount / 100) if _date_start == _date else 0
                self._amount_dop_b = self._amount_dop
            case 3:
                self._comiss_type = "EA"  # EA - В конце срока (сумма)
                self._amount_dop = _amount if _date_end == _date else 0
                self._amount_dop_e = self._amount_dop
            case 4:
                self._comiss_type = "ES"  # ES - В конце срока (% с суммы кредита)
                self._amount_dop = (_sum_cred * _amount / 100) if _date_end == _date else 0
                self._amount_dop_e = self._amount_dop
            case 5:
                self._comiss_type = "EF"  # EF - В конце срока (% от стоимости)
                self._amount_dop = (_summa_ekv * _amount / 100) if _date_end == _date else 0
                self._amount_dop_e = self._amount_dop
            case 6:
                self._comiss_type = "MA"  # MA - Eжемесячно (сумма)
                self._amount_dop = 0 if _date_start == _date else _amount
                self._amount_dop_m = self._amount_dop
            case 7:
                self._comiss_type = "MS"  # MS - Eжемесячно (% с суммы кредита)
                self._amount_dop = 0 if _date_start == _date else (_sum_cred * _amount / 100)
                self._amount_dop_m = self._amount_dop
            case 8:
                self._comiss_type = "MF"  # MF - Eжемесячно (% от стоимости)
                self._amount_dop = 0 if _date_start == _date else (_summa_ekv * _amount / 100)
                self._amount_dop_m = self._amount_dop
            case 9:
                self._comiss_type = "MZ"  # MZ - Ежемесячно (% от суммы задолженности)
                self._amount_dop = 0 if _date_start == _date else (_sum_ost * _amount / 100)
                self._amount_dop_m = self._amount_dop
            case 10:
                self._comiss_type = "KA"  # KA - Ежеквартально (сумма)
                self._amount_dop = _amount if _date.strftime('%m') in self._kvartal else 0
                self._amount_dop_k = self._amount_dop
            case 11:
                self._comiss_type = "KS"  # KS - Ежеквартально (% с суммы кредита)
                self._amount_dop = (_sum_cred * _amount / 100) if _date.strftime('%m') in self._kvartal else 0
                self._amount_dop_k = self._amount_dop
            case 12:
                self._comiss_type = "KF"  # KF - Ежеквартально (% от стоимости)
                self._amount_dop = (_summa_ekv * _amount / 100) if _date.strftime('%m') in self._kvartal else 0
                self._amount_dop_k = self._amount_dop
            case 13:
                self._comiss_type = "KZ"  # KZ - Ежеквартально (% от суммы задолженности)
                self._amount_dop = (_sum_ost * _amount / 100) if _date.strftime('%m') in self._kvartal else 0
                self._amount_dop_k = self._amount_dop
            case 14:
                self._comiss_type = "YA"  # YA - Ежегодно (сумма)
                self._amount_dop = _amount if _date_start.strftime('%m') == _date.strftime('%m') else 0
                self._amount_dop_y = self._amount_dop
            case 15:
                self._comiss_type = "YS"  # YS - Ежегодно (% с суммы кредита)
                self._amount_dop = (_sum_cred * _amount / 100) if _date_start.strftime(
                    '%m') == _date.strftime('%m') else 0
                self._amount_dop_y = self._amount_dop
            case 16:
                self._comiss_type = "YF"  # YF - Ежегодно (% от стоимости)
                self._amount_dop = (_summa_ekv * _amount / 100) if _date_start.strftime(
                    '%m') == _date.strftime('%m') else 0
                self._amount_dop_y = self._amount_dop
            case 17:
                self._comiss_type = "YZ"  # YZ - Ежегодно (% от суммы задолженности)
                self._amount_dop = (_sum_ost * _amount / 100) if _date_start.strftime(
                    '%m') == _date.strftime('%m') else 0
                self._amount_dop_y = self._amount_dop
            case _:
                self._comiss_type = "BA"
                self._amount_dop = _amount if _date_start == _date else 0
                self._amount_dop_b = self._amount_dop

    ######################################
    # paint table column
    def paint_table_column(self, datarow=None):
        if datarow is None:
            datarow = []
        m_datacol = ["Дата", "Долг", "Плат.%", "Плат.тело", "Переплата", "Плат.доп.", "Итого"]

        self.tableWidget.setRowCount(len(datarow))
        self.tableWidget.setColumnCount(len(m_datacol))
        self.tableWidget.setHorizontalHeaderLabels(m_datacol)
        self.tableWidget.setColumnWidth(0, 82)
        self.tableWidget.setColumnWidth(1, 90)
        self.tableWidget.setColumnWidth(2, 90)
        self.tableWidget.setColumnWidth(3, 90)
        self.tableWidget.setColumnWidth(4, 90)
        self.tableWidget.setColumnWidth(5, 90)
        self.tableWidget.setColumnWidth(6, 90)

        for row, data_row in enumerate(datarow):
            for col, data_header in enumerate(m_datacol):
                color = data_row[7]
                item = QTableWidgetItem(data_row[col])
                item.setBackground(color)
                if col == 0:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
                else:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight)
                self.tableWidget.setItem(row, col, item)
            self.tableWidget.setRowHeight(row, 15)

    ######################################
    # calc table row
    def calc_table_row(self):
        self._datarow = []

        m_sum_kred = self.sum_kred.value()
        m_proc_stavka = self.proc_stavka.value()
        m_priv_proc_stavka = self.priv_proc_stavka.value()
        m_priv_proc_stavka2 = self.priv_proc_stavka2.value()
        m_priv_proc_stavka3 = self.priv_proc_stavka3.value()
        m_srok = self.srok_kred.value()
        m_priv_srok = self.priv_srok_kred.value()
        m_priv_srok2 = self.priv_srok_kred2.value()
        m_priv_srok3 = self.priv_srok_kred3.value()
        m_type_proc = self.type_proc.currentText()
        m_type_annuitet = self.type_annuitet.currentText()
        m_coef_otsech = self.coef_otsech.value()

        # start itog
        self.sum_dop_b = 0
        self.calc_dop(self.date_cred.date().toPyDate())
        m_sum_one = self.sum_dop_b
        self.start_itog.setProperty("value", m_sum_one)
        # buff itog
        self.buff_sum_dop_y = 0
        self.buff_sum_dop_k = 0
        self.buff_sum_dop_m = 0

        if m_sum_kred == 0:
            Error_MessageBox_Window("Расчет и вывод графика невозможен !!! Не расчитана СУММА КРЕДИТА!!!",
                                    is_exit=False).show()
            return

        # Аннуитет
        if m_type_proc == "аннуитетная":
            # расчет кредитного портфеля
            # Расчитываем процентную ставку выраженную в долях
            match m_type_annuitet:
                case "30/360":
                    zc = 30
                    zn = 360
                case "факт/360":
                    zc = monthrange(self.date_cred.date().toPyDate().year, self.date_cred.date().toPyDate().month)[1]
                    zn = 360
                case "факт/факт":
                    zc = monthrange(self.date_cred.date().toPyDate().year, self.date_cred.date().toPyDate().month)[1]
                    zn = 365 + calendar.isleap(self.date_cred.date().toPyDate().year)
                case _:
                    zc = 30
                    zn = 360

            # Льготный период
            m_priv_proc_stavka = (m_priv_proc_stavka * 0.01 / zn) * zc
            m_proc_stavka = (m_proc_stavka * 0.01 / zn) * zc

            # Сумма аннуитетного платежа
            if m_priv_proc_stavka == 0:
                annuitet_priv = m_sum_kred / m_srok
            else:
                annuitet_priv = (m_priv_proc_stavka / (1.00 - (1.00 + m_priv_proc_stavka ** -m_srok))) * m_sum_kred

            # Переплата по кредиту
            sum_pereplata = 0
            m_sum_plat = self.sum_plat.value()
            summ_calc_pereplata = m_sum_kred
            summ_itog_pereplata = 0
            summ = m_sum_kred
            d_date = self.date_cred.date().toPyDate()
            summ_dop = 0
            summ_calc_pro = 0
            summ_plat = 0
            srok_new = 0

            annuitet = annuitet_priv
            m_proc_stavka_buff = m_priv_proc_stavka
            summ_pro = m_sum_kred * m_proc_stavka_buff

            i = 1
            while i <= m_srok:
                # пересчет аннуитета (без пересчета)
                if i == m_priv_srok + 1 and not self.check_recalc_graf.isChecked():
                    m_proc_stavka_buff = m_proc_stavka
                    if m_proc_stavka_buff == 0:
                        annuitet = summ / (m_srok - m_priv_srok)
                    else:
                        annuitet = (m_proc_stavka_buff /
                                    (1.00 - (1.00 + m_proc_stavka_buff) ** -(m_srok - m_priv_srok))) * summ
                    summ_pro = summ * m_proc_stavka_buff

                # расчет аннуитета (с пересчетом)
                if self.check_recalc_graf.isChecked():
                    if i <= m_priv_srok:
                        m_proc_stavka_buff = m_priv_proc_stavka
                    else:
                        m_proc_stavka_buff = m_proc_stavka

                    if m_proc_stavka_buff == 0:
                        annuitet = summ / (m_srok - i + 1)
                    else:
                        annuitet = (m_proc_stavka_buff /
                                    (1.00 - (1.00 + m_proc_stavka_buff) ** -(m_srok - i + 1))) * summ
                    summ_pro = summ * m_proc_stavka_buff

                if m_sum_plat > annuitet:
                    sum_pereplata = m_sum_plat - annuitet

                if (int(d_date.strftime("%Y"))) % 2 == 0:
                    mTColorType = QColor(255, 228, 225)  # MistyRose
                else:
                    mTColorType = QColor(240, 248, 255)  # AliceBlue

                # корректируем последний этап переплаты
                if (summ_calc_pereplata - annuitet - sum_pereplata + m_proc_stavka_buff * summ) < 0 < m_sum_plat:
                    sum_pereplata = m_sum_kred - summ_itog_pereplata - summ_plat - (annuitet - summ_pro)

                # учет ежегодных
                # year itog
                self.sum_dop_y = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_y = self.buff_sum_dop_y + self.sum_dop_y
                m_sum_year = self.sum_dop_y
                self.year_itog.setProperty("value", self.buff_sum_dop_y)

                # учет квартальных
                # kvartal itog
                self.sum_dop_k = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_k = self.buff_sum_dop_k + self.sum_dop_k
                m_sum_kvartal = self.sum_dop_k
                self.kvart_itog.setProperty("value", self.buff_sum_dop_k)

                # учет ежемесяных
                # month itog
                self.sum_dop_m = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_m = self.buff_sum_dop_m + self.sum_dop_m
                m_sum_month = self.sum_dop_m
                self.month_itog.setProperty("value", self.buff_sum_dop_m)

                # добавляем строку
                self._datarow.insert(i - 1,
                                     (d_date.strftime("%Y.%m"),
                                      "{:.2f}".format(summ),
                                      "{:.2f}".format(summ_pro),
                                      "{:.2f}".format((annuitet - summ_pro)),
                                      "{:.2f}".format(sum_pereplata),
                                      "{:.2f}".format((m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal)),
                                      "{:.2f}".format((annuitet + m_sum_one + m_sum_year +
                                                       m_sum_month + m_sum_kvartal + sum_pereplata)),
                                      mTColorType))
                # +1 месяц
                d_date = d_date + relativedelta(months=1)
                summ_plat += annuitet - summ_pro
                summ_calc_pro += summ_pro
                summ_itog_pereplata += sum_pereplata
                srok_new += 1
                #
                if not self.check_recalc_graf.isChecked():
                    summ = summ - annuitet + m_proc_stavka_buff * summ
                else:
                    summ = summ - annuitet + m_proc_stavka_buff * summ - sum_pereplata

                summ_pro = summ * m_proc_stavka_buff
                summ_dop = summ_dop + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal
                m_sum_one = 0
                if summ < 0:
                    break

                # с учетом переплаты
                summ_calc_pereplata = summ_calc_pereplata - annuitet - sum_pereplata + m_proc_stavka_buff * summ
                if summ_calc_pereplata < 0:
                    break
                i += 1

            # новый срок
            self.srok_kred_new.setProperty("value", srok_new)
            # int itog
            self.int_itog.setProperty("value", summ_calc_pro)

            # учет в конце срока
            # end itog
            self.sum_dop_e = 0
            self.calc_dop(d_date, _sum_ost=0, _date_end=d_date)
            m_sum_end = self.sum_dop_e
            self.end_itog.setProperty("value", m_sum_end)
            summ_dop += m_sum_end

            # добавляем
            if m_sum_end > 0:
                i_end = len(self._datarow) - 1
                self._datarow[i_end] = (self._datarow[i_end][0],
                                        self._datarow[i_end][1],
                                        self._datarow[i_end][2],
                                        self._datarow[i_end][3],
                                        self._datarow[i_end][4],
                                        "{:.2f}".format(float(self._datarow[i_end][5]) + m_sum_end),
                                        "{:.2f}".format(float(self._datarow[i_end][6]) + m_sum_end),
                                        self._datarow[i_end][7])

            # Итого
            mTColorType = QColor(144, 238, 144)  # LightGreen
            self._datarow.insert(i,
                                 ("Итого:",
                                  None,
                                  "{:.2f}".format(summ_calc_pro),
                                  "{:.2f}".format(summ_plat),
                                  "{:.2f}".format(summ_itog_pereplata),
                                  "{:.2f}".format(summ_dop),
                                  "{:.2f}".format((summ_calc_pro + summ_plat + summ_itog_pereplata + summ_dop)),
                                  mTColorType))
            # Переплата
            mTColorType = QColor(173, 216, 230)  # LightBlue
            self._datarow.insert(i + 1,
                                 ("Переплата:",
                                  None,
                                  None,
                                  None,
                                  None,
                                  None,
                                  "{:.2f}".format((summ_calc_pro + summ_dop)),
                                  mTColorType))
            self.pereplata.setProperty("value", (summ_calc_pro + summ_dop))

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Стандартный
        elif m_type_proc == "классика":
            summ = m_sum_kred
            summ_graf = m_sum_kred
            n_pr = 0
            n_ob = 0
            n_cred = 0
            n_perepl = 0
            summ_dop = 0
            m_sum_plat = self.sum_plat.value()
            mass_param = []
            sum_pereplata = 0

            # платежи кредит
            d_date = self.date_cred.date().toPyDate()
            i = 1
            while i <= m_srok:
                match m_type_annuitet:
                    case "30/360":
                        zc = 30
                        zn = 360
                    case "факт/360":
                        zc = monthrange(d_date.year, d_date.month)[1]
                        zn = 360
                    case "факт/факт":
                        zc = monthrange(d_date.year, d_date.month)[1]
                        zn = 365 + calendar.isleap(d_date.year)
                    case _:
                        zc = 30
                        zn = 360

                # льготная
                if i <= m_priv_srok3:
                    pr = summ_graf * m_priv_proc_stavka3 * (zc / zn) / 100
                elif i <= (m_priv_srok3 + m_priv_srok2):
                    pr = summ_graf * m_priv_proc_stavka2 * (zc / zn) / 100
                elif i <= (m_priv_srok3 + m_priv_srok2 + m_priv_srok):
                    pr = summ_graf * m_priv_proc_stavka * (zc / zn) / 100
                # обычная
                else:
                    pr = summ_graf * m_proc_stavka * (zc / zn) / 100

                # учет ежегодных
                # year itog
                self.sum_dop_y = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_y = self.buff_sum_dop_y + self.sum_dop_y
                m_sum_year = self.sum_dop_y
                self.year_itog.setProperty("value", self.buff_sum_dop_y)

                # учет квартальных
                # kvartal itog
                self.sum_dop_k = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_k = self.buff_sum_dop_k + self.sum_dop_k
                m_sum_kvartal = self.sum_dop_k
                self.kvart_itog.setProperty("value", self.buff_sum_dop_k)

                # учет ежемесяных
                # month itog
                self.sum_dop_m = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_m = self.buff_sum_dop_m + self.sum_dop_m
                m_sum_month = self.sum_dop_m
                self.month_itog.setProperty("value", self.buff_sum_dop_m)

                # учет переплаты
                calc_sum_cred = m_sum_kred / m_srok
                sum_itog = round(calc_sum_cred + pr + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal, 2)

                mass_param.insert(i - 1,
                                  (d_date.strftime("%Y.%m"),
                                   round(summ, 2),
                                   round(pr, 2),
                                   round(calc_sum_cred, 2),
                                   round(m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal, 2),
                                   0,
                                   0))

                if m_sum_plat > round(calc_sum_cred + pr, 2):
                    # переплата
                    sum_pereplata = m_sum_plat - round(calc_sum_cred + pr, 2)
                    mass_param[i - 1] = (mass_param[i - 1][0],
                                         mass_param[i - 1][1],
                                         mass_param[i - 1][2],
                                         mass_param[i - 1][3],
                                         mass_param[i - 1][4],
                                         mass_param[i - 1][5],
                                         sum_pereplata)
                    # если последний платеж, корректируем переплату
                    if summ - (m_sum_plat - round(pr, 2)) <= 0:
                        sum_pereplata = 0
                        calc_sum_cred = summ
                        mass_param[i - 1] = (mass_param[i - 1][0],
                                             mass_param[i - 1][1],
                                             mass_param[i - 1][2],
                                             calc_sum_cred,
                                             mass_param[i - 1][4],
                                             mass_param[i - 1][5],
                                             sum_pereplata)
                        # пересчет %
                        match m_type_annuitet:
                            case "30/360":
                                zc = 30
                                zn = 360
                            case "факт/360":
                                zc = monthrange(d_date.year, d_date.month)[1]
                                zn = 360
                            case "факт/факт":
                                zc = monthrange(d_date.year, d_date.month)[1]
                                zn = 365 + calendar.isleap(d_date.year)
                            case _:
                                zc = 30
                                zn = 360

                        # льготная
                        if i <= m_priv_srok3:
                            pr = summ * m_priv_proc_stavka3 * (zc / zn) / 100
                        elif i <= (m_priv_srok3 + m_priv_srok2):
                            pr = summ * m_priv_proc_stavka2 * (zc / zn) / 100
                        elif i <= (m_priv_srok3 + m_priv_srok2 + m_priv_srok):
                            pr = summ * m_priv_proc_stavka * (zc / zn) / 100
                        # обычная
                        else:
                            pr = summ * m_proc_stavka * (zc / zn) / 100

                        mass_param[i - 1] = (mass_param[i - 1][0],
                                             mass_param[i - 1][1],
                                             round(pr, 2),
                                             mass_param[i - 1][3],
                                             mass_param[i - 1][4],
                                             mass_param[i - 1][5],
                                             mass_param[i - 1][6])

                        sum_itog = round(calc_sum_cred + pr + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal, 2)
                        #########################################################################
                    summ -= (m_sum_plat - round(pr, 2))
                else:
                    summ -= round(calc_sum_cred, 2)

                mass_param[i - 1] = (mass_param[i - 1][0],
                                     mass_param[i - 1][1],
                                     mass_param[i - 1][2],
                                     mass_param[i - 1][3],
                                     mass_param[i - 1][4],
                                     sum_itog + sum_pereplata,
                                     mass_param[i - 1][6])

                summ_graf -= round(calc_sum_cred, 2)
                # +1 месяц
                d_date = d_date + relativedelta(months=1)
                n_pr += pr
                n_ob = n_ob + calc_sum_cred + pr + m_sum_one + sum_pereplata + m_sum_year + m_sum_month + m_sum_kvartal
                n_cred += calc_sum_cred
                n_perepl += sum_pereplata
                summ_dop = summ_dop + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal
                m_sum_one = 0
                if summ < 0:
                    break
                i += 1

            #
            srok_new = 0
            i = 1
            while i <= len(mass_param):

                if int(mass_param[i - 1][0][0:4]) % 2 == 0:
                    mTColorType = QColor(255, 228, 225)  # MistyRose
                else:
                    mTColorType = QColor(240, 248, 255)  # AliceBlue

                # добавляем строку
                self._datarow.insert(i - 1,
                                     (mass_param[i - 1][0],
                                      "{:.2f}".format(float(mass_param[i - 1][1])),
                                      "{:.2f}".format(float(mass_param[i - 1][2])),
                                      "{:.2f}".format(float(mass_param[i - 1][3])),
                                      "{:.2f}".format(float(mass_param[i - 1][6])),
                                      "{:.2f}".format(float(mass_param[i - 1][4])),
                                      "{:.2f}".format(float(mass_param[i - 1][5])),
                                      mTColorType))
                srok_new += 1
                i += 1

            # новый срок
            self.srok_kred_new.setProperty("value", srok_new)
            # int itog
            self.int_itog.setProperty("value", n_pr)

            # учет в конце срока
            # end itog
            self.sum_dop_e = 0
            self.calc_dop(d_date, _sum_ost=0, _date_end=d_date)
            m_sum_end = self.sum_dop_e
            self.end_itog.setProperty("value", m_sum_end)
            summ_dop += m_sum_end

            # добавляем
            if m_sum_end > 0:
                i_end = len(self._datarow) - 1
                self._datarow[i_end] = (self._datarow[i_end][0],
                                        self._datarow[i_end][1],
                                        self._datarow[i_end][2],
                                        self._datarow[i_end][3],
                                        self._datarow[i_end][4],
                                        "{:.2f}".format(float(self._datarow[i_end][5]) + m_sum_end),
                                        "{:.2f}".format(float(self._datarow[i_end][6]) + m_sum_end),
                                        self._datarow[i_end][7])

            # Итого
            mTColorType = QColor(144, 238, 144)  # LightGreen
            self._datarow.insert(i,
                                 ("Итого:",
                                  None,
                                  "{:.2f}".format(n_pr),
                                  "{:.2f}".format(n_cred),
                                  "{:.2f}".format(n_perepl),
                                  "{:.2f}".format(summ_dop),
                                  "{:.2f}".format(n_ob + m_sum_end),
                                  mTColorType))
            # Переплата
            mTColorType = QColor(173, 216, 230)  # LightBlue
            self._datarow.insert(i + 1,
                                 ("Переплата:",
                                  None,
                                  None,
                                  None,
                                  None,
                                  None,
                                  "{:.2f}".format(round(n_pr + summ_dop, 2)),
                                  mTColorType))
            self.pereplata.setProperty("value", (n_pr + summ_dop))
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Рассрочка
        elif m_type_proc == "рассрочка":
            summ = m_sum_kred
            summ_graf = m_sum_kred
            n_pr = 0
            n_ob = 0
            n_cred = 0
            n_perepl = 0
            summ_dop = 0
            m_sum_plat = self.sum_plat.value()
            mass_param = []
            sum_pereplata = 0
            m_curs_start = self.curs_start.value()
            m_curs_year_0 = self.curs_year_0.value()
            m_curs_year_1 = self.curs_year_1.value()
            m_curs_year_2 = self.curs_year_2.value()
            m_curs_year_3 = self.curs_year_3.value()
            m_curs_year_4 = self.curs_year_4.value()

            # платежи кредит
            d_date = self.date_cred.date().toPyDate()
            d_date_etalon = d_date
            i = 1
            while i <= m_srok:
                # начальный год
                if int(d_date.year) == int(d_date_etalon.year):
                    nk = m_curs_year_0 / m_curs_start
                elif int(d_date.year) == int(d_date_etalon.year) + 1:
                    nk = m_curs_year_1 / m_curs_start
                elif int(d_date.year) == int(d_date_etalon.year) + 2:
                    nk = m_curs_year_2 / m_curs_start
                elif int(d_date.year) == int(d_date_etalon.year) + 3:
                    nk = m_curs_year_3 / m_curs_start
                elif int(d_date.year) == (int(d_date_etalon.year) + 4) or \
                        int(d_date.year) > int(d_date_etalon.year) + 4:
                    nk = m_curs_year_4 / m_curs_start
                else:
                    nk = 0

                if nk <= m_coef_otsech:
                    nk = 1
                pr = (nk - 1) * (m_sum_kred / m_srok)

                # учет ежегодных
                # year itog
                self.sum_dop_y = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_y = self.buff_sum_dop_y + self.sum_dop_y
                m_sum_year = self.sum_dop_y
                self.year_itog.setProperty("value", self.buff_sum_dop_y)

                # учет квартальных
                # kvartal itog
                self.sum_dop_k = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_k = self.buff_sum_dop_k + self.sum_dop_k
                m_sum_kvartal = self.sum_dop_k
                self.kvart_itog.setProperty("value", self.buff_sum_dop_k)

                # учет ежемесяных
                # month itog
                self.sum_dop_m = 0
                self.calc_dop(d_date, _sum_ost=summ)
                self.buff_sum_dop_m = self.buff_sum_dop_m + self.sum_dop_m
                m_sum_month = self.sum_dop_m
                self.month_itog.setProperty("value", self.buff_sum_dop_m)

                calc_sum_cred = m_sum_kred / m_srok
                sum_itog = round(calc_sum_cred + pr + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal, 2)

                mass_param.insert(i - 1,
                                  (d_date.strftime("%Y.%m"),
                                   round(summ, 2),
                                   round(pr, 2),
                                   round(calc_sum_cred, 2),
                                   round(m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal, 2),
                                   0,
                                   0))

                if m_sum_plat > round(calc_sum_cred + pr, 2):
                    # переплата
                    sum_pereplata = m_sum_plat - round(calc_sum_cred + pr, 2)
                    mass_param[i - 1] = (mass_param[i - 1][0],
                                         mass_param[i - 1][1],
                                         mass_param[i - 1][2],
                                         mass_param[i - 1][3],
                                         mass_param[i - 1][4],
                                         mass_param[i - 1][5],
                                         sum_pereplata)
                    # если последний платеж, корректируем переплату
                    if summ - (m_sum_plat - round(pr, 2)) <= 0:
                        sum_pereplata = 0
                        calc_sum_cred = summ
                        mass_param[i - 1] = (mass_param[i - 1][0],
                                             mass_param[i - 1][1],
                                             mass_param[i - 1][2],
                                             calc_sum_cred,
                                             mass_param[i - 1][4],
                                             mass_param[i - 1][5],
                                             sum_pereplata)
                        # пересчет %
                        # начальный год
                        if int(d_date.year) == int(d_date_etalon.year):
                            nk = m_curs_year_0 / m_curs_start
                        elif int(d_date.year) == int(d_date_etalon.year) + 1:
                            nk = m_curs_year_1 / m_curs_start
                        elif int(d_date.year) == int(d_date_etalon.year) + 2:
                            nk = m_curs_year_2 / m_curs_start
                        elif int(d_date.year) == int(d_date_etalon.year) + 3:
                            nk = m_curs_year_3 / m_curs_start
                        elif int(d_date.year) == (int(d_date_etalon.year) + 4) or int(d_date.year) > int(
                                d_date_etalon.year) + 4:
                            nk = m_curs_year_4 / m_curs_start
                        else:
                            nk = 0

                        if nk <= m_coef_otsech:
                            nk = 1
                        pr = (nk - 1) * calc_sum_cred

                        mass_param[i - 1] = (mass_param[i - 1][0],
                                             mass_param[i - 1][1],
                                             round(pr, 2),
                                             mass_param[i - 1][3],
                                             mass_param[i - 1][4],
                                             mass_param[i - 1][5],
                                             mass_param[i - 1][6])

                        sum_itog = round(calc_sum_cred + pr + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal, 2)
                        #########################################################

                    summ -= (m_sum_plat - round(pr, 2))
                else:
                    summ -= round(calc_sum_cred, 2)

                mass_param[i - 1] = (mass_param[i - 1][0],
                                     mass_param[i - 1][1],
                                     mass_param[i - 1][2],
                                     mass_param[i - 1][3],
                                     mass_param[i - 1][4],
                                     sum_itog + sum_pereplata,
                                     mass_param[i - 1][6])

                summ_graf -= round(calc_sum_cred, 2)
                # +1 месяц
                d_date = d_date + relativedelta(months=1)
                n_pr += pr
                n_ob = n_ob + calc_sum_cred + pr + m_sum_one + sum_pereplata + m_sum_year + m_sum_month + m_sum_kvartal
                n_cred += calc_sum_cred
                n_perepl += sum_pereplata
                summ_dop = summ_dop + m_sum_one + m_sum_year + m_sum_month + m_sum_kvartal
                m_sum_one = 0
                if summ < 0:
                    break
                i += 1

            #
            srok_new = 0
            i = 1
            while i <= len(mass_param):

                if int(mass_param[i - 1][0][0:4]) % 2 == 0:
                    mTColorType = QColor(255, 228, 225)  # MistyRose
                else:
                    mTColorType = QColor(240, 248, 255)  # AliceBlue

                # добавляем строку
                self._datarow.insert(i - 1,
                                     (mass_param[i - 1][0],
                                      "{:.2f}".format(float(mass_param[i - 1][1])),
                                      "{:.2f}".format(float(mass_param[i - 1][2])),
                                      "{:.2f}".format(float(mass_param[i - 1][3])),
                                      "{:.2f}".format(float(mass_param[i - 1][6])),
                                      "{:.2f}".format(float(mass_param[i - 1][4])),
                                      "{:.2f}".format(float(mass_param[i - 1][5])),
                                      mTColorType))
                srok_new += 1
                i += 1

            # новый срок
            self.srok_kred_new.setProperty("value", srok_new)
            # int itog
            self.int_itog.setProperty("value", n_pr)

            # учет в конце срока
            # end itog
            self.sum_dop_e = 0
            self.calc_dop(d_date, _sum_ost=0, _date_end=d_date)
            m_sum_end = self.sum_dop_e
            self.end_itog.setProperty("value", m_sum_end)
            summ_dop += m_sum_end

            # добавляем
            if m_sum_end > 0:
                i_end = len(self._datarow) - 1
                self._datarow[i_end] = (self._datarow[i_end][0],
                                        self._datarow[i_end][1],
                                        self._datarow[i_end][2],
                                        self._datarow[i_end][3],
                                        self._datarow[i_end][4],
                                        "{:.2f}".format(float(self._datarow[i_end][5]) + m_sum_end),
                                        "{:.2f}".format(float(self._datarow[i_end][6]) + m_sum_end),
                                        self._datarow[i_end][7])

            # Итого
            mTColorType = QColor(144, 238, 144)  # LightGreen
            self._datarow.insert(i,
                                 ("Итого:",
                                  None,
                                  "{:.2f}".format(n_pr),
                                  "{:.2f}".format(n_cred),
                                  "{:.2f}".format(n_perepl),
                                  "{:.2f}".format(summ_dop),
                                  "{:.2f}".format(n_ob + m_sum_end),
                                  mTColorType))
            # Переплата
            mTColorType = QColor(173, 216, 230)  # LightBlue
            self._datarow.insert(i + 1,
                                 ("Переплата:",
                                  None,
                                  None,
                                  None,
                                  None,
                                  None,
                                  "{:.2f}".format(round(n_pr + summ_dop, 2)),
                                  mTColorType))
            self.pereplata.setProperty("value", (n_pr + summ_dop))

    ######################################
    # event - date_cred - dateChanged
    def on_date_cred_changed(self, value):
        # curs
        if self.curr_code.currentText() == "UAH":
            self.curs.setProperty("value", 1.0)
            self.curs.setEnabled(False)
        else:
            # Read curs
            p = Read_curs(value.toPyDate(), self.curr_code.currentText())
            self.curs.setProperty("value", p.curs_amount)
            self.curs.setEnabled(True)

    ######################################
    # event - curr_code - currentTextChanged
    def on_curr_code_changed(self, value):
        # curs
        if value == "UAH":
            self.curs.setProperty("value", 1.0)
            self.curs.setEnabled(False)
        else:
            # Read curs
            p = Read_curs(self.date_cred.date().toPyDate(), value)
            self.curs.setProperty("value", p.curs_amount)
            self.curs.setEnabled(True)

    ######################################
    # event - summa - valueChanged
    def on_summa_value_changed(self):
        self.calc_param()

    ######################################
    # event - curs - valueChanged
    def on_curs_value_changed(self):
        self.calc_param()

    ######################################
    # event - proc_perv_vznos - valueChanged
    def on_proc_perv_vznos_value_changed(self):
        self.calc_param()

    ######################################
    # event - perv_vznos - valueChanged
    def on_perv_vznos_value_changed(self):
        self.calc_param(is_perv_vznos_proc=False)

    ######################################
    # event - check_recalc - stateChanged
    def on_check_recalc_state_changed(self, value):
        if value:
            self.is_exists_perv_vznos_proc = False
            self.proc_perv_vznos.setEnabled(False)
            self.is_exists_perv_vznos = True
            self.perv_vznos.setEnabled(True)
        else:
            self.is_exists_perv_vznos_proc = True
            self.proc_perv_vznos.setEnabled(True)
            self.is_exists_perv_vznos = False
            self.perv_vznos.setEnabled(False)

        self.proc_perv_vznos.setProperty("value", 0)
        self.perv_vznos.setProperty("value", 0)

        # calc
        if self.is_exists_perv_vznos_proc:
            self.perv_vznos.setProperty("value",
                                        self.proc_perv_vznos.value() * self.summa.value() * self.curs.value() / 100)

        self.summa_ekv.setProperty("value", self.summa.value() * self.curs.value())
        calc_sum_cred = self.summa_ekv.value() - self.perv_vznos.value()
        self.sum_kred.setProperty("value", 0 if calc_sum_cred <= 0 else calc_sum_cred)

    ######################################
    # event - srok_cred - valueChanged
    def on_srok_cred_value_changed(self):
        self.srok_kred_year.setProperty("value", self.srok_kred.value() / 12)

    ######################################
    # event - priv_srok_cred - valueChanged
    def on_priv_srok_cred_value_changed(self):
        self.priv_srok_kred_year.setProperty("value", self.priv_srok_kred.value() / 12)

    ######################################
    # event - priv_srok_cred2 - valueChanged
    def on_priv_srok_cred2_value_changed(self):
        self.priv_srok_kred_year2.setProperty("value", self.priv_srok_kred2.value() / 12)

    ######################################
    # event - priv_srok_cred3 - valueChanged
    def on_priv_srok_cred3_value_changed(self):
        self.priv_srok_kred_year3.setProperty("value", self.priv_srok_kred3.value() / 12)

    ######################################
    # event - srok_cred_new - valueChanged
    def on_srok_cred_new_value_changed(self):
        self.srok_kred_year_new.setProperty("value", self.srok_kred_new.value() / 12)

    ######################################
    # event - type_calc - currentIndexChanged
    def on_type_calc_index_changed(self, value):
        self.read_type_calc_params(self._list_type_calc_file[value])

    ######################################
    # event - type_proc - currentTextChanged
    def on_type_proc_value_changed(self, value):
        match value:
            case "классика":
                self.type_annuitet.setEnabled(True)
                self.type_annuitet.setCurrentText("30/360"
                                                  if self.type_annuitet.currentText() == ""
                                                  else self.type_annuitet.currentText())
                self.groupBox_rasrochka.setEnabled(False)
                self.priv_proc_stavka.setEnabled(True)
                self.priv_proc_stavka2.setEnabled(True)
                self.priv_proc_stavka3.setEnabled(True)
                self.priv_srok_kred.setEnabled(True)
                self.priv_srok_kred2.setEnabled(True)
                self.priv_srok_kred3.setEnabled(True)
                self.check_recalc_graf.setEnabled(False)
            case "аннуитетная":
                self.type_annuitet.setEnabled(True)
                self.type_annuitet.setCurrentText("30/360"
                                                  if self.type_annuitet.currentText() == ""
                                                  else self.type_annuitet.currentText())
                self.groupBox_rasrochka.setEnabled(False)
                self.priv_proc_stavka.setEnabled(True)
                self.priv_proc_stavka2.setEnabled(False)
                self.priv_proc_stavka3.setEnabled(False)
                self.priv_srok_kred.setEnabled(True)
                self.priv_srok_kred2.setEnabled(False)
                self.priv_srok_kred3.setEnabled(False)
                self.check_recalc_graf.setEnabled(True)
            case "рассрочка":
                self.type_annuitet.setEnabled(False)
                self.type_annuitet.setCurrentText("")
                self.groupBox_rasrochka.setEnabled(True)
                self.priv_proc_stavka.setEnabled(False)
                self.priv_proc_stavka2.setEnabled(False)
                self.priv_proc_stavka3.setEnabled(False)
                self.priv_srok_kred.setEnabled(False)
                self.priv_srok_kred2.setEnabled(False)
                self.priv_srok_kred3.setEnabled(False)
                self.check_recalc_graf.setEnabled(False)

    ######################################
    # event - button_calc - Clicked
    def on_button_calc_clicked(self):
        self.calc_table_row()
        self.paint_table_column(datarow=self._datarow)

    ######################################
    # event - button_update - Clicked
    def on_button_update_clicked(self):
        # read type calc params
        self.read_type_calc_params(self._list_type_calc_file[self.type_calc.currentIndex()])

    ######################################
    # event - button_json_file - Clicked
    def on_button_json_file_clicked(self):
        # subprocess.call(['notepad.exe', self._list_type_calc_file[self.type_calc.currentIndex()]])
        os.startfile(self._list_type_calc_file[self.type_calc.currentIndex()])

    ######################################
    # event - button_export_csv - Clicked
    def on_button_export_csv_clicked(self):
        path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if ok:
            columns = range(self.tableWidget.columnCount())
            header = [self.tableWidget.horizontalHeaderItem(column).text()
                      for column in columns]
            with open(path, 'w') as csvfile:
                writer = csv.writer(
                    csvfile, dialect='excel', lineterminator='\n')
                writer.writerow(header)
                for row in range(self.tableWidget.rowCount()):
                    writer.writerow(
                        self.tableWidget.item(row, column).text()
                        for column in columns)


# primary block code
app = QApplication(sys.argv)
window = MainWindow()
window.setFixedSize(1058, 765)
window.setWindowIcon(QIcon("icon.ico"))
window.show()
sys.exit(app.exec())

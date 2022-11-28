#! python3
import os
import sys
import time
import collections
import configparser

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication, QWidget

os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ['PATH']
from interface import USB_BACKEND, HID_BACKEND


N_CHNL = 4  # DAC Channel Count


'''
from USBHID_UI import Ui_USBHID
class USBHID(QWidget, Ui_USBHID):
    def __init__(self, parent=None):
        super(USBHID, self).__init__(parent)
        
        self.setupUi(self)
'''
class USBHID(QWidget):
    def __init__(self, parent=None):
        super(USBHID, self).__init__(parent)
        
        uic.loadUi('USBDAC.ui', self)

        self.devices = self.get_devices()
        self.cmbPort.addItems(self.devices.keys())

        self.Waves = {}
        for file in os.listdir('waves'):
            if file.endswith('.txt'):
                self.cmbWave.addItem(file[:-4])

                text = open(f'waves/{file}', 'r').read().replace(',', ' ')
                self.Waves[file[:-4]] = [int(x, 16) for x in text.split()]

        self.initSetting()

        self.tmrRcv = QtCore.QTimer()
        self.tmrRcv.setInterval(10)
        self.tmrRcv.timeout.connect(self.on_tmrRcv_timeout)
        self.tmrRcv.start()

        self.tmrRcv_Cnt = 0
    
    def get_devices(self):
        hids = HID_BACKEND.get_all_connected_interfaces()
        hids = [(f'HID: {dev.info()}', dev) for dev in hids]
        #usbs = USB_BACKEND.get_all_connected_interfaces()
        #usbs = [(f'USB: {dev.info()}', dev) for dev in usbs]

        return collections.OrderedDict(hids) # + usbs)

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w', encoding='utf-8')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini', encoding='utf-8')
        
        if not self.conf.has_section('HID'):
            self.conf.add_section('HID')
            self.conf.set('HID', 'port', '')

        if not self.conf.has_section('DAC'):
            self.conf.add_section('DAC')
            self.conf.set('DAC', 'chnl', '1')
            self.conf.set('DAC', 'wave', '')

        index = self.cmbPort.findText(self.conf.get('HID', 'port'))
        self.cmbPort.setCurrentIndex(index if index != -1 else 0)

        index = self.cmbWave.findText(self.conf.get('DAC', 'wave'))
        self.cmbWave.setCurrentIndex(index if index != -1 else 0)

        self.on_cmbWave_currentIndexChanged(self.cmbWave.currentText())  # 确保启动时必定执行一次此函数

        try:
            self.dacChnl = int(self.conf.get('DAC', 'chnl'))
        except:
            self.dacChnl = 1

        eval(f'self.rdoCH{self.dacChnl}').setChecked(True)
        
        for i in range(N_CHNL):
            eval(f'self.rdoCH{i+1}').toggled.connect(lambda checked, chnl=i+1: self.on_rdoCHx_toggled(checked, chnl))

    def on_rdoCHx_toggled(self, checked, chnl):
        if checked:
            self.dacChnl = chnl

    @pyqtSlot(str)
    def on_cmbWave_currentIndexChanged(self, text):
        self.txtMain.clear()

        if text in self.Waves:
            self.Wave = self.Waves[text]

            i = 0
            while i < len(self.Wave):
                self.txtMain.append(''.join([f'{x:03X}, ' for x in self.Wave[i:i+20]]))
                i += 20

    @pyqtSlot()
    def on_btnOpen_clicked(self):
        if self.btnOpen.text() == '打开连接':
            try:
                self.dev = self.devices[self.cmbPort.currentText()]
                self.dev.open()
                self.dev.packet_size = 32   # 没这句 Win7 下发送不出数据
            except Exception as e:
                print(e)
            else:
                self.cmbPort.setEnabled(False)
                self.btnOpen.setText('断开连接')
        else:
            self.dev.close()

            self.cmbPort.setEnabled(True)
            self.btnOpen.setText('打开连接')

    @pyqtSlot()
    def on_btnSend_clicked(self):
        if self.btnOpen.text() == '断开连接':
            i = 0
            while i < len(self.Wave):
                dword = self.Wave[i:i+15]   # 每个包 32 字节（16 字），第一个字是控制字，后面跟 15 个字的数据

                dbyte = [i & 0xFF, (0 << 4) | (i >> 8)]     # 控制字高 4 位为 DAC 通道号，低 12 位为数据在波形上的偏移

                for x in dword:
                    dbyte.append(x & 0xFF)
                    dbyte.append(x >> 8)

                self.dev.write(dbyte)
                
                i += 15

    def on_tmrRcv_timeout(self):
        self.tmrRcv_Cnt += 1

        if self.btnOpen.text() == '断开连接':
            pass
        
        else:
            if self.tmrRcv_Cnt % 100 == 0:
                devices = self.get_devices()
                if len(devices) != self.cmbPort.count():
                    self.devices = devices
                    self.cmbPort.clear()
                    self.cmbPort.addItems(devices.keys())
    
    def closeEvent(self, evt):
        self.conf.set('HID', 'port', self.cmbPort.currentText())
        self.conf.set('DAC', 'wave', self.cmbWave.currentText())
        self.conf.set('DAC', 'chnl', f'{self.dacChnl}')
        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    usb = USBHID()
    usb.show()
    app.exec()

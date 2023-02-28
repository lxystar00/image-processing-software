import sys
from PyQt5 import QtGui
import first
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QSlider
from PyQt5 import uic
from dehaze import DarkChannel, AtmLight, TransmissionEstimate, Guidedfilter, TransmissionRefine, Recover

from PyQt5.QtCore import Qt
import cv2
import math
import numpy as np

import torch

import argparse

import matplotlib.pyplot as plt
import PIL.Image as Image
import scipy.misc
import torch.nn.parallel
import torchvision.transforms as transforms
from torch.autograd import Variable


print(torch.cuda.is_available())


class Pic1:
    def __init__(self):
        self.ui = uic.loadUi('first.ui')
        #print(self.ui.label_4.size+'1')
        self.ui.pushButton_2.clicked.connect(self.openImage)
        self.ui.radioButton.toggled.connect(self.model_choose)
        self.ui.radioButton_2.toggled.connect(self.model_choose)
        self.ui.pushButton_3.clicked.connect(self.saveImage)
        self.ui.horizontalSlider.valueChanged.connect(self.omega_change)


    # 选择本地图片上传
    def openImage(self):
        global imgNamepath# 这里为了方便别的地方引用图片路径，将其设置为全局变量
        imgNamepath, imgType = QFileDialog.getOpenFileName(self.ui, "选择图片", "C:\\", "*.jpg;;*.png;;All Files(*)")
        self.ui.label_4.setPixmap(QtGui.QPixmap(""))  # 移除label上的图片 # # 显示所选图片的路径
        self.ui.lineEdit.setText(imgNamepath)# 在label控件上显示选择的图片
        img = QtGui.QPixmap(imgNamepath).scaled(541,391, Qt.KeepAspectRatio)  # 按比例缩放图片
        print("img: ", img.width(), img.height())
        self.ui.label_4.setFixedSize(img.width(), img.height())
        self.ui.label_4.setPixmap(img)
        self.ui.label_4.repaint()


    def saveImage(self):
        img = self.ui.label_5.pixmap().toImage()
        fpath, ftype = QFileDialog.getSaveFileName(self.ui, "保存", "D:\\", "*.jpg;;*.png;;All Files(*)")
        img.save(fpath)

    def omega_change(self):
        global omega
        omega = self.ui.horizontalSlider.value()/100
        self.startAction()

    def model_choose(self):
        global checked
        #radioButton = self.ui.sender()
        if self.ui.radioButton.isChecked() == True:
            self.omega_change()

        else:
            if self.ui.radioButton_2.isChecked() == True:
                self.network()
            else:
              return

    def startAction(self):
        src = cv2.imread(imgNamepath)

        I = src.astype('float64') / 255
        dark = DarkChannel(I, 15)
        A = AtmLight(I, dark)
        te = TransmissionEstimate(omega, I, A, 15)
        t = TransmissionRefine(src, te)
        J = Recover(I, t, A, 0.1)

        cv2.imwrite("./image/J.png", J * 255)

        self.ui.label_5.setPixmap(QtGui.QPixmap(""))  # 移除label上的图片
        imgShow = QtGui.QPixmap("./image/J.png").scaled(541,391, Qt.KeepAspectRatio)
        self.ui.label_5.setFixedSize(imgShow.width(), imgShow.height())
        self.ui.label_5.setScaledContents(True)
        self.ui.label_5.setPixmap(imgShow)


    def network(self):
        net = torch.load("./AOD_net_epoch_relu_10.pth",
                         map_location=torch.device('cpu'))
        # net.to("cpu").eval()
        net = net.cpu()

        img = Image.open(imgNamepath).convert('RGB')

        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
        ]
        )
        imgIn = transform(img).unsqueeze_(0)

        # ===== Test procedures =====
        varIn = Variable(imgIn)

        varIn = varIn.cpu()

        prediction = net(varIn)
        prediction = prediction.data.cpu().numpy().squeeze().transpose((1, 2, 0))

        cv2.imwrite("./image/M.png", prediction * 255)  # 使用cv2实现图片与numpy数组的相互转化

        self.ui.label_5.setPixmap(QtGui.QPixmap(""))  # 移除label上的图片
        imgShow = QtGui.QPixmap("./image/M.png").scaled(541,391, Qt.KeepAspectRatio)
        self.ui.label_5.setFixedSize(imgShow.width(), imgShow.height())
        self.ui.label_5.setScaledContents(True)
        self.ui.label_5.setPixmap(imgShow)


if __name__ == '__main__':
    app = QApplication([])
    # 显示创建的界面
    MainWindow = Pic1()  # 创建窗体对象
    MainWindow.ui.show()  # 显示窗体
    app.exit(app.exec_())  # 程序关闭时退出进程

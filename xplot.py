"""
Saruul Nasanjargal (Hannover, 2024)
"""
import sys, os, time
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QWidget, QGridLayout, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QListWidgetItem
from PyQt5.QtWidgets import QDialog, QPushButton, QSplitter, QDoubleSpinBox, QSizePolicy, QLabel, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
import qtmodern.styles
import matplotlib.pyplot as plt
import pyqtgraph.exporters
import argparse


SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DEFAULT_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tests/testdata.txt')
DEFAULT_PTS_TO_DISPLAY = 100

sys.path.append(SRC)
from file_read_backwards import FileReadBackwards

QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QtCore.QLocale.setDefault(QtCore.QLocale("en_US"))


def read_backwards_from(filename):
    '''
    reads the second to last line from a file
    '''
    data = []

    with FileReadBackwards(filename) as file:
        lineCount = 0
        for line in file:
            if lineCount == 2:
                break
            else:
                data.append(line.split())
                lineCount += 1

    data.pop(0)   
    file.close()
    return data[0]


class xPlotPreferences(QDialog):
    preferences_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        
        self.setWindowTitle('Preferences')
        # self.setGeometry(200, 200, 300, 200)
        self.layout = QtWidgets.QGridLayout()                        # Grid layout
        self.setLayout(self.layout)
        self.edit_pts_to_display = QtWidgets.QLineEdit('Hello World')
        self.label = QtWidgets.QLabel("Hello2")
        self.binSizeSpinBox = QtWidgets.QDoubleSpinBox()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.binSizeSpinBox.sizePolicy().hasHeightForWidth())
        self.binSizeSpinBox.setSizePolicy(sizePolicy)
        self.binSizeSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.binSizeSpinBox.setProperty("showGroupSeparator", True)
        self.binSizeSpinBox.setDecimals(0)
        self.binSizeSpinBox.setMinimum(2)
        self.binSizeSpinBox.setMaximum(10000)
        self.binSizeSpinBox.setProperty("value", 100)
        self.binSizeSpinBox.setObjectName("binSizeSpinBox")
        self.label.setText("Points to plot:")
        self.btn_exit = QPushButton('Close', self)
        self.btn_exit.clicked.connect(self.close)
        self.layout.addWidget(self.edit_pts_to_display, 0, 0)
        self.layout.addWidget(self.binSizeSpinBox, 1, 1)
        self.layout.addWidget(self.label, 1, 0)
        self.layout.addWidget(self.btn_exit, 2, 0)

        self.binSizeSpinBox.valueChanged.connect(self.change_pts_to_display)


    def change_pts_to_display(self):
        self.preferences_changed.emit(int(self.binSizeSpinBox.value()))



class xPlot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-f', '--file_path', help="Path to the text file to be parsed")
        self.args = self.parser.parse_args()

        self.nchan = None                                            # Number of channels
        self.chxx = {}                                               # Dictionary with plot objects
        self.sharedList = []                                         # List of lists containing all of the data to plot
        self.pts_to_display = DEFAULT_PTS_TO_DISPLAY                 # Maximum number of points to display
        if self.args.file_path is None:
            self.file_path = DEFAULT_FILEPATH                        # Path of the input data file
        else:
            self.file_path = self.args.file_path
        self.init_ui()
        self.win_preferences = xPlotPreferences()
        self.win_preferences.preferences_changed.connect(self.handle_preferences_changed)

    def handle_preferences_changed(self, new_pts_to_display):
        self.pts_to_display = new_pts_to_display


    def handle_pts_to_display(self, new_pts_to_display):
        self.pts_to_display = new_pts_to_display
        if (len(self.sharedList) > new_pts_to_display):
            self.sharedList = self.sharedList[:-(len(self.sharedList)-int(new_pts_to_display))]


    def pause(self):
        self.ispaused = not self.ispaused
        if self.ispaused:
            self.act_pause.setText("Unpause")
        else:
            self.act_pause.setText("Pause")


    def export(self):
        exporter = pg.exporters.ImageExporter(self.plotw.plotItem)
        exporter.parameters()['width'] = 1800   # Set the width of the exported image
        exporter.parameters()['height'] = 1600  # Set the height of the exported image
        file_path, _ = QFileDialog.getSaveFileName(None, "Save File", "", "PNG Files (*.png);;PDF Files (*.pdf)")

        if file_path:
            exporter.export(file_path)
            print(f"Plot saved as: {file_path}")


    def open_file(self):
        self.file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "TXT Files (*.txt)")
        self.init_file()


    def open_preferences(self):
        main_window_position = self.pos()
        main_window_width = self.width()
        new_window_x = main_window_position.x() + main_window_width + 10  # Adjust for desired horizontal spacing
        new_window_y = main_window_position.y()
        self.win_preferences.setGeometry(new_window_x, new_window_y, 300, 200)
        self.win_preferences.show()


    def new_file_path_entered(self):
        self.file_path = self.textw.text()
        self.init_file()


    def init_file(self):
        data = read_backwards_from(self.file_path)
        self.nchan = len(data)
        self.chxx = {}
        self.sharedList = []
        self.listw.clear()
        self.plotw.clear()
        self.textw.clear()
        self.textw.insert(self.file_path)
        for ch in range(self.nchan):
            self.chxx['ch'+str(ch)] = self.plotw.plot(pen=(ch,self.nchan),name='ch'+str(ch))
            self.chxx['ch'+str(ch)+'_checkbox'] = QListWidgetItem('ch' + str(ch) + ' - ' + data[ch], self.listw)
            self.chxx['ch'+str(ch)+'_checkbox'].setFlags(self.chxx['ch'+str(ch)+'_checkbox'].flags() | pg.QtCore.Qt.ItemIsUserCheckable)
            self.chxx['ch'+str(ch)+'_checkbox'].setCheckState(pg.QtCore.Qt.Checked)

    def init_ui(self):

        """
        Center pane: graph
        """
        self.layout_center_pane = QVBoxLayout()
        self.widget_center_pane = QWidget()
        self.widget_center_pane.setLayout(self.layout_center_pane)
        self.plotw = pg.PlotWidget()                                 # Data graph
        self.plotw.setLabel('left', "Temperature", units='K')
        self.plotw.setLabel('bottom', "Samples", units='#')
        self.ispaused = False
        self.layout_center_pane.addWidget(self.plotw)
        

        """
        Left pane: menu, input file directory, and channel selection
        """
        self.layout_left_pane = QVBoxLayout()
        self.widget_left_pane = QWidget()
        self.widget_left_pane.setLayout(self.layout_left_pane)
        self.menuw = QtWidgets.QMenu()                               # Dropdown menu with options
        self.act_open_file = self.menuw.addAction("Open")            # Open new input data file
        self.act_export = self.menuw.addAction("Export")             # Export graph
        self.act_pause = self.menuw.addAction("Pause")               # Pause the data plotting
        self.act_open_pref = self.menuw.addAction("Preferences")     # Show Preferences window
        self.act_exit = self.menuw.addAction("Exit")                 # Exit the program
        self.act_open_file.triggered.connect(self.open_file)
        self.act_export.triggered.connect(self.export)
        self.act_pause.triggered.connect(self.pause)
        self.act_open_pref.triggered.connect(self.open_preferences)
        self.act_exit.triggered.connect(exit)
        self.pbtnw = QtWidgets.QPushButton('Option')                 # Push button for dropdown menu
        self.pbtnw.setMenu(self.menuw)
        self.textw = QtWidgets.QLineEdit(self.file_path)             # Input data file can be edited here
        self.textw.returnPressed.connect(self.new_file_path_entered)
        self.listw = QtWidgets.QListWidget()                         # List of identified channels
        self.plot_item = self.plotw.getPlotItem()
        self.plot_item.setLabels(title='')
        self.timer = QtCore.QTimer()                                 # Timer for graph update
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        self.layout_left_pane.addWidget(self.pbtnw)
        self.layout_left_pane.addWidget(self.textw)
        self.layout_left_pane.addWidget(self.listw)
        self.widget_left_pane.setMinimumWidth(200)
        self.widget_left_pane.setMaximumWidth(500)

        """
        Right pane: plot options
        """
        self.layout_right_pane = QGridLayout()
        self.widget_right_pane = QWidget()
        self.widget_right_pane.setLayout(self.layout_right_pane)
        self.spinbox_pts_to_plot = QDoubleSpinBox()
        sizePolicy = QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinbox_pts_to_plot.sizePolicy().hasHeightForWidth())
        self.spinbox_pts_to_plot.setSizePolicy(sizePolicy)
        self.spinbox_pts_to_plot.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.spinbox_pts_to_plot.setProperty("showGroupSeparator", True)
        self.spinbox_pts_to_plot.setDecimals(0)
        self.spinbox_pts_to_plot.setMinimum(100)
        self.spinbox_pts_to_plot.setSingleStep(100)
        self.spinbox_pts_to_plot.setMaximum(10000)
        self.spinbox_pts_to_plot.setProperty("value", 100)
        self.label = QLabel("Points to display:")
        self.layout_right_pane.addWidget(self.label,0,0)
        self.layout_right_pane.addWidget(self.spinbox_pts_to_plot,0,1)
        self.widget_right_pane.setMinimumWidth(200)
        self.widget_right_pane.setMaximumWidth(300)

        self.spinbox_pts_to_plot.valueChanged.connect(self.handle_pts_to_display)

        """
        Left/Center and Center/Right splitters
        """
        self.splitter_left_center = QSplitter()                      # Create a QSplitter to handle resizing
        self.splitter_left_center.addWidget(self.widget_left_pane)
        self.splitter_left_center.addWidget(self.widget_center_pane)
        self.splitter_left_center.setHandleWidth(10)
        
        self.splitter_main = QSplitter()
        self.splitter_main.addWidget(self.splitter_left_center)
        self.splitter_main.addWidget(self.widget_right_pane)
        self.splitter_main.setHandleWidth(10)

        self.splitter_left_center.setStretchFactor(1,1);
        self.splitter_main.setStretchFactor(0,1);

        """
        Main layout and widget
        """
        self.layout = QGridLayout()                                  # Main layout to hold everything
        self.widget = QWidget()                                      # Main widget to hold everything
        self.setCentralWidget(self.widget)
        self.widget.setWindowTitle('xplot')
        self.widget.setLayout(self.layout)

        self.layout.addWidget(self.splitter_main, 0,0)


    def update(self):
        # Update the plot with new data
        if not self.ispaused:
            if self.nchan == None:
                self.init_file()
            data = read_backwards_from(self.file_path)
            self.sharedList.append(data)
            if len(self.sharedList) > (self.pts_to_display-1):
                self.sharedList.pop(0)
            # n = np.zeros((8,len(self.sharedList)))
            n = np.random.randn(self.nchan,len(self.sharedList))
            for ch in range(self.nchan):
                if self.chxx['ch'+str(ch)+'_checkbox'].checkState():
                    self.chxx['ch'+str(ch)].setData([float(l[ch]) for l in self.sharedList]+n[ch])
                else:
                    self.chxx['ch'+str(ch)].clear()
                self.chxx['ch'+str(ch)+'_checkbox'].setText('ch' + str(ch) + ' - ' + data[ch])


if __name__ == '__main__':

    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    pal = app.palette()
    pal.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(66, 66, 66))
    app.setPalette(pal)

    xplot = xPlot()
    xplot.show()

    sys.exit(app.exec_())




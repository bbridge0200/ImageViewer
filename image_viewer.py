import sys
from PyQt5.QtWidgets import QToolButton, QToolBar, QFileDialog
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np
import pyqtgraph as pg
from aicsimageio import AICSImage

class App(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)

        #### Create Gui Elements ###########
        self.main_box = QtWidgets.QWidget()
        self.setCentralWidget(self.main_box)
        self.main_box.setLayout(QtWidgets.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()
        self.main_box.layout().addWidget(self.canvas)


        #self.main_box.layout().addWidget(self.label)

        self.view = self.canvas.addViewBox()
        self.view.setAspectLocked(True)
        self.view.setRange(QtCore.QRectF(0,0, 100, 100))

        #  default image plot

        self.img = pg.ImageItem(border='w')
        self.img = np.zeros([100, 100], dtype=np.uint8)
        self.img = pg.ImageItem(self.img)
        self.view.addItem(self.img)

        toolbar = QToolBar()
        tool = QToolButton()
        tool.setText("Add Image")

        toolbar.addWidget(tool)

        self.addToolBar(toolbar)
        tool.clicked.connect(self.add_image)

    def add_image(self):
        """"""
        f_name = QFileDialog.getOpenFileName(self, 'Open File', 'c\\', 'All Files (*)')
        self.img = pg.ImageItem(border='w')
        self.img = AICSImage(f_name)
        numpy_array = self.img.data
        meta = self.img.metadata
        self.img = make_assumptions(numpy_array, meta)
        self.img = pg.ImageItem(self.img)
        self.view.addItem(self.img)


def make_assumptions(numpy_array, meta):
    """
    Since AICSImageViewer does not support over 2 dim images, we made this to make assumtions
    about 3,4, and 5-d images to be able to fit them in this viewer.
    We assume:
    - First time point
    - Middle Z stack
    - Transmitted Light channel if available, if not first channel
    """
    if "C" in meta["dimensions_order"]:
        index = 0
        try:
            # use transmitted light channel

            if "transmitted light" in meta["channel_names"]:
                # local testing uses "transmitted light" as channel name
                index = meta["channel_names"].index("transmitted light")
            else:
                # tim uses TL/488 50um Dual as Transmitted Light channel name
                # note: we need a standard name for TL images
                index = meta["channel_names"].index("TL/488 50um Dual")
        except BaseException:
            # just use the first image if we cant find expcted TL names
            index = 0

        if meta["dimensions_order"] == "CXY":
            return numpy_array[index, :, :]
        elif meta["dimensions_order"] == "CZXY":
            return numpy_array[index, int(np.shape(numpy_array)[1] / 2), :, :]  # middle slice
        elif meta["dimensions_order"] == "CTXY":
            return numpy_array[index, 0, :, :]
        elif meta["dimensions_order"] == "CTZXY":
            return numpy_array[index, 0, round(np.shape(numpy_array)[2] / 2), :, :]
        elif meta["dimensions_order"] == "TCZXY":
            return numpy_array[0, index, round(np.shape(numpy_array)[2] / 2), :, :]
        else:
            return numpy_array
    elif 's' in ["dimensions_order"]:
        return stitch_montage(numpy_array, meta)
    else:
        if meta["dimensions_order"] == "ZXY":
            # use middle z stack
            # test where the z vals lie from 3i slidebook
            return numpy_array[np.shape(numpy_array)[2] / 2, :, :]
        elif meta["dimensions_order"] == "TXY":
            return numpy_array[0, :, :]
        elif meta["dimensions_order"] == "TZXY":
            return numpy_array[0, np.shape(numpy_array)[2] / 2, :, :]
        else:
            return numpy_array



def stitch_montage(montage_image, meta):
    # sort the stage locations by y
    sorted_cols = meta["stage_locations"].sort(key=lambda coordinates: coordinates[1])
    # group the same x values, stable
    split_by_col = list(split_tuple_equals_to_list(sorted_cols).values())
    #! sort for x? test
    # coords now split into lists with same x, sorted y.

    image = list()
    for col in split_by_col:
        image_col = list()
        for coords in col:
            #Create image cols with the same x coords
            idx = meta["stage_locations"].index(coords)
            image_col.append(montage_image[idx, :, :])
        image.append(np.vstack(image_col))
    # Stack cols horizontally for montage
    montage = np.hstack(image)
    return montage

def split_tuple_equals_to_list(list, idx=0):
    ret = dict() # supporting dict to split list of tuples by idx ==
    for i in list:
        key = i[idx]
        if key not in ret:
            ret[key] = []
        ret[key].append[i]
    return ret


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    this_app = App()
    this_app.show()
    sys.exit(app.exec_())
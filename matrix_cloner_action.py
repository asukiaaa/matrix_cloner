import math
import os
import pcbnew
import traceback
import wx
from .outline_measure import getWidthHeightNmOfBoard

pluginName = 'Matrix cloner'

def repeat(baseBoard, destinationBoard, lengthNmX, lengthNmY, numberX, numberY, ignoreUserLayer=True):
    modules = list(baseBoard.GetModules())
    tracks = list(baseBoard.GetTracks())
    drawings = list(baseBoard.GetDrawings())
    areas = [baseBoard.GetArea(i) for i in range(0, baseBoard.GetAreaCount())]
    for x in range(0, numberX):
        for y in range(0, numberY):
            if destinationBoard == baseBoard and x == 0 and y == 0:
                continue
            offsetX = lengthNmX * x
            offsetY = lengthNmY * y
            for baseItem in modules:
                newItem = baseItem.__class__(baseItem)
                destinationBoard.Add(newItem)
                basePosition = baseItem.GetPosition()
                newItem.SetPosition(pcbnew.wxPoint(basePosition[0] + offsetX, basePosition[1] + offsetY))
            for baseItem in tracks + drawings + areas:
                if ignoreUserLayer and 'User' in baseItem.GetLayerName():
                    continue
                newItem = baseItem.Duplicate()
                newItem.Move(pcbnew.wxPoint(offsetX, offsetY))
                destinationBoard.Add(newItem)


def getAndRepeatBoard(targetWidthNm, targetHeightNm, numberX, numberY, filePathToSave=None):
    board = pcbnew.GetBoard()
    wh = getWidthHeightNmOfBoard(board)
    if wh is None:
        raise Exception('Cannot get size of board')
    widthNm = wh[0]
    heightNm = wh[1]
    if numberX is None:
        numberX = math.floor(targetWidthNm / widthNm)
        numberY = math.floor(targetHeightNm / heightNm)
    # print(numberX, numberY)
    targetBoard = None
    if filePathToSave is None:
        targetBoard = board
    else:
        # targetBoard = pcbnew.BOARD() # causes segmentation fault on saving
        board.Save(filePathToSave)
        targetBoard = pcbnew.LoadBoard(filePathToSave)
    repeat(targetBoard, targetBoard, lengthNmX=widthNm, lengthNmY=heightNm, numberX=numberX, numberY=numberY)
    if targetBoard != board:
        print("save as", filePathToSave)
        targetBoard.Save(filePathToSave)
        print("saved")
    else:
        print("clone on board")
    pcbnew.Refresh()


class Dialog(wx.Dialog):
    RADIO_ID_SELECT_NUMBER = 0
    RADIO_ID_SELECT_SIZE = 1
    selectedRadio = RADIO_ID_SELECT_SIZE

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=-1, title=pluginName)
        panel = wx.Panel(self)
        radioSelectSize = wx.RadioButton(panel, self.RADIO_ID_SELECT_SIZE, 'Create matrix by panel size')
        self.textCtrlWidthMm = wx.TextCtrl(panel, value='100')
        self.textCtrlHeightMm = wx.TextCtrl(panel, value='100')
        radioSelectNumber = wx.RadioButton(panel, self.RADIO_ID_SELECT_NUMBER, 'Create matrix by number')
        self.textCtrlNumberX = wx.TextCtrl(panel, value='2')
        self.textCtrlNumberY = wx.TextCtrl(panel, value='3')
        sizeInputSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizeInputSizer.Add(wx.StaticText(panel, label='width'), flag=wx.ALIGN_CENTER_VERTICAL)
        sizeInputSizer.Add(self.textCtrlWidthMm, flag=wx.ALIGN_CENTER_VERTICAL)
        sizeInputSizer.Add(wx.StaticText(panel, label='mm x height'), flag=wx.ALIGN_CENTER_VERTICAL)
        sizeInputSizer.Add(self.textCtrlHeightMm, flag=wx.ALIGN_CENTER_VERTICAL)
        sizeInputSizer.Add(wx.StaticText(panel, label='mm'), flag=wx.ALIGN_CENTER_VERTICAL)
        numberInputSizer = wx.BoxSizer(wx.HORIZONTAL)
        numberInputSizer.Add(wx.StaticText(panel, label='horizontal(x) number'), flag=wx.ALIGN_CENTER_VERTICAL)
        numberInputSizer.Add(self.textCtrlNumberX, flag=wx.ALIGN_CENTER_VERTICAL)
        numberInputSizer.Add(wx.StaticText(panel, label=' vertical(y) number'), flag=wx.ALIGN_CENTER_VERTICAL)
        numberInputSizer.Add(self.textCtrlNumberY, flag=wx.ALIGN_CENTER_VERTICAL)
        radioSizer = wx.BoxSizer(wx.VERTICAL)
        radioSizer.Add(radioSelectSize)
        radioSizer.Add(sizeInputSizer)
        radioSizer.Add(radioSelectNumber)
        radioSizer.Add(numberInputSizer)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadiogroup)
        execbtn = wx.Button(panel, label='Clone for matrix')
        clsbtn = wx.Button(panel, label='Close')
        clsbtn.Bind(wx.EVT_BUTTON, self.onClose)
        execbtn.Bind(wx.EVT_BUTTON, self.onExec)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(execbtn)
        buttonSizer.Add(clsbtn)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(radioSizer, flag=wx.EXPAND|wx.LEFT, border=5)
        layout.Add(buttonSizer, flag=wx.EXPAND|wx.LEFT, border=5)
        panel.SetSizer(layout)
        self.onSelectSize()

    def onRadiogroup(self, e):
        rb = e.GetEventObject()
        self.selectedRadio = rb.GetId()
        if self.selectedRadio == self.RADIO_ID_SELECT_SIZE:
            self.onSelectSize()
        else:
            self.onSelectNumber()

    def onSelectSize(self):
        self.textCtrlHeightMm.Enable()
        self.textCtrlWidthMm.Enable()
        self.textCtrlNumberX.Disable()
        self.textCtrlNumberY.Disable()

    def onSelectNumber(self):
        self.textCtrlHeightMm.Disable()
        self.textCtrlWidthMm.Disable()
        self.textCtrlNumberX.Enable()
        self.textCtrlNumberY.Enable()

    def onClose(self,e):
        e.Skip()
        self.Close()

    def onExec(self,e):
        try:
            targetWidthNm = None
            targetHeightNm = None
            numberX = None
            numberY = None
            if self.selectedRadio == self.RADIO_ID_SELECT_SIZE:
                targetWidthNm = float(self.textCtrlWidthMm.GetValue())*(10**6)
                targetHeightNm = float(self.textCtrlHeightMm.GetValue())*(10**6)
            else:
                numberX = int(self.textCtrlNumberX.GetValue())
                numberY = int(self.textCtrlNumberY.GetValue())
            # boardFileName = pcbnew.GetBoard().GetFileName()
            # boardDirPath = os.path.dirname(boardFileName)
            # boardProjectName = (os.path.splitext(os.path.basename(boardFileName)))[0]
            # filePathToSave = '%s/%s_matrix.kicad_pcb' % (boardDirPath, boardProjectName)
            filePathToSave = None
            getAndRepeatBoard(targetWidthNm=targetWidthNm, targetHeightNm=targetHeightNm, numberX=numberX, numberY=numberY, filePathToSave=filePathToSave)
            message = 'Cloned'
            wx.MessageBox(message, pluginName, wx.OK|wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox('Error: ' + str(e) + '\n\n' + traceback.format_exc(), pluginName, wx.OK|wx.ICON_INFORMATION)
        e.Skip()


class MatrixClonerAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = pluginName
        self.category = 'A descriptive category name'
        self.description = ' plugin to put pcb as matrix to order with using v cut.'
        self.show_toolbar_button = True
        # self.icon_file_name = os.path.join(os.path.dirname(__file__), 'matrix_putter.png')

    def Run(self):
        dialog = Dialog(None)
        dialog.Center()
        dialog.ShowModal()
        dialog.Destroy()

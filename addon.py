import math

import xbmc
import xbmcaddon
import xbmcgui

monitor = xbmc.Monitor()
capture = xbmc.RenderCapture()
myplayer = xbmc.Player()

CaptureWidth = 48
CaptureHeight = 54

def notify(msg):
    xbmcgui.Dialog().notification("BlackBarsNever", msg, None, 1000)

class Player(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)
        self.reset()

    def reset(self):
        self.lowestZoom = math.inf

    def onAVStarted(self):
        self.reset()
        self.abolishBlackBars()

    def onPlayBackStarted(self):
        self.abolishBlackBars()

    def onPlayBackResumed(self):
        self.abolishBlackBars()

    def CaptureFrame(self):
        capture.capture(CaptureWidth, CaptureHeight)
        capturedImage = capture.getImage(2000)
        return capturedImage

    # _bArray: byte Array that contains the data we want to test
    # _lineStart: where to start testing
    # _lineCount: how many lines to test
    # _threshold: value to determine testing
    # returns: True False
    def LineColorLessThan(self, _bArray, _lineStart, _lineCount, _threshold=25):
        __sliceStart = _lineStart * CaptureWidth * 4
        __sliceEnd = (_lineStart + _lineCount) * CaptureWidth * 4

        # zero out the alpha channel
        i = __sliceStart + 3
        while i < __sliceEnd:
            _bArray[i] &= 0x00
            i += 4

        __imageLine = _bArray[__sliceStart:__sliceEnd]
        return all([v < _threshold for v in __imageLine])

    # Returns Aspect ratio (i.e. 2.35)
    # Detects hardcoded black bars
    def GetAspectRatioFromFrame(self):
        # wait for transitions by capturing images until captured image is not dark
        while True:
            __myimage = self.CaptureFrame()
            # test for darkness in the 2.40 aspect ratio area
            __middleScreenDark = self.LineColorLessThan(__myimage, 7, 2)
            if not __middleScreenDark:
                break
            xbmc.sleep(1000)

        if self.LineColorLessThan(__myimage, 1, 5):
            __aspectratio = 2.35
        elif self.LineColorLessThan(__myimage, 1, 3):
            __aspectratio = 2.00
        elif self.LineColorLessThan(__myimage, 0, 1):
            __aspectratio = 1.85
        else:
          __aspectratio = capture.getAspectRatio() + 0.005

        return __aspectratio

    def abolishBlackBars(self):
        aspectratio = self.GetAspectRatioFromFrame()
        aspectratio2 = capture.getAspectRatio() + 0.005
        xbmc.log('Calculated Aspect Ratio = ' + str(aspectratio) + ' ' + 'Player Aspect Ratio = ' + str(aspectratio2), level=xbmc.LOGINFO)
        zoom_amount = max(1.0, aspectratio / 1.78)
        if zoom_amount < self.lowestZoom:
            # pick the lowest zoom seen yet, to correct false positives
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.SetViewMode", "params": {"viewmode": {"zoom": ' + str(zoom_amount) + ' }}, "id": 1}')
            notify("Zoom: {:0.2f}".format(zoom_amount))
            self.lowestZoom = zoom_amount

p = Player()

while not monitor.abortRequested():
    # Sleep/wait for abort for 10 seconds
    if monitor.waitForAbort(10):
        # Abort was requested while waiting. We should exit
        break

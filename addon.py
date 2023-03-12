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

    def onAVStarted(self):
        xbmc.log("AV playback started")
        self.abolishBlackBars()

    def CaptureFrame(self):
        capture.capture(CaptureWidth, CaptureHeight)
        capturedImage = capture.getImage(2000)
        return capturedImage

    ##############
    #
    # LineColorLessThan
    #    _bArray: byte Array that contains the data we want to test
    #    _lineStart: where to start testing
    #    _lineCount: how many lines to test
    #    _threshold: value to determine testing
    # returns: True False
    ###############

    def LineColorLessThan(self, _bArray, _lineStart, _lineCount, _threshold):
        __sliceStart = _lineStart * CaptureWidth * 4
        __sliceEnd = (_lineStart + _lineCount) * CaptureWidth * 4

        # zero out the alpha channel
        i = __sliceStart + 3
        while (i < __sliceEnd):
            _bArray[i] &= 0x00
            i += 4

        __imageLine = _bArray[__sliceStart:__sliceEnd]
        __result = all([v < _threshold for v in __imageLine])

        return __result

    ###############
    #
    # GetAspectRatioFromFrame
    #   - returns Aspect ratio * 100 (i.e. 2.35 = 235)
    #   Detects hardcoded black bars
    ###############

    def GetAspectRatioFromFrame(self):
        __aspectratio = int((capture.getAspectRatio() + 0.005) * 100)
        __threshold = 25

        line1 = 'Interim Aspect Ratio = ' + str(__aspectratio)
        xbmc.log(line1, level=xbmc.LOGINFO)

        # screen capture and test for an image that is not dark in the 2.40
        # aspect ratio area. keep on capturing images until captured image
        # is not dark
        while (True):
            __myimage = self.CaptureFrame()
            xbmc.log(line1, level=xbmc.LOGINFO)

            __middleScreenDark = self.LineColorLessThan(
                __myimage, 7, 2, __threshold)
            if __middleScreenDark == False:
                xbmc.sleep(1000)
                break
            else:
                xbmc.sleep(1000)

        # Capture another frame. after we have waited for transitions
        __myimage = self.CaptureFrame()
        __ar185 = self.LineColorLessThan(__myimage, 0, 1, __threshold)
        __ar200 = self.LineColorLessThan(__myimage, 1, 3, __threshold)
        __ar235 = self.LineColorLessThan(__myimage, 1, 5, __threshold)

        if (__ar235 == True):
            __aspectratio = 235

        elif (__ar200 == True):
            __aspectratio = 200

        elif (__ar185 == True):
            __aspectratio = 185

        return __aspectratio

    def abolishBlackBars(self):
        aspectratio = self.GetAspectRatioFromFrame()
        aspectratio2 = int((capture.getAspectRatio() + 0.005) * 100)

        _info = xbmc.getInfoLabel('Player.Process(VideoDAR)')
        _info2 = xbmc.getInfoLabel('Player.Process(videoheight)')
        window_id = xbmcgui.getCurrentWindowId()
        line1 = 'Calculated Aspect Ratio = ' + \
            str(aspectratio) + ' ' + 'Player Aspect Ratio = ' + str(aspectratio2)

        xbmc.log(line1, level=xbmc.LOGINFO)

        if (aspectratio > 178):
            zoom_amount = (aspectratio / 178)
        else:
            zoom_amount = 1.0

        if (aspectratio > 178) and (aspectratio2 == 178):
            # this is 16:9 and has hard coded black bars
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "method": "Player.SetViewMode", "params": {"viewmode": {"zoom": ' + str(zoom_amount) + ' }}, "id": 1}')
            notify("Black Bars were detected. Zoomed " + str(zoom_amount))
        elif (aspectratio > 178):
            # this is an aspect ratio wider than 16:9, no black bars, we assume a 16:9 (1.77:1) display
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "method": "Player.SetViewMode", "params": {"viewmode": {"zoom": ' + str(zoom_amount) + ' }}, "id": 1}')
            if (zoom_amount <= 1.02):
                notify("Wide screen was detected. Slightly zoomed " + str(zoom_amount))
            elif (zoom_amount > 1.02):
                notify("Wide screen was detected. Zoomed " + str(zoom_amount))

p = Player()

while not monitor.abortRequested():
    # Sleep/wait for abort for 10 seconds
    if monitor.waitForAbort(10):
        # Abort was requested while waiting. We should exit
        break

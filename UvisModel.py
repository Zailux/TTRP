from Observable import Observable
import serial 

class UltraVisModel:
    def __init__(self):
        self.activeUser = Observable()

        self.tracking = Observable()

    def setActiveUser(self, activeUser):
        self.activeUser.set(activeUser)


    def getSerial(self):
        self.ser = serial.Serial()
        self.ser.port = 'COM5'
        self.ser.baudrate = 9600
        self.ser.parity = serial.PARITY_NONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.xonxoff = False
        
        #self.ser.timeout = serial.Timeout(1)
        return self.ser



class Handle:

    number_handles = 0

    def __init__(self, mode, handlestring):
        
        if mode=="running":
            Handle.number_handles += 1
        '''
        self.ID = ID
        self.Q0 = Q0
        self.Qx = Qx
        self.Qy = Qy
        self.Qz = Qz
        self.Tx = Tx
        self.Ty = Ty
        self.Tz = Tz
        self.Err = Err
        '''

    @classmethod
    def getCount(cls):
        return cls.number_handles

    
    





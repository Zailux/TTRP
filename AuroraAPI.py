import serial
import time
from functools import singledispatch
#eventually checkout singledispatchmethod Python 3.8+


class Aurora:

    def __init__(self, ser):
        #Aurora System relevant Attributes

        self.sysmode =''
        #validate Serial Objecttype and open Serialport
        try: 
            if (type(ser) is not serial.serialwin32.Serial):
                raise TypeError('Invalid Object type of: '+ type(ser)+" was used. Please use pySerial Object")
            
            self.ser = ser

            self.ser.open()
            print("Sucessfully opened: "+self.ser.name)

        except serial.SerialException as e:
            raise serial.SerialException(e)
            #print("Serialexception: "+ str(e))
        


    #Debug & Additional Methods
    def writeCMD(self,cmd):
        #Validate input
        try: 
            if (type(cmd) is not str):
                raise TypeError("The Objecttype of: "+ type(cmd)+" is invalid. Please use a String for the command.")
            if (cmd.rstrip() == ""):
                raise ValueError("The command is empty. Please type a valid commandstring.")
        except ValueError as e:
            print(str(e))
            return
        except TypeError as e:
            print(str(e))
            return

        #Format input string and removes trailing Space
        cmd = cmd.rstrip().upper()

        #adds SPACE if no parameter
        if (cmd.find(' ') == -1):
            cmd = cmd+' \r'

        else:
            if(cmd.find(' ') != cmd.rfind(' ')): print("The command contains two spaces. Is the command correct?")
            cmd = cmd+'\r'
        
        cmd = cmd.encode()
        
        #Executes the given command and reads it
        self.ser.write(cmd)
        time.sleep(1)
        self.readSerial()



    #NDI Aurora Methods  

    def apirev(self):
        self.ser.write( b'APIREV \r')
        time.sleep(1)
        return self.readSerial()

    def beep(self, num):
        try: 
            num = int(num)
            if (not (0 < num < 10)): 
                raise ValueError("Invalid Parametervalue: Please choose a value between 1-9")  
            cmd ='BEEP '+str(num)+'\r'
            self.ser.write(cmd.encode())
            time.sleep(1)
            self.readSerial()

        except ValueError as e:
            print (str(e)) 

    
    def init(self):
        try: 
            self.reset()
            self.ser.write( b'INIT \r')
            time.sleep(1)
            self.readSerial()
        except Exception as e:
            print("FATAL ERROR INIT: " + str(e))
      

    def reset(self):
        self.ser.write( b'RESET \r')
        time.sleep(1)
        self.readSerial()

    def pinit(self,handle):
        
        if (not(isinstance(handle,Handle))):
                raise TypeError('Invalid Object of type:'+ type(handle)+". Please use a correct Aurora.Handle Object.")

        cmd = 'PINIT '+handle.ID+'\r'
        print("Initialisiere Handle " + handle.ID)

        #Könnte Fehler werfen??
        self.ser.write(cmd.encode())
        time.sleep(2)
        self.readSerial()

    def pena(self,handle,mode):
        penamodes = 'SDB'
        if ((not (isinstance(mode,str) and len(mode)==1))and mode.upper() not in penamodes ):
            raise ValueError("Please choose mode between: 'S','D' or 'B'.")
        if (not(isinstance(handle,Handle))):
            raise TypeError('Invalid Object of type:'+ type(handle)+". Please use a correct Handle Object.")

        cmd = 'PENA '+handle.ID+mode.upper()+'\r'
        print("Activates Handle" + handle.ID+" using mode:"+mode+".")

        #Könnte Fehler werfen??
        self.ser.write(cmd.encode())
        time.sleep(2)
        self.readSerial()

    def phsr(self, option=0):
        
        option = int(option)
        if (not (0 <= option < 5)): 
            raise ValueError("Invalid Parameter: Please choose a value between 0-4. Not 00-04")  
        
        cmd ='PHSR 0'+str(option)+'\r'
        
        self.ser.write(cmd.encode())
        time.sleep(1)
        phsr_string = self.readSerial().decode()

        return phsr_string


    def tstart(self, option=None):
        option = int(option)

        if (option!=None):
            cmd = 'TSTART \r'
        elif ((option!=40 or option!=80)): 
            raise ValueError("Invalid Parameter: Please choose value 40 or 80")  
        else:
            cmd ='TSTART '+str(option)+'\r'

        self.ser.write(cmd)
        time.sleep(1)
        self.readSerial()

    def tstop(self):
        self.ser.write( b'TSTOP \r')
        time.sleep(1)
        self.readSerial()


    #SerialMethods ------------------------
    #Einbau der Validierung Möglich
    def readSerial(self):
        out = ''
        #out = self.ser.read(1)  
        out = self.ser.read_until()
        print(out)
        #print(out.decode())
        return out

    def getSerial(self):
        return self.ser


class HandleFactory:
   
    def __init__(self, phsr ):
        #01 0A 00D 2674\r als antwort
        #01 0A 00 001 74\r keine Handles 

        self.handles = []
        self.num_handles = int(phsr[0:2])
        phsr = phsr[2:]
       
        while len(self.handles) != self.num_handles:
           
            # ID und Status 
            h_id = phsr[0:2]
            h_state = phsr[2:5]
            h = Handle(h_id,h_state)

            #Verwendete Daten from Inputstring entfernen 
            phsr = phsr[5:]
            self.handles.append(h)

    def getNum_Handles(self):
        return self.num_handles
    
    def getHandles(self):
        return self.handles



class Handle:


    def __init__(self, ID, state):
                
        self.ID = ID
        self.state = state
        self.refname = "Strenum bspw."
       

    def setVal(self):
        '''self.Q0 = Q0
        self.Qx = Qx
        self.Qy = Qy
        self.Qz = Qz
        self.Tx = Tx
        self.Ty = Ty
        self.Tz = Tz
        self.Err = Err'''
        return
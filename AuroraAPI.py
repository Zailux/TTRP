import serial
import time
import threading


class Aurora:
    
    
    def __init__(self, ser, threaded=False, num_tries=3):
        #Aurora System relevant Attributes
        if threaded:
            self.lock = threading.Lock()
        else:
            self.lock = False
      
        self.readsleep = 0
        
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
    #Commands & Parameters are not case sensitive
    def writeCMD(self,cmd,expect=False):
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

        #Removes trailing Space
        cmd = cmd.rstrip()

        #adds SPACE if no parameter
        if (cmd.find(' ') == -1):
            cmd = cmd+' \r'

        else:
            if(cmd.find(' ') != cmd.rfind(' ')): print("The command contains two spaces. Is the command correct?")
            cmd = cmd+'\r'
        
        cmd = cmd.encode()
        
        #Executes the given command and reads it
        self.ser.write(cmd)
        if (expect != False):        
            self.readSerial(expected=expect)
        else:
            self.readSerial()

    


    #NDI Aurora Methods  

    def apirev(self):
        self.ser.write( b'APIREV \r')
        return self.readSerial()

    def beep(self, num):
        try:
            
            num = int(num)
            if (not (0 < num < 10)): 
                raise ValueError("Invalid Parametervalue: Please choose a value between 1-9")  
            cmd ='BEEP '+str(num)+'\r'
            self.ser.write(cmd.encode())
            #time.sleep(1)
            self.readSerial()
            

        except ValueError as e:
            print (str(e)) 

        finally:
            self.lock.release()

    
    def init(self):
        self.ser.write(b'INIT \r')
        self.readSerial()
        

    def get(self, attr=None):
        return

    def reset(self):
        self.ser.write(b'RESET \r')
        self.readSerial()

    def pinit(self,handle):
        
        if (not(isinstance(handle,Handle))):
                raise TypeError('Invalid Object of type:'+ type(handle)+". Please use a correct Aurora.Handle Object.")

        cmd = 'PINIT '+handle.ID+'\r'
        print("Initialize Handle " + handle.ID)

        #Könnte Fehler werfen??
        self.ser.write(cmd.encode())
        time.sleep(0.6)
        self.readSerial()

    def pena(self,handle,mode):
        penamodes = 'SDB'
        if ((not (isinstance(mode,str) and len(mode)==1))and mode.upper() not in penamodes ):
            raise ValueError("Please choose mode between: 'S','D' or 'B'.")
        if (not(isinstance(handle,Handle))):
            raise TypeError('Invalid Object of type:'+ type(handle)+". Please use a correct Handle Object.")

        cmd = 'PENA '+handle.ID+mode.upper()+'\r'
        print("Activates Handle " + handle.ID+" using mode:\""+mode+"\"")

        #Könnte Fehler werfen??
        self.ser.write(cmd.encode())
        self.readSerial()

    def pdis(self, option=None):
        return

    def phsr(self, option=0):
        
        option = int(option)
        if (not (0 <= option < 5)): 
            raise ValueError("Invalid Parameter: Please choose a value between 0-4. Not 00-04")  
        
        cmd ='PHSR 0'+str(option)+'\r'
        
        self.ser.write(cmd.encode())
        phsr_string = self.readSerial().decode()

        if (phsr_string.startswith("ERROR")):
            raise Warning("PHSR was unsuccessful. Please initialize the System properly.")
        
        return phsr_string


    def sflist(self, option=None):
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


    def tstart(self,option=None):

        if (option==None):
            cmd = 'TSTART \r'
        else:
            option = int(option)
            if ((option!=40 or option!=80)): 
                raise ValueError("Invalid Parameter: Please choose value 40 or 80")           
            cmd = 'TSTART '+str(option)+'\r'

        self.ser.write(cmd.encode())
        time.sleep(1.8)
        self.readSerial()

    def tstop(self):
        self.ser.write( b'TSTOP \r')
        time.sleep(0.5)
        self.readSerial()


    def tx(self, option=None):

        if(option == None):
            self.ser.write(b'TX \r')
        else:
            if ((option!='0001' or option!='0800')): 
                raise ValueError("Invalid Parameter: Please choose value 0001 or 0800") 
            cmd = 'TX '+str(option)+'\r'
            self.ser.write(cmd.encode())

        tx_str = self.readSerial().decode()

        return tx_str



    #NDI Aurora Ergänzungsmethoden
    def resetandinitSystem(self):
        self.reset()
        self.init()
    
    #SerialMethods ------------------------
    #Optional Feature Einbau der CRC Message, Gen + Check sinnvoll.
    def readSerial(self,expected=b'\r'):
        out = ''
        time.sleep(self.readsleep)
        out = self.ser.read_until(expected)
                
        try:
            self.checkAuroraError(out)
        except Warning as w:
            print(w)
                
        
        print(out)
        return out


    def checkAuroraError(self,msg):

        if (not msg.startswith(b'ERROR')):
            return
        else:
            #Strip Message Into the 
            msg = msg.decode()
            errcode = msg[5:7]

        errmsg = self.getAuroraErrormessage(errcode)
        exceptmsg = f'ERRCODE {errcode}: {errmsg}'
        #Aurora Exception erstellen!
        raise Warning(exceptmsg)


    def getAuroraErrormessage(self,errorcode):

        AuaErrorDict = {
            '01': 'Invalid command.',
            '02': 'Command too long.',
            '03': 'Command too short.',
            '04': 'Invalid CRC calculated for command; calculated CRC does not match the one sent.',
            '05': 'Time-out on command execution.',
            '06': 'Unable to set up new communication parameters. This occurs if one of the communication parameters is out of range.',
            '07': 'Incorrect number of parameters.',
            '08': 'Invalid port handle selected.',
            '09': 'Invalid mode selected. Either the tool tracking priority is out of range, or the tool has sensor coils defined and ‘button box’ was selected',
            '0A': 'Invalid LED selected. The LED selected is out of range.',
            '0B': 'Invalid LED state selected. The LED state selected is out of range.',
            '0C': 'Command is invalid while in the current operating mode.',
            '0D': 'No tool is assigned to the selected port handle.',
            '0E': 'Selected port handle not initialized. The port handle needs to be initialized before the command is sent.',
            '0F': 'Selected port handle not enabled. The port handle needs to be enabled before the command is sent.',    
            '10': 'System not initialized. The system must be initialized before the command is sent.',
            '11': 'Unable to stop tracking. This occurs if there are hardware problems. Please contact NDI.',
            '12': 'Unable to stop tracking. This occurs if there are hardware problems. Please contact NDI.',
            '13': 'Unable to initialize the port handle.',
            '14': 'Invalid Field Generator characterization parameters or incompatible hardware',
            '15': 'Invalid command',
            '16': 'Invalid command',
            '17': 'Invalid command',
            '18': 'Invalid command',
            '19': 'Invalid command',
            '1A': 'Invalid command'
            #REST TBD !!!!
            }

        #Check for Reserved Error Codes 
        #Reserved Error Codes are in hexadecimal, but for Coding purpose it is translated to integer. 
        #18,1B,1C,26-28,2F-30,34-C1,C5-F3,F7-FF

        int_errorcode = int(errorcode,16)
    
        reserved_codes =[24,27,28,range(38,41),range(47,49),range(52,194),range(197,244),range(247,256)]
        for res_code in reserved_codes:
            if type(res_code) is range:
                if(int_errorcode in res_code): 
                    return 'Reserved.'        
            elif int_errorcode is res_code:
                return 'Reserved.'

        return AuaErrorDict.get(errorcode,'ERROR CODE NOT FOUND. PLEASE CONTACT YOUR ADMINISTRATOR! Either not implemented or Unknown')

    

    def getSerial(self):
        return self.ser



class HandleManager:
   
    def __init__(self, phsr ):
        #01 0A 00D 2674\r als antwort
        #01 0A 00 001 74\r keine Handles 

        self.handles = {}
        self.num_handles = int(phsr[0:2])
        phsr = phsr[2:]
       
        while len(self.handles) != self.num_handles:
           
            # ID und Status 
            h_id = phsr[0:2]
            h_state = phsr[2:5]
            h = Handle(h_id,h_state)

            #Verwendete Daten from Inputstring entfernen 
            phsr = phsr[5:]
            self.handles[h_id] = h

    def getNum_Handles(self):
        return self.num_handles
    
    def getHandles(self):
        return self.handles

    def updateHandles(self,tx_str):
        #expects the outpout from tx decoded tx string. 
        #SYSTEMSTATUS TO BE DONE!
        #b'020A+06975+04593-00366-05486-007807-007185-015834+003950002003D000003E8\n0B+08324+03951+03881+00150+011264-001768-017704+006430002003F000003E8\n0000DA87\r'
        #b'020A+06972+04598-00378-05486-007800-007179-015834+003950002003D00003048\n0BMISSING 0002003F 00003048\n0000C84C\r'
        #b'01 0A +0.6391 +0.4357 -0.1303 -0.6201    -0071.88 -0076.86 -0160.67   +0.0326 0002003D 00000690 \n 
        # 0000 9F29\r'
        #id+  q0+qx+qy+qz    tx+ty+tz +error/indicatorvalue +       port status + framestatus     (systemstatus+crc)
                #2+   6+6+6+6             +7+7+7+6                                    8+8


        num = int(tx_str[0:2],16)
        if (self.num_handles != num ):
            print("Uneven nums OMFG")
        self.num_handles = num
        tx_str = tx_str[2:]
        
        #Split Message into Handles and System States
        tx_str = tx_str.splitlines()

        #extract Systeminfo and clean it afterwards
        sys_status, crc = tx_str[-1][:4],tx_str[-1][4:]
        tx_str.pop()
        
        for handle in tx_str:
            h_id = handle[0:2]
            new_handle = self.handles[h_id]

            handle = handle[2:]

            if (handle.startswith("MISSING")):
                handle = handle[7:]
                port_state = handle[0:8]
                frame_id = handle[8:]
                new_handle.setTXData(MISSING=True,port_state=port_state,frame_id=frame_id)

            else:
                Q0 = float(self.insert_separator(handle[0:6],2))
                Qx = float(self.insert_separator(handle[6:12],2))
                Qy = float(self.insert_separator(handle[12:18],2))
                Qz = float(self.insert_separator(handle[18:24],2))
                Tx = float(self.insert_separator(handle[24:31],5))
                Ty = float(self.insert_separator(handle[31:38],5))
                Tz = float(self.insert_separator(handle[38:45],5))
                calc_Err = float(self.insert_separator(handle[45:51],2))
                port_state = handle[51:59]
                frame_id = handle[59:67]

                new_handle.setTXData(False,Q0, Qx, Qy, Qz,Tx,Ty,Tz,calc_Err,port_state,frame_id)
            
            self.handles[h_id] = new_handle
        

    def insert_separator(self, string, index):
        return string[:index] + '.' + string[index:]



class Handle:

    def __init__(self, ID, state):
        
        #Handle Data
        self.ID = ID
        self.handle_state = state
        self.refname = "Strenum bspw."

        #Transformation Data
        self.MISSING = False

        self.Q0 = None
        self.Qx = None
        self.Qy = None
        self.Qz = None
        self.Tx = None
        self.Ty = None
        self.Tz = None
        self.Err = None

        self.port_state = None
        self.frame_id = None


        
    def setTXData(self,MISSING = False, Q0=None,Qx=None,Qy=None,Qz=None,Tx=None,Ty=None,Tz=None,calc_Err=None,port_state=None,frame_id=None):
        self.MISSING = MISSING       
        self.Q0 = Q0
        self.Qx = Qx
        self.Qy = Qy
        self.Qz = Qz
        self.Tx = Tx
        self.Ty = Ty
        self.Tz = Tz
        self.calc_Err = calc_Err
        self.port_state = port_state
        self.frame_id = frame_id


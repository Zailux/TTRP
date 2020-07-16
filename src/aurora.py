"""
The aurora module, is a python implementation of
NDI Aurora System API Revision 4. The guide is in the docs accessable.

Supported NDI API Version:
    Combined Firmware Revision: 011

Classes
    Aurora
        The main class of the API, utiilzes pyserial (3.4) in order to
        communicate with the Aurora System. Most of the basic available commands
        are implemented, based on the Aurora_API_Guide_v4.
    Handlemanager
        The Handlemanager is an optional object, which can be used to
        keep track of the current state of the Aurora System. It provides
        methods to get state of the system and it can hold the current
        handle data.
    Handle
        Represents the data model of an handle. This object can be used, to
        access the handle data more consistently.
"""

__version__ = '0.1'
__author__ = 'Bach, Thanh Nam; Baader, Tobias'

import functools
import logging
import threading
import time
from copy import copy, deepcopy
from decimal import Decimal
import struct
import serial

from bitstring import BitArray, Bits

SYSMODES = ['SETUP', 'TRACKING']


class Aurora:

    def __init__(self, ser, debug_mode=False):
        # Aurora System relevant Attributes
        self._lock = threading.Lock()
        self._observers = {}

        self.readsleep = 0
        self.sysmode = None
        # registered Methods !

        # validate Serial Objecttype and open Serialport
        if not isinstance(ser, serial.serialwin32.Serial):
            raise TypeError(
                'Invalid Object type of: ' +
                type(ser) +
                " was used. Please use pySerial Object")

        self.ser = ser
        if(self.ser.isOpen()):
            self.ser.close()
        self.ser.open()
        logging.info("Sucessfully opened Port: " + self.ser.name)

        logging.info("Try Reading APIREV Aurora System")
        with self._lock:
            if (len(self.apirev()) == 0):
                raise Warning(
                    ("Empty Return Message during Initilization. "
                     "Please ensure that the system is properly "
                    f"connected at {self.ser.name} and turned on."))

    # Observer Pattern - Add Observer Method / Callback Method
    def register(self, key, observer):
        '''Implementation of observer pattern.
        Observers can register methods for a callback. The key should be
        the Aurora methodname.
        '''
        key = str(key)
        if (key not in self._observers):
            self._observers[key] = []
            self._observers[key].append(observer)
        elif(observer not in self._observers[key]):
            self._observers[key].append(observer)
        else:
            raise Warning(
                f"Observermethod: {observer} for Key {key} already exists")

    def __callback(self, key):
        """Calls the observers methods, based on the methodkey of Aurora method."""
        key = str(key)
        if (key in self._observers):
            logging.debug(
                f'{self.__class__}: Callback for "{key}" - {self._observers[key]}')
            for observer_method in self._observers[key]:
                observer_method()

    def get_sysmode(self):
        return self.sysmode

    def set_sysmode(self, mode):
        if (mode not in SYSMODES):
            raise ValueError(
                "Invalid Value. Value must be in " +
                str(SYSMODES))
        self.sysmode = mode

        self.__callback(key='set_sysmode')

    # Debug & Additional Methods
    # Commands & Parameters are not case sensitive
    def write_cmd(self, cmd, expect=False):
        # Validate input
        try:
            if (not isinstance(cmd, str)):
                raise TypeError(
                    "The Objecttype of: " +
                    type(cmd) +
                    " is invalid. Please use a String for the command.")
            if (cmd.rstrip() == ""):
                raise ValueError(
                    "The command is empty. Please type a valid commandstring.")
        except ValueError as e:
            logging.exception(str(e))
            return
        except TypeError as e:
            logging.exception(str(e))
            return

        # Removes trailing Space
        cmd = cmd.rstrip()

        # adds SPACE if no parameter
        if (cmd.find(' ') == -1):
            cmd = cmd + ' \r'

        else:
            if(cmd.find(' ') != cmd.rfind(' ')):
                logging.warning(
                    "The command contains two spaces. Is the command correct?")
            cmd = cmd + '\r'

        cmd = cmd.encode()

        # Executes the given command and reads it
        with self._lock:
            self.ser.write(cmd)
            if (expect is not False):
                self.read_serial(expected=expect)
            else:
                self.read_serial()

    # ----------------------------- #
    # ---- NDI Aurora Methods  ---- #
    # ----------------------------- #

    def apirev(self):
        self.ser.write(b'APIREV \r')
        return self.read_serial()

    def beep(self, num):
        try:
            num = int(num)
            if (not (0 < num < 10)):
                raise ValueError(
                    "Invalid Parametervalue: Please choose a value between 1-9")
            cmd = 'BEEP ' + str(num) + '\r'
            self.ser.write(cmd.encode())
            # time.sleep(1)
            self.read_serial()
        except ValueError as e:
            logging.exception(str(e))

    def init(self):
        self.ser.write(b'INIT \r')
        if (self.read_serial().startswith(b'OKAY')):
            self.set_sysmode('SETUP')

    def get(self, attr=None):
        pass
        return

    def reset(self):
        self.ser.write(b'RESET \r')
        msg = self.read_serial()
        if (msg.startswith(b'RESET') or msg.startswith(b'OKAY')):
            self.set_sysmode('SETUP')

    def pinit(self, handle):

        if (not(isinstance(handle, Handle))):
            raise TypeError(f'Invalid Object of type: {type(handle)}. \
                            Please use a correct Aurora.Handle Object.')

        cmd = 'PINIT ' + handle.ID + '\r'
        logging.info("Initialize Handle " + handle.ID)

        # Könnte Fehler werfen??
        self.ser.write(cmd.encode())
        time.sleep(0.7)
        self.read_serial()

    def pena(self, handle, mode):
        penamodes = 'SDB'
        if ((not (isinstance(mode, str) and len(mode) == 1))
                and mode.upper() not in penamodes):
            raise ValueError("Please choose mode between: 'S','D' or 'B'.")
        if (not(isinstance(handle, Handle))):
            raise TypeError(
                'Invalid Object of type:' +
                type(handle) +
                ". Please use a correct Handle Object.")

        cmd = 'PENA ' + handle.ID + mode.upper() + '\r'
        logging.info(
            "Activates Handle " +
            handle.ID +
            " using mode:\"" +
            mode +
            "\"")

        # Könnte Fehler werfen??
        self.ser.write(cmd.encode())
        self.read_serial()

    def pdis(self, option=None):
        return

    def phsr(self, option=0):

        option = int(option)
        if (not (0 <= option < 5)):
            raise ValueError(
                "Invalid Parameter: Please choose a value between 0-4. Not 00-04")

        cmd = 'PHSR 0' + str(option) + '\r'

        self.ser.write(cmd.encode())
        phsr_string = self.read_serial().decode()

        if (phsr_string.startswith("ERROR")):
            raise Warning(
                "PHSR was unsuccessful. Please initialize the System properly.")

        return phsr_string

    def sflist(self, option=None):
        option = int(option)

        if (option is not None):
            cmd = 'TSTART \r'
        elif ((option != 40 or option != 80)):
            raise ValueError("Invalid Parameter: Please choose value 40 or 80")
        else:
            cmd = 'TSTART ' + str(option) + '\r'

        self.ser.write(cmd)
        time.sleep(1)
        self.read_serial()

    def tstart(self, option=None):

        if (option is None):
            cmd = 'TSTART \r'
        else:
            option = int(option)
            if ((option is 40 or option is 80)):
                cmd = 'TSTART ' + str(option) + '\r'
            else:
                raise ValueError(
                    "Invalid Parameter: Please choose value 40 or 80")

        self.ser.write(cmd.encode())
        time.sleep(1.8)
        if (self.read_serial().startswith(b'OKAY')):
            self.set_sysmode('TRACKING')

    def tstop(self):
        self.ser.write(b'TSTOP \r')
        time.sleep(0.7)

        if (self.read_serial().startswith(b'OKAY')):
            self.set_sysmode('SETUP')

    def bx(self, option=None):
        if(option == None):
            self.ser.write(b'BX \r')
        else:
            print("No Options implemented for BX!")

        header_bytes = self.readSerialByteCode(7)
        repl_length = int.from_bytes(header_bytes[2:4], 'little')
        rest_length = repl_length+1
        rest = self.readSerialByteCode(rest_length)
        return header_bytes, rest

    def readSerialByteCode(self, length):
        out = self.ser.read(length)
        return out

    def tx(self, option=None):

        if(option is None):
            self.ser.write(b'TX \r')
        else:
            if ((option != '0001' or option != '0800')):
                raise ValueError(
                    "Invalid Parameter: Please choose value 0001 or 0800")
            cmd = 'TX ' + str(option) + '\r'
            self.ser.write(cmd.encode())

        tx_str = self.read_serial(to_log=False).decode()

        return tx_str

    # ---------------------------------------- #
    # ---- NDI Aurora Additional Methods  ---- #
    # ---------------------------------------- #

    def reset_and_init_system(self):
        self.reset()
        self.init()

    # Optional Feature Einbau der CRC Message, Gen + Check sinnvoll.
    def read_serial(self, expected=b'\r', to_log=True):
        out = ''
        time.sleep(self.readsleep)
        out = self.ser.read_until(expected)

        try:
            self.check_aurora_error(out)
        except Warning as w:
            logging.warning(w)

        if (to_log):
            logging.info(out)
        return out

    def check_aurora_error(self, msg):

        if (not msg.startswith(b'ERROR')):
            return
        else:
            # Strip Message Into the
            msg = msg.decode()
            errcode = msg[5:7]

        errmsg = self.get_aurora_errormsg(errcode)
        exceptmsg = f'ERRCODE {errcode}: {errmsg}'
        # Aurora Exception erstellen!
        raise Warning(exceptmsg)

    def get_aurora_errormsg(self, errorcode):

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
            # TODO not all Commands are maintained yet.
        }

        # Check for Reserved Error Codes
        # Reserved Error Codes are in hexadecimal, but for Coding purpose it is translated to integer.
        # 18,1B,1C,26-28,2F-30,34-C1,C5-F3,F7-FF

        int_errorcode = int(errorcode, 16)

        reserved_codes = [
            24, 27, 28, range(
                38, 41), range(
                47, 49), range(
                52, 194), range(
                    197, 244), range(
                        247, 256)]
        for res_code in reserved_codes:
            if isinstance(res_code, range):
                if(int_errorcode in res_code):
                    return 'Reserved.'
            elif int_errorcode is res_code:
                return 'Reserved.'

        return AuaErrorDict.get(
            errorcode,
            'ERROR CODE NOT FOUND. PLEASE CONTACT YOUR ADMINISTRATOR! Either not implemented or Unknown')

# Maybe make it a singleton and also enable to version to run Aua API
# either auto update the HM oder not.


class HandleManager:

    def __init__(self, phsr):
        # 01 0A 00D 2674\r als antwort
        # 01 0A 00 001 74\r keine Handles
        self._hmlock = threading.Lock()
        self.handles = {}
        self.num_handles = int(phsr[0:2])
        phsr = phsr[2:]

        while len(self.handles) != self.num_handles:

            # ID und Status
            h_id = phsr[0:2]
            h_state = phsr[2:5]
            h = Handle(h_id, h_state)

            # Verwendete Daten from Inputstring entfernen
            phsr = phsr[5:]
            self.handles[h_id] = h

    def get_numhandles(self):
        return self.num_handles

    def get_handles(self, real_copy=False):
        with self._hmlock:
            return self.handles if not real_copy else deepcopy(self.handles)

    def get_missing_handles(self):
        misshandles = []
        h = self.get_handles()
        for h_id, handle in h.items():
            if (handle.MISSING):
                misshandles.append(h_id)
        return misshandles

    def update_handlesBX(self, bx_header, bx_data):
        #print(len(bx_header))
        #print(len(bx_data))
        #
        ''' <Reply Option 0001 Data> = <Q0><Qx><Qy><Qz><Tx><Ty><Tz><Indicator Value>
            <Port Status><Frame Number>
            or
            <Reply Option 0001 Data> = <Port Status><Frame Number>

        42 Byte vollständiger Handle. Ansonsten 10 Byte der Handle
        '''

        # header
        start_seq = int.from_bytes(bx_header[0:2], 'little')
        repl_length = int.from_bytes(bx_header[2:4], 'little')
        crc = bx_header[4:6]
        n_handles = int.from_bytes(bx_header[6:7], 'little')

        #print("Handles: " + str(n_handles))
        #print("repl_length: " + str(repl_length))


        handle_bytes = []
        VALID, MISSING, DISABLED = [1,2,4] #Handle Status Values
        index = 0
        for i in range(n_handles):
            #handle_bytes = bx_data[i*42:(i*42)+42]
            handle_bytes = bx_data[index:index+2]
            h_id_int = handle_bytes[0]
            h_id = ''
            if (h_id_int == 10):
                h_id = '0A'
            elif (h_id_int == 11):
                h_id = '0B'
            elif (h_id_int == 12):
                h_id = '0C'
            elif (h_id_int == 13):
                h_id = '0D'
            new_handle = self.handles[h_id]

            #print(int.from_bytes(h_id, 'little'))
            handle_status =BitArray(handle_bytes[1:2]).int
            index+=2

            if (handle_status == VALID):
                is_missing=False
                handle_data_bytes = bx_data[index:index+32]
                Q0, =  struct.unpack('<f', handle_data_bytes[0:4])
                Qx, =  struct.unpack('<f', handle_data_bytes[4:8])
                Qy, =  struct.unpack('<f', handle_data_bytes[8:12])
                Qz, =  struct.unpack('<f', handle_data_bytes[12:16])
                Tx, =  struct.unpack('<f', handle_data_bytes[16:20])
                Ty, =  struct.unpack('<f', handle_data_bytes[20:24])
                Tz, =  struct.unpack('<f', handle_data_bytes[24:28])
                calc_Err = struct.unpack('<f', handle_data_bytes[28:32])

                index += 32
            elif handle_status in [MISSING, DISABLED]:
                is_missing=True

            handle_bytes = bx_data[index:index+8]
            port_state = handle_bytes[0:4]
            frame_id = self._hex_to_string(handle_bytes[4:8])
            index +=8

            if (handle_status == VALID):
                new_handle.set_tx_data(is_missing, Q0, Qx, Qy, Qz, Tx, Ty, Tz,
                                        calc_Err, port_state, frame_id)
            elif handle_status in [MISSING, DISABLED]:
                new_handle.set_tx_data(MISSING=is_missing, port_state=port_state, frame_id=frame_id)
            else:
                logging.error("Error. Please Debug this issue")
            self.handles[h_id] = new_handle

        return False if len(bx_data) < (42*n_handles) else True

    def _hex_to_string(self, hex_val):
        #Example input b'\x90G\x00\x00' ^= 90470000
        hex_val = str(BitArray(hex_val).hex).upper()

        return hex_val

    def update_handles(self, tx_str):
        # expects the outpout from tx decoded tx string.
        # SYSTEMSTATUS TO BE DONE!
        # b'020A+06975+04593-00366-05486-007807-007185-015834+003950002003D000003E8\n0B+08324+03951+03881+00150+011264-001768-017704+006430002003F000003E8\n0000DA87\r'
        #b'020A+06972+04598-00378-05486-007800-007179-015834+003950002003D00003048\n0BMISSING 0002003F 00003048\n0000C84C\r'
        # b'01 0A +0.6391 +0.4357 -0.1303 -0.6201    -0071.88 -0076.86 -0160.67   +0.0326 0002003D 00000690 \n
        # 0000 9F29\r'
        # id+  q0+qx+qy+qz    tx+ty+tz +error/indicatorvalue +       port status + framestatus     (systemstatus+crc)
        # 2+   6+6+6+6             +7+7+7+6
        # 8+8

        # STILL BUGGY TX_STR can contain disabled handles !!!
        # wee need to validate handles or rather the tx_str

        num = int(tx_str[0:2], 16)
        if (self.num_handles != num):
            logging.critical(
                f"Critical Issue - Wrong InputString tx_str: {tx_str}")
        self.num_handles = num
        tx_str = tx_str[2:]

        # Split Message into Handles and System States
        tx_str = tx_str.splitlines()

        # extract Systeminfo and clean it afterwards
        sys_status, crc = tx_str[-1][:4], tx_str[-1][4:]
        tx_str.pop()

        with self._hmlock:
            for handle in tx_str:
                h_id = handle[0:2]
                new_handle = self.handles[h_id]
                handle = handle[2:]

                if (handle.startswith("MISSING")):
                    handle = handle[7:]
                    port_state = handle[0:8]
                    frame_id = handle[8:]
                    new_handle.set_tx_data(
                        MISSING=True, port_state=port_state, frame_id=frame_id)

                else:
                    Q0 = self._string2dec(handle[0:6], 2)
                    Qx = self._string2dec(handle[6:12], 2)
                    Qy = self._string2dec(handle[12:18], 2)
                    Qz = self._string2dec(handle[18:24], 2)
                    Tx = self._string2dec(handle[24:31], 5)
                    Ty = self._string2dec(handle[31:38], 5)
                    Tz = self._string2dec(handle[38:45], 5)
                    calc_Err = self._string2dec(handle[45:51], 2)
                    port_state = handle[51:59]
                    frame_id = handle[59:67]

                    new_handle.set_tx_data(
                        False,
                        Q0,
                        Qx,
                        Qy,
                        Qz,
                        Tx,
                        Ty,
                        Tz,
                        calc_Err,
                        port_state,
                        frame_id)

                self.handles[h_id] = new_handle

    def _string2dec(self, string, separator_index, round_to=4):
        s = string[:separator_index] + '.' + string[separator_index:]
        f = round(Decimal(s), round_to)
        return f

# TODO empty class for interpreting Port bits. Not integrated yet
class Port():
    def __init__(self):
        self.OCCUPIED = None
        self.GPIO_1 = None
        self.GPIO_2 = None
        self.GPIO_3 = None
        self.INITIALIZED = None
        self.ENABLE = None
        self.OUT_OF_VOLUME = None
        self.PARTIALLY_OUT_OF_VOLUME = None
        self.BROKEN_SENSOR = None
        self.PROCESS_EXCEPTION = None

    def from_string(self, string):
        pass

    def from_bitarray(self, bit_array):
        # Expect an Bitarray. From DB it can be created like BitArray(b'?\x00\x02\x00').bin
        self.OCCUPIED = bit_array[0]
        self.GPIO_1 = bit_array[1]
        self.GPIO_2 = bit_array[2]
        self.GPIO_3 = bit_array[3]
        self.INITIALIZED = bit_array[4]
        self.ENABLE = bit_array[5]
        self.OUT_OF_VOLUME = bit_array[6]
        self.PARTIALLY_OUT_OF_VOLUME = bit_array[7]
        self.BROKEN_SENSOR = bit_array[8]
        self.PROCESS_EXCEPTION = bit_array[11]


class Handle:

    def __init__(
            self,
            ID,
            handle_state,
            refname='DEFAULT',
            MISSING=None,
            Q0=None,
            Qx=None,
            Qy=None,
            Qz=None,
            Tx=None,
            Ty=None,
            Tz=None,
            calc_Err=None,
            port_state=None,
            frame_id=None):

        # Handle Data
        self.ID = ID
        self.handle_state = handle_state
        self.refname = refname

        # Transformation Data
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

    def __copy__(self):
        cls = self.__class__
        copy_handle = cls.__new__(cls)
        copy_handle.__dict__.update(self.__dict__)
        return copy_handle

    def get_trans_data(self):
        ''' Return Translational Data as list x,y,z in mm'''
        return [self.Tx, self.Ty, self.Tz]

    def get_orient_data(self):
        ''' Return Translational Data as list Q0,Qx,Qy,Qz in quarternion'''
        return [self.Q0, self.Qx, self.Qy, self.Qz]

    def set_reference_name(self, refname):
        if (isinstance(refname, str)):
            self.refname = refname
        else:
            raise TypeError("The parameter type must be String")

    def set_tx_data(
            self,
            MISSING=False,
            Q0=None,
            Qx=None,
            Qy=None,
            Qz=None,
            Tx=None,
            Ty=None,
            Tz=None,
            calc_Err=None,
            port_state=None,
            frame_id=None):
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

    # obsolete there is a standard __dict__ attribute for every object in
    # python. 7
    '''
    def to_dict(self):

        h_dict = {
            'ID' : self.ID,
            'handle_state' : self.handle_state,
            'refname' : self.refname,
            'MISSING' : self.MISSING,
            'Q0' : self.Q0,
            'Qx' : self.Qx,
            'Qy' : self.Qy,
            'Qz' : self.Qz,
            'Tx' : self.Tx,
            'Ty' : self.Ty,
            'Tz' : self.Tz,
            'calc_Err' : self.calc_Err,
            'port_state' : self.port_state,
            'frame_id' : self.frame_id
        }

        return h_dict
    '''

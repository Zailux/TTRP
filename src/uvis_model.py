"""This is the Uvis Model module.

This module contains the following classes:
    UltraVisModel
        The main class of this module, which provides
        methods to access the data / model of the uvis application.
    Examination
        The model of the examination / Untersuchung. Contains
        information about the doctor, patient etc.
    Record
        Represent a record / Aufzeichnung, of an examination.
        Contains the image and the reference to the positional
        data of an record.
"""

import logging
import sys
import uuid

import pandas as pd
import PIL

#sys.path.insert(1, '..\\')
from src.aurora import Handle
from src.config import Configuration
from src.helper import Helper

global hp
global _cfg
hp = Helper()
_cfg = Configuration()


class UltraVisModel:
    """ The UltraVisModel class provides
        methods to access the data / model of the uvis application.
        It is primarily for reading and saving data from the csv tables.
        As for a more handy accessability, the model maintains the application
        data in a "workitem". A dict, which consolidates the Examination, Records
        and Handles in one object.
        Via an observer pattern, the model triggers a callback to
        the corresponding methods in the controller (caller).
    """
    def __init__(self):
        datapath = _cfg.DATAPATH
        self.EXAMINATION_PATH = datapath+'examination.csv'
        self.RECORDS_PATH = datapath+'record.csv'
        self.HANDLE_PATH = datapath+'handles.csv'
        try:
            self.t_examination = pd.read_csv(self.EXAMINATION_PATH, index_col=0)
            self.t_records = pd.read_csv(self.RECORDS_PATH, index_col=0)
            self.t_handles = pd.read_csv(self.HANDLE_PATH, index_col=0)
        except FileNotFoundError as e:
            logging.error(e)
            #disable saving functions!
        self._observers = {}
        self._curr_workitem = {"Examination":None, "Records":[], "Handles":[]}

    def register(self, key, observer):
        """Implementation of observer pattern.
        Observers can register methods for a callback. The key should be
        the UltraVisModel methodname.
        """
        key = str(key)
        if (key not in self._observers):
            self._observers[key] = []
            self._observers[key].append(observer)
        elif(observer not in self._observers[key]):
            self._observers[key].append(observer)
        else:
            raise Warning(f"Observermethod: {observer} for Key {key} already exists")

    def __callback(self, key):
        """Calls the observers methods, based on the methodkey of UltraVisModel method."""
        key = str(key)
        if (key in self._observers):
            logging.debug(f'{self.__class__}: Callback for "{key}" - {self._observers[key]}')
            for observer_method in self._observers[key]:
                observer_method()

    def clear_current_workitem(self):
        """ Clears the _curr_workitem dictionary and reset its values to a
        clean state {"Examination":None, "Records":[], "Handles":[]}.
        """
        self._curr_workitem.clear()
        self._curr_workitem = {"Examination":None, "Records":[], "Handles":[]}

    def get_current_workitem(self):
        """ Return the current workitem """
        return self._curr_workitem

    def get_length_workitem(self):
        # Might be length of workitem in the future, if I make it as a class
        # len(workitem) or something should do it.
        itemcount = 0
        exam, records, handles = self.get_current_workitem().values()
        itemcount += 1 if exam is not None else 0
        itemcount += len(records)
        itemcount += len(handles)

        return itemcount

    # handling von gruppe von objekten. Ggf. ist das auch einfach
    # über n Selekt auf Basis der Examination ID möglich
    # loadWorkitem is inefficient. It would be better if this methods gets the E_ID and
    # then tries to find all corresponding data (records & handles) and then refreshes just once afterwards
    def set_current_workitem(self, obj, as_instance=True):
        """Set the current workitem for the UvisModel.
        You can either set single instances of an Examination Object, Record Object
        or a Position (a list object with 4 Handle Objects).
        Alternatively you can set a whole workitem, as a tuple (Examination, [Record,...], [Handle,...]).
        """
        if (as_instance):
            item = obj
            if (isinstance(item, Examination)):
                self._curr_workitem["Examination"] = item
            elif (isinstance(item, Record)):
                self._curr_workitem["Records"].append(item)
            elif (all(isinstance(h, Handle) for h in obj)):
                self._curr_workitem["Handles"].append(item)
            else:
                raise TypeError(f'{type(obj)} is not correct')
        elif (not as_instance):
            # expect a tuple of the full workitem
            exam, records, positions = obj
            if (not isinstance(exam, Examination) or
                not all(isinstance(rec, Record) for rec in records) or
                not all(isinstance(handle, Handle) for handle in positions)):

                self._curr_workitem["Examination"] = exam
                self._curr_workitem["Records"] = records
                self._curr_workitem["Handles"] = positions
            else:
                raise TypeError(f'The workitem tuple {obj} contains items which are not of Type {Examination}, {Record} or {Handle}.')

        self.__callback(key="set_current_workitem")

    def persist_workitem(self):
        """Persists Workitem.
        For each item (an Examination, Record or Handle) of the workitem,
        the method gets the next ID in the table via _getnextID
        and tries to save the changes in the local dataframe (self.t_examination e.g.).
        If everything works, it persists the changes in the csv files.

        At success the method return the new E_ID as a string.
        """
        exam,records,handles = self.get_current_workitem().values()

        #persist ExamID
        old_E_ID = exam.E_ID
        num = self._getnextID(df=self.t_examination)
        new_E_ID = 'E-'+str(num) if str(old_E_ID).startswith('temp') else old_E_ID
        exam_index = self.t_examination.index.tolist()
        idx = exam_index.index(old_E_ID)
        exam_index[idx] = new_E_ID
        self.t_examination.index = exam_index

        # Persist Records
        df = self.t_records
        df['E_ID'].where(df['E_ID'] != old_E_ID,new_E_ID,True)
        for i,rec in enumerate(records):
            old_R_ID = rec.R_ID
            new_index = self._getnextID(df)
            new_R_ID = 'R-'+str(new_index) if str(old_R_ID).startswith('temp') else old_R_ID
            as_list = df.index.tolist()
            idx = as_list.index(old_R_ID)
            as_list[idx] = new_R_ID
            df.index = as_list

            #Persist corresponding Position
            df2 = self.t_handles
            df2['R_ID'].where(df2['R_ID'] != old_R_ID,new_R_ID,True)
            if old_R_ID != new_R_ID:
                logging.debug(f'Replaced tempID: {old_R_ID} with new ID: {new_R_ID} \
                                (in Records and Handles Table)')

        #write changes to tables
        self.t_examination.to_csv(self.EXAMINATION_PATH)
        self.t_records.to_csv(self.RECORDS_PATH)
        self.t_handles.to_csv(self.HANDLE_PATH)

        return new_E_ID

    def load_workitem(self, E_ID):
        """Loads the workitem based on the examination id (E_ID).
        The workitem can be accessed via get_current_workitem.
        """
        exam = self.get_examination(ID=E_ID)
        records = []
        positions = []

        if not exam:
            logging.error(f"Can't load Examination with {E_ID}")
            return

        records = self.get_record(E_ID=E_ID)
        for rec in records:
            R_ID = rec.R_ID
            pos = self.get_position(R_ID)
            positions.append(pos)

        self.clear_current_workitem()
        workitem = (exam,records,positions)

        self.set_current_workitem(workitem, as_instance=False)

    #für Examination & Record. Über vererbung lösen auch möglich.
    def _getnextID(self,df):
        indexlist = df.index.tolist()
        length = []

        for i, ID in enumerate(indexlist):
            if (not str(ID).startswith('temp')):
                length.append(ID)
        next_id = len(length)
        return next_id

    def get_examination(self, ID=None):
        """Return an Examination Object from the csv. Else it returns None."""
        E_ID = str(ID)
        try:
            e = self.t_examination.loc[E_ID]
            examination = Examination(
                E_ID=E_ID, doctor=e.doctor, patient=e.patient,
                examitem=e.examitem, created=e.created)
            return examination

        except KeyError as e:
            logging.debug(str(e))
            logging.error(f'Record with key "{E_ID}" could not be found.')
            return None

    def save_examination(self, examination, persistant=False):
        """Saves a temporary Instance of an Examination Object to the csv."""
        if (not(isinstance(examination,Examination))):
            raise TypeError(f'Invalid Object of type: {type(examination)}". \
                              Please use a correct {Examination} Object.')
        logging.debug('Trying to write data:')

        if (persistant):
            '''
            as_list = df.index.tolist()
            idx = as_list.index('Republic of Korea')
            as_list[idx] = 'South Korea'
            df.index = as_list
            ''' #here kommt noch was
            pass
        exam = examination.__dict__
        df = pd.DataFrame(data=exam,index=[0])
        df = df.set_index('E_ID')
        logging.debug(df)
        try:
            new_exam = self.t_examination.append(df,verify_integrity=True)
            new_exam.to_csv(self.EXAMINATION_PATH)
            self.t_examination = new_exam
        except ValueError as e:
            logging.error("Could not save record. Errormsg - "+str(e))
            raise ValueError(str(e))
        logging.info("Succesfully saved record "+str(exam["E_ID"]))

    def get_record(self, R_ID=None, E_ID=None):
        """Returns an Record object or Record object list from the csv.
        Get corresponding Records via the E_ID or a specific instance via R_ID.
        If it can't find an object the method returns None.
        """
        if (R_ID is not None and E_ID is not None):
            raise ValueError('Either use R_ID or E_ID not both parameters')

        if R_ID is not None:
            R_ID = str(R_ID)
            try:
                r = self.t_records.loc[R_ID]
                rec = Record(R_ID=R_ID, descr=r.descr, date=r.date,US_img=r.US_img,E_ID=r.E_ID)
                return rec
            except KeyError as e:
                logging.debug(str(e))
                logging.error(f'Record with key "{R_ID}" could not be found.')
                return None

        if E_ID is not None:
            result = []
            df = self.t_records[self.t_records["E_ID"] == E_ID]
            for R_ID in df.index.tolist():
                rec = self.get_record(R_ID=R_ID)
                result.append(rec)
            return result

    def save_record(self, record, persistant=False):

        if (not(isinstance(record,Record))):
            raise TypeError('Invalid Object of type:'+ type(record)+". Please use a correct Record Object.")

        logging.debug('Trying to write data:')
        if (persistant):
            #here kommt noch was
            pass

        rec = record.__dict__
        df = pd.DataFrame(data=rec,index=[0])
        df = df.set_index('R_ID')
        logging.debug(df)
        try:
            new_record = self.t_records.append(df,verify_integrity=True)
            new_record.to_csv(self.RECORDS_PATH)
            self.t_records = new_record
        except ValueError as e:
            logging.error("Could not save record. Errormsg - "+str(e))
            raise ValueError(str(e))

        logging.info("Succesfully saved record "+str(rec["R_ID"]))

    def get_position(self, R_ID=None):
        """Return the position as list with the 4 handle objects. Else it returns None."""
        R_ID = str(R_ID)
        try:
            position = []

            df = self.t_handles[self.t_handles["R_ID"] == R_ID]
            index = df.index.tolist()

            for i in index:
                h = self.t_handles.loc[i]
                init_dict = {
                    'ID' : h.ID,
                    'handle_state' : h.handle_state,
                    'refname' : h.refname,
                    'MISSING' : h.MISSING,
                    'Q0' : h.Q0,
                    'Qx' : h.Qx,
                    'Qy' : h.Qy,
                    'Qz' : h.Qz,
                    'Tx' : h.Tx,
                    'Ty' : h.Ty,
                    'Tz' : h.Tz,
                    'calc_Err' : h.calc_Err,
                    'port_state' : h.port_state,
                    'frame_id' : h.frame_id
                }
                handle = Handle(**init_dict)
                position.append(handle)

            return position

        except KeyError as e:
            logging.debug(str(e))
            logging.error(f'Record with Key "{R_ID}" could not be found.')
            return None

    def save_position(self, R_ID,handles):

        try:
            temp_data = self.t_handles
            for h in handles.values():
                h = h.__dict__
                h['R_ID'] = R_ID
                handle_data = h
                new_df = pd.DataFrame(data=handle_data,index=[len(temp_data.index)])
                temp_data = temp_data.append(new_df,verify_integrity=True)
            logging.debug(str(temp_data))
            temp_data.to_csv(self.HANDLE_PATH)
            self.t_handles = temp_data
        except ValueError as e:
            logging.error("Could not save Position. Errormsg - "+str(e))
            raise ValueError(str(e))

    def savePILImage(self,img,img_name,filetype='.png'):
        """Saves an PIL Image to the _cfg defined DATAPATH.
        Returns path of the saved image as a string.
        """
        if (type(img)!= PIL.Image.Image):
            raise TypeError(f'Wrong type "{type(img)}for img. Use appropriate PIL Image Object')

        image_path = _cfg.SAVEDIMGPATH+str(img_name)+filetype

        try:
            img.save(image_path)
            return image_path
        except IOError as e:
            raise IOError(str(e))



# ------------------------------#
# ---- DATA MODEL INSTANCES ----#
# ------------------------------#

class Examination():
    """The data model of an examination.
    If no E_ID is given at the instantitation, it will generate a tempID with uuid4():
    'tempE-5d51171a-eae6-4b93-b4dd-abadecda3976'.

    Attributes
        Will be documented at the end.
    """
    def __init__(self, E_ID=None, doctor=None, patient=None, examitem=None, created=None):

        self.E_ID = E_ID
        self.doctor = doctor
        self.patient = patient
        self.examitem = examitem
        self.created = created
        if (E_ID is None):
            uid = uuid.uuid4()
            self.E_ID = 'tempE-'+str(uid)


class Record():
    """The data model of an record.
    If no R_ID is given at the instantitation, it will generate a tempID with uuid4():
    'tempR-5d51171a-eae6-4b93-b4dd-abadecda3976'.

    Attributes
        Will be documented at the end.
    """
    def __init__(self, E_ID, R_ID=None, descr=None, date=None, US_img=None):

        self.R_ID = R_ID
        self.descr = descr
        self.date = date
        self.US_img = US_img
        self.E_ID = E_ID
        if (R_ID is None):
            uid = uuid.uuid4()
            self.R_ID = 'tempR-'+str(uid)





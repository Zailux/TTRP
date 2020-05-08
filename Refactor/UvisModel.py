
import pandas as pd
import logging
import sys
sys.path.insert(1, '..\\')
from AuroraAPI import Handle
import uuid
import PIL

from helper import Helper
from config import Configuration
global hp
hp = Helper()
global _cfg
_cfg = Configuration()

class UltraVisModel:
    def __init__(self):
        
        #datapath = '..\\data\\'
        datapath = 'TTRP\\data\\'
        self.examination_path = datapath+'examination.csv'
        self.records_path = datapath+'record.csv'
        self.handle_path = datapath+'handles.csv'

        try: 
            self.t_examination = pd.read_csv(self.examination_path,index_col=0)
            self.t_records = pd.read_csv(self.records_path,index_col=0)
            self.t_handles = pd.read_csv(self.handle_path,index_col=0)
        except FileNotFoundError as e:
            logging.error(e)
            #disable saving functions!
        
        self._observers = {}

        self.__currWorkitem = {"Examination":None, "Records":[],"Handles":[]}
    
    def clearCurrentWorkitem(self):
        self.__currWorkitem.clear()
        self.__currWorkitem = {"Examination":None, "Records":[],"Handles":[]}

    def getCurrentWorkitem(self):
         return self.__currWorkitem

    #handling von gruppe von objekten. Ggf. ist das auch einfach über n Selekt auf Basis der Examination ID möglich

    def setCurrentWorkitem(self, obj):
        #validation
        
        if (type(obj) == Examination):
            self.__currWorkitem["Examination"] = obj
        elif (type(obj) == Record):
            self.__currWorkitem["Records"].append(obj)
        elif (all(isinstance(h, Handle) for h in obj)):
            self.__currWorkitem["Handles"].append(obj)
        else:
            raise TypeError(f'{type(obj)} is not correct')

        self.__callback(key="setCurrentWorkitem")

    #für Examination & Record
    def _getnextID(self,df):
        indexlist = df.index.tolist()
        length = []

        for i, ID in enumerate(indexlist):
            if (not str(ID).startswith('temp')):
                length.append(ID)

        next_id = len(length)
        return next_id


    # NEXT FEATURE get all corresponding Data based on Examination ID.  
    def getExamination(self, ID=None):
        E_ID = str(ID)
        try:
            e = self.t_examination.loc[E_ID]
            examination = Examination(E_ID= E_ID,doctor=e.doctor,patient=e.patient,examitem=e.examitem,created=e.created)

            return examination

        except KeyError as e:
            logging.debug(str(e))
            logging.error(f'Record with key "{E_ID}" could not be found.')
            return None

    
    def persistWorkitem(self):
        exam,records,handles = self.getCurrentWorkitem().values()

        #persist ExamID
        old_E_ID = exam.E_ID
        num_E_ID = self._getnextID(df=self.t_examination)
        new_E_ID = 'E-'+str(num_E_ID) if str(old_E_ID).startswith('temp') else old_E_ID
        
        
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
            
            logging.debug(f'Replaced tempID: {old_R_ID} with new ID: {new_R_ID} (in Records and Handles Table)' if old_R_ID != new_R_ID else None)

     
        #write changes to tables
        
        self.t_examination.to_csv(self.examination_path)
        self.t_records.to_csv(self.records_path)
        self.t_handles.to_csv(self.handle_path)
        

        



    def saveExamination(self, examination, persistant=False):
        
        if (not(isinstance(examination,Examination))):
            raise TypeError(f'Invalid Object of type: {type(examination)}". Please use a correct {Examination} Object.')
        
        logging.debug('Trying to write data:')
        
        if (persistant):
            '''
            as_list = df.index.tolist()
            idx = as_list.index('Republic of Korea')
            as_list[idx] = 'South Korea'
            df.index = as_list
            '''



            #here kommt noch was
            pass


        exam = examination.__dict__
        df = pd.DataFrame(data=exam,index=[0])
        df = df.set_index('E_ID')
        logging.debug(df)

        try:
            new_exam = self.t_examination.append(df,verify_integrity=True)
            new_exam.to_csv(self.examination_path)
            self.t_examination = new_exam
        except ValueError as e:
            logging.error("Could not save record. Errormsg - "+str(e))
            raise ValueError(str(e))

        logging.info("Succesfully saved record "+str(exam["E_ID"]))

    def getRecord(self, R_ID=None):
        
        R_ID = str(R_ID)
        try:
            r = self.t_records.loc[R_ID]
            rec = Record(R_ID=R_ID, descr=r.Beschreibung, date=r.Datum,US_img=r.US_Bild,E_ID=r.E_ID)

            return rec

        except KeyError as e:
            logging.debug(str(e))
            logging.error(f'Record with key "{R_ID}" could not be found.')
            return None

    def saveRecord(self, record, persistant=False):
        
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
            new_record.to_csv(self.records_path)
            self.t_records = new_record
        except ValueError as e:
            logging.error("Could not save record. Errormsg - "+str(e))
            raise ValueError(str(e))

        logging.info("Succesfully saved record "+str(rec["R_ID"]))
        
        
    #WIP
    def getPosition(self, R_ID=None):

        R_ID = str(R_ID)
        try:
            h = self.t_handles.loc[R_ID]
            #record = Record(R_ID=R_ID, descr=a.Beschreibung, date=a.Datum,US_img=a.US_Bild)

            #return record

        except KeyError as e:
            logging.debug(str(e))
            logging.error(f'Record with Key "{R_ID}" could not be found.')
        pass


    def savePosition(self, R_ID,handles):

        try:
            temp_data = self.t_handles    

            for h in handles.values():
                h = h.to_dict()
                h['R_ID'] = R_ID

                handle_data = h
                new_df = pd.DataFrame(data=handle_data,index=[len(temp_data.index)])

                temp_data = temp_data.append(new_df,verify_integrity=True)

            
            logging.debug(str(temp_data))
            temp_data.to_csv(self.handle_path)
            self.t_handles = temp_data

        except ValueError as e:
            logging.error("Could not save Position. Errormsg - "+str(e))
            raise ValueError(str(e))


    def savePILImage(self,img,img_name,filetype='.png'):

        if (type(img)!= PIL.Image.Image):
            raise TypeError(f'Wrong type "{type(img)}for img. Use appropriate PIL Image Object')

        image_path = _cfg.SAVEDIMGPATH+str(img_name)+filetype

        try:
            img.save(image_path)
            return image_path
        except IOError as e:
            raise IOError(str(e))

    def register(self,key,observer):
        key = str(key)
        if (key not in self._observers):
            self._observers[key] = []
            self._observers[key].append(observer)
        elif(observer not in self._observers[key]):
            self._observers[key].append(observer)
        else:    
            raise Warning(f"Observermethod: {observer} for Key {key} already exists")

    def __callback(self,key):
        key = str(key)
        if (key in self._observers):
            logging.debug(f'Callback for "{key}" - {self._observers[key]}')
            for observer_method in self._observers[key]:
                observer_method()




class Record():

    def __init__(self,E_ID, R_ID = None, descr=None, date=None,US_img=None ):
            
        self.R_ID = R_ID
        self.descr = descr
        self.date = date
        self.US_img = US_img
        self.E_ID = E_ID

        if (R_ID is None):
            uid = uuid.uuid4()
            self.R_ID = 'tempR-'+str(uid)



class Examination():

    def __init__(self, E_ID = None, doctor=None, patient=None, examitem=None,created=None):
            
        self.E_ID = E_ID
        self.doctor = doctor
        self.patient = patient
        self.examitem = examitem
        self.created = created
        

        if (E_ID is None):
            uid = uuid.uuid4()
            self.E_ID = 'tempE-'+str(uid)

    


    
   

    
    





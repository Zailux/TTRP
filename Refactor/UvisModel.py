
import pandas as pd
import logging
import sys
sys.path.insert(1, 'd:\\Nam\\Docs\\Uni\\Master Projekt\\Track To Reference\\WP\\TTRP')
sys.path.insert(1, '..\\')
from AuroraAPI import Handle
import uuid

class UltraVisModel:
    def __init__(self):
        
        datapath = '..\\data\\'
        self.untersuch_path = datapath+'untersuchung.csv'
        self.aufz_path = datapath+'aufzeichnung.csv'
        self.handle_path = datapath+'handles.csv'

        try: 
           # self.untersuchungen = pd.read_csv(self.untersuch_path,index_col=0)
            self.t_aufzeichnungen = pd.read_csv(self.aufz_path,index_col=0)
            self.t_handles = pd.read_csv(self.handle_path,index_col=0)
        except FileNotFoundError as e:
            logging.error(e)
            #disable saving functions!


    def getUntersuchung(self, ID=None):
        pass


    def addUntersuchung(self, ID):
        pass



    def getAufzeichnung(self, A_ID=None):
        
        A_ID = str(A_ID)
        try:
            a = self.t_aufzeichnungen.loc[A_ID]
            aufz = Aufzeichnung(A_ID=A_ID, descr=a.Beschreibung, date=a.Datum,US_img=a.US_Bild)

            return aufz

        except KeyError as e:
            logging.debug(str(e))
            logging.error(f'Aufzeichnung with Key "{A_ID}" could not be found.')




    def saveAufzeichnung(self, aufzeichnung, persistant=False):
        
        if (not(isinstance(aufzeichnung,Aufzeichnung))):
            raise TypeError('Invalid Object of type:'+ type(aufzeichnung)+". Please use a correct Aufzeichnung Object.")
        
        logging.debug('Trying to write data:')
        
        if (persistant):
            #here kommt noch was
            pass


        aufz = aufzeichnung.to_dict()
        
        df = pd.DataFrame(data=aufz,index=[0])
        df = df.set_index('A_ID')
        logging.debug(df)

        try:
            new_aufz = self.t_aufzeichnungen.append(df,verify_integrity=True)
            new_aufz.to_csv(self.aufz_path)
            self.t_aufzeichnungen = new_aufz
        except ValueError as e:
            logging.error("Could not save Aufzeichnung. Errormsg - "+str(e))
            raise ValueError(str(e))

        logging.info("Succesfully saved Aufzeichnung "+str(aufzeichnung.A_ID))
        
        
    
    def getPosition(self, A_ID=None):
        pass


    def savePosition(self, A_ID,handles):

        try:
            temp_data = self.t_handles    

            for h in handles.values():
                h = h.to_dict()
                h['A_ID'] = A_ID

                handle_data = h
                new_df = pd.DataFrame(data=handle_data,index=[len(temp_data.index)])

                temp_data = temp_data.append(new_df,verify_integrity=True)

            
            logging.debug(str(temp_data))
            temp_data.to_csv(self.handle_path)
            self.t_handles = temp_data

        except ValueError as e:
            logging.error("Could not save Position. Errormsg - "+str(e))
            raise ValueError(str(e))





class Aufzeichnung():

    def __init__(self, A_ID = None, descr=None, date=None,US_img=None):
            
        self.A_ID = A_ID
        self.descr=descr
        self.date = date
        self.US_img=US_img

        if (A_ID is None):
            uid = uuid.uuid4()
            self.A_ID = 'tempA-'+str(uid)

    def to_dict(self):
        d = {
            'A_ID' : self.A_ID,
            'descr' : self.descr,
            'date' : self.date,
            'US_img' : self.US_img
        }
        return d

    
    
   

    
    





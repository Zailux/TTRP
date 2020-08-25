"""This is the Uvis Model module.

This module contains the following classes\:
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
import os
import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageTk
from pyquaternion import Quaternion
import matplotlib.pyplot as plt

#sys.path.insert(1, '..\\')
#sys.path.insert(0, os.path.abspath('../src'))
from src.aurora import Handle
from src.Calibrator import Calibrator
from src.config import Configuration
from src.helper import Helper

global hp
global _cfg
hp = Helper()
_cfg = Configuration()
logger = _cfg.LOGGER

# ------------------------------#
# ---- DATA MODEL INSTANCES ----#
# ------------------------------#

class Examination():
    """
    :param str E_ID: The Examination ID

    :param str doctor: The doctor performing the examination.

    :param str patient: The patient name.

    :param str examitem: The examination item (e.g. left lung ...)

    :param date.datetime created: The timestamp of the performed examination.

    The data model of an examination. Can be instantiated as empty object.
    If no E_ID is given at the instantitation, it will generate a tempID with `uuid4()`:
    'tempE-5d51171a-eae6-4b93-b4dd-abadecda3976'.
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
    """
    :param str E_ID: The foreign key of the :class:`Examination`.

    :param str R_ID: The key or ID of the :class:`Record`.

    :param str descr: The description of the record (e.g. which struture is to seen in the image).

    :param date.datetime date: The timestamp of the performed examination.

    :param str US_img: Path of the saved image in the filesystem (e.g `data\img\imag_name`).

    The data model of an record.
    If no R_ID is given at the instantitation, it will generate a tempID with uuid4():
    'tempR-5d51171a-eae6-4b93-b4dd-abadecda3976'.
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


class Comparison():
    """
    :param str R_ID_base: The key of the base :class:`Record`.

    :param str R_ID_nav: The key of the navigated / target :class:`Record`.

    :param numpy.array vec_base: The ultrasound probe position vector of the base :class:`Record`.

    :param numpy.array vec_nav: The ultrasound probe position vector of the navigated / target :class:`Record`.

    :param float acc_t: Translational accuracy in mm (95% confidence interval)

    :param float acc_o: Orientation accuracy in degree (95% confidence interval)

    :param list calc_errors: List of calculation errors pessimitic calculated.

    :param str doc_eval: Evaluation of the doctor regarding the two images.

    :param str E_ID: The foreign key of the :class:`Examination`.

    The object holding the results from compairing two records.
    """
    def __init__(self, R_ID_base=None, R_ID_nav=None, vec_base=None,
                 vec_nav=None, acc_t=None, acc_o=None, calc_errors=None,
                 doc_eval=None, E_ID=None):

        self.R_ID_base = R_ID_base
        self.R_ID_nav = R_ID_nav
        self.vec_base = vec_base
        self.vec_nav = vec_nav
        self.acc_t = acc_t
        self.acc_o = acc_o
        self.calc_errors = calc_errors
        self.doc_eval = doc_eval
        self.E_ID = E_ID


    def set_values_from_records(self, tgt_rec:Record, nav_rec:Record):
        """Sets the values via Record objects. TODO"""
        self.R_ID_base = tgt_rec.R_ID
        self.R_ID_nav = nav_rec.R_ID


# TODO
class Evaluation():
    pass


# ------------------------------#
# ---- MAIN MODEL CLASS     ----#
# ------------------------------#

class UltraVisModel:
    """ The UltraVisModel class provides
        methods to access the data / model of the uvis application.
        It is primarily for reading and saving data from the csv tables.
        As for a more handy accessability, the model maintains the application
        data in a "workitem". A dict, which consolidates the Examination, Records
        and Handles in one object.
        Via an observer pattern, the model triggers a callback to
        the corresponding methods in the controller (caller).
        During instatiation the `pd.DataFrame` object are loaded from the filesystem
        to provide the application with the data.
    """
    def __init__(self):
        datapath = _cfg.DATAPATH
        self.COMPARISON_PATH = datapath+'comparison.csv'
        self.HANDLE_PATH = datapath+'handles.csv'
        self.EVALUATION_PATH = datapath+'evaluation.csv'
        self.EXAMINATION_PATH = datapath+'examination.csv'
        self.RECORDS_PATH = datapath+'record.csv'
        try:
            self.t_comparison = pd.read_csv(self.COMPARISON_PATH, index_col=0)
            self.t_examination = pd.read_csv(self.EXAMINATION_PATH, index_col=0)
            self.t_evaluation = pd.read_csv(self.EVALUATION_PATH, index_col=0)
            self.t_handles = pd.read_csv(self.HANDLE_PATH, index_col=0)
            self.t_records = pd.read_csv(self.RECORDS_PATH, index_col=0)
        except FileNotFoundError as e:
            logger.error(e)
            #disable saving functions!
        self._init_baseline_dataset()

        self._observers = {}
        self._curr_workitem = {"Examination":None, "Records":[], "Handles":[]}

    def _init_baseline_dataset(self):
        """Loads the baseline datasets. Might cause errors when datasets are not in the filesystem.
        The datasets can be found in the MS Team folder. See further_readings in the code documentation"""
        DATAPATH = _cfg.DATAPATH+'baseline_trials\\'
        DATAPATH2 = _cfg.DATAPATH+'baseline_human_trials\\'
        DATAPATH3 = _cfg.DATAPATH+'baseline_human_expert_trials\\'

        try:
            self.b_examination = pd.read_csv(DATAPATH+'examination.csv', index_col=0)
            self.b_handles = pd.read_csv(DATAPATH+'handles.csv', index_col=0)
            self.b_records = pd.read_csv(DATAPATH+'record.csv', index_col=0)
            self.hb_examination = pd.read_csv(DATAPATH2+'examination.csv', index_col=0)
            self.hb_handles = pd.read_csv(DATAPATH2+'handles.csv', index_col=0)
            self.hb_records = pd.read_csv(DATAPATH2+'record.csv', index_col=0)
            self.heb_examination = pd.read_csv(DATAPATH3+'examination.csv', index_col=0)
            self.heb_handles = pd.read_csv(DATAPATH3+'handles.csv', index_col=0)
            self.heb_records = pd.read_csv(DATAPATH3+'record.csv', index_col=0)
        except FileNotFoundError as e:
            logger.error(e)

    def register(self, key, observer):
        """
        :param str key: Function name of the observed function in the model.

        :param function observer: Observer method or function to be called back.

        Implementation of observer pattern.
        Observers can register methods for a callback. The key should be
        the UltraVisModel methodname. When the method in the model is executed
        the :func:`_callback` is triggered.
        """
        key = str(key)
        if (key not in self._observers):
            self._observers[key] = []
            self._observers[key].append(observer)
        elif(observer not in self._observers[key]):
            self._observers[key].append(observer)
        else:
            raise Warning(f"Observermethod: {observer} for key {key} already exists")

    def _callback(self, key):
        """:param str key: Key / functionname of Observed method in UltraVisModel.

        Calls the observers methods, based on the methodkey of UltraVisModel method."""
        key = str(key)
        if (key in self._observers):
            logger.debug(f'{self.__class__}: Callback for "{key}" - {self._observers[key]}')
            for observer_method in self._observers[key]:
                observer_method()

    def clear_current_workitem(self):
        """ Clears the _curr_workitem dictionary and reset its values to a
        clean state {"Examination":None, "Records":[], "Handles":[]}.
        """
        self._curr_workitem.clear()
        self._curr_workitem = {"Examination":None, "Records":[], "Handles":[]}

    def get_current_workitem(self):
        """:returns: Return the current workitem.

        :rtype: dict
        """
        return self._curr_workitem

    def get_length_workitem(self):
        """:returns: Return the length or rather the num of items workitem.

        :rtype: int
        """
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
        """
        :param obj: Object or tuple to be set for the workitem.
        :type obj: Examination, Record, Handle, tuple

        :param bool as_instance: If `True` use single object. If `False` then use `tuple` with the objects.

        :exception TypeError:
            Will be raised object is not of :class:`uvis_model.Examination`, :class:`uvis_model.Record`,
            :class:`aurora.Handle` or `tuple` containing the object types..

        Set the current workitem for the UvisModel.
        You can either append single instances of an Examination Object, Record Object
        or a Position (a list object with 4 Handle Objects) to the workitem.
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

        self._callback(key="set_current_workitem")

    #Renaming of image name can be implemented.
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
                logger.debug(f'Replaced tempID: {old_R_ID} with new ID: {new_R_ID} \
                                (in Records and Handles Table)')

        #write changes to tables
        self._dataset_to_csv()
        logger.info(f'Successfully persist workitem {new_E_ID}')
        return new_E_ID

    def load_workitem(self, E_ID):
        """
        :param str E_ID: The ID of an :class:`Examination`

        Loads the workitem based on the examination id (E_ID).
        The workitem can be accessed via :func:`get_current_workitem`.
        """
        exam = self.get_examination(ID=E_ID)
        records = []
        positions = []

        if not exam:
            logger.error(f"Can't load Examination with {E_ID}")
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
        """:param df.DataFrame df: The dataframe for which the next ID is necessary.

        :return: Returns the next ID for persisting.

        :rtype: int

        Supporting method for getting the next real ID for persisting."""
        indexlist = df.index.tolist()
        length = []

        for i, ID in enumerate(indexlist):
            if (not str(ID).startswith('temp')):
                length.append(ID)
        next_id = len(length)
        return next_id

    def get_examination(self, ID=None):
        """:return: Return an class:`Examination` Object from the csv. Else it returns :const:`None`."""
        E_ID = str(ID)
        try:
            e = self.t_examination.loc[E_ID]
            examination = Examination(
                E_ID=E_ID, doctor=e.doctor, patient=e.patient,
                examitem=e.examitem, created=e.created)
            return examination

        except KeyError as e:
            logger.debug(str(e))
            logger.error(f'Record with key "{E_ID}" could not be found.')
            return None

    def save_examination(self, examination, persistant=False):
        """:param Examination examination: Examination object for saving

        :param bool persistant: Flag whether save Examination temporarily or persisant. Defaults to :const:`False`

        :exception TypeError:
            Will be raised examination param is not of :class:`uvis_model.Examination`.

        Saves a (temporary) instance of an Examination Object to the csv."""
        if (not(isinstance(examination,Examination))):
            raise TypeError(f'Invalid Object of type: {type(examination)}". \
                              Please use a correct {Examination} Object.')
        logger.debug('Trying to write data:')

        if (persistant):
            """
            as_list = df.index.tolist()
            idx = as_list.index('Republic of Korea')
            as_list[idx] = 'South Korea'
            df.index = as_list
            """ #here kommt noch was
            pass
        exam = examination.__dict__
        df = pd.DataFrame(data=exam,index=[0])
        df = df.set_index('E_ID')
        logger.debug(df)
        try:
            new_exam = self.t_examination.append(df,verify_integrity=True)
            new_exam.to_csv(self.EXAMINATION_PATH)
            self.t_examination = new_exam
        except ValueError as e:
            logger.error("Could not save record. Errormsg - "+str(e))
            raise ValueError(str(e))
        logger.info("Succesfully saved record "+str(exam["E_ID"]))

    def get_record(self, R_ID=None, E_ID=None):
        """
        :param str R_ID: The key of an :class:`Record` object.
            Used to get single record object.

        :param str E_ID: The key of an :class:`Examination` object.
            Used for all corresponding records to the examination.

        :return: Either return single :class:`Record` object or `list` of :class:`Record` objects.

        :rtype: Record, list, None

        Returns an Record object or Record object list from the csv.
        Get corresponding Records via the E_ID or a specific instance via R_ID.
        If it can't find an object the method returns :const:`None`.
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
                logger.debug(str(e))
                logger.error(f'Record with key "{R_ID}" could not be found.')
                return None

        if E_ID is not None:
            result = []
            df = self.t_records[self.t_records["E_ID"] == E_ID]
            for R_ID in df.index.tolist():
                rec = self.get_record(R_ID=R_ID)
                result.append(rec)
            return result

    def save_record(self, record, persistant=False):
        """:param Record record: Record object for saving

        :param bool persistant: Flag whether save record temporarily or persisant. Defaults to :const:`False`

        :exception TypeError:
            Will be raised examination param is not of :class:`uvis_model.Record`.

        Saves a (temporary) instance of an Examination Object to the csv."""
        if (not(isinstance(record,Record))):
            raise TypeError('Invalid Object of type:'+ type(record)+". Please use a correct Record Object.")

        # TODO add renaming image for persistant save (see rename_images for that.)
        if (persistant):
            df = self.t_records
            old_R_ID = record.R_ID
            new_index = self._getnextID(df)
            new_R_ID = 'R-'+str(new_index) if str(old_R_ID).startswith('temp') else old_R_ID
            as_list = df.index.tolist()
            idx = as_list.index(old_R_ID)
            as_list[idx] = new_R_ID
            df.index = as_list

            #Persist corresponding Position
            df2 = self.t_handles
            df2['R_ID'].where(cond=(df2['R_ID'] != old_R_ID), other=new_R_ID, inplace=True)
            if old_R_ID != new_R_ID:
                logger.debug(f'Successfully persisted tempID: {old_R_ID} with new ID: {new_R_ID} \
                (in Records and Handles Table)')
                return new_R_ID
            return None

        logger.debug('Trying to write data:')
        rec = record.__dict__
        df = pd.DataFrame(data=rec, index=[0])
        df = df.set_index('R_ID')
        logger.debug(df)
        try:
            new_record = self.t_records.append(df, verify_integrity=True)
            new_record.to_csv(self.RECORDS_PATH)
            self.t_records = new_record
        except ValueError as e:
            logger.error("Could not save record. Errormsg - "+str(e))
            raise ValueError(str(e))

        logger.info("Succesfully saved record "+str(rec["R_ID"]))
        return rec["R_ID"]

    def get_position(self, R_ID=None, as_dict=False, handle_df=None):
        """
        :param str R_ID: Record ID.

        :param bool as_dict: Flag for getting the position as a dict or a list.

        :param pd.DataFrame handle_df: DataFrame contained all recorded handle data (or sensor data).

        :returns: Return the position as list or dict with the 4 :class:`aurora.Handle` objects. Else it returns :const:`None`.

        :rtype: dict, list, None
        """
        if handle_df is None:
            handle_df = self.t_handles
        R_ID = str(R_ID)
        try:
            position = []
            position_dict = {}
            df = handle_df[handle_df["R_ID"] == R_ID]
            del df['R_ID']
            temp = df.to_dict(orient='records')

            for h_dict in temp:
                handle = Handle(**h_dict)
                position.append(handle)
                position_dict[handle.ID] = handle

            return position if not as_dict else position_dict

        except KeyError as e:
            logger.debug(str(e))
            logger.error(f'Record with Key "{R_ID}" could not be found.')
            return None

    def save_position(self, R_ID, handles):
        """
        :param str R_ID: Record ID.

        :param dict handles: Dictionary containing the 4 :class:`aurora.Handle` objects.

        :exception ValueError:
            Will be raised if the saving procedure failed.
        Saves the 4 :class:`aurora.Handle` objects to the database / csv.

        """
        try:
            df = self.t_handles

            for h in handles.values():
                h = h.__dict__
                h['R_ID'] = R_ID
                handle_data = h
                new_handle_df = pd.DataFrame(data=handle_data, index=[0])
                df = df.append(new_handle_df, ignore_index=True)

            logger.debug(str(df))
            df.to_csv(self.HANDLE_PATH)
            self.t_handles = df
        except ValueError as e:
            logger.error("Could not save Position. Errormsg - "+str(e))
            raise ValueError(str(e))

    def clear_temp_data(self):
        """Revmoves all temporary from the whole data set.
        Temp data are items which start with 'temp' in their IDs."""
        df1 = [self.t_examination, self.t_records]
        df2 = self.t_handles

        for df in df1:
            index_list = df.index.tolist()
            match_index = df.index.str.match('temp').tolist()
            drop_index_list = df.loc[match_index].index.to_list()
            df.drop(drop_index_list, inplace=True)


        match_array = df2['R_ID'].str.match('temp').to_list()
        drop_index_list= df2.loc[match_array].index.to_list()
        df2.drop(drop_index_list, inplace=True)

        self._dataset_to_csv()

    def get_comparison(self, Eval_ID, as_df=True):

        df = self.t_comparison[self.t_comparison["E_ID"] == Eval_ID]
        if as_df:
            return df

    def _dataset_to_csv(self):
        """Writes the dataframes to the csv files. Locking could be implemented"""
        self.t_examination.to_csv(self.EXAMINATION_PATH)
        self.t_records.to_csv(self.RECORDS_PATH)
        self.t_handles.to_csv(self.HANDLE_PATH)

    def compare_records(self, tgt_rec:Record, nav_rec:Record, E_ID=None, insert_data=True):
        """Compares two records and creates an Comparison object with calculated values"""
        logger.info("Compare stuff")
        R_ID_base = tgt_rec.R_ID  # Target R_ID
        R_ID_nav = nav_rec.R_ID   # Navigated R_ID or rather saved one
        h_base = self.get_position(R_ID=R_ID_base)
        h_nav = self.get_position(R_ID=R_ID_nav)

        pos1, ori1 = self.pos_to_transformed_data(h_base)
        pos2, ori2 = self.pos_to_transformed_data(h_nav)

        vec_base = np.array(pos1, dtype=float)
        vec_nav = np.array(pos2, dtype=float)
        dist_vec = np.subtract(vec_nav, vec_base)

        #Distance in mm overall
        distance = np.linalg.norm(dist_vec)
        # Distance for each dimension
        x_dif, y_dif, z_dif = np.absolute(dist_vec) # removed from db, due to conversion issues
        acc_t = distance

        # Pessimistic comparing.
        calc_errors = np.array([self._get_max_calcerror(h_base), self._get_max_calcerror(h_nav)])

        #acc_o TODO bzw. TBD wegen Tobi mit ori1 und ori2
        # doc_eval TBD

        E_ID = tgt_rec.E_ID if E_ID is None else E_ID

        input_dict = {"R_ID_base": R_ID_base,
                      "R_ID_nav": R_ID_nav,
                      "vec_base": vec_base,
                      "vec_nav": vec_nav,
                      "acc_t": acc_t,
                      "acc_o":None,
                      "calc_errors":calc_errors,
                      "doc_eval":None,
                      "E_ID": E_ID}

        df = pd.DataFrame(data=[input_dict], index=[len(self.t_comparison.index)])

        if insert_data:
            return self._insert_comparison(df)
        else:
            return df

    def _insert_comparison(self, df:pd.DataFrame):
        try:
            self.t_comparison = self.t_comparison.append(df, verify_integrity=True)
            self.t_comparison.to_csv(self.COMPARISON_PATH)
        except ValueError as e:
            logger.error("Could not insert comparison row. Errormsg - "+str(e))
            raise ValueError(str(e))
        c = df.iloc[0]
        logger.info(f"Succesfully saved comparison of {c.R_ID_base} and {c.R_ID_nav}")
        return True

    def evaluate_comparison_data(self, df:pd.DataFrame):
        # calculate comparison data and evaluates them and writes it in a db.
        # get relevant values and get averages etc.
        Eval_ID = df["E_ID"].unique()[0]
        logger.info(f"Start evaluating Examination {Eval_ID}.")

        data_acc = df['acc_t']
        acc_t_med = data_acc.median()
        acc_t_avg = data_acc.mean()
        acc_t_std = data_acc.std()

        data_calc = df['calc_errors'].tolist()
        as_list = []

        for item in data_calc:
            item = self.list_string_to_list(item, float)
            as_list = as_list+item

        min_err, max_err, avg_err = min(as_list), max(as_list), np.mean(as_list)
        eval_dict = {"descr": None, "acc_t_avg": acc_t_avg, "acc_t_med": acc_t_med,
                     "acc_t_std": acc_t_std,
                     "acc_o_avg": None, "acc_o_med": None, "acc_o_std": None,
                     "calc_error_min": min_err, "calc_error_max": max_err, "calc_error_avg": avg_err,
                     "doc_eval_avg":None}

        eval_df = pd.DataFrame(data=[eval_dict], index=[Eval_ID])
        self._insert_evaluation(eval_df)

    def _insert_evaluation(self, df:pd.DataFrame):
        try:
            self.t_evaluation = self.t_evaluation.append(df, verify_integrity=True)
            self.t_evaluation.to_csv(self.EVALUATION_PATH)
        except ValueError as e:
            logger.error("Could not insert Evaluation results row. Errormsg - "+str(e))
            raise ValueError(str(e))

        logger.info(f"Succesfully saved evaluation {df.index}.") # Der Output ist nicht richtig

    # TODO ändere das so ab, dass du die Daten aus deinen Ordnern rausziehst. Ne weitere methode, die die auswerten
    # für den einzelnen Datensatz zurückliefert.
    def calculate_baseline(self, records_df:pd.DataFrame = None):
        # Calculate average position, etc. of a fixed baseline measurement --> what is the avg position.
        # How much do the values vary in such measurements

        if records_df is not None:
            df = records_df
        else:
            df = self.b_records

        R_ID_list = df.index.to_list()
        #R_ID_list = ["R-137","R-133","R-127","R-125","R-124","R-114","R-104"] # Hr. Froehlich ausgewählt R_ID
        t_data = []
        ori_data = []
        calc_errors = []

        for R_ID in R_ID_list:
            position = self.get_position(R_ID=R_ID) # aufrufbar mit definierten df
            vector, ori1 = self.pos_to_transformed_data(position)
            err = self._get_max_calcerror(position)
            t_data.append(vector)
            ori_data.append(ori1)
            calc_errors.append(err)

        def calc_translational():

            t_array = np.asarray(t_data)
            acc_t_med = np.median(t_array, axis=0)
            acc_t_avg = np.mean(t_array, axis=0)
            acc_t_std = np.std(t_array, axis=0)  # ist das so korrekt?

            # Get 95 % of data, via STD and Mean
            edge_vector = np.add(acc_t_avg, (acc_t_std*2))
            dis_vec = np.subtract(edge_vector, acc_t_avg) # eigentlich unnötiger rechenschritt
            acc_t_95 = np.linalg.norm(dis_vec)

            logger.info(f"Median Vector is {acc_t_med}")
            logger.info(f"Average Vector is {acc_t_avg}")
            logger.info(f"Standard Deviation vector is {acc_t_std}")

            # Confidenz Interval
            logger.info(f"Translative Accurary for CI 95 is is {acc_t_95} mm.")

            dis2 = np.subtract(acc_t_med, acc_t_avg)
            dis2 = np.linalg.norm(dis2)
            logger.info(f"Distance between median and average is {dis2} mm.")

            dis_array = []
            for rec in t_array:
                distance = np.subtract(acc_t_avg, rec)
                distance = np.linalg.norm(distance)
                dis_array.append(distance)

            dis_array = np.asarray(dis_array)
            logger.info(f"Median Vector is {acc_t_med}")
            logger.info(f"Average Vector is {acc_t_avg}")
            logger.info(f"Standard Deviation vector is {acc_t_std}")
            print(np.mean(dis_array)) #mean distance
            print(np.median(dis_array)) # median distance
            print(np.std(dis_array)) # std distance
            return dis_array


        def calc_calc_errors():
            err = np.asarray(calc_errors)
            max_err = np.max(err)
            median_err = np.median(err)

        def calc_orientation():
            # TODO Ich brauche noch die Umwandlung des US Kopf orientierung
            # auf Ziel Koordinaten system.
            # https://stackoverflow.com/questions/18818102/convert-quaternion-representing-rotation-from-one-coordinate-system-to-another
            # https://gamedev.stackexchange.com/questions/140465/convert-quaternion-to-a-different-coordinate-system

            q_list = np.asarray(ori_data)
            q_avg = hp.q_average(Q=q_list)

            self.q_avg = Quaternion(q_avg)
            print(q_avg)

            # STD, AVG and Median for Orientation
            # With average quarternion make a look to get difference for all quarternions
            # Copy avg quarterion complex konjugated as a equalsized list and  multiply them matrixes.
            # the u get a list differences quarternions.
            # extract the degree difference for all of the quaternions
            # have the list averaged, std, and medianed !

            # ALternatively use a for loop

        arr = calc_translational()
        #calc_orientation()

        print("donus")

        return arr

    def display_boxplot(self, input_arr, columns=None):
        """
        :param list input_arr: List of numpy.array containing the data for each plot column.

        :param list columns: List of the column names.

        Creates and displays a boxplot for the baseline evaluations."""
        df = pd.DataFrame(input_arr, columns=columns)
        bplot = df.boxplot()
        plt.axes(bplot)
        plt.show()

    def _get_max_calcerror(self, position:list):
        """Checks the calculation errors for 4 handles and return the highest calculation error."""
        errors = []
        for handle in position:
            errors.append(handle.calc_Err)
        return max(errors)

    # TODO how to deal with position / Handles appropriately? List Or dict !!! no mixture
    # TODO Should I average Quarternion here already ?
    def pos_to_transformed_data(self, position, orientation_type='quaternion'):
        """
        :param list position: A list with the 4 :class:`aurora.Handle` objects.

        :returns: Return 2 lists with the transformed translative and transformed orientation data.

        :rtype: list, list

        Takes a record or rather the position and return the transformed data of the
        Ultrasound probe. """
        cali = Calibrator()
        handle_US = position[0]
        handle_HR = position[1]
        handle_LR = position[2]
        handle_B = position[3]
        a = handle_HR.get_trans_data() # becken rechts
        b = handle_LR.get_trans_data() # becken links
        c = handle_B.get_trans_data() # brustbein

        cali.set_trafo_matrix(a,b,c)

        trans_pos = cali.transform_backward(handle_US.get_trans_data(), do_scale=False)
        q0,i,j,k = handle_US.get_orient_data()
        yaw, pitch, roll = cali.quaternion_to_rotations(q0,i,j,k)

        trans_ori_quat =[q0,i,j,k]
        trans_ori_euler = [yaw, pitch, roll]  #TODO sobald Orientierung funzt
        trans_ori = {"quaternion": trans_ori_quat,
                     "euler": trans_ori_euler
        }
        if not orientation_type in trans_ori.keys():
            raise ValueError(f"return_type '{orientation_type}' is not in {list(trans_ori.keys())}")
        return trans_pos, trans_ori[orientation_type]

    def rename_images(self, rec_df:pd.DataFrame = None, PATH=None):
        """Renames the image files, with temporary filenames."""
        logger.info("Start Renaming Images")
        if rec_df is None:
            rec_df = self.t_records
            PATH = self.RECORDS_PATH

        for R_ID, img_path in zip (rec_df.index.tolist(), rec_df["US_img"]):
            img_file = Path(img_path)
            if not img_file.is_file():
                logger.warning(f"Can't find image in Path {img_path}.")
                continue
            img_name = img_path.split("/")[-1]
            if len(img_name) > 18:
                new_path = _cfg.SAVEDIMGPATH+R_ID+"_img.png"
                os.rename(img_path, new_path)
                rec_df.at[R_ID, "US_img"] = new_path
                rec_df.to_csv(PATH)
                logger.debug(f"Changed file {img_path} to {new_path}")
            else:
                continue

        logger.info("Done renaming images.")

    def get_img(self, filename, asPILimage=True):
        # Opens Image and translates it to TK compatible file.
        #filename = self.imgdir+filename

        try:
            img = Image.open(filename)
        except FileNotFoundError as err:
            logger.exception("File was no found, Err Img replace\n" + err)
            #tkimage = self.notfoundimg
        finally:
            return img if asPILimage else ImageTk.PhotoImage(img)

    def save_PIL_image(self, img, img_name, filetype='.png'):
        """Saves an PIL Image to the _cfg defined DATAPATH.
        Returns path of the saved image as a string.
        """
        if (type(img)!= Image.Image):
            raise TypeError(f'Wrong type "{type(img)}for img. Use appropriate PIL Image Object')

        image_path = _cfg.SAVEDIMGPATH+str(img_name)+filetype

        try:
            img.save(image_path)
            return image_path
        except IOError as e:
            raise IOError(str(e))

    def list_string_to_list(self, string, dtype):
        """Suboptimale Methode. Had to do this workaround for the csv.
        Takes a String which is formatted as a list and actually converts it to a list."""
        a = string.replace("[","").replace("]","").replace("'","").split(" ")
        result = []
        for item in a:
            result.append(dtype(item))
        return result

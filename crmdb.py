# structure of table: facestream
# columns:
# faceid (text, persisted, as in Azure's FaceList)
# event (text, datetime)
# duration (integer, seconds)
# gender
# age (real)

# CRM functions

import os
#from PIL import Image
import sqlite3
import datetime
import logging

time_format = '%Y-%m-%d %H:%M:%S'

def get_CRMDB_dir():
    return os.path.expanduser("~/CRMDB")

faceAttributes='gender,age,headPose,smile,emotion'

def connect(**kwargs):
    # keyword args: dbname - name of database
    # crmdb: customer relationships management database
    crmdb_name=kwargs.get('dbname','report.ai.db')
    path=os.path.join(get_CRMDB_dir(),crmdb_name)
    #print("connect crmdb:",path)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    # previousid references to identified trackstream.trackid
    # previousconf is the confidence
    sql_face = """
    CREATE TABLE facestream (
        id integer PRIMARY KEY,
        trackid text NOT NULL,
        faceid text NOT NULL,
        cloudid text,
        event text NOT NULL,
        gender text,
        age integer,
        headPose text,
        smile real,
        emotion text,
        previousid text,
        previousconf real)
        """
    sql_track = """
    CREATE TABLE trackstream (
        id integer PRIMARY KEY,
        trackid text NOT NULL,
        cloudid text,
        true_name text,
        tracking_start text NOT NULL,
        tracking_stop text NOT NULL)
        """
    try:
        cursor.execute(sql_face)
        cursor.execute(sql_track)
    except:
        None
        #print("crmdb: Exception")
    else:
        print("crmdb: created tables TRACKSTREAM, FACESTREAM")
    conn.commit()
    return conn

def now():
    t=str(datetime.datetime.now().strftime(time_format))
    return t

def record_face(trackid,faceid,faceAttributes,returning_face,**kwargs):
    # keyword args: dt - event (datetime)
    # @@@ take care of returning_face
    conn=connect(**kwargs)
    cursor=conn.cursor()
    #system_dt=datetime.datetime.now().strftime(time_format)
    # system datetime override using keyword argument 'dt'
    event=str(kwargs.get('dt',now()))
    gender=faceAttributes['gender']
    age=faceAttributes['age']
    headPose="TBD" #faceAttributes['headPose']
    smile=faceAttributes['smile']
    emotions=faceAttributes['emotion'] # emotion probabilities
    emotion=max(emotions, key=emotions.get) # most probable emotion
    # translate cloudid (azure's group's personid) to local trackid
    prevcloudid=returning_face['personId']
    if prevcloudid is not None:
        cursor.execute("SELECT trackid FROM trackstream WHERE cloudid=?",(prevcloudid,))
        prevtrackids=cursor.fetchall()
        if len(prevtrackids)==1:
            prevtrackid=prevtrackids[0][0]
        elif len(prevtrackid>1):
            prevtrackid=prevtrackids[0][0]
            logging.error("multiple prevtrackids")
        else:
            logging.warning("unmatched prevcloudid")
            prevtrackid=None
        prevconfidence=returning_face['confidence']
    else:
        prevtrackid=None
        prevconfidence=0.0
    logging.info("faceid: {} gender: {} age: {}".format(faceid,gender,age))
    sql = """
        INSERT
            INTO facestream (trackid, faceid, event, gender, age, headPose, smile, emotion, previousid, previousconf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    cursor.execute(sql, (trackid,faceid,event,gender,age,headPose,smile,emotion,prevtrackid,prevconfidence))
    conn.commit()
    conn.close()

def face_image_path(faceid):
    path=os.path.join(get_CRMDB_dir(),'faces',faceid+'.jpg')
    return path

def record_track(trackid,tracking_start,tracking_stop,**kwargs):
    # keyword args: dt - event (datetime)
    conn=connect(**kwargs)
    true_name=kwargs.get('true_name',None)
    cursor=conn.cursor()
    sql = """
        INSERT
            INTO trackstream (trackid, tracking_start, tracking_stop, true_name)
            VALUES (?, ?, ?, ?)"""
    cursor.execute(sql, (trackid,tracking_start,tracking_stop,true_name))
    conn.commit()
    conn.close()

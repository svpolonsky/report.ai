# python export.py
# Generate report and export to Excel


# Anaconda doesn't have openpyxl (works with Excel), use "pip install openpyxl" to add this module

import os
import pandas as pd
import crmdb
import argparse
import logging
import datetime

LOGFORMAT = "%(levelname)s [%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(format=LOGFORMAT,level = logging.INFO)

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", type=str, help="input database file name")
ap.add_argument("-o", "--output", type=str, help="output excel file name")
args = vars(ap.parse_args())

if args["input"] is not None:
    input=args["input"]
else:
    input="report.ai.db"

if args["output"] is not None:
    output=args["output"]
else:
    output="report.ai.xlsx"

#@@@ this date should be taken from cli
report_date='2019-04-18'

def process_tracks(df):
    # convert string dates to datetime
    df['tracking_start']=pd.to_datetime(df['tracking_start'])
    df['tracking_stop']=pd.to_datetime(df['tracking_stop'])

    # add new columns
    df['gender']='undefined'
    df['age']=0.
    df['emotion']='undefined'
    # compute the values for new columns by averaging over track
    for ind, row in df.iterrows():
        trackid=row['trackid']
        logging.info(trackid)
        sql_query="SELECT * FROM facestream WHERE trackid='{}'".format(trackid)
        faces=pd.read_sql_query(sql_query,conn)
        logging.info(faces['faceid'].count())
        # clean false gender detection: majority-based gender
        genders=faces.groupby('gender').size().sort_values(ascending=False)
        gender=genders.index.tolist()
        if len(gender)>1:
            logging.warning('multiple genders for the same person')
        try:
            df.at[ind, 'gender'] = gender[0]
        except IndexError:
            logging.warning('gender undefined')
        # report most frequent emotion
        emotions=faces.groupby('emotion').size().sort_values(ascending=False)
        emotion=emotions.index.tolist()
        try:
            df.at[ind, 'emotion'] = emotion[0]
        except IndexError:
            logging.warning('emotion undefined')
        # average ages from multiple faces
        df.at[ind, 'age']=faces['age'].mean()
        # is the visitor returning?
        previousids=faces.groupby('previousid').size().sort_values(ascending=False)
        previousid=previousids.index.tolist()
        try:
            df.at[ind, 'prevtrackid'] = previousid[0]
        except IndexError:
            logging.warning('previousid undefined')
    return df


conn=crmdb.connect(dbname=input)
# get all tracks for a given date
sql="SELECT * FROM trackstream WHERE date(tracking_start)=date('{}')".format(report_date)
df=process_tracks(pd.read_sql_query(sql,conn))
conn.close()

#print(df)

# group data for reports
def group_data(df):
    col_interval_age='Возростная\nгруппа' #'interval\nage'
    col_interval_time='Отчетный\nпериод'

    # 1st grouping index: interval_time
    def interval_time(row):
       h=row['tracking_start'].hour
       t0,t1,t2,t3=(9,13,16,21)
       str='{}: {}:00-{}:00'
       if t0<=h<t1:
           return str.format(1,t0,t1)
       elif t1<=h<t2:
           return str.format(2,t1,t2)
       elif t2<=h<t3:
           return str.format(3,t2,t3)
       else:
           return '0: non-work'

    df[col_interval_time]=df.apply (interval_time, axis=1)

    # 2nd grouping dimension: interval_age
    def interval_age(row):
       age=row['age']
       t0,t1,t2,t3=(0,20,45,99)
       str='{}: {}-{}'
       if t0<=age<t1:
           return str.format(1,t0,t1)
       elif t1<=age<t2:
           return str.format(2,t1,t2)
       else:
           return str.format(3,t2,t3)

    df[col_interval_age]=df.apply (interval_age, axis=1)

    # reduce emotion just to negative,neutral,positive
    def emotion3(row):
        emotion=row['emotion']
        if emotion in {'happiness','surprise'}:
            return 'positive'
        elif emotion in {'neutral'}:
            return 'neutral'
        elif emotion in {}:
            return 'negative'
        elif emotion in {'undefined'}:
            return 'undefined'
        else:
            raise ValueError('emotion3 unknown emotion', emotion)

    df['emotion3']=df.apply (emotion3, axis=1)

    col_emotion_positive='П эмоции'
    col_emotion_neutral='Н эмоции'
    col_emotion_negative='О эмоции'
    col_visitor_number='Количество\nпосетителей'

    def report_2v0(x):
        d=dict()
        d[col_visitor_number]=x['trackid'].agg('count')
        d[col_emotion_positive]=(x['emotion3'] == 'positive').sum()
        d[col_emotion_neutral]=(x['emotion3'] == 'neutral').sum()
        d[col_emotion_negative]=(x['emotion3'] == 'negative').sum()
        ans=pd.Series(d)
        return ans

    #print(df)
    all=df.groupby([col_interval_time, col_interval_age]).apply(report_2v0)
    returning=df[df['prevtrackid'].notnull()].groupby([col_interval_time, col_interval_age]).apply(report_2v0)
    renaming_scheme={col_visitor_number:'Количество\nвернувшихся'}
    returning.rename(columns=renaming_scheme, inplace=True)
    report=pd.concat([all,returning],axis=1)
    return report

report=group_data(df)

# export raw data to Excel
path=os.path.join(crmdb.get_CRMDB_dir(),output)
logging.info(path)
with pd.ExcelWriter(path) as writer:
    sheet='Report'
    report.to_excel(writer,sheet,index=True)
    df.to_excel(writer,'Raw data',index=False)

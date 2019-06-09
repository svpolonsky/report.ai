# runs during off-hours: maintain cloud infrastructure to identify returning visitors
import os
import time
from PIL import Image
import pandas as pd
import crmdb
import logging
LOGFORMAT = "%(levelname)s [%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(format=LOGFORMAT,level = logging.INFO)

import cognitive_face as CF
SUBSCRIPTION_KEY='aa80855ca8004d7aabf0a37b930c137d'
CF.Key.set(SUBSCRIPTION_KEY)
BASE_URL = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)
small_delay=0.1

def offhours():
    # CONNECT TO GROUP
    group_id='group-000'
    group_name='report.ai'
    groups=CF.large_person_group.list()

    group_ids=[g['largePersonGroupId'] for g in groups]

    if group_id in group_ids:
        logging.debug("group_id {} exists".format(group_id))
    else:
         CF.large_person_group.create(group_id,group_name)

    #-------------------------------------------------------
    # ADD NEW PERSONS TO CLOUD
    #-------------------------------------------------------

    conn=crmdb.connect(dbname="report.ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT trackid,cloudid FROM trackstream WHERE cloudid IS NULL")
    tracks = cursor.fetchall()


    for localid,cloudid in tracks:
        logging.debug("localid={} cloudid={}".format(str(localid),str(cloudid)))
        if cloudid is None:
            # move track to cloud as person
            # use localid (aka trackid) as person name since I don't know real names
            try:
                time.sleep(small_delay)
                ans=CF.large_person_group_person.create(group_id,localid)
            except BaseException as e:
                print(e)
                logging.error('Cognitive Face API call error')
                continue

            cloudid=ans['personId']
            logging.info("moving person localid {} to cloudid {}".format(localid,cloudid))
            sql="UPDATE trackstream SET cloudid=? WHERE trackid=?"
            cursor.execute(sql,(cloudid,localid))
            conn.commit()
        # add faces to cloud
        logging.info("move faces for {} to cloud".format(localid))
        cursor.execute("SELECT faceid,cloudid FROM facestream WHERE trackid=?",(localid,))
        faceids=cursor.fetchall()
        for localfaceid,cloudfaceid in faceids:
            #print(localfaceid,cloudfaceid)
            if cloudfaceid is None:
                path=crmdb.face_image_path(localfaceid)
                try:
                    time.sleep(small_delay)
                    ans=CF.large_person_group_person_face.add(path,group_id,cloudid)
                    cloudfaceid=ans['persistedFaceId']
                except BaseException as e:
                    logging.error(str(e))
                    cloudfaceid='CognitiveFaceException'
                #print(cloudfaceid)
                logging.info("face: moved localid {} to cloudid {}".format(localfaceid,cloudfaceid))
                sql="UPDATE facestream SET cloudid=? WHERE faceid=?"
                cursor.execute(sql,(cloudfaceid,localfaceid))
                conn.commit()

    conn.close()
    try:
        CF.large_person_group.train(group_id)
    except:
        logging.error('failed to train')
        return
    i=0
    while True:
        logging.info('group training: {}'.format(i))
        i+=1
        try:
            time.sleep(5)
            res=CF.large_person_group.get_status(group_id)
            if res['status']=='succeeded':
                break
        except:
            logging.error('connection problem')

if __name__ == "__main__":
    offhours()

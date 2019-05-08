# python for FACE API: https://docs.microsoft.com/ru-ru/azure/cognitive-services/face/tutorials/faceapiinpythontutorial
# request support: https://docs.microsoft.com/en-us/azure/azure-supportability/how-to-create-azure-support-request

# free
# name=Polonsky, northeurope
# key1=aa80855ca8004d7aabf0a37b930c137d
# key2=0b6a3d8f5a974978ad1a7d92c5c30a57

import logging
LOGFORMAT = "%(levelname)s [%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
#LOGFORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=LOGFORMAT,level = logging.INFO)
#logging.basicConfig()
import os
import math
import numpy as np
import testset
import uuid
import time
from PIL import Image
import pandas as pd
import crmdb
import cognitive_face as CF
SUBSCRIPTION_KEY='aa80855ca8004d7aabf0a37b930c137d'
CF.Key.set(SUBSCRIPTION_KEY)
BASE_URL = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)




#img_url = 'https://raw.githubusercontent.com/Microsoft/Cognitive-Face-Windows/master/Data/detection1.jpg'
#result = CF.face.detect(img_url)
#print(result)


def group_run(image_paths):
    """GroupRun.

    This will group faces based on similarity in a group, and will place faces that don't have any other similar faces in a messy group.
    """

    faces = {}

    for image_path in paths:
        logging.info( str(image_path) )
        # Detect faces from target image path, 3sec delay for free Azure service
        time.sleep(3)
        detected_faces = CF.face.detect(image_path)
        logging.info( detected_faces )
        # Add detected face id to faces.
        if not detected_faces:
            print("No face detected in {}".format(image_path))
            continue
        n_faces=len(detected_faces)
        logging.info("Detected {} faces".format(n_faces))
        if n_faces != 1:
            logging.info('Expect only one face on image')
            continue
        logging.info(detected_faces[0]['faceId'])
        faces[detected_faces[0]['faceId']] = testset.person_name(image_path)

    # Call grouping, the grouping result is a group collection, each group contains similar faces.
    group_result = CF.face.group(face_ids=list(faces.keys()))
    print('group: ',group_result)
    # Face groups containing faces that are similar.
    for i, group in enumerate(group_result['groups']):
        print("Found face group {}: {}.".format(
            i + 1,
            " ".join([faces[face_id] for face_id in group])
        ))

    # Messy group contains all faces which are not similar to any other faces.
    if group_result['messyGroup']:
        print ("Found messy face group: {}.".format(
            " ".join([faces[face_id] for face_id in group_result['messyGroup']])
        ))

def centroid(rect):
    cX=int(rect['left']+rect['width']/2.0)
    cY=int(rect['top']+rect['height']/2.0)
    return {'X':cX,'Y':cY}

def dist(a,b):
    d2=float(a['X']-b['X'])**2+float(a['Y']-b['Y'])**2
    d=math.sqrt(d2)
    return d

def filter_detections(tracked_persons,detected_faces):
    # match tracker and azure detected faces
    # tracker: tracked_persons
    # azure: detected_faces
    # return filtered azure faces in tracker's order
    filtered_faces=[]
    face_centroids=[centroid(face['faceRectangle']) for face in detected_faces]
    for person in tracked_persons:
        tracker_centroid={'X':person['facebox']['xcenter'],'Y':person['facebox']['ycenter']}
        # match tracker to Azure by minimum distance between centroids
        dists=[dist(tracker_centroid,face_centroid) for face_centroid in face_centroids]
        face_index=np.argmin(dists)
        if dists[face_index]>10:
            logging.warning('dists[face_index]>10: {}'.format(dists[face_index]))
        filtered_faces.append(detected_faces[face_index])
        return filtered_faces

# example of 'identified' {'faceId': '...', 'candidates': [{'personId': '...', 'confidence': 0.72452}]}
def returning_face(identified):
    # return person with the highest confidence
    personId=None
    confidence=0.0
    for candidate in identified['candidates']:
        if candidate['confidence']>confidence:
            confidence=candidate['confidence']
            personId=candidate['personId'] # Azure or cloud
    return {'personId':personId, 'confidence':confidence}

def analyze_face(image_path,tracked_persons):
    # look only for tracked faces
    logging.debug('path: '+str(image_path) )
    logging.debug('person: '+testset.person_name(image_path))
    image=Image.open(str(image_path))
    #image.show()
    # Detect faces from target image path, 3sec delay for free Azure service
    try:
        time.sleep(3)
        detected_faces = CF.face.detect(image_path,attributes=crmdb.faceAttributes)
    except ConnectionError:
        # @@@ I need to process this: save image locally for postprocessing
        logging.error('connection error: extend the code to store image locally for postprocessing')
        detected_faces=None

    #print('detected faces:',detected_faces)
    # Add detected face id to faces.
    if not detected_faces:
        logging.warning("No face detected in {}".format(image_path))
        return

    n_faces=len(detected_faces)
    logging.debug("Detected {} faces".format(n_faces))


    filtered_faces=filter_detections(tracked_persons,detected_faces)
    faceids=[face['faceId'] for face in filtered_faces]
    # @@@ use configuration to get large_person_group_id; later use parameter threshold
    try:
        time.sleep(3)
        identified_faces=CF.face.identify(faceids,large_person_group_id='group-000',max_candidates_return=2)
    except BaseException as e:
        identified_faces=[{'faceId': None, 'candidates': []}] * len(faceids)

    for track,face,identified in zip(tracked_persons,filtered_faces, identified_faces):
        faceid='face-'+str(uuid.uuid1()) # length=36, max length for Azure is 64
        crmdb.record_face(track['trackid'],faceid,face['faceAttributes'],returning_face(identified))
        # crop face from the image and save as filename faceid
        r=face['faceRectangle']
        box=(r['left'], r['top'], r['left']+r['width'], r['top']+r['height'])
        region = image.crop(box)
        #@@@ call crmdb.save_face_image
        path=os.path.expanduser("~/CRMDB/faces")
        outfile=os.path.join(path, faceid+".jpg")
        region.save(outfile)


def test_image(fname):
    """
    Test on sequence of images. One face per track.
    """
    image_paths=testset.image_paths(fname)
    face_list_id='aaa-111'
    #CF.face_list.create(face_list_id,name='report.ai')
    #ls=CF.face_list.list()
    #print(ls)
    for image_path in image_paths:
        # this replaces face tracker for a while
        tracking_start=crmdb.now()
        bbox=testset.read_bounding_box(image_path)
        # tracker should provide an ID for each tracke person
        personid='person-'+str(uuid.uuid1())
        logging.info(personid)
        # tracker might track multiple persons, hence array for bbox
        analyze_face(image_path,[{'personid':personid,'facebox':bbox}])
        tracking_stop=crmdb.now()
        crmdb.record_person(personid,tracking_start,tracking_stop)

def most_probabale(l):
    # find the most frequent id in the list, possibly taking care of their weghts
    # l - list of (id,weight)
    # for now, ignore weights
    df = pd.DataFrame(l, columns = ['id'])
    ids=df.groupby('id').size().sort_values(ascending=False).index.tolist()
    try:
        id =ids[0]
    except IndexError:
        id = None
    return id

def test_video(videos):
    """
      Test on videos (sequence of images)
    """

    # initialize quality measures
    total=0
    positive=0 # positive means resturning
    true_positive=0
    true_negative=0
    false_positive=0
    false_negative=0
    # analyze videos
    for video in videos:
        current_name=testset.person_name(video)
        logging.info('true name {}'.format(current_name))
        trackid='track-'+str(uuid.uuid1())
        tracking_start=crmdb.now()
        frame_number=0
        for frame_number in [30,60]:
            path=testset.frame_path(video, frame_number)
            if path.is_file():
                logging.debug(path)
                bbox=testset.read_bounding_box(path)
                analyze_face(path,[{'trackid':trackid,'facebox':bbox}])
            else:
                break
        # the face is gone
        tracking_stop=crmdb.now()
        crmdb.record_track(trackid,tracking_start,tracking_stop,true_name=current_name)
        #-----------------------------------------------------------------------
        # quality metrics
        #-----------------------------------------------------------------------
        # majority vote to identify the track
        total+=1
        conn=crmdb.connect()
        cursor = conn.cursor()
        # ground truth: is this a returning (positive) face?
        cursor.execute("SELECT count(*) FROM trackstream WHERE true_name = ? AND cloudid NOT NULL", (current_name,))
        count=cursor.fetchone()[0]
        logging.info('GT: {} matches'.format(count))
        if count==0:
            logging.debug('There is no person named %s'%current_name)
        else:
            logging.debug('Person %s found in %s row(s)'%(current_name,count))
            positive+=1
        # what does AI think about this face? Is it returning?
        cursor.execute("SELECT previousid FROM facestream WHERE trackid=?",(trackid,))
        prevtrackids=cursor.fetchall()
        prevtrackid=most_probabale(prevtrackids)
        logging.info("AI match: {}".format(prevtrackid))
        if prevtrackid is not None:
            # positive: AI thinks the face is returning
            logging.info('AI: match')
            cursor.execute("SELECT true_name FROM trackstream WHERE trackid=?",(prevtrackid,))
            ans=cursor.fetchall()
            assert len(ans)==1
            prev_name=ans[0][0]
            if current_name==prev_name:
                logging.info('GT: match')
                true_positive+=1
            else:
                logging.info('GT: no match')
                false_positive+=1
            logging.info('name match: {} {}'.format(current_name,prev_name))
        else:
            # negative: AI thinks the face is seen for the first time
            logging.info('AI: no match')
            if count==0:
                logging.info('GT: no match')
                true_negative+=1
            else:
                logging.info('GT: match')
                false_negative+=1
        conn.close()
    # quality statistics
    print('total:',total)
    print('positive:',positive)
    print('TP:',true_positive)
    print('TN:',true_negative)
    print('FP:',false_positive)
    print('FN:', false_negative)
    return {'TP':true_positive,'FP':false_positive,'TN':true_negative,'FN':false_negative}

if __name__ == "__main__":
    fname='test_5.txt'
    videos=testset.video_paths(fname)
    #test_image(fname)
    test_video(videos)

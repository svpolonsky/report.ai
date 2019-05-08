# remove report.ai stuff in Azure's cloud
import os
import glob
import crmdb
import cognitive_face as CF
SUBSCRIPTION_KEY='aa80855ca8004d7aabf0a37b930c137d'
CF.Key.set(SUBSCRIPTION_KEY)
BASE_URL = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)

def clean_cloud():
    # this should be taked from configuration file
    group_id='group-000'
    try:
        CF.large_person_group.delete(group_id)
    except BaseException as e:
        print('cloud database not found')

def clean_local():
    # remove sqlite database
    dbfile='/home/stas/CRMDB/report.ai.db'
    try:
        os.remove(dbfile)
    except FileNotFoundError:
        print('local database not found:',dbfile)
    # remove face jpgs in faces directory
    files = glob.glob('/home/stas/CRMDB/faces/*.jpg')
    for f in files:
        os.remove(f)


if __name__ == "__main__":
    clean_local()
    clean_cloud()

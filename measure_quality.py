import random
from facestream import test_video
from offhours import offhours
import logging
LOGFORMAT = "%(levelname)s [%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(format=LOGFORMAT,level = logging.INFO)

def measure_quality(fname,ndays):
    with open(fname) as file:
        lines=[line.rstrip() for line in file]
    n=len(lines)
    ns=sorted(random.sample(range(n), ndays))
    ns.append(n)
    #ns=[6,12,17] # test_5.txt
    logging.debug(ns)
    stats=list()
    batch=0
    n1=0
    for n2 in ns:
        logging.info('batch {}: {} {}'.format(batch,n1,n2))
        stat=test_video(lines[n1:n2])
        stats.append(stat)
        offhours()
        batch+=1
        n1=n2
    print(stats)
    return stats

random.seed(21)
stats=measure_quality('test_all.txt',30)

import csv
keys = stats[0].keys()
with open('measure_quality.csv', 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(stats)

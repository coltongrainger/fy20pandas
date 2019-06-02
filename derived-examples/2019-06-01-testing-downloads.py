import pandas as pd
import random

import json

import os
import requests
from pathlib import Path

#  fakesection: Import `all.csv` (Wood's NARA metadata).

%cd ~/fy/20/pandas/derived-examples
# %ls metadata/*
df = pd.read_csv('metadata/2018-05-16-NARA-master-manifest/all.csv')

# trim spaces and remove redundant column
df.rename(str.strip, axis='columns',inplace=True)
df.drop(columns=['Box or Volume Number.1'], inplace=True)

# take sample from each record group
NARA_record_group_dict = dict([(23, 'USCS'), # Records of the Coast and Geodetic Survey
                               (24, 'Navy'), # Records of the Bureau of Naval Personnel
                               (26, 'CG'), # Records of the U.S. Coast Guard
                               (261, 'RAC') # Records of Former Russian Agencies
                              ])
sample = pd.concat([df.loc[df['Record Group'] == gp].sample(10, random_state=1)\
                    for gp in NARA_record_group_dict])

# drop entries without a valid NARA URL
ndf = sample[~sample['NARA URL'].str.contains(" ")]
# TODO pair all entries with valid NARA URLs <ccg, 2019-06-02>

#  fakesection: bulk downloads for a single entry # 

# sample a random entry
entry = ndf.sample(1, random_state=0)
nara_id = entry['NARA URL'].iloc[0].split("/")[-1]
digital_directory = entry['Digital Directory'].iloc[0]
# base_url = 'https://catalog.archives.gov/'
# record_group = "rg-0{0}".format(int(entry['Record Group'].iloc[0]))
# num_images = int(entry['Number of Images'].iloc[0])

# access NARA API
api_base = 'https://catalog.archives.gov/api/v1/'
api_url = '{0}?naIds={1}'.format(api_base, nara_id)
res = requests.get(api_url)

# create local directories if needed
paths = dict([(k, '/home/colton/fy/20/pandas/derived-examples/{0}/{1}'\
              .format(k, digital_directory))\
              for k in ['data', 'metadata']])
for path in paths:
    p = Path(path)
    if (p.exists() == False and p.is_dir() == False):
        os.mkdir(path)

# write NARA API output as json for reference
api_output = "{0}/nara_id_{1}.json".format(paths['metadata'], nara_id)
if res.status_code == 200:
    with open(api_output, 'wb') as f:
        f.write(res.content)

# parse NARA API output
entry_img_array = res.json().get('opaResponse').get('results').get('result')[0]\
                  .get('objects').get('object')

# download all images for this entry
for img_info in entry_img_array[1:-1]: 
    img_name = img_info.get('file').get('@name')
    # TODO test for mimetype "image/jpeg" here
    img_url = img_info.get('file').get('@url')
    img_res = requests.get(img_url)

    # create subdirectory if needed
    img_path = '/home/colton/fy/20/pandas/derived-examples/data/{0}/nara_id_{1}'\
               .format(digital_directory,nara_id)
    img_p = Path(img_path)
    if (img_p.exists() == False and img_p.is_dir() == False):
        os.mkdir(img_path)

    # write individual image file
    local_img_name = "{0}/{1}".format(img_path, img_name)
    if img_res.status_code == 200:
        with open(local_img_name, 'wb') as img_f:
            img_f.write(img_res.content)

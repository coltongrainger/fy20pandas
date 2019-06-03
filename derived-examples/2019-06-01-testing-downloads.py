import pandas as pd
import json
import random

from pathlib import Path
import os

import requests
import logging
import http.client

#  fakesection: setup logging for requests # 

# https://stackoverflow.com/questions/16337511/
http.client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

#  fakesection: import Wood's NARA metadata

%cd ~/fy/20/pandas/derived-examples
# %ls metadata/*
df = pd.read_csv('2018-05-16-NARA-master-manifest/all.csv')

# trim spaces and remove redundant column
df.rename(str.strip, axis='columns',inplace=True)
df.drop(columns=['Box or Volume Number.1'], inplace=True)

# take sample from each record group
NARA_record_group_dict = dict([(23, 'USCS'), # Records of the Coast and Geodetic Survey
                               (24, 'Navy'), # Records of the Bureau of Naval Personnel
                               (26, 'CG'), # Records of the U.S. Coast Guard
                               (261, 'RAC') # Records of Former Russian Agencies
                              ])
sample = pd.concat([df.loc[df['Record Group'] == gp].sample(5, random_state=1)\
                    for gp in NARA_record_group_dict])

# drop entries without a valid NARA URL
ndf = sample[~sample['NARA URL'].str.contains(" ")]
# TODO pair all entries with valid NARA URLs <ccg, 2019-06-02>

#  fakesection: download each image under a given nara_id # 

def download_nara_entry(entry): # entry is assumed to be a *DataFrame*

    # access NARA API
    nara_id = entry['NARA URL'].iloc[0].split("/")[-1]
    api_base = 'https://catalog.archives.gov/api/v1/'
    api_url = '{0}?naIds={1}'.format(api_base, nara_id)
    res = requests.get(api_url)

    # metadata from Wood's all.csv (which is redundant, given NARA's metadata)
    # base_url = 'https://catalog.archives.gov/'
    # record_group = "rg-0{0}".format(int(entry['Record Group'].iloc[0]))
    # num_images = int(entry['Number of Images'].iloc[0])
    # digital_directory = ['Digital Directory'].iloc[0]

    # parse NARA API output for metadata
    entry_img_array = res.json().get('opaResponse').get('results').get('result')[0]\
                      .get('objects').get('object')
    digital_directory = entry_img_array[0].get('file').get('@path').split("/")[-2]

    # create local directories if needed
    paths = dict([(k, '/home/colton/fy/20/pandas/derived-examples/{0}/{1}'\
                  .format(k, digital_directory))\
                  for k in ['data', 'metadata']])
    for k, val in paths.items():
        p = Path(val)
        if (p.exists() == False and p.is_dir() == False):
            os.mkdir(val)

    # write NARA API output to file for reference
    api_output = "{0}/nara_id_{1}.json".format(paths['metadata'], nara_id)
    if res.status_code == 200:
        with open(api_output, 'wb') as f:
            f.write(res.content)

    # download all images for this unique nara_id
    for img_info in entry_img_array: 

        # test for mimetype "image/jpeg"
        # we don't want "application/pdf"
        if img_info.get('file').get('@mime') == "image/jpeg":

            img_name = img_info.get('file').get('@name')
            img_url = img_info.get('file').get('@url')
            img_res = requests.get(img_url)

            # create subdirectory if needed
            img_path = '{0}/nara_id_{1}'\
                       .format(paths['data'], nara_id)
            img_p = Path(img_path)
            if (img_p.exists() == False and img_p.is_dir() == False):
                os.mkdir(img_path)

            # write a single image to file
            local_img_name = "{0}/{1}".format(img_path, img_name)
            if img_res.status_code == 200:
                with open(local_img_name, 'wb') as img_f:
                    img_f.write(img_res.content)

return None

#  fakesection: tests # 

# test
# download_nara_entry(ndf.sample(1, random_state=0))

# test apply
# ndf.groupby('NARA URL').apply(download_nara_entry)

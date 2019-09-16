import os, sys, traceback
from os import listdir
from os.path import isfile, join
import requests
import bs4
import multiprocessing
from urllib.parse import urlparse
import hashlib
import time
import json
from pathlib import Path
import glob
import urllib.parse
import base64

poolSize = 10
gateUrl = 'https://j7f6n2sy1e.execute-api.us-west-1.amazonaws.com/stage'

def uploadImage(params):
    imageFile = params[0]
    jsonFile = params[1]
    print('uploading image {}: {}'.format(imageFile, jsonFile))
    with open(jsonFile) as f:
        jsonContents = f.read()
        dict = json.loads(jsonContents)
        dict['customJson'] = 'true'
        dict['media_type'] = 'mural'
        name=os.path.basename(imageFile)
        jdict = bytes(json.dumps(dict).encode('utf-8'))
        userTags=urllib.parse.quote(base64.encodebytes(jdict))
        url = '{}?name={}&user_meta={}'.format(gateUrl, name, userTags)
        r = requests.get(url)
        if r.ok:
            uploadUrl = json.loads(r.text)['uploadUrl']
            with open(imageFile, 'rb') as f:
                imgData = f.read()
                r2 = requests.put(uploadUrl, data=imgData, headers={'content-type':'binary/octet-stream'})
                if r2.ok:
                    print('succesfully uploaded {}'.format(imageFile))
        else:
            print('upload failure for {}'.format(imageFile))

def ingestImages(imageDir):
    # find json first
    print(imageDir)
    jsons = glob.glob(join(imageDir, '*.json'))
    if len(jsons):
        jsonFile = jsons[0]
        print('found json: {}'.format(jsonFile))
        imageFiles = glob.glob(join(imageDir,'**','*.jpg'))
        if len(imageFiles):
            paramsList = [(imgF, jsonFile) for imgF in imageFiles]
            pool = multiprocessing.Pool(poolSize)
            res = pool.map(uploadImage, paramsList)

if __name__ == '__main__':
    folder = sys.argv[1]
    # imageDirs = [join(folder, d) for d in listdir(folder)]
    # for d in imageDirs:
    #     ingestImages(d)
    jsons = glob.glob(join(folder, '**', '*.json'), recursive=True)
    if len(jsons):
        jsonFile = jsons[0]
        print('found json: {}'.format(jsonFile))
        imageFiles = glob.glob(join(folder,'**','*.jpg'), recursive=True)
        if len(imageFiles):
            paramsList = [(imgF, jsonFile) for imgF in imageFiles]
            print('found {} total uploads'.format(len(paramsList)))
            pool = multiprocessing.Pool(poolSize)
            res = pool.map(uploadImage, paramsList)

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

scrapeFolder = 'scraped'

def scrapeMuralsUrls(pageUrl):
    s = requests.Session()
    r = s.get(pageUrl)
    scheme =  urlparse(pageUrl).scheme
    host = urlparse(pageUrl).hostname
    urls = []
    if r.ok:
        bs = bs4.BeautifulSoup(r.text, 'html.parser')
        links = bs.select('#block-system-main > div > div > div.view-content > div.views-row > div.views-field.views-field-title > span > a')
        urls = [scheme + '://' + host+tag['href'] for tag in links]
        print('retrieved {} urls from page {}'.format(len(urls), pageUrl))
        return urls
    else:
        raise ValueError('failed to retrieve html {}: {}'.format(r.status_code, r.text))

def scrapeImages(bs):
    urls =[img['src'] for img in bs.select('.gallery-frame > ul > li > img')]
    urls = [u.split('?')[0] for u in urls]
    return urls

def downloadImage(imgUrl, folder):
    fName = imgUrl.split('/')[-1]
    r = requests.get(imgUrl)
    if r.ok:
        fPath = join(folder, fName)
        if not os.path.isfile(fPath):
            with open(fPath, 'wb') as f:
                f.write(r.content)
            print('downloaded {} -> {}'.format(imgUrl, fPath))
        else:
            print('cache hit {} -> {}'.format(imgUrl, fPath))

warnings = []
def scrapeMetadata(bs, url = None):
    meta = {}

    r = bs.select('.field.field-name-field-murals-artist.field-type-taxonomy-term-reference.field-label-inline.clearfix > div.field-items')
    if len(r) >= 1:
        chldrn = [c for c in r[0].children]
        meta['artist'] = str(r[0].string).strip()
    else:
        meta['artist'] = 'n/a'
        warnings.append({'url': url, 'msg':"can't find artist field"})

    r = bs.select('.field.field-name-field-murals-address.field-type-text-long.field-label-inline.clearfix > div.field-items > div > p')
    if len(r) >= 1:
         chldrn = [c for c in r[0].children]
         try:
             meta['location'] = chldrn[0].strip()
             if len(chldrn) > 1:
                 meta['location_url'] = chldrn[1]['href']
         except:
             meta['location'] = 'n/a'
             meta['location_url'] = 'n/a'
             warnings.append({'url': url, 'msg':"can't find address field"})
    else:
        meta['location'] = 'n/a'
        meta['location_url'] = 'n/a'
        warnings.append({'url': url, 'msg':"can't find address field"})

    r = bs.select('.field.field-name-field-murals-size.field-type-text.field-label-inline.clearfix > div.field-items')
    if len(r) >= 1:
        chldrn = [c for c in r[0].children]
        meta['size'] = str(r[0].string).strip()
    else:
        meta['size'] = 'n/a'
        warnings.append({'url':url, 'msg': "can't find size field"})

    r = bs.select('.field.field-name-field-murals-medium.field-type-text.field-label-inline.clearfix > div.field-items > div')
    if len(r) >= 1:
         chldrn = [c for c in r[0].children]
         meta['medium'] = str(r[0].string).strip()
    else:
         meta['medium'] = 'n/a'
         warnings.append({'url':url, 'msg': "can't find medium field"})

    r = bs.select('.field.field-name-field-murals-date.field-type-text.field-label-inline.clearfix > div.field-items > div')
    if len(r) >= 1:
         chldrn = [c for c in r[0].children]
         meta['date'] = str(r[0].string).strip()
    else:
         meta['date'] = 'n/a'
         warnings.append({'url':url, 'msg': "can't find date field"})

    r = bs.select('.field.field-name-field-murals-type.field-type-list-text.field-label-inline.clearfix > div.field-items > div')
    if len(r) >= 1:
         chldrn = [c for c in r[0].children]
         types = [str(t.string).strip() for t in r[0]]
         meta['types'] = types
    else:
         meta['types'] = 'n/a'
         warnings.append({'url':url, 'msg': "can't find types field"})

    r = bs.select('.field.field-name-field-murals-description.field-type-text-long.field-label-above > div.field-items > div > p')
    if len(r) >= 1:
        chldrn = [c for c in r[0].children]
        try:
            meta['description'] = chldrn[0].strip()
        except:
            meta['description'] = 'n/a'
            warnings.append({'url':url, 'msg': "can't find description field"})
    else:
        meta['description'] = 'n/a'
        warnings.append({'url':url, 'msg': "can't find description field"})

    return meta

skipIfHit = False
def scrapeMuralData(muralUrl):
    global scrapeFolder, warnings, skipIfHit
    s = requests.Session()
    muralKey = itemHash = hashlib.sha1((muralUrl).encode('utf-8')).hexdigest()
    dirPath = os.path.join(scrapeFolder, muralKey)

    if os.path.isdir(dirPath) and skipIfHit:
        print('SKIP: cache hit for mural {}'.format(muralUrl))
        return

    r = s.get(muralUrl)
    if r.ok:
        meta = {'muralUrl': muralUrl}
        imagesDir = os.path.join(dirPath, 'images')
        if not os.path.isdir(dirPath):
            os.makedirs(dirPath)
            os.makedirs(imagesDir)

        bs = bs4.BeautifulSoup(r.text, 'html.parser')

        imgUrls = scrapeImages(bs)
        meta['images'] = imgUrls
        meta['images_total'] = len(imgUrls)
        for url in imgUrls:
            downloadImage(url, imagesDir)

        try:
            meta.update(scrapeMetadata(bs, muralUrl))
            # print(json.dumps(meta, indent=4))
        except:
            type, err, tb = sys.exc_info()
            print('error scraping {}: {}'.format(muralUrl, err))
            raise

        with open(join(dirPath, 'meta.json'), 'w') as f:
            f.write(json.dumps(meta, indent=4))
        if len(warnings):
            with open(join(scrapeFolder, 'warnings.txt'), 'a') as f:
                for w in warnings:
                    f.write('{}\t{}\n'.format(w['msg'],w['url']))
    else:
        raise ValueError('failed to retrieve html {}: {}'.format(r.status_code, r.text))

def readTypesFromJsons(folder):
    jsons = list(Path(folder).glob('**/*.json'))
    print('found {} JSONs'.format(len(jsons)))
    types = {}
    for j in jsons:
        with open(j, 'r') as f:
            jObj = json.loads(f.read())
            if 'types' in jObj:
                for t in jObj['types']:
                    if not t in types:
                        types[t] = 0
                    types[t] += 1
            else:
                print('file {} does not have "types" field'.format(j))
    print('here are all the types')
    for t,c in types.items():
        print('\t{}\t{}'.format(t,c))

if __name__ == '__main__':
    host = 'https://www.muralconservancy.org'
    nPages = 89
    poolSize = 10
    cacheFolder = sys.argv[1] if len(sys.argv) > 1 else './murals-scraped'
    readTypes = True if len(sys.argv) == 3 and sys.argv[2] == '--types' else False
    if not os.path.isdir(scrapeFolder):
        os.makedirs(scrapeFolder)
    else:
        if os.path.isfile(join(scrapeFolder, 'warnings.txt')):
            os.remove(join(scrapeFolder, 'warnings.txt'))

    pool = multiprocessing.Pool(poolSize)
    pageUrls = ['{}/murals?page={}'.format(host, pageIdx) for pageIdx in range(0,nPages)]


    ## TEST scrapeMuralsUrls
    # muralsUrls = scrapeMuralsUrls(pageUrls[0])

    ## TEST scrapeMuralData
    # url='https://www.muralconservancy.org/murals/111th-street-jesus'
    # url='https://www.muralconservancy.org/murals/shared-hope#slide-1-field_murals_image-579'
    # url='https://www.muralconservancy.org/murals/dial-900-society'
    # url='https://www.muralconservancy.org/murals/circus-train'
    # url='https://www.muralconservancy.org/murals/goose-stepping-over-innocense'
    # url='https://www.muralconservancy.org/murals/wind'
    # scrapeMuralData(url)

    if True:
        if readTypes:
            readTypesFromJsons(scrapeFolder)
        else:
            try:
                res = pool.map(scrapeMuralsUrls, pageUrls)
                allUrls = []
                for r in res:
                    allUrls.extend(r)
                # print('TOTAL URLS', len(allUrls))
                # print(allUrls[0])
                print('found {} mural pages'.format(len(allUrls)))

                res = pool.map(scrapeMuralData, allUrls)
                print('done.')
            except:
                type, err, tb = sys.exc_info()
                print('caught exception:', err)
                traceback.print_exc(file=sys.stdout)

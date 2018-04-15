BASE_URL = "http://api.brain-map.org/api/v2"

from urllib.request import urlopen, urlretrieve
import xmltodict
import os
from threading import Thread
from queue import Queue

MODEL = "Atlas"
ATLAS_ID = 1

DOWNSAMPLE = 3
ATLAS_IMAGE_URL = "atlas_image_download"

IMAGE_DIRECTORY = "images"

XML_URL = BASE_URL + "/data/query.xml?criteria=model::" + MODEL + ",rma::criteria,[id$eq" + str(ATLAS_ID) + "],rma::include,atlas_data_sets(atlas_images(treatments))"

class Worker(Thread):
    def __init__(self, queue, daemon=True):
        Thread.__init__(self)
        self.queue = queue
        self.setDaemon(daemon)
        
    def run(self):
        while True:
            target, args = self.queue.get()
            target(*args)
            self.queue.task_done()

NUMBER_OF_WORKERS = 10
PROCESSING_QUEUE = Queue()
WORKERS = [Worker(PROCESSING_QUEUE).start() for i in range(NUMBER_OF_WORKERS)]

def getImageURL(base: str, imageType: str, id: str, downsample: int) -> str:
    return '/'.join([base, imageType, id]) + "?" + '&'.join(["downsample=" + str(downsample)])
    
def getXMLImageList(XMLData) -> ['atlas-image']:
    return XMLData['Response']['atlases']['atlas']['atlas-data-sets']['atlas-data-set']['atlas-images']['atlas-image']
    
def saveImages(base: str, imageType: str, XMLData: dict, imageDirectory: str, downsample: int, queue) -> int:
    atlasImages = getXMLImageList(XMLData)
    for i in range(len(atlasImages)):
        id = atlasImages[i]['id']['#text']
        queue.put((saveImageFromURL, [getImageURL(base, imageType, id, downsample), imageDirectory, id + '-' + str(i) + '.jpg'])) 
        

def createDirectory(dirName: str) -> None:
    if not os.path.exists(dirName):
        os.makedirs(dirName)

def saveImage(imageData: str, imageDirectory: str, imageName: str) -> None:
    with open(os.path.join(imageDirectory, imageName)) as fileHandle:
        fileHandle.write(imageData)

def saveImageFromURL(imageURL: str, imageDirectory: str, imageName: str) -> None:
    urlretrieve(imageURL, os.path.join(imageDirectory, imageName))

def getURLRequestData(requestURL: str) -> dict:
    fileHandle = urlopen(requestURL)
    data = fileHandle.read()
    fileHandle.close()
    data = xmltodict.parse(data)
    return data

createDirectory(IMAGE_DIRECTORY)
XMLData = getURLRequestData(XML_URL)
saveImages(BASE_URL, ATLAS_IMAGE_URL, XMLData, IMAGE_DIRECTORY, DOWNSAMPLE, PROCESSING_QUEUE)
PROCESSING_QUEUE.join()
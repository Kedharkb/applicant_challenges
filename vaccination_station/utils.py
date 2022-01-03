import datetime

def convertToEpochTime(date):
    return int(datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S%z').timestamp())
    
def convertEpochToDate(epochTime):
    return datetime.datetime.utcfromtimestamp(epochTime).strftime('%Y-%m-%dT%H:%M:%S%z')



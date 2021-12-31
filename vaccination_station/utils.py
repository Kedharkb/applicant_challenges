import datetime
def convertToDate(date):
    return int(datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S%z').timestamp())
    
def convertDateToString(date):
    return slot['date'].strftime('%Y-%m-%dT%H:%M:%S%z')
import json
import datetime
import traceback
import sys 

from utils import convertToDate
from utils import convertDateToString

timeSheet = {}
bookedSlotsSheet = {}
reminderSlots = {}



def catch_exception(func, exception=Exception):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except exception as err:
            print(traceback.format_exc())
        else:
            return result
    return wrapper

def slotNotifier(f):
    def wrap(*args, **kwargs):
        return_value = f(*args, **kwargs)
        for email, value in reminderSlots.items():
            if value['date'] in timeSheet[value['doctor']]:
                print('Notification Sent to' + email) 
        return return_value
    return wrap


def loadSlots(availableTimeSlots=[]):
    
    if(len(availableTimeSlots)==0):
        f = open('initial-time-slots.json')
        availableTimeSlots = json.load(f)
    
    for slot in availableTimeSlots:
        if not slot['doctor'] in timeSheet: 
            timeSheet[slot['doctor']] = []
        timeSheet[slot['doctor']].append(convertToDate(slot['date'])) 
    return timeSheet




''' Function to create appointment'''
@catch_exception
def bookSlot(slotDetails, userDetails):

    preferredDoctor = slotDetails['doctor']
    preferredSlot = convertToDate(slotDetails['date'])
    availableTimeSlots = timeSheet[preferredDoctor]
    
    if len(availableTimeSlots) == 0: return False,timeSheet,bookedSlotsSheet

    if preferredSlot in availableTimeSlots:
        availableTimeSlots.remove(preferredSlot)
        if not preferredDoctor in bookedSlotsSheet: 
            bookedSlotsSheet[preferredDoctor] = []
        bookedSlotsSheet[preferredDoctor].append({'date':preferredSlot,**userDetails}) 
        return True,timeSheet, bookedSlotsSheet
    
    return False,timeSheet, bookedSlotsSheet




@catch_exception
def getBookedSlots(doctor):
    bookedSlots = []
    for obj in bookedSlotsSheet[doctor]:
        bookedSlots.append(obj['date'])
    return  bookedSlots   


''' Function to create timeslot'''
@catch_exception
@slotNotifier
def createTimeSlot(slots):
    statusObjList = []
    for slot in slots:
        statusObj = {}
        slotDate = convertToDate(slot['date'])
        doctor = slot['doctor']
        availableTimeSlots = timeSheet[doctor]
        availableTimeSlots.sort()
        statusObj[slotDate] = True
        statusObj['doctor'] = doctor 
        bookedSlots = getBookedSlots(doctor)
        
        if slotDate in availableTimeSlots or slotDate in bookedSlots:  
            statusObj[slotDate] = False
            statusObjList.append(statusObj)
            continue
        upper = min([ i for i in availableTimeSlots if i >= slotDate], key=lambda x:abs(x-slotDate),default=[])
        lower = min([ i for i in availableTimeSlots if i < slotDate], key=lambda x:abs(x-slotDate),default=[])
        
        slotPlus15 = datetime.datetime.fromtimestamp(slotDate) + datetime.timedelta(minutes = 15)
        slotPlus15 = int(slotPlus15.timestamp())

        if(slotDate not in timeSheet[doctor] and not upper and slotDate >= lower):  
            timeSheet[doctor].append(slotDate)
        elif(slotDate not in timeSheet[doctor] and not lower and slotDate <= upper):
            timeSheet[doctor].append(slotDate)
        elif( slotDate not in timeSheet[doctor] and slotDate >= lower and slotPlus15 <= upper): 
            timeSheet[doctor].append(slotDate)
        else: statusObj[slotDate] = False
        
        statusObjList.append(statusObj)
    return statusObjList, timeSheet, bookedSlotsSheet
    

''' Function to cancel appointment'''
@catch_exception
@slotNotifier
def cancelBooking(slotDetails):
    status = False
    doctor = slotDetails['doctor']
    date =  convertToDate(slotDetails['date'])
    for (idx, item) in enumerate(bookedSlotsSheet[doctor]):
        if item['date'] == date:
            slot = bookedSlotsSheet[doctor].pop(idx)
            timeSheet[doctor].append(item['date']) 
            status =True
            break
    return status, timeSheet, bookedSlotsSheet
  


''' Function to subscribe for notification'''
@catch_exception
def subscribeNotification(slotDetails, userDetails):
    slot = {**slotDetails, **userDetails}
    slot['date'] =  convertToDate(slotDetails['date'])
    if not userDetails['email'] in reminderSlots: reminderSlots[userDetails['email']] = {}
    reminderSlots[userDetails['email']] = {'doctor': slotDetails['doctor'], 'date':  slot['date']}
    return reminderSlots


if __name__ == "__main__":
    loadSlots()
    print(sys.argv)
    if  sys.argv[1] == "1" :
        slotDetails = eval(sys.argv[2])
        userDetails = eval(sys.argv[3])
        status,timeSheet,bookedSlotsSheet = bookSlot(slotDetails,userDetails)
        print(status,timeSheet,bookedSlotsSheet)
    
    elif sys.argv[1] == "2" :
        slots = eval(sys.argv[2])
        statusObjList, timeSheet, bookedSlotsSheet = createTimeSlot(slots)
        print(statusObjList,timeSheet,bookedSlotsSheet)

    elif sys.argv[1] == "3" :
        slot = eval(sys.argv[2])
        status, timeSheet, bookedSlotsSheet = cancelBooking(slot)
        print(status,timeSheet,bookedSlotsSheet)

    
    elif sys.argv[1] == "4" :
        slotDetails = eval(sys.argv[2])
        userDetails = eval(sys.argv[3])
        status, timeSheet, bookedSlotsSheet = subscribeNotification(slotDetails,userDetails)
        print(status,timeSheet,bookedSlotsSheet)


    # slotDetails = {'date': '2021-01-01T08:00:00+00:00','doctor': "Dr. Smith"}
    # userDetails = {'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar.kb@gmail.com'}
     
    # print("timeSheet",timeSheet)
    # print("bookedslotsheet",bookedSlotsSheet)
    # print(status,bookedSlots,availableTimeSlots)
    # print("*"*100)
    # slotDetails = {'date':'2021-01-01T08:15:00+00:00','doctor': "Dr. Smith"} 
    # bookSlot(slotDetails,userDetails) 
 
    # slots = [{'date':'2021-01-01T08:00:00+00:00','doctor': "Dr. Smith"},{'date':'2021-01-01T08:45:00+00:00','doctor': "Dr. Smith"},{'date':'2021-01-01T08:47:00+00:00','doctor': "Dr. Smith"}]
    # print(statusObjList)
   
    
 
    # statusObjList, timeSheet, bookedSlotsSheet = cancelBooking( {'date':'2021-01-01T08:15:00+00:00','doctor': "Dr. Smith"} )
    
    # print(bookedSlots,availableTimeSlots)
    # slotDetails = {'date':'2021-01-01T08:00:00+00:00','doctor': "Dr. Smith"}
    # userDetails = {'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar.kb@gmail.com'}
    # reminderSlots = subscribeNotification(slotDetails,userDetails) 
    # print(reminderSlots)

    # statusObjList, timeSheet, bookedSlotsSheet = cancelBooking( {'date':'2021-01-01T08:00:00+00:00','doctor': "Dr. Smith"} )




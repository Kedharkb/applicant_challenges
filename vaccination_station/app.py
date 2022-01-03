import json
import datetime
import traceback
import sys 
import copy

from utils import convertToEpochTime, convertEpochToDate

timeSheet = {}
bookedSlotsSheet = {}
reminderSlots = {}
stringJson = {}


def catch_exception(func, exception=Exception):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except exception as err:
            print(traceback.format_exc())
        else:
            return result
    return wrapper

def slot_notifier(f):
    def wrap(*args, **kwargs):
        return_value = f(*args, **kwargs)
        for email, value in reminderSlots.items():
            if any(x >= value['startDate'] and x <= value['endDate'] for x in timeSheet[value['doctor']]):
                print('Notification Sent to' + email) 
        return return_value
    return wrap

def covert_epochtime_to_String(f):
    def wrap(*args, **kwargs):
        return_value = copy.deepcopy(f(*args, **kwargs))
 
        if "timeSheet" in return_value["data"]:
            for key, value in return_value["data"]["timeSheet"].items():
                return_value["data"]["timeSheet"][key] = [convertEpochToDate(date) for date in value]
        
        if "bookedSlotsSheet" in return_value["data"]:
            for key, value in return_value["data"]["bookedSlotsSheet"].items():
                return_value["data"]["bookedSlotsSheet"][key] = [{**obj , "date":convertEpochToDate(obj["date"])} for obj in value]        
        
        if "reminderSlots" in return_value["data"]:
            for key, value in return_value["data"]["reminderSlots"].items():
                return_value["data"]["reminderSlots"][key] = {**value , "startDate":convertEpochToDate(value["startDate"]), "endDate": convertEpochToDate(value["endDate"])}        
        
        return return_value

    return wrap    

def loadSlots(availableTimeSlots=[]):
    global timeSheet, bookedSlotsSheet, reminderSlots
    if(len(availableTimeSlots)==0):
        f = open('initial-time-slots.json')
        availableTimeSlots = json.load(f)
    
    for slot in availableTimeSlots:
        if not slot['doctor'] in timeSheet: 
            timeSheet[slot['doctor']] = []
        timeSheet[slot['doctor']].append(convertToEpochTime(slot['date'])) 
    return timeSheet


def loadStringsJson(): 
    global stringJson
    f = open('strings.json')
    stringJson = json.load(f)
    return stringJson


''' Function to create appointment'''
@covert_epochtime_to_String
@catch_exception
def bookSlot(slotDetails, userDetails):
    if not slotDetails or not userDetails:
         return {"status":False, 
         "message": stringJson['missing_input'], 
         "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }
    
    preferredDoctor = slotDetails['doctor']
    preferredSlot = convertToEpochTime(slotDetails['date'])
    availableTimeSlots = timeSheet[preferredDoctor]
    
    if len(availableTimeSlots) == 0: return {
         "status":False, 
         "message": stringJson['empty_slots'], 
         "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }
    
    if preferredSlot in availableTimeSlots:
        availableTimeSlots.remove(preferredSlot)
        if not preferredDoctor in bookedSlotsSheet: 
            bookedSlotsSheet[preferredDoctor] = []
        bookedSlotsSheet[preferredDoctor].append({'date':preferredSlot,**userDetails}) 
        return {
         "status":True, 
         "message": stringJson['slot_booked'], 
         "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }
    
    return {
         "status":False, 
         "message": stringJson['slot_unavailable'], 
         "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }




@catch_exception
def getBookedSlots(doctor):
    bookedSlots = []
    for obj in bookedSlotsSheet.get(doctor,[]):
        bookedSlots.append(obj['date'])
    return  bookedSlots   


''' Function to create timeslot'''
@covert_epochtime_to_String
@catch_exception
@slot_notifier
def createTimeSlot(slots=[]):
    
    statusObjList = []
    if not slots:
        return { "statusObjList":statusObjList, 
                 "message": stringJson['missing_input'], 
                 data: {"timeSheet":timeSheet, 
                 "bookedSlotsSheet": bookedSlotsSheet } }
    
    
    for slot in slots:
        statusObj = {}
        slotDate = convertToEpochTime(slot['date'])
        doctor = slot['doctor']
        
        availableTimeSlots = timeSheet[doctor]
        availableTimeSlots.sort()
        statusObj[convertEpochToDate(slotDate)] = True
        statusObj['message'] = stringJson['slot_creation_successful']
        statusObj['doctor'] = doctor 
        
        bookedSlots = getBookedSlots(doctor)
        
        if slotDate in availableTimeSlots or slotDate in bookedSlots:  
            statusObj[convertEpochToDate(slotDate)] = False
            statusObj['message'] = stringJson['slot_creation_unsuccessful']
            statusObjList.append(statusObj)
            continue
        

        upper = min([ i for i in availableTimeSlots if i >= slotDate], key=lambda x:abs(x-slotDate),default=[])
        lower = min([ i for i in availableTimeSlots if i < slotDate], key=lambda x:abs(x-slotDate),default=[])
        
        slotPlus15 = datetime.datetime.fromtimestamp(slotDate) + datetime.timedelta(minutes = 15)
        slotPlus15 = int(slotPlus15.timestamp())

        cond1 = (slotDate not in timeSheet[doctor] and not upper and slotDate >= lower)
        cond2 = (slotDate not in timeSheet[doctor] and not lower and slotDate <= upper)
        cond3 = ( slotDate not in timeSheet[doctor] and upper and lower and slotDate >= lower and slotPlus15 <= upper)
        
        if cond1 or cond2 or cond3:  
            timeSheet[doctor].append(slotDate)
        else: 
            statusObj[convertEpochToDate(slotDate)] = False
            statusObj['message'] = stringJson['slot_creation_unsuccessful']

        statusObjList.append(statusObj)
    
    return {"statusObjList":statusObjList, "data": {"timeSheet":timeSheet, "bookedSlotsSheet": bookedSlotsSheet } } 
    

''' Function to cancel appointment'''
@covert_epochtime_to_String
@catch_exception
@slot_notifier
def cancelBooking(slotDetails= {}):

    if not slotDetails:
        return {"status":False, 
        "message": stringJson['missing_input'], 
        "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }
    
    status = False
    doctor = slotDetails['doctor']
    date =  convertToEpochTime(slotDetails['date'])
    
    for (idx, item) in enumerate(bookedSlotsSheet.get(doctor,[])):
        if item['date'] == date:
            slot = bookedSlotsSheet[doctor].pop(idx)
            timeSheet[doctor].append(item['date']) 
            status =True
            break
    
    if status: return {
         "status":True, 
         "message": stringJson['slot_cancelled'], 
         "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }       
    
    else: return {
         "status":False, 
         "message": stringJson['invalid_slot'], 
         "data":{"timeSheet":timeSheet,"bookedSlotsSheet":bookedSlotsSheet } }
  


''' Function to subscribe for notification'''
@covert_epochtime_to_String
@catch_exception
def subscribeNotification(slotDetails= {}, userDetails= {}):

    if not slotDetails or not userDetails:
         return {"status":False, 
         "message": stringJson['missing_input'], 
         "data": {"reminderSlots":reminderSlots }
          } 
    
    slot = {**slotDetails, **userDetails}
    slot['startDate'] =  convertToEpochTime(slotDetails['startDate'])
    slot['endDate'] =  convertToEpochTime(slotDetails['endDate'])
    
    if not userDetails['email'] in reminderSlots: reminderSlots[userDetails['email']] = {}
    reminderSlots[userDetails['email']] = {'doctor': slotDetails['doctor'], 'startDate':  slot['startDate'], 'endDate':slot['endDate']}
    
    return {"status":True, "message": stringJson['notification_subscribed'], "data": {"reminderSlots":reminderSlots }}


if __name__ == "__main__":
    loadStringsJson()
    loadSlots()
    print(sys.argv)
    if  sys.argv[1] == "1" :
        slotDetails = eval(sys.argv[2])
        userDetails = eval(sys.argv[3])
        result = bookSlot(slotDetails,userDetails)
        print(result)
    
    elif sys.argv[1] == "2" :
        slots = eval(sys.argv[2])
        result = createTimeSlot(slots)
        print(result)

    elif sys.argv[1] == "3" :
        slot = eval(sys.argv[2])
        result = cancelBooking(slot)
        print(result)

    
    elif sys.argv[1] == "4" :
        slotDetails = eval(sys.argv[2])
        userDetails = eval(sys.argv[3])
        result = subscribeNotification(slotDetails,userDetails)
        print(result)


    # slotDetails = {'date': '2021-01-01T08:00:00+00:00','doctor': "Dr. Smith"}
    # userDetails = {'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar1.kb@gmail.com'}  
    # result = bookSlot(slotDetails,userDetails) 
    # print(result)
    # print("*"*100)
    # slotDetails = {'date': '2021-01-01T08:15:00+00:00','doctor': "Dr. Smith"}
    # userDetails = {'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar2.kb@gmail.com'}
    # result = bookSlot(slotDetails,userDetails) 
    # print(result)
    # print("*"*100)
    # slotDetails = {'date': '2021-01-01T08:30:00+00:00','doctor': "Dr. Smith"}
    # userDetails = {'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar3.kb@gmail.com'}
    # result = bookSlot(slotDetails,userDetails) 
    # print(result)
    # print("*"*100)
    # slotDetails = {'startDate':'2021-01-01T08:00:00+00:00','endDate':"2021-01-02T08:00:00+00:00",'doctor': "Dr. Smith"}
    # userDetails = {'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar4.kb@gmail.com'}
    # result = subscribeNotification(slotDetails,userDetails) 
    # print(result)
    # print("*"*100)
    # result = cancelBooking({'date': '2021-01-01T08:15:00+00:00','doctor': "Dr. Smith"})
    # print(result)
    # print("*"*100)
    # # print("bookedslotsheet",bookedSlotsSheet)
    # slots = [{'date':'2021-01-01T07:30:00+00:00','doctor': "Dr. Smith"},{'date':'2021-01-01T07:45:00+00:00','doctor': "Dr. Smith"},{'date':'2021-01-02T09:15:00+00:00','doctor': "Dr. Lauterbach"}]
    # result = createTimeSlot(slots)
    # print(result)
    # print("*"*100)
    # print(bookedSlots,availableTimeSlots)
    # print(reminderSlots)
    # statusObjList, timeSheet, bookedSlotsSheet = cancelBooking( {'date':'2021-01-01T08:00:00+00:00','doctor': "Dr. Smith"} )




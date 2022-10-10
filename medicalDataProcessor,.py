from asyncio.windows_events import NULL
import json
import re
import hashlib

# data files
configFile, dataFile = 'config.json', 'data.json'

# user types / privilege levels
privilege_levels = ['patient', 'lab staff', 'pharmacy staff', 'nurse', 'doctor']

# sensitivity levels
sensLvlMap = {
    '1': 'low',
    '2': 'medium',
    '3': 'high'
}

# data types
dataTypeMap = {
    '1': 'personal details',
    '2': 'sickness details',
    '3': 'drug prescriptions',
    '4': 'lab test prescriptions'
}

# allowed actions
allowed = {
    'patient': ['view my records'],
    'lab staff': ['view all records', 'filter and view records by username'],
    'pharmacy staff': ['view all records', 'filter and view records by username'],
    'nurse': ['view all records', 'filter and view records by username'],
    'doctor': ['view all records', 'filter and view records by username', 'add new record']
}

#exit function
def exitApp():
    input('> Press ENTER to exit.')
    exit()


# check existancy of a data
def isExists(dataToCheck, field, filename):
    data = []
    with open(filename) as fileData:
        data = json.load(fileData)
    for row in data:
        if row[field] == dataToCheck:
            return True
    return False


# allow by sensitivity level
def isAllowedBySensLvl(sensLvl, privilegeLevel):
    if sensLvl == 'high' and privilegeLevel in ['patient', 'doctor']: return True
    if sensLvl == 'medium' and privilegeLevel in ['patient', 'doctor', 'nurse']: return True
    if sensLvl == 'low': return True
    return False

# validate username
def validateUsername(username):
    return re.match("^[a-zA-Z0-9_.-]+$", username),not(isExists(username, 'username', configFile))


# hass password
def hash(strPsswd):
    return hashlib.md5(strPsswd.encode()).hexdigest()


# add user data to the config.json file
def addData(userData, filename):
    data = []
    with open(filename) as fileData:
        data = json.load(fileData)
    data.append(userData)
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def register():
    # get username and validate it
    is_valid_username, is_avaialble_username = False, False
    while (not is_valid_username or not is_avaialble_username):
        username = input('> Enter a username: ')
        is_valid_username, is_avaialble_username = validateUsername(username)
        if (not is_valid_username):
            print('> Invalid username. Try again.')
        elif (not is_avaialble_username):
            print('> Username already taken. Enter new one.')

    # get password and hash it using md5
    hashedPassword = hash(input('> Enter a password: '))

    # get privilege level and validate
    is_valid_role = False
    while (not is_valid_role):
        privilegeLevel = input('> Select user role from' + str(privilege_levels) + ': ')
        is_valid_role = privilegeLevel in privilege_levels
        if (not is_valid_role):
            print('> Invalid user role. Try again.')

    # privilege_level
    if privilegeLevel == 'patient':
        userType = 'patient'
    else:
        userType = 'staff'
    
    # create user record and save it to the config.json file
    userRecord = {
        'username': username,
        'password': hashedPassword,
        'userType': userType,
        'privilegeLevel': privilegeLevel
    }
    addData(userRecord, configFile)
    print('> Successfully registered the user.')


def login():
    username = input("> Please enter your username: ")
    data = []
    with open(configFile) as file:
        data = json.load(file)
    for user in data:
        if (user['username'] == username):
            password = input("> Please enter your password: ")
            if (user["password"] == hash(password)):
                print('> Successfully logged in.')
                return { 
                    "username": user['username'],
                    "userType": user['userType'],
                    "privilegeLevel": user['privilegeLevel']
                }
            print('> Wrong password.\n> login failed.')
            return False
    print('> Username dosen\'t exists.\n> login failed.')
    return False


def addNewRecord(userType):
    isUserExists = False
    while (not isUserExists):
        patientUsername = input("> Enter username of the patient: ")
        isUserExists = isExists(patientUsername, 'username', configFile)
        if (not isUserExists):
            print('> Username dosen\'t exists. Try again')
    sensLvl = ''
    while (not sensLvl in ['1', '2', '3']):
        sensLvl = input('> Select the sensitivity level of data'
                            +'\n\t1 - low'
                            +'\n\t2 - medium'
                            +'\n\t3 - high\n> : ')
        if (not sensLvl in ['1', '2', '3']):
            print('> Invalid selection. Try again')
    sensLvl = sensLvlMap[sensLvl]

    dataType = ''
    while (not dataType in ['1', '2', '3', '4']):
        dataType = input('> Select the report type'
                            +'\n\t1 - personal details'
                            +'\n\t2 - sickness details'
                            +'\n\t3 - drug prescriptions'
                            +'\n\t4 - lab test prescriptions\n> : ')
        if (not dataType in ['1', '2', '3', '4']):
            print('> Invalid selection. Try again')

    if dataType == '1':
        playload = {"name": '', "age": '', "address": '', "mobile": ''}
    elif dataType == '2':
        playload = {"sikness": '', "symptoms": '', "date": ''}
    elif dataType == '3':
        playload = {"drugs": [], "date": ''}
    elif dataType == '4':
        playload = {"test name": '', "result": '', "date": ''}
    dataType = dataTypeMap[dataType]

    for req in playload:
        if (req == 'drugs' or req == 'symptoms'):
            playload[req] = list(input('> Enter ' + req +
                                       ' (seperate each by a single\',\'): ').split(','))
        else:
            playload[req] = input('> Enter ' + req + ': ')

    dataRecord = {
        'patientUsername': patientUsername,
        'sensitivityLevel': sensLvl,
        'dataType': dataType,
        'data': playload
    }
    addData(dataRecord, dataFile)
    print('> New record added successfully.')


def viewRecord(username, privilegeLevel):
    allData, data = [], []
    with open(dataFile) as fileData:
        allData = json.load(fileData)
    # get requested users list
    for row in allData:
        if (row['patientUsername'] == username or username == ''):
            if (isAllowedBySensLvl(row['sensitivityLevel'], privilegeLevel)):
                data.append(row)
    
    if (len(data) == 0):
        print(' -------------------------------------------------------')
        print('\tNo records to disolay!')
        print(' -------------------------------------------------------')
        return
    
    # display record
    for row in data:
        print(' -------------------------------------------------------')
        print(' \tPatient username: ' + row['patientUsername']
            + '\n\tSensitivity level: ' + row['sensitivityLevel']
            + '\n\tData type: ' + row['dataType']
            + '\n\tDetails: ')
        for data in row['data']:
            print('\t\t' + data + ' - ' + str(row['data'][data]))
    print(' -------------------------------------------------------')

print("> Welcome to the medical data center.")
is_valid_action = False
while (not is_valid_action):
    action = input("> 'login' or 'register'? ")
    is_valid_action = action in ['login', 'register']
    if (not is_valid_action):
        print('> Invalid action. Try again.')

if action == 'register':
    register()
    exitApp()

else:
    user = login()
    if (not user):
        exitApp()
    print('> Hello ' + user['username'] + '!')
    # create action list for user allowed by their privilege level
    allowedActions = ''
    i = 1
    for action in allowed[user['privilegeLevel']]:
        allowedActions += '\n\t' + str(i) + ' - ' + action
        i += 1
    allowedActions += '\n\t9 - logout'
    while(True):
        actionType = input('> Select action type: ' + allowedActions + '\n> :')

        # view my/all records
        if actionType == '1':
            if (user['privilegeLevel'] == 'patient'):
                viewRecord(user['username'], user['privilegeLevel'])
            else: viewRecord('', user['privilegeLevel'])

        # filter and view records by username
        elif actionType == '2':
            isUserExists = False
            while (not isUserExists):
                patientUsername = input("> Enter username of the patient: ")
                isUserExists = isExists(patientUsername, 'username', configFile)
                if (not isUserExists):
                    print('> Username dosen\'t exists. Try again')
            viewRecord(patientUsername, user['privilegeLevel'])

        # add new record
        elif actionType == '3':
            addNewRecord(user['userType'])
        
        # logout
        elif actionType == '9':
            exitApp()
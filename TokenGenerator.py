from configparser import ConfigParser
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge

###################################
### Get inputs from config file ###
###################################
config = ConfigParser()
config.read('config.ini')

#################
### DB config ###
#################
userId = config.get('Smaco', 'userId')
password = config.get('Smaco', 'password')
yob = config.get('Smaco', 'yob')

samco = StocknoteAPIPythonBridge()

# login = samco.login(body={"userId": 'DA43319', 'password': 'max#8021972', 'yob': '1988'})
login = samco.login(body={"userId": userId, 'password': password, 'yob': yob})
print("Login details", login)  # this will return a user details and generated session token


import requests
import sys
import json
import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml

requests.packages.urllib3.disable_warnings()

from requests.packages.urllib3.exceptions import InsecureRequestWarning

def get_logger(logfile, level):
    '''
    Create a logger
    '''
    if logfile is not None:

        '''
        Create the log directory if it doesn't exist
        '''

        fldr = os.path.dirname(logfile)
        if not os.path.exists(fldr):
            os.makedirs(fldr)

        logger = logging.getLogger()
        logger.setLevel(level)
 
        log_format = '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(lineno)-3d | %(message)s'
        formatter = logging.Formatter(log_format)
 
        file_handler = TimedRotatingFileHandler(logfile, when='midnight', backupCount=7)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        return logger

    return None


class Authentication:

    @staticmethod
    def get_jsessionid(vmanage_host, vmanage_port, username, password):
        api = "/j_security_check"
        base_url = "https://%s:%s"%(vmanage_host, vmanage_port)
        url = base_url + api
        payload = {'j_username' : username, 'j_password' : password}
        
        response = requests.post(url=url, data=payload, verify=False)
        try:
            cookies = response.headers["Set-Cookie"]
            jsessionid = cookies.split(";")
            return(jsessionid[0])
        except:
            if logger is not None:
                logger.error("No valid JSESSION ID returned\n")
            exit()
       
    @staticmethod
    def get_token(vmanage_host, vmanage_port, jsessionid):
        headers = {'Cookie': jsessionid}
        base_url = "https://%s:%s"%(vmanage_host, vmanage_port)
        api = "/dataservice/client/token"
        url = base_url + api      
        response = requests.get(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            return(response.text)
        else:
            return None

class update_location:

    def __init__(self, vmanage_host, vmanage_port, jsessionid, token):
        base_url = "https://%s:%s/dataservice/"%(vmanage_host, vmanage_port)
        self.base_url = base_url
        self.jsessionid = jsessionid
        self.token = token
    
    def get_device_templateid(self,device_template_name):
        if self.token is not None:
            headers = {'Cookie': self.jsessionid, 'X-XSRF-TOKEN': self.token}
        else:
            headers = {'Cookie': self.jsessionid}
        api = "template/device"
        url = self.base_url + api        
        template_id_response = requests.get(url=url, headers=headers, verify=False)
        device_info = dict()

        if template_id_response.status_code == 200:
            items = template_id_response.json()['data']
            template_found=0
            if logger is not None:
                logger.info("\nFetching Template uuid of %s"%device_template_name)
            print("\nFetching Template uuid of %s"%device_template_name)
            for item in items:
                if item['templateName'] == device_template_name:
                    device_info["device_template_id"] = item['templateId']
                    device_info["device_type"] = item["deviceType"]
                    template_found=1
                    return(device_info)
            if template_found==0:
                if logger is not None:
                    logger.error("\nDevice Template is not found")
                print("\nDevice Template is not found")
                exit()
        else:
            if logger is not None:
                logger.error("\nDevice Template is not found " + str(template_id_response.text))
            print("\nError fetching list of templates")
            exit()

    def get_attached_devices(self,device_template_id):
        if self.token is not None:
            headers = {'Content-Type': "application/json",'Cookie': self.jsessionid, 'X-XSRF-TOKEN': self.token}
        else:
            headers = {'Content-Type': "application/json",'Cookie': self.jsessionid}

        api = "template/device/config/attached/%s"%device_template_id
        url = self.base_url + api

        device_ids = requests.get(url=url,headers=headers,verify=False)

        if device_ids.status_code == 200:
            items = device_ids.json()['data']
            device_uuid = list()
            for i in range(len(items)):
                device_uuid.append(items[i]['uuid'])
            return device_uuid
        else:
            print("\nError retrieving attached devices")
            if logger is None:
                print("\nError retrieving attached devices " + str(device_template_edit_res.text))
            exit()

    def push_device_template(self,device_info,device_uuids,loc_parameters):
        
        if self.token is not None:
            headers = {'Content-Type': "application/json",'Cookie': self.jsessionid, 'X-XSRF-TOKEN': self.token}
        else:
            headers = {'Content-Type': "application/json",'Cookie': self.jsessionid}
        
        device_template_id = device_info["device_template_id"]

        # Fetching Device csv values
        if logger is not None:
            logger.info("\nFetching device csv values")
        print("\nFetching device csv values")

        payload = { 
                    "templateId":device_template_id,
                    "deviceIds":device_uuids,
                    "isEdited":False,
                    "isMasterEdited":False
                  }
        payload = json.dumps(payload)
        
        api = "template/device/config/input/"
        url = self.base_url + api
        device_csv_res = requests.post(url=url, data=payload,headers=headers, verify=False)

        if device_csv_res.status_code == 200:
            device_csv_values = device_csv_res.json()['data']
        else:
            if logger is not None:
                logger.error("\nError getting device csv values" + str(device_csv_res.text))
            print("\nError getting device csv values")
            exit()

        # Adding the values to device specific variables

        temp = device_csv_values

        for item1 in temp:
            sys_ip = item1["csv-deviceIP"]
            for item2 in loc_parameters:
                if sys_ip == item2["device_sys_ip"]:
                    item1["//system/location"] = item2["loc_name"]
                    item1["//system/gps-location/latitude"] = item2["latitude"]
                    item1["//system/gps-location/longitude"] = item2["longitude"]                 
                    break
                else:
                    continue

        if logger is not None:
            logger.info("\nUpdated device csv values are" + str(temp))
        device_csv_values = temp

        # Updating Device CSV values

        print("\nUpdating Device CSV values")
        if logger is not None:
            logger.info("\nUpdating Device CSV values")

        payload = { 
                    "deviceTemplateList":[
                    {
                        "templateId":device_template_id,
                        "device":device_csv_values,
                        "isEdited":False,
                        "isMasterEdited":False
                    }]
                  }
        payload = json.dumps(payload)

        api = "template/device/config/attachfeature"
        url = self.base_url + api
        attach_template_res = requests.post(url=url, data=payload,headers=headers, verify=False)


        if attach_template_res.status_code == 200:
            attach_template_pushid = attach_template_res.json()['id']
        else:
            if logger is not None:
                logger.error("\nUpdating Device CSV values failed, "+str(attach_template_res.text))
            print("\nUpdating Device CSV values failed")
            exit()

        # Fetch the status of template push

        api = "device/action/status/%s"%attach_template_pushid
        url = self.base_url + api        

        while(1):
            template_status_res = requests.get(url,headers=headers,verify=False)
            if template_status_res.status_code == 200:
                if template_status_res.json()['summary']['status'] == "done":
                    print("\nUpdated Location parameters")
                    if logger is not None:
                        logger.info("\nUpdated Location parameters")
                    return
            else:
                if logger is not None:
                    logger.error("\nUpdating Location parameters failed " + str(template_status_res.text))                
                print("\nUpdating Location parameters failed")
                exit()

if __name__ == "__main__":
    try:
        log_level = logging.DEBUG
        logger = get_logger("log/location_logs.txt", log_level)
        if logger is not None:
            logger.info("Loading configuration details from YAML\n")
            print("Loading configuration details from YAML\n")
        with open("config_details.yaml") as f:
            config = yaml.safe_load(f.read())
        
        vmanage_host = config["vmanage_host"]
        vmanage_port = config["vmanage_port"]
        vmanage_username = config["vmanage_username"]
        vmanage_password = config["vmanage_password"]
        device_template_name = config["device_template_name"]

        
        Auth = Authentication()
        jsessionid = Auth.get_jsessionid(vmanage_host,vmanage_port,vmanage_username,vmanage_password)
        token = Auth.get_token(vmanage_host,vmanage_port,jsessionid)
        location_settings = update_location(vmanage_host,vmanage_port,jsessionid, token)
        loc_parameters = list()

        # Loop over edge routers to update location parameters
        for device in config["devices"]:
            print("Device: {}".format(device["system_ip"]))

            loc_name = device["location_name"]
            latitude = device["latitude"]
            longitude = device["longitude"]

            temp_parameters =  { 
                                 "device_sys_ip": device["system_ip"],
                                 "loc_name": device["location_name"],
                                 "latitude": device['latitude'],
                                 "longitude": device['longitude']
                               }

            loc_parameters.append(temp_parameters)

            if logger is not None:
                logger.info("\location parameters are " + str(loc_parameters))

        device_info = location_settings.get_device_templateid(device_template_name)
            
        device_uuids = location_settings.get_attached_devices(device_info["device_template_id"])
            
        location_settings.push_device_template(device_info,device_uuids,loc_parameters)

    except Exception as e:
        print(e)



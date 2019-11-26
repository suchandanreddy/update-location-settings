# Update Location Settings

# Objective 

*   How to use vManage REST APIs to update location name and GPS settings of vEdge or cEdge router. 


# Requirements

To use this code you will need:

* Python 3.7+
* vManage user login details. (User should have privilege level to edit device template)
* vEdge or cEdge routers with device template attached.

# Install and Setup

- Clone the code to local machine.

```
git clone https://github.com/suchandanreddy/update-location-settings.git
cd update-location-settings
```
- Setup Python Virtual Environment (requires Python 3.7+)

```
python3.7 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

- Create config_details.yaml using below sample format to update the environment variables for vManage login details and Location parameters

## Example:

```
# vManage Connectivity Info
vmanage_host: 
vmanage_port: 
vmanage_username: 
vmanage_password: 


# Device template Info

device_template_name: 

# Network Routers
devices:
  - system_ip: 
    location_name: 
    latitude:
    longitude: 
  - system_ip: 
    location_name: 
    latitude: 
    longitude: 
```


After setting the env variables, run the python script `update-location-settings.py`

`update-location-settings.py` script does the below steps in sequence. 

## Workflow

- Fetch the device template-id associated with the device template name. 
- Retrieve device uuids of the attached devices to the device template. 
- Update the location parameters using the values from config_details.yaml file

## Restrictions

- vEdge or cEdge should be in vManage mode with device template attached which contains System feature template with device specific variables for location name, latitude and longitude

## Sample output

```
$python3 update-location-settings.py 

Loading configuration details from YAML

Device: 1.1.1.5

Fetching Template uuid of BR1-CSR-1000v-AMP

Fetching device csv values

Updating Device CSV values

Updated Location parameters
```
import requests
import json
import time
import urllib3
import logging
log = logging.getLogger('azure test drive custom script')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_resource_group():
    res = None
    headers = {'Metadata': True}
    uri = 'group ip address'
    res = requests.get(uri, headers=headers)
    return res.content

def get_controller_ip():
    headers = {'Metadata': True}
    uri = "network ip address"
    res = requests.get(uri, headers=headers)
    if res.status_code != 200:
        raise res.status_code, Exception(str(res.text))
    else:
        return res.content

def get_default_password():
    default_password = ''
    default_password_file = '/opt/avi/bootstrap/default_password'
    try:
        for line in open(default_password_file, "r"):
            default_password = str(line[0:-1])
        return default_password
    except Exception as e:
        log.info(str(e))
        return None

def get_headers(controller_ip):
    headers = ''
    count = 10
    for retry in range(count):
        try:
            uri = 'http://%s/api/initial-data' % controller_ip
            res = requests.get(uri, verify=False)
            if res.status_code != 200:
                raise RuntimeError("Initial data API status not 200")
            res = json.loads(res.content)
            avi_version = res['version']['Version']
            headers = {'Content-Type': 'application/json', 'X-Avi-Version': avi_version, 'X-Avi-Tenant': 'admin'}
            return headers
        except Exception as e:
            if retry == (count - 1):
                raise RuntimeError(str(e))
            else:
                log.info('Retrying number %s' % retry)
                time.sleep(30)
    return headers


def print_user_data():
    try:
        for line in open('/var/lib/cloud/instance/user-data.txt','r'):
            log.info(line)
    except Exception as e:
        log.info(str(e))
        pass

def get_cloud_data(controller_ip, headers, default_password):
    res = ''
    data = {'name': 'Default-Cloud'}
    uri = 'https://%s/api/cloud?name=Default-Cloud' % controller_ip
    try:
        res = requests.get(uri, auth=('admin', default_password), headers=headers, verify=False)
        if res.status_code != 200:
            raise Exception(str(res.text))
        _data = res.json()
        _data = _data['results'][0]
        return 200, _data
    except Exception as e:
        return res.status_code, e


try:
    lvl = logging.INFO
    log.setLevel(lvl)
    ch = logging.StreamHandler()
    ch.setLevel(lvl)
    formatter = logging.Formatter(
        '%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    print_user_data()
    resource_group = get_resource_group()
    controller_ip = get_controller_ip()
    default_password = get_default_password()
    if not default_password:
        exit(0)
    time.sleep(60)
    headers = get_headers(controller_ip)
    status_code, _data = get_cloud_data(controller_ip, headers, default_password)
    if status_code != 200:
        log.info(_data)
        exit()

    _uuid = _data['uuid']
    _data['azure_configuration']['resource_group'] = resource_group
    uri = 'https://%s/api/cloud/%s'%(controller_ip, _uuid)
    vnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s"%("6ac6cebc-1d7d-4b3c-8a6f-74093246ae02", resource_group, "servers-vnet")
    _data['azure_configuration']['network_info'][0]["virtual_network_id"] = vnet_id
    log.info('Put api to uri %s'%(uri))
    res = requests.put(uri, auth=('admin', default_password), headers=headers, data=json.dumps(_data), verify=False)
except Exception as e:
    log.info(str(e))



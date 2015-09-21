##Krunch Uploader Ver. #1.0
##darin.hensley@rackspace.com

import logging 
import os 
import sys
sys.path.insert(0, './modules')
import json
import time
import signal
import threading
from os.path import expanduser
from modules.auth import Authenticate
from modules.getinfo import get_containers, get_files, get_link
from modules.container_util import create_containers
from modules.upload_actions import do_the_uploads, retry, signal_handler
from modules.logger import debug, error, info

def main():
    title = """\
         _   __                      _             
        | | / /                     | |            
        | |/ / _ __ _   _ _ __   ___| |__          
        |    \| '__| | | | '_ \ / __| '_ \         
        | |\  \ |  | |_| | | | | (__| | | |        
        \_| \_/_|   \__,_|_| |_|\___|_|_|_|        
        | | | |     | |               | |          
        | | | |_ __ | | ___   __ _  __| | ___ _ __ 
        | | | | '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|
        | |_| | |_) | | (_) | (_| | (_| |  __/ |   
         \___/| .__/|_|\___/ \__,_|\__,_|\___|_|   
              | |                                  
              |_|  
               Version 1.5 TronTeam
"""
    sys.stdout.write("\x1b[2J\x1b[H")
    print title
 
    username = raw_input("Please enter your username: ")
    apikey = raw_input("Please enter your apikey: ")

    authenticate = Authenticate(username, apikey)
    cloud_url = get_link(authenticate.jsonresp)
    #per 1 million files the list will take
    #approx 300MB of memory.

    file_container_list, file_list = get_files(authenticate, cloud_url)
    cloud_container_list = get_containers(authenticate, cloud_url)
    create_containers(cloud_container_list,
            file_container_list, authenticate, cloud_url)

    return file_list, authenticate


class FileQuantity(object):
    """Keeps track of files that have been uploaded and how many are left"""
    def __init__(self, file_quantity):
        self.quantity = file_quantity
        self.total = file_quantity
        self.lock = threading.Lock()

    def deduct(self):
        with self.lock:
            self.quantity = self.quantity - 1

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    retry_list = []
    file_list, authenticate = main()
    file_quantity = FileQuantity(len(file_list))
    do_the_uploads(file_list, file_quantity, retry_list, authenticate)
    while True:
        cont = retry(file_list, file_quantity, 
                retry_list, error, authenticate)
        if not cont:
            break

    print "\nLogs and their locations are:"
    print error
    print info
    print debug




import logging
import sys
import os
import time
import requests

logger = logging.getLogger("krunch")

file_qauntity = None


def prepare_dir_scan(absolute_path, stratus=None):
    """This scans parent directories with absolute paths  and prepares them for os.walk. 
       Also, creates a list of containers(without absolut paths) for cloud files/dir
       container syncing."""
    print "\nHold...scanning parent directories...",
    container_list = [x for x in os.listdir(absolute_path)
                      if x.lower() != "signature.txt"
                      and x.lower() != "signature"]

    dir_list = [os.path.abspath(os.path.join(absolute_path, x))
                for x in os.listdir(absolute_path)]

    print "done!"
    return container_list, dir_list


def get_files(authenticate, cloud_url, container_list=None,
              dir_list=None, absolute_path=None):
    """Tranverses the mountpoint and get's the files. Each parent directory is a 
       container"""
    file_list = []
    file_container_list = []
    dir_name_list = []

    #test to see if this is Status version or not
    if not container_list and not dir_list and not absolute_path:
        while True:
	    absolute_path = raw_input("\nPlease enter mount point: ")
            if not os.path.isdir(absolute_path):
                msg = ("\'{}\' path not found!".format(absolute_path))
                logger.error(msg)
            else:
                break
        container_list, dir_list = prepare_dir_scan(absolute_path)

    print "\nScanning " + absolute_path + " for files...",

    for directory in dir_list:
        for root, dirs, files in os.walk(directory, topdown=False):
            for i in files:
                file_name = os.path.join(root, i)
                if os.path.getsize(file_name) >= 5300000000:
                    msg = (
                        "ERROR! File \'{}\' is past 5GB limit. File disregarded.".format(file_name))
                    print "\n"
                    logger.error(msg)
                    continue
                try:
                    file_name.decode('utf-8')
                except UnicodeError:
                    msg = (
                        "ERROR! Filename \'{}\' is not utf-8!. File disregarded.".format(file_name))
                    logger.error(msg)
                    continue
                real_filename = file_name.replace(directory + "/", "")
                dir_name = os.path.basename(directory)
                foo = (file_name, real_filename, dir_name, cloud_url)
                file_list.append(foo)

    print "done!"
    return container_list, file_list


def get_containers(authenticate, cloud_url):
    """Fetches container list from Cloud. Compares and uploads only the ones that
       are on mountpoint that are not in Cloud."""
    auth_header = {"X-Auth-Token": authenticate.token}
    container_list = []

    #set limit listing here! 10k Max
    limit = "2000"
    limit_cloud_url = cloud_url + "?limit=" + limit
    print '\nFetching Cloud Container List...',
    for i in range(5):
        prexisting_containers = False
        try:
            while True:
                r = requests.get(limit_cloud_url, headers=auth_header, timeout=1)
                if r.status_code == 200:
                    item = r.text
                    temp_list = list(item for item in item.split('\n') if item.strip())
                    container_quantity = len(temp_list)
                    container_list = container_list + temp_list
                    if container_quantity >= int(limit):
                        print "here..........."
                        limit_cloud_url = cloud_url + '?limit=' + limit + '&marker=' + temp_list[-1]
                        prexisting_containers = True
                        continue
                elif r.status_code == 401:
                    msg = (
                        "Could not get container list. Token has expired. Renewing Token...")
                    logger.error(msg)
                    authenticate.get_token()
                    auth_header = {"X-Auth-Token": authenticate.token}
                    time.sleep(2)
                    continue
                elif r.status_code == 204 and not prexisting_containers:
                    msg = "Account has no pre-existing containers..."
                    logger.info(msg)
                    break
                break
            break
        except requests.exceptions.RequestException:
            if i == 4:
                msg = (
                    "Error! Could not do API call! For retrieving container list!"
                    "\nThis was the 5th and final try. Re-run this script and"
		    "\nit will continue to add the containers where it last"
		    "\nstopped")
                logger.info(msg)
                sys.exit()
            msg = (
                "Error! Could not do API call for retrieving container list!"
                "\nTrying again...")
            logger.info(msg)
            time.sleep(1)

    print "done!"
    return container_list


def get_link(jsonresp, region=None):
    """Gets the endpoints for Cloud files depending on region"""
    foo = jsonresp["access"]["serviceCatalog"]
    for i in foo:
        for value in i.values():
            if value == "cloudFiles":
                bar = i

    if not region:
        sys.stdout.write("\x1b[2J\x1b[H")
        cloud_choice = raw_input("Use cloud internal network for uploading?(Y/y): ").upper()
        if cloud_choice == "Y":
            cloudURL = "internalURL"
        else:
            cloudURL = "publicURL"

        regions = [
            {str(bar["endpoints"][0]["region"]): str(bar["endpoints"][0][cloudURL])},
            {str(bar["endpoints"][1]["region"]): str(bar["endpoints"][1][cloudURL])},
            {str(bar["endpoints"][2]["region"]): str(bar["endpoints"][2][cloudURL])},
            {str(bar["endpoints"][3]["region"]): str(bar["endpoints"][3][cloudURL])},
            {str(bar["endpoints"][4]["region"]): str(bar["endpoints"][4][cloudURL])}]

        print "Please Pick A Datacenter:"
        for i, item in enumerate(regions):
            for value in item.values():
                j = str(i + 1)
                if cloudURL == "internalURL":
                    name = value[24:27].upper()
                else:
                    name = value[19:22].upper()
                print "%s) %s" % (j, name)

        value = raw_input("Please enter choice: ")
        value = int(value) - 1
        while True:
                        
            try:
                link = regions[value].values()[0] + "/"
                region = regions[value].keys()[0]
                msg = (
                    "\n{}\n^This link will be used. Double check it!"
                    "\nJSON order is not always the same".format(link))
                logger.info(msg)
                break
            except IndexError:
                print "Wrong value!"
    else:
        #For Stratus
        link = [x.get("internalURL") for x in bar["endpoints"] if x["region"] == region]
        link = str(link[0]) + "/"
        msg = (
            "\n{}\n^This link will be used. Double check it!".format(link))
        logger.info(msg)

    return link


if __name__ == '__main__':
    foo = get_containers()

    

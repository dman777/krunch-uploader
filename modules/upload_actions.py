import Queue
import hashlib
import requests
import time
import sys
import logging
import threading
from threading import Thread
from logger import debug, error, info

logger = logging.getLogger("krunch")

kill_received = False

class CustomQueue(Queue.Queue):
    #Can not use .join() because it would block any processing
    #for SIGINT untill threads are done. To counter this,
    # wait() is given a time out along with while not kill_received
    #to be checked

    def join(self):
        self.all_tasks_done.acquire()
        try:
            while not kill_received and self.unfinished_tasks:
                self.all_tasks_done.wait(10.0)
        finally:
            self.all_tasks_done.release()

def signal_handler(signal, frame):
    global kill_received
    kill_received = True
    msg = (
         "\n\n\nYou pressed Ctrl+C!"
         " Cleaning up threads!..This will take 2 minutes...\n")
    logger.info(msg) 
    threadz = threading.Event()
    for i in range(40):
        threadz.clear()
        time.sleep(3)
        threads_remaining = len(threading.enumerate())
        print "\n{} threads remaining to clean up...".format(threads_remaining)
        if threads_remaining == 1:
            msg = (
                "\nYour logs and their locations are:"
                "\n{}\n{}\n{}\n\n".format(debug, error, info))
            logger.info(msg)
            sys.exit()
    msg = (
        "{} threads refused to die. Exiting...".format(threads_remaining))
    logger.error(msg)
    sys.exit()

def do_the_uploads(file_list, file_quantity,
        retry_list, authenticate):
    """The uploading engine"""
    value = raw_input(
        "\nPlease enter how many concurent "
        "uploads you want at one time(example: 200)> ")
    value = int(value)
    logger.info('{} concurent uploads will be used.'.format(value))

    confirm = raw_input(
        "\nProceed to upload files? Enter [Y/y] for yes: ").upper()
    if confirm == "Y":
        kill_received = False
        sys.stdout.write("\x1b[2J\x1b[H")
        q = CustomQueue()

        def worker():
            global kill_received
            while not kill_received:
                item = q.get()
                upload_file(item, file_quantity, retry_list, authenticate, q)
                q.task_done()

        for i in range(value):
            t = Thread(target=worker)
            t.setDaemon(True)
            t.start()

        for item in file_list:
            q.put(item)
        
        q.join()
        
        print "Finished. Cleaning up processes...",
        #Allowing the threads to cleanup
        time.sleep(4)
        print "done."


def retry(file_list, file_quantity, retry_list,
        error, authenticate):
    copy_retry_list = []
    copy_retry_list = list(retry_list)
    #must delete elements of orignial retry_list
    #if retry_list=[] was used, there would be 2 instances
    #of the list and the script would
    #use the memory location of the old list. 
    del retry_list[:]

    while True:
        copy_retry_list_count = len(copy_retry_list)
        if copy_retry_list_count:
            print (
                "\nFile upload is complete. However, there"
                "\nare {} files that failed and can be retried."
                "\nThese can be verified in {}".format(copy_retry_list_count, error))

            confirm = raw_input(
                "Would you like to retry?"
                "\nEnter [N/n] to exit or [Y/y] for retry: ").upper()

            if confirm == "Y":
                msg = ("\nRetrying failed upload files..")
                logger.info(msg)
                do_the_uploads(copy_retry_list, file_quantity, retry_list, authenticate)
                return True
            else:
                return False
        else:
            msg = ("\nCongratulations! No failed uploads were found!!!")
            logger.info(msg)
            return False


def md5sum(absolute_path_filename):
    """Calculates the checksum before uploading. When given to cloud files, Cloud will calculate
       the checksum and do a compare also. Krunch uploader will do a extra compare afterwards
       as a double check since it takes very little overhead to do this."""
    blocksize = 4000
    f = open(absolute_path_filename, 'rb')
    buf = f.read(blocksize)
    md5sum = hashlib.md5()
    while len(buf) > 0:
        md5sum.update(buf)
        buf = f.read(blocksize)
    return md5sum.hexdigest()


def upload_file(file_obj, file_quantity, retry_list, authenticate, q):
    """Uploads a file. One file per it's own thread. No batch style. This way if one upload
       fails no others are effected."""
    absolute_path_filename, filename, dir_name, url = file_obj
    url = url + dir_name + '/' + filename

    print '\nCalculating checksum for "{}"...'.format(filename)
    src_md5 = md5sum(absolute_path_filename)

    if src_md5:
        pass
    else:
        msg = (
            'Filename \"{}\" is missing md5 checksum!'
            ' This will not stop upload, but md5 check will not be checked!'.format(filename))
        logger.error(msg)

    token = authenticate.get_token()

    header_collection = {
        "X-Auth-Token": token,
        "ETag": src_md5}
    
    MAX_NUMBER_ATTEMPTS = 5
    print "\nUploading " + absolute_path_filename
    for attempt_number in range(MAX_NUMBER_ATTEMPTS):
        max_number_attempts_reached = MAX_NUMBER_ATTEMPTS - 1
        try:
            with open(absolute_path_filename, "r") as f:
                r = requests.put(url, data=f, headers=header_collection, timeout=45)
        except requests.exceptions.ConnectionError:
            if attempt_number == max_number_attempts_reached:
               msg = (
                   'Error! Connection error for file "{}". This was attempt #{}'
                   ' and final. File will go on the retry list'.format(filename, attempt_number + 1))
               retry_list.append(file_obj)
            else: 
                msg = (
                    'Error! Connection error for file "{}". This is attempt #{}.'
                    ' Trying again...'.format(filename, attempt_number + 1))
            logger.error(msg)
            continue 

        except requests.exceptions.TooManyRedirects:
            if attempt_number == max_number_attempts_reached:
               msg = (
                   'Error! Too many redirects for file "{}".' 
                   ' This was attempt #{} and final.'
                   ' File will go on the retry list'.format(filename, attempt_number + 1))
               retry_list.append(file_obj)
            else: 
                msg = (
                    'Error! Too many redirects for file "{}".'
                    ' File will go on the retry list'.format(filename, attempt_number + 1))
            logger.error(msg)
            continue

        except requests.exceptions.HTTPError:
            #r.status_code = e.response.status_code
            if attempt_number == max_number_attempts_reached:
                msg = (
                    'Error! HTTP error code {} for file "{}".'
                    ' This was attempt #{} and final.'
                    ' File will go on the retry list.'.format(r.status_code,
                                                              filename, attempt_number + 1))
                retry_list.append(file_obj)
            else: 
                msg = (
                    'Error! Error! HTTP error code {} for file "{}".'
                     ' This is attempt #{}. Trying again...'.format(r.status_code,
                                                                     filename, attempt_number + 1))
            sys.exit()
            logger.error(msg)
            continue

        except requests.exceptions.RequestException:
            if attempt_number == max_number_attempts_reached:
                msg = ('Error! Could not do API call to \"{}\"'
                       ' This was the 5th and final try.'
                       ' File will be placed on the retry list.'.format(filename))
                logger.error(msg)
                retry_list.append(file_obj)
            else:
                msg = ('Error! Could not do API call to upload \"{}\". '
                       'This was the #{} attempt. Trying again...'.format(filename, attempt_number + 1))
            logger.error(msg)
            continue

        if r.status_code == 401:
            msg = ('Token has expired for upload \"{}\"'
                  ' Renewing token...'.format(filename))
            logger.error(msg)
            authenticate.get_token()
            auth_header = {"X-Auth-Token": authenticate.token}
            if attempt_number == max_number_attempts_reached:
                retry_list.append(file_obj)
            continue
        elif 'etag' in r.headers: 
            if src_md5 == r.headers['etag']:
                file_quantity.deduct()
                msg = (
                    'File \"{}\" successfully'
                    ' loaded with verified md5 \"{}\"'.format(filename, src_md5))
                logger.info(msg)
                msg = (
                    '{} out of {} files left'.format(file_quantity.quantity, file_quantity.total))
                logger.info(msg)
                break
        else:
            msg = (
                'File \"{}\" checksum verification failed with'
                ' \"{}\". This will be placed on the retry list'.format(filename, src_md5))
            logger.error(msg)
            retry_list.append(file_obj)
            break


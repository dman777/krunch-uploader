import logging
from os.path import expanduser
import os
from modules.filter import MyFilter

home = expanduser("~") + '/'

directory = home + "krunchuploader_logs"

if not os.path.exists(directory):
    os.makedirs(directory)

debug = directory + "/krunchuploader__debug_" + str(os.getpid()) + ".txt"
error = directory + "/krunchuploader__error_" + str(os.getpid()) + ".txt"
info = directory + "/krunchuploader__info_" + str(os.getpid()) + ".txt"

os.open(debug, os.O_CREAT | os.O_EXCL)
os.open(error, os.O_CREAT | os.O_EXCL)
os.open(info, os.O_CREAT | os.O_EXCL)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=debug,
                    filemode='w')

logger = logging.getLogger("krunch")

fh_error = logging.FileHandler(error)
fh_error.setLevel(logging.ERROR)
fh_error.setFormatter(formatter)
fh_error.addFilter(MyFilter(logging.ERROR))

fh_info = logging.FileHandler(info)
fh_info.setLevel(logging.INFO)
fh_info.setFormatter(formatter)
fh_info.addFilter(MyFilter(logging.INFO))

std_out_error = logging.StreamHandler()
std_out_error.setLevel(logging.ERROR)
std_out_error.addFilter(MyFilter(logging.ERROR))
std_out_info = logging.StreamHandler()
std_out_info.addFilter(MyFilter(logging.INFO))
std_out_info.setLevel(logging.INFO)

logger.addHandler(fh_error)
logger.addHandler(fh_info)
logger.addHandler(std_out_error)
logger.addHandler(std_out_info)


Krunch-Uploader
===============
Python 2.7.*

Modules required: requests, pyzt, python-dateutil

Version 1.5 - Cloud Files Bulk Uploader with luxury and concurrency. Enter name, api key, mount point and it will do the rest.

#Directions:
Have a single mount point with all the containers and files you would like to upload. 
For each directory under that mount point, a container will be created in your cloud account.
If the container already exists in your cloud account, no problem. Container will not be over written.
Krunch Uploader will upload all your files per each directory/container to the relative container in the cloud account.

For example:
<br>
If I have a hard drive full of files I will mount that drive to /mnt/temp. This will be the mount point given to Krunch Uploader. Past this point, every child directory(not grandchildren) of /mnt/temp will be a container that will be created and uploaded to your cloud files account. With in each container/directory will be the files that also get uploaded.
Here is a diagram:<br>
<p>&nbsp; &nbsp;</p>
<body><p>&nbsp; &nbsp;</p>

         /mnt/temp/
                  |
                   ----ContainerA
                  |       |file1
                  |       |file2
                  |
                  ----ContainerB
                          |file1
                          |file2
</body>
#Features:
 * Any failed uploads will be placed on a retry list. After first bulk upload, user will be 
   presented with the retry list and given the option to retry.
 * Verbose logging- Info, Error, and Debug logs are given. 
 * Choose your own number of uploads(threads)
 * Menu driven for ease.
 * Md5 sum check sum verification for each upload to ensure data integrity. 
 * Custom value for concurrent uploads
 * Each upload will try 5 times before giving up
 * automatic token renewal
 * utf-8 check in filenames
 * 5GB file limit size check
 * Light weight- python multi-threading is used instead of multiprocessing. This allows for full optimization of this I/O bound utlity. In addition, a smaller memory foot print. 

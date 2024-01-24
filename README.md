
# D118-PS-Misc-Fields

Short and sweet script to generate a comma delimited .txt file for AutoComm into PowerSchool to populate some custom fields like email and lunch ID.

## Overview

The script first does a query for all students in PowerSchool, getting their basic information as well as the current values of their lunch ID and custom email. For each student, their custom email and lunch ID is compared to what it should be based on their student number, and if it does not match, their entry is output to the comma delimited .txt file. Then the .txt file is uploaded to our local SFTP server for import by AutoComm into PowerSchool.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- D118_SFTP_USERNAME
- D118_SFTP_PASSWORD
- D118_SFTP_ADDRESS

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool and the local SFTP server. If you wish to directly edit the script and include these credentials, you can.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

You will also need a SFTP server running and accessible that is able to have files written to it in the directory /sftp/miscFields/ or you will need to customize the script (see below). That setup is a bit out of the scope of this readme.
In order to import the information into PowerSchool, a scheduled AutoComm job should be setup, that uses the managed connection to your SFTP server, and imports into student_number, and whichever Activity fields you need based on the data, using comma as a field delimiter, LF as the record delimiter with the UTF-8 character set. It is important to note that the order of the AutoComm fields must match the order of the output which is defined by the line `print(f'{stuID},{newLunch},{newEmail}', file=output)` which uses their student number, lunch ID, then custom email as the default order.

## Customization

This script is somewhat customized to our school district as it is designed to use custom fields in PowerSchool, but modifying it for other ones should not be impossible. Some things you will likely want to change are listed below:

- `EMAIL_SUFFIX` is obvious, it is the way the emails are constructed. In our district it is the student number and then the suffix, if you use something like firstlast you will also need to change `newEmail = stuID + EMAIL_SUFFIX` to use the relevant fields instead of the student ID.
- `OUTPUT_FILE_NAME` and `OUTPUT_FILE_DIRECTORY`define the file name and directory on the SFTP server that the file will be exported to. These combined will make up the path for the AutoComm import.
- As mentioned above, if you have a different way of constructing student emails it will need to be changed in the relevant line.
- If you want to reference other custom fields, simply edit the `cur.execute(*SQL QUERY HERE*) line to match the field names.

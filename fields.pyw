# importing module
import oracledb # needed for connection to PowerSchool (oracle database)
import sys # needed for non scrolling text output
import datetime # needed to get current date to check what term we are in
import os # needed to get environment variables
import pysftp # needed for sftp file upload

un = 'PSNavigator' #PSNavigator is read only, PS is read/write
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') #the password for the PSNavigator account
cs = os.environ.get('POWERSCHOOL_PROD_DB') #the IP address, port, and database name to connect to

#set up sftp login info
sftpUN = os.environ.get('D118_SFTP_USERNAME')
sftpPW = os.environ.get('D118_SFTP_PASSWORD')
sftpHOST = os.environ.get('D118_SFTP_ADDRESS')
cnopts = pysftp.CnOpts(knownhosts='known_hosts') # connection options to use the known_hosts file for key validation

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
print("SFTP Username: " + str(sftpUN) + " |SFTP Password: " + str(sftpPW) + " |SFTP Server: " + str(sftpHOST)) #debug so we can see what credentials are being used

with oracledb.connect(user=un, password=pw, dsn=cs) as con: # create the connecton to the database
    with con.cursor() as cur:  # start an entry cursor
        with open('updateLog.txt', 'w') as log: # open a log file
            with open('miscFields.txt', 'w') as output:  # open the output file
                print("Connection established: " + con.version)

                cur.execute('SELECT students.student_number, students.id, students.schoolid, students.enroll_status, students.lunch_id, students.grade_level, students.dcid, U_StudentsUserFields.custom_student_email FROM students LEFT JOIN u_studentsuserfields ON students.dcid = u_studentsuserfields.studentsdcid ORDER BY student_number DESC')
                rows = cur.fetchall() #fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
                for student in rows:
                    print(student)
                    stuID = str(int(student[0]))
                    currentLunch = str(int(student[4]))
                    currentEmail = str(student[7])
                    newLunch = stuID
                    newEmail = stuID + '@d118.org'
                    if (currentEmail != newEmail) or (currentLunch != newLunch):
                        if currentEmail != newEmail: # just used for logging
                            print(f'ACTION: Custom email field for {newEmail} is not correct, updating')
                            print(f'ACTION: Custom email field for {newEmail} is not correct, updating', file=log)
                        if currentLunch != newLunch: # just for logging
                            print(f'ACTION: Lunch ID field for {newEmail} is not correct, updating')
                            print(f'ACTION: Lunch ID field for {newEmail} is not correct, updating', file=log)
                        print(f'{stuID},{newLunch},{newEmail}', file=output) # if either their custom email or lunch id is incorrect we write both values to the file for the input
            
            #after all the output file is done writing and now closed, open an sftp connection to the server and place the file on there
            with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
                print('SFTP connection established')
                print('SFTP connection established', file=log)
                # print(sftp.pwd)  # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.chdir('/sftp/miscFields/')
                # print(sftp.pwd) # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.put('miscFields.txt') #upload the file onto the sftp server
                print("Fields file placed on remote server")
                print("Fields file placed on remote server", file=log)
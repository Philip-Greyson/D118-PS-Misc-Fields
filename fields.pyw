"""Script to generate a file to populate some custom fields in PowerSchool.

https://github.com/Philip-Greyson/D118-PS-Misc-Fields

Just takes their student ID number in order to make sure the custom email field is correct, and their lunch ID matches the student ID number.
If either are incorrect currently, exports the new correct one to a .txt file, then takes that file and uploads it to our local SFTP server in order to be imported into PowerSchool.

needs oracledb: pip install oracledb --upgrade
needs pysftp: pip install pysftp --upgrade
"""

# importing module
import datetime as dt  # needed to get current date to check what term we are in
import os  # needed to get environment variables
from datetime import *

import oracledb  # needed for connection to PowerSchool (oracle database)
import pysftp  # needed for sftp file upload

un = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
cs = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

#set up sftp login info
D118_SFTP_UN = os.environ.get('D118_SFTP_USERNAME')  # username for the d118 sftp server
D118_SFTP_PW = os.environ.get('D118_SFTP_PASSWORD')  # password for the d118 sftp server
D118_SFTP_HOST = os.environ.get('D118_SFTP_ADDRESS')  # ip address/URL for the d118 sftp server

CNOPTS = pysftp.CnOpts(knownhosts='known_hosts')  # connection options to use the known_hosts file for key validation

OUTPUT_FILE_NAME = 'miscFields.txt'
OUTPUT_FILE_DIRECTORY = '/sftp/miscFields/'
EMAIL_SUFFIX = '@d118.org'
COURSES_SCHOOL_ID = 5

print(f"Database Username: {un} |Password: {pw} |Server: {cs}")  # debug so we can see where oracle is trying to connect to/with
print(f'D118 SFTP Username: {D118_SFTP_UN} | D118 SFTP Password: {D118_SFTP_PW} | D118 SFTP Server: {D118_SFTP_HOST}')  # debug so we can see what info sftp connection is using

if __name__ == '__main__':  # main file execution
    with open('updateLog.txt', 'w', encoding='utf-8') as log:  # open logging file
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with oracledb.connect(user=un, password=pw, dsn=cs) as con:  # create the connecton to the database
            try:
                with con.cursor() as cur:  # start an entry cursor
                    print(f'INFO: Connection established to PS database on version: {con.version}')
                    print(f'INFO: Connection established to PS database on version: {con.version}', file=log)
                    with open(OUTPUT_FILE_NAME, 'w') as output:  # open the output file
                        print("Connection established: " + con.version)

                        today = datetime.now()  # get todays date and store it for finding the correct term later
                        # print("today = " + str(today)) #debug

                        # find the current term for the high school, used to find the high schooler's courses later
                        cur.execute("SELECT id, firstday, lastday, schoolid, yearid FROM terms WHERE IsYearRec = 0 AND schoolid = :school ORDER BY dcid DESC", school=COURSES_SCHOOL_ID)  # get a list of terms for a building, filtering to non-full years
                        termRows = cur.fetchall()
                        for term in termRows:
                            print(f'DBUG: Found term {term}', file=log)  # debug to see the terms
                            if (term[1] < today) and term[2] > today:
                                currentTerm = str(term[0])  # store the yearid as the term year we really look for in each student
                                print(f'DBUG: Current term is to {currentTerm} at building {COURSES_SCHOOL_ID}')
                                print(f'DBUG: Current term is to {currentTerm} at building {COURSES_SCHOOL_ID}', file=log)

                        cur.execute('SELECT students.student_number, students.id, students.schoolid, students.enroll_status, students.lunch_id, students.grade_level, students.dcid, U_StudentsUserFields.custom_student_email, u_def_ext_students0.totalcurrentcourses FROM students LEFT JOIN u_studentsuserfields ON students.dcid = u_studentsuserfields.studentsdcid LEFT JOIN u_def_ext_students0 ON students.dcid = u_def_ext_students0.studentsdcid ORDER BY student_number DESC')
                        students = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
                        for student in students:
                            try:  # do each student in a try/except block so if one throws an error we can skip to the next
                                print(f'DBUG: Starting student {student[0]} at building {student[2]}, current custom email {student[7]}, current lunch id {student[4]}')  # debug
                                print(f'DBUG: Starting student {student[0]} at building {student[2]}, current custom email {student[7]}, current lunch id {student[4]}', file=log)  # debug
                                stuID = str(int(student[0]))  # not converting to an int first likes to leave a trailing .0
                                internalID = str(student[1])
                                currentLunch = str(int(student[4]))
                                currentEmail = str(student[7])
                                currentCourseNumber = int(student[8]) if student[8] else None
                                newLunch = stuID
                                newEmail = stuID + EMAIL_SUFFIX
                                coursesChanged = False
                                numCourses = 0  # set the default to 0

                                # if the student is at the high school, look for their current classes, output number of classes in current term
                                if (student[2] == COURSES_SCHOOL_ID and student[3] == 0):  # only look at courses for students in specific building who are active
                                    cur.execute('SELECT cc.course_number, courses.course_name, cc.sectionid FROM cc LEFT JOIN courses ON cc.course_number = courses.course_number WHERE courses.credit_hours != 0 AND cc.termid = :term AND cc.studentid = :internalID', term=currentTerm, internalID=internalID)
                                    courseRows = cur.fetchall()
                                    numCourses = len(courseRows)
                                    print(f'INFO: Student {stuID} has {numCourses} current classes')
                                    print(f'INFO: Student {stuID} has {numCourses} current classes', file=log)
                                    print(f'DBUG: {courseRows}')
                                    print(f'DBUG: {courseRows}', file=log)
                                    if numCourses != currentCourseNumber:
                                        print(f'INFO: Current custom course count of {currentCourseNumber} does not match new count of {numCourses}, updating')
                                        print(f'INFO: Current custom course count of {currentCourseNumber} does not match new count of {numCourses}, updating', file=log)
                                        coursesChanged = True  # set flag to true so we know to output

                                if (currentEmail != newEmail) or (currentLunch != newLunch) or coursesChanged:
                                    if currentEmail != newEmail:  # just used for logging
                                        print(f'INFO: Custom email field for {newEmail} is not correct, updating')
                                        print(f'INFO: Custom email field for {newEmail} is not correct, updating', file=log)
                                    if currentLunch != newLunch:  # just for logging
                                        print(f'INFO: Lunch ID field for {newEmail} is not correct, updating')
                                        print(f'INFO: Lunch ID field for {newEmail} is not correct, updating', file=log)
                                    print(f'{stuID},{newLunch},{newEmail},{numCourses}', file=output)  # if either their custom email or lunch id is incorrect we write both values to the file for the input
                            except Exception as er:
                                print(f'ERROR while processing student {student[0]}: {er}')
                                print(f'ERROR while processing student {student[0]}: {er}', file=log)
            except Exception as er:
                print(f'ERROR while doing PowerSchool query: {er}')
                print(f'ERROR while doing PowerSchool query: {er}', file=log)

        try:
            # Now connect to the D118 SFTP server and upload the file to be imported into PowerSchool
            with pysftp.Connection(D118_SFTP_HOST, username=D118_SFTP_UN, password=D118_SFTP_PW, cnopts=CNOPTS) as sftp:
                print(f'INFO: SFTP connection to D118 at {D118_SFTP_HOST} successfully established')
                print(f'INFO: SFTP connection to D118 at {D118_SFTP_HOST} successfully established', file=log)
                # print(sftp.pwd)  # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.chdir(OUTPUT_FILE_DIRECTORY)
                # print(sftp.pwd) # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.put(OUTPUT_FILE_NAME)  # upload the file to our sftp server
        except Exception as er:
            print(f'ERROR while connecting to D118 SFTP server: {er}')
            print(f'ERROR while connecting to D118 SFTP server: {er}', file=log)

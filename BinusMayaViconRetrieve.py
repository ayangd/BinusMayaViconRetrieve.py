# Created by Michael Dlone
# Version 2020.9.16

import sys
# Package import handling
# Installs non-existing packages using pip
def tryImport(package):
    try:
        __import__(package)
    except ImportError:
        try:
            import pip
            pip.main(['install', package])
        except ImportError:
            print('pip and other package is not installed!')
            sys.exit()

def tryAllImport(packages):
    for p in packages:
        tryImport(p)

tryAllImport(['requests', 'bs4'])

import requests, bs4, re, json, traceback
from bs4 import BeautifulSoup as bs
from getpass import getpass

def clean(ls):
    l = []
    for e in ls:
        if re.match('^[\\s\n]+$', str(e)) == None:
            l.append(e)
    return l

def promptNumber(p, m, n):
    while True:
        i = input(p)
        if not i.isnumeric():
            continue
        i = int(i)
        if i >= m and i <= n:
            return i

# URLs
loginPageURL = 'https://binusmaya.binus.ac.id/login/'
loginURL = 'https://binusmaya.binus.ac.id/login/sys_login.php'
newStudentURL = 'https://binusmaya.binus.ac.id/newStudent'
getStudentCoursesURL = 'https://binusmaya.binus.ac.id/services/ci/index.php/student/init/getStudentCourseMenuCourses'
videoConferenceURL = 'https://binusmaya.binus.ac.id/services/ci/index.php/BlendedLearning/VideoConference/getList/{}/{}/{}/{}'

session = requests.Session()
test = None

# Login loop
while True:
    loginPage = session.get(loginPageURL)
    if not loginPage.ok:
        print('Cannot get login page. Maybe wait for a moment.')
        sys.exit(1)
    loginPageSoup = bs(loginPage.content, features='html.parser')

    loginPageForm = loginPageSoup.find('form')
    loginPageInputs = loginPageForm.findAll('input')

    loginPageScripts = loginPageSoup.findAll('script')
    loaderScript = None
    for script in loginPageScripts:
        if 'src' in script.attrs.keys():
            if script.attrs['src'].find('../login/loader.php') != -1:
                loaderScript = script
    loaderURL = loginPageURL + loaderScript.attrs['src']

    loaderScriptContent = session.get(loaderURL)
    if not loaderScriptContent.ok:
        print('Cannot get login page. Maybe wait for a moment.')
        sys.exit(1)
    hiddenInputs = re.findall('<input[^>]*>', loaderScriptContent.content.decode())

    print('Please input your credentials for data retrieval.')
    username = input('Login: ')
    password = getpass()

    loginForm = {
        loginPageInputs[0].attrs['name']: username,
        loginPageInputs[1].attrs['name']: password,
        loginPageInputs[2].attrs['name']: loginPageInputs[2].attrs['value'],
        bs(hiddenInputs[0], features='html.parser').find('input').attrs['name']:
            bs(hiddenInputs[0], features='html.parser').find('input').attrs['value'],
        bs(hiddenInputs[1], features='html.parser').find('input').attrs['name']:
            bs(hiddenInputs[1], features='html.parser').find('input').attrs['value']
    }

    loginResponse = session.post(loginURL, data=loginForm, headers={'Referer': loginPageURL}, allow_redirects=False)
    if not loginResponse.ok:
        print('Cannot login. Maybe wait for a moment.')
    if loginResponse.headers['Location'] == 'https://binusmaya.binus.ac.id/block_user.php':
        break
    else:
        print('Login failed.')

# Courses retrieval
studentCoursesResponse = session.post(getStudentCoursesURL, headers={'Referer': newStudentURL})
if not studentCoursesResponse.ok:
    print('Cannot get courses list. Maybe wait for a moment.')
    sys.exit(1)
studentCourses = json.loads(studentCoursesResponse.content.decode())

while True:
    # Semester selection
    options = 0
    print('Select semester.')
    for semester in studentCourses[0][3]:
        options += 1
        print('{}. {}'.format(options, semester[1]))
    options += 1
    print(f'{options}. Exit')
    semesterIndex = promptNumber('> ', 1, options) - 1
    if semesterIndex == options - 1:
        break

    # Class selection
    options = 0
    print('Select class.')
    classList = studentCourses[0][3][semesterIndex]
    skip = 2
    for class_ in classList:
        if skip != 0:
            skip -= 1
            continue
        options += 1
        print('{}. {} ({})'.format(options, class_['COURSE_TITLE_LONG'], class_['CLASS_SECTION']))
    options += 1
    print(f'{options}. Back')
    classIndex = promptNumber('> ', 1, options) + 1
    if classIndex == options + 1:
        continue

    # Data preparation
    courseCode = classList[classIndex]['CRSE_CODE']
    courseID = classList[classIndex]['CRSE_ID']
    strm = classList[classIndex]['STRM']
    classNumber = classList[classIndex]['CLASS_NBR']

    # VideoConferenceRetrieval
    videoConferenceResponse = session.get(videoConferenceURL.format(courseCode, courseID, strm, classNumber), headers={'Referer':newStudentURL})
    if not videoConferenceResponse.ok:
        print('Cannot get video conference list. Maybe wait for a moment.')
    else:
        videoConferenceSoup = bs(videoConferenceResponse.content.decode(), features='html.parser')
        videoConferenceList = videoConferenceSoup.find('tbody')
        videoConferenceListContent = list(videoConferenceList.children)
        videoConferenceListContent = clean(videoConferenceListContent)
        test = videoConferenceListContent
        if str(videoConferenceListContent[0]).find('No Data') == -1:
            try:
                print('Video Conference for {} ({}):'.format(classList[classIndex]['COURSE_TITLE_LONG'], classList[classIndex]['CLASS_SECTION']))
                for videoConferenceData in videoConferenceListContent:
                    videoConferenceDataContent = list(videoConferenceData.children)
                    videoConferenceDataContent = clean(videoConferenceDataContent)
                    #print(videoConferenceDataContent)
                    videoConferenceDataContent = [clean(list(x.children))[0] if len(clean(list(x.children))) > 0 else 'N/A' for x in videoConferenceDataContent]
                    _, week, session_, date, time, number, password, link = videoConferenceDataContent
                    print('Week/Session: {}/{}'.format(week, session_))
                    print('Date/Time: {}/{}'.format(date, time))
                    print('Meeting Number: {}'.format(number))
                    print('Password: {}'.format(password))
                    if link == 'N/A':
                        print('Link: N/A')
                    else:
                        print('Link: {}'.format(link.attrs['link_vc']))
                    print('')
            except Exception as e:
                print('An error occured! Please tell this to the developer!')
                print('This can sometimes happen because BinusMaya has either changed its internals or the developer\'s dumbness.')
                print(traceback.format_exc())
                print(f'Parsed values: {videoConferenceListContent}')
        else:
            print('No Video Conference available.')

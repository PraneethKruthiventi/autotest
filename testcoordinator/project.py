import subprocess
import os
import conf
from conf import participant_dir
import xml.etree.ElementTree as ET
import time
from pymongo import MongoClient
import shlex
import timed_execution
import json
from celery import Celery
import tasks

def listofParticipants():
    """ This method will go through each user in the participant
    directory and looks for changes for the repository
    corresponding to each user.  
    
    Yields the username, and the subdirectory that changed as a
    tuple.
    """
    dirs1 = os.listdir(conf.participant_dir)
    for user in dirs1:
        direct=participant_dir + user + '/'
        previous={}
        print "Checking for user %s" % user
        for y in os.listdir(direct):
            if os.path.isdir(direct+'/'+y) and y[0] !='.':
                previous[y] = subprocess.check_output(['/usr/bin/git','log','-1','--oneline',y],cwd=direct)
        subprocess.call(['/usr/bin/git', 'reset', '--hard', 'HEAD'], cwd=direct)
        subprocess.call(['/usr/bin/git', 'clean',  '-d',  '-fx', '""'], cwd=direct)
        subprocess.call(['/usr/bin/git', 'pull', '-s', 'recursive', '-X', 'theirs'], cwd=direct)

        for y in os.listdir(direct):
            if os.path.isdir(direct+'/'+y) and y[0] !='.':
                after = subprocess.check_output(['/usr/bin/git',
                                                 'log','-1',
                                                 '--oneline',y],
                                                cwd=direct)
                if y not in previous or previous[y] != after:
                    yield user,y
        
  
''' copied to ts    
def inputoutput(progname):
    """ Yields the combinations of input_string, output_string
    and description expected to pass for the given program.
    """
    tree = ET.parse(conf.program_dir+progname+".xml")
    root=tree.getroot()
    for test in root:
        if test.tag != 'test':
            continue
        input_str=test.find('input').text
        output_str=test.find('output').text
        description=test.find('description').text
        yield input_str,output_str,description 
'''       
def mainloop():
    """ This is the main driver program to look for changes and
    run tests, save the results and send mails for iteration.
    """
    print conf.db_host
    client = MongoClient(conf.db_host)
    db = client.autotest
    col_submissions=db.submissions
    col_scores=db.scores
    result={}#creating empty dict for results
        
    for user,programname in listofParticipants():
        if user not in result:
            result[user]=[]#creating a new tupple in res with no values
        program_dir=conf.participant_dir+user+'/'+programname #getting program code into program
        program_name=conf.program_dir+programname+'.xml'#getting program code  xml into program

        # Check if this programis something we support
        if not os.path.isfile(program_name): 
            result[user].append('The program *%s* is INVALID' % programname)
            result[user].append('-----------------------------------------------')
            result[user].append('Sorry but we did not recognize this program name. \nPerhaps you created a private directory for some other purpose.')
            col_submissions.save({
                    "user_name":user,
                    "program":programname,
                    "program_result":'INVALID PROGRAM',
                    "test_case_result":[None,None,None],
                    "time":time.time(),
                })
            continue
        _submission = tasks.progtest.apply_async(args=(user, programname), queue='testing')
        submission = _submission.get()
        print "==> Saving submission record in the DB, after execution <=="
        col_submissions.save({
            "user_name":submission["user"],
            "program":submission["programname"],
            "program_result":submission["progstatus"],
            "score":submission["score"],
            "test_case_result":submission["description"],
            "time":time.time()
        })
        
        # If the user gets some score, update the score collection with latest
        # information
        if your_score:
            current_score = col_scores.find_one({'user_name':user})
            if not current_score:
                current_score = {
                    'user_name': user,
                    'programs': {}
                }
            current_score['programs'][programname] = {
                    'status': submission["progstatus"],
                    'score': submission["score"]
            }
            col_scores.save(current_score)
            progs = current_score['programs']
            total_score = sum(progs[x]['score'] for x in progs)
            result[user].insert(0, "YOUR NEW SCORE IS %s" % str(total_score))


# Python main routine to run the mainloop in a loop :-) 
# We have a minimum delay of 10 seconds between checks
if __name__ == '__main__':
    while True:
        start_time=time.time()
        mainloop()
        exec_time = time.time()-start_time
        print exec_time
        
        if exec_time > 10:
            pass
        else:
            time.sleep(10-exec_time)


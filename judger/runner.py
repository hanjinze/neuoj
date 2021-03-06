#!/usr/bin/python
import shlex
import subprocess
import os
import time

import memcache
import MySQLdb

import nocalls


global mc


def run(source, lang, indata, outdata, timelimit, memlimit):
    print source
    os.setuid(501)
    os.chdir('/Users/godfather/judge/')
    if lang == 'JAVA':
        timelimit *= 3
    cmd = {}
    fname = {}
    fname['GCC'] = 'Main.c'
    fname['G++'] = 'Main.cpp'
    fname['JAVA'] = 'Main.java'
    f = file(fname[lang], 'w')
    f.write(source)
    f.close()
    cmd['GCC'] = 'gcc Main.c -o Main -O2 -std=c99'
    cmd['G++'] = 'g++ Main.cpp -o Main -O2'
    cmd['JAVA'] = 'javac Main.java'
    fd1 = file('out.txt', 'w')
    fd2 = file('err.txt', 'w')
    print cmd[lang]
    p = subprocess.Popen(shlex.split(cmd[lang]), stdout=fd1, stderr=fd2)
    p.wait()
    fd1.close()
    fd2.close()
    if p.returncode != 0:
        e = file('err.txt', 'r')
        return ('CE', e.read())
    cmd['GCC'] = './Main'
    cmd['G++'] = './Main'
    cmd['JAVA'] = 'java Main'
    returncode = 0
    fd0 = file('in.txt', 'w')
    fd0.write(indata)
    fd0.close()
    fd0 = file('in.txt', 'r')
    fd1 = file('out.txt', 'w')
    fd2 = file('err.txt', 'w')
    start = time.time()
    p = subprocess.Popen(shlex.split(cmd[lang]), stdin=fd0, stdout=fd1, stderr=fd2)
    mm = 0
    while True:
        #s = file('/proc/' + str(p.pid) + '/status', 'r').read()
        if p.poll() != None:
            fd0.close()
            fd1.close()
            fd2.close()
            fd1 = file('out.txt', 'r')
            fd2 = file('err.txt', 'r')
            if p.poll() != 0:
                return ('RE', 0, 0)
            out = fd1.read()
            outdata = str(outdata).replace('\r', '')
            if len(out) == 0:
                return ('WA', tt, mm)
            while out[-1] == '\n':
                out = out[:-1]
            while outdata[-1] == '\n':
                outdata = outdata[:-1]
            if out == outdata:
                return ('AC', tt, mm)
            else:
                out = out.replace('\n', '')
                out = out.replace(' ', '')
                outdata = outdata.replace('\n', '')
                outdata = outdata.replace(' ', '')
                if out == outdata:
                    return ('PE', tt, mm)
                return ('WA', tt, mm)
        tt = time.time() - start
        if tt > timelimit:
            #os.kill(p.pid,9)
            p.kill()
            return ('TLE', tt, mm)
            #print s
        #if s.find('RSS') < 0:
        #    continue
        #s = s[s.find('RSS') + 6:]
        #s = s[:s.find('kB') - 1]
        #mm = int(s)
        mm=64+tt/10
        if mm > memlimit:
            #os.kill(pid,9)
            p.kill()
            return ('MLE', tt, mm)


def submit(c, runid, result):
    if mc.get('results') != None and len(mc.get('results')) > 0:
        mcs = mc.get('results')
    else:
        mcs = []
    mcs.append((c, runid, result))
    mc.set('results', mcs)


def testcode(s):
    s = s.replace('\n', '')
    s = s.replace(' ', '')
    s = s.replace('\r', '')
    for nocall in nocalls.nocalls:
        if s.find(nocall + '(') >= 0:
            return False
    return True


if __name__ == '__main__':
    mc = memcache.Client(['127.0.0.1:11211'])
    while True:
        time.sleep(1)
        print 'sleep done'
        conn = MySQLdb.connect(host='localhost', user='root', passwd='', db='neuoj')
        cursor = conn.cursor()
        if mc.get('pendings') != None and len(mc.get('pendings')) > 0:
            temp = mc.get('pendings')
            print 'length of pendings',len(temp)
            runid, c, source, lang, datas, timelimit, memlimit = temp.pop(0)
            print 'runing',runid
            if testcode(source):
                mc.set('pendings', temp)
                print c, runid
                result = ('AC', 0, 0)
                PE = False
                for data in datas:
                    re = run(source, lang, data[0], data[1], timelimit, memlimit)
                    if re[0] == 'CE':
                        result = ('CE', re[1])
                        break
                    elif re[0] == 'RE':
                        result = re
                        break
                    elif re[0] == 'WA':
                        result = re
                        break
                    elif re[0] == 'TLE':
                        result = re
                        break
                    elif re[0] == 'MLE':
                        result = re
                        break
                    elif re[0] == 'PE':
                        PE = True
                    #print re
                if result[0] != 'AC':
                    submit(c, runid, result)
                elif PE:
                    submit(c, runid, ('PE', re[1], re[2]))
                else:
                    submit(c, runid, re)
            else:
                submit(c, runid, ('RF', 0, 0))#Restricted Function
        conn.commit()
        cursor.close()
        conn.close()

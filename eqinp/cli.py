import os
import shutil
import subprocess


class Cli:
    def __init__(
        self,
        inpfile,
        weatherfile,
        doe2dir='C:/doe22',
        clirundir='cliruns'
    ):
        self.inpfilefull = inpfile
        self.inpfiledir, self.inpfilename = os.path.split(self.inpfilefull)
        self.tempfilefull = self.inpfiledir + '/' + \
            clirundir + '/' + self.inpfilename.replace(" ", "_")

        self.tempfiledir, self.tempfilename = os.path.split(self.tempfilefull)

        self.tempsimfilefull = self.tempfilefull.replace(".inp", '.SIM')
        self.tempbdlfilefull = self.tempfilefull.replace(".inp", '.BDL')

        self.weatherfile = weatherfile
        self.batchfilefull = self.tempfiledir + '/RUN_' + self.tempfilename + '.BAT'
        self.doe2dir = doe2dir

    def copyinputs(self):
        shutil.copy(self.inpfilefull, self.tempfilefull)

    def checkdirs(self):
        if not os.path.exists(self.doe2dir):
            print('cannot find doe2 directory: ' + self.doe2dir)
            return
        if not os.path.exists(self.doe2dir + '/weather/' + self.weatherfile):
            print(self.doe2dir + '/weather/' + self.weatherfile)
            print('cannot find weather file: ' + self.weatherfile)
            return
        if not os.path.exists(self.tempfiledir):
            os.mkdir(self.tempfiledir)
            print('created directory: ' + self.tempfiledir)

    def getfileloc(self, x):
        return os.path.split(x)[0]

    def createbatch(self):
        head = ['call C:\doe22\doe22env CONFIG\n']
        foot = ['call C:\doe22\doe22env CLEAR\n']
        body = ['call C:\doe22\doe22 exent {0} {1}\n'.format(
            self.tempfilename.replace('.inp', ''), self.weatherfile.replace(
                '.bin', '').replace('.binm', '')
        )]
        batchtemplate = ''.join(head+body+foot)

        with open(self.batchfilefull, 'w') as f:
            f.writelines(batchtemplate)

    def rundoe2(self, showoutput):
        '''
        batch runner for doe2 CLI. 
        currently not using Popen due
        to process remaining open periodically.
        '''
        originaldir = os.getcwd()
        os.chdir(self.tempfiledir)

        print('simulating: {0}'.format(self.inpfilename))
        p = subprocess.call(self.batchfilefull)
        os.chdir(originaldir)

    def getsim(self):
        return self.tempsimfilefull

    def getbdl(self):
        return self.tempbdlfilefull

    def run(self, showoutput):
        self.checkdirs()
        self.copyinputs()
        self.createbatch()
        self.rundoe2(showoutput)
        self.tempsimfilefull = self.tempfilefull.replace(".inp", '.SIM')
        self.tempbdlfilefull = self.tempfilefull.replace(".inp", '.BDL')

        return self.tempsimfilefull
        # self.copyresults()

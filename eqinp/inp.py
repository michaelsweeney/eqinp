import os
import shutil
import subprocess
import re

from .cli import Cli
# from .parm import Parm


class Inp:

    '''
    container for inp file with load / saveas /
    basic compiling, regex-style operations
    '''

    def __init__(self, inpfile, weatherfile):
        self.inpfilefull = inpfile
        self.inpfiledirectory, self.inpfilename = os.path.split(inpfile)
        self.workinginp = self._loadfile()
        self.objectdict = self._get_object_dict()
        self.weatherfile = weatherfile
        self.cli = Cli(self.inpfilefull, weatherfile)

    def _loadfile(self):
        with open(self.inpfilefull, 'r') as f:
            flist = f.readlines()
            return ''.join(flist)

    def find_reg(self, query):
        '''
        FOR TESTING REGEX SYNTAX / SEARCHING THROUGH QUERIES
        '''
        inpstr = self.workinginp

        pattern = re.compile(query)

        hits = []
        for m in re.finditer(pattern, inpstr):
            start = m.start()
            end = m.end()
            res = inpstr[m.start(): m.end()]
            hits.append(res)
        return hits

    def set_global_parameter(self, param, val, showoutput=True):
        pattern = '.*PARAMETER.*\n.*\"{0}\".*\.\..*\n'.format(param)
        replace = 'PARAMETER\n   "{0}" = {1} ..\n'.format(param, val)
        working = self.workinginp
        result = re.findall(pattern, working)

        if len(result) > 1:
            print(
                'error: more than one matching parameter found: {0}'.format(param))
            return
        if len(result) == 0:
            print('error: no matching parameters found.')
            return
        else:
            result = result[0]
            if showoutput:
                print('replacing: \n{0}\nwith:\n{1}'.format(result, replace))
            self.string_replace(result, replace)
        return

    def sub_func(self, find, replace_func, showoutput=True, **kwargs):
        '''
        uses kwargs to allow passing function to handle regexp match.

        example ('inp' is Inp instance): multiplies infiltration by 9:

        def multiplyinfiltration(matchstr, **kwargs):
            left, right = matchstr.split("=")
            right = float(right.strip()) * kwargs['mult']
            combined = left + ' = ' + str(right) + '\n'
            return combined

        inp.sub_func('.*INF-FLOW.*', multiplyinfiltration, mult = 9)
        '''

        working = self.workinginp
        newstr, numreplacements = re.subn(
            find,
            lambda x: replace_func(x.group(), **kwargs),
            working
        )

        if showoutput:
            print(numreplacements, ' replacements: ',
                  'find: ', find, 'replace: ', replace_func)
        self.workinginp = newstr

    def _get_left_of_assignment(self, x):
        return x.split('=')[0].replace('\n', '').replace('\"', '').strip()

    def _get_right_of_assignment(self, x):
        return x.split(
            '='
        )[1].split('\n')[0].strip()

    def _get_object_dict(self):
        working = self.workinginp
        sub = re.sub('\$.*\n', '',  working)
        split = sub.split('..')

        trimmed = {
            self._get_left_of_assignment(x): self._get_right_of_assignment(x) for x in split if len(x.split('=')) > 1
        }

        return trimmed

    def _get_object_parameters(self, bdlobjname, bdlobjtype):
        '''returns dict of parameters in object.'''
        working = self.workinginp.split('\n')
        hits = [
            (num, line) for num, line in enumerate(working)
            if bdlobjname == self._get_left_of_assignment(line) and bdlobjtype in line and "=" in line
        ]
        if len(hits) > 1:
            print('error: more than one object found: {0}'.format(hits))
            return
        else:
            hit = hits[0]

        objstring = '\n'.join(working[hit[0]:]).split('..')[0].split('\n')
        objdict = {
            self._get_left_of_assignment(x): self._get_right_of_assignment(x) for x in objstring if len(x.split('=')) > 1
        }
        del objdict[bdlobjname]
        return objdict

    def _get_object_index(self, bdlobjname):
        '''find occurrence of bdlobjname, find next-occuring .. 
        and return tuple of start/end'''

        start = 0
        end = 0
        isobject = False
        linesplit = self.workinginp.split('\n')
        for num, line in enumerate(linesplit):
            if bdlobjname == self._get_left_of_assignment(line):
                isobject = True
                start = num
            if '..' in line and isobject:
                end = num
                isobject = False
                return start, end
        if start == 0 and end == 0:
            print('error: no index found for object {0}'.format(bdlobjname))
            return

    def set_object_parameter(self, bdlobjname, paramname, val, showoutput=True):
        '''
        explicitly sets input file object based on object name, parameter name, and value.
        bdlobjname should be a string without *additional* quotes - i.e. "SPC-1" NOT '"SPC-1"'.
        paramname should be a string i.e. 'POLYGON'
        val can be either depending on whether quotes are required in the input file 
        '''

        if type(val) != str:
            val = str(val)

        workingstr = self.workinginp
        workinglist = workingstr.split('\n')

        objectdict = self.objectdict
        bdlobjtype = objectdict[bdlobjname]
        objectindex = self._get_object_index(bdlobjname)

        parameters = self._get_object_parameters(bdlobjname, bdlobjtype)

        if paramname not in parameters:
            print(
                '{0} not found in {1}. adding key and value pair but errors may occur due to bdl parameter order.'.format(
                    paramname, bdlobjname)
            )
        parameters[paramname] = val

        compiled_obj_header = '"{0}" = {1}'.format(bdlobjname, bdlobjtype)
        compiled_obj_middle = [
            param[0] + '=' + param[1]
            for param in parameters.items()
        ]
        compiled_obj_foot = '..'
        compiled_obj = [compiled_obj_header] + \
            compiled_obj_middle+[compiled_obj_foot]

        left_of_compiled = workinglist[0:objectindex[0]]
        right_of_compiled = workinglist[objectindex[1]:]

        compiled_full = left_of_compiled + compiled_obj + right_of_compiled
        self.workinginp = '\n'.join(compiled_full)
        return compiled_full

    def string_replace(self, find, replace):
        '''simple non-regex find / replace'''
        self.workinginp = self.workinginp.replace(find, replace)

    def sub_reg(self, find, replace, showoutput=True):
        '''regex find/replace'''
        working = self.workinginp
        newstr, numreplacements = re.subn(find, replace, working)
        if showoutput:
            print(numreplacements, ' replacements: ',
                  'find: ', find, 'replace: ', replace)
        self.workinginp = newstr

    def saveas(self, fname):
        with open(fname, 'w') as f:
            print('writing to disk: \n' + fname)
            f.writelines(self.workinginp)
        self.inpfilefull = fname

    def run(self, showoutput=False):
        self.cli = Cli(self.inpfilefull, self.weatherfile)
        return self.cli.run(showoutput)

    def getinpfile(self):
        return self.inpfilefull

    def getsimfile(self):
        if not os.path.exists(self.cli.getsim()):
            print('error: no sim file found')
        return self.cli.getsim()

    def getbdlfile(self):
        if not os.path.exists(self.cli.getbdl()):
            print('error: no bdl file found')
            return
        return self.cli.getbdl()

    def geterrors(self):
        bdlfile = self.getbdlfile()

        with open(bdlfile, 'r') as f:
            flist = f.readlines()

        errorlist = []
        for line in flist:
            if 'ERROR' in line.upper():
                errorlist.append(line)
        joined = ''.join(errorlist).split('\n')
        if joined == ['']:
            return 'no errors'
        else:
            return joined

    def makeparm(self, ecmtag, operations, showoutput=True, weatherfile=False):

        inpfile = self.inpfilefull
        if not weatherfile:
            weatherfile = self.weatherfile
        parm = self._parm(inpfile, weatherfile, ecmtag,
                          operations, showoutput=showoutput)
        return parm

    def _parm(self, rootinp, weatherfile, ecmtag, operations, showoutput):
        ''' create inp file and return new Inp object

        schemaformat = {
        rootinp: '',
        weatherfile: '',
        ecmtag: '',
        operations: [
                {
                    kind: -> regex | replace | object | parameter | func
                    find: '',
                    replace: '',
                }
            ]
        }
        '''

        if type(operations) == dict:
            operations = [operations]

        inp = Inp(rootinp, weatherfile)

        if len(ecmtag.split('.')) > 1:
            if ecmtag.split('.')[1] == 'inp':
                ecmtag = ecmtag.split('.')[0]
        new_file = inp.inpfiledirectory + '/' + ecmtag + '.inp'

        for op in operations:

            kind = op['kind']

            if kind not in [
                'parameter', 'object', 'func', 'replace', 'regex'
            ]:
                print(f'invalid operation kind: {kind}. \
                    must pass valid kind: "parameter", "object", "func", "replace", "regex"')
                return

            if kind == 'parameter':
                param = op['param']
                val = op['val']
                inp.set_global_parameter(param, val, showoutput=showoutput)

            if kind == 'object':
                bdlobjname = op['bdlobjname']
                paramname = op['paramname']
                val = op['val']
                inp.set_object_parameter(
                    bdlobjname, paramname, val, showoutput=showoutput)

            if kind == 'func':
                inp.sub_func(find, replace, showoutput)

            if kind == 'replace':
                find = op['find']
                replace = op['replace']
                inp.string_replace(find, replace, showoutput)

            if kind == 'regex':
                find = op['find']
                replace = op['replace']
                inp.sub_reg(find, replace, showoutput)

        inp.saveas(new_file)
        return Inp(new_file, weatherfile)

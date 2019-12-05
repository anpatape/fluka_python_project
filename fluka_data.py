import os
import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from time import time


def say(msg):
    print(msg)


def __tuple2str__( tupl ):
    st = ''
    for i in range(0, len(tupl)):
        st = st + str(tupl [i])
    return st


def ascii2lines(fn, mode='r'):
    try:
        f = open(file=fn, mode=mode)
        try:
            lines = f.readlines()
        except:
            say("ERROR: UnicodeDecodeError in '%s'. Trying to convert to ASCII: " % (fn))
            f.close()
            printable = set(string.printable)
            f = open(file=fn, mode='rb')
            blines = f.readlines()
            lines = []
            for line in blines:
                try:
                    line = line.decode('utf-8')
                except:
                    # convert to ascii
                    filter(lambda x: x in printable, line)
                    line = str(line)
                    # print("line has been changed: ", line)
                lines.append(line)
        f.close()
        return lines
    except:
        say("ERROR: Cannot open file '%s'" % (fn))
        return None


def lines2ascii(lines, fn, mode='w'):
    try:
        f = open(file=fn, mode=mode)
        for line in lines:
            if line[-1:] == """\n""":
                f.write(line)
            else:
                line += """\n"""
                f.write(line)
        f.close()
    except:
        say("ERROR: Cannot open file '%s'" % (fn))


def ascii2nparray(fn, mode='r',comment='#'):
    l = ascii2lines(fn=fn, mode=mode)
    lines = []
    for line in l:
        line  = line.strip()
        if line[0] != comment:
            st = line.split()
            for i in range(len(st)):
                st[i] = float(st[i])
            lines.append(st)
    return np.array(lines)


class DataNode(object):
    def __init__(self, lines, nstart=0):
        self.current_line_number = nstart
        self.lines = lines
        self.nmax = len(lines)
        self.current_line = self.lines[self.current_line_number].strip()
        float_number_pattern = "^(\s*)(-*)([\d]+)(\.)([\d]+)(E)([+]*)([-]*)([\d]+)"
        float_number_start_pattern = "^(\s*)(-*)([\d]+)(\.)([\d]+)(E)([+]*)([-]*)([\d]+)"
        any_number_pattern = "(-*)([\d]+)(\.*)([\d]*)(E*)([+]*)([-]*)([\d]*)"
        any_number_start_pattern = "^(-*)([\d]+)(\.*)([\d]*)(E*)([+]*)([-]*)([\d]*)"
        from_line_pattern = "from *-*[\d]"
        self.from_line = re.compile(from_line_pattern)
        self.float_number = re.compile(float_number_pattern)
        self.float_number_start = re.compile(float_number_start_pattern)
        self.any_number = re.compile(any_number_pattern)
        self.any_number_start = re.compile(any_number_start_pattern)

    def skip_empty_lines(self):
        while self.current_line == '':
            self.current_line_number += 1
            self.current_line = self.lines[self.current_line_number].strip()

    def peek_next_line(self):
        i = self.current_line_number + 1
        if i < self.nmax-1:
            return self.lines[self.current_line_number + 1].strip()
        else:
            return 'EOF'

    def get_next_line(self):
        i = self.current_line_number + 1
        if i < self.nmax:
            self.current_line_number = i
            self.current_line = self.lines[self.current_line_number].strip()
        else:
            self.current_line_number = i
            self.current_line = 'EOF'


class USRBIN(DataNode):
    def __init__(self, lines, nstart=0):
        super(USRBIN, self).__init__(lines, nstart=nstart)
        self.tag_data_begin = '1'
        self.bins = self.get_bins()
        self.data = self.get_data()
        self.errors = self.get_data()

    def get_bins(self):
        bins = []
        while self.current_line != self.tag_data_begin:
            self.get_next_line()
        while self.from_line.search(self.current_line) is None:
            self.get_next_line()
        while self.from_line.search(self.current_line) is not None:
            coord = self.any_number.findall(self.current_line)
            bb = []
            for i in range(0, len(coord)):
                bb.append(float(__tuple2str__(coord[i])))
            bins.append(bb)
            self.get_next_line()
        for i in range(len(bins)):
            bins[i][2] = int(bins[i][2])
        return bins

    def get_data(self):
        data = []
        while self.float_number_start.search(self.current_line) is None:
            self.get_next_line()
        while self.float_number_start.search(self.current_line) is not None:
            line = self.current_line.split()
            for s in line:
                data.append(float(s))
            self.get_next_line()
        nx = self.bins[0][2]
        ny = self.bins[1][2]
        nz = self.bins[2][2]
        b = np.zeros((nx, ny, nz))
        for i in range(0, nx):
            for j in range(0, ny):
                for k in range(0, nz):
                    b[i, j, k] = float(data[i + nx * j + nx * ny * k])
        return b


#
#

def get_usrbins(fn):
    lines = ascii2lines(fn=fn)
    start = 0
    data = []
    usrbin = USRBIN(lines, nstart=start)
    data.append(usrbin.data)
    while usrbin.current_line is not 'EOF':
        usrbin = USRBIN(lines, nstart=usrbin.current_line_number)
        data.append(usrbin.data)
    #print(len(data))
    return data


path = "/home/apatapenka/NorthStar/fluka_simulations/Layout_radiation_protection/NorthStar_design_vault/30kev_treshold/"
fn = "simple_vault_ns_40.bnn.lis"
#fn = os.path.join(path, fn)

lines = ascii2lines(fn=fn)
usrbin = USRBIN(lines)
usrbin.get_bins()

#print(usrbin.bins)
#print(usrbin.errors)

data = get_usrbins(fn)


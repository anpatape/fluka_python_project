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
    data.append(usrbin)
    while usrbin.current_line is not 'EOF':
        usrbin = USRBIN(lines, nstart=usrbin.current_line_number)
        data.append(usrbin)
    #print(len(data))
    return data


def data_3D_slice(usrbin_data,
            xmin=None, xmax=None,
            ymin=None, ymax=None,
            zmin=None, zmax=None):
    bins = usrbin_data.bins
    x = np.linspace(bins[0][0], bins[0][1], bins[0][2])
    y = np.linspace(bins[1][0], bins[1][1], bins[1][2])
    z = np.linspace(bins[2][0], bins[2][1], bins[2][2])
    # X
    if xmin is not None:
        ix_min = np.where(x >= xmin)[0]
    else:
        ix_min = 0
    if xmax is not None:
        ix_max = np.where(x <= xmax)[-1]
    else:
        ix_max = bins[0][2]
    # Y
    if ymin is not None:
        iy_min = np.where(y >= ymin)[0][0]
    else:
        iy_min = 0
    if ymax is not None:
        iy_max = np.where(y <= ymax)[0][-1]
    else:
        iy_max = bins[1][2]
    # Z
    if zmin is not None:
        iz_min = np.where(z >= zmin)[0]
    else:
        iz_min = 0
    if zmax is not None:
        iz_max = np.where(z <= zmax)[-1]
    else:
        iz_max = bins[2][2]
    print(ix_min,ix_max, iy_min,iy_max, iz_min,iz_max)
    return usrbin.data[ix_min:ix_max, iy_min:iy_max, iz_min:iz_max]


def data_2D_plot(data, x1, x2 ,proj):
    pass


#path = "/home/apatapenka/NorthStar/fluka_simulations/Layout_radiation_protection/NorthStar_design_vault/30kev_treshold/"
#fn = "simple_vault_ns_concr_local_40.bnn.lis"
fn = "simple_vault_ns_concr_local_30.bnn.lis"
#fn = "simple_vault_ns_30.bnn.lis"
#fn = os.path.join(path, fn)

data_ = get_usrbins(fn)
bins = data_[0].bins
x = np.linspace(bins[0][0], bins[0][1], bins[0][2])
y = np.linspace(bins[1][0], bins[1][1], bins[1][2])
z = np.linspace(bins[2][0], bins[2][1], bins[2][2])
#print(bins)

from scipy.optimize import curve_fit

def exp_f(x, a, b):
    return a * np.exp(b * x)

#x = np.linspace(0,4,50)
#y = exp_f(x, 2.5, 1.3)
#yn = y + 0.2*np.random.normal(size=len(x))
#p0 = [1, 1]
#popt, pcov = curve_fit(exp_f, x, yn, p0=p0)
#print(popt, pcov)

##################
# X = 0; I = 18
# Y = 0; I = 4
# walls : X = 203:433  cm
#         Z = 861:1091 cm
##################

norm = (1.2E+5/4.0E+7)*6.2415E+18*1.0E-12*3600

data = data_[0].data * norm
data = data + np.flip(data, 2)

ax = plt.figure()
plt.imshow(np.log10(np.sum(data,1)))

"""
##################################################
#
# Prompt doses YZ
#
##################################################


# i_y = 4  # 0-10
# i_z = 17 # 0-108

W = np.zeros((108, 18))
W = W + 2.3
lambda_coeff = []
for i_y in range(0, 18):
    for i_z in range(0, 108):

        inds = np.where(x > 203)
        yd = data[:, i_y, i_z][inds]
        xd = x[inds]
        Dose_after_wall = yd[-1]
        Dose_desired = 5.0E-5

        if Dose_after_wall > Dose_desired:

            a, b = np.polyfit(xd, np.log(yd), 1, w=np.sqrt(yd))

            a,b = np.polyfit(xd, np.log(yd), 1) #, w=np.sqrt(yd))
            y_a = a*xd + b
            yd_a = np.exp(a*xd + b)

            # errors :
            mx = np.average(xd)
            my = np.average(yd)
            Dyy = np.sum((np.log(yd) - np.average(np.log(yd)))**2)
            Dxx = np.sum((xd - np.average(xd))**2)
            sk = np.sqrt(1/(len(xd)-2) * (Dyy/Dxx - a**2))


            inds = np.where( x < 203)
            Dose_ = data[:, i_y, i_z][inds]
            Dose_0 = Dose_[-1]
            #print('Dose inner wall ', Dose_0)

            a_min = a + np.abs(1*sk)
            Thickness = -(np.log(Dose_0) - np.log(Dose_desired))/a_min


            try:
                Thickness = float(Thickness)
                W[i_z, i_y] = Thickness /100
                print('Wall thickness: %s, decay parameter: %s +- %s' % (round(Thickness), a * 100, np.abs(sk * 2) * 100))
                lambda_coeff.append(a_min)
            except Exception:
                print(i_z, i_y)
            #else:
                #W[i_x, i_y] = 2.3
                #print('Normalno: ', i_x, i_y)
#plt.imshow(W.T)
# for seaborn
W = W.T
W = np.flip(W,0)


import seaborn
import seaborn as sns
import pandas as pd

dd = data[-1,:,:]
dd = np.flip(dd, 0)
df = pd.DataFrame(dd)
plt.figure()
ax = sns.heatmap(W, annot=True, yticklabels=np.round(np.flip(y)), xticklabels=np.round(z), cbar_kws={"label": "Required wall thickness, m"})
ax.figure.axes[-1].yaxis.label.set_size(16)
ax.set_xlabel('Z')
ax.set_ylabel('Y')
ax.xaxis.label.set_size(18)
ax.yaxis.label.set_size(18)
#plt.xticks(x)
#plt.yticks(y)

ax = plt.figure()
ax = sns.heatmap(dd*1.0E+6, yticklabels=np.round(np.flip(y)), xticklabels=np.round(z),
                 cbar_kws={"label": " \u03BCSv/h"})
ax.figure.axes[-1].yaxis.label.set_size(16)
ax.set_xlabel('Z')
ax.set_ylabel('Y')
ax.xaxis.label.set_size(18)
ax.yaxis.label.set_size(18)
#ax.set_yticks(y)
#sns.heatmap(dd, annot=False, cbar_kws={"label": " \u03BCSv/h"})


print('Wall thickness: ', (W))
print('Lambda koeff.: ', np.max(lambda_coeff), np.min(lambda_coeff))

#plt.semilogy(xd, yd) #/np.max(yd))

#plt.semilogy(xd, yd)
#plt.semilogy(xd, yd_a)

#plt.plot(xd, a + b*xd)

#print(yd/np.max(yd), yd_a)
#plt.show()
"""


"""
##################################################
#
# Prompt doses XY
#
##################################################


# i_y = 4  # 0-10
# i_x = 17 # 8-20

W = np.zeros((40, 18))
W = W + 2.3
lambda_coeff = []
for i_y in range(0, 18):
    for i_x in range(0, 40):

        inds = np.where(z > 861)
        yd = data[i_x, i_y, :][inds]
        xd = z[inds]
        Dose_after_wall = yd[-1]
        Dose_desired = 5.0E-5

        if Dose_after_wall > Dose_desired:

            a, b = np.polyfit(xd, np.log(yd), 1, w=np.sqrt(yd))

            a,b = np.polyfit(xd, np.log(yd), 1) #, w=np.sqrt(yd))
            y_a = a*xd + b
            yd_a = np.exp(a*xd + b)

            # errors :
            mx = np.average(xd)
            my = np.average(yd)
            Dyy = np.sum((np.log(yd) - np.average(np.log(yd)))**2)
            Dxx = np.sum((xd - np.average(xd))**2)
            sk = np.sqrt(1/(len(xd)-2) * (Dyy/Dxx - a**2))


            inds = np.where( z < 861)
            Dose_ = data[i_x, i_y, :][inds]
            Dose_0 = Dose_[-1]
            #print('Dose inner wall ', Dose_0)

            a_min = a + np.abs(1*sk)
            Thickness = -(np.log(Dose_0) - np.log(Dose_desired))/a_min


            try:
                Thickness = float(Thickness)
                W[i_x, i_y] = Thickness /100
                print('Wall thickness: %s, decay parameter: %s +- %s' % (round(Thickness), a * 100, np.abs(sk * 2) * 100))
                lambda_coeff.append(a_min)
            except Exception:
                print(i_x, i_y)
            #else:
                #W[i_x, i_y] = 2.3
                #print('Normalno: ', i_x, i_y)


#plt.imshow(W.T)
# for seaborn
W = W.T
W = np.flip(W,0)


import seaborn
import seaborn as sns
import pandas as pd

dd = data[:,:,-1].T
dd = np.flip(dd, 0)
df = pd.DataFrame(dd)
plt.figure()
ax = sns.heatmap(W, annot=True, yticklabels=np.round(np.flip(y)), xticklabels=np.round(x), cbar_kws={"label": "Required wall thickness, m"})
ax.figure.axes[-1].yaxis.label.set_size(16)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.xaxis.label.set_size(18)
ax.yaxis.label.set_size(18)
#plt.xticks(x)
#plt.yticks(y)

ax = plt.figure()
ax = sns.heatmap(dd*1.0E+6, yticklabels=np.round(np.flip(y)), xticklabels=np.round(x),
                 cbar_kws={"label": " \u03BCSv/h"})
ax.figure.axes[-1].yaxis.label.set_size(16)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.xaxis.label.set_size(18)
ax.yaxis.label.set_size(18)
#ax.set_yticks(y)
#sns.heatmap(dd, annot=False, cbar_kws={"label": " \u03BCSv/h"})


print('Wall thickness: ', (W))
print('Lambda koeff.: ', np.max(lambda_coeff), np.min(lambda_coeff))

#plt.semilogy(xd, yd) #/np.max(yd))

#plt.semilogy(xd, yd)
#plt.semilogy(xd, yd_a)

#plt.plot(xd, a + b*xd)

#print(yd/np.max(yd), yd_a)
#plt.show()
"""

##################################################
#
# Residual doses
#
##################################################


fn = "simple_vault_ns_concr_local_40.bnn.lis"
fn = "simple_vault_ns_40.bnn.lis"

lines = ascii2lines(fn=fn)
usrbin = USRBIN(lines)
usrbin.get_bins()

print(usrbin.bins)
#print(usrbin.errors)



from matplotlib import ticker, cm
import matplotlib.colors as colors
from matplotlib.colors import LogNorm
import matplotlib.patches as patches


data_ = get_usrbins(fn)

for index in range(5):
    data = data_[index].data[:, 4, :] # Y = 0
    data = data +  np.flip(data, 1)
    print(data.shape)
    
    # Dose: Sv/hour
    data = data*3600*1.0E-12

    bins = data_[4].bins
    x = np.linspace(bins[0][0], bins[0][1], bins[0][2])
    y = np.linspace(bins[1][0], bins[1][1], bins[1][2])
    z = np.linspace(bins[2][0], bins[2][1], bins[2][2])

    xx, zz = np.meshgrid(z, x)

    #print(np.min(data))
    fig, ax = plt.subplots()
    #plt.imshow(np.log10(data))
    #cs = plt.contourf(xx, zz, np.log10(data), 100)
    levels_ = []
    for i in range(0, 10):
        levels_.append(1.0E-7 * 10 ** i)
        levels_.append(5.0E-7 * 10 ** i)
    levels_ = np.array(levels_)*1
    #levels_ = [5.0E-6, 5.0E-5, 5.0E-4]
    #cs =plt.contourf(xx, zz, data, 500, levels=levels_, cmap=plt.cm.coolwarm, norm=LogNorm())
    cs  = plt.contourf(xx, zz, data, 500, cmap=plt.cm.jet, norm=LogNorm(), levels=levels_)
    cbar = plt.colorbar()
    cbar.ax.set_ylabel('Sv/h')
    cs2 = plt.contour(cs, levels=[5.0E-5], colors='white', linewidth=4)
    ax.clabel(cs2, fmt='%2.2e', colors='w', fontsize=18)
    cs2 = plt.contour(cs, levels=[1.0E-4], colors='gray',  linewidth=4)
    ax.clabel(cs2, fmt='%2.2e', colors='gray', fontsize=18)
    #cs1 =plt.contourf(xx, zz, data, 500, cmap=plt.cm.coolwarm, norm=LogNorm())
    #norm=colors.LogNorm(vmin=5.0E-5/1000, vmax=5.0E-5*1000 ))
    #ax.set_yticks(x)
    #ax.set_xticks(z)
    plt.xlabel('Z, cm')
    plt.ylabel('X, cm')

    rect = patches.Rectangle((-861,-203),861*2, 203*2,linewidth=2,edgecolor='black',facecolor='none')
    ax.add_patch(rect)

    #print(np.max(data), np.min(data))
    plt.savefig(fn + '_' + str(index) +'.jpg', figsize=(27, 9), dpi=180,)
    


plt.show()

#print(np.max(data_[0].data) / np.max(data_[0].data),
#      np.max(data_[1].data) / np.max(data_[0].data),
#      np.max(data_[2].data) / np.max(data_[0].data),
#      np.max(data_[3].data) / np.max(data_[0].data),
#      np.max(data_[4].data) / np.max(data_[0].data))

#print(data_[4].bins)

#!/usr/local/bin/python
#
# Copyright 2015 Realm Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, getopt
import numpy as np
import os.path
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

xkcdStyle = False # plot as Randall Munroe

datastores = ['sqlite', 'realm', 'ormlite', 'greendao', 'realmlowlevel', 'sugarorm', 'couchbase'] # names of the tested data stores (see MainActivity.java)
datasizes = []                                                                                    # NUMBER_OF_OBJECTS in MainActivity.java
tests = ['BatchWrite', 'SimpleWrite', 'SimpleQuery', 'FullScan', 'Sum', 'Count']                  # the benchmark (see TestDataStore.java)

# read the timer resolution
def readTimer(datasize):
    inFileName = str(datasize) + '/timer'
    values = [int(line.strip()) for line in open(inFileName)]
    return values

# read the raw data for a given test
def readRawValues(datasize, datastore, test):
    inFileName = str(datasize) + '/' + datastore + '_' + test + '.csv'
    return [int(line.strip()) for line in open(inFileName)]

# returns number of bogus timings and list of real timings
def readValues(datasize, datastore, test):
    values = sorted(readRawValues(datasize, datastore, test))
    timings = [x for x in values if x > 0] # remove bogus values
    return (len(values) - len(timings), timings)

# was a datastore benchmarked?
def datastoreBenchmarked(datasize, datastore):
    return os.path.exists(str(datasize) + '/' + datastore + '_Sum.csv')

def benchmark(datasize):
    x = []
    y = []
    c = []
    patches = []
    colors = ['green', 'blue', 'red']
    if xkcdStyle:
        plt.xkcd()
    plt.figure()
    plt.title('Data stores comparison')
    plt.ylabel('Operations/time')
    plt.tick_params(axis='both', which='both',
        bottom='off', top='off')

    n = 0
    for datastore in datastores:
        if datastoreBenchmarked(datasize, datastore):
            patches.append(mpatches.Patch(color=colors[n % len(tests)], label=datastore))
            n = n + 1

    for test in tests:
        n = 0
        for datastore in datastores:
            if datastoreBenchmarked(datasize, datastore):
                (_, values) = readValues(datasize, datastore, test)
                if len(values) == 0:
                    y.append(0)
                else:
                    if test == 'BatchWrite':
                        values[0] = values[0] / float(datasize)
                    y.append(1.0e9/values[0])
                x.append(test.replace('Simple', ''))
                c.append(colors[n % len(tests)])
                n = n + 1

    plt.legend(bbox_to_anchor=(1, 1),
        bbox_transform=plt.gcf().transFigure,
        handles=patches)
    t = [test.replace('Simple', '') for test in tests]
    rects = plt.bar(np.arange(len(y)), y, color=c)
    plt.xticks(np.arange(1, len(datastores)*len(tests), len(datastores)), t)
    outFileName = str(datasize) + '/timings.png'
    plt.savefig(outFileName)
    plt.close()

def validate(datasize):
    for test in tests:
        for datastore in datastores:
            if datastoreBenchmarked(datasize, datastore):
                pylab.figure()
                pylab.title(datastore + ':' + test)
                pylab.xlabel('Value')
                pylab.ylabel('Count')
                (_, values) = readValues(datasize, datastore, test)
                if len(values) > 1:
                    n, bins, patches = pylab.hist(values, 10, histtype='bar', label=datastore)
                    pylab.legend()
                    outFileName = str(datasize) + '/hist_' + datastore + '_' + test + '.png'
                    pylab.savefig(outFileName)
                else:
                    print('Cannot generate histogram for ' + datastore + ':' + test + ' for size ' + str(datasize))
                pylab.close()

def plotraw(datasize):
    timer_res = readTimer(datasize)[2] # 3rd line
    for test in tests:
        for datastore in datastores:
            if datastoreBenchmarked(datasize, datastore):
                if xkcdStyle:
                    plt.xkcd()
                plt.figure()
                plt.title(datastore + ':' + test)
                plt.xlabel('Iteration')
                plt.ylabel('time [ns]')
                values = readRawValues(datasize, datastore, test)
                if len(values) > 0:
                    plt.plot(values)
                    plt.axhline(timer_res, color='red')
                    plt.savefig(str(datasize) + '/raw_' + datastore + '_' + test + '.png')
                plt.close()

def analyze(datasize):
    print('Analyzing size,' + str(datasize))
    timer_res = readTimer(datasize)[2] # 3rd line
    print('Timer resolution,' + str(timer_res))
    print('Data store,Test,minimum,average,maximum,bogus,real')
    for datastore in datastores:
        if datastoreBenchmarked(datasize, datastore):
            for test in tests:
                (bogus, timings) = readValues(datasize, datastore, test)
                ops = []
                if test.endswith('Write'):
                    ops = [10e9*float(datasize)/float(t) for t in timings]
                else:
                    ops = [10e9/float(t) for t in timings]
                minimum = ops[-1]
                maximum = ops[0]
                average = sum(ops)/float(len(ops))
                row = [datastore, test, str(minimum), str(average), str(maximum), str(bogus), str(len(timings))]
                print ','.join(row)

def speedup(datasize):
    dstores = [s for s in datastores if s != 'sqlite']
    print('Data size = ', datasize)
    if xkcdStyle:
        plt.xkcd()
    plt.figure()
    plt.title(str(datasize) + ' rows/objects')
    plt.ylabel('Speed up')
    plt.xlabel('Test')
    x = []
    y = []
    colors = []
    for test in tests:
        (_, timings) = readValues(datasize, 'sqlite', test)
        sqlite = float(timings[0])
        patches = []
        for ds in dstores:
            if datastoreBenchmarked(datasize, ds):
                if ds == 'realm':
                    c = 'green'
                elif ds == 'realmlowlevel':
                    c = 'blue'
                else:
                    c = 'yellow'
                patches.append(mpatches.Patch(color=c, label=ds))
                (_, values) = readValues(datasize, ds, test)
                value = 0
                if len(values) > 0:
                    value = float(values[0])
                    speedup = 0.0
                    if value < sqlite:
                        speedup = sqlite / value
                    else:
                        speedup = -value / sqlite
                    colors.append(c)
                else:
                    speedup = 0
                    colors.append('red')
                x.append(test)
                y.append(speedup)
                print('  datastore = ', ds, ' test = ', test, ' spedup = ', speedup)
            plt.legend(bbox_to_anchor=(1, 1),
                bbox_transform=plt.gcf().transFigure,
                handles=patches)
            rects = plt.bar(np.arange(len(y)), y, color=colors)
            for rect in rects:
                height = rect.get_height()
                plt.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%2.2f'%float(height),
                    ha='center', va='bottom')
        plt.xticks(np.arange(1, len(dstores)*len(tests), len(dstores)), tests)
        outFileName = str(datasize) + '/speedup.png'
        plt.savefig(outFileName)
        plt.close()

def usage():
    print('dsb.py [-h] [-d <dir>] [-b] [-s] [-v] [-a] [-p] [-e <engine>] [-t test]')
    print(' -d <dir> : only analyze these directories')
    print(' -v       : validate')
    print(' -a       : analyze')
    print(' -s       : speed up graphs')
    print(' -e <engine>: only these engines')
    print(' -p       : plot raw data')
    print(' -x       : XKCD style graphs')
    print(' -t <test>: only these tests')
    print(' -h       : this message')

def main(argv):
    global datasizes
    global datastores
    global tests
    global xkcdStyle

    xkcdStyle = False

    datasizes = os.listdir('.')

    do_analyze = False
    do_validate = False
    do_speedup = False
    do_plotraw = False
    do_benchmark = False

    try:
        optlist, args = getopt.getopt(argv, 'h:d:bvsape:xt:')
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in optlist:
        if opt == '-d':
            arr = arg.split(',')
            if len(arr) == 1:
                datasizes = [arg]
            else:
                datasizes = arr
        elif opt == '-x':
            xkcdStyle = True
        elif opt == '-v':
            do_validate = True
        elif opt == '-a':
            do_analyze = True
        elif opt == '-s':
            do_speedup = True
        elif opt == '-p':
            do_plotraw = True
        elif opt == '-e':
            arr = arg.split(',')
            if len(arr) == 1:
                datastores = [arr]
            else:
                datastores = arr
        elif opt == '-t':
            arr = arg.split(',')
            if len(arr) == 1:
                tests = [arr]
            else:
                tests = arr
        elif opt == '-b':
            do_benchmark = True
        elif opt == '-h':
            usage()
            sys.exit(0)
        else:
            usage()
            sys.exit(2)

    if do_analyze:
        for datasize in datasizes:
            analyze(datasize)

    if do_validate:
        for datasize in datasizes:
            validate(datasize)

    if do_speedup:
        for datasize in datasizes:
            speedup(datasize)

    if do_plotraw:
        for datasize in datasizes:
            plotraw(datasize)

    if do_benchmark:
        for datasize in datasizes:
            benchmark(datasize)

if __name__ == '__main__':
    main(sys.argv[1:])

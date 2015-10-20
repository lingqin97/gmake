#!/usr/bin/env python2
from __future__ import print_function
import os
from glob import glob
import re
import Queue


class Node(object):
    def __init__(self, key):
        self.key = key
        self.color = 'w'
        self.__neighborsSet = set()

    def addneighbor(self, nbr):
        self.__neighborsSet.add(nbr)

    def neighbors(self):
        return list(self.__neighborsSet)


class Graph(object):
    def __init__(self):
        self.nodes = {}
        self.nodeNum = 0

    def __contains__(self, key):
        return key in self.nodes

    def __iter__(self):
        return iter(self.nodes.values())

    def addnode(self, key):
        self.nodeNum += 1
        newnode = Node(key)
        self.nodes[key] = newnode
        return newnode

    def getnode(self, key):
        if key in self.nodes:
            return self.nodes[key]

    def setwhite(self):
        for key in self.nodes:
            self.nodes[key].color = 'w'

    def addedge(self, key1, key2):
        if key1 not in self.nodes:
            self.addnode(key1)
        if key2 not in self.nodes:
            self.addnode(key2)

        self.nodes[key1].addneighbor(self.nodes[key2])


def bfs(graph, startkey):
    graph.setwhite()
    startnode = graph.nodes[startkey]
    nodequeue = Queue.Queue()
    startnode.color = 'b'
    nodequeue.put(startnode)
    retlist = []
    while nodequeue.qsize() > 0:
        currentnode = nodequeue.get()
        retlist.append(currentnode.key)
        for nbr in currentnode.neighbors():
            if nbr.color == 'w':
                nbr.color = 'b'
                nodequeue.put(nbr)

    return retlist


def src2obj(srcfile):
    srcsplit = list(os.path.splitext(srcfile))
    srcsplit[-1] = '.o'
    return ''.join(srcsplit)


class Makefile(object):
    @staticmethod
    def help():
        print("functions: \n"
              "debug(bool)\n"
              "cxx11() or cxx0x()\n"
              "libs(list)\n"
              "rdynamic()\n"
              "ldflags(string)"
              "incpaths(list)\n"
              "out(string)       the dir of object files\n"
              "complie(string)   default g++\n"
              "headers(list)     must called before srcs(list)\n"
              "srcs(list)\n"
              "target(string)    string is None if build as shared lib\n"
              "printf()\n")

    def __init__(self):
        self.__graph = Graph()
        self.__srcList = []
        self.__headerdirs = []
        self.__headList = []
        self.__filesList = []
        self.__cxxflag = 'CXXFLAGS = -Wall -Wno-unused-local-typedefs -O2'
        self.__objs = 'objs = '
        self.__ldflag = ''
        self.__CXX = 'CXX = g++\n'
        self.__AR = 'AR = ar\n'

    def debug(self, enable):
        if enable:
            self.__cxxflag += ' -g'

        return self

    def cxx11(self):
        self.__cxxflag += ' -std=c++11'
        return self

    def cxx0x(self):
        self.__cxxflag += ' -std=c++0x'
        return self

    def libs(self, libs):
        for lib in libs:
            self.__ldflag += ' -l%s' % lib

        return self

    def rdynamic(self):
        self.__ldflag += ' -rdynamic'
        return self

    def ldflags(self, flags):
        self.__ldflag += " " + flags
        return self

    def incpaths(self, incs):
        for inc in incs:
            self.__cxxflag += ' -I%s' % inc

        return self

    def out(self, outdir):
        self.__outdir = outdir
        return self

    def complie(self, name):
        self.__CXX = 'CXX = ' + name + '\n'
        return self

    def srcs(self, srcdirs):
        if not self.__headList:
            raise "no headList"

        for srcdir in srcdirs:
            regex = ''
            if srcdir:
                regex = srcdir + '/*.cpp'
            else:
                regex = '*.cpp'
            self.__srcList += [filename for filename in glob(regex)]

        for src in self.__srcList:
            self.__objs += os.path.join(self.__outdir, os.path.basename(src)
                                        + '.o') + ' '

        self.__objs += '\n'
        map(self.__graph.addnode, self.__srcList)
        map(self.__findheaders, self.__srcList)
        return self

    def headers(self, headerdirs):
        self.__headerdirs = headerdirs
        for headerdir in headerdirs:
            regex1 = ''
            regex2 = ''
            if headerdir:
                regex1 = headerdir + '/*.h'
                regex2 = headerdir + '/*/*.h'
            else:
                regex1 = '*.h'
                regex2 = '*/*.h'
            self.__headList += [filename for filename in glob(regex1)]
            self.__headList += [filename for filename in glob(regex2)]

        map(self.__graph.addnode, self.__headList)
        map(self.__findheaders, self.__headList)
        return self

    def target(self, name, boutlib=False, bstaticlib=False):
        self.__tg = ''
        if not boutlib:
            self.__tg += name + ': ' + self.__outdir + \
                        ' $(objs)\n\t$(CXX) -o ' + name + ' $(objs)' + \
                        self.__ldflag + '\n\n'

            return self

        if bstaticlib:
            self.__tg += name + ': ' + self.__outdir + \
                        ' $(objs)\n\t$(AR) crs ' + name + \
                        ' $(objs)' + self.__ldflag + '\n\n'
        else:
            self.__tg += name + ': ' + self.__outdir + \
                        ' $(objs)\n\t$(CXX) -fPIC -shared -o ' + name + \
                        ' $(objs)' + self.__ldflag + '\n\n'

        return self

    def printf(self):
        xx = ''
        for src in self.__srcList:
            obj = os.path.join(self.__outdir, os.path.basename(src) + '.o')
            xx += obj + ': ' + ' '.join(bfs(self.__graph, src)) + \
                '\n' + '\t$(CXX) $(CXXFLAGS) -c ' + src + ' -o ' + obj + '\n\n'

        cout = self.__objs + self.__CXX + self.__AR + self.__cxxflag + '\n\n' \
             + self.__tg + self.__outdir + ':\n\tmkdir ' + self.__outdir + \
               '\n\n' + xx

        print(cout)

    def __findheaders(self, src, count=2500):
        fd = open(src, 'r')  # TODO: encoding
        code = fd.read(count)
        fd.close()
        headers = re.findall('(?<=")[\w/]+\.h', code)
        # print src, headers
        for header in headers:
            for hdir in self.__headerdirs:
                nheader = os.path.join(hdir, header)
                if (nheader in self.__headList):
                    self.__graph.addedge(src, nheader)


if __name__ == "__main__":
    Makefile().debug(False).cxx11().sharedlib('magsdk')\
            .libs(['pthread', 'ikkcpr', 'magh264'])\
            .out('outlib').headers([''])\
            .srcs(['']).target().printf()

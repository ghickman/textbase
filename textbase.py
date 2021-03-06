'''
textbase - A Python library to manipulate Inmagic/DBText style data files

The main utitlity class is TextBase.
It can be initialised with an open file, or a string buffer, named sourcefile.
Sourcefile is iterated over, splitting the contents into chunks.
Each chunk is parsed and added to an internal buffer list.
The internal buffer contains a dict for each record. Each entry in the dict
is keyed on the DBText record fieldname, the entry itself is a list of the values.

The TextBase object can be used as a generator to iterate over the contents,
or the Textbase object can be index-addressed like a list.

Example Usage:
--------------

import textbase
t = textbase.TextBase(somebuf)

print len(t)

for x in t[10:20]:
    print x.keys()

print t[0]


If you do not want the records parsed into Python dictionaries and just want 
to muck about with the records as text blobs, initialise like this:
  t = textbase.TextBase(somebuf, parse=False)

Please send me feedback if this is useful for you, or suggestions etc.
Author: Etienne Posthumus
Mail: ep@epoz.org
Dev started: 17 November 2004
'''

__version__ = "0.10"
__date__ = '20180726'


import io
from collections import OrderedDict


def parse(filename):
    # Files read as binary, we do explicit decoding at the boundary,
    return TextBase(io.open(filename, 'rb'))


class TextBase:
    def __init__(self, sourcefile=None, separator=b'$', parse=True, keep_original=False, encoding='utf8'):
        self.separator = separator
        self.__entries__ = []
        self.keep_original = keep_original
        self.encoding = encoding

        if isinstance(sourcefile, io.IOBase):
            self.sourcefile = sourcefile
        else:
            self.sourcefile = io.BytesIO(sourcefile)

        if parse:
            self.process = self.parse
        else:
            self.process = self.dontparse

        # check for unicode Byte Order Mark (BOM)
        BOMcheck = self.sourcefile.read(3)
        if BOMcheck != '\xef\xbb\xbf':
            self.sourcefile.seek(0)

        self.split()

    def dontparse(self, chunk):
        self.__entries__.append(''.join(chunk))

    def parse(self, chunk):
        lastField = ''
        datadict = OrderedDict()
        for x in chunk:
            if x[0] == '#':  # skip comments
                continue

            # find where the first space character is
            spacepos = x.find(' ')

            # skip line if there are no spaces
            if spacepos == -1:
                continue

            # Get key value
            if x[0] != ';' and spacepos > 0:
                lastField = x[0:spacepos]
                if lastField.endswith(':'):
                    lastField = lastField[:-1]

            data = x[spacepos:].strip()

            # Special case multi-line values
            # The string <space><newline> is part of a multiline string but the
            # way we pull data out typically strips newlines so fix that here.
            if x[spacepos:] == " \n":
                data = "\n\n"

            if lastField in datadict.keys():
                if spacepos == 0:
                    datadict[lastField][-1] = datadict[lastField][-1] + ' ' + data
                else:
                    datadict[lastField].append(data)
            else:
                datadict[lastField] = [data]

        if self.keep_original:
            datadict['__original__'] = (''.join(chunk))

        if datadict:
            self.__entries__.append(datadict)

    def split(self):
        chunk = []
        for line in self.sourcefile:
            if line.strip() == self.separator:
                if chunk:
                    self.process(chunk)
                    chunk = []
            else:
                # this is the boundary that an actual read line gets "into" the system
                # we will do an explicit decoding here.
                chunk.append(line.decode(self.encoding))
        if chunk:
            self.process(chunk)

    def dump(self, filename):
        with io.open(filename, 'wb') as F:
            for x in self.__entries__:
                for k, v in x.items():
                    F.write(b'\n%s ' % k.encode('utf8'))
                    tmp = u'\n; '.join(v)
                    F.write(tmp.encode('utf8'))
                F.write(b'\n$')

    def __getitem__(self, key):
        return self.__entries__[key]

    def __iter__(self):
        return iter(self.__entries__)

    def __len__(self):
        return len(self.__entries__)

#!/usr/bin/env python

"""
Example usage:

parser.py -i war_and_peace.txt -o output.pkl

"""

import argparse
import fileinput
import logging
import pickle
import sys
import string
from utils import TokenMap, Arc
from collections import deque

logging.getLogger(__name__)

PROGRAM_NAME = 'parser'
PROGRAM_VERSION = '1.0'

class NGramStore:
    def __init__(self):
        self._ngrams = dict()

    def __len__(self):
        return len(self._ngrams)

    def write(self, key):
        if (key in self._ngrams):
            self._ngrams[key] += 1
        else:
            self._ngrams[key] = 1

    def read(self):
        for key, value in self._ngrams.iteritems():
            yield (key, value)

class TextParser:
    _inputfile = ''

    def __init__(self, inputfile, n, quiet=False):
        self._inputfile = inputfile
        assert self._inputfile, "Input file must be provided."
        self._ngramsize = n
        assert self._ngramsize > 0, "N must be positive."

        if self._inputfile == '-':
            logging.info("Parse {}-ngrams from stdin.".format(self._ngramsize))
        else:
            logging.info("Parse {}-grams from file '{}'.".format(self._ngramsize, self._inputfile))

        self._quiet = quiet
        self._store = NGramStore()

        self._storeNGrams()

    def _ngramGenerator(self):
        ngram = deque()
        for line in fileinput.input(self._inputfile):
            for word in line.split():
                word = word.strip(string.punctuation).lower()
                word = "".join(filter(lambda x : x in string.printable, word))
                inputToks = " ".join(ngram)
                outputTok = word
                yield inputToks, outputTok
                ngram.append(outputTok)
                if (len(ngram) > self._ngramsize):
                    ngram.popleft()

    def _storeNGrams(self):
        ngramsparsed = 0
        for inputToks, outputTok in self._ngramGenerator():
            self._store.write((inputToks, outputTok))
            ngramsparsed += 1
            self._printCount(ngramsparsed)
        self._endCountPrinting(ngramsparsed)

    def _printCount(self, ngramcount):
        """
        Overwrite the line and reprint the message to prevent stdout spam.
        """
        if not self._quiet and ngramcount % 1000 == 0:
            sys.stdout.write('\r{}-grams collected: {}K '.format(self._ngramsize, ngramcount/1000))
            sys.stdout.flush()

    def _endCountPrinting(self, ngramcount):
        """
        Write out newline to move past the progress printer and log the total
        number of ngrams collected.
        """
        if not self._quiet:
            sys.stdout.write('\n')
            sys.stdout.flush()
        logging.info("Collected {} {}-grams.".format(ngramcount, self._ngramsize))

    def write(self, outputfile):
        tokMap = TokenMap(self._store.read())
        pickle.dump(tokMap, outputfile)

    def _printProgress(self, progress):
        """
        Overwrite the line and reprint the message to prevent stdout spam.
        """
        if not self._quiet:
            sys.stdout.write('\rWriting store to CSV: [{0:50s}] {1:.2f}% '.format('#' * int(progress * 50.0), progress * 100.0))
            sys.stdout.flush()

    def _endProgressPrinting(self, nummetrics):
        """
        Write out newline to move past the progress printer and log the total
        number of metrics collected.
        """
        if not self._quiet:
            sys.stdout.write('\n')
            sys.stdout.flush()
        logging.info("Wrote metrics for {} requests to CSV.".format(nummetrics))


def main(argv):
    parser = argparse.ArgumentParser(prog='{}'.format(PROGRAM_NAME), description='Parse text corpra into n-gram model.')
    parser.add_argument('-v', '--version', action='version', version='{} {}'.format(PROGRAM_NAME, PROGRAM_VERSION))
    parser.add_argument('-i', '--infile', action='store', type=str, required=True, help='the input file, set to \'-\' for stdin.')
    parser.add_argument('-o', '--outfile', action='store', type=argparse.FileType('wb'), required=True, help='the output destination')
    parser.add_argument('-n', '--ngramsize', action='store', type=int, help='the ngram size to parse', default=2)
    parser.add_argument('-l', '--loglevel', action='store', type=str, help='log level to use', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    parser = TextParser(args.infile, args.ngramsize)
    parser.write(args.outfile)

if __name__ == "__main__":
    main(sys.argv[1:])

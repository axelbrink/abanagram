from _tracemalloc import stop

__author__ = 'Axel Brink'

# Documentation on threading producer/consumer:
# See http://www.bogotobogo.com/python/Multithread/python_multithreading_Synchronization_Producer_Consumer_using_Queue.php

import os.path, re, time, threading, queue
from collections import Counter

MAXNUMWORDS = 2

WORDSFILES = [os.path.join('OpenTaal-woordenlijsten', 'basiswoorden-gekeurd.txt'),
              os.path.join('OpenTaal-woordenlijsten', 'flexies-ongekeurd.txt')]
              #os.path.join('OpenTaal-woordenlijsten', 'basiswoorden-ongekeurd.txt')

class WordBag:
    def __init__(self, text):
        self.text = text.strip()
        self.bag = Counter(re.sub('[^a-zA-Z]+', '', text).lower())  # keep only lowercase alpha characters
        # TODO: Letters met accenten converteren

    def __str__(self):
        return self.text

    def __repr__(self):
        return "WordBag(%s)" % self.text

    def contains(self, other):
        """
        :param other: WordBag
        :return: boolean
        """
        return all(self.bag[k] >= v for k, v in other.bag.items())

    def equals(self, other):
        """
        :param other: WordBag
        :return: boolean
        """
        return self.bag == other.bag

    def __sub__(self, other):
        """ Subtract. The text field remains empty. """
        wb = WordBag('')
        wb.bag = self.bag - other.bag
        return wb


class AnagramProducerThread(threading.Thread):

    def __init__(self, wordsfiles, commandqueue, result_callback, status_callback):
        '''
        Thread for producing results. Receives search commands via a queue
        and produces results and status updates by calling callback functions.
        :param wordsfiles: list of strings (file names)
        :param commandqueue: queue.Queue containing one or more search commands
        :param result_callback: function(string) to call for each result
        :param status_callback: function(string) to call for status updates
        '''
        assert type(wordsfiles) is list
        assert callable(result_callback)
        assert callable(status_callback)
        #status_callback("Initializing AnagramProducerThread.")
        super(AnagramProducerThread, self).__init__()

        self.result_callback = result_callback
        self.status_callback = status_callback
        self.commandqueue = commandqueue
        self.wordsfiles = wordsfiles
        self.allwords = []

    def readwordlist(self, filename):
        #wordlist = []
        self.status_callback("Reading input file %s ..." % filename)
        starttime = time.clock()
        # The word should contain at least two consecutive normal characters.
        excludepattern = re.compile(r"^[a-zA-Z\ '\-]*[a-zA-Z\ ]{2,}[a-zA-Z\ '\-\r\n]*$")  # re.compile(r'[^a-zA-Z\'\ \n\r]')
        #excludepattern = re.compile(r"#^[A-Za-zÀ-ÿ\ '\-]*[A-Za-zÀ-ÿ\ ]{2,}[A-Za-zÀ-ÿ\ '\-\r\n]*$")
        f = open(filename, 'r')
        self.allwords.extend([WordBag(text) for text in f if excludepattern.search(text)])
        #for line in f.xreadlines():
        #    wb = WordBag(line)
        #    if
        # Nog uitfilteren:
        # * woorden die na het strippen bestaan uit 1 teken (excl. 'u')
        # * woorden die een cijfer bevatten
        # * woorden die bestaan uit hoofdletters
        f.close()
        print("  (took %.1f sec)" % (time.clock() - starttime))

    @staticmethod
    def filterwordlist_contains(wordlist, queryword):
        return [word for word in wordlist if queryword.contains(word)]

    @staticmethod
    def filterwordlist_equals(wordlist, queryword):
        return [word for word in wordlist if queryword.equals(word)]

    def add_result(self, allresults, result):
        """
        :param allresults: list of results
        :param result:     set of WordBags
        :return: None
        """

        if not result in allresults:
            allresults.append(result)
            resulttext = ' '.join([w.text for w in result])
            #if self.result_callback:
            self.result_callback(resulttext)
            #else:
            #    print("Result: '%s'" % resulttext)

    def search(self, wordlist, matchedwords, queryword, allresults, maxnumwords):
        """

        :param wordlist: list of WordBags that is the currently applicable universe of words
        :param matchedwords: list of WordBags that has already been matched in the initial query
        :param queryword: current query word
        :param allresults: set of results (a result is a set of WordBags)
        """
        querylen = sum(queryword.bag.values())
        #print "Search: ", matchedwords, queryword.bag, querylen


        if len(matchedwords) >= maxnumwords - 1:
            # Only look for a complete match
            filteredwordlist = self.filterwordlist_equals(wordlist, queryword)
            for word in filteredwordlist:
                self.add_result(allresults, set(matchedwords + [word]))
        else:
            # Shorter words are OK
            filteredwordlist = self.filterwordlist_contains(wordlist, queryword)
            #print "list size reduced from %i to %i" % (len(wordlist), len(filteredwordlist))
            for word in filteredwordlist:
                if len(word.text) == querylen:
                    self.add_result(allresults, set(matchedwords + [word]))
                else:
                    self.search(filteredwordlist, list(matchedwords) + [word], queryword - word, allresults, maxnumwords)

    def _start_search(self, query, maxnumwords):
        self.status_callback("Starting search: %s (max %i words)" % (query, maxnumwords))
        starttime = time.clock()
        queryword = WordBag(query)
        self.allresults = []
        self.search(self.allwords, [], queryword, self.allresults, maxnumwords)
        self.status_callback("Done searching (took %.1f sec)" % (time.clock() - starttime))

    def run(self):
        self.status_callback("AnagramProducerThread starting")
        for fname in self.wordsfiles:
            self.readwordlist(fname)
        #print ("TEMP %i words read from, ready to start." % len(self.allwords))
        self.status_callback("%i words read, waiting for command." % len(self.allwords))

        stop_received = False
        while not stop_received:
            command, querytext, maxnumwords = self.commandqueue.get()
            self.status_callback("Command received: %s" % command)
            if command == "SEARCH":
                self._start_search(querytext, maxnumwords)
            elif command == "STOP":
                stop_received = True
        self.status_callback("AnagramProducerThread exiting.")
        return


class AnagramFinder:
    def __init__ (self, result_callback, status_callback):
        """
        :param callback: function to call for each word
        :param wordsfiles: list of file names that contain words
        """
        #assert type(wordsfiles) is list
        assert callable(result_callback)
        assert callable(status_callback)
        #if not callable(callback):
        #self.result_callback = result_callback
        self.status_callback = status_callback
        #status_callback("Initializing AnagramFinder")
        self.commandqueue = queue.Queue(maxsize=10)
        self.producer = AnagramProducerThread(WORDSFILES, self.commandqueue, result_callback, status_callback)
        self.producer.start()
        #status_callback("AnagramFinder ready.")

    def search(self, querytext, maxnumwords):
        self.commandqueue.put(("SEARCH", querytext, maxnumwords))

    def stop(self):
        self.commandqueue.put(("STOP", None, None))
        self.producer.join()
        self.status_callback("Worker stopped.")


def print_result(text):
    print("RESULT: %s" % text)

def print_status(text):
    print("STATUS UPDATE: %s" % text)

if __name__ == "__main__":
    print("Abanagram by Axel Brink, November 2017")
    print("MAXNUMWORDS = %i" % MAXNUMWORDS)

    af = AnagramFinder(print_result, print_status)

    query = input("Input text (leave empty to exit): ")
    while query != "" and query != "exit":
        af.search(query, MAXNUMWORDS)
        query = input("Input text: ")
    af.stop()

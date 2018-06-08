#!/usr/bin/python
import sys
from urllib2 import urlopen


class Scraper:

    def __init__(self, html):
        if (html.startswith("http://")):
            f = urlopen(html)
            self.url = f.geturl()
        else:
            f = open(html, 'r')
        self.data = f.read()
        # sys.stderr.write("scraped %d bytes\n" % len(self.data))
        self.pos = 0
        f.close()

    def move_to(self, key):
        p = self.data.find(key, self.pos)
        if (p > -1):
            dist = p - self.pos
            self.pos = p + len(key)
            return dist
        else:
            return -1

    def moveBack(self, key):
        p = self.data.rfind(key, 0, self.pos)
        if (p > -1):
            dist = self.pos - p
            self.pos = p + len(key)
            return dist
        else:
            return -1

    def scout(self, key):
        p = self.data.find(key, self.pos)
        if (p > -1):
            return p
        else:
            return -1

    def comesBefore(self, key, other):
        posKey = self.scout(key)
        posOther = self.scout(other)
        if (posKey >= 0):
            if (posOther == -1):
                return True
            else:
                return posKey < posOther
        else:
            return False

    def comesFirst(self, choices):
        firstChoice = None
        firstPos = sys.maxint
        for choice in choices:
            pos = self.scout(choice)
            if (pos > -1) and (pos < firstPos):
                firstChoice = choice
                firstPos = pos
        return firstChoice

    def peek(self, rng):
        start = max(0, self.pos - rng)
        end = min(len(self.data), self.pos + rng)
        return str(self.pos) + ": " + self.data[start:self.pos] + "|" + self.data[self.pos:end]

    # pull functions throw an exception if we don't find the key(s)

    def pullUntil(self, key):
        pEnd = self.data.index(key, self.pos)
        good = self.data[self.pos:pEnd]
        self.pos = pEnd + len(key)
        return good

    def pull_from_to(self, keyStart, keyEnd):
        self.pos = self.data.index(keyStart, self.pos) + len(keyStart)
        return self.pullUntil(keyEnd)

    def pullLine(self):  # returns the rest of the current line (getting rid of the newline)
        return self.pullUntil("\n")


# misc conversion funcs

dateMonths = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
              "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}


# "Thursday, Dec 13" -> "20071213"
def parseDateYahooShort(dateStr):
    # sys.stderr.write("parsing '%s'\n" % dateStr)
    dateElts = dateStr.split()
    dateMonth = dateMonths[dateElts[1]]
    dateDay = dateElts[2]
    if (len(dateDay) < 2):
        dateDay = "0" + dateDay
    if (int(dateMonth) < 9):
        dateYear = "2008"
    else:
        dateYear = "2007"
    return dateYear + dateMonth + dateDay


# "Sundy December 9, 2007" -> 20071209
def parseDateYahooLong(date):
    sys.stderr.write("parsing '%s'\n" % date)
    dayofweek, month, day, year = date.strip().split()
    month = dateMonths[month[:3]]
    if (len(day) < 3):
        day = "0" + day[:1]  # rid the comma
    else:
        day = day[:2]
    return year + month + day


# "1:00 pm ET" -> 1300
# "1:00pm ET" -> 1300
def parseTimeYahoo(time):
    elts = time.split()
    if (len(elts) == 3):
        h, m = elts[0].split(":")
        ap = elts[1]
    else:
        h, m = elts[0][:-2].split(":")
        ap = elts[0][-2:]
    if (ap == "pm"):
        h = str(int(h) + 12)
    elif (int(h) < 10):
        h = "0" + h
    return h + m

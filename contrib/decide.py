# encoding: utf-8

import re
from time import strftime

def asciicount(text):
    return sum(map(ord, text))

DECIDERE = re.compile(r'(".+?"|(?<!").+?(?!"))(?:\s+|$)') 

@register('decide')
def handler(event):
    args = event.content
    if len(args) == 0:
        return
    # num = asciicount("*!*" + event.source.ident)
    num = asciicount("*!*")
    decide_result = regexdecide(args, num)    
    event.reply(u"Du solltest dich %s entscheiden." % decide_result)

def regexdecide(text, num):
    matchlist = sorted(DECIDERE.findall(text))
    c = asciicount(text) + asciicount(strftime("%d/%m/%Y"))
    if len(matchlist) > 1:
        return u"für " + matchlist[(c + (num % 100)) % len(matchlist)]
    else:
        if ((c % (num % 100)) % 2 + 1) == 1:
            return u"für %s" % matchlist[0]
        else:
            return u"gegen %s" % matchlist[0]

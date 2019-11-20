#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
#

'''
Deletes a user in Gogs through the API
'''

import sys
import gogs
import config
import types

api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password)

import types
def var_dump(obj, depth=4, l=""):
    #fall back to repr
    if depth<0: return repr(obj)
    #expand/recurse dict
    if isinstance(obj, dict):
        name = ""
        objdict = obj
    else:
        #if basic type, or list thereof, just print
        canprint=lambda o:isinstance(o, (int, float, str, unicode, bool, types.NoneType, types.LambdaType))
        try:
            if canprint(obj) or sum(not canprint(o) for o in obj) == 0: return repr(obj)
        except TypeError, e:
            pass
        #try to iterate as if obj were a list
        try:
            return "[\n" + "\n".join(l + var_dump(k, depth=depth-1, l=l+"  ") + "," for k in obj) + "\n" + l + "]"
        except TypeError, e:
            #else, expand/recurse object attribs
            name = (hasattr(obj, '__class__') and obj.__class__.__name__ or type(obj).__name__)
            objdict = {}
            for a in dir(obj):
                if a[:2] != "__" and (not hasattr(obj, a) or not hasattr(getattr(obj, a), '__call__')):
                    try: objdict[a] = getattr(obj, a)
                    except Exception, e: objdict[a] = str(e)
    return name + "{\n" + "\n".join(l + repr(k) + ": " + var_dump(v, depth=depth-1, l=l+"  ") + "," for k, v in objdict.iteritems()) + "\n" + l + "}"

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: show_user.py <username>"
        exit(1)

    user = gogs.GogsUser(sys.argv[1], config.new_user_password)
    api.populateUser(user)
    print var_dump(user)

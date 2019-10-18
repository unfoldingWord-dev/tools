import re

text = "This is my text [[rc://fr/obs-tn/help/04/09]] this here [[rc://fr/obs-tn/help/19/12]] end"
data = {'rc://fr/obs-tn/help/04/09': {'title': '04-09', 'link': '#04-09'}, 'rc://fr/obs-tn/help/19/12': {'title': '19-12', 'link':'#19-12'}}
repl1 = {}
repl2 = {}
for rc, info in data.iteritems():
    pattern = '[[{0}]]'.format(rc)
    replace = '<a href="{0}">{1}</a>'.format(info['link'], info['title'])
    repl1[pattern] = replace
    repl2[rc] = info['link']

def rep(m, repl):
    key = re.sub(r'rc://[^/]+', 'rc://[^/]+', m.group())
    print(repl)
    print("HERE: "+m.group()+" "+key)
    return repl[key]

#print(r'\b('+'|'.join(repl1.keys())+r')\b')
text = re.sub('|'.join(map(re.escape, repl1.keys())), lambda m: repl1[m.group()], text, flags=re.IGNORECASE)
print(text)


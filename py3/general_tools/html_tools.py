import re
from bs4 import BeautifulSoup

def get_first_header(html):
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.find(re.compile(r'^h\d'))

    lines = text.split('\n')
    if len(lines):
        for line in lines:
            if re.match(r'<h1>', line):
                return re.sub(r'<h1>(.*?)</h1>', r'\1', line)
        return lines[0]
    return "NO TITLE"


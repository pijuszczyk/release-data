import datetime
import re
from bs4 import BeautifulSoup
from common import endoflife

URLS = [
    "https://support.apple.com/en-us/HT201222",  # latest
    "https://support.apple.com/kb/HT213078",  # 2018-2019
    "https://support.apple.com/kb/HT213077",  # 2016-2017
    "https://support.apple.com/kb/HT209441",  # 2015
    "https://support.apple.com/kb/HT205762",  # 2014
    "https://support.apple.com/kb/HT205759",  # 2013
    "https://support.apple.com/kb/HT204611",  # 2011 to 2012
    "https://support.apple.com/kb/HT5165",  # 2010
    "https://support.apple.com/kb/HT4218",  # 2008-2009
    "https://support.apple.com/kb/HT1263",  # 2005-2007
]

# If you are changing these, please use
# https://gist.githubusercontent.com/captn3m0/e7cb1f4fc3c07a5da0296ebda2b33e15/raw/5747e42ad611ec9ffdb7a2d1c0e3946bb87ab6d7/apple.txt
# as your corpus to validate your changes
CONFIG = {
    "macos": [
        # This covers Sierra and beyond
        r"^macOS[\D]+(?P<version>\d+(?:\.\d+)*)",
        # This covers Mavericks - El Capitan
        r"OS\s+X\s[\w\s]+\sv?(?P<version>\d+(?:\.\d+)+)",
        # This covers even older versions (OS X)
        r"^Mac\s+OS\s+X\s[\w\s]+\sv?(?P<version>\d{2}(?:\.\d+)+)",
    ],
    "ios": [
        r"iOS\s+(?P<version>\d+)",
        r"iOS\s+(?P<version>\d+(?:)(?:\.\d+)+)",
        r"iPhone\s+v?(?P<version>\d+(?:)(?:\.\d+)+)",
    ],
    "ipados": [
        r"iPadOS\s+(?P<version>\d+)",
        r"iPadOS\s+(?P<version>\d+(?:)(?:\.\d+)+)"
    ],
    "watchos": [
        r"watchOS\s+(?P<version>\d+)",
        r"watchOS\s+(?P<version>\d+(?:)(?:\.\d+)+)"
    ],
}


def parse_date(s):
    d, m, y = s.strip().split(" ")
    m = m[0:3].lower()
    return datetime.datetime.strptime(f"{d} {m} {y}", "%d %b %Y")


# Only update the date if we are adding first time or if the date is lower
def handle_version(key, version, date_text, releases):
    try:
        date = parse_date(date_text)
        date_fmt = date.strftime("%Y-%m-%d")

        if version not in releases[key]:
            releases[key][version] = date
            print(f"{key}-{version}: {date_fmt}")
        elif releases[key][version] > date:
            releases[key][version] = date
            print(f"{key}-{version}: {date_fmt} [UPDATED]")
        else:
            print(f"{key}-{version}: {date_fmt} [IGNORED]")

    except ValueError:
        print(f"{key}-{version}: Failed to parse {date_text} for {version}")


def parse(url, releases):
    response = endoflife.fetch_url(url)
    soup = BeautifulSoup(response, features="html5lib")
    table = soup.find(id="tableWraper")
    for tr in reversed(table.findAll("tr")[1:]):
        td_list = tr.findAll("td")
        version_text = td_list[0].get_text().strip()
        for key, regexes in CONFIG.items():
            for regex in regexes:
                matches = re.findall(regex, version_text, re.MULTILINE)
                for version in matches:
                    date_text = td_list[2].get_text().strip()
                    handle_version(key, version, date_text, releases)


print("::group::apple")

releases_by_product = {k: {} for k in CONFIG.keys()}
for url in URLS:
    parse(url, releases_by_product)

for k in CONFIG.keys():
    endoflife.write_releases(k, {
        v: d.strftime("%Y-%m-%d") for v, d in releases_by_product[k].items()
    })

print("::endgroup::")

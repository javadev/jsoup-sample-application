#-------------------------------------------------------------------------------
# Name:     process.py
#
# Author:   Radomirs Cirskis
#
# Created:  2012-09-29
# Licence:  WTFPL
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from __future__ import print_function
import os, sys, re
import requests, bs4
from datetime import datetime
import csv, zipfile

# Configuration:
from config import *

def get_contestants():
    """
    Retrieves contestant data
    Returns a dictionary wiht contestants
    """
    start_pos = 1
    contestants = {}
    while True:
        # raw JSON imput:
        raw = requests.get( GET_SCOREBOARD_URL, params={'start_pos':start_pos}).json
        if raw.has_key('rows'):
            contestants.update( { r['n']: r for r in raw['rows'] } )
            start_pos += 20
        else:
            break
    return contestants


def process_source():
    """
    Python script that downloads all the files from a specified URL with the matching information on
    metat data page specified by an URL
    In addition, the script writes into a .csv the following columns that should match
    the downloaded name of the file : FileName, ContestantName, Country, Language, Year, Round, Rank,
    ProblemName, Size(large/small), Time(hr), Time(min), Time(sec)
    """
    print( "* Loading contestant meta data ..." )
    contestants = get_contestants()
    req = requests.get(SOURCE_URL)
    csv_output = open(OUTPUT_FILE,'wb')
    csv_writer = csv.writer(csv_output)
    csv_writer.writerow([
       'FileName',
       'ContestantName',
       'Country',
       'Language',
       'Year',
       'Round',
       'Rank',
       'ProblemName',
       'Size(large/small)',
       'Time(hr)',
       'Time(min)',
       'Time(sec)'])

    soup = bs4.BeautifulSoup(req.content)
    page_base = soup.find('base')['href']
    try:
        contest_year = '20'+ re.search( 'jam/([0-9]{2})', SOURCE_URL).group(1)
    except:
        contest_year = None

    for link in soup('a',href=re.compile('\./name')):
        username = link.text
        print( "* Processing contestant '{}'".format(username), file=sys.stderr )
        link = link['href']
        if link.startswith('.'):
            link = page_base + link[2:]

        req = requests.get(link)
        soup = bs4.BeautifulSoup(req.content)

        for round in soup('table','stats'):
            rank = round.caption.a.text.split()[1]
            round_title = round.caption.b.text
            print( "= Round '{}'".format(round_title), file=sys.stderr )
            header_row = round.tr
            problems = []
            for problem_th in header_row('th'):
                problems.append(problem_th.text)
                if problem_th.has_attr('colspan'):
                    problems.append(problem_th.text)
            sizes = [th.text for th in header_row.next_sibling('th')]
            solution_tds = round('td')
            for i in xrange(len(solution_tds)):
                # solution present
                if solution_tds[i].a != None:
                    #FileName, ContestantName, Country, Language, Year, Round, Rank,
                    #ProblemName, Size(large/small), Time(hr), Time(min), Time(sec)
                    now = datetime.now()
                    language = solution_tds[i].a.text.strip()
                    download_link = solution_tds[i].a['href']
                    size = sizes[i]
                    problem_name = problems[i]
                    if contestants.has_key(username):
                        country = contestants[username]['c']
                    else:
                        country = None
                    # Download file:
                    src_file = requests.get(download_link)
                    file_name = src_file.headers['content-disposition'].split('filename=')[1]
                    ss_idx = FILE_SS_MAP.get( re.search( '([0-9]_[0-9])', file_name).group(1) )
                    if ss_idx != None and contestants[username]['ss'][ss_idx] > 0:
						time_spent_sec = contestants[username]['ss'][ss_idx]
						time_spent_hour = time_spent_sec / 3600
						time_spent_sec -= time_spent_hour * 3600
						time_spent_min = time_spent_sec / 60
						time_spent_sec -= time_spent_min * 60
                    else:
                        time_spent_hour = time_spent_min = time_spent_sec = None
					
                    dir_name = re.sub('[ /-]','_',problem_name).strip().lower()
                    if not os.path.exists(os.path.join(OUTPUT_DIR, dir_name)):
                        os.makedirs(os.path.join(OUTPUT_DIR, dir_name))
                    # Prefix the file name with the problem name as it isn't unique:
                    full_file_name = os.path.join(OUTPUT_DIR, dir_name, file_name)
                    if not os.path.exists(full_file_name):
                        print( "- Downloading '{}' into '{}'".format(file_name,full_file_name), file=sys.stderr )
                        output = open( full_file_name, 'wb')
                        output.write( src_file.content)
                        output.close()
                    else:
                        print( "- File '{}' already downloaded into '{}'".format(file_name,full_file_name), file=sys.stderr )
                    # Unzip (assuming there is only one file per .zip file):
                    zf = zipfile.ZipFile(full_file_name)
                    source_file_name = zf.namelist()[0]
                    new_source_file_name = os.path.splitext(full_file_name)[0] + os.path.splitext(source_file_name)[1]
                    output = open( new_source_file_name,'wb')
                    output.write( zf.read(source_file_name))
                    zf.close()
                    output.close()
                    csv_writer.writerow([
                        new_source_file_name,username,country,language,contest_year,
                        round_title,rank,problem_name,size,
                        time_spent_hour,time_spent_min,time_spent_sec])
    csv_output.close()

if __name__ == '__main__':
    process_source()

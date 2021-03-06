#! /usr/bin/env python
"""
File: atomic_journal.py

Description: A simple journal that uses atom for editing Markdown
    and MongoDB for data persistence.

"""

import os
from pymongo import MongoClient
import socket
from datetime import datetime
from dateutil.tz import tzlocal
import imp
import subprocess



if os.name == 'nt':
    home_dir = os.environ["HOMEPATH"]
    user = os.environ["USERNAME"]
else:
    home_dir = os.environ["HOME"]
    user = os.environ["USER"]



def get_author():
    """
    Function : GET_AUTHOR

    Description : Get the author from ~/.twsetup_defaults.py.
    """

    f_default = home_dir+"/.twsetup_defaults.py"
    if os.path.exists(f_default):
        defaults = imp.load_source("twsetup_defaults", f_default)
        if "NAME" in dir(defaults):
            return defaults.NAME
    else:
        return "Anoynmous"

def get_email():
    """
    Function : GET_EMAIL

    Description : Get the email from ~/.twsetup_defaults.py.
    """

    f_default = home_dir+"/.twsetup_defaults.py"
    if os.path.exists(f_default):
        defaults = imp.load_source("twsetup_defaults", f_default)
        if "EMAIL" in dir(defaults):
            return defaults.EMAIL
    else:
        return "anyuser@hotmail.com"

def get_aj_tmp_dir():
    f_default = home_dir+"/.twsetup_defaults.py"
    if os.path.exists(f_default):
        defaults = imp.load_source("twsetup_defaults", f_default)
        if "AJ_TMP_DIR" in dir(defaults):
            return defaults.AJ_TMP_DIR

def make_header():
    """
    Function : MAKE_HEADER

    Description : Create a header for the journal.
    """

    host_name = socket.gethostname()
    user_name = user
    t = datetime.now()
    tz_name = datetime.now(tzlocal()).tzname()
    tz_dst = datetime.now(tzlocal()).dst()

    date = [
      t.year,
      t.month,
      t.day
    ]

    date_str = []
    itr = map(str,date)
    for x in itr:
        date_str.append(x)
    for k, x in enumerate(date_str):
        if len(x) == 1:
            date_str[k] = "0"+x

    time = [
      t.hour,
      t.minute
    ]

    time_str = []
    itr = map(str, time)
    for x in itr:
        time_str.append(x)
    for k, x in enumerate(time_str):
        if len(x) == 1:
            time_str[k] = "0"+x

    author = get_author()
    email = get_email()

    date_time = "-".join(
        date_str
        ) + "  " + ":".join(time_str) + " " + tz_name

    header = "###" + author + "\n" + date_time + "\n\n---"

    return header

def get_time_str():
    header = make_header()
    return header.split("\n")[1].split("  ")[1]

def get_date_str():
    header = make_header()
    return header.split("\n")[1].split("  ")[0]


def get_date_time_str():
    header_lst = make_header().split("\n")
    return header_lst[-3]


def get_atomic_journalDB():
    client = MongoClient()
    wgapl = client["wgapl"]
    ajDB = wgapl["ajdb"]
    return ajDB

def is_entry_today():
    ajDB = get_atomic_journalDB()
    if ajDB.find_one({"date":get_date_str()}) != None:
        return True
    else:
        return False

def clear_text_buffer():
    journal_buffer = "/tmp/"+ user +"_aj_buffer.md"
    if os.path.exists(journal_buffer):
        os.remove(journal_buffer)


def create_text_buffer():

    aj_tmpdir = get_aj_tmp_dir()
    if aj_tmpdir == None:
        journal_buffer = "/tmp/"+ user +"_aj_buffer.md"
    else:
        journal_buffer = aj_tmpdir +"/"+user+"_aj_buffer.md"
    if not is_entry_today():
        fh = open(journal_buffer, "w")
        header = make_header()+"\n"
        fh.write(header)
        fh.close()
        return journal_buffer
    else:
        clear_text_buffer()
        ajDB = get_atomic_journalDB()
        entry = ajDB.find_one({"date":get_date_str()})
        contents = entry["text"]
        contents += "\n---\n" + get_time_str() + "\n\n"
        fh = open(journal_buffer, "w")
        fh.write(contents)
        fh.close()
        return journal_buffer



def insert_item(text):
    date = get_date_str()
    author = get_author()
    email = get_email()
    ajDB = get_atomic_journalDB()
    entry = {
    "date" : date,
    "author" : author,
    "email" : email,
    "text" : text
    }
    ajDB.insert(entry)

def update_item(text):
    date = get_date_str()
    author = get_author()
    email = get_email()
    ajDB = get_atomic_journalDB()
    entry = {
    "date" : date,
    "author" : author,
    "email" : email,
    "text" : text
    }

    query = {"$and": [
        {"date": date},
        {"author": author}
        ]
             }
    ajDB.update(query,entry)



def open_atom():
    """
    Function : SLOW_AND_STEAD()

    Description : Opens the contents of todays journal in the atom
                  text editor.
    """
    # create_text_buffer() creates the text buffer intelligently
    journal_buffer = create_text_buffer()

    # Launch atom, tell it to open a new window and to wait for
    # atom to close before continuing.
    atom_proc_str = "atom -w -n "+journal_buffer
    p = subprocess.Popen(atom_proc_str, shell=True)
    p.communicate()

    # Read in the contents of the temporary buffer file.
    fh = open(journal_buffer, "r")
    contents = fh.read()
    fh.close()

    # Get rid of the temporary text file.
    clear_text_buffer()

    return contents


def slow_and_steady():
    """
    Function : SLOW_AND_STEADY()

    Description : The main() function.
    """
    # This call opens up the atom editor.
    contents = open_atom()

    # If there is no entry for today, we *insert* the contents.
    if not is_entry_today():
        insert_item(contents)
    # Otherwise we **update** the previous contents
    else:
        update_item(contents)

if __name__ == "__main__":
    slow_and_steady()

#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause

"""Repo Activity REST API Version - DEPRECATED Example only
This script is comparison with the other script (repo_activity.py)
which uses the GraphQL API. This one is very slow and should not
be used to gather data.

This script uses the GitHub REST API to retrieve relevant
information about all repositories from one or more GitHub
orgs.

This version runs much more slowly than the other GraphQL 
version, and if there are a lot of orgs / repos, the API
rate limit will be exceeded if the script is not slowed down.

As input, this script requires a file named 'orgs.txt' containing
the name of one GitHub org per line residing in the same folder 
as this script.

Your API key should be stored in a file called gh_key in the
same folder as this script.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

As output:
* A message about each org being processed will be printed to the screen.
* the script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date.

output/a_repo_activity_2022-01-14.csv"
"""

import sys
import pandas as pd
import csv
from datetime import datetime
from time import sleep
from github import Github
from os.path import dirname, join
from common_functions import read_key

# Read GitHub key from file
try:
    gh_key = read_key('gh_key')
    g = Github(gh_key)

except:
    print("Error reading GH Key. Exiting")
    sys.exit()

# prepare csv file and write header row

today = datetime.today().strftime('%Y-%m-%d')
output_filename = "./output/a_repo_activity_" + today + ".csv"

try:
    current_dir = dirname(__file__)
    file_path = join(current_dir, output_filename)

    csv_output = open(file_path, 'w')
    csv_output.write('org,repo,license,private,forked,archived,last_updated,last_pushed,last_committer_login,last_committer_name,last_committer_email,last_committer_date\n')

except:
    print('Could not write to csv file. Exiting')
    sys.exit(1)

# Read list of orgs from a file

org_list = []
with open('orgs.txt') as orgfile:
    orgs = csv.reader(orgfile)
    for row in orgs:
        org_list.append(row[0])
        
# Get repos and repo info for each org

for github_org in org_list:

#    sleep(90) #add delay to slow down hitting rate limits
    print("Processing ", github_org)

    try:
        org = g.get_organization(github_org)
    except:
        print("ERROR: Cannot process ", github_org)
        continue

    try:
        for x in org.get_repos():
            try:
                for y in x.get_commits():
                    try:
                        author_login = y.author.login
                        author_name = y.author.name
                        author_email = y.author.email
                        break
                    except:
                        author_login = None
                        author_name = None
                        author_email = None
                        

                try:
                    last_commit_date = x.get_commit(y.sha).commit.author.date
                except:
                    last_commit_date = "No commits, repo may be empty"

                # When this fails it usually means there is no license
                try:
                    license = x.get_license().license.name
                except:
                    license = "Likely Unlicensed" 

                csv_string = github_org + ',' + x.full_name + ',' + str(license) + ',' + str(x.private) + ',' + str(x.fork) + ',' + str(x.archived) + ',' + str(x.updated_at) + ',' + str(x.pushed_at) + ',' + str(author_login) + ',' + str(author_name) + ',' + str(author_email) + ',' + str(last_commit_date) + '\n'
                csv_output.write(csv_string)
            except: 
                print("Cannot process data for", x) 
                csv_output.write(github_org + ',' + x.full_name + ',' + str(x.private) + ',' + str(x.fork) + ',' + str(x.archived) + ',' + str(x.updated_at) + ',' + str(x.pushed_at) + ',' + 'Error' + ',' + 'Error' + ',' + 'Error' + ',' + 'Error' + '\n')

    except:
         print("Cannot get repos for", github_org)

#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

"""Calculate OSSF's Criticality Score for pinned repos on a list of orgs

This script uses the GitHub GraphQL API to retrieve a list of pinned
repositories from a list of GitHub organizations and then runs 
criticality score on each of those repos. It can also take an individual 
repo URL as one of the inputs

As input, this script requires a file named 'monitoring.txt' residing in
the same folder as this script. This file should contain the name of one
GitHub org or URL to an individual repository per line. Example file format:
    vmware
    https://github.com/greenplum-db/gpdb
    vmware-tanzu

Your API key should be stored in a file called gh_key in the
same folder as this script.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

This script depends on another tool called Criticality Score to run.
See https://github.com/ossf/criticality_score for more details, including
how to set up a required environment variable. This function requires that
you have this tool installed, and it might only run on mac / linux. 

As output:
* A message about each repo being processed will be printed to the screen.
* the script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date.

output/monitoring_2023-01-28.csv"

"""

import sys
import subprocess
import os
import requests
import json
import csv
from common_functions import create_file, read_key, read_orgs  

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

# Use the token to set the environment variable required by criticality_score
os.environ['GITHUB_AUTH_TOKEN'] = api_token

def make_query():
    """Creates and returns a GraphQL query to get pinned repos for an org"""
    return """query pinned($org_name: String!) {
                 organization(login:$org_name) {
                    pinnedItems(first: 10, types: REPOSITORY) {
                        nodes {
                            ... on Repository {
                              url
                            }
                        }
                    }
                  }
                }"""

# TODO use read_orgs function to read from file.
org_list = read_orgs('monitoring.txt')

# Set up the parameters needed to use GitHub's GraphQL API
url = 'https://api.github.com/graphql'
headers = {'Authorization': 'token %s' % api_token}

# Iterate through each GH org, run the query to get pinned repos, 
# and store the repo URLs in repo_list
repo_list = []

for org_name in org_list:
    # To handle both orgs and individual repos ...
    # Maybe split this into 2. If startswith http, run crit score on that URL
    # Otherwise run this query for pinned items on an org

    if org_name.startswith('http'):
        repo_list.append(org_name)

    else:
        query = make_query()

        variables = {"org_name": org_name}
        r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
        json_data = json.loads(r.text)

        # Wrap in try/except for when org isn't valid.
        try:
            for url_dict in json_data['data']['organization']['pinnedItems']['nodes']:
                repo_list.append(url_dict['url'])
        except:
            print("Could not get data on", org_name, "- check to make sure the org name is correct and has pinned repos")

# For each repo in repo_list, run criticality_score and append
# the json output to csv_row_list
csv_row_list = []

for repo in repo_list:
    cmd_str = 'criticality_score --repo ' + repo + ' --format json'
    print("Processing", repo)
    try:
        proc = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out, err = proc.communicate()

        if not err:
            json_str = out.decode("utf-8")
            csv_row_list.append(json.loads(json_str))
        else:
            print('Error calculating scores', repo)
    except:
        print('Error calculating scores', repo)

# Create csv output file and write to it

keys = csv_row_list[0].keys()

file, file_path = create_file("monitoring")

with open(file_path, 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(csv_row_list)

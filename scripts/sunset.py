#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

"""Gather data to determine whether a repo can be archived

This script uses the GitHub GraphQL API to retrieve relevant
information about a repository, including forks to determine ownership
and possibly contact people to understand how they are using a project.
More detailed information is gathered about recently updated forks and 
their owners with the recently updated threshold set in a variable called
recently_updated (currently set to 9 months).

Usage
-----

Run the script with one repo url as input
    $python3 sunset.py -u "https://github.com/org_name/repo_name"

Run the script with a csv file containing one org_name,repo_name pair
per line:
    $python3 sunset.py -f sunset.csv

Dependencies and Requirements
-----------------------------

This script depends on another tool called Criticality Score to run.
See https://github.com/ossf/criticality_score for more details, including
how to set up a required environment variable. This function requires that
you have this tool installed, and it might only run on mac / linux. 

Your API key should be stored in a file called gh_key in the
same folder as this script.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

Before using this script, please make sure that you are adhering 
to the GitHub Acceptable Use Policies:
https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies
In particular, "You may not use information from the Service 
(whether scraped, collected through our API, or obtained otherwise)
for spamming purposes, including for the purposes of sending unsolicited
emails to users or selling User Personal Information (as defined in the
GitHub Privacy Statement), such as to recruiters, headhunters, and job boards."

Output
------

* Prints basic data about each repo processed to the screen to show progress.
* the script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date.

output/sunset_2022-01-14.csv"
"""

import argparse
import sys
from common_functions import create_file, read_key, get_criticality
from datetime import date
from dateutil.relativedelta import relativedelta
import csv

def make_query(after_cursor = None):
    """Creates and returns a GraphQL query with cursor for pagination on forks"""

    return """query repo_forks($org_name: String!, $repo_name: String!){
        repository(owner: $org_name, name: $repo_name){
            forks (first:20, after: AFTER) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                totalCount
                nodes {
                updatedAt
                url
                owner {
                    __typename
                    url
                    ... on User{
                    name
                    company
                    email
                    organizations (last:50){
                        nodes{
                        name
                        }
                    }
                    }
                }
                }
            }
            stargazerCount
            }
        }""".replace(
            "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

def get_fork_data(api_token, org_name, repo_name):
    """Executes the GraphQL query to get repository data.

    Parameters
    ----------
    api_token : str
        The GH API token retrieved from the gh_key file.
    org_name and repo_name : str
        The GitHub organization name and repository name to analyze.

    Returns
    -------
    repo_info_df : pandas dataframe
        Dataframe with all of the output from the API query
    num_forks : int
        Number of forks for the repo
    num_stars : int
        Number of stars for the repo
    status : str
        Value is "OK" or "Error" depending on whether data could be gathered for that org/repo pair
    """

    import requests
    import json
    import pandas as pd

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}

    repo_info_df = pd.DataFrame()

    has_next_page = True
    after_cursor = None

    while has_next_page:
        try:
            query = make_query(after_cursor)

            variables = {"org_name": org_name, "repo_name": repo_name}
            r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
            json_data = json.loads(r.text)

            df_temp = pd.DataFrame(json_data["data"]["repository"]["forks"]["nodes"])
            repo_info_df = pd.concat([repo_info_df, df_temp])

            num_forks = json_data["data"]["repository"]["forks"]["totalCount"]
            num_stars = json_data["data"]["repository"]["stargazerCount"]

            has_next_page = json_data["data"]["repository"]["forks"]["pageInfo"]["hasNextPage"]
            after_cursor = json_data["data"]["repository"]["forks"]["pageInfo"]["endCursor"]

            status = "OK"
        except:
            has_next_page = False
            num_forks = None
            num_stars = None
            status = "Error"

    return repo_info_df, num_forks, num_stars, status

# Read arguments from the command line to specify whether the repo and org
# should be read from a file for multiple repos or from a url to analyze 
# a single repo

parser = argparse.ArgumentParser()

parser.add_argument("-f", "--filename", dest = "csv_file", help="File name of a csv file containing one repo_name,org_name per line")
parser.add_argument("-u", "--url", dest = "gh_url", help="URL for a GitHub repository")

args = parser.parse_args()

if args.csv_file:
    with open(args.csv_file) as f:
        reader = csv.reader(f)
        repo_list = list(reader)

if args.gh_url:
    gh_url = args.gh_url

    url_parts = gh_url.strip('/').split('/')
    org_name = url_parts[3]
    repo_name = url_parts[4]

    repo_list = [[org_name,repo_name]]

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

# Uses nine months as recently updated fork threshold
recently_updated = str(date.today() + relativedelta(months=-9))

# all_rows it the variable that will be written to the csv file. This initializes it with a csv header line
all_rows = [["Org", "Repo", "Status", "Stars", "Forks", "Dependents", "Crit Score", "fork url", "Fork last updated", "account type", "owner URL", "name", "company", "email", "Other orgs that the owner belongs to"]]

for repo in repo_list:
    org_name = repo[0]
    repo_name = repo[1]

    try:
        repo_info_df, num_forks, num_stars, status = get_fork_data(api_token, org_name, repo_name)

        if status == "OK":

            dependents_count, criticality_score = get_criticality(org_name, repo_name, api_token)

            # criticality_score sometimes fails in a way that is not reflected in it's own error status
            # and dumps an error message into these variables. I suspect it's caused by a timeout, since it
            # seems to happen mostly with very large repos. This is to clean that up and make the csv
            # file more readable. The check is for isnumeric because Criticality Score returns strings 
            # for some reason.

            if dependents_count.isnumeric() is False:
                criticality_score = "Error"
                dependents_count = "Error"

            print(org_name, repo_name, "Dependents:", dependents_count, "Criticality Score:", criticality_score, "Stars", num_stars, "Forks", num_forks)
            
            # Only run this section if there are forks
            if num_forks > 0:
                # We only need recent forks in the csv file, so this creates a subset of the dataframe.
                # If there are no recent forks (empty df), only the basic repo info is
                # written to the csv file. Otherwise, details about the forks are gathered and added to the csv.
                recent_forks_df = repo_info_df.loc[repo_info_df['updatedAt'] > recently_updated]

                if len(recent_forks_df) == 0:
                    row = [org_name, repo_name, status, num_stars, num_forks, dependents_count, criticality_score]
                    all_rows.append(row)
                    
                else:
                    for fork_obj in recent_forks_df.iterrows():
                        fork = fork_obj[1]

                        fork_updated = fork['updatedAt']
                        fork_url = fork['url']
                        fork_owner_type = fork['owner']['__typename']
                        fork_owner_url = fork['owner']['url']
                        try:
                            fork_owner_name = fork['owner']['name']
                        except:
                            fork_owner_name = None
                        try:
                            fork_owner_company = fork['owner']['company']
                        except:
                            fork_owner_company = None
                        try:
                            fork_owner_email = fork['owner']['email']
                        except:
                            fork_owner_email = None
                        try:
                            fork_owner_orgs = ''
                            for orgs in fork['owner']['organizations']['nodes']:
                                fork_owner_orgs = fork_owner_orgs + orgs['name'] + ';'
                            fork_owner_orgs = fork_owner_orgs[:-1] #strip last ;
                            if len(fork_owner_orgs) == 0:
                                fork_owner_orgs = None
                        except:
                            fork_owner_orgs = None

                        row = [org_name, repo_name, status, num_stars, num_forks, dependents_count, criticality_score, fork_url, fork_updated, fork_owner_type, fork_owner_url, fork_owner_name, fork_owner_company, fork_owner_email, fork_owner_orgs]
                        all_rows.append(row)
            else:
                row = [org_name, repo_name, status, num_stars, num_forks, dependents_count, criticality_score, None, None, None, None, None, None, None, None]
                all_rows.append(row)
        else:
            print("Cannot process", org_name, repo_name)
            row = [org_name, repo_name, status]
            all_rows.append(row)
    except:
        status = "Error"
        print("Cannot process",  org_name, repo_name)
        row = [org_name, repo_name, status]
        all_rows.append(row)
        
# Create csv output file and write to it.
file, file_path = create_file("sunset")

try:
    with file:    
        write = csv.writer(file)
        write.writerows(all_rows)
except:
    print('Could not write to csv file. This may be because the output directory is missing or you do not have permissions to write to it. Exiting')

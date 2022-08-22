#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

"""Gather data to determine whether a repo can be archived
TODO Save output to a csv file after decided how best to format it.
TODO Take as input a list of orgs from a file.

Instructions to run the script with one repo url as input
$python3 sunset.py https://github.com/vmware-tanzu/pinniped

This script uses the GitHub GraphQL API to retrieve relevant
information about a repository, including forks to determine ownership
and possibly contact people to understand how they are using a project.
More detailed information is gathered about recently updated forks and 
their owners with the recently updated threshold set in a variable called
recently_updated (currently set to 9 months).

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

As output:
* Currently prints details to the screen.
* TODO print them to a file
"""

import sys
from common_functions import read_key, get_criticality
from datetime import date
from dateutil.relativedelta import relativedelta

def make_query(after_cursor = None):
    """Creates and returns a GraphQL query with cursor for pagination on forks"""

    return """query repo_forks($org_name: String!, $repo_name: String!){
        repository(owner: $org_name, name: $repo_name){
            stargazerCount
            forks (first:100, after: AFTER) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                totalCount
                edges {
                    node {
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
            }
            }
        }""".replace(
            "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

def get_fork_data(api_token, org_name, repo_name):
    """Executes the GraphQL query to get repository data from one or more GitHub orgs.

    Parameters
    ----------
    api_token : str
        The GH API token retrieved from the gh_key file.

    Returns
    -------
    ?????
    """

    import requests
    import json
    import pandas as pd

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}

    repo_info_df = pd.DataFrame()

    has_next_page = True
    after_cursor = None

    print(org_name, repo_name)

    while has_next_page:
        try:
            query = make_query(after_cursor)

            variables = {"org_name": org_name, "repo_name": repo_name}
            r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
            json_data = json.loads(r.text)

            #df_temp = pd.DataFrame(json_data["data"]["repository"]["forks"]["edges"])
            df_temp = pd.DataFrame(json_data["data"]["repository"])
            repo_info_df = pd.concat([repo_info_df, df_temp])

            has_next_page = json_data["data"]["repository"]["forks"]["pageInfo"]["hasNextPage"]
            after_cursor = json_data["data"]["repository"]["forks"]["pageInfo"]["endCursor"]
        except:
            has_next_page = False
            print("ERROR Cannot process")

    return repo_info_df

try:
    gh_url = str(sys.argv[1])

except:
    print("Please enter the URL for the GitHub repo. Example: https://github.com/vmware-tanzu/velero")
    gh_url = input("Enter a URL: ")

url_parts = gh_url.strip('/').split('/')
org_name = url_parts[3]
repo_name = url_parts[4]

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

# Uses nine months as recently updated fork threshold
recently_updated = str(date.today() + relativedelta(months=-9))

repo_info_df = get_fork_data(api_token, org_name, repo_name)

dependents_count, criticality_score = get_criticality(org_name, repo_name, api_token)
print("Dependents:", dependents_count)
print("Criticality Score:", criticality_score, "(Values 0 to 1)")

num_stars = repo_info_df['stargazerCount']['totalCount']
num_forks = repo_info_df['forks']['totalCount']
print("Stars:", num_stars, "Forks", num_forks)
print("Recently updated forks")
print("Fork last updated, account type, fork url, owner URL, name, company, email, Other orgs that the owner belongs to")
for fork in repo_info_df['forks']['edges']:
    if fork['node']['updatedAt'] > recently_updated:
        fork_updated = fork['node']['updatedAt']
        fork_url = fork['node']['url']
        fork_owner_type = fork['node']['owner']['__typename']
        fork_owner_url = fork['node']['owner']['url']
        try:
            fork_owner_name = fork['node']['owner']['name']
        except:
            fork_owner_name = None
        try:
            fork_owner_company = fork['node']['owner']['company']
        except:
            fork_owner_company = None
        try:
            fork_owner_email = fork['node']['owner']['email']
        except:
            fork_owner_email = None
        try:
            fork_owner_orgs = ''
            for orgs in fork['node']['owner']['organizations']['nodes']:
                fork_owner_orgs = fork_owner_orgs + orgs['name'] + ';'
            fork_owner_orgs = fork_owner_orgs[:-1] #strip last ;
            if len(fork_owner_orgs) == 0:
                fork_owner_orgs = None
        except:
            fork_owner_orgs = None
        print(fork_updated, fork_owner_type, fork_url, fork_owner_url, fork_owner_name, fork_owner_company, fork_owner_email, fork_owner_orgs)
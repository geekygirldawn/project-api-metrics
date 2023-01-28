#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

""" Gathers some basic data about PRs in a specific repo starting with the
most recent PRs.

Usage
-----

pr_activity.py [-h] -o ORG_NAME -r REPO_NAME [-n NUM_PAGES]
  -h, --help            show this help message and exit
  -o ORG_NAME, --org ORG_NAME
                        The name of the GitHub organization where your repo is found (required)
  -r REPO_NAME, --repo REPO_NAME
                        The name of a GitHub repository in that org where your PRs can be found (required)
  -n NUM_PAGES, --num NUM_PAGES
                        The number of pages of results with 10 results per page (10 = 100 results) - default is 10

Output
------

* the script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date.

output/sunset_2022-01-14.csv
"""

import argparse
import pandas as pd
from common_functions import read_key, create_file

def make_query(before_cursor = None):
    """Creates and returns a GraphQL query with cursor for pagination"""

    return """query repo($org_name: String!, $repo_name: String!){
  repository(owner: $org_name, name: $repo_name) {
    pullRequests (last: 10, before: BEFORE) {
        pageInfo{
            hasPreviousPage
            startCursor
        }
        nodes {
          createdAt
          mergedAt
          additions
          deletions
          changedFiles
          state
          comments{
            totalCount
          }
          author{
            ... on User{
            	login
                name
                pullRequests{
                    totalCount
                }
          	}
          }
        }
      }
    }
  }""".replace(
        "BEFORE", '"{}"'.format(before_cursor) if before_cursor else "null"
    )

parser = argparse.ArgumentParser()

parser.add_argument("-o", "--org", required=True, dest = "org_name", help="The name of the GitHub organization where your repo is found (required)")
parser.add_argument("-r", "--repo", required=True, dest = "repo_name", help="The name of a GitHub repository in that org where your PRs can be found (required)")
parser.add_argument("-n", "--num", dest = "num_pages", default=10, type=int, help="The number of pages of results with 10 results per page (10 = 100 results) - default is 10")

args = parser.parse_args()

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

def get_pr_data(api_token, org_name, repo_name, num_pages):
    """Executes the GraphQL query to get PR data from a repository.

    Parameters
    ----------
    api_token : str
        The GH API token retrieved from the gh_key file.
    org_name : str
        The name of the GitHub organization where your repo is found
    repo_name : str
        The name of a GitHub repository in that org where your PRs can be found 
    num_pages : int
        The number of pages of results with 10 results per page (10 = 100 results)

    Returns
    -------
    repo_info_df : pandas.core.frame.DataFrame
    """
    import requests
    import json
    import pandas as pd

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}
    
    repo_info_df = pd.DataFrame()

    has_previous_page = True
    before_cursor = None

    i = 1 # Iterator starts at page 1

    while has_previous_page and i <= num_pages:
        i+=1
        try:
            query = make_query(before_cursor)

            variables = {"org_name": org_name, "repo_name": repo_name}
            r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
            json_data = json.loads(r.text)

            df_temp = pd.DataFrame(json_data["data"]["repository"]["pullRequests"]["nodes"])
            repo_info_df = pd.concat([repo_info_df, df_temp])

            has_previous_page = json_data["data"]["repository"]["pullRequests"]["pageInfo"]["hasPreviousPage"]
            before_cursor = json_data["data"]["repository"]["pullRequests"]["pageInfo"]["startCursor"]

            status = "OK"
        except:
            has_previous_page = False
            status = "Error"

    return repo_info_df, status

repo_info_df, status = get_pr_data(api_token, args.org_name, args.repo_name, args.num_pages)

def expand_author(author):
    import pandas as pd
    if pd.isnull(author):
        author_list = [None, None, None]
    else:
        author_list = [author['login'], author['name'], author['pullRequests']['totalCount']]
    return author_list

def expand_count(comments):
    import pandas as pd
    if pd.isnull(comments):
        comment_ct = 0
    else:
        comment_ct = comments['totalCount']
    return comment_ct

repo_info_df['author_list'] = repo_info_df['author'].apply(expand_author)
repo_info_df[['author_login', 'author_name', 'author_pr_count', ]] = pd.DataFrame(repo_info_df.author_list.tolist(), index= repo_info_df.index)
repo_info_df['comment_ct'] = repo_info_df['comments'].apply(expand_count)
repo_info_df = repo_info_df.drop(columns=['author','author_list','comments'])

# prepare file and write dataframe to csv

try:
    file, file_path = create_file("pr_activity")
    repo_info_df.to_csv(file_path, index=False)

except:
    print('Could not write to csv file. This may be because the output directory is missing or you do not have permissions to write to it. Exiting')


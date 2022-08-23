#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

""" Search for repos mentioning a keyword
This script uses the GitHub GraphQL API to retrieve relevant
information about repositories mentioning certain keywords.

As input, this script requires a file named 'keywords.txt' containing
one keyword per line residing in the same folder as this script.

Your API key should be stored in a file called gh_key in the
same folder as this script.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

As output:
* A message about each keyword being processed will be printed to the screen.
* the script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date.
  Example: "output/keyword_search_2022-07-22.csv"
"""

import sys
from common_functions import read_key, create_file

def make_query(after_cursor = None):
    """Creates and returns a GraphQL query with cursor for pagination"""

    return """query MyQuery ($keyword: String!){
        search(query: $keyword, type: REPOSITORY, first: 100, after: AFTER) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
            ... on Repository {
                nameWithOwner
                name
                owner{
                    login
                }
                url
                description
                updatedAt
                createdAt
                isFork
                isEmpty
                isArchived
                forkCount
                stargazerCount
            }
            }
        }
    }""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

def get_repo_data(api_token):
    """Executes the GraphQL query to get repository data from one or more GitHub orgs.

    Parameters
    ----------
    api_token : str
        The GH API token retrieved from the gh_key file.

    Returns
    -------
    repo_info_df : pandas.core.frame.DataFrame
    """
    import requests
    import json
    import pandas as pd
    from common_functions import read_file 

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}
    
    repo_info_df = pd.DataFrame()
    
    # Read list of keywords from a file

    try:
        keyword_list = read_file('keywords.txt')
    except:
        print("Error reading keywords. This script depends on the existance of a file called keywords.txt containing one keyword per line. Exiting")
        sys.exit()
    
    for keyword in keyword_list:  
        has_next_page = True
        after_cursor = None
    
        print("Processing", keyword)

        while has_next_page:

            try:
                query = make_query(after_cursor)

                variables = {"keyword": keyword}
                r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
                json_data = json.loads(r.text)

                df_temp = pd.DataFrame(json_data["data"]["search"]["nodes"])
                repo_info_df = pd.concat([repo_info_df, df_temp])

                has_next_page = json_data["data"]["search"]["pageInfo"]["hasNextPage"]
                after_cursor = json_data["data"]["search"]["pageInfo"]["endCursor"]
            except:
                has_next_page = False
                print("ERROR Cannot process", keyword)
        
    return repo_info_df

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

repo_info_df = get_repo_data(api_token)

def expand_owner(owner):
    import pandas as pd
    if pd.isnull(owner):
        owner = 'Not Found'
    else:
        owner = owner['login']
    return owner

repo_info_df['owner_name'] = repo_info_df['owner'].apply(expand_owner)
repo_info_df = repo_info_df.drop(columns=['owner'])

# Reformat to put columns in a logical order
repo_info_df = repo_info_df[['owner_name','name','nameWithOwner','url','description','updatedAt','createdAt','isFork','isEmpty','isArchived','forkCount','stargazerCount']]

# prepare file and write dataframe to csv

try:
    file, file_path = create_file("keyword_search")
    repo_info_df.to_csv(file_path, index=False)

except:
    print('Could not write to csv file. This may be because the output directory is missing or you do not have permissions to write to it. Exiting')

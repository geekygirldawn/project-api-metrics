#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

"""Quick Inclusivity Check for GitHub orgs
This script uses the GitHub GraphQL API to retrieve default branch
name and code of conduct for each repo in a GitHub org.

As input, this script requires a file named 'orgs.txt' containing
the name of one GitHub org per line residing in the same folder 
as this script.

Your API key should be stored in a file called gh_key in the
same folder as this script.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

As output:
* A message will be printed to the screen for any org with a default 
  branch name of "master" or a missing / unrecognized code of conduct.
  Orgs that are forks of another repo, private, empty, or archived
  will not be printed, but the details will be written to the csv file.
* The script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date. All details are written to the csv file
  including repos that aren't printed to the screen.

output/inclusivity_check_2022-01-14.csv"

"""

import sys
from common_functions import read_key, expand_name_df
from datetime import datetime
from os.path import dirname, join

def make_query(after_cursor = None):
    """Creates and returns a GraphQL query with cursor for pagination"""

    return """query RepoQuery($org_name: String!) {
             organization(login: $org_name) {
               repositories (first: 5 after: AFTER){
                 pageInfo {
                   hasNextPage
                   endCursor
                 }
                 nodes { 
                   nameWithOwner
                    defaultBranchRef {
                        name 
                    }
                    codeOfConduct{
                        url
                    }
                    isPrivate
                    isFork
                    isEmpty
                    isArchived
                 }
                }
             }
        }""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

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
    from common_functions import read_orgs 

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}
    
    repo_info_df = pd.DataFrame()
    
    # Read list of orgs from a file

    try:
        org_list = read_orgs('orgs.txt')
    except:
        print("Error reading orgs. This script depends on the existance of a file called orgs.txt containing one org per line. Exiting")
        sys.exit()
    
    for org_name in org_list:  
        has_next_page = True
        after_cursor = None
    
        print("Processing", org_name)

        while has_next_page:

            try:
                query = make_query(after_cursor)

                variables = {"org_name": org_name}
                r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
                json_data = json.loads(r.text)

                df_temp = pd.DataFrame(json_data['data']['organization']['repositories']['nodes'])
                repo_info_df = pd.concat([repo_info_df, df_temp])

                has_next_page = json_data["data"]["organization"]["repositories"]["pageInfo"]["hasNextPage"]

                after_cursor = json_data["data"]["organization"]["repositories"]["pageInfo"]["endCursor"]
            except:
                has_next_page = False
                print("ERROR Cannot process", org_name)
        
    return repo_info_df

repo_info_df = get_repo_data(api_token)

# This section reformats the output into what we need in the csv file
repo_info_df = expand_name_df(repo_info_df,'defaultBranchRef','defaultBranch')

def expand_coc(coc):
    import pandas as pd
    if pd.isnull(coc):
        coc_url = 'Not Found'
    else:
        coc_url = coc['url']
    return coc_url

repo_info_df['codeOfConduct_url'] = repo_info_df['codeOfConduct'].apply(expand_coc)
repo_info_df = repo_info_df.drop(columns=['defaultBranchRef', 'codeOfConduct'])

# prepare file and write dataframe to csv

try:
    today = datetime.today().strftime('%Y-%m-%d')
    output_filename = "./output/inclusivity_check_" + today + ".csv"
    current_dir = dirname(__file__)
    file_path = join(current_dir, output_filename)
    repo_info_df.to_csv(file_path, index=False)

except:
    print('Could not write to csv file. This may be because the output directory is missing or you do not have permissions to write to it. Exiting')

print("repo            branch   Code of Conduct")
for rows in repo_info_df.iterrows():
    repo = rows[1]['nameWithOwner']
    branch = rows[1]['defaultBranch']
    coc = rows[1]['codeOfConduct_url']
    private = rows[1]['isPrivate']
    fork = rows[1]['isFork']
    empty = rows[1]['isEmpty']
    archive = rows[1]['isArchived']
    if private or fork or empty or archive:
        pass
    elif (branch == 'master' or  coc == 'Not Found'):
        print(repo, branch, coc)
print("\nMore details can be found in", file_path)

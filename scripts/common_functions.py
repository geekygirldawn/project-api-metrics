# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause

"""Common Functions
This file contains some common functions that are used within
the other scripts in this repo.

This file can also be imported as a module.
"""

def read_key(file_name):
    """Retrieves a GitHub API key from a file.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    key : str
    """

    from os.path import dirname, join

    # Reads the first line of a file containing the GitHub API key
    # Usage: key = read_key('gh_key')

    current_dir = dirname(__file__)
    file2 = "./" + file_name
    file_path = join(current_dir, file2)

    with open(file_path, 'r') as kf:
        key = kf.readline().rstrip() # remove newline & trailing whitespace
    return key

def read_orgs(file_name):
    """Retrieves a list of orgs from a file.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    org_list : list
    """
    import csv

    org_list = []

    with open(file_name) as orgfile:
        orgs = csv.reader(orgfile)
        for row in orgs:
            org_list.append(row[0])

    return org_list

def read_file(file_name):
    """Retrieves a list from a file.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    a_list : list
    """
    import csv

    content_list = []

    with open(file_name) as in_file:
        content = csv.reader(in_file)
        for row in content:
            content_list.append(row[0])

    return content_list

def expand_name_df(df,old_col,new_col):
    """Takes a dataframe df with an API JSON object with nested elements in old_col, 
    extracts the name, and saves it in a new dataframe column called new_col

    Parameters
    ----------
    df : dataframe
    old_col : str
    new_col : str

    Returns
    -------
    df : dataframe
    """
    
    import pandas as pd

    def expand_name(nested_name):
        """Takes an API JSON object with nested elements and extracts the name
        Parameters
        ----------
        nested_name : JSON API object

        Returns
        -------
        object_name : str
        """
        if pd.isnull(nested_name):
            object_name = 'Not Found'
        else:
            object_name = nested_name['name']
        return object_name

    df[new_col] = df[old_col].apply(expand_name)
    return df
    

def get_criticality(org_name, repo_name, api_token):
    """See https://github.com/ossf/criticality_score for more details
    This function requires that you have version 1.0.7 of this tool 
    installed (the older Python version but not the final Python version,
    which doesn't work for some reason within the script - possibly because
    of how they've implemented the deprecation warnings). You can install
    the correct version using:
    pip install 'criticality-score<1.0.8' --force-reinstall
    
    Parameters
    ----------
    org_name : str
    repo_name : str
    api_token : str

    Returns
    -------
    dependents_count : str
        Numeric integer that is returned as a string
    criticality_score : str
        This value ranges from 0 to 1 (like a float) with lower scores indicating less critical projects.
    
    """

    import subprocess
    import os
    
    os.environ['GITHUB_AUTH_TOKEN'] = api_token

    cmd_str = 'criticality_score --repo github.com/' + org_name + '/' + repo_name + ' --format csv'

    try:
        proc = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out, err = proc.communicate()
        
        if not err:
            csv_str = out.decode("utf-8")
            items = csv_str.split(',')
            dependents_count = items[25]
            criticality_score = items[26].rstrip()
        else: 
            dependents_count = None
            criticality_score = None
    except:
        dependents_count = None
        criticality_score = None

    return dependents_count, criticality_score

def create_file(pre_string):
    """Creates an output file in an "output" directory with today's date
    as part of the filename and prints the file_path to the terminal to
    make it easier to open the output file.
    
    Parameters
    ----------
    pre_string : str
        This is the string that will preface today's date in the filename

    Returns
    -------
    file : file object
    file_path : str
        This is the full path to the file name for the output.
    
    """
    from datetime import datetime
    from os.path import dirname, join

    today = datetime.today().strftime('%Y-%m-%d')
    output_filename = "./output/" + pre_string + "_" + today + ".csv"
    current_dir = dirname(__file__)
    file_path = join(current_dir, output_filename)
    file = open(file_path, 'w', newline ='')

    print("Output file:\n", file_path, sep="")

    return file, file_path

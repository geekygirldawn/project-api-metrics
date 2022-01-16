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

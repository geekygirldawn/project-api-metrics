# Project Api Metrics

This repo contains a few Python scripts that query the GitHub API to gather
metrics related to project health and other activities.

I am also using this repo as I learn how to use the GitHub GraphQL API.

## GraphQL API Scripts

The first 2 scripts in this repo demonstrate the difference in speed and
rate limits between the GitHub REST API and the GraphQL API. The original
REST script took hours to run across our 60+ GitHub orgs and had to be
slowed down to avoid hitting the rate limit, while the GraphQL version, 
which gathers the same data, runs in less than 15 minutes without hitting
any rate limits.

    repo_activity.py
    repo_activity_REST.py

Note: These scripts gather names and email addresses of 
committers, which we use to help us find a contact within VMware if we 
have questions about a repository. Note that the [GitHub Acceptable Use
Policies](https://docs.github.com/en/github/site-policy/github-acceptable-use-policies)
prohibits certain usage of information, and I would encourage you to read 
this policy and not use scripts like these for unethical purposes.

## Contributing

I welcome any suggestions via issues or pull requests! Please have a look
at the [CONTRIBUTING.md](CONTRIBUTING.md) document for more details.

Participation in this project is subject to the 
[Code of Conduct](CODE-OF-CONDUCT.md)

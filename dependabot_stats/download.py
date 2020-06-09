from collections import namedtuple
import csv
import os

from github import Github


PullRequest = namedtuple('PullRequest', ['repo', 'opened_at', 'closed_at', 'is_security'])

github = Github(os.environ['GITHUB_TOKEN'])



def download_repos(user, topic):
    query = f'user:{user} topic:{topic}'
    return [repo.name for repo in github.search_repositories(query=query)]


def download_pull_requests(user, repos):
    query = f'user:{user} author:app/dependabot author:app/dependabot-preview is:pr is:closed'

    for issue in github.search_issues(query=query):
        if issue.repository.name not in repos:
            continue

        pull_request = issue.as_pull_request()
        is_security = any(label.name == 'security' for label in pull_request.labels)
        yield PullRequest(issue.repository.name, pull_request.created_at, pull_request.closed_at, is_security)


def write_results(pull_requests, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['repo', 'opened_at', 'closed_at', 'is_security'])

        writer.writeheader()

        for pull_request in pull_requests:
            writer.writerow({
                'repo': pull_request.repo,
                'opened_at': pull_request.opened_at.isoformat(),
                'closed_at': pull_request.closed_at.isoformat(),
                'is_security': 'true' if pull_request.is_security else 'false',
            })


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--user', default='alphagov')
    parser.add_argument('--topic', default='govuk')
    parser.add_argument('--output', default='data.csv')

    args = parser.parse_args()

    repos = download_repos(args.user, args.topic)
    pull_requests = download_pull_requests(args.user, repos)
    write_results(pull_requests, args.output)
class GitHubTool:
    '''
    Placeholder for GitHub API operations:
    - create issue
    - assign issue to Copilot
    - watch pull request
    - commit files
    '''
    name = "github"

    def run(self, action: str, **kwargs):
        return {
            "ok": False,
            "message": "GitHubTool is a placeholder. Wire this to PyGithub or requests.",
            "action": action,
            "kwargs": kwargs,
        }

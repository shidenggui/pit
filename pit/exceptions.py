class PitError(Exception):
    pass


class InvalidBranchName(PitError):
    def __init__(self, branch_name: str):
        self.branch_name = branch_name

    def __str__(self):
        return f"fatal: '{self.branch_name}' is not a valid branch name."


class BranchAlreadyExists(PitError):
    def __init__(self, branch_name: str):
        self.branch_name = branch_name

    def __str__(self):
        return f"fatal: A branch named '{self.branch_name}' already exists."


class InvalidRevision(PitError):
    def __init__(self, revision: str):
        self.revision = revision

    def __str__(self):
        return f"fatal: Not a valid object name: {self.revision}."


class UnknownRevision(PitError):
    def __init__(self, revision: str):
        self.revision = revision

    def __str__(self):
        return f"""fatal: ambiguous argument '{self.revision}': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'"""


class AmbiguousRevision(PitError):
    def __init__(self, revision: str):
        self.revision = revision

    def __str__(self):
        return f"""error: short SHA1 {self.revision} is ambiguous 
fatal: Not a valid object name: '{self.revision}'"""


class CheckoutConflict(PitError):
    def __init__(self, conflicts: list[str]):
        self.conflicts = conflicts

    def __str__(self):
        files = "\n".join([f"    {path}" for path in self.conflicts])
        return f"""error: The following untracked working tree files would be overwritten by checkout:
{files}
Please move or remove them before you switch branches.
Aborting"""

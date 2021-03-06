class CommandError(Exception):
    def __init__(self, message, expire_in=0):
        self.message = message
        self.expire_in = expire_in

class ExtractionError(Exception):
    def __init__(self, message):
        self.message = message

class PermissionsError(CommandError):
    def __init__(self, reason, expire_in=0):
        self.reason = reason
        self.expire_in = expire_in
        self.message = "You don't have permission to use that command.\nReason: " + reason

class HelpfulError(Exception):
    def __init__(self, issue, solution, expire_in=0):
        self.issue = issue
        self.solution = solution
        self.expire_in = expire_in
        self.message = self._construct_msg()

    def _construct_msg(self):
        return ("\n"
            "An error has occured.\n"
            "  Cause: {}\n"
            "  Solution: {}\n"
            ).format(self.issue, self.solution)

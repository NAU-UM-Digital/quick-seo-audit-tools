from ...helpers.requests import *

# add subparser for import to __main__
def add(subparsers):
    command_string = "custom-headers"
    feature_status = "REFACTORING IN PROGRESS"
    description = "customize request headers with flags"
    
    new_subparser = subparsers.add_parser(command_string, help=f"[{feature_status}] {description}")
    new_subparser.add_argument("destination")
    new_subparser.add_argument("--email", metavar="STRING", action="store", help="add email to response headers", default=False)
    new_subparser.add_argument("--user-agent", metavar="STRING", action="store", help="customize user-agent in response headers", default=False)
    new_subparser.set_defaults(func=testAppRequestGet)

    return new_subparser


def testAppRequestGet(args):
    appRequestGet(args.destination, userAgent=args.user_agent, email=args.email)

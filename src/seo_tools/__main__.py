import argparse
from .helpers import globals
from . import subparsers as new_subparsers

# Initialize the argument parser
def init_args():

    parser = argparse.ArgumentParser(
        "seo-tools"
    )

    # Add global arguments to the parser
    general = parser.add_argument_group("global flags")
    general.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress response text"
    )
    general.add_argument(
        "--debug",
        action="store_true",
        help="show errors on failure"
    )

    # Add subparsers imported and registered above in array
    subparsers = parser.add_subparsers(
        title="cli tools for SEO auditing"
    )
    for new_subparser in new_subparsers.all_subparsers_array:
        new_subparser.add(subparsers)
        

    args = parser.parse_args()
    globals.args = args
    return args



def main_cli():
    global args
    args = init_args()

    if args.debug is True:
        args.func(args)
    else:
        try:
            args.func(args)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

if __name__ == '__main__':
    main_cli()
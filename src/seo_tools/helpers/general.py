from . import globals

def cliPrint(input, introDash=True):

    if globals.args.quiet is False:
        if introDash is True:
            print("--",str(input))
        else:
            print(str(input))
      
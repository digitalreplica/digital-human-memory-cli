#!/usr/bin/env python3
import argparse
import subprocess
import os
import uuid

##### Globals #####
CLI_NAME = 'hdm'
COMMAND_HELP = {
    "help": "Show help",
    "guid": "Generates a random guid"
}

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("command", help="HumanDigitalMemory command", nargs='*')
args = parser.parse_args()

# Setup CLI
cwd = os.getcwd()
prompt = f"{CLI_NAME} ({cwd}) >"

# Loop over commands
while True:
    # Pull from command line, or read from STDIN
    command = None
    command_args = None
    if args.command:
        command = args.command.pop(0)
        command_args = args.command
    else:
        print("Enter your name:")
        x = input()
        print("Hello ", x)

        print(command)


# guid
if args.command == "guid":
    guid = str(uuid.uuid4())
    subprocess.run("pbcopy", universal_newlines=True, input=guid)

#!/usr/bin/env python2.7
import subprocess
import os
from os import getuid
from contextlib import contextmanager
import glob
import time
from configobj import ConfigObj
from validate import Validator
from plumbum.machines.paramiko_machine import ParamikoMachine


class Cd:
    """Context manager for changing the current working directory"""
    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = ''

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


# Path to configuration file
global CONFIGURATION_FILE_DIRECTORY
CONFIGURATION_FILE_DIRECTORY = './configs/'

# Other variables
verbose = True


#Enables you to remotely connect to a server
def connect_to_server(name, host, user, path):
    print('Connecting to "'+name+'" ...\n')
    command = 'ssh-keyscan ' + host + ' >> ' + SSH_KEY_PATH + 'known_hosts'
    subprocess.call(command, shell=True)
    remote = ParamikoMachine(host, user=user, keyfile=path)
    return remote


#Enables you to remotely disconnect from the server you previously connected to
def disconnect_from_server(rem, connection_name):
    print('Closing "'+connection_name+'" connection ...')
    rem.close


# Prompt the user to input an integer between 0 and number of files - 1
# If anything else is inputted then re-prompt user
# In the end returns the value that the user choose
def prompt(file_choice, dictionary, number_of_item_to_chose_form):
    while (isinstance(file_choice, int) is not True) or ((file_choice >= 0) is not True) \
            or ((file_choice <= number_of_item_to_chose_form) is not True):
        file_choice = raw_input('\nPlease select your choice [0 - ' + str(number_of_item_to_chose_form) + ']: ')

        file_choice = int(file_choice)

        if file_choice < 0:
            print("Input cannot be negative.")
        if file_choice > number_of_item_to_chose_form:
            print("Input must be smaller than " + str(number_of_item_to_chose_form) + ".")
        if isinstance(file_choice, int) is False:
            print("Input must be an Integer.")

    print('You have chosen: ' + dictionary[file_choice])

    return dictionary[file_choice]


# Prompts user with choices of configuration files
def prompt_configuration_file():
    i = -1
    file_list = glob.glob(CONFIGURATION_FILE_DIRECTORY+"*.ini")

    print('### Configuration')
    print('## Chose configuration file')
    for filename in file_list:
        i += 1
        print("#" + filename + " [" + str(i) + "]")

    list_of_indices = [x for x in range(0, i+1)]
    dictionary_of_file_paths = dict(zip(list_of_indices, file_list))
    file_choice = ''

    input_result = prompt(file_choice, dictionary_of_file_paths, i)

    return input_result


def prompt_server():
    server_choice = ''
    list_of_builds = CONNECTION_TO_FILE['builds'].keys()
    number_of_builds = len(list_of_builds)

    list_of_indices = [x for x in range(0, number_of_builds+1)]
    dictionary_of_builds = dict(zip(list_of_indices, list_of_builds))
    print('### Configuration')
    print('## Chose server you want to build to')

    if validate_configuration_file(CONNECTION_TO_FILE):
        for key, server in dictionary_of_builds.iteritems():
            set_server_variables(server)

            # If verbose option turn on print out information on environment
            if verbose:
                print("# " + server + " [" + str(key) + "]\n")
                print("\t Name: " + SERVER_NAME)
                print("\t Host: " + SERVER_HOST)
                print("\t User: " + SERVER_USER)
                print("\t SSH Key Path: " + SSH_KEY_PATH)
                print("\t Source build path : " + SOURCE_BUILD_PATH)
                print("\t Destination build path : " + DESTINATION_BUILD_PATH + "\n\n")

        input_result = prompt(server_choice, dictionary_of_builds, number_of_builds-1)

        return input_result
    else:
        # If the configuration file is not valid then inform user and exit
        print("Configuration file not valid.\n")
        return False


def prompt_to_continue():
    continue_answer = raw_input("Would you like to continue building to "
                                "" + SERVER + " or would you like to cancel this build ? [yes or no]: ")
    return continue_answer


def prompt_to_write_commit_message():
    commit_message = raw_input("Commit message: ")
    return commit_message


def set_server_variables(server):
    # SSH Server credentials
    global SERVER_NAME
    global SERVER_HOST
    global SERVER_USER
    global SSH_KEY_PATH
    global SOURCE_BUILD_PATH
    global DESTINATION_BUILD_PATH

    SERVER_NAME = CONNECTION_TO_FILE['builds'][server]['server_name']
    SERVER_HOST = CONNECTION_TO_FILE['builds'][server]['server_host']
    SERVER_USER = CONNECTION_TO_FILE['builds'][server]['server_user']
    SSH_KEY_PATH = CONNECTION_TO_FILE['builds'][server]['ssh_key_path']
    SOURCE_BUILD_PATH = CONNECTION_TO_FILE['builds'][server]['source_build_path']
    DESTINATION_BUILD_PATH = CONNECTION_TO_FILE['builds'][server]['destination_build_path']


# Connect to the configuration file, the configuration file is structured by the configspec.ini
# file which dictates the type and specifics of each argument
def connect_to_configuration():
    return ConfigObj(CONFIGURATION_FILE_PATH, configspec='configspec.ini')


def validate_configuration_file(conf):
    validator = Validator()
    return conf.validate(validator)


def get_configuration_from_user():

    # Prompt the user for which configuration he wants to use, all configuration files
    # that will be considered will be in ./configs by default
    global CONFIGURATION_FILE_PATH
    CONFIGURATION_FILE_PATH = prompt_configuration_file()

    # Connection to configuration file
    global CONNECTION_TO_FILE
    CONNECTION_TO_FILE = connect_to_configuration()

    # Prompt the user for which server he wants to use to build to, all servers
    # that will be considered will be in the configuration file previously chosen
    global SERVER
    SERVER = prompt_server()
    if SERVER is False:
        exit(0)
    else:
        set_server_variables(SERVER)


def banner():
    print("#### Magento build tool - by nabello and ijanders\n")


# Create new snapshot of site
def create_snapshot():
    print('## Create snapshot')

    set_server_variables(SERVER)

    answer = ''
    timestamp = time.time()
    # commit_message = 'Snapshot of ' + SERVER + ' at ' + str(timestamp)
    commands = dict()
    commands[0] = "modman update-all --force --copy"
    commands[1] = "git add ."
    commands[2] = "git status"

    # Navigate to Magento root folder
    with Cd(SOURCE_BUILD_PATH):
        for key, command in commands.iteritems():
            print("# " + command)
            subprocess.call(command, shell=True)

        while answer != 'yes' or answer != 'no':
            answer = prompt_to_continue()

            if answer == 'yes':
                commit_message = prompt_to_write_commit_message()
                yes = "git commit -m '" + commit_message + "'"
                push = "git push origin"
                print("# " + yes)

                subprocess.call(yes, shell=True)
                print("# " + push)
                subprocess.call(push, shell=True)
                break

            if answer == 'no':
                no = "git reset --hard HEAD"
                print("# " + no)
                subprocess.call(no, shell=True)

                print("Exiting ...\n")
                exit(0)
            else:
                print("Please enter yes or no as your answer.")


def deploy_snapshot():
    print('## Deploy snapshot')

    #Connect to server we want to deploy snapshot
    remote = connect_to_server(SERVER_NAME, SERVER_HOST, SERVER_USER, SSH_KEY_PATH)

    # Pull change in destination root folder
    with remote.cwd(DESTINATION_BUILD_PATH):
        print("# git pull")
        remote['git']['pull']()

    #Disconnect from server we previously connected to deploy snapshot
    disconnect_from_server(remote, SERVER_NAME)


def build():
    print('### Build')

    # Create snapshot
    create_snapshot()

    #Deploy to server
    deploy_snapshot()


def main():
    ### Banner
    banner()

    ### CONFIGURATION: Get and validate configuration file by prompting the user
    get_configuration_from_user()

    ### BUILD
    build()


if __name__ == '__main__':
    main()
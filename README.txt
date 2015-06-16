## Author: nabello
## Git URL:
## Summary: This project is a build tool for Magento. It contains a main script and must be configured as the
## sample configuration file provided in config.ini.sample



#################
# Configuration #
########################################################################################################################
# The configuration file is structured in a specific way, you must follow and respect the structure to insure validation
# and proper use of it. Additionally you must name your configuration file with the .ini extension in order to be able
# to select it when you use the script. In order to use the configuration file it must live in the configs directory.
# Use the config.ini.sample file provided in the configs directory, it contains a configuration example you can
# inspire yourself of it to build your own configuration file.

# The following configuration file contains the mandatory information to enable this tool to create a snapshot and
# remotely deploy it to a given server.

# server_name: This parameter must at least be 3 characters long and smaller than 30 characters. It is used to label the
# remote server of snapshot deployment. It's default value is "Default_Name".

# server_host: This parameter must be an IP address, it is used to provide a destination IP address for the remote
# server that you will use for snapshot deployment. It's default value is 127.0.0.1

# server_user: This parameter must at least be 1 character long and smaller than 10 characters. It is used to provide a
# user with which you will log into the remote server that you will use for snapshot deployment. It's default value is
# "root".

# ssh_key_path: This parameter must be at least 1 character long, there is no limit to how long it can be. It is used
# to provide a path to the ssh key for authentication with the remote server that you will use for snapshot deployment.
# It's default value is "~/.ssh/"

# source_build_path: The parameter must be at least 1 character long, there is no limit to how long it can be. It is
# used to provide a source path to create a snapshot on the local server. It's default value is "~/var/www/magento"

# destination_build_path: The parameter must be at least 1 character long, there is no limit to how long it can be. It
# is used to provide a source path to deploy to on the remote server that you will use for snapshot deployment. It's
# default value is "/var/www/magento"

# Default values are used when the parameter name is omitted
# e.g. [[example_build1]]
#               server_name = "August Locks"
#               ssh_key_path = "~/.ssh"
#
# is equivalent to:
#       [[example_build1]]
#               server_name = "August Locks"
#               server_host = "127.0.0.1"
#               server_user = "root"
#               ssh_key_path = "~/.ssh"
#               source_build_path = "/var/www/magento"
#               destination_build_path = "/var/www/magento"

#You can add as much "Build" configurations as following
# e.g. [builds]
#
#       [[example_build1]]
#           server_name = "August Locks"
#           server_host = "127.0.0.1"
#           server_user = "root"
#           ssh_key_path = "~/.ssh"
#           source_build_path = "/var/www/magento"
#           destination_build_path = "/var/www/magento"
#
#       [[example_build2]]
#           ...
#
#       [[example_build3]]
#           ...

# The file configspec.ini must not be edited as this file defines the structure of a configuration file. Editing this
# file will result in the tool no longer working properly.



####################
# Script Execution #
########################################################################################################################
# The tool can be started by executing the build.py script as follows:
# e.g.
# ./build
#
# Then all you need to do is follow the prompts and answer to your need.
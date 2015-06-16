#!/usr/bin/env python2.7

import subprocess
import sys
import string
from os import chdir
from configobj import ConfigObj
# from plumbum import local, FG, cmd
from plumbum.machines.paramiko_machine import ParamikoMachine
import json
import time

execution_path = "./script/deploy-client/"
checks_path = execution_path + "checks/"


def returnArgX(cmd, x):
    param = string.split(cmd, ' ')
    if len(param) >= (x+1):
        return param[x]
    else:
        return None


def execute(command):
    cmd_name = returnArgX(command, 0)
    args = command.split(" ")
    if 'cd' == cmd_name:
        chdir(returnArgX(command, 1))
    elif 'server' == cmd_name:
        confInfo(command)
    elif 'client' == cmd_name:
        confInfo(command)
    elif 'graphite' == cmd_name:
        confInfo(command)
    elif 'install' == cmd_name:
        cmd_remote(command)
    elif 'sendmail' == cmd_name:
        if len(args)==2:
            sendmail(args[1])
        else:
            print("You have too much or not enough parameters.")
    else:
        subprocess.call(command, shell=True)


def prompt():
    cmd = raw_input('@ -> : ')
    if cmd != 'exit' and cmd != 'quit':
        execute(cmd)
    else:
        sys.exit("\nCiao bello!\n")


def confInfo(cmd):
    cmdArg1 = returnArgX(cmd, 1)
    mch = returnArgX(cmd, 0)

    if cmdArg1=='ls':
        displaySection(get_sections(mch))
    elif cmdArg1=='info':
        displaySectionInfo(get_sections(mch))
    elif cmdArg1=='type':
        displaySectionType(get_sections(mch))
    elif cmdArg1=='crt':
        create_client_server(mch, cmd)
    elif cmdArg1=='mdf':
        mdfSection(get_sections(mch),mch)
    elif cmdArg1=='del':
        delSection(get_sections(mch),mch)
    else:
        print('You must specify a valid action!')


def to_shortcut(machine):
    if machine == 'server':
        return 'sensu-servers'
    elif machine == 'client':
        return 'sensu-clients'

    elif machine == 'graphite':
        return 'graphite-servers'


def get_mainconf_connection():
    return ConfigObj(execution_path+'mainconf.clone')


def crtHipchatSection(api, room, hipfrom):
    room = room.replace("_", " ")
    new_section = {'api': api,'room': room,'from': hipfrom}
    return new_section


def create_client_server(mch, command):
    command = command.split(" ")
    if len(command) != 11:
        project_name = raw_input('projectname=')
        server_name = raw_input('servername=')
        ip = raw_input('ip=')
        user = raw_input('user=')
        key_name = raw_input('keyname=')
        tags = raw_input('tags=')
        api = raw_input('HipchatApi=')
        room = raw_input('HipchatRoom=')
        hipfrom = raw_input('HipchatFrom=')
    else:
        project_name = command[2]
        server_name = command[3]
        ip = command[4]
        user = command[5]
        key_name = command[6]
        tags = command[7]
        api = command[8]
        room = command[9]
        hipfrom = command[10]
        #e.g. client crt test 192.168.90.222 root test.pem cq5
    
    config = get_mainconf_connection()
    hipchat = crtHipchatSection(api, room, hipfrom)

    # If the project section was previously created then simply add a server section to it
    if project_name in config['machines'][to_shortcut(mch)]:
        new_server = {'ip': ip, 'user': user, 'keyname': key_name, 'tags': tags}
        #Create server section
        config['machines'][to_shortcut(mch)][project_name][server_name] = new_server

    # Else Create the project section before adding the server section to it
    else:
        new_server = {server_name: {'ip': ip,'user': user,'keyname': key_name,'tags': tags}}
        #Create project section
        config['machines'][to_shortcut(mch)][project_name] = new_server

    # Create hipchat section
    config['machines'][to_shortcut(mch)][project_name][server_name]['hipchat'] = hipchat
    config.write()


def mdfSection(args, mch):
    config = get_mainconf_connection()
    execute(mch+' ls')
    dict=getNames(args)
    choice = raw_input('Wich machine do you want to modify:')
    oldname = dict[str(choice)]
    thing = config['machines'][to_shortcut(mch)][oldname]
    print(to_shortcut(mch))
    for key,value in thing.iteritems():
        print('\t'+key+'='+value)
    name = raw_input('name=')
    ip = raw_input('ip=')
    user = raw_input('user=')
    keyname = raw_input('keyname=')
    type= raw_input('type=')
    
    newSection = {'ip':ip,'user':user,'keyname':keyname,'type':type}
    del config['machines'][to_shortcut(mch)][oldname]
    config['machines'][to_shortcut(mch)][name]=newSection
    config.write()


def delSection(args, mch):
    config = get_mainconf_connection()
    execute(mch+' ls')
    dict = getNames(args)
    choice = raw_input('Wich machine do you want to modify:')
    oldname = dict[str(choice)]
    thing = config['machines'][to_shortcut(mch)][oldname]
    print(to_shortcut(mch))
    for key,value in thing.iteritems():
        if key == 'name':
            oldname=value
        print('\t'+key+'='+value)
    delete = raw_input('Are you sure you want to delete this machine ? [y/n] : ')
    
    while True:
        if delete == 'y':
            delete = True
            break
        elif delete == 'n':
            delete = False
            break
        else:
            delete = raw_input('I did\'t undestand that ! Are you sure you want to delete this machine ? [y/n] : ')
    if delete:
        del config['machines'][to_shortcut(mch)][oldname]
        config.write()
    elif not delete:
        print('Deletion aborted !')
    else: 
        print('delSection() error.')


def get_sections(mch):
    config = get_mainconf_connection()
    machines = config['machines']

    if mch == 'server':
        servers = machines['sensu-servers']
        return servers
    elif mch == 'client' or mch == 'checks':
        clients = machines['sensu-clients']
        return clients
    elif mch == 'graphite':
        graphites = machines['graphite-servers']
        return graphites
    else:
        print('get_sections() error.')


def displaySection(args):
    i=0
    for arg in args:
        i += 1
        print(str(i)+' : '+arg)


def displaySectionInfo(args):
    for key,arg in args.iteritems():
        print(createBnr(key,'top',25,3))
        for key,value in arg.iteritems():
            print(key+' = '+value)
        print(createBnr('########','bottom',25,3))



def displaySectionType(args):
    dict = getDictOfMchByOneParamManyValues(args,'type')
    for key,value in dict.iteritems():
        print(createBnr(key,'top',25,3))
        for i in value:
            print(i)
        print(createBnr('########','bottom',25,3))


def getNames(args):
    names={}
    i=0
    for arg in args:
        i+=1
        names[str(i)]=arg
    return names


def getParam(args,param):
    type=set()
    for key1,value1 in args.iteritems():
        for key2,value2 in value1.iteritems():
            if key2==param:
                type.add(value2)
    return type


def getMachineByParam(args,param, value0):
    ls=[]    
    for key1,value1 in args.iteritems():
        for key2,value2 in value1.iteritems():
            if key2==param:
                if value2==value0:
                    ls.append(key1)
    return ls


def getDictOfMchByOneParamManyValues(args,param):
    types = getParam(args,'type')
    dictionary = {}
    for i in types:
        dictionary[i] = getMachineByParam(args,param, i)

    return dictionary


def get_dict_of_mch_info_by_one_param_one_value(args, param, value0=None):
    ls = []
    dictionary = {}
    if value0 is not None:
        if param == 'name':
            for key1,value1 in args.iteritems():
                if key1 == value0:
                    dictionary[key1] = value1
        else:
            for key1,value1 in args.iteritems():
                for key2,value2 in value1.iteritems():
                    if key2 == param:
                        if value2 == value0:
                            dictionary[key1] = value1

    elif value0 is None:
        dictionary = get_sections(param)
    return dictionary


def getMainPathsLocal(type):
    config = get_mainconf_connection()
    main = config['main']['paths']['local'][type]
    return main


def get_mch_selection(cmd_type, project_name, selection_type, selection_value):
    dictionary = {}
    args = get_sections(cmd_type)
    args = args[project_name]

    if selection_type:
        dictionary = get_dict_of_mch_info_by_one_param_one_value(args, selection_type, selection_value)
    else:
        dictionary = get_dict_of_mch_info_by_one_param_one_value(args, cmd_type, selection_value)

    return dictionary


#Install Sensu server, client or graphite
def cmd_remote(command):
    cmd_main = returnArgX(command, 0)
    cmd_type = returnArgX(command, 1)
    project_name = returnArgX(command, 2)
    selection_type = returnArgX(command, 3)
    selection_value = returnArgX(command, 4)
    print(selection_value)
    connection_dict = get_mch_selection(cmd_type, project_name, selection_type, selection_value)

    #Parse through the dictionary for the connection configuration
    for server_name, value1 in connection_dict.iteritems():
        for key2, value2 in value1.iteritems():
            if key2 == 'ip':
                host = value2
            elif key2 == 'user':
                user = value2
            elif key2 == 'keyname':
                path = getMainPathsLocal('ssh_keys') + value2
            elif key2 == 'tags':
                tags = value2.split('/')
            elif key2 == 'hipchat':
                for key3, value3 in value2.iteritems():
                    if key3 == 'api':
                        hipchat_api = value3
                    elif key3 == 'room':
                        hipchat_room = value3
                    elif key3 == 'from':
                        hipchat_from = value3

    if cmd_main == 'install':

        if cmd_type == 'client':
            install_client(project_name, server_name, host, user, path, hipchat_api, hipchat_room, hipchat_from, cmd_type)

        elif cmd_type == 'checks':
            install_checks(server_name, host, user, path, tags)

        else:
            print("DEBUG: Wrong command type ...")

    elif cmd_main == 'deploy':
        deploy(dict, cmd_type)

    else:
        print("Command syntax incomplete or nonexistent.")


def getReportDetails(j_file, value):
    json_file = open(j_file, "r")
    data = json.load(json_file)
    json_file.close()

    tmp = data["details"][value]
    return tmp


def getReportGlobal(j_file):
    json_file = open(j_file, "r")
    data = json.load(json_file)
    json_file.close()

    tmp = data["global"]
    return tmp


def install_client(project_name, server_name, host, user, path, hipchat_api, hipchat_room, hipchat_from, cmd_type):
    config = get_mainconf_connection()
    server = config['machines']['sensu-servers']['sensu-server1']
    server_ip = server['ip']
    remote = server['remote']
    key_name = server['keyname']
    server_key_path = getMainPathsLocal('ssh_keys') + key_name

    #***Add vhost on rabbitmq server***
    print('Adding vhost ...')
    rpc_vhost = "/" + project_name
    rpc_user = project_name
    rpc_pw = 'none9999'
    if remote == '1':
        server = connection(server_ip, server_ip, "root", server_key_path)
        server["rabbitmqctl"]["add_vhost"][rpc_vhost]()
        server["rabbitmqctl"]["add_user"][rpc_user][rpc_pw]()
        server["rabbitmqctl"]["set_permissions"]["-p"][rpc_vhost][rpc_user][".*"][".*"][".*"]()
        disconnect(server, 'server')
    else:
        execute("rabbitmqctl add_vhost "+rpc_vhost)
        execute("rabbitmqctl add_user " + rpc_user + " " + rpc_pw)
        execute('rabbitmqctl set_permissions -p ' + rpc_vhost + ' ' + rpc_user + ' ".*" ".*" ".*"')
    print('done.\n')
    #*******************************

    #Add to known_host file
    execute('ssh-keyscan ' + host + ' >> ' + getMainPathsLocal('ssh_keys') + 'known_hosts')
    rem = connection(server_name, host, user, path)
    #*******************************

    #***UPLOAD and RUN test script***
    print('Uploading test script ...')
    rem.upload(execution_path + '/test_machine.py', '/home/')
    print('done.\n')

    print('Running test script ...')
    rem["chmod"]["755"]["/home/test_machine.py"]()
    with rem.cwd('/home'):
        rem['/home/test_machine.py ' + server_name]()
    print('done.\n')
    #*******************************

    #***DOWNLOAD report***
    print('Downloading report ...')
    rem.download('/home/' + server_name + '_test-report.json', execution_path + '/test-reports/')
    with rem.cwd('/home'):
        rem['rm']['/home/' + server_name + '_test-report.json']()
        rem['rm']['/home/test_machine.py']()
    print('done.\n')
    #*******************************

    global_report = getReportGlobal(execution_path + 'test-reports/' + server_name + '_test-report.json')
    osdistro = getReportDetails(execution_path + '/test-reports/' + server_name + '_test-report.json', 'os')

    #***Creating installconf***
    print('Creating installconf ...')
    create_installconf(osdistro, project_name, host, server_ip, rpc_user, rpc_vhost, hipchat_api, hipchat_room, hipchat_from)
    #*******************************

    #***Create installer tar***
    execute("rm " + execution_path + "installer/client/client.tar")
    execute("tar --directory " + execution_path + "installer/ -cf client.tar client ; mv client.tar " + execution_path +
            "installer/client/")
    #*******************************

    #osdistro value can be centos, ubuntu or rhel
    if global_report == '0':

        #***Deploying installation***
        print('Uploading install scripts to a ' + osdistro + ' machine ...')
        #rem.upload(execution_path+osdistro+'/install.py', '/home/')
        rem.upload(execution_path + '/installer/client/client.tar', '/home/')
        rem.upload(execution_path + '/rpc/client_cert.pem', '/home/')
        rem.upload(execution_path + '/rpc/client_key.pem', '/home/')
        rem.upload(execution_path + '/rpc/cacert.pem', '/home/')
        #rem.upload(execution_path+osdistro+'/installconf', '/home/')
        print('done.\n')

        rem["tar"]["-xf"]["/home/client.tar"]["-C"]["/home/"]()
        #rem["chmod"]["755"]["/home/install.py"]()
        rem["chmod"]["-R"]["755"]["/home/client/"]()
        print('Installing ' + cmd_type + ' on ' + server_name + ' ...')
        with rem.cwd('/home/client'):
            rem['/home/client/install_client.py']()
        print('Cleaning up remote machine.\n')
        #rem['rm']['-R']['/home/client']()
        #rem['rm']['-R']['/home/client.tar']()
        print('done.\n')
        #*******************************

        #Init checks (Update: git pull and tar them)
        print("Initialising checks ...")
        default_tags = ["System"]
        init_checks(default_tags)

        print('Setup Checks ...')
        #Deploy the standalone checks, we are currently deploying everything standalone
        for tag in default_tags:
            print('Deploying standalone ' + tag + ' checks...')
            setup_checks(rem, tag, True)

    disconnect(rem, server_name)

    print('Sending Email...')
    sendmail(server_name, osdistro)
    print('Done.')

    print("Cleaning up provisioning...")
    execute("rm " + execution_path + "installer/client/installconf")
    print('Done.')


def create_installconf(os, client_host_name, client_address, rabbitmq_host, rpc_user, rpc_vhost,
                       hipchat_api, hipchat_room, hipchat_from):
        execute("cp " + execution_path + "installer/client/installconf.default" + " "
                + execution_path+"installer/client/installconf")

        config = ConfigObj(execution_path + 'installer/client/' + 'installconf')
        cmd = {'ostype': os, 'clienthostname': client_host_name, 'clientaddr': client_address}

        config['install']['cmd'] = cmd

        config['install']['rabbitmq']['host'] = rabbitmq_host

        config['install']['rpc']['username'] = rpc_user
        config['install']['rpc']['vhost'] = rpc_vhost

        hipchat = {'api': hipchat_api,'room': hipchat_room,'from': hipchat_from}
        config['install']['hipchat'] = hipchat
        config.write()


def init_checks(tags):
        #Clear tared-checks and tared-json directories
        print("Updating and tarring checks/json files ...")
        execute("rm -rf "+checks_path+"tared-checks/*")
        execute("rm -rf "+checks_path+"tared-json/*")
        print("Finished removing old tars")
        #TODO Uncomment after git repo is created
        #execute("git pull")

        for tag in tags:
            #Tar checks
            print("tar --directory "+checks_path+"raw-checks/ -cf " + tag + "-checks.tar " + tag + "-checks ; mv "
                  + tag + "-checks.tar "+checks_path+"tared-checks/")
            execute("tar --directory "+checks_path+"raw-checks/ -cf " + tag + "-checks.tar " + tag + "-checks ; mv "
                    + tag + "-checks.tar "+checks_path+"tared-checks/")

            #Tar json
            print("tar --directory " + checks_path + "raw-json/ -cf " + tag + "-json.tar " + tag + "-json ; mv " + tag
                  + "-json.tar " + checks_path + "tared-json/")
            execute("tar --directory " + checks_path + "raw-json/ -cf " + tag + "-json.tar " + tag + "-json ; mv " + tag
                    + "-json.tar " + checks_path + "tared-json/")


def setup_checks(rem, check_type, standalone=False, remote_plugin_path='/etc/sensu/plugins/', remote_conf_path='/etc/sensu/conf.d/'):
    if standalone:
        rem.upload(checks_path+'tared-json/'+check_type+'-json.tar', remote_conf_path)
        with rem.cwd(remote_conf_path):
            #JSON Files
            rem['tar']['-xf'][check_type+'-json.tar']()
            rem['rm'][check_type+'-json.tar']()
            rem["chmod"]["-R"]["755"][check_type+"-json"]()
            rem["mv"][check_type+"-json"][check_type]()
                         
    rem.upload(checks_path+'tared-checks/'+check_type+'-checks.tar', remote_plugin_path)
    with rem.cwd(remote_plugin_path):
        rem['tar']['-xf'][check_type+'-checks.tar']()
        rem['rm'][check_type+'-checks.tar']()
        rem["chmod"]["-R"]["755"][check_type+"-checks"]()
        rem["mv"][check_type+"-checks"][check_type]()
        rem["service"]["sensu-client"]["restart"]()


def install_checks(server_name, host, user, path, tags):
    rem = connection(server_name, host, user, path)
    time_sleeping = 0
    sleep_time = 3000
    max_time_sleeping = 60000

    # while rem['ps']['-e']['|']['grep']['sensu-client'] != 0:
    #     time.sleep(sleep_time)
    #     time_sleeping += sleep_time
    #     print(time_sleeping)
    #     if time_sleeping > max_time_sleeping:
    #         exit()

    #Init checks (Update: git pull and tar them)
    print("Initialising checks ...")
    init_checks(tags)

    print('Setup Checks ...')
    #Deploy the standalone checks
    for tag in tags:
        print('Deploying standalone ' + tag + ' checks...')
        setup_checks(rem, tag, True)

    disconnect(rem, server_name)


def deploy(dict, cmd_type):
    for key1, value1 in dict.iteritems():
        for key2, value2 in value1.iteritems():
            if key2 == 'ip':
                host = value2
            elif key2 == 'user':
                user = value2
            elif key2 == 'keyname':
                path = getMainPathsLocal('ssh_keys') + value2
        rem = connection(key1, host, user, path)
        disconnect(rem, key1)


def connection(name, host, user, path):
    print('Connecting to "'+name+'" ...\n')
    remote = ParamikoMachine(host, user=user, keyfile=path)
    return remote


def disconnect(rem, str):
    print('Closing "'+str+'" connection ...')
    rem.close


def createBnr(msg,position,Width,Heigth):
    msgSize = len(msg)
    width = Width
    heigth = Heigth
    topBottom = ''
    middle  = ''

    if msgSize>= width:
        width = width + 30

    halfMsgSize = msgSize / 2
    halfWidth = width/2
    indexStartMsg = halfWidth - halfMsgSize

    for i in range(1,(width-msgSize)) :
        if i == 1 or i == (width-msgSize-1):
            topBottom = topBottom+'*'
            middle = middle+'*'
        elif i == (indexStartMsg):
            for j in range(0,msgSize):
                topBottom = topBottom+'*'
                middle = middle+msg[j]
        else:
            topBottom += '*'
            middle += ' '

    if position == 'top':
        return '\n\n\n'+topBottom+'\n'+middle+'\n'+topBottom+'\n'
    elif position == 'bottom':
        return '\n'+topBottom+'\n'+middle+'\n'+topBottom+'\n\n\n'

    return '\n'+topBottom+'\n'+middle+'\n'+topBottom+'\n'


def sendmail(sensu_name, os_distro):
    subprocess.call(execution_path+'sendmail.py '+sensu_name+' '+os_distro, shell=True)


def main():
    cmd = ""
    for value in sys.argv[1:]:
        cmd = cmd+value+" "
    
    if len(sys.argv)<2:
        while True:
            prompt()
    else:
        execute(cmd[:-1])
            
            

if __name__ == '__main__':
    main()
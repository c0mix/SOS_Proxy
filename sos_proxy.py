'''
Author: Lorenzo Comi

Takes min. 2 inputs: <network interface to monitor> <source ip to monitor>
Example:$ python sos_proxy.py wlan0 10.42.0.102

Devices configuration example: Internet <-> (eth0) attacker PC + burp (wlan0) <-> Fake hotspot <-> Target Device
'''


import sys
import os
import time
import argparse
import socket
import re
import datetime
import subprocess


available_interfaces = []
domain_list = []
verbose = False
ask = False


def print_welcome():
    print ''
    print 'Welcome in sos_proxy tool!'
    print ''
    print 'sos_proxy facilitate the HTTP interception of non-proxable devices looping through the following actions:\n' \
          '-> Intercept DNS request\n' \
          '-> Resolve the associated domain \n' \
          '-> Create a virtual interface for each domain\n' \
          '-> Update the /etc/hosts file \n' \
          '-> Provide useful information on how to setup your burp proxies'
    print ''
    print 'More info on this technique:\nhttps://portswigger.net/burp/documentation/desktop/tools/proxy/options/invisible'
    print ''


def setup_proxy(viface, real_ip, domain):
    print ''
    print '[INFO] Domain "{}" found! Please create a new burp proxy with the following parameters:'.format(domain)
    print '[INFO] Interface: {0} \tRedirect: {1}'.format(viface, real_ip)
    print ''


def restored_proxy(viface, real_ip, domain):
    print ''
    print '[INFO] Restored proxy for domain "{}" Please check if your burp proxy has the following parameters:'.format(domain)
    print '[INFO] Interface: {0} \tRedirect: {1}'.format(viface, real_ip)
    print ''


def list_interfaces():
    # Use ip to extract network interfaces
    cmd = "ip a | grep mtu | cut -d ':' -f 2 | cut -d ' ' -f2"
    # Use ifconfig to extract network interfaces
    #cmd = "ifconfig | grep fla | cut -d ':' -f 1"
    out = os.popen(cmd).read()
    for interface in out.split('\n'):
        available_interfaces.append(interface)


def check_interface(interface):
    if interface.strip() not in available_interfaces:
        exit('Interface {} not found!'.format(interface))


def check_ip(source_ip):
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", source_ip):
        exit('Invalid IP address: {}'.format(source_ip))


def monitor_dns(interface, source_ip):
    # create a tmux tab to stay stealth and monitor the new domains
    cmd = 'touch /tmp/domains && sudo tmux new -d -s Domain_Monitor "tcpdump -n -i {} udp dst port 53 and src {} -l > /tmp/domains"'.format(interface, source_ip)
    os.system(cmd)
    time.sleep(1)
    # verify if tmux and tcpdump started correctly
    if "Domain_Monitor" not in subprocess.check_output(['sudo tmux list-sessions | grep Domain_Monitor | cut -d ":" -f1'], shell=True):
        print "[ERROR] There was an error starting tmux and/or tcpdump, please verify that the parameters you've entered, such as network interface or ip to monitor, are correct, up and running! Exiting..."
        exit(1)
    print '[INFO] Domain_Monitor correctly started on {0} and IP {1}!'.format(interface, source_ip)


def recursive_read(interface_real, iface_counter=0):
    global ask
    f = open('/tmp/domains', 'r')
    while True:
        try:
            # search for new domains approximately every 10 seconds
            time.sleep(5)
            f.seek(0)
            for line in f.readlines():
                domain = line.split(' ')[-2]
                if check_new(domain):
                    iface_counter += 1
                    if iface_counter == 255:
                        # TODO handle this issue and go on with other interface or with different ip assignation
                        print "[WARN] Maximum IP reached: 255 please change the create_iface settings... Exiting"
                        cleanup(iface_counter, interface_real)

                    real_ip = do_nslookup(domain)
                    if real_ip:
                        if not ask:
                            viface = create_iface(iface_counter, interface_real)
                            edit_hosts(viface, domain, iface_counter)
                            setup_proxy(viface, real_ip, domain[:-1])
                        else:
                            answer = query_yes_no(question='[INFO] Do you want to intercept this domain: {} ?'.format(domain))
                            if answer:
                                viface = create_iface(iface_counter, interface_real)
                                edit_hosts(viface, domain, iface_counter)
                                setup_proxy(viface, real_ip, domain[:-1])
                            elif answer == 'Interrupt':
                                iface_counter -= 1
                                raise KeyboardInterrupt
                            else:
                                iface_counter -= 1
                    else:
                        iface_counter -= 1

        except KeyboardInterrupt:
            print '\n[INFO] KeyboardInterrupt, Clean & Exit procedure started!'
            f.close()
            cleanup(iface_counter, interface_real)
            exit(0)


def edit_hosts(viface, domain, iface_counter):
    if iface_counter == 1:
        # first time here so backup current hosts file
        cmd = 'sudo cp /etc/hosts /etc/hosts.bkp'
        os.system(cmd)
        print '[INFO] Backup /etc/hosts to /etc/hosts.bkp'
        cmd = 'sudo su root -c "echo \'\n# The Following lines are produced by sos_proxy script\' >> /etc/hosts"'
        os.system(cmd)

    # append new line to /etc/hosts
    cmd = 'sudo su root -c "echo \'{0}    {1}\' >> /etc/hosts"'.format(viface, domain)
    os.system(cmd)


def do_nslookup(domain):
    global verbose
    try:
        real_ip = socket.gethostbyname(domain)
        return real_ip
    except:
        if verbose:
            print '[ERROR] It was not possible to resolve the domain: {}'.format(domain)
        return False


def cleanup(iface_counter, interface_real):
    # kill Domain_Monitor tmux session
    cmd = 'sudo tmux list-sessions | grep Domain_Monitor | cut -d ":" -f1 | xargs -n 1 sudo tmux kill-session -t'
    os.system(cmd)

    # delete all virtual interfaces
    while iface_counter > 0:
        #use ip to delete virtual interface
        cmd = 'sudo ip addr del 100.100.100.{1}/32 dev {0}'.format(interface_real, iface_counter)
        # use ifconfig to delete virtual interface
        #cmd = 'sudo ifconfig {0}:{1} down'.format(interface_real, iface_counter)
        os.system(cmd)
        iface_counter -= 1

    # take a copy of the current /etc/hosts?
    if query_yes_no(question='[INFO] Would you like to save the current (modified) hosts file?'):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = 'hosts_{}'.format(timestamp)
        cmd = 'sudo cp /etc/hosts hosts_files/{}'.format(filename)
        os.system(cmd)
        print '[INFO] hosts file saved in folder "hosts_files" as: {}'.format(filename)

    # restore /etc/hosts
    if os.path.isfile('/etc/hosts.bkp'):
        cmd = 'sudo cp /etc/hosts.bkp /etc/hosts'
        os.system(cmd)

    # remove temporary file /tmp/domains
    if os.path.isfile('/tmp/domains'):
        cmd = 'rm /tmp/domains'
        os.system(cmd)


def create_iface(interface_number, interface_real):
    # use ip to create a virtual interface
    cmd = "sudo ip a add dev {1}:{0} 100.100.100.{0}".format(interface_number, interface_real)
    # use ifconfig to create a virtual interface
    #cmd = 'sudo ifconfig {1}:{0} 100.100.100.{0}'.format(interface_number, interface_real)
    os.system(cmd)
    return '100.100.100.{0}'.format(interface_number)


def check_new(domain):
    # check if the new domain is already in the list
    global domain_list
    if domain in domain_list:
        return False
    else:
        domain_list.append(domain)
        return True


def query_yes_no(question, default="yes"):
    # Ask a yes/no question via raw_input() and return their answer.
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("[ERROR] invalid default answer: '{}'".format(default))

    while True:
        try:
            sys.stdout.write(question + prompt)
            choice = raw_input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("[WARN] Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")
        except KeyboardInterrupt:
            return "Interrupt"


def restore_hosts(hosts_file):
    # backup current hosts file
    cmd = 'sudo cp /etc/hosts /etc/hosts.bkp'
    os.system(cmd)

    # restore /etc/hosts
    cmd = 'sudo cp {} /etc/hosts'.format(hosts_file)
    os.system(cmd)


def parse_hosts(hosts_file):
    hosts = open(hosts_file, 'r')
    header_found = False
    iface_counter = 0
    for line in hosts.readlines():
        if header_found:
            try:
                iface_counter += 1
                viface = line.split('    ')[0]
                domain = line.split('    ')[1].strip('\n')
                domain_list.append(domain)
                real_ip = do_nslookup(domain)
                restore_iface(viface, interface_real)
                restored_proxy(viface, real_ip, domain[:-1])
            except:
                pass
        if 'sos_proxy' in line:
            header_found = True

    hosts.close()
    print '[INFO] All the interface were restored from {}'.format(hosts_file)
    return iface_counter


def restore_iface(viface_ip, interface_real):
    # use ip to create a virtual interface
    cmd = "sudo ip a add dev {1}:{0} {2}".format(viface_ip.split('.')[-1], interface_real, viface_ip)
    # use ifconfig to create a virtual interface
    #cmd = 'sudo ifconfig {1}:{0} {2}'.format(viface_ip.split('.')[-1], interface_real, viface_ip)
    os.system(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase the cli output verbosity", action="store_true")
    parser.add_argument("monitor_interface", help="the name of the interface that reaches the target")
    parser.add_argument("target_IPaddress", help="the IP address of the target device")
    parser.add_argument("-i", "--physical-interface", help="the name of the interface for "
                                                           "creating virtual interfaces", default='eth0')
    parser.add_argument("-a", "--ask-toset", help="ask before set any new virtual interface", action="store_true")
    parser.add_argument("-r", "--restore", help="restore a previously made proxy configuration "
                                                "using a hosts file and go ahead from that")
    args = parser.parse_args()

    print_welcome()
    ask = args.ask_toset
    verbose = args.verbose
    list_interfaces()
    interface = args.monitor_interface
    check_interface(interface)
    source_ip = args.target_IPaddress
    check_ip(source_ip)
    interface_real = args.physical_interface
    check_interface(interface_real)
    monitor_dns(interface, source_ip)
    hosts_file = args.restore
    if args.restore and os.path.isfile(hosts_file):
        restore_hosts(hosts_file)
        iface_counter = parse_hosts(hosts_file)
        recursive_read(interface_real, iface_counter)
    else:
        recursive_read(interface_real, iface_counter=0)
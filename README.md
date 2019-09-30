# SOS_Proxy

Is it possible to proxy a device that does not support this functionality?

Sometime, under particular circumstancies, *YES*. You can do that with Burp Suite and the invisible proxying technique explained at the following link.
https://portswigger.net/burp/documentation/desktop/tools/proxy/options/invisible


> 1. Create a separate virtual network interface for each destination host. 
> 2. Create a separate Proxy listener for each interface (or two listeners if HTTP and HTTPS are both in use).
> 3. Using your hosts file, redirect each destination hostname to a different network interface (i.e., to a different listener).
> 4. Configure Burp’s listener on each interface to redirect all traffic to the IP address of the host whose traffic was redirected to it.


SOS_Proxy is a simple Python tool that aims to automate the invisible proxy technique with the following features:
- DNS traffic monitoring
- Virtual interfaces creator
- Print information to set Burp’s proxies
- Possibility to choose which domain has to be intercepted
- Possibility to backup and restore a hosts file configuration


```
$ python sos_proxy.py --help
usage: sos_proxy.py [-h] [-v] [-i PHYSICAL_INTERFACE] [-a] [-r RESTORE]
                    monitor_interface target_IPaddress

positional arguments:
  monitor_interface     the name of the interface that reaches the target
  target_IPaddress      the IP address of the target device

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase the cli output verbosity
  -i PHYSICAL_INTERFACE, --physical-interface PHYSICAL_INTERFACE
                        the name of the interface for creating virtual
                        interfaces
  -a, --ask-toset       ask before set any new virtual interface
  -r RESTORE, --restore RESTORE
                        restore a previously made proxy configuration using a
                        hosts file and go ahead from that
```

## Video Demo
[![](http://img.youtube.com/vi/R9VAWpXcXAw/0.jpg)](https://www.youtube.com/watch?v=R9VAWpXcXAw)

Please note that on the device it was already installed a custom CA in order to break the SSL connection.

## Dependencies
- tmux
- tcpdump
- ifconfig/ip
- python 2.7

```
$ sudo apt install tmux tcpdump
```

## Useful Resources
In order to start Burp with enough privileges to bind a proxy on port 80/443 I suggest the use of this tool: *authbind* https://www.gremwell.com/node/387

## Notes
- This tool was made quick & dirty, actually it has been tested only on Ubuntu 18.04.3 LTS so be careful and use `-a` and `-v` parameters the first time you run it.
- Following a simple list of useful commands for debugging the tool:
    - $ tail -f /tmp/domains <- tcpdump write here the found domains
    - $ watch -n 2 ip a <- monitor the virtual interface creation
    - $ sudo tmux att -t Domain_Monitor <- check if tcpdump is working or not

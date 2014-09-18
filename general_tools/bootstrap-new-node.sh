#!/bin/bash
#
# Simple setup script for new systems, mainly to bootstrap Puppet
# After running this, cd into /etc/puppet and run `make base`

# Installs basic packages for CentOS
if [ -d /etc/yum.repos.d/ ]; then
    VER='6'
    grep -q 'release 7' /etc/centos-release && VER='7'
    if [ "$VER" == '6' ]; then
        rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
    fi
    if [ "$VER" == '7' ]; then
        rpm -ivh http://dl.fedoraproject.org/pub/epel/beta/7/x86_64/epel-release-7-1.noarch.rpm
        yum --enablerepo epel -y install iptables-services
        systemctl mask firewalld.service
        systemctl enable iptables.service
        systemctl enable ip6tables.service
        systemctl stop firewalld.service
        systemctl start iptables.service
        systemctl start ip6tables.service
    fi
    # Both 6 and 7 need the following
    yum --enablerepo epel -y install @base @core puppet git redhat-lsb telnet keyutils trousers fipscheck mdadm xinetd vim-enhanced tmux screen postfix ntp wget rsync yum-utils yum-plugin-downloadonly man unzip
    chkconfig puppet off
fi

# Clone DSM Puppet config directory to /etc/puppet
if [ ! -d /etc/puppet/.git ]; then
    rm -rf /etc/puppet
fi
git clone gitolite3@us.door43.org:puppet /etc/puppet

#!/usr/bin/env python3
# Copyright (c) 2019 Nippon Telegraph and Telephone Corporation

import sys
import json
import os
import ethtool
import ipaddress

from oslo_config import cfg

from jinja2 import Environment, FileSystemLoader


common_opts = [
    cfg.StrOpt('template-dir',
               default='/usr/local/etc/lagogw/template',
               help='Path to a templates directory.'),
    cfg.StrOpt('output-dir',
               default='.',
               help='Path to a directory to output created config files.'),
]

output_opts = [
    cfg.StrOpt('vsw-conf',
               default=None,
               help='Path to a file to output vsw configuration.'),
    cfg.StrOpt('ocd-conf',
               default=None,
               help='Path to a file to output openconfigd configuration.'),
    cfg.StrOpt('ipsec-conf',
               default=None,
               help='Path to a file to output ipsec configuration.'),
    cfg.StrOpt('ipsec-secrets',
               default=None,
               help='Path to a file to output ipsec secrets.')
]


vsw_opts = [
    cfg.StrOpt('dpdk_coremask',
               default='0x1c'),
    cfg.StrOpt('dpdk_vdevs',
               default='["crypto_openssl"]'),
    cfg.StrOpt('rx_core',
               default='2'),
    cfg.StrOpt('tx_core',
               default='3'),
    cfg.StrOpt('rt_core',
               default='4'),
    cfg.StrOpt('ipsec_core_bind',
                default='true'),
    cfg.StrOpt('ipsec_in_cores',
               default='0x20'),
    cfg.StrOpt('ipsec_out_cores',
               default='0x40')
]

ocd_opts = [
    cfg.StrOpt('wanif'),
    cfg.StrOpt('lanif'),
    cfg.StrOpt('wan_device'),
    cfg.StrOpt('wan_ipv4'),
    cfg.StrOpt('wan_ipv4_prefix_length'),
    cfg.StrOpt('remote_ipv4'),
    cfg.StrOpt('local_device'),
    cfg.StrOpt('local_ipv4'),
    cfg.StrOpt('local_ipv4_prefix_length'),
]

ipsec_opts = [
    cfg.StrOpt('local_ipv4_subnet'),
    cfg.StrOpt('remote_ipv4_subnet'),
    cfg.StrOpt('ike',
               default='aes128-sha1-ecp521'),
    cfg.StrOpt('esp',
               default='aes128-sha1-ecp521')
]

secrets_opts = [
    cfg.StrOpt('psk',
               default='lagopus')
]

def make_vsw_conf(conf, tpl):
    conf.register_opts(vsw_opts, group='vsw')

    config = {
        'dpdk_coremask':conf.vsw.dpdk_coremask,
        'dpdk_vdevs':conf.vsw.dpdk_vdevs,
        'rx_core':conf.vsw.rx_core,
        'tx_core':conf.vsw.tx_core,
        'rt_core':conf.vsw.rt_core,
        'ipsec_core_bind':conf.vsw.ipsec_core_bind,
        'ipsec_in_cores':conf.vsw.ipsec_in_cores,
        'ipsec_out_cores':conf.vsw.ipsec_out_cores,
    }

    return tpl.render(config)

def mask2length(subnet_mask):
    return ipaddress.ip_network('0.0.0.0/'+subnet_mask).prefixlen
def device_id(if_name):
    devid = ethtool.get_businfo(if_name)
    if devid == '':
        devid = os.path.basename(os.readlink("/sys/class/net/" + if_name + "/device"))
    return devid

def make_ocd_conf(conf, tpl):
    conf.register_opts(ocd_opts, group='openconfigd')

    config = {
        'wan_device':conf.openconfigd.wan_device,
        'wan_ipv4':conf.openconfigd.wan_ipv4,
        'wan_ipv4_prefix_length':conf.openconfigd.wan_ipv4_prefix_length,
        'remote_ipv4':conf.openconfigd.remote_ipv4,
        'local_device':conf.openconfigd.local_device,
        'local_ipv4':conf.openconfigd.local_ipv4,
        'local_ipv4_prefix_length':conf.openconfigd.local_ipv4_prefix_length,
    }

    if conf.openconfigd.wanif :
        if config['wan_ipv4'] == None:
            config['wan_ipv4'] = ethtool.get_ipaddr(conf.openconfigd.wanif)
            config['wan_ipv4_prefix_length'] = mask2length(ethtool.get_netmask(conf.openconfigd.wanif))
            config['wan_device'] = device_id(conf.openconfigd.wanif)
            conf.set_override('wan_ipv4', config['wan_ipv4'], group="openconfigd")
            conf.set_override('wan_ipv4_prefix_length', config['wan_ipv4_prefix_length'], group="openconfigd")
            conf.set_override('wan_device', config['wan_device'], group="openconfigd")

    if conf.openconfigd.lanif :
        if config['local_ipv4'] == None:
            config['local_ipv4'] = ethtool.get_ipaddr(conf.openconfigd.lanif)
            config['local_ipv4_prefix_length'] = mask2length(ethtool.get_netmask(conf.openconfigd.lanif))
            config['local_device'] = device_id(conf.openconfigd.lanif)
            conf.set_override('local_ipv4', config['local_ipv4'], group="openconfigd")
            conf.set_override('local_ipv4_prefix_length', config['local_ipv4_prefix_length'], group="openconfigd")
            conf.set_override('local_device', config['local_device'], group="openconfigd")

    return tpl.render(config)

def make_ipsec_conf(conf, tpl):
    conf.register_opts(ipsec_opts, group='ipsec')

    config = {
        'local_ipv4':conf.openconfigd.wan_ipv4,
        'local_ipv4_subnet':conf.ipsec.local_ipv4_subnet,
        'remote_ipv4':conf.openconfigd.remote_ipv4,
        'remote_ipv4_subnet':conf.ipsec.remote_ipv4_subnet,
        'ike':conf.ipsec.ike,
        'esp':conf.ipsec.esp
    }

    return tpl.render(config)

def make_ipsec_secrets(conf, tpl):
    conf.register_opts(secrets_opts, group='secrets')

    config = {
        'local_ipv4':conf.openconfigd.wan_ipv4,
        'remote_ipv4':conf.openconfigd.remote_ipv4,
        'psk':conf.secrets.psk
    }

    return tpl.render(config)

def main():
    conf = cfg.ConfigOpts()
    conf.register_cli_opts(common_opts)
    conf(sys.argv[1:])
    conf.register_opts(output_opts, group='output')

    env = Environment(loader=FileSystemLoader(conf.template_dir, encoding='utf8'))
    tpl = env.get_template('vsw.conf.template')
    vsw_conf = make_vsw_conf(conf, tpl)
    if conf.output.vsw_conf != None :
        print(conf.output.vsw_conf)
        f = open(conf.output.vsw_conf, 'w')
    else:
        f = open(conf.output_dir + '/vsw.conf', 'w')
    f.write(vsw_conf)
    f.close()

    tpl = env.get_template('openconfigd.conf.template')
    ocd_conf = make_ocd_conf(conf, tpl)
    if conf.output.ocd_conf != None:
        f = open(conf.output.ocd_conf, 'w')
    else:
        f = open(conf.output_dir + '/openconfigd.conf', 'w')
    f.write(ocd_conf)
    f.close()

    tpl = env.get_template('ipsec.conf.template')
    ipsec_conf = make_ipsec_conf(conf, tpl)
    if conf.output.ipsec_conf != None :
        f = open(conf.output.ipsec_conf , 'w')
    else:
        f = open(conf.output_dir + '/ipsec.conf', 'w')
    f.write(ipsec_conf)
    f.close()

    tpl = env.get_template('ipsec.secrets.template')
    secrets_conf = make_ipsec_secrets(conf, tpl)
    if conf.output.ipsec_secrets != None :
        f = open(conf.output.ipsec_secrets, 'w')
    else:
        f = open(conf.output_dir + '/ipsec.secrets', 'w')
    f.write(secrets_conf)
    f.close()

    return

if __name__ == '__main__':
    main()


# Setup Tool for Lagopus IPsec Gateway

## install

```
sudo apt install python3 python3-setuptools libpython3.6-dev libnl-route-3-dev
sudo pip3 install oslo.config oslo.log ethtool jinja2
git clone https://github.com/hibitomo/lago-gw
cd lago-gw
sudo ./setup.py install
```

## How to use

```
setup-lagogw --config-file ./sample/setup.conf --output-dir . --template-dir ./templates
```

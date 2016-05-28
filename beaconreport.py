#
# based on Taka Wang's work here: https://github.com/taka-wang/py-beacon
#
from datetime import datetime
from paho.mqtt import client as mqtt
import blescan
import bluetooth._bluetooth as bluez
import calendar
import ConfigParser
import json


class Scanner(object):
    """Scanner."""
    def __init__(self, deviceId=0, loops=1):
        """Initialize scanner."""
        self.deviceId = deviceId
        self.loops = loops
        try:
            self.sock = bluez.hci_open_dev(self.deviceId)
            blescan.hci_le_set_scan_parameters(self.sock)
            blescan.hci_enable_le_scan(self.sock)
        except Exception, e:
            print e

    def scan(self):
        return blescan.parse_events(self.sock, self.loops)


class BeaconReport(object):
    """BeaconReport class"""
    def __init__(self, config_file='config'):
        config_v = self.parse_config(config_file)
        self.url = config_v.get('url')
        self.port = config_v.get('port')
        self.keepalive = config_v.get('keepalive')
        self.client_id = config_v.get('client_id')
        self.username = config_v.get('username')
        self.password = config_v.get('password')
        self.certificate = config_v.get('certificate')
        self.client_key = config_v.get('client_key')
        self.client_cert = config_v.get('client_cert')
        self.mqtt_protocol = config_v.get('mqtt_protocol')
        self.topic_id = config_v.get('topic_id')
        self.mqtt_client = self.init_mqtt()
        self.scanner = Scanner()

    def parse_config(self, config_file):
        """Read config file"""
        ret = {}
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        ret["url"] = config.get('MQTT', 'url')
        ret["port"] = int(config.get('MQTT', 'port'))
        ret["keepalive"] = int(config.get('MQTT', 'keepalive'))
        ret["client_id"] = config.get('MQTT', 'client_id')
        ret["username"] = config.get('MQTT', 'username')
        ret["password"] = config.get('MQTT', 'password')
        certificate = config.get('MQTT', 'certificate')
        client_cert = config.get('MQTT', 'client_cert')
        client_key = config.get('MQTT', 'client_key')
        ret["certificate"] = certificate if certificate else None
        ret["client_key"] = client_key if client_key else None
        ret["client_cert"] = client_cert if client_cert else None
        ret["mqtt_protocol"] = config.get('MQTT', 'protocol')
        ret["topic_id"] = config.get('MQTT', 'topic_id')
        return ret

    def init_mqtt(self):
        """Init MQTT connection"""
        proto = mqtt.MQTTv311
        if self.mqtt_protocol == "3.1":
            proto = mqtt.MQTTv31

        if not self.client_id:
            client = mqtt.Client(protocol=proto)
        else:
            client = mqtt.Client(self.client_id, protocol=proto)

        if self.username is not None:
            client.username_pw_set(self.username, self.password)

        if self.certificate is not None:
            client.tls_set(self.certificate,
                           certfile=self.client_cert,
                           keyfile=self.client_key)

        try:
            client.connect(self.url, self.port, self.keepalive)
            client.loop_start()
            return client
        except Exception, e:
            print(e)
            return None

    def report(self, topic, data):
        if self.mqtt_client:
            d = datetime.utcnow()
            timestamp = calendar.timegm(d.utctimetuple())
            data['tst'] = timestamp
            self.mqtt_client.publish(topic, json.dumps(data))

    def do_scan(self):
        if self.scanner:
            for beacon, data in self.scanner.scan().items():
                topic = self.topic_id + '%s' % beacon
                self.report(topic, data)

if __name__ == '__main__':
    beacon_report = BeaconReport('config')
    while True:
        beacon_report.do_scan()

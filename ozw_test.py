'''
Manages the functions of the z-wave card
'''
import sys
import time
from pprint import pprint
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from openzwave.node import ZWaveNode
from pydispatch import dispatcher
from config import constants
from helpers.helper_functions import wait, singleton
from . import signal_handlers


@singleton
class Zwave:
    '''
    Functions to start, stop and retrieve devices from 
    the network.
    '''
    device = constants.ZWAVE_DEV
    _option = ZWaveOption(device=device)
    _option.set_log_file(constants.ZWAVE_LOG)
    _option.set_console_output(False)
    _option.lock()
    network = ZWaveNetwork(_option)

    def __init__(self):
        '''
        Initialize the necessary functions to run the z-wave network
        '''
    @property
    def nodes(self):
        '''
        Shows the nodes of the network. Generally the first node
        is always the z-wave controller

        :return: nodes
        :rtype: dict
        '''
        return self.network.nodes

    def set_node_value(self, node_id, value_id, data):
        node = self.nodes.get(node_id)
        if not node:
            return False
        value = node.get_values().get(value_id)
        if value.type == "Bool":
            if isinstance(data, bool):
                value.data = data
            else:
                value.data = (data == "True")

    def print_node_info(self, node_id):
        '''
        Print the node values in a easy to read
        format.

        :param node_id: id of the node for the values
        :type node_id: int
        '''
        node = self.nodes.get(node_id)
        if node:
            values = node.get_values()
            for k in values.values():
                if k.data_items == "Unknown":
                    continue
                pprint(k.to_dict())

        else:
            print("No data for node_id: {}".format(node_id))

    def run(self):
        '''
        Initialize and run the network
        '''
        self.connect_signals()
        self.init_network()

    def connect_signals(self):
        '''
        Connects the Z-Wave network signals to the appropiate
        signal handlers.
        i.e. signal lock event for notification and database update
        '''
        dispatcher.connect(
            signal_handlers.louie_network_started,
            ZWaveNetwork.SIGNAL_NETWORK_STARTED
        )
        dispatcher.connect(
            signal_handlers.louie_network_failed,
            ZWaveNetwork.SIGNAL_NETWORK_FAILED
        )
        dispatcher.connect(
            signal_handlers.louie_network_ready,
            ZWaveNetwork.SIGNAL_NETWORK_READY
        )

    def init_network(self):
        '''
        Initialize the Z-Wave card and network until the network is ready.
        '''
        self.network.start()
        count = 0
        while wait(1) and count < 300:
            if self.network.state >= self.network.STATE_STARTED:
                print("Z-Wave Network Started!")
                break
            count += 1
        if self.network.state < self.network.STATE_STARTED:
            print(".")
            print("Can't initialise driver! Look at the logs in OZW_Log.log")
            return
        print("***** Waiting for network to become ready : ")

        count = 0
        while wait(1) and count < 90:
            if self.network.state >= self.network.STATE_READY:
                print("***** Network is ready")
                break
            count += 1
        if self.network.state < self.network.STATE_READY:
            print("Unable to prepare network.")

    def inclusion(self, security=False):
        '''
        Put the z-wave card into inclusion mode. If security is selected, ensure that a 
        network encryption key is initialzized in the libraries.
        In env/libs/python/../python-openzwave/ozw_config/options.xml
        If this isn't setup, secure inclusion mode WILL NOT WORK.

        :param security: secure or insecure inclusion, defaults to False
        :type security: bool, optional
        :return: successfully set mode
        :rtype: bool
        '''
        return self.network.controller.add_node(doSecurity=security)

    def exclusion(self):
        '''
        Puts the device into exlusion mode
        '''
        return self.network.controller.remove_node()

    def cancel(self):
        '''
        Cancels the current command.
        eg. If you put exclusion mode, it will go back to normal

        :return: If cancel succeeded
        :rtype: bool
        '''
        return self.network.controller.cancel_command()

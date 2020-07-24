from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from openzwave.node import ZWaveNode
from pydispatch import dispatcher
import sys
import time

YALE_COMMANDS= ["Association Group Info",
        "Association V2",
        "Battery",
        "Configuration",
        "Device Reset Locally",
        "Door Lock Logging",
        "Door Lock V2",
        "Firmware Update Meta-Data V3",
        "Manufacturer Specific V2",
        "Notification V4",
        "Powerlevel",
        "Schedule Entry Lock V3",
        "Security S0",
        "Time Parameters",
        "Time V2",
        "User Code",
        "Version V2",
        "Z-Wave Plus Info V2",
 ]

def louie_network_started(network):
    print("Network homeid {:08x} - {} nodes were found.".format(network.home_id, network.nodes_count))

def louie_network_failed(network):
    print("Hello from network : can't load :(.")

def louie_network_ready(network):
    print("Hello from network : I'm ready : {} nodes were found.".format(network.nodes_count))
    print("Hello from network : my controller is : {}".format(network.controller))
    dispatcher.connect(louie_node_update, ZWaveNetwork.SIGNAL_NODE)
    dispatcher.connect(louie_value_update, ZWaveNetwork.SIGNAL_VALUE)
    dispatcher.connect(louie_node_added, ZWaveNetwork.SIGNAL_NODE_ADDED)

def louie_node_update(network, node):
    print("NODE : {}.".format(node))

def louie_value_update(network, node, value):
    print("     VALUE : {}.".format( value ))

def louie_node_added(network, node, value):
    print("Node added: {} {}.".format(node.manufacturer_name, value ))

class Run:
    dev = '/dev/ttyAMA0'
    _option = ZWaveOption(device=dev)
    _option.set_log_file("OZW_Log.log")
    _option.set_console_output(False)
    _option.lock()
    network = ZWaveNetwork(_option)
    def run(self):
        
        dispatcher.connect(louie_network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
        dispatcher.connect(louie_network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
        dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
        self.network.start()
        for i in range(0,300):
            if self.network.state>=self.network.STATE_STARTED:
                print(" done")
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(1.0)
        if self.network.state<self.network.STATE_STARTED:
            print(".")
            print("Can't initialise driver! Look at the logs in OZW_Log.log")
            quit(1)
        print("***** Waiting for network to become ready : ")
        for i in range(0,90):
            if self.network.state>=self.network.STATE_READY:
                print("***** Network is ready")
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(1.0)
        #time.sleep(5.0)
        # print(self.network.controller.add_node(True))
        # if self.network.controller.add_node(True):
        #     time.sleep(10)
        
        while 1:
            # print(self.network.nodes)
            inp = input()
            if inp == "c":
                if self.network.controller.add_node(True):
                    print("Add_node 10 sec")
                    time.sleep(10)
                else:
                    print("Unable to go into inclusion")
                    self.network.controller.cancel_command()
            elif inp == "d":
                if self.network.controller.remove_node():
                    print("remove_node 10 sec")
                    time.sleep(10)
                else:
                    print("Unable to go into exclusion mode")
                    self.network.controller.cancel_command()
            elif inp == "q":
                break
            elif inp == "add":
                for node in self.network.nodes.values():
                    if node.manufacturer_id == '0x0129':
                        value = input("id:")
                        command = input("command:")
                        print(node.add_value(value_id=int(value), command_class=command))
            print(self.network.state_str)
            print(self.network.nodes)
            if type(self.network.nodes) is dict:
                try:
                    for i, node in self.network.nodes.items():
                        print(str(i) + ":")
                        print('',node.manufacturer_name, node.manufacturer_id)
                        print('',node.product_name, node.product_id)
                        print('',node.device_type)
                        values = node.get_values()
                        
                        for i,k in values.items():
                            if k.data_items == "Unknown":
                                continue
                            print(str(i)+":")
                            print("","Label:      ", k.label)
                            print("","Data:       ", k.data)
                            print("","Data_items: ", k.data_items)
                            print("","is_polled:  ", k.is_polled)
                        inp = input("Set Value[id]: ")
                        if inp:
                            if inp == 'q':
                                break
                            try:
                                if values.get(int(inp)).type == "Bool":
                                    values.get(int(inp)).data = input("value[T/F]: ") == "T"
                                else:
                                    values.get(int(inp)).data = input("value: ")
                            except (TypeError, ValueError):
                                continue

                    # print(self.network.nodes[7].capabilities,"\n")
                            '''print(node.get_command_class_genres())
                            node.refresh_info()
                            self.__print("is_sleeping", node.is_sleeping)
                            self.__print("is_ready", node.is_ready)
                            self.__print("is_locked", node.is_locked)
                            print("USER:")
                            for i in node.get_values().values():
                                i.enable_poll()
                                self.__print(i.label, i.data, ide=str(i.value_id))
                                print("         type:        {}".format(i.type))
                                print("         data_items:  {}".format(i.data_items))
                                print("         is_polled:   {}".format(i.is_polled))
                                print("         is_read_only:{}".format(i.is_read_only))'''
                except (ValueError, KeyError):
                    print("Unable to read data")
                except KeyboardInterrupt:
                    break
            # break
                # for _, val in values:
                #     print(val.data_as_string())
            time.sleep(1.0)
        self.network.stop()
    def __print(self, first, second, ide=""):
        ide += ":" + first + ":"
        first = ide
        i = 30 - len(first)
        for k in range(0,i):
            first += " "
        print("     {}{}".format(first, second))

if __name__ == "__main__":
    run = Run()
    try:
        run.run()
    except KeyboardInterrupt:
        run.network.stop()

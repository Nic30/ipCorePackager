from typing import List, Dict, Union, Tuple

from ipCorePackager.constants import INTF_DIRECTION
from ipCorePackager.otherXmlObjs import Parameter
from ipCorePackager.type import Type


class IpConfigNotSpecified(Exception):
    """
    This error means that you need to implement this function to use this functionality

    f.e. you have to implement Simulation agent for interface when you create new one and you can not use existing
    """
    pass


class IntfConfigBase(Type):
    def __init__(self):
        self.parameters = []

        self.name = None
        self.quartus_name = None

        self.map = {}
        self.quartus_map = None

    def _asQuartusTcl(self, buff: List[str], version: str, intfName: str,
                      component, top, allInterfaces: List['Interface'],
                      thisIf: 'Interface', intfMapOrName: Dict[str, Union[Dict, str]]):
        """
        Add interface to Quartus tcl by specified name map

        :param buff: line buffer for output
        :param version: Quartus version
        :param intfName: name of top interface
        :param component: component object from ipcore generator
        :param top: top design instance
        :param allInterfaces: list of all interfaces of top unit
        :param thisIf: interface to add into Quartus TCL
        :param intfMapOrName: Quartus name string for this interface
            or dictionary to map subinterfaces
        """

        if isinstance(intfMapOrName, str):
            self.quartus_add_interface_port(
                buff, intfName, thisIf, intfMapOrName)
        else:
            for thisIf_ in thisIf._interfaces:
                v = intfMapOrName[thisIf_._name]
                self._asQuartusTcl(buff, version, intfName, component, top,
                                   allInterfaces, thisIf_, v)

    def asQuartusTcl(self, buff: List[str], version: str, component,
                     top, allInterfaces: List['Interface'],
                     thisIf: 'Interface'):
        """
        Add interface to Quartus tcl

        :param buff: line buffer for output
        :param version: Quartus version
        :param intfName: name of top interface
        :param component: component object from ipcore generator
        :param top: top design instance
        :param allInterfaces: list of all interfaces of top unit
        :param thisIf: interface to add into Quartus TCL
        """
        name = self.getInterfaceName(thisIf)
        self.quartus_tcl_add_interface(buff, thisIf)
        clk = thisIf._getAssociatedClk()
        if clk is not None:
            self.quartus_prop(buff, name, "associatedClock",
                              clk._sigInside.name, escapeStr=False)
        rst = thisIf._getAssociatedRst()
        if rst is not None:
            self.quartus_prop(buff, name, "associatedReset",
                              rst._sigInside.name, escapeStr=False)

        m = self.get_quartus_map()
        if m:
            intfMapOrName = m
        else:
            intfMapOrName = thisIf.name
        self._asQuartusTcl(buff, version, name, component,
                           top, allInterfaces, thisIf, intfMapOrName)

    def get_quartus_map(self):
        if self.quartus_map is None:
            return self.map
        else:
            return self.quartus_map

    def get_quartus_name(self):
        if self.quartus_name is None:
            return self.name
        else:
            return self.quartus_name

    def addSimpleParam(self, interfaceName: str, paramName, value):
        p = Parameter()
        p.name = paramName
        p.value.resolve = "immediate"
        p.value.id = "BUSIFPARAM_VALUE.%s.%s" % (interfaceName.upper(),
                                                 paramName.upper())
        p.value.text = value
        self.parameters.append(p)
        return p

    def postProcess(self, component, entity, allInterfaces, thisIf):
        pass

    def quartus_tcl_add_interface(self, buff, thisIntf):
        """
        Create interface in Quartus TCL

        :return: add_interface command string
        """
        if self.getthisIntf._direction == INTF_DIRECTION.MASTER:
            dir_ = "start"
        else:
            dir_ = "end"

        name = self.getInterfaceName(thisIntf)
        buff.extend(["add_interface %s %s %s" %
                     (name, self.get_quartus_name(), dir_)])

        self.quartus_prop(buff, name, "ENABLED", True)
        self.quartus_prop(buff, name, "EXPORT_OF", "")
        self.quartus_prop(buff, name, "PORT_NAME_MAP", "")
        self.quartus_prop(buff, name, "CMSIS_SVD_VARIABLES", "")
        self.quartus_prop(buff, name, "SVD_ADDRESS_GROUP", "")

    def quartus_prop(self, buff: List[str], intfName: str, name: str, value,
                     escapeStr=True):
        """
        Set property on interface in Quartus TCL

        :param buff: line buffer for output
        :param intfName: name of interface to set property on
        :param name: property name
        :param value: property value
        :param escapeStr: flag, if True put string properties to extra ""
        """
        if escapeStr and isinstance(value, str):
            value = '"%s"' % value
        elif isinstance(value, bool):
            value = str(value).lower()
        else:
            value = str(value)

        buff.append("set_interface_property %s %s %s" %
                    (intfName, name, value))

    def addParam(self, thisIntf, name, value):
        """
        Add parameter with width of this interface (and interface is signal in this case)
        """
        _, width, widthLocked = self.getWidth(thisIntf, value)
        p = self.addSimpleParam(name, name, width)
        if not widthLocked:
            p.value.resolve = "user"

    def quartus_add_interface_port(self, buff: List[str], intfName: str, signal,
                                   logicName: str):
        """
        Add subinterface to Quartus interface

        :param buff: line buffer for output
        :param intfName: name of top interface
        :param signal: subinterface to create port for
        :param logicName: name of port in Quartus
        """
        d = signal._direction
        if d == INTF_DIRECTION.MASTER:
            dir_ = "Output"
        elif d == INTF_DIRECTION.SLAVE:
            dir_ = "Input"
        else:
            raise ValueError(d)

        _, width, _ = self.getWidth(signal)

        buff.append("add_interface_port %s %s %s %s %s" % (
            intfName,
            self.getPhysicalName(signal),
            logicName,
            dir_,
            width
        ))

    def getInterfaceName(self, thisIntf):
        raise NotImplementedError(
            "Implement this method in your IntfConfig class")

    def getDirection(self, thisIntf) -> INTF_DIRECTION:
        raise NotImplementedError(
            "Implement this method in your IntfConfig class")

    def getWidth(self, thisIntf) -> Tuple[int, str, bool]:
        """
        :return: tuple (current value of width,
            string of value (can be ID or int),
            Flag which specifies if width of signal is locked or can be changed by parameter)
        """
        raise NotImplementedError(
            "Implement this method in your IntfConfig class")

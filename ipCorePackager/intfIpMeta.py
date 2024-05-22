from typing import List, Dict, Union

from ipCorePackager.constants import INTF_DIRECTION
from ipCorePackager.otherXmlObjs import Parameter
from ipCorePackager.type import Type


class IntfIpMetaNotSpecifiedError(Exception):
    """
    This error means that you need to implement this function
    to use this functionality

    e.g. you have to implement Simulation agent for interface
    if you create new one and you can not use existing
    """
    pass


class VALUE_RESOLVE:
    IMMEDIATE = "immediate"
    USER = "user"
    NONE = None


class IntfIpMeta(Type):

    def __init__(self):
        self.parameters = []

        self.name = None
        self.quartus_name = None

        self.map = {}
        self.quartus_map = None

    def _asQuartusTcl(self, buff: List[str], version: str, intfName: str,
                      component: "Component", packager: "IpPackager",
                      thisIf: 'HwIO', intfMapOrName: Dict[str, Union[Dict, str]]):
        """
        Add interface to Quartus tcl by specified name map

        :param buff: line buffer for output
        :param version: Quartus version
        :param intfName: name of top interface
        :param component: component object from ipcore generator
        :param packager: instance of IpPackager which is packaging current design
        :param thisIf: interface to add into Quartus TCL
        :param intfMapOrName: Quartus name string for this interface
            or dictionary to map child HwIO instances
        """

        if isinstance(intfMapOrName, str):
            self.quartus_add_interface_port(
                buff, intfName, thisIf, intfMapOrName, packager)
        else:
            for thisIf_ in thisIf._hwIOs:
                v = intfMapOrName[thisIf_._name]
                self._asQuartusTcl(buff, version, intfName, component,
                                   packager, thisIf_, v)

    def asQuartusTcl(self, buff: List[str], version: str, component: "Component",
                     packager: "IpPackager", thisIf: 'HwIO'):
        """
        Add interface to Quartus tcl

        :param buff: line buffer for output
        :param version: Quartus version
        :param intfName: name of top interface
        :param component: component object from ipcore generator
        :param packager: instance of IpPackager which is packaging current design
        :param allInterfaces: list of all interfaces of top unit
        :param thisIf: interface to add into Quartus TCL
        """
        name = packager.getInterfaceLogicalName(thisIf)
        self.quartus_tcl_add_interface(buff, thisIf, packager)
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
                           packager, thisIf, intfMapOrName)

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

    def addWidthParam(self, thisIntfName: str, name: str, value, packager: "IpCorePackager"):
        _, v_str, v_is_const = packager.serialzeValueToTCL(value, do_eval=True)
        p = self.addSimpleParam(thisIntfName, name, v_str)
        if v_is_const:
            p.value.resolve = VALUE_RESOLVE.USER

    def addSimpleParam(self, interfaceLogicalName: str, paramName: str, value: str,
                       resolve=VALUE_RESOLVE.IMMEDIATE):
        p = Parameter()
        p.name = paramName
        if resolve is not VALUE_RESOLVE.NONE:
            p.value.resolve = resolve
        p.value.id = "BUSIFPARAM_VALUE.%s.%s" % (interfaceLogicalName.upper(),
                                                 paramName.upper())
        p.value.text = value
        self.parameters.append(p)
        return p

    def postProcess(self, component, packager, thisIf):
        pass

    def quartus_tcl_add_interface(self, buff, thisIntf, packager):
        """
        Create interface in Quartus TCL

        :return: add_interface command string
        """
        if packager.getInterfaceDirection(thisIntf) == INTF_DIRECTION.MASTER:
            dir_ = "start"
        else:
            dir_ = "end"

        name = packager.getInterfaceLogicalName(thisIntf)
        q_name =  self.get_quartus_name()
        buff.extend([f"add_interface {name:s} {q_name:s} {dir_:s}"])

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

        buff.append(f"set_interface_property {intfName:s} {name:s} {value:s}")

    def quartus_add_interface_port(self, buff: List[str], intfName: str, signal,
                                   logicName: str, packager: "IpCorePackager"):
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

        _, width, _ = packager.getTypeWidth(packager.getInterfaceType(signal), do_eval=True)

        phy_name = packager.getInterfacePhysicalName(signal)
        buff.append(f"add_interface_port {intfName:s} {phy_name:s} {logicName:s} {dir_:s} {width:s}")

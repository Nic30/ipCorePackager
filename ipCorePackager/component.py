from itertools import islice
from os.path import basename
from time import time

from ipCorePackager.busInterface import BusInterface
from ipCorePackager.constants import INTF_DIRECTION
from ipCorePackager.helpers import appendSpiElem, \
    appendStrElements, mkSpiElm, ns, whereEndsWithExt, whereEndsWithExts
from ipCorePackager.intfIpMeta import IntfIpMetaNotSpecified, VALUE_RESOLVE
from ipCorePackager.model import Model
from ipCorePackager.otherXmlObjs import VendorExtensions, \
    FileSet, File, Parameter, Value
from ipCorePackager.port import Port
import xml.etree.ElementTree as etree


any_syn_fileSetName = "xilinx_anylanguagesynthesis"
any_sim_fileSetName = "xilinx_anylanguagebehavioralsimulation_view_fileset"
tcl_fileSetName = "xilinx_xpgui_view_fileset"
xdc_fileSetName = any_syn_fileSetName
DEFAULT_QUARTUS_VERSION = "16.1"


def tcl_comment(s):
    return f"# {s:s}"


def tcl_set_module_property(name: str, value, escapeStr=True):
    if escapeStr and isinstance(value, str):
        value = '"%s"' % value
    elif isinstance(value, bool):
        value = str(value).lower()
    else:
        value = repr(value)

    return f"set_module_property {name:s} {value:s}"


def tcl_add_fileset_file(filename: str):
    """
    :param filename: relative filename with .vhdl or .v

    :return: add_fileset_file command string
    """
    if filename.endswith(".vhd"):
        t = "VHDL"
    elif filename.endswith(".v") or filename.endswith(".sv") or filename.endswith(".svh"):
        t = "VERILOG"
    elif filename.endswith(".xdc"):
        t = "XDC"
    else:
        raise NotImplementedError(
            "Can not resolve type of file by extension", filename)
    name = basename(filename)

    return f"add_fileset_file {name:s} {t:s} PATH {filename:s}"


class Component():
    """
    Containers of informations about IP core

    :attention: Xilinx IP-XACT is element position dependent
    """
    _strValues = ["vendor", "library", "name", "version", "description"]
    # _iterableValues = ["fileSets", "parameters" ]

    def __init__(self, packager: "IpPackager"):
        self.vendor = ''
        self.library = ''
        self.name = ""
        self.version = "1.0"
        self.busInterfaces = []
        self.model = Model(packager, any_syn_fileSetName,
                           any_sim_fileSetName, tcl_fileSetName)
        self.fileSets = []
        self.description = ""
        self.parameters = []
        self.vendorExtensions = VendorExtensions()
        self._files = []
        self._top = None
        self._packager = packager

    # @classmethod
    # def load(cls, xmlStr):
    #    self = cls()
    #    for prefix, uri in ns.items():
    #        etree.register_namespace(prefix, uri)
    #    self.root = etree.fromstring(xmlStr)
    #    self.name = findS(self.root, "name").text
    #
    #    intf = findS(self.root, "busInterfaces")
    #    self.interfaces = {}
    #    for i in intf:
    #        i = BusInterface.fromElem(i)
    #        if i.name in self.interfaces.keys():
    #            raise Exception("Multiple interfaces with same name")
    #        self.interfaces[i.name] = i
    #    self.model = Model.fromElem(findS(self.root, "model"))
    #
    #    return self

    def _xmlFileSets(self, componentElem):

        def fileSetFromFiles(name, files):
            fileSet = FileSet()
            fileSet.name = name
            for fn in files:
                f = File.fromFileName(fn)
                fileSet.files.append(f)
            return fileSet

        filesets = appendSpiElem(componentElem, "fileSets")
        hdlExtensions = [".vhd", '.v', '.sv', '.svh', '.xdc']

        hdl_fs = fileSetFromFiles(
            any_syn_fileSetName,
            whereEndsWithExts(self._files, hdlExtensions))
        hdl_sim_fs = fileSetFromFiles(
            any_sim_fileSetName,
            whereEndsWithExts(self._files, hdlExtensions))
        tclFileSet = fileSetFromFiles(
            tcl_fileSetName,
            whereEndsWithExt(self._files, ".tcl"))
        for fs in [hdl_fs, hdl_sim_fs, tclFileSet]:
            filesets.append(fs.asElem())

    def _xmlParameters(self, compElem):
        parameters = appendSpiElem(compElem, "parameters")
        for p in self.parameters:
            parameters.append(p.asElem())

    def ip_xact(self):
        # Vivado 2015.2 bug - order of all elements is NOT optional
        for prefix, uri in ns.items():
            etree.register_namespace(prefix, uri)
        c = mkSpiElm("component")
        appendStrElements(c, self, self._strValues[:-1])
        for intf in self.busInterfaces:
            if hasattr(intf, "_bi"):
                bi = appendSpiElem(c, "busInterfaces")
                for intf in self.busInterfaces:  # for all interfaces which have bus interface class
                    if hasattr(intf, "_bi"):
                        bi.append(intf._bi.asElem())
                break

        c.append(self.model.asElem())
        self._xmlFileSets(c)

        appendStrElements(c, self, [self._strValues[-1]])
        self._xmlParameters(c)
        c.append(self.vendorExtensions.asElem(
            self.name + "_v" + self.version, revision=str(int(time()))))

        return c

    def registerInterface(self, intf: 'Interface'):
        if intf._interfaces:
            for i in intf._interfaces:
                self.registerInterface(i)
        else:
            pack = self._packager
            name = pack.getInterfacePhysicalName(intf)
            d = pack.getInterfaceDirection(intf)
            t = pack.getInterfaceType(intf)
            p = Port.fromParams(name,
                                INTF_DIRECTION.asDirection(d),
                                t,
                                pack)
            self.model.ports.append(p)

    def asignTopUnit(self, top, topName):
        """
        Set hwt unit as template for component
        """
        self._top = top
        self.name = topName
        pack = self._packager
        self.model.addDefaultViews(topName, pack.iterParams(top))

        for intf in pack.iterInterfaces(self._top):
            self.registerInterface(intf)
            if intf._isExtern:
                self.busInterfaces.append(intf)

        self.busInterfaces.sort(key=lambda x: x._name)
        for intf in self.busInterfaces:
            biClass = None
            try:
                biClass = intf._getIpCoreIntfClass()
            except IntfIpMetaNotSpecified:
                pass
            if biClass is not None:
                bi = BusInterface.fromBiClass(intf, biClass, self._packager)
                intf._bi = bi
                bi.busType.postProcess(self, self._packager, intf)

        # generate component parameters
        compNameParam = Parameter()
        compNameParam.name = "Component_Name"
        compNameParam.value = Value()
        v = compNameParam.value
        v.id = "PARAM_VALUE.Component_Name"
        v.resolve = VALUE_RESOLVE.USER
        v.text = self.name
        self.parameters.append(compNameParam)
        # generic as parameters
        for _p in pack.iterParams(self._top):
            p = Parameter()
            p.name = pack.getParamPhysicalName(_p)
            p.value = self._packager.paramToIpValue(
                "PARAM_VALUE.", _p, Value.RESOLVE_USER)
            self.parameters.append(p)

        # for bi in self.busInterfaces:
        #    bi.name = trimUnderscores(bi.name)
        #    for p in bi.parameters:
        #        p.name = removeUndescores_witSep(p.name, ".")
        #        p.value.id = removeUndescores_witSep(p.value.id , ".")
        #        p.value.text = removeUndescores_witSep(p.value.text , ".")

    def quartus_tcl(self, quartus_version=None):
        if quartus_version is None:
            quartus_version = DEFAULT_QUARTUS_VERSION
        buff = [
            tcl_comment("module properties"),
            f"package require -exact qsys {quartus_version:s}",
            tcl_set_module_property("DESCRIPTION", self.description),
            tcl_set_module_property("NAME", self.name),
            tcl_set_module_property("VERSION", self.version),
            tcl_set_module_property("INTERNAL", False),
            tcl_set_module_property("OPAQUE_ADDRESS_MAP", True),
            tcl_set_module_property("GROUP", self.library),
            tcl_set_module_property("AUTHOR", self.vendor),
            tcl_set_module_property("DISPLAY_NAME", self.name),
            tcl_set_module_property("INSTANTIATE_IN_SYSTEM_MODULE", True),
            tcl_set_module_property("EDITABLE", True),
            tcl_set_module_property("REPORT_TO_TALKBACK", False),
            tcl_set_module_property("ALLOW_GREYBOX_GENERATION", False),
            tcl_set_module_property("REPORT_HIERARCHY", False),
        ]

        buff.extend([
            'add_fileset QUARTUS_SYNTH QUARTUS_SYNTH "" ""',
            'set_fileset_property QUARTUS_SYNTH TOP_LEVEL %s' % self.name,
            "set_fileset_property QUARTUS_SYNTH ENABLE_RELATIVE_INCLUDE_PATHS false",
            "set_fileset_property QUARTUS_SYNTH ENABLE_FILE_OVERWRITE_MODE false"
        ])
        for f in self._files:
            if not f.endswith(".tcl"):
                s = tcl_add_fileset_file(f)
                buff.append(s)

        buff.append(tcl_comment("params"))
        # first is name of this component
        for p in islice(self.parameters, 1, None):
            p.asQuartusTcl(buff, quartus_version)

        buff.append(tcl_comment("interfaces"))
        for intf in self.busInterfaces:
            # for all interfaces which have bus interface class
            if hasattr(intf, "_bi"):
                bi = intf._bi
                bi.busType.asQuartusTcl(buff, quartus_version,
                                        self, self._packager, intf)
                buff.append("")
        return "\n".join(buff)

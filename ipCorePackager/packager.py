import os
from os.path import relpath
import shutil
from typing import List, Optional, Union, Tuple

from ipCorePackager.component import Component
from ipCorePackager.helpers import prettify
from ipCorePackager.tclGuiBuilder import GuiBuilder,\
    paramManipulatorFns
from ipCorePackager.uniqList import UniqList
from ipCorePackager.otherXmlObjs import Value


# [TODO] memory maps https://forums.xilinx.com/t5/Embedded-Processor-System-Design/exporting-AXI-BASEADDR-to-xparameters-h-from-Vivado-IP/td-p/428650
class IpPackager(object):
    """
    IP-core packager

    :summary: Packs HDL, constraint and other files to IP-Core package
        for distribution and simple integration

    """

    def __init__(self, topObj, name,
                 extraVhdlFiles: List[str]=[],
                 extraVerilogFiles: List[str]=[]):
        """
        :param topObj: Unit instance of top component
        :param name: name of top
        :param extraVhdlFiles: list of extra vhdl file names for files
            which should be distributed in this IP-core
        :param extraVerilogFiles: same as extraVhdlFiles just for Verilog
        """
        self.top = topObj
        self.name = name
        self.hdlFiles = UniqList()

        for f in extraVhdlFiles:
            self.hdlFiles.append(f)

        for f in extraVerilogFiles:
            self.hdlFiles.append(f)

    def saveHdlFiles(self, srcDir):
        """
        :param srcDir: dir name where dir with HDL files should be stored
        """
        path = os.path.join(srcDir, self.name)
        try:
            os.makedirs(path)
        except OSError:
            # wipe if exists
            shutil.rmtree(path)
            os.makedirs(path)

        files = self.hdlFiles
        self.hdlFiles = self.toHdlConversion(self.top, self.name, path)
        for srcF in files:
            dst = os.path.join(path,
                               os.path.relpath(srcF, srcDir).replace('../', '')
                               )
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(srcF, dst)
            self.hdlFiles.append(dst)

    def mkAutoGui(self):
        """
        :summary: automatically generate simple gui in TCL
        """
        gui = GuiBuilder()
        p0 = gui.page("Main")
        handlers = []
        for g in self.topUnit._entity.generics:
            p0.param(g.name)
            for fn in paramManipulatorFns(g.name):
                handlers.append(fn)

        with open(self.guiFile, "w") as f:
            f.write(gui.asTcl())
            for h in handlers:
                f.write('\n\n')
                f.write(str(h))

    def createPackage(self, repoDir, vendor: str="hwt", library: str="mylib",
                      description: Optional[str]=None):
        '''
        :param repoDir: directory where IP-Core should be stored
        :param vendor: vendor name of IP-Core
        :param library: library name of IP-Core
        :param description: description of IP-Core

        :summary:  synthetise hdl if needed
            copy hdl files
            create gui file
            create component.xml, component_hw.tcl
        '''
        ip_dir = os.path.join(repoDir, self.name + "/")
        if os.path.exists(ip_dir):
            shutil.rmtree(ip_dir)

        ip_srcPath = os.path.join(ip_dir, "src")
        tclPath = os.path.join(ip_dir, "xgui")
        guiFile = os.path.join(tclPath, "gui.tcl")
        for d in [ip_dir, ip_srcPath, tclPath]:
            os.makedirs(d)
        self.saveHdlFiles(ip_srcPath)

        self.guiFile = guiFile
        self.mkAutoGui()

        c = Component()
        c._files = [relpath(p, ip_dir) for p in sorted(self.hdlFiles)] + \
                   [relpath(guiFile, ip_dir)]

        c.vendor = vendor
        c.library = library
        if description is None:
            c.description = self.name + "_v" + c.version
        else:
            c.description = description

        c.asignTopUnit(self.topUnit)

        xml_str = prettify(c.xml())
        with open(ip_dir + "component.xml", "w") as f:
            f.write(xml_str)

        quartus_tcl_str = c.quartus_tcl()
        with open(ip_dir + "component_hw.tcl", "w") as f:
            f.write(quartus_tcl_str)

    def toHdlConversion(self, top, topName: str, saveTo: str) -> List[str]:
        """
        :param top: object which is represenation of design
        :param topName: name which should be used for ipcore
        :param saveTo: path of directory where generated files should be stored

        :return: list of file namens in correct compile order
        """
        raise NotImplementedError(
            "Implement this function for your type of your top module")

    def serializeType(self, hdlType: 'HdlType') -> str:
        raise NotImplementedError(
            "Implement this function for your hdl types")

    def paramToIpValue(self, idPrefix: str, g: "Param", resolve) -> Value:
        raise NotImplementedError(
            "Implement this function for your Param type")
    
    def getType(self, intf: "Interface") -> "HdlType":
        raise NotImplementedError(
            "Implement this function for your Param and Interface type")

    def getVectorFromType(self, dtype) -> Union[False, None, Tuple[int, int]]:
        """
        :return: None if type has not specific width,
            False if type is just single bit and not a vector
            [high, low] if type is vector 
        """
        raise NotImplementedError(
            "Implement this function for your HdlType")
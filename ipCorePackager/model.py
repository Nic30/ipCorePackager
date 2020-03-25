from typing import List

from ipCorePackager.helpers import appendSpiElem, \
    appendStrElements, findS, mkSpiElm, spi_ns_prefix, appendSpiArray
from ipCorePackager.otherXmlObjs import Value
import xml.etree.ElementTree as etree


class FileSetRef():
    @classmethod
    def fromElem(cls, elm):
        self = cls()
        self.localName = findS(elm, 'localName').text
        return self

    def asElem(self):
        e = etree.Element(spi_ns_prefix + "fileSetRef")
        appendSpiElem(e, "localName").text = self.localName
        return e


class View():
    _requiredVal = ["name", "displayName", "envIdentifier"]
    _optionalVal = ["language", "modelName"]

    @classmethod
    def fromElem(cls, elm):
        self = cls()
        for n in self._requiredVal:
            e = findS(elm, n)
            if e is None:
                raise Exception("View is missing " + n)
            setattr(self, n, e.text)
        for n in self._optionalVal:
            e = findS(elm, n)
            if e is None:
                continue
            setattr(self, n, e.text)

        self.fileSetRef = FileSetRef.fromElem(findS(elm, "fileSetRef"))
        return self

    def asElem(self):
        e = mkSpiElm("view")
        appendStrElements(e, self,
                          reqPropNames=self._requiredVal,
                          optPropNames=self._optionalVal)
        e.append(self.fileSetRef.asElem())
        return e


class ModelParameter():
    def __init__(self, name: str, displayName: str, datatype: str,
                 value: Value):
        self.name = name
        self.displayName = displayName
        self.datatype = datatype
        self.value = value

    @classmethod
    def fromParam(cls, p, packager):
        gType = packager.getParamType(p)
        val = packager.paramToIpValue("MODELPARAM_VALUE.", p,
                                      Value.RESOLVE_GENERATED)
        name = packager.getParamPhysicalName(p)

        return cls(name,
                   name.replace("_", " "),
                   packager.serializeType(gType).lower(),
                   val)

    def asElem(self):
        e = mkSpiElm("modelParameter")
        e.attrib["spirit:dataType"] = self.datatype
        appendStrElements(e, self,
                          reqPropNames=['name', "displayName"])
        e.append(self.value.asElem())
        return e


class Model():

    def __init__(self, packager: "IpPackager",
                 any_syn_fileSetName, any_sim_fileSetName, tcl_fileSetName):
        self._packager = packager
        self.views = []
        self.ports = []
        self.modelParameters = []
        self.any_syn_fileSetName = any_syn_fileSetName
        self.any_sim_fileSetName = any_sim_fileSetName
        self.tcl_fileSetName = tcl_fileSetName

    def addDefaultViews(self, name: str, parameters: List['Param']):
        viewsTemplate = ("""
<views xmlns:xilinx="http://www.xilinx.com" xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <spirit:view>
    <spirit:name>xilinx_anylanguagesynthesis</spirit:name>
    <spirit:displayName>Synthesis</spirit:displayName>
    <spirit:envIdentifier>vhdlSource:vivado.xilinx.com:synthesis</spirit:envIdentifier>
    <spirit:modelName>{0}</spirit:modelName>
    <spirit:fileSetRef>
      <spirit:localName>""" + self.any_syn_fileSetName + """</spirit:localName>
    </spirit:fileSetRef>
  </spirit:view>
  <spirit:view>
    <spirit:name>xilinx_anylanguagebehavioralsimulation</spirit:name>
    <spirit:displayName>Simulation</spirit:displayName>
    <spirit:envIdentifier>vhdlSource:vivado.xilinx.com:simulation</spirit:envIdentifier>
    <spirit:modelName>{0}</spirit:modelName>
    <spirit:fileSetRef>
      <spirit:localName>""" + self.any_sim_fileSetName + """</spirit:localName>
    </spirit:fileSetRef>
  </spirit:view>
  <spirit:view>
    <spirit:name>xilinx_xpgui</spirit:name>
    <spirit:displayName>UI Layout</spirit:displayName>
    <spirit:envIdentifier>:vivado.xilinx.com:xgui.ui</spirit:envIdentifier>
    <spirit:fileSetRef>
      <spirit:localName>""" + self.tcl_fileSetName + """</spirit:localName>
    </spirit:fileSetRef>
  </spirit:view>
</views>
        """).format(name)
        for v in etree.fromstring(viewsTemplate):
            v = View.fromElem(v)
            v.modelName = name
            self.views.append(v)

        pack = self._packager
        for p in parameters:
            mp = ModelParameter.fromParam(p, pack)
            self.modelParameters.append(mp)

    # @classmethod
    # def fromElem(cls, elm):
    #    self = cls()
    #    views = findS(elm, "views")
    #    for vElm in views:
    #        self.views.append(View.fromElem(vElm))
    #    ports = findS(elm, "ports")
    #    for p in ports:
    #        self.ports.append(Port.fromElem(p))
    #    return self

    def asElem(self):
        e = mkSpiElm("model")
        appendSpiArray(e, 'views', self.views)
        appendSpiArray(e, 'ports', self.ports)
        appendSpiArray(e, 'modelParameters', self.modelParameters)

        return e

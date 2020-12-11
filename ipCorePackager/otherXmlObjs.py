import os
from time import gmtime, strftime

from ipCorePackager.helpers import spi_ns_prefix, mkSpiElm, \
    appendSpiElem, appendStrElements, mkXiElm, appendXiElem, appendSpiAtribs


class Value():
    __slots__ = ['id', 'format', 'bitStringLength',
                 'resolve', 'dependency', 'text']
    RESOLVE_GENERATED = "generated"
    RESOLVE_USER = "user"

    # @classmethod
    # def fromElem(cls, elm):
    #     self = cls()
    #     self.id = elm.attrib[spi_ns_prefix + 'id']
    #     self.text = elm.text
    #     self.resolve = elm.attrib[spi_ns_prefix + 'resolve']
    #     self.dependency = elm.attrib[spi_ns_prefix + 'dependency']
    #     for n in ['format', 'bitStringLength']:
    #         try:
    #             value = elm.attrib[spi_ns_prefix + n]
    #             setattr(self, n, value)
    #         except KeyError:
    #             pass
    #     return self

    def asElem(self):
        e = mkSpiElm("value")
        appendSpiAtribs(self, e, spi_ns_prefix, reqPropNames=['id'],
                        optPropNames=['format', 'bitStringLength', 'resolve'])

        e.text = str(self.text)
        return e


class FileSet():
    def __init__(self):
        self.name = ""
        self.files = []

    def asElem(self):
        e = mkSpiElm("fileSet")
        appendSpiElem(e, "name").text = self.name
        for f in self.files:
            e.append(f.asElem())
        return e


class File():
    _strValues = ["name", "fileType", "userFileType"]

    def __init__(self):
        self.name = ""
        self.fileType = ""
        self.userFileType = ""

    @classmethod
    def fromFileName(cls, fileName):
        self = cls()
        IMPORTED_FILE = "IMPORTED_FILE"
        extDict = {
            ".vhd": ("vhdlSource", IMPORTED_FILE),
            ".tcl": ("tclSource", "XGUI_VERSION_2"),
            ".v":   ("verilogSource", IMPORTED_FILE),
            ".xdc": (None, "xdc"),
        }
        fileType = extDict[os.path.splitext(fileName.lower())[1]]
        if fileType[0] is None:
            del self.fileType
        else:
            self.fileType = fileType[0]

        self.userFileType = fileType[1]
        self.name = fileName
        return self

    def asElem(self):
        e = mkSpiElm("file")
        appendStrElements(
            e, self,
            reqPropNames=[self._strValues[0], ],
            optPropNames=self._strValues[1:])
        return e


class Parameter():
    __slots__ = ["name", 'displayName', "value", 'order']

    def __init__(self):
        self.name = ""
        self.value = Value()

    # @classmethod
    # def fromElem(cls, elm):
    #    self = cls()
    #    self.name = elm.find('spirit:name', ns).text
    #    v = elm.find('spirit:value', ns)
    #    self.value = Value.fromElem(v)
    #    return self

    def asElem(self):
        e = mkSpiElm("parameter")
        appendSpiElem(e, "name").text = self.name
        e.append(self.value.asElem())
        return e

    def asQuartusTcl(self, buff, version):
        name = self.name
        f = self.value.format
        if f == "long":
            t = "INTEGER"
            width = 32
            param_descr = f"{name:s} {t:s} {width:d}"
        elif f == "bool":
            t = "BOOLEAN"
            width = 1
            param_descr = f"{name:s} {t:s} {width:d}"
        elif f == "string":
            t = "STRING"
            param_descr = f"{name:s} {t:s}"
        else:
            raise NotImplementedError(f)

        val = self.value.text

        buff.extend([
            f"add_parameter {param_descr:s}",
            f"set_parameter_property {name:s} DEFAULT_VALUE {val:s}",
            f"set_parameter_property {name:s} DISPLAY_NAME {name:s}",
            f"set_parameter_property {name:s} TYPE {t:s}",
            f"set_parameter_property {name:s} UNITS None",
            f"set_parameter_property {name:s} HDL_PARAMETER true",
        ])


class CoreExtensions():
    def __init__(self):
        self.supportedFamilies = {
            "zynq": "Production",
            "artix7": "Production",
            "kintex7": "Production",
            "virtex7": "Production"
        }
        self.taxonomies = [
            "/BaseIP"
        ]
        self.displayName = ""
        self.coreRevision = ""
        self.coreCreationDateTime = gmtime()

    def asElem(self, displayName, revision):
        r = mkXiElm("coreExtensions")
        sf = appendXiElem(r, "supportedFamilies")
        for family, lifeCycle in self.supportedFamilies.items():
            f = appendXiElem(sf, "family")
            f.text = family
            f.attrib["xilinx:lifeCycle"] = lifeCycle

        ta = appendXiElem(r, "taxonomies")
        for t in self.taxonomies:
            appendXiElem(ta, "taxonomy").text = t

        appendXiElem(r, "displayName").text = displayName
        appendXiElem(r, "coreRevision").text = revision
        appendXiElem(r, "coreCreationDateTime").text = strftime(
            "%Y-%m-%dT%H:%M:%SZ", self.coreCreationDateTime)
        return r


#  [TODO] XILINX_VERSION has to be extracted into some configuration
class VendorExtensions():
    XILINX_VERSION = "2014.4.1"

    def __init__(self):
        self.coreExtensions = CoreExtensions()
        self.packagingInfo = {"xilinxVersion": self.XILINX_VERSION}

    def asElem(self, displayName, revision):
        r = mkSpiElm("vendorExtensions")
        r.append(self.coreExtensions.asElem(displayName, revision))
        pi = appendXiElem(r, "packagingInfo")
        for key, val in self.packagingInfo.items():
            appendXiElem(pi, key).text = val

        return r

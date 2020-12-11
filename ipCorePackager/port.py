from ipCorePackager.helpers import appendSpiElem, \
    mkSpiElm
from ipCorePackager.constants import DIRECTION


class WireTypeDef():
    _requiredVal = ["typeName"]

    # @classmethod
    # def fromElem(cls, elm):
    #     self = cls()
    #     for s in cls._requiredVal:
    #         setattr(self, s, findS(elm, s).text)
    #     self.viewNameRefs = []
    #     for r in elm.findall("spirit:viewNameRef", ns):
    #         self.viewNameRefs.append(r.text)
    #     return self

    def asElem(self):
        e = mkSpiElm("wireTypeDef")
        for s in self._requiredVal:
            appendSpiElem(e, s).text = getattr(self, s)
        for r in self.viewNameRefs:
            appendSpiElem(e, "viewNameRef").text = r
        return e


class Port():
    def __init__(self, packager: "IpCorePackager"):
        self._packager = packager
    # @classmethod
    # def fromElem(cls, elm):
    #     self = cls()
    #     self.name = findS(elm, "name").text
    #     vec = findS(elm, "vector")
    #     if vec is not None:
    #         self.vector = [findS(vec, "left").text, findS(vec, "right").text]
    #     else:
    #         self.vector = None
    #
    #     wire = findS(elm, "wire")
    #     self.direction = findS(wire, "direction").text
    #     self.type = WireTypeDef.fromElem(findS(findS(wire, "wireTypeDefs"),
    #                                            "wiretypedef"))
    #     return self

    @staticmethod
    def fromParams(name: str, direction: DIRECTION,
                   dtype: "HdlType", packager: "IpPackager"):
        port = Port(packager)
        port.name = name
        port.direction = direction.name.lower()
        port.type = WireTypeDef()
        t = port.type

        t.typeName = packager.serializeType(dtype)
        try:
            t.typeName = t.typeName[:t.typeName.index('(')]
        except ValueError:
            pass

        port.vector = packager.getVectorFromType(dtype)
        t.viewNameRefs = ["xilinx_vhdlsynthesis",
                          "xilinx_vhdlbehavioralsimulation"]
        return port

    def asElem(self):
        e = mkSpiElm("port")
        appendSpiElem(e, "name").text = self.name
        w = appendSpiElem(e, "wire")
        appendSpiElem(w, "direction").text = self.direction
        if self.vector:
            v = appendSpiElem(w, "vector")

            def mkBoundary(name, val):
                d = appendSpiElem(v, name)

                d.attrib["spirit:format"] = "long"
                tclVal, tclValOfVal, valConst = self._packager.serialzeValueToTCL(val)
                if valConst:
                    resolve = "immediate"
                    d.text = tclVal
                else:
                    # value is simple type and does not contains generic etc...
                    resolve = 'dependent'
                    d.attrib["spirit:dependency"] = f"({tclVal:s})"
                    d.text = tclValOfVal
                d.attrib["spirit:resolve"] = resolve
            mkBoundary("left", self.vector[0])
            mkBoundary("right", self.vector[1])
        td = appendSpiElem(w, "wireTypeDefs")
        td.append(self.type.asElem())
        return e

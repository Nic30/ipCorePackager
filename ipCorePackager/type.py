from ipCorePackager.helpers import mkSpiElm, spi_ns_prefix


class Type():
    __slots__ = ['name', 'version', 'vendor', 'library']

    #@classmethod
    # def fromElem(cls, elm):
    #    self = cls()
    #    for s in ['name', 'version', 'vendor', 'library']:
    #        setattr(self, s, elm.attrib[spi_ns_prefix + s])
    #    return self

    def asElem(self, elmName):
        e = mkSpiElm(elmName)
        for s in ['name', 'version', 'vendor', 'library']:
            e.attrib[spi_ns_prefix + s] = getattr(self, s)
        return e

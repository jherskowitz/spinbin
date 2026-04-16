import xml.etree.ElementTree as ET


class XspfBase:
    NS = "http://xspf.org/ns/0/"

    def _addAttributesToXml(self, parent, attrs):
        for attr in attrs:
            value = getattr(self, attr)
            if value:
                el = ET.SubElement(parent, "{{{0}}}{1}".format(self.NS, attr))
                el.text = value


if hasattr(ET, "register_namespace"):
    ET.register_namespace("", XspfBase.NS)


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Xspf(XspfBase):
    def __init__(self, obj=None, **kwargs):
        self.version = "1"
        self._title = ""
        self._creator = ""
        self._info = ""
        self._annotation = ""
        self._location = ""
        self._identifier = ""
        self._image = ""
        self._date = ""
        self._license = ""
        self._trackList = []

        if obj:
            if "playlist" in obj:
                obj = obj["playlist"]
            for k, v in obj.items():
                setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def creator(self):
        return self._creator

    @creator.setter
    def creator(self, creator):
        self._creator = creator

    @property
    def annotation(self):
        return self._annotation

    @annotation.setter
    def annotation(self, annotation):
        self._annotation = annotation

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = identifier

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        self._date = date

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, license):
        self._license = license

    @property
    def track(self):
        return self._trackList

    @track.setter
    def track(self, track):
        self.add_track(track)

    def add_track(self, track=None, **kwargs):
        if track is None:
            track = {}
        if isinstance(track, list):
            for t in track:
                self.add_track(t)
        elif isinstance(track, Track):
            self._trackList.append(track)
        elif isinstance(track, dict) and len(track) > 0:
            self._trackList.append(Track(track))
        elif len(kwargs) > 0:
            self._trackList.append(Track(kwargs))

    def toXml(self, encoding="utf-8", pretty_print=True):
        root = ET.Element("{{{0}}}playlist".format(self.NS))
        root.set("version", self.version)
        self._addAttributesToXml(
            root,
            [
                "title", "info", "creator", "annotation",
                "location", "identifier", "image", "date", "license",
            ],
        )
        if len(self._trackList):
            track_list = ET.SubElement(root, "{{{0}}}trackList".format(self.NS))
            for track in self._trackList:
                track.getXmlObject(track_list)
        if pretty_print:
            indent(root)
        return ET.tostring(root, encoding)


class Track(XspfBase):
    def __init__(self, obj=None, **kwargs):
        self._location = ""
        self._identifier = ""
        self._title = ""
        self._creator = ""
        self._annotation = ""
        self._info = ""
        self._image = ""
        self._album = ""
        self._trackNum = ""
        self._duration = ""

        if obj:
            for k, v in obj.items():
                setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = identifier

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def creator(self):
        return self._creator

    @creator.setter
    def creator(self, creator):
        self._creator = creator

    @property
    def annotation(self):
        return self._annotation

    @annotation.setter
    def annotation(self, annotation):
        self._annotation = annotation

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    @property
    def album(self):
        return self._album

    @album.setter
    def album(self, album):
        self._album = album

    @property
    def trackNum(self):
        return self._trackNum

    @trackNum.setter
    def trackNum(self, trackNum):
        self._trackNum = trackNum

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = duration

    def getXmlObject(self, parent):
        track = ET.SubElement(parent, "{{{0}}}track".format(self.NS))
        self._addAttributesToXml(
            track,
            [
                "location", "identifier", "title", "creator",
                "annotation", "info", "image", "album",
                "trackNum", "duration",
            ],
        )
        return parent

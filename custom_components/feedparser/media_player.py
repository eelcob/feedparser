"""NOS News Media Player"""
"""TODO: rotate news on play every x seconds"""
"""TODO: If possible make link be the pressable link in the card"""

import asyncio
import re
import time
import feedparser
import voluptuous as vol
import logging
from datetime import timedelta
from dateutil import parser
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME

from homeassistant.components.media_player.const import (
    MEDIA_TYPE_IMAGE,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
#    SUPPORT_PLAY,
#    SUPPORT_STOP,
#    SUPPORT_PAUSE,
)

try:
    from homeassistant.components.media_player import (
        MediaPlayerEntity as MediaPlayerDevice,
    )
except ImportError:
    from homeassistant.components.media_player import MediaPlayerDevice

SUPPORT_NOS = (
    SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
#    | SUPPORT_PAUSE
#    | SUPPORT_STOP
#    | SUPPORT_PLAY
)

__version__ = "0.0.2"

global number
number = 0

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ["feedparser"]

CONF_FEED_URL = "feed_url"
CONF_DATE_FORMAT = "date_format"
CONF_INCLUSIONS = "inclusions"
CONF_EXCLUSIONS = "exclusions"
CONF_SHOW_TOPN = "show_topn"

DEFAULT_SCAN_INTERVAL = timedelta(hours=1)

COMPONENT_REPO = "https://github.com/eelcob/feedparser/"
SCAN_INTERVAL = timedelta(minutes=2)
ICON = "mdi:rss"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_FEED_URL): cv.string,
        vol.Required(CONF_DATE_FORMAT, default="%a, %b %d %I:%M %p"): cv.string,
        vol.Optional(CONF_SHOW_TOPN, default=9999): cv.positive_int,
        vol.Optional(CONF_INCLUSIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_EXCLUSIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    async_add_devices(
        [
            NOSClient(
                feed=config[CONF_FEED_URL],
                name=config[CONF_NAME],
                date_format=config[CONF_DATE_FORMAT],
                show_topn=config[CONF_SHOW_TOPN],
                inclusions=config[CONF_INCLUSIONS],
                exclusions=config[CONF_EXCLUSIONS],
            )
        ],
        True,
    )

class NOSClient(MediaPlayerDevice):
    def __init__(
        self,
        feed: str,
        name: str,
        date_format: str,
        show_topn: str,
        exclusions: str,
        inclusions: str,
    ):
        self._feed = feed
        self._name = name
        self._date_format = date_format
        self._show_topn = show_topn
        self._inclusions = inclusions
        self._exclusions = exclusions
        self._state = None
        self._entries = []

    def update(self):
        #global num
        parsedFeed = feedparser.parse(self._feed)

        if not parsedFeed:
            return False
        else:
            self._state = (
                self._show_topn
                if len(parsedFeed.entries) > self._show_topn
                else len(parsedFeed.entries)
            )
            self._entries = []

            for entry in parsedFeed.entries[: self._state]:
                entryValue = {}
                for key, value in entry.items():
                    if (
                        (self._inclusions and key not in self._inclusions)
                        or ("parsed" in key)
                        or (key in self._exclusions)
                    ):
                        continue
                    if key in ["published", "updated", "created", "expired"]:
                        value = parser.parse(value).strftime(self._date_format)

                    entryValue[key] = value

                if 'image' in self._inclusions and 'image' not in entryValue.keys():
                    image = []
                    images = []
                    if 'summary' in entry.keys():
                        images = re.findall(r"<img.+?src=\"(.+?)\".+?>", entry['summary'])
                    if images:
                        entryValue['image'] = images[0]
                    else:
                        if 'links' in entry.keys():
                            images = re.findall("\'0\', \'href\': \'(.*jpg)", str(entry['links']))
                        if image:
                            entryValue['image'] = image
                        else:
                            if "media_content" in entry.keys():
                               images = entry['media_content'][0]['url']
                            if images:
                               entryValue['image'] = images[0]
                            else:
                               entryValue['image'] = "https://www.home-assistant.io/images/favicon-192x192-full.png"
                entryValue['entity_picture'] = entryValue['image']
                entryValue['media_title'] = entryValue['title']

                self._entries.append(entryValue)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        key = self.wherearewe()
        return key

    @property
    def media_content_type(self):
        return MEDIA_TYPE_IMAGE

    @property
    def supported_features(self):
        return SUPPORT_NOS

    def wherearewe(self):
        return frozenset(self._entries[number].items())

    def async_media_next_track(self):
        global number
        number = number + 1
        self.wherearewe()

    def async_media_previous_track(self):
        global number
        number = number - 1
        self.wherearewe()

#    async def while_loop():
#        self.media_next_track()
#        await asyncio.sleep(20)
#
#    async def forever():
#        while True:
#            await while_loop()
#
#    def async_media_play_pause(self):
#
#        loop = asyncio.new_event_loop()
#        asyncio.set_event_loop(loop)
#        loop.run_forever(forever)
#
#        #loop.run_until_complete(media_next_track())
#        self.media_next_track()
#        global number
#        while True:
#            number = number + 1
#            self.wherearewe()
#            time.sleep(20)


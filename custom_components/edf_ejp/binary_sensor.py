"""
Support for ejp site.


configuration.yaml

sensor:
  - platform: edf_ejp
    regions:
      - ouest
      - sud
      - paca
      - nord
"""
import logging
from datetime import timedelta
from datetime import datetime
import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import ( CONF_RESOURCES)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import BinarySensorDevice

__version__ = '0.0.1'

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(days=1)
now = datetime.today()

SENSOR_PREFIX = 'EJP '

SENSOR_TYPES = {
    'jour': ['today', '', 'mdi:flash'],
    'tomorrow': ['tomorrow', '', 'mdi:flash'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
        vol.Required('regions', default=[]):
        vol.All(cv.ensure_list, [vol.In({'ouest','paca','nord','sud'})])
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the ejp sensors."""

    try:
        data = EJPData()
    except requests.exceptions.HTTPError as error:
        _LOGGER.error(error)
        return False

    entities = []
    
    for resource in SENSOR_TYPES:
        sensor_type = resource.lower()
        for region in config['regions']:
           entities.append(EjpSensor(data, sensor_type, region))

    add_entities(entities)


# pylint: disable=abstract-method
class EJPData(object):
    """Representation of a Ejp data."""

    def __init__(self):
        """Initialize the data."""
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data."""
        try:
            """"""
            self.data = requests.get('https://particulier.edf.fr/bin/edf_rc/servlets/ejptemponew?Date_a_remonter='+now.strftime('%Y-%m-%d')+'&TypeAlerte=EJP', timeout=5).json()
            _LOGGER.debug("Data = %s", self.data)
        except requests.exceptions.RequestException:
            _LOGGER.error("Error occurred while fetching data.")
            self.data = None
            return False

class EjpSensor(BinarySensorDevice):
    """Representation of a Ejp Sensor."""

    def __init__(self, data, sensor_type,region):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type
        self.region = region
        self._name = SENSOR_PREFIX + region + '_' +SENSOR_TYPES[self.type][0]
        self._unit = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor. (total/current power consumption/production or total gas used)"""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        self.data.update()
        energy = self.data.data
        value = None
        
        if self.region+'_'+self.type == 'ouest_jour':
            value = energy["JourJ"]["EjpOuest"]
        elif self.region+'_'+self.type == 'paca_jour':
            value = energy["JourJ"]["EjpPaca"]
        elif self.region+'_'+self.type == 'sud_jour':
            value = energy["JourJ"]["EjpSud"]
        elif self.region+'_'+self.type == 'nord_jour':
            value = energy["JourJ"]["EjpNord"]
        if self.region+'_'+self.type == 'ouest_tomorrow':
            value = energy["JourJ1"]["EjpOuest"]
        elif self.region+'_'+self.type == 'paca_tomorrow':
            value = energy["JourJ1"]["EjpPaca"]
        elif self.region+'_'+self.type == 'sud_tomorrow':
            value = energy["JourJ1"]["EjpSud"]
        elif self.region+'_'+self.type == 'nord_tomorrow':
            value = energy["JourJ1"]["EjpNord"]
            
        self._state = value == 'EJP'

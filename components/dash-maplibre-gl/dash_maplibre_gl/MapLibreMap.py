# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class MapLibreMap(Component):
    """A MapLibreMap component.
MapLibreMap wraps MapLibre GL JS as a Dash component: a token-free, WebGL
3D map that starts flat (pitch/bearing 0) and lets the user drag to tilt
and rotate in 3D, switch between raster basemaps, drape the interferogram
raster overlay, and displace the surface with DEM terrain relief.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- activeBasemap (string; optional):
    Key into `basemaps` for the currently visible basemap layer.

- basemaps (dict; optional):
    Map of basemap id -> {url, attribution, tileSize}. Each entry
    becomes a raster source/layer; visibility is toggled by
    activeBasemap instead of swapping the whole style.

    `basemaps` is a dict with strings as keys and values of type dict
    with keys:

    - attribution (string; optional)

    - tileSize (number; optional)

    - url (string; optional)

- className (string; default ''):
    CSS class applied to the map container div.

- demEncoding (a value equal to: 'terrarium', 'mapbox'; default 'mapbox'):
    Encoding used by the raster-DEM tiles: 'terrarium' (e.g. AWS Open
    Data's elevation-tiles-prod) or 'mapbox' (Mapbox Terrain-RGB).

- demTiles (string | list of strings; optional):
    Raster-DEM tile URL template(s) (Mapbox terrain-RGB encoding) used
    to displace the terrain surface. Null disables terrain.

- earthquakeData (dict; default {type: 'FeatureCollection', features: []}):
    GeoJSON FeatureCollection of earthquake epicenters; each feature's
    properties should include magnitude, quakeColour, time, depthKm,
    eventId.

- flyTo (dict; optional):
    Write-only camera animation trigger: {longitude, latitude, zoom,
    duration}. Set a new object to fly the camera, mirroring Leaflet's
    flyTo transition.

    `flyTo` is a dict with keys:

    - duration (number; optional)

    - latitude (number; optional)

    - longitude (number; optional)

    - zoom (number; optional)

- initialViewState (dict; default {    longitude: -123.6, latitude: 54.64, zoom: 6, pitch: 0, bearing: 0,}):
    Camera at construction time: {longitude, latitude, zoom, pitch,
    bearing}. Pitch/bearing default to 0 so the map starts
    flat/top-down like a 2D map; the user can then drag to tilt and
    rotate in 3D.

    `initialViewState` is a dict with keys:

    - bearing (number; optional)

    - latitude (number; optional)

    - longitude (number; optional)

    - pitch (number; optional)

    - zoom (number; optional)

- interferogramOpacity (number; default 0.85):
    Opacity of the interferogram raster layer.

- interferogramTileUrl (string; optional):
    XYZ tile URL template ({x}/{y}/{z}) for the interferogram raster
    overlay, fetched TMS-scheme from the existing /getTileUrl proxy.

- style (dict; optional):
    CSS style applied to the map container div.

- terrainExaggeration (number; default 1.5):
    Vertical exaggeration factor applied to the DEM terrain.

- wmsOverlay (dict; optional):
    Optional WMS raster overlay (e.g. glacier footprints): {url,
    layers, styles, format, opacity, visible}.

    `wmsOverlay` is a dict with keys:

    - format (string; optional)

    - layers (string; optional)

    - opacity (number; optional)

    - styles (string; optional)

    - url (string; optional)

    - visible (boolean; optional)"""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_maplibre_gl'
    _type = 'MapLibreMap'
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, initialViewState=Component.UNDEFINED, flyTo=Component.UNDEFINED, basemaps=Component.UNDEFINED, activeBasemap=Component.UNDEFINED, interferogramTileUrl=Component.UNDEFINED, interferogramOpacity=Component.UNDEFINED, demTiles=Component.UNDEFINED, demEncoding=Component.UNDEFINED, terrainExaggeration=Component.UNDEFINED, earthquakeData=Component.UNDEFINED, wmsOverlay=Component.UNDEFINED, style=Component.UNDEFINED, className=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'activeBasemap', 'basemaps', 'className', 'demEncoding', 'demTiles', 'earthquakeData', 'flyTo', 'initialViewState', 'interferogramOpacity', 'interferogramTileUrl', 'style', 'terrainExaggeration', 'wmsOverlay']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'activeBasemap', 'basemaps', 'className', 'demEncoding', 'demTiles', 'earthquakeData', 'flyTo', 'initialViewState', 'interferogramOpacity', 'interferogramTileUrl', 'style', 'terrainExaggeration', 'wmsOverlay']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(MapLibreMap, self).__init__(**args)

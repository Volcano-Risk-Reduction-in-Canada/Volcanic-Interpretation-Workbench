import React from 'react';
import PropTypes from 'prop-types';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const INTERFEROGRAM_SOURCE_ID = 'interferogram';
const INTERFEROGRAM_LAYER_ID = 'interferogram-layer';
const INTERFEROGRAM_MAX_ZOOM = 15;
const DEM_SOURCE_ID = 'dem-terrain';
// Terrain only needs to look plausible, not sharp -- capping it well below
// the interferogram's native max zoom (15) keeps fewer/coarser DEM tile
// requests in flight, freeing up the browser's ~6-concurrent-connections-
// per-origin cap for interferogram tile fetches instead. Raise this if
// terrain looks too blocky up close, lower it if terrain still competes
// for bandwidth against the interferogram layer.
const DEM_MAX_ZOOM = 10;
const HILLSHADE_LAYER_ID = 'hillshade-layer';
const EARTHQUAKES_SOURCE_ID = 'earthquakes';
const EARTHQUAKES_LAYER_ID = 'earthquakes-layer';
const WMS_SOURCE_ID = 'wms-overlay';
const WMS_LAYER_ID = 'wms-overlay-layer';
const POINTS_SOURCE_ID = 'ts-points';
const POINTS_LAYER_ID = 'ts-points-layer';
// Layer name inside the vector tiles (tippecanoe --layer, see
// scripts/build_point_tiles.py).
const POINTS_SOURCE_LAYER = 'points';
const SELECTED_POINT_SOURCE_ID = 'ts-selected-point';
const SELECTED_POINT_LAYER_ID = 'ts-selected-point-layer';
// Half-width (px) of the box searched around a click: dots are only 1-3px
// across at mid zooms, so an exact-pixel hit test would be frustrating.
const POINT_CLICK_TOLERANCE = 5;

// Bottom-to-top stacking of overlay layers (basemaps sit beneath them all).
// Layers are removed/re-added at runtime (new interferogram URL, new DEM,
// points toggled with the Timeseries tab) and MapLibre appends a re-added
// layer on top by default -- see beforeIdFor().
const OVERLAY_ORDER = [
    HILLSHADE_LAYER_ID,
    INTERFEROGRAM_LAYER_ID,
    POINTS_LAYER_ID,
    SELECTED_POINT_LAYER_ID,
    WMS_LAYER_ID,
    EARTHQUAKES_LAYER_ID,
];

const EMPTY_FC = {type: 'FeatureCollection', features: []};

const DEFAULT_POINT_STYLE = {
    property: 'rate',
    min: -25,
    max: 25,
    stops: [[-1, '#d7191c'], [0, '#ffffbf'], [1, '#2b83ba']],
};

/**
 * Resolve a (possibly relative) tile URL template against the page.
 * MapLibre fetches vector tiles from a Web Worker, whose base URL is a
 * blob: URL that a relative path like '/getPointTile?...' can't resolve
 * against -- the tiles then sit in 'loading' forever with no error. (Raster
 * and DEM tiles load on the main thread, so their relative URLs are fine.)
 */
function absoluteUrl(url) {
    // Undo any escaping of the {z}/{x}/{y} placeholders.
    return new URL(url, window.location.href).href
        .replace(/%7B/gi, '{').replace(/%7D/gi, '}');
}

/**
 * Data value of a colour-stop position (-1..1) for the range [lo, hi].
 * When the range spans zero, position 0 is pinned to 0 and each side
 * scales to its own half of the range (so an asymmetric range like
 * [-10, 20] still diverges at zero); otherwise -1..1 spreads linearly over
 * lo..hi. Mirrored by _stop_value in timeseries_components.py (colourbar).
 */
function stopValue(position, lo, hi) {
    if (lo < 0 && hi > 0) {
        return position < 0 ? -position * lo : position * hi;
    }
    return lo + ((hi - lo) * (position + 1)) / 2;
}

/**
 * MapLibre 'circle-color' expression for pointStyle: its [position, colour]
 * stops placed on the [min, max] range by stopValue(), interpolated in Lab
 * space for an even perceptual gradient between them.
 */
function pointColorExpression(pointStyle) {
    const {property, min, max, stops} = {...DEFAULT_POINT_STYLE, ...pointStyle};
    const lo = Math.min(min, max);
    const hi = max > min ? max : lo + 1;
    const expression = [
        'interpolate-lab', ['linear'], ['to-number', ['get', property], 0],
    ];
    [...stops].sort((a, b) => a[0] - b[0]).forEach(([position, color]) => {
        expression.push(stopValue(position, lo, hi), color);
    });
    return expression;
}

// MapLibre's built-in NavigationControl compass is a small, easy-to-miss
// icon. This is a plain-text "N" indicator that always stays legible
// (independent of whatever Bootstrap theme the host page applies) and
// rotates to keep pointing at true north as the map's bearing changes.
class NorthArrowControl {
    onAdd(map) {
        this._map = map;
        this._container = document.createElement('div');
        this._container.className = 'maplibregl-ctrl maplibregl-ctrl-group';
        this._container.style.cssText = (
            'background:#fff; width:29px; height:29px; display:flex;'
            + 'align-items:center; justify-content:center;'
        );
        this._arrow = document.createElement('div');
        this._arrow.style.cssText = (
            'font-weight:700; font-size:13px; color:#1a1a1a; line-height:1;'
        );
        this._arrow.textContent = 'N';
        this._container.appendChild(this._arrow);
        this._onRotate = () => {
            this._arrow.style.transform = `rotate(${-map.getBearing()}deg)`;
        };
        map.on('rotate', this._onRotate);
        this._onRotate();
        return this._container;
    }

    onRemove() {
        this._container.parentNode.removeChild(this._container);
        this._map.off('rotate', this._onRotate);
        this._map = undefined;
    }
}

function buildBaseStyle(basemaps, activeBasemap, monochrome) {
    const sources = {};
    const layers = [];
    const activeEntry = basemaps[activeBasemap] || {};
    Object.keys(basemaps).forEach((key) => {
        const basemap = basemaps[key];
        if (basemap.hillshade) {
            // Virtual entry (e.g. "Topography (Hillshade)") -- no raster
            // source/layer of its own, it reuses an existing basemap's
            // tiles (via baseKey) plus the hillshade layer added
            // separately in addHillshadeLayer().
            return;
        }
        sources[key] = {
            type: 'raster',
            tiles: [basemap.url],
            tileSize: basemap.tileSize || 256,
            attribution: basemap.attribution || '',
        };
        if (basemap.maxzoom) {
            // Overzoom past the provider's deepest tiles instead of
            // requesting (blank/"no data") tiles that don't exist.
            sources[key].maxzoom = basemap.maxzoom;
        }
        layers.push({
            id: `basemap-${key}`,
            type: 'raster',
            source: key,
            layout: {
                visibility: (
                    key === activeBasemap || activeEntry.baseKey === key
                ) ? 'visible' : 'none',
            },
            paint: {'raster-saturation': monochrome ? -1 : 0},
        });
    });
    return {version: 8, sources, layers};
}

/**
 * MapLibreMap wraps MapLibre GL JS as a Dash component: a token-free, WebGL
 * 3D map that starts flat (pitch/bearing 0) and lets the user drag to tilt
 * and rotate in 3D, switch between raster basemaps, drape the interferogram
 * raster overlay, and displace the surface with DEM terrain relief.
 */
export default class MapLibreMap extends React.Component {
    constructor(props) {
        super(props);
        this.containerRef = React.createRef();
        this.map = null;
        // Set once the 'load' handler has added the overlay layers. Prop
        // updates gate on this rather than map.isStyleLoaded(), which is
        // false whenever *any* source still has tiles in flight -- with
        // basemap/DEM/point tiles streaming in, that silently dropped
        // updates (e.g. a basemap switch) made mid-load.
        this.overlaysReady = false;
        // flyTo received before the overlays were ready; see flyCamera().
        this.pendingFlyTo = null;
    }

    isReady() {
        return Boolean(this.map && this.overlaysReady);
    }

    componentDidMount() {
        const {initialViewState, basemaps, activeBasemap, basemapMonochrome} = this.props;

        const map = new maplibregl.Map({
            container: this.containerRef.current,
            style: buildBaseStyle(basemaps, activeBasemap, basemapMonochrome),
            center: [initialViewState.longitude, initialViewState.latitude],
            zoom: initialViewState.zoom,
            pitch: initialViewState.pitch || 0,
            bearing: initialViewState.bearing || 0,
            // 85 is MapLibre's hard-coded upper bound (it throws above
            // this). Note terrain here is a 2.5D heightmap drape, not a
            // volumetric model, so there's no literal subsurface geometry
            // to reveal -- this just allows a near-horizontal, more
            // dramatic viewing angle than the library's 60 degree default.
            maxPitch: 85,
        });
        this.map = map;

        map.addControl(
            new maplibregl.NavigationControl({visualizePitch: true}),
            'top-right',
        );
        map.addControl(new NorthArrowControl(), 'top-right');

        map.on('load', () => this.addOverlayLayers());
        // Registered once here, not in addPointsLayers(), since the points
        // layer is added/removed every time the Timeseries tab toggles.
        // MapLibre's layer-delegated mouseenter/mouseleave skip a missing
        // layer, and handlePointClick checks for it itself.
        map.on('click', (e) => this.handlePointClick(e));
        map.on('mouseenter', POINTS_LAYER_ID, () => {
            map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', POINTS_LAYER_ID, () => {
            map.getCanvas().style.cursor = '';
        });
    }

    componentDidUpdate(prevProps) {
        const {map} = this;
        if (!map) {
            return;
        }

        if (prevProps.activeBasemap !== this.props.activeBasemap) {
            this.setActiveBasemap(this.props.activeBasemap);
        }
        if (prevProps.basemapMonochrome !== this.props.basemapMonochrome) {
            this.updateBasemapMonochrome();
        }
        if (prevProps.interferogramTileUrl !== this.props.interferogramTileUrl) {
            this.updateInterferogramSource();
        } else {
            if (prevProps.interferogramOpacity !== this.props.interferogramOpacity) {
                this.updateInterferogramOpacity();
            }
            if (prevProps.interferogramVisible !== this.props.interferogramVisible) {
                this.updateInterferogramVisibility();
            }
        }
        if (prevProps.pointSource !== this.props.pointSource) {
            this.updatePointsSource();
        } else if (prevProps.pointStyle !== this.props.pointStyle) {
            this.updatePointStyle();
        }
        if (
            prevProps.demTiles !== this.props.demTiles
            || prevProps.terrainExaggeration !== this.props.terrainExaggeration
        ) {
            this.updateTerrain();
        }
        if (prevProps.earthquakeData !== this.props.earthquakeData) {
            this.updateEarthquakes();
        }
        if (prevProps.wmsOverlay !== this.props.wmsOverlay) {
            this.updateWmsOverlay();
        }
        if (prevProps.flyTo !== this.props.flyTo && this.props.flyTo) {
            this.flyCamera(this.props.flyTo);
        }
    }

    flyCamera(flyTo) {
        // MapLibre (3.6) crashes its render loop -- freezing the map -- if
        // terrain is attached mid-animation: each frame reads a terrain
        // elevation centre that's only set when terrain existed as the
        // animation began. Dash fires flyTo callbacks on page load, before
        // 'load' has attached terrain, so hold the flight until then.
        if (!this.isReady()) {
            this.pendingFlyTo = flyTo;
            return;
        }
        const {longitude, latitude, zoom, duration} = flyTo;
        this.map.flyTo({
            center: [longitude, latitude],
            zoom,
            duration: duration === undefined ? 2000 : duration,
        });
    }

    componentWillUnmount() {
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
    }

    addOverlayLayers() {
        // Each layer touches a different, independently-flaky external
        // source (S3, a third-party WMS service). Isolate them so one
        // throwing (e.g. a WMS error response MapLibre can't decode as an
        // image) can't stop the others -- terrain goes first since it's
        // core to every site view, unlike the decorative overlays.
        const steps = [
            () => this.addTerrain(),
            () => this.addHillshadeLayer(),
            () => this.addInterferogramLayer(),
            () => this.addPointsLayers(),
            () => this.addWmsLayer(),
            () => this.addEarthquakesLayer(),
        ];
        steps.forEach((step) => {
            try {
                step();
            } catch (error) {
                console.error('MapLibreMap: failed to add overlay layer', error);
            }
        });
        this.overlaysReady = true;
        if (this.pendingFlyTo) {
            const flyTo = this.pendingFlyTo;
            this.pendingFlyTo = null;
            this.flyCamera(flyTo);
        }
    }

    /**
     * Id of the first already-present overlay layer that `layerId` should
     * sit beneath (per OVERLAY_ORDER), for map.addLayer's beforeId; or
     * undefined to append on top.
     */
    beforeIdFor(layerId) {
        const {map} = this;
        const above = OVERLAY_ORDER.slice(OVERLAY_ORDER.indexOf(layerId) + 1);
        return above.find((id) => map.getLayer(id));
    }

    addInterferogramLayer() {
        const {map} = this;
        const {interferogramTileUrl, interferogramOpacity, interferogramVisible} = this.props;
        if (!interferogramTileUrl || map.getSource(INTERFEROGRAM_SOURCE_ID)) {
            return;
        }
        map.addSource(INTERFEROGRAM_SOURCE_ID, {
            type: 'raster',
            tiles: [interferogramTileUrl],
            tileSize: 256,
            scheme: 'tms',
            maxzoom: INTERFEROGRAM_MAX_ZOOM,
        });
        map.addLayer({
            id: INTERFEROGRAM_LAYER_ID,
            type: 'raster',
            source: INTERFEROGRAM_SOURCE_ID,
            // fade-duration 0: snap newly-loaded, correct-resolution tiles
            // in immediately instead of cross-fading over the 300ms
            // default, so the layer looks sharp again as soon as data
            // arrives rather than lingering blurry through a fade.
            paint: {'raster-opacity': interferogramOpacity, 'raster-fade-duration': 0},
            layout: {visibility: interferogramVisible ? 'visible' : 'none'},
        }, this.beforeIdFor(INTERFEROGRAM_LAYER_ID));
    }

    updateInterferogramSource() {
        const {map} = this;
        if (!this.isReady()) {
            return;
        }
        if (map.getLayer(INTERFEROGRAM_LAYER_ID)) {
            map.removeLayer(INTERFEROGRAM_LAYER_ID);
        }
        if (map.getSource(INTERFEROGRAM_SOURCE_ID)) {
            map.removeSource(INTERFEROGRAM_SOURCE_ID);
        }
        this.addInterferogramLayer();
    }

    updateInterferogramOpacity() {
        const {map} = this;
        if (!this.isReady() || !map.getLayer(INTERFEROGRAM_LAYER_ID)) {
            return;
        }
        map.setPaintProperty(
            INTERFEROGRAM_LAYER_ID, 'raster-opacity', this.props.interferogramOpacity
        );
    }

    updateInterferogramVisibility() {
        const {map} = this;
        if (!this.isReady() || !map.getLayer(INTERFEROGRAM_LAYER_ID)) {
            return;
        }
        // A hidden layer's source stops requesting tiles, unlike opacity 0.
        map.setLayoutProperty(
            INTERFEROGRAM_LAYER_ID, 'visibility',
            this.props.interferogramVisible ? 'visible' : 'none'
        );
    }

    addPointsLayers() {
        const {map} = this;
        const {pointSource, pointStyle} = this.props;
        if (!pointSource || !pointSource.url || map.getSource(POINTS_SOURCE_ID)) {
            return;
        }
        const source = {
            type: 'vector',
            tiles: [absoluteUrl(pointSource.url)],
            // MBTiles rows are TMS-ordered; /getPointTile passes y through.
            scheme: 'tms',
            minzoom: pointSource.minzoom === undefined ? 0 : pointSource.minzoom,
            maxzoom: pointSource.maxzoom === undefined ? 14 : pointSource.maxzoom,
        };
        if (pointSource.bounds) {
            // Skip requesting tiles outside the data extent.
            source.bounds = pointSource.bounds;
        }
        map.addSource(POINTS_SOURCE_ID, source);
        map.addLayer({
            id: POINTS_LAYER_ID,
            type: 'circle',
            source: POINTS_SOURCE_ID,
            'source-layer': POINTS_SOURCE_LAYER,
            paint: {
                'circle-color': pointColorExpression(pointStyle),
                'circle-radius': [
                    'interpolate', ['linear'], ['zoom'],
                    8, 1, 12, 1.5, 14, 3, 16, 6, 18, 10,
                ],
                // Faint outline once dots are big enough to separate, so
                // pale (near-zero, cream) dots stay visible on light
                // hillshade; none when zoomed out, where it would only
                // darken the dot field.
                'circle-stroke-color': 'rgba(0, 0, 0, 0.35)',
                'circle-stroke-width': [
                    'interpolate', ['linear'], ['zoom'],
                    13, 0, 15, 0.6, 18, 1,
                ],
            },
        }, this.beforeIdFor(POINTS_LAYER_ID));
        map.addSource(SELECTED_POINT_SOURCE_ID, {type: 'geojson', data: EMPTY_FC});
        map.addLayer({
            id: SELECTED_POINT_LAYER_ID,
            type: 'circle',
            source: SELECTED_POINT_SOURCE_ID,
            paint: {
                'circle-radius': [
                    'interpolate', ['linear'], ['zoom'],
                    8, 5, 14, 7, 16, 9, 18, 13,
                ],
                'circle-color': 'rgba(0, 0, 0, 0)',
                'circle-stroke-color': '#000000',
                'circle-stroke-width': 2.5,
            },
        }, this.beforeIdFor(SELECTED_POINT_LAYER_ID));
    }

    removePointsLayers() {
        const {map} = this;
        [SELECTED_POINT_LAYER_ID, POINTS_LAYER_ID].forEach((layerId) => {
            if (map.getLayer(layerId)) {
                map.removeLayer(layerId);
            }
        });
        [SELECTED_POINT_SOURCE_ID, POINTS_SOURCE_ID].forEach((sourceId) => {
            if (map.getSource(sourceId)) {
                map.removeSource(sourceId);
            }
        });
    }

    updatePointsSource() {
        if (!this.isReady()) {
            return;
        }
        // Also drops the selection ring: a new source means a different
        // site/beam (or the Timeseries tab closing).
        this.removePointsLayers();
        this.addPointsLayers();
    }

    updatePointStyle() {
        const {map} = this;
        if (!this.isReady() || !map.getLayer(POINTS_LAYER_ID)) {
            return;
        }
        // Paint-only change: recolours from the tiles already loaded, no
        // refetch.
        map.setPaintProperty(
            POINTS_LAYER_ID, 'circle-color', pointColorExpression(this.props.pointStyle)
        );
    }

    handlePointClick(e) {
        const {map} = this;
        if (!this.isReady() || !map.getLayer(POINTS_LAYER_ID)) {
            return;
        }
        const {x, y} = e.point;
        const tol = POINT_CLICK_TOLERANCE;
        const features = map.queryRenderedFeatures(
            [[x - tol, y - tol], [x + tol, y + tol]], {layers: [POINTS_LAYER_ID]}
        );
        if (!features.length) {
            return;
        }
        // Several dots can fall inside the tolerance box -- take the one
        // drawn nearest the cursor.
        let nearest = null;
        let nearestDist = Infinity;
        features.forEach((feature) => {
            const p = map.project(feature.geometry.coordinates);
            const dist = ((p.x - x) ** 2) + ((p.y - y) ** 2);
            if (dist < nearestDist) {
                nearest = feature;
                nearestDist = dist;
            }
        });
        const [longitude, latitude] = nearest.geometry.coordinates;
        map.getSource(SELECTED_POINT_SOURCE_ID).setData({
            type: 'FeatureCollection',
            features: [{
                type: 'Feature',
                geometry: {type: 'Point', coordinates: [longitude, latitude]},
                properties: {},
            }],
        });
        if (this.props.setProps) {
            this.props.setProps({
                clickedPoint: {
                    fid: nearest.id,
                    longitude,
                    latitude,
                    // Distinguishes a re-click of the same point as a new
                    // event for Dash.
                    timestamp: Date.now(),
                },
            });
        }
    }

    addEarthquakesLayer() {
        const {map} = this;
        if (map.getSource(EARTHQUAKES_SOURCE_ID)) {
            return;
        }
        const data = this.props.earthquakeData || EMPTY_FC;
        map.addSource(EARTHQUAKES_SOURCE_ID, {type: 'geojson', data});
        map.addLayer({
            id: EARTHQUAKES_LAYER_ID,
            type: 'circle',
            source: EARTHQUAKES_SOURCE_ID,
            paint: {
                'circle-radius': ['*', 3, ['coalesce', ['get', 'magnitude'], 1]],
                'circle-color': ['coalesce', ['get', 'quakeColour'], '#ffffff'],
                'circle-opacity': 0.6,
                'circle-stroke-color': '#000000',
                'circle-stroke-width': 1,
            },
        }, this.beforeIdFor(EARTHQUAKES_LAYER_ID));
        map.on('click', EARTHQUAKES_LAYER_ID, (e) => {
            const feature = e.features && e.features[0];
            if (!feature) {
                return;
            }
            const p = feature.properties;
            // Inline-styled: the host page's Bootstrap theme (e.g. Darkly)
            // sets a global text color that otherwise bleeds into
            // MapLibre's un-namespaced popup DOM, making white text land
            // on the popup's own white background.
            const html = '<div style="color:#1a1a1a; font-size:13px; line-height:1.5;">'
                + `Magnitude: ${p.magnitude} ${p.magType || ''}<br/>`
                + `Date: ${p.time ? String(p.time).slice(0, 10) : ''}<br/>`
                + `Depth: ${p.depthKm} km<br/>`
                + `EventID: ${p.eventId}`
                + '</div>';
            new maplibregl.Popup()
                .setLngLat(feature.geometry.coordinates)
                .setHTML(html)
                .addTo(map);
        });
        map.on('mouseenter', EARTHQUAKES_LAYER_ID, () => {
            map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', EARTHQUAKES_LAYER_ID, () => {
            map.getCanvas().style.cursor = '';
        });
    }

    updateEarthquakes() {
        const {map} = this;
        if (!this.isReady()) {
            return;
        }
        const source = map.getSource(EARTHQUAKES_SOURCE_ID);
        const data = this.props.earthquakeData || EMPTY_FC;
        if (source) {
            source.setData(data);
        } else {
            this.addEarthquakesLayer();
        }
    }

    addWmsLayer() {
        const {map} = this;
        const {wmsOverlay} = this.props;
        if (!wmsOverlay || !wmsOverlay.url || map.getSource(WMS_SOURCE_ID)) {
            return;
        }
        const params = new URLSearchParams({
            service: 'WMS',
            request: 'GetMap',
            version: '1.1.1',
            layers: wmsOverlay.layers,
            styles: wmsOverlay.styles || '',
            format: wmsOverlay.format || 'image/png',
            transparent: 'true',
            width: '256',
            height: '256',
            srs: 'EPSG:3857',
        });
        const tileUrl = `${wmsOverlay.url}?${params.toString()}&bbox={bbox-epsg-3857}`;
        map.addSource(WMS_SOURCE_ID, {
            type: 'raster',
            tiles: [tileUrl],
            tileSize: 256,
        });
        map.addLayer({
            id: WMS_LAYER_ID,
            type: 'raster',
            source: WMS_SOURCE_ID,
            paint: {
                'raster-opacity': wmsOverlay.opacity === undefined ? 0.5 : wmsOverlay.opacity,
            },
            layout: {visibility: wmsOverlay.visible === false ? 'none' : 'visible'},
        }, this.beforeIdFor(WMS_LAYER_ID));
    }

    updateWmsOverlay() {
        const {map} = this;
        if (!this.isReady()) {
            return;
        }
        if (map.getLayer(WMS_LAYER_ID)) {
            map.removeLayer(WMS_LAYER_ID);
        }
        if (map.getSource(WMS_SOURCE_ID)) {
            map.removeSource(WMS_SOURCE_ID);
        }
        this.addWmsLayer();
    }

    setActiveBasemap(activeBasemap) {
        const {map} = this;
        const {basemaps} = this.props;
        if (!this.isReady()) {
            return;
        }
        const activeEntry = basemaps[activeBasemap] || {};
        Object.keys(basemaps).forEach((key) => {
            const entry = basemaps[key];
            if (entry.hillshade) {
                return;
            }
            const layerId = `basemap-${key}`;
            if (map.getLayer(layerId)) {
                const visible = key === activeBasemap || activeEntry.baseKey === key;
                map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
            }
        });
        if (map.getLayer(HILLSHADE_LAYER_ID)) {
            map.setLayoutProperty(
                HILLSHADE_LAYER_ID, 'visibility', activeEntry.hillshade ? 'visible' : 'none'
            );
        }
    }

    updateBasemapMonochrome() {
        const {map} = this;
        const {basemaps, basemapMonochrome} = this.props;
        if (!this.isReady()) {
            return;
        }
        // Applied to every basemap layer unconditionally (not just the
        // active one) -- MapLibre retains paint properties on hidden
        // layers, so switching basemaps later needs no extra hook here.
        Object.keys(basemaps).forEach((key) => {
            const layerId = `basemap-${key}`;
            if (map.getLayer(layerId)) {
                map.setPaintProperty(
                    layerId, 'raster-saturation', basemapMonochrome ? -1 : 0
                );
            }
        });
    }

    addTerrain() {
        const {map} = this;
        const {demTiles, demEncoding, terrainExaggeration} = this.props;
        if (!demTiles || map.getSource(DEM_SOURCE_ID)) {
            return;
        }
        map.addSource(DEM_SOURCE_ID, {
            type: 'raster-dem',
            tiles: Array.isArray(demTiles) ? demTiles : [demTiles],
            tileSize: 256,
            encoding: demEncoding || 'mapbox',
            maxzoom: DEM_MAX_ZOOM,
        });
        // Same render-loop crash as in flyCamera() for any other camera
        // animation in flight (e.g. drag inertia from panning while the
        // page loads) -- end it before terrain goes on.
        map.stop();
        map.setTerrain({source: DEM_SOURCE_ID, exaggeration: terrainExaggeration || 1});
    }

    addHillshadeLayer() {
        const {map} = this;
        const {basemaps, activeBasemap} = this.props;
        if (!map.getSource(DEM_SOURCE_ID) || map.getLayer(HILLSHADE_LAYER_ID)) {
            return;
        }
        const activeEntry = (basemaps && basemaps[activeBasemap]) || {};
        map.addLayer({
            id: HILLSHADE_LAYER_ID,
            type: 'hillshade',
            source: DEM_SOURCE_ID,
            layout: {visibility: activeEntry.hillshade ? 'visible' : 'none'},
            paint: {
                'hillshade-illumination-direction': 335,
                'hillshade-exaggeration': 0.6,
                'hillshade-shadow-color': '#3a3a3a',
                'hillshade-highlight-color': '#ffffff',
                'hillshade-accent-color': '#5a5a5a',
            },
        }, this.beforeIdFor(HILLSHADE_LAYER_ID));
    }

    updateTerrain() {
        const {map} = this;
        const {demTiles} = this.props;
        if (!this.isReady()) {
            return;
        }
        // The hillshade layer (if present) references DEM_SOURCE_ID, and
        // MapLibre refuses to remove a source still in use by a layer --
        // tear it down here and re-add it below, alongside the source.
        if (map.getLayer(HILLSHADE_LAYER_ID)) {
            map.removeLayer(HILLSHADE_LAYER_ID);
        }
        if (!demTiles) {
            map.setTerrain(null);
            if (map.getSource(DEM_SOURCE_ID)) {
                map.removeSource(DEM_SOURCE_ID);
            }
            return;
        }
        if (map.getSource(DEM_SOURCE_ID)) {
            map.removeSource(DEM_SOURCE_ID);
        }
        this.addTerrain();
        this.addHillshadeLayer();
    }

    render() {
        return (
            <div
                id={this.props.id}
                ref={this.containerRef}
                style={{width: '100%', height: '100%', ...this.props.style}}
                className={this.props.className}
            />
        );
    }
}

MapLibreMap.defaultProps = {
    initialViewState: {
        longitude: -123.6, latitude: 54.64, zoom: 6, pitch: 0, bearing: 0,
    },
    basemaps: {},
    activeBasemap: null,
    basemapMonochrome: false,
    interferogramTileUrl: null,
    interferogramOpacity: 0.85,
    interferogramVisible: true,
    pointSource: null,
    pointStyle: DEFAULT_POINT_STYLE,
    clickedPoint: null,
    demTiles: null,
    demEncoding: 'mapbox',
    terrainExaggeration: 1.5,
    earthquakeData: EMPTY_FC,
    wmsOverlay: null,
    flyTo: null,
    style: {},
    className: '',
};

MapLibreMap.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Camera at construction time: {longitude, latitude, zoom, pitch,
     * bearing}. Pitch/bearing default to 0 so the map starts flat/top-down
     * like a 2D map; the user can then drag to tilt and rotate in 3D.
     */
    initialViewState: PropTypes.shape({
        longitude: PropTypes.number,
        latitude: PropTypes.number,
        zoom: PropTypes.number,
        pitch: PropTypes.number,
        bearing: PropTypes.number,
    }),

    /**
     * Write-only camera animation trigger: {longitude, latitude, zoom,
     * duration}. Set a new object to fly the camera, mirroring Leaflet's
     * flyTo transition.
     */
    flyTo: PropTypes.shape({
        longitude: PropTypes.number,
        latitude: PropTypes.number,
        zoom: PropTypes.number,
        duration: PropTypes.number,
    }),

    /**
     * Map of basemap id -> {url, attribution, tileSize, maxzoom} for a
     * normal raster basemap entry, or {label, hillshade: true, baseKey} for
     * a virtual entry that reuses another basemap's tiles (baseKey) with a
     * hillshade layer draped on top instead of fetching tiles of its own.
     * Each normal entry becomes a raster source/layer; visibility is
     * toggled by activeBasemap instead of swapping the whole style.
     * maxzoom (optional) is the deepest zoom the provider has tiles for.
     */
    basemaps: PropTypes.objectOf(PropTypes.shape({
        url: PropTypes.string,
        attribution: PropTypes.string,
        tileSize: PropTypes.number,
        maxzoom: PropTypes.number,
        hillshade: PropTypes.bool,
        baseKey: PropTypes.string,
    })),

    /**
     * Key into `basemaps` for the currently visible basemap layer.
     */
    activeBasemap: PropTypes.string,

    /**
     * Desaturate the currently-active basemap raster layer(s) to grayscale
     * (uses MapLibre's raster-saturation paint property).
     */
    basemapMonochrome: PropTypes.bool,

    /**
     * XYZ tile URL template ({x}/{y}/{z}) for the interferogram raster
     * overlay, fetched TMS-scheme from the existing /getTileUrl proxy.
     */
    interferogramTileUrl: PropTypes.string,

    /**
     * Opacity of the interferogram raster layer.
     */
    interferogramOpacity: PropTypes.number,

    /**
     * Show/hide the interferogram raster layer (hidden layers stop
     * fetching tiles).
     */
    interferogramVisible: PropTypes.bool,

    /**
     * Point-target vector tiles for the Timeseries tab: {url, bounds,
     * minzoom, maxzoom}. url is an XYZ template ({x}/{y}/{z}) served
     * TMS-scheme by the /getPointTile route; each feature's id is the
     * GeoPackage fid. Null removes the points layer.
     */
    pointSource: PropTypes.shape({
        url: PropTypes.string,
        bounds: PropTypes.arrayOf(PropTypes.number),
        minzoom: PropTypes.number,
        maxzoom: PropTypes.number,
    }),

    /**
     * Point colouring: {property, min, max, stops}. property is the tile
     * attribute to colour by; stops is a list of [position, colour] with
     * position from -1 (min) through 0 (pinned to 0 when the range spans
     * zero) to 1 (max).
     */
    pointStyle: PropTypes.shape({
        property: PropTypes.string,
        min: PropTypes.number,
        max: PropTypes.number,
        stops: PropTypes.arrayOf(PropTypes.array),
    }),

    /**
     * Read-only: the point nearest the user's last click on the points
     * layer, {fid, longitude, latitude, timestamp}.
     */
    clickedPoint: PropTypes.shape({
        fid: PropTypes.number,
        longitude: PropTypes.number,
        latitude: PropTypes.number,
        timestamp: PropTypes.number,
    }),

    /**
     * Raster-DEM tile URL template(s) (Mapbox terrain-RGB encoding) used to
     * displace the terrain surface. Null disables terrain.
     */
    demTiles: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.arrayOf(PropTypes.string),
    ]),

    /**
     * Encoding used by the raster-DEM tiles: 'terrarium' (e.g. AWS Open
     * Data's elevation-tiles-prod) or 'mapbox' (Mapbox Terrain-RGB).
     */
    demEncoding: PropTypes.oneOf(['terrarium', 'mapbox']),

    /**
     * Vertical exaggeration factor applied to the DEM terrain.
     */
    terrainExaggeration: PropTypes.number,

    /**
     * GeoJSON FeatureCollection of earthquake epicenters; each feature's
     * properties should include magnitude, quakeColour, time, depthKm,
     * eventId.
     */
    earthquakeData: PropTypes.object,

    /**
     * Optional WMS raster overlay (e.g. glacier footprints): {url, layers,
     * styles, format, opacity, visible}.
     */
    wmsOverlay: PropTypes.shape({
        url: PropTypes.string,
        layers: PropTypes.string,
        styles: PropTypes.string,
        format: PropTypes.string,
        opacity: PropTypes.number,
        visible: PropTypes.bool,
    }),

    /**
     * CSS style applied to the map container div.
     */
    style: PropTypes.object,

    /**
     * CSS class applied to the map container div.
     */
    className: PropTypes.string,
};

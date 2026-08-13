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

const EMPTY_FC = {type: 'FeatureCollection', features: []};

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
        } else if (prevProps.interferogramOpacity !== this.props.interferogramOpacity) {
            this.updateInterferogramOpacity();
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
            const {longitude, latitude, zoom, duration} = this.props.flyTo;
            map.flyTo({
                center: [longitude, latitude],
                zoom,
                duration: duration === undefined ? 2000 : duration,
            });
        }
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
    }

    addInterferogramLayer() {
        const {map} = this;
        const {interferogramTileUrl, interferogramOpacity} = this.props;
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
        });
    }

    updateInterferogramSource() {
        const {map} = this;
        if (!map || !map.isStyleLoaded()) {
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
        if (!map || !map.isStyleLoaded() || !map.getLayer(INTERFEROGRAM_LAYER_ID)) {
            return;
        }
        map.setPaintProperty(
            INTERFEROGRAM_LAYER_ID, 'raster-opacity', this.props.interferogramOpacity
        );
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
        });
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
        if (!map || !map.isStyleLoaded()) {
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
        });
    }

    updateWmsOverlay() {
        const {map} = this;
        if (!map || !map.isStyleLoaded()) {
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
        if (!map || !map.isStyleLoaded()) {
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
        if (!map || !map.isStyleLoaded()) {
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
        });
    }

    updateTerrain() {
        const {map} = this;
        const {demTiles} = this.props;
        if (!map || !map.isStyleLoaded()) {
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
     * Map of basemap id -> {url, attribution, tileSize} for a normal raster
     * basemap entry, or {label, hillshade: true, baseKey} for a virtual
     * entry that reuses another basemap's tiles (baseKey) with a hillshade
     * layer draped on top instead of fetching tiles of its own. Each normal
     * entry becomes a raster source/layer; visibility is toggled by
     * activeBasemap instead of swapping the whole style.
     */
    basemaps: PropTypes.objectOf(PropTypes.shape({
        url: PropTypes.string,
        attribution: PropTypes.string,
        tileSize: PropTypes.number,
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

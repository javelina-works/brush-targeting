<template>
  <div>
    <h1>Planner Page</h1>
    <!-- Map Container -->
    <div id="map" ref="mapContainer"></div>

    <!-- Control Buttons -->
    <div class="controls">
      <button v-if="!hasVoronoiCells" @click="generateTessellation">
        Generate Tessellation
      </button>
      <button v-if="!hasDepots" @click="generateDepots">
        Generate Depots
      </button>
    </div>
  </div>
</template>
  
<script>
import { ref, watch, watchEffect, onMounted, computed } from 'vue';
import L from "leaflet";
import { useMapData, useDepotsMutation, useTessellationMutation } from './graphQL'


export default {
  props: {
    locationId: String,
    jobId: String
  },
  setup(props) {
    const map = ref(null);
    const hasVoronoiCells = ref(false);
    const hasDepots = ref(false);
    const layers = ref([
      "region_contour", 
      "removed_targets",
      "approved_targets"
    ]);

    // Load map assets
    const { result, loading, error } = useMapData(props.locationId, props.jobId, layers.value);
    const { mutate: generateTessellationMutation } = useTessellationMutation();
    const { mutate: generateDepotsMutation } = useDepotsMutation();


    // Initialize Leaflet map
    const initMap = () => {
      map.value = L.map("map", {
        maxZoom: 21,
      }).setView([30.2506, -103.6035], 14);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map.value);
      
      L.control.scale().addTo(map.value);
    };


  const layerFactory = {
    region_contour: () => L.geoJSON(null, {
        style: { color: "blue", weight: 2, fillOpacity: 0.1 },
    }),
    approved_targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "blue", radius: 5 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Approved Target</b><br>ID: ${feature.properties.id}`);
            layer.on("click", () => moveFeature(feature, "approved_targets", "removed_targets"));
        },
    }),
    removed_targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "red", radius: 5 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Removed Target</b><br>ID: ${feature.properties.id}`);
            layer.on("click", () => moveFeature(feature, "removed_targets", "approved_targets"));
        },
    }),
    default: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "gray", radius: 5 }),
        onEachFeature: (feature, layer) => {
        layer.bindPopup(`<b>Unknown Layer</b><br>ID: ${feature.properties?.id || "N/A"}`);
        },
    }),
  };


  function updateMapLayers(newData) {
    if (!newData || !newData.mapAssets) return;
    console.log("📡 API Data Received:", newData.mapAssets);

    newData.mapAssets.forEach(asset => {
        try {
            const parsedGeoJson = JSON.parse(asset.geojson); // ✅ Convert JSON string to object
            const name = asset.name

            if (geojsonLayers[name]) {
            updateLayer(name, parsedGeoJson);
            } else {
            // If a new layer type appears, initialize it dynamically
            geojsonLayers[name] = (layerFactory[name] || layerFactory.default)();
            geojsonLayers[name].addTo(map);
            updateLayer(name, parsedGeoJson);
            layerControl.addOverlay(geojsonLayers[name], name);
            }
        } catch (error) {
            console.error(`❌ Error parsing GeoJSON for ${asset.name}:`, error);
        }
    });
  }


    // Process and update map layers
    const processMapAssets = (assets) => {
      assets.forEach((asset) => {
        if (asset.name === "voronoi_cells") {
          addVoronoiLayer(asset.geojson);
          hasVoronoiCells.value = true;
        }
        if (asset.name === "depot_locations") {
          addDepotMarkers(asset.geojson);
          hasDepots.value = true;
        }
      });
    };

    // Add Voronoi layer
    const addVoronoiLayer = (geojson) => {
      const layer = L.geoJSON(JSON.parse(geojson), { style: { color: "blue" } }).addTo(map.value);
      layers.value["voronoi_cells"] = layer;
    };

    // Add depot markers
    const addDepotMarkers = (geojson) => {
      const depots = JSON.parse(geojson).features;
      depots.forEach((feature) => {
        const { coordinates } = feature.geometry;
        const marker = L.marker([coordinates[1], coordinates[0]], { title: "Depot" }).addTo(map.value);
        layers.value["depot_" + feature.properties.id] = marker;
      });
    };

    // Generate tessellation
    const generateTessellation = async () => {
      const { data } = await generateTessellationMutation({
        locationId: props.locationId,
        jobId: props.jobId,
        targetAreaAcres: 0.5,
        maxIterations: 10
      });

      if (data && data.generateTesselation.geojson) {
        addVoronoiLayer(data.generateTesselation.geojson);
        hasVoronoiCells.value = true;
      }
    };

    // Generate depots
    const generateDepots = async () => {
      const { data } = await generateDepotsMutation({
        locationId: props.locationId,
        jobId: props.jobId
      });

      if (data && data.generateDepots.geojson) {
        addDepotMarkers(data.generateDepots.geojson);
        hasDepots.value = true;
      }
    };

  /** ✅ Watch for API Data and Update Layers */
  watch(result, (newData) => {
    updateMapLayers(newData);
  });

    // Reactively update map when assets load
    watchEffect(() => {
      if (result.value && result.value.getMapAssets) {
        processMapAssets(result.value.getMapAssets);
      }
    });

    // Initialize map on mount
    onMounted(() => {
      initMap();
    });

    return {
      hasVoronoiCells,
      hasDepots,
      generateTessellation,
      generateDepots
    };
  }
};



</script>

<style scoped>
#map {
  width: 100%;
  height: 500px;
}
.controls {
  margin-top: 10px;
}
button {
  margin-right: 10px;
  padding: 8px 12px;
  font-size: 16px;
  cursor: pointer;
}
</style>
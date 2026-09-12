/**
 * RailBlock AI - Interactive Geographic Corridor Route, Terrain & Work-Zones Map Engine
 * Visualizes: Stations, Rivers & Bridges, Jungles & Sanctuaries, Live Train Timings & Work Undergoing
 */

class TerrainRouteVisualizer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.stations = [];
    this.rivers = [];
    this.jungles = [];
    this.trains = [];
    this.blocks = [];
    this.activeFilter = 'ALL';
    this.selectedElement = null;
    this.animationTimer = null;
    this.trainOffsets = {};
  }

  setData(stations, terrain, trains, blocks) {
    this.stations = stations || [];
    this.rivers = (terrain && terrain.rivers) || [];
    this.jungles = (terrain && terrain.jungles) || [];
    this.trains = trains || [];
    this.blocks = blocks || [];
    this.initTrainAnimation();
    this.render();
  }

  initTrainAnimation() {
    this.trains.forEach((t, i) => {
      if (!this.trainOffsets[t.train_number]) {
        this.trainOffsets[t.train_number] = (i * 0.18) % 1.0;
      }
    });

    if (this.animationTimer) clearInterval(this.animationTimer);
    this.animationTimer = setInterval(() => {
      this.trains.forEach(t => {
        const speedFactor = t.train_type === 'VANDE_BHARAT' ? 0.0025 : (t.train_type.includes('FREIGHT') ? 0.0008 : 0.0015);
        if (t.direction === 'DOWN') {
          this.trainOffsets[t.train_number] = (this.trainOffsets[t.train_number] + speedFactor) % 1.0;
        } else {
          this.trainOffsets[t.train_number] = (this.trainOffsets[t.train_number] - speedFactor + 1.0) % 1.0;
        }
      });
      this.updateTrainPositions();
    }, 100);
  }

  render() {
    if (!this.container) return;

    const minKm = 0.0;
    const maxKm = 781.0;
    const totalKm = maxKm - minKm;

    this.container.innerHTML = `
      <div style="position: relative; width: 100%; min-width: 1100px; background: linear-gradient(180deg, #0b1523 0%, #112236 100%); border-radius: 12px; border: 1px solid var(--border-color); padding: 2rem 1.5rem 3rem 1.5rem; overflow-x: auto;">
        
        <!-- Legend Bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.75rem; flex-wrap: wrap; gap: 0.75rem;">
          <div style="display: flex; gap: 1rem; align-items: center; font-size: 0.76rem;">
            <span style="display: flex; align-items: center; gap: 5px;"><span style="display:inline-block; width:12px; height:12px; border-radius:50%; background:#f5a623;"></span> <b>Station Hubs</b></span>
            <span style="display: flex; align-items: center; gap: 5px;"><span style="display:inline-block; width:14px; height:6px; background:#0284c7; border-radius:2px;"></span> <b>🌊 Rivers & Rail Bridges</b></span>
            <span style="display: flex; align-items: center; gap: 5px;"><span style="display:inline-block; width:14px; height:8px; background:rgba(34,197,94,0.3); border:1px solid #22c55e; border-radius:2px;"></span> <b>🌲 Jungles & Wildlife Reserves</b></span>
            <span style="display: flex; align-items: center; gap: 5px;"><span style="display:inline-block; width:14px; height:10px; background:repeating-linear-gradient(45deg,#ef4444,#ef4444 4px,#f59e0b 4px,#f59e0b 8px); border-radius:2px;"></span> <b>🚧 Work Undergoing</b></span>
          </div>
          <div style="font-size: 0.76rem; color: var(--ir-gold); font-weight: 700;">
            📍 Grand Chord Super Trunk Route (781 KM) • 160 km/h Automatic Block
          </div>
        </div>

        <!-- Geographic Schematic Canvas / Container -->
        <div style="position: relative; height: 320px; width: 100%;">
          
          <!-- JUNGLES LAYER (Behind Tracks) -->
          ${this.jungles.map(j => {
            const leftPct = Math.max(0, Math.min(100, ((j.start_km - minKm) / totalKm) * 100));
            const widthPct = Math.max(3, Math.min(100 - leftPct, ((j.end_km - j.start_km) / totalKm) * 100));
            return `
              <div style="position: absolute; left: ${leftPct}%; width: ${widthPct}%; top: 15px; height: 260px; background: radial-gradient(circle, rgba(16, 185, 129, 0.16) 0%, rgba(5, 150, 105, 0.05) 100%); border: 1px dashed rgba(34, 197, 94, 0.35); border-radius: 14px; pointer-events: auto; cursor: pointer; transition: all 0.2s;" 
                   title="${j.name} (${j.flora_type})"
                   onclick="TerrainRouteVisualizer.showDetails('jungle', '${j.id}')">
                <div style="padding: 0.4rem 0.5rem; font-size: 0.7rem; font-weight: 700; color: #34d399; display: flex; align-items: center; gap: 4px;">
                  <span>🌲</span> <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${j.name}</span>
                </div>
                ${j.elephant_wildlife_caution ? '<span class="badge badge-high" style="position: absolute; bottom: 8px; left: 8px; font-size: 0.6rem;">⚠️ Wildlife Zone</span>' : ''}
              </div>
            `;
          }).join('')}

          <!-- RIVERS LAYER (Vertical Blue Currents Crossing Tracks) -->
          ${this.rivers.map(r => {
            const leftPct = Math.max(0, Math.min(98, ((r.km - minKm) / totalKm) * 100));
            return `
              <div style="position: absolute; left: ${leftPct}%; width: 22px; top: 0; bottom: 0; background: linear-gradient(180deg, rgba(2, 132, 199, 0.2) 0%, rgba(14, 165, 233, 0.45) 50%, rgba(2, 132, 199, 0.2) 100%); border-left: 2px solid #0284c7; border-right: 2px solid #0284c7; border-radius: 4px; pointer-events: auto; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 4px 0; z-index: 5;"
                   title="${r.name} - Width: ${r.width_meters}m"
                   onclick="TerrainRouteVisualizer.showDetails('river', '${r.id}')">
                <span style="font-size: 0.65rem; color: #38bdf8; writing-mode: vertical-rl; transform: rotate(180deg); font-weight: 700; letter-spacing: 0.05em; white-space: nowrap;">
                  🌊 ${r.name.split('(')[0]}
                </span>
                <span style="font-size: 0.6rem; color: #7dd3fc; font-weight: bold; background: rgba(0,0,0,0.6); padding: 1px 3px; border-radius: 3px;">
                  KM ${r.km}
                </span>
              </div>
            `;
          }).join('')}

          <!-- ACTIVE WORK UNDERGOING ZONES (Pulsating Highlight on Tracks) -->
          ${this.blocks.map(b => {
            const leftPct = Math.max(0, Math.min(100, ((b.start_km - minKm) / totalKm) * 100));
            const widthPct = Math.max(3.5, Math.min(100 - leftPct, ((b.end_km - b.start_km) / totalKm) * 100));
            const topPos = b.line === 'UP_MAIN' ? '90px' : '155px';
            return `
              <div style="position: absolute; left: ${leftPct}%; width: ${widthPct}%; top: ${topPos}; height: 26px; background: repeating-linear-gradient(45deg, rgba(239, 68, 68, 0.75), rgba(239, 68, 68, 0.75) 8px, rgba(245, 158, 11, 0.75) 8px, rgba(245, 158, 11, 0.75) 16px); border: 2px solid #f59e0b; border-radius: 6px; z-index: 15; box-shadow: 0 0 15px rgba(239, 68, 68, 0.6); cursor: pointer; display: flex; align-items: center; justify-content: center;"
                   title="WORK UNDERGOING: ${b.block_id} (${b.start_time}-${b.end_time}) - ${b.allocated_machines.join(', ') || 'Maintenance Gang'}"
                   onclick="TerrainRouteVisualizer.showDetails('block', '${b.block_id}')">
                <span style="font-size: 0.65rem; font-weight: 800; color: #fff; text-shadow: 0 1px 3px #000; background: rgba(0,0,0,0.6); padding: 1px 4px; border-radius: 3px;">
                  🚧 ${b.duration_minutes}m Work
                </span>
              </div>
            `;
          }).join('')}

          <!-- UP MAIN LINE (Track 1) -->
          <div style="position: absolute; left: 0; right: 0; top: 100px; height: 6px; background: #38bdf8; border-radius: 3px; z-index: 10; box-shadow: 0 0 8px rgba(56, 189, 248, 0.4);">
            <span style="position: absolute; left: 10px; top: -18px; font-size: 0.68rem; font-weight: 700; color: #38bdf8;">UP MAIN LINE (Delhi ➔ DDU)</span>
          </div>

          <!-- DOWN MAIN LINE (Track 2) -->
          <div style="position: absolute; left: 0; right: 0; top: 165px; height: 6px; background: #f5a623; border-radius: 3px; z-index: 10; box-shadow: 0 0 8px rgba(245, 166, 35, 0.4);">
            <span style="position: absolute; left: 10px; top: 12px; font-size: 0.68rem; font-weight: 700; color: #f5a623;">DOWN MAIN LINE (DDU ➔ Delhi)</span>
          </div>

          <!-- STATIONS NODES -->
          ${this.stations.map((s, idx) => {
            const leftPct = Math.max(0, Math.min(97, ((s.km - minKm) / totalKm) * 100));
            return `
              <div style="position: absolute; left: ${leftPct}%; top: 75px; z-index: 20; display: flex; flex-direction: column; align-items: center; transform: translateX(-50%); cursor: pointer;"
                   onclick="TerrainRouteVisualizer.showDetails('station', '${s.code}')">
                <div style="font-size: 0.72rem; font-weight: 800; color: #fff; background: rgba(19, 34, 53, 0.9); border: 1px solid var(--ir-gold); padding: 2px 6px; border-radius: 4px; white-space: nowrap; margin-bottom: 4px;">
                  🚉 ${s.code}
                </div>
                <div style="width: 16px; height: 16px; border-radius: 50%; background: var(--ir-gold); border: 3px solid #0f172a; box-shadow: 0 0 10px #f5a623;"></div>
                <div style="width: 2px; height: 50px; background: rgba(255,255,255,0.2);"></div>
                <div style="width: 14px; height: 14px; border-radius: 50%; background: #f5a623; border: 3px solid #0f172a;"></div>
                <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 4px; font-family: var(--font-mono); white-space: nowrap;">
                  KM ${s.km}
                </div>
              </div>
            `;
          }).join('')}

          <!-- MOVING TRAINS CONTAINER LAYER -->
          <div id="liveTrainsLayer" style="position: absolute; inset: 0; z-index: 25; pointer-events: none;">
            <!-- Updated dynamically in updateTrainPositions -->
          </div>

        </div>

        <!-- Detail Inspection Drawer / Info Pane -->
        <div id="terrainDetailDrawer" style="margin-top: 1.5rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; display: none;">
          <!-- Injected via showDetails -->
        </div>

      </div>
    `;

    this.updateTrainPositions();
  }

  updateTrainPositions() {
    const layer = document.getElementById('liveTrainsLayer');
    if (!layer || !this.trains.length) return;

    layer.innerHTML = this.trains.slice(0, 10).map(t => {
      const offset = this.trainOffsets[t.train_number] || 0.5;
      const leftPct = Math.max(1, Math.min(96, offset * 100));
      const topPos = t.direction === 'DOWN' ? '88px' : '153px';
      
      let trainColor = '#818cf8';
      if (t.train_type === 'VANDE_BHARAT') trainColor = '#f5a623';
      else if (t.train_type === 'RAJDHANI_SHATABDI') trainColor = '#38bdf8';
      else if (t.train_type.includes('FREIGHT')) trainColor = '#94a3b8';

      return `
        <div style="position: absolute; left: ${leftPct}%; top: ${topPos}; transform: translate(-50%, -50%); display: flex; align-items: center; gap: 4px; pointer-events: auto; cursor: pointer; transition: left 0.1s linear;"
             onclick="TerrainRouteVisualizer.showDetails('train', '${t.train_number}')">
          <div style="background: ${trainColor}; color: #0f172a; padding: 2px 7px; border-radius: 10px; font-size: 0.68rem; font-weight: 800; display: flex; align-items: center; gap: 4px; box-shadow: 0 0 12px ${trainColor}; border: 1px solid #fff;">
            <span>🚆</span>
            <span>${t.train_number} (${t.average_speed_kmph} km/h)</span>
          </div>
        </div>
      `;
    }).join('');
  }

  static showDetails(type, id) {
    const drawer = document.getElementById('terrainDetailDrawer');
    if (!drawer) return;
    drawer.style.display = 'block';

    if (type === 'river') {
      const r = (window.AppState.terrainData && window.AppState.terrainData.rivers.find(x => x.id === id)) || { name: "Major River Bridge", km: id, width_meters: 650 };
      drawer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="color: #38bdf8;">🌊 ${r.name}</h4>
          <span class="badge badge-mega">Railway Engineering Waterway Structure</span>
        </div>
        <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.35rem;">
          <b>Location:</b> KM ${r.km} | <b>Bridge Waterway Span:</b> ${r.width_meters} meters | <b>Monsoon Level:</b> ${r.water_level || 'Safe Gauge'} | <b>Type:</b> ${r.type}
        </p>
      `;
    } else if (type === 'jungle') {
      const j = (window.AppState.terrainData && window.AppState.terrainData.jungles.find(x => x.id === id)) || { name: "Forest Sanctuary Reserve", start_km: 18, end_km: 42 };
      drawer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="color: #34d399;">🌲 ${j.name}</h4>
          <span class="badge badge-eng">Forest Sanctuary Corridor</span>
        </div>
        <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.35rem;">
          <b>Section Span:</b> KM ${j.start_km} to KM ${j.end_km} (${j.end_km - j.start_km} KM Forest Track) | <b>Flora:</b> ${j.flora_type} | 
          <b>Wildlife Caution:</b> ${j.elephant_wildlife_caution ? '⚠️ Active Animal Crossing Zone (Speed Restrictions Enforced)' : 'Normal Wildlife Clearance'}
        </p>
      `;
    } else if (type === 'block') {
      const b = window.AppState.currentPlan.blocks.find(x => x.block_id === id);
      if (b) {
        drawer.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="color: #ef4444;">🚧 Active Maintenance Work Undergoing: ${b.block_id}</h4>
            <span class="badge badge-critical">Form B Sanctioned</span>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.35rem;">
            <b>Section:</b> ${b.station_from} ➔ ${b.station_to} [${b.line} KM ${b.start_km}-${b.end_km}] | 
            <b>Timing:</b> ${b.start_time} to ${b.end_time} (${b.duration_minutes} Mins) | 
            <b>Machines Deployed:</b> ${b.allocated_machines.join(', ') || 'Manual Maintenance Squad'} |
            <b>Co-bundled Works:</b> ${b.bundled_tasks.map(t => t.title).join(' + ')}
          </p>
        `;
      }
    } else if (type === 'station') {
      const s = window.AppState.network.stations.find(x => x.code === id);
      if (s) {
        drawer.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="color: var(--ir-gold);">🚉 ${s.name} (${s.code})</h4>
            <span class="badge badge-mega">Junction Hub • ${s.lines} Running Platforms</span>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.35rem;">
            <b>Chainage:</b> KM ${s.km} | <b>Zone/Division:</b> ${s.zone} (${s.state}) | <b>Loco/Wagon Depot:</b> ${s.has_depot ? 'Available' : 'None'}
          </p>
        `;
      }
    } else if (type === 'train') {
      window.viewTrainHalts(id);
    }
  }
}

window.TerrainRouteVisualizer = TerrainRouteVisualizer;

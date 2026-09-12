/**
 * RailBlock AI - Interactive Dynamic Track Line Schematic Diagram
 * Visualizes Multi-Line Railway Track Sections, S&T Signals, OHE Power Feeds, and Active Work Zones
 */

class CorridorTrackSchematic {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.stations = [];
    this.blocks = [];
  }
  
  setData(stations, blocks) {
    this.stations = stations || [];
    this.blocks = blocks || [];
    this.render();
  }
  
  render() {
    if (!this.container || !this.stations.length) return;
    
    const svgWidth = 1400;
    const svgHeight = 280;
    const padding = { left: 80, right: 80, top: 40 };
    const usableWidth = svgWidth - padding.left - padding.right;
    
    // Station coordinates
    const maxKm = 781.0;
    const stnCoords = this.stations.map(s => ({
      ...s,
      x: padding.left + (s.km / maxKm) * usableWidth
    }));
    
    let svgHtml = `
      <svg viewBox="0 0 ${svgWidth} ${svgHeight}" style="width: 100%; height: auto; font-family: Inter, sans-serif;">
        <defs>
          <linearGradient id="upLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#38bdf8" />
            <stop offset="100%" stop-color="#0284c7" />
          </linearGradient>
          <linearGradient id="downLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#f5a623" />
            <stop offset="100%" stop-color="#d97706" />
          </linearGradient>
          <pattern id="railSleepers" width="8" height="10" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="10" stroke="#334155" stroke-width="1.5" />
          </pattern>
        </defs>
        
        <!-- Track Background Sleeper Beds -->
        <rect x="${padding.left}" y="90" width="${usableWidth}" height="16" fill="url(#railSleepers)" opacity="0.4" />
        <rect x="${padding.left}" y="150" width="${usableWidth}" height="16" fill="url(#railSleepers)" opacity="0.4" />
        
        <!-- Track Lines -->
        <!-- UP MAIN LINE (Delhi/Ghaziabad to DDU) -->
        <line x1="${padding.left}" y1="98" x2="${svgWidth - padding.right}" y2="98" stroke="#38bdf8" stroke-width="4" />
        <text x="15" y="102" fill="#38bdf8" font-size="11" font-weight="bold">UP MAIN ➔</text>
        
        <!-- DOWN MAIN LINE (DDU to Ghaziabad/Delhi) -->
        <line x1="${padding.left}" y1="158" x2="${svgWidth - padding.right}" y2="158" stroke="#f5a623" stroke-width="4" />
        <text x="5" y="162" fill="#f5a623" font-size="11" font-weight="bold">⬅ DOWN MAIN</text>
        
        <!-- 3rd / Goods Bypass Loops at Major Junctions -->
        <path d="M 60 70 L 150 70 M 680 70 L 880 70 M 1150 70 L 1320 70" stroke="#64748b" stroke-width="2.5" stroke-dasharray="6,4" />
        <text x="15" y="73" fill="#64748b" font-size="9">3RD/LOOP</text>
    `;
    
    // Draw Scheduled / Active Maintenance Block Overlays
    for (const block of this.blocks) {
      const x1 = padding.left + (block.start_km / maxKm) * usableWidth;
      const x2 = padding.left + (block.end_km / maxKm) * usableWidth;
      const bWidth = Math.max(25, Math.abs(x2 - x1));
      const bX = Math.min(x1, x2);
      const isUp = block.line.includes('UP');
      const bY = isUp ? 86 : 146;
      
      const badgeColor = block.is_integrated_mega_block ? '#10b981' : '#f59e0b';
      
      svgHtml += `
        <g class="block-zone" style="cursor: pointer;">
          <rect x="${bX}" y="${bY}" width="${bWidth}" height="24" rx="4" fill="${badgeColor}" fill-opacity="0.35" stroke="${badgeColor}" stroke-width="2" />
          <circle cx="${bX + bWidth/2}" cy="${bY + 12}" r="5" fill="${badgeColor}">
            <animate attributeName="r" values="4;7;4" dur="1.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
          </circle>
          <text x="${bX + bWidth/2}" y="${bY - 6}" fill="${badgeColor}" font-size="10" font-weight="bold" text-anchor="middle">
            ⚡ ${block.block_id} (${block.duration_minutes}m)
          </text>
        </g>
      `;
    }
    
    // Draw Station Nodes & Interlocking Signals
    for (const stn of stnCoords) {
      const isJunction = stn.lines >= 4;
      
      svgHtml += `
        <g class="station-node" transform="translate(${stn.x}, 0)">
          <!-- Vertical Station Gridline -->
          <line x1="0" y1="50" x2="0" y2="210" stroke="#334155" stroke-width="1" stroke-dasharray="3,3" />
          
          <!-- Station Platform Node -->
          <circle cx="0" cy="98" r="${isJunction ? 6 : 4}" fill="#0f172a" stroke="#38bdf8" stroke-width="${isJunction ? 3 : 2}" />
          <circle cx="0" cy="158" r="${isJunction ? 6 : 4}" fill="#0f172a" stroke="#f5a623" stroke-width="${isJunction ? 3 : 2}" />
          
          <!-- 25kV Traction Substation Icon for Depots -->
          ${stn.has_depot ? `
            <rect x="-8" y="25" width="16" height="14" rx="2" fill="#8b5cf6" opacity="0.8" />
            <text x="0" y="36" fill="#fff" font-size="8" font-weight="bold" text-anchor="middle">TSS</text>
          ` : ''}
          
          <!-- Station Label & KM -->
          <rect x="-40" y="215" width="80" height="22" rx="4" fill="#132235" stroke="#243852" stroke-width="1" />
          <text x="0" y="230" fill="${isJunction ? '#f5a623' : '#f1f5f9'}" font-size="${isJunction ? 11 : 10}" font-weight="${isJunction ? 'bold' : 'normal'}" text-anchor="middle">
            ${stn.code}
          </text>
          <text x="0" y="250" fill="#64748b" font-size="9" font-family="JetBrains Mono" text-anchor="middle">
            KM ${stn.km}
          </text>
        </g>
      `;
    }
    
    svgHtml += `</svg>`;
    this.container.innerHTML = svgHtml;
  }
}

window.CorridorTrackSchematic = CorridorTrackSchematic;

/**
 * RailBlock AI - Time-Distance Marey String Chart & Gantt Timetable Visualizer
 * High-performance HTML5 Canvas rendering for train trajectories and maintenance block occupations
 */

class MareyStringChart {
  constructor(canvasId, tooltipId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.tooltip = document.getElementById(tooltipId);
    
    this.stations = [];
    this.trains = [];
    this.blocks = [];
    
    this.padding = { top: 40, right: 60, bottom: 40, left: 100 };
    this.hoverItem = null;
    
    this._initEvents();
    this.resize();
  }
  
  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.width = rect.width || 1200;
    this.height = 550;
    
    // Support high-DPI displays
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(dpr, dpr);
    
    this.render();
  }
  
  setData(stations, trains, blocks) {
    this.stations = stations || [];
    this.trains = trains || [];
    this.blocks = blocks || [];
    this.render();
  }
  
  _initEvents() {
    if (!this.canvas) return;
    window.addEventListener('resize', () => this.resize());
    
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      this._handleHover(x, y, e.clientX, e.clientY);
    });
    
    this.canvas.addEventListener('mouseleave', () => {
      if (this.tooltip) this.tooltip.style.display = 'none';
      this.hoverItem = null;
      this.render();
    });
  }
  
  _timeToX(timeStr) {
    if (!timeStr) return 0;
    const [h, m] = timeStr.split(':').map(Number);
    const totalMinutes = h * 60 + m;
    const chartWidth = this.width - this.padding.left - this.padding.right;
    return this.padding.left + (totalMinutes / (24 * 60)) * chartWidth;
  }
  
  _kmToY(km) {
    const maxKm = 781.0;
    const chartHeight = this.height - this.padding.top - this.padding.bottom;
    return this.padding.top + (km / maxKm) * chartHeight;
  }
  
  render() {
    if (!this.ctx || !this.stations.length) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, w, h);
    
    // Draw Background
    ctx.fillStyle = '#09101a';
    ctx.fillRect(0, 0, w, h);
    
    // 1. Draw Time Grid (Vertical lines every 2 hours)
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '11px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    
    for (let hour = 0; hour <= 24; hour += 2) {
      const timeStr = `${hour.toString().padStart(2, '0')}:00`;
      const x = this._timeToX(timeStr);
      
      ctx.beginPath();
      ctx.moveTo(x, this.padding.top);
      ctx.lineTo(x, h - this.padding.bottom);
      ctx.stroke();
      
      ctx.fillText(timeStr, x, h - this.padding.bottom + 20);
      ctx.fillText(timeStr, x, this.padding.top - 12);
    }
    
    // 2. Draw Station Lines (Horizontal lines)
    ctx.textAlign = 'right';
    for (const stn of this.stations) {
      const y = this._kmToY(stn.km);
      
      ctx.strokeStyle = stn.lines > 4 ? '#334155' : '#1e293b';
      ctx.lineWidth = stn.lines > 4 ? 1.5 : 1;
      
      ctx.beginPath();
      ctx.moveTo(this.padding.left, y);
      ctx.lineTo(w - this.padding.right, y);
      ctx.stroke();
      
      // Station Name
      ctx.fillStyle = stn.lines > 4 ? '#f1f5f9' : '#94a3b8';
      ctx.font = stn.lines > 4 ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif';
      ctx.fillText(`${stn.code} (${Math.round(stn.km)}k)`, this.padding.left - 10, y + 3);
    }
    
    // 3. Draw Scheduled Maintenance Blocks (Shaded Rectangles)
    for (const block of this.blocks) {
      const x1 = this._timeToX(block.start_time);
      const x2 = this._timeToX(block.end_time);
      const y1 = this._kmToY(block.start_km);
      const y2 = this._kmToY(block.end_km);
      
      const blockWidth = Math.max(8, x2 - x1);
      const blockHeight = Math.max(12, Math.abs(y2 - y1));
      const blockTop = Math.min(y1, y2);
      
      // Block color based on Integrated Mega-Block or single dept
      if (block.is_integrated_mega_block) {
        ctx.fillStyle = 'rgba(16, 185, 129, 0.28)'; // Emerald green
        ctx.strokeStyle = '#10b981';
      } else if (block.primary_department === 'ENGINEERING') {
        ctx.fillStyle = 'rgba(56, 189, 248, 0.25)'; // Sky blue
        ctx.strokeStyle = '#0284c7';
      } else if (block.primary_department === 'TRD') {
        ctx.fillStyle = 'rgba(245, 166, 35, 0.25)'; // Gold
        ctx.strokeStyle = '#f5a623';
      } else {
        ctx.fillStyle = 'rgba(192, 132, 252, 0.25)'; // Purple
        ctx.strokeStyle = '#c084fc';
      }
      
      ctx.lineWidth = 1.5;
      ctx.fillRect(x1, blockTop, blockWidth, blockHeight);
      ctx.strokeRect(x1, blockTop, blockWidth, blockHeight);
      
      // Hatch pattern for work zone
      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      ctx.font = 'bold 9px JetBrains Mono, monospace';
      ctx.textAlign = 'left';
      if (blockWidth > 35) {
        ctx.fillText(`⚡${block.block_id}`, x1 + 4, blockTop + 14);
      }
    }
    
    // 4. Draw Train Paths (Trajectories)
    for (const train of this.trains) {
      const timings = train.station_timings;
      const points = [];
      
      for (const stn of this.stations) {
        if (timings[stn.code]) {
          const tArr = timings[stn.code].arr;
          const tDep = timings[stn.code].dep;
          const xArr = this._timeToX(tArr);
          const xDep = this._timeToX(tDep);
          const y = this._kmToY(stn.km);
          points.push({ x: xArr, y, t: tArr });
          if (xDep !== xArr) points.push({ x: xDep, y, t: tDep });
        }
      }
      
      if (points.length < 2) continue;
      
      // Style train trajectory line
      ctx.beginPath();
      if (train.train_type === 'VANDE_BHARAT') {
        ctx.strokeStyle = '#f5a623'; // Bright gold
        ctx.lineWidth = 3;
      } else if (train.train_type === 'RAJDHANI_SHATABDI') {
        ctx.strokeStyle = '#38bdf8'; // Cyan
        ctx.lineWidth = 2.5;
      } else if (train.train_type === 'SUPERFAST_MAIL') {
        ctx.strokeStyle = '#818cf8'; // Indigo
        ctx.lineWidth = 2;
      } else if (train.train_type === 'PASSENGER_MEMU') {
        ctx.strokeStyle = '#4ade80'; // Green
        ctx.lineWidth = 1.5;
      } else {
        // Freight
        ctx.strokeStyle = '#94a3b8'; // Grey dashed
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
      }
      
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.stroke();
      ctx.setLineDash([]); // Reset dash
      
      // Label train at start
      ctx.fillStyle = ctx.strokeStyle;
      ctx.font = 'bold 9px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(train.train_number, points[0].x + 3, points[0].y - 3);
    }
  }
  
  _handleHover(x, y, clientX, clientY) {
    if (!this.tooltip) return;
    
    // Check if hovering over a block
    for (const block of this.blocks) {
      const x1 = this._timeToX(block.start_time);
      const x2 = this._timeToX(block.end_time);
      const y1 = this._kmToY(block.start_km);
      const y2 = this._kmToY(block.end_km);
      
      const blockWidth = Math.max(8, x2 - x1);
      const blockHeight = Math.max(12, Math.abs(y2 - y1));
      const blockTop = Math.min(y1, y2);
      
      if (x >= x1 && x <= x1 + blockWidth && y >= blockTop && y <= blockTop + blockHeight) {
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = `${clientX + 15}px`;
        this.tooltip.style.top = `${clientY + 15}px`;
        
        const depts = block.participating_departments.join(', ');
        const machines = block.allocated_machines.length ? block.allocated_machines.join(', ') : 'Manual Squads';
        
        this.tooltip.innerHTML = `
          <div style="font-weight: 700; color: #f5a623; margin-bottom: 4px;">⚡ ${block.block_id} (${block.sanction_status})</div>
          <div style="font-size: 0.8rem; color: #f1f5f9;"><b>Section:</b> ${block.station_from} ➔ ${block.station_to} [${block.line}]</div>
          <div style="font-size: 0.8rem; color: #f1f5f9;"><b>Window:</b> ${block.start_time} - ${block.end_time} (${block.duration_minutes} min)</div>
          <div style="font-size: 0.8rem; color: #34d399;"><b>Coordinated Depts:</b> ${depts}</div>
          <div style="font-size: 0.8rem; color: #94a3b8;"><b>Machines:</b> ${machines}</div>
          <div style="font-size: 0.8rem; color: #38bdf8; margin-top: 4px;"><b>Bundled Tasks:</b> ${block.bundled_tasks.length} tasks | Shadow Gain: ${block.coordination_efficiency_gain_pct}%</div>
        `;
        return;
      }
    }
    
    this.tooltip.style.display = 'none';
  }
}

window.MareyStringChart = MareyStringChart;

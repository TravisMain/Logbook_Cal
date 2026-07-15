// Standalone Web Application Logic for Business Travel Logbook Generator
// Runs directly in browser using SheetJS (XLSX)

const initialClients = [];

const freqOptions = ["Very Frequent", "Frequent", "Regular", "Occasional", "Rare"];
const freqWeights = { "Very Frequent": 10, "Frequent": 6, "Regular": 4, "Occasional": 2, "Rare": 1 };

let clients = [...initialClients];

document.addEventListener("DOMContentLoaded", () => {
    renderClientsTable();
    setupEventListeners();
    updateLiveSummary();
});

function setupEventListeners() {
    document.getElementById("addClientBtn").addEventListener("click", () => {
        clients.push({ name: "", dist: 0, freq: "Frequent" });
        renderClientsTable();
    });

    ["openOdo", "closeOdo", "targetBizKm"].forEach(id => {
        document.getElementById(id).addEventListener("input", updateLiveSummary);
    });

    document.getElementById("generateBtn").addEventListener("click", generateAndDownloadExcel);
}

function renderClientsTable() {
    const tbody = document.getElementById("clientsBody");
    tbody.innerHTML = "";

    clients.forEach((client, idx) => {
        const tr = document.createElement("tr");

        // Name input
        const tdName = document.createElement("td");
        const inpName = document.createElement("input");
        inpName.type = "text";
        inpName.value = client.name;
        inpName.addEventListener("input", e => clients[idx].name = e.target.value);
        tdName.appendChild(inpName);
        tr.appendChild(tdName);

        // Distance input
        const tdDist = document.createElement("td");
        tdDist.className = "text-center";
        const inpDist = document.createElement("input");
        inpDist.type = "number";
        inpDist.value = client.dist;
        inpDist.style.textAlign = "center";
        inpDist.addEventListener("input", e => {
            clients[idx].dist = parseFloat(e.target.value) || 0;
            if (document.getElementById("roundOnly").checked) {
                clients[idx].dist = Math.round(clients[idx].dist);
            }
        });
        tdDist.appendChild(inpDist);
        tr.appendChild(tdDist);

        // Frequency select
        const tdFreq = document.createElement("td");
        tdFreq.className = "text-center";
        const selFreq = document.createElement("select");
        freqOptions.forEach(opt => {
            const o = document.createElement("option");
            o.value = opt;
            o.textContent = opt;
            if (opt === client.freq) o.selected = true;
            selFreq.appendChild(o);
        });
        selFreq.addEventListener("change", e => clients[idx].freq = e.target.value);
        tdFreq.appendChild(selFreq);
        tr.appendChild(tdFreq);

        // Action delete button
        const tdAct = document.createElement("td");
        tdAct.className = "text-center";
        const btnDel = document.createElement("button");
        btnDel.className = "btn btn-danger";
        btnDel.innerHTML = "🗑️";
        btnDel.title = "Remove destination";
        btnDel.addEventListener("click", () => {
            clients.splice(idx, 1);
            renderClientsTable();
        });
        tdAct.appendChild(btnDel);
        tr.appendChild(tdAct);

        tbody.appendChild(tr);
    });
}

function updateLiveSummary() {
    const open = parseInt(document.getElementById("openOdo").value) || 0;
    const close = parseInt(document.getElementById("closeOdo").value) || 0;
    const biz = parseInt(document.getElementById("targetBizKm").value) || 0;

    const total = Math.max(0, close - open);
    const priv = Math.max(0, total - biz);
    const pct = total > 0 ? ((biz / total) * 100).toFixed(1) : "0.0";

    document.getElementById("statTotalKm").textContent = total.toLocaleString();
    document.getElementById("statBizKm").textContent = biz.toLocaleString();
    document.getElementById("statPrivateKm").textContent = priv.toLocaleString();
    document.getElementById("statBizPct").textContent = `${pct}%`;
}

// Math Engine & SheetJS Generator
function generateAndDownloadExcel() {
    if (clients.length === 0) {
        alert("Please add at least one client destination.");
        return;
    }

    const startStr = document.getElementById("startDate").value || "";
    const endStr = document.getElementById("endDate").value || "";
    const openOdo = parseInt(document.getElementById("openOdo").value) || 0;
    const closeOdo = parseInt(document.getElementById("closeOdo").value) || 0;
    const targetBiz = parseInt(document.getElementById("targetBizKm").value) || 0;
    const roundOnly = document.getElementById("roundOnly").checked;

    const startDt = new Date(startStr);
    const endDt = new Date(endStr);
    if (isNaN(startDt) || isNaN(endDt) || endDt <= startDt) {
        alert("Please select valid Start and End dates.");
        return;
    }

    const btn = document.getElementById("generateBtn");
    btn.disabled = true;
    btn.innerHTML = "⌛ Generating Logbook...";

    setTimeout(() => {
        try {
            const { ledger, allTrips } = runTripGenerator(startDt, endDt, openOdo, closeOdo, targetBiz, roundOnly);
            exportToXLSX(startStr, endStr, openOdo, closeOdo, targetBiz, roundOnly, ledger, allTrips);
            btn.innerHTML = "✅ Downloaded Successfully! Generate Again?";
            setTimeout(() => btn.innerHTML = '✨ Generate & Download Excel Logbook (.xlsx)', 4000);
        } catch (err) {
            alert("Error generating logbook: " + err.message);
            btn.innerHTML = '✨ Generate & Download Excel Logbook (.xlsx)';
        } finally {
            btn.disabled = false;
        }
    }, 100);
}

function runTripGenerator(startDt, endDt, openOdo, closeOdo, targetBiz, roundOnly) {
    const weekdays = [];
    let cur = new Date(startDt);
    while (cur <= endDt) {
        const day = cur.getDay();
        if (day !== 0 && day !== 6) weekdays.push(new Date(cur));
        cur.setDate(cur.getDate() + 1);
    }

    const remKm = targetBiz;
    const avgDist = clients.reduce((sum, c) => sum + c.dist * 2, 0) / clients.length;

    const weightedClients = [];
    clients.forEach(c => {
        const w = freqWeights[c.freq] || 3;
        for (let i = 0; i < w; i++) weightedClients.push(c);
    });

    // Select a random 2-week vacation period (14 days) between April 1st and October 1st of the start year
    const startYear = startDt.getFullYear();
    const vacStart = new Date(startYear, 3, 1 + Math.floor(Math.random() * 150)); // April 1st + up to 150 days
    const vacEnd = new Date(vacStart);
    vacEnd.setDate(vacStart.getDate() + 13); // 14 days total (inclusive)

    // Exclude standard SA public holidays and the simulated vacation period
    const isHoliday = (date) => {
        const y = date.getFullYear();
        const m = date.getMonth();
        const d = date.getDate();
        
        // Fixed SA public holidays
        if (m === 0 && d === 1) return true;   // New Year's Day (Jan 1)
        if (m === 2 && d === 21) return true;  // Human Rights Day (Mar 21)
        if (m === 3 && d === 27) return true;  // Freedom Day (Apr 27)
        if (m === 4 && d === 1) return true;   // Worker's Day (May 1)
        if (m === 5 && d === 16) return true;  // Youth Day (Jun 16)
        if (m === 7 && d === 9) return true;   // National Women's Day (Aug 9)
        if (m === 8 && d === 24) return true;  // Heritage Day (Sep 24)
        if (m === 11 && d === 16) return true; // Day of Reconciliation (Dec 16)
        if (m === 11 && d === 25) return true; // Christmas Day (Dec 25)
        if (m === 11 && d === 26) return true; // Day of Goodwill (Dec 26)

        // Annual business shutdown: No business travel between 15th December and 5th January (inclusive)
        if (m === 11 && d >= 15) return true;
        if (m === 0 && d <= 5) return true;
        
        // Easter-related holidays (Good Friday / Family Day)
        // Approximate for standard 2025/2026:
        if (y === 2025) {
            if (m === 3 && (d === 18 || d === 21)) return true; // Good Friday: Apr 18, Family Day: Apr 21
        } else if (y === 2026) {
            if (m === 3 && (d === 3 || d === 6)) return true;   // Good Friday: Apr 3, Family Day: Apr 6
        }

        // Simulated 2-week vacation period
        if (date >= vacStart && date <= vacEnd) return true;
        
        return false;
    };

    const getMonthWeight = (date) => {
        // December (month index 11) is quiet
        if (date.getMonth() === 11) return 0.2;
        return 1.0;
    };

    const activeWeekdays = weekdays.filter(dt => !isHoliday(dt));

    // Shuffle pool with monthly weights (weighted random distribution)
    const shuffledPool = activeWeekdays.map(dt => ({
        sort: Math.random() * (1.0 / getMonthWeight(dt)),
        value: dt
    })).sort((a, b) => a.sort - b.sort).map(a => a.value);

    // Initial estimate of number of trips needed
    let numTrips = Math.max(40, Math.min(shuffledPool.length - 10, Math.floor(remKm / Math.max(10, avgDist * 0.9))));
    let selectedDays = shuffledPool.slice(0, numTrips);

    // Helper to build a trip object for a date
    function buildTrip(dt) {
        if (clients.length >= 2 && Math.random() < 0.10) {
            const idx1 = Math.floor(Math.random() * clients.length);
            const c1 = clients[idx1];
            const candidates = clients.filter((c, i) => i !== idx1 && Math.abs(c.dist - c1.dist) <= 15);
            
            if (candidates.length > 0) {
                const c2 = candidates[Math.floor(Math.random() * candidates.length)];
                const dist1 = roundOnly ? Math.round(c1.dist) : c1.dist;
                const dist2 = roundOnly ? Math.round(c2.dist) : c2.dist;
                const transitDist = roundOnly ? Math.round(5 + Math.random() * 10) : (5 + Math.random() * 10);
                return {
                    date: dt,
                    type: 'cluster',
                    clients: [c1.name, c2.name],
                    base_dists: [c1.dist, c2.dist],
                    legs: [
                        { frm: "Work", to: c1.name, dist: dist1 },
                        { frm: c1.name, to: c2.name, dist: transitDist },
                        { frm: c2.name, to: "Work", dist: dist2 }
                    ]
                };
            }
        }
        
        // Simple return trip
        const c = weightedClients[Math.floor(Math.random() * weightedClients.length)];
        const dist = roundOnly ? Math.round(c.dist) : c.dist;
        return {
            date: dt,
            type: 'simple',
            client: c.name,
            base_dist: c.dist,
            legs: [
                { frm: "Work", to: c.name, dist: dist },
                { frm: c.name, to: "Work", dist: dist }
            ]
        };
    }

    // Build initial trips
    let tripObjects = selectedDays.map(dt => buildTrip(dt));

    // Dynamic adjustment of trip counts to align close to targetBiz before micro-balancing
    let total = tripObjects.reduce((sum, t) => sum + t.legs.reduce((s, l) => s + l.dist, 0), 0);
    let diff = targetBiz - total;

    // Remaining unused days pool
    let unusedDays = shuffledPool.slice(numTrips);

    let adjustmentAttempts = 0;
    while (Math.abs(diff) > 40 && adjustmentAttempts < 1000) {
        adjustmentAttempts++;
        if (diff > 0 && unusedDays.length > 0) {
            const nextDt = unusedDays.pop();
            const newT = buildTrip(nextDt);
            tripObjects.push(newT);
            diff -= newT.legs.reduce((s, l) => s + l.dist, 0);
        } else if (diff < 0 && tripObjects.length > 30) {
            const removed = tripObjects.pop();
            unusedDays.push(removed.date);
            diff += removed.legs.reduce((s, l) => s + l.dist, 0);
        } else {
            break;
        }
    }

    // Sort trips chronologically for date progression realism
    tripObjects.sort((a, b) => a.date - b.date);

    // Exact balance
    total = tripObjects.reduce((sum, t) => sum + t.legs.reduce((s, l) => s + l.dist, 0), 0);
    diff = Math.round((targetBiz - total) * 10) / 10;

    if (roundOnly) {
        let diffInt = Math.round(diff);
        let oddAdjustedIdx = -1;
        
        // Odd balancing: adjust one leg of a simple trip
        if (diffInt % 2 !== 0) {
            for (let i = 0; i < tripObjects.length; i++) {
                if (tripObjects[i].type === 'simple') {
                    tripObjects[i].legs[0].dist += (diffInt > 0 ? 1 : -1);
                    tripObjects[i].legs[0].dist = Math.max(1, tripObjects[i].legs[0].dist);
                    diffInt += (diffInt > 0 ? -1 : 1);
                    oddAdjustedIdx = i;
                    break;
                }
            }
        }

        // Even balancing: adjust in pairs of 2 km, enforcing STRICT maximum variance of +/- 2 km one-way!
        let balancingAttempts = 0;
        while (diffInt !== 0 && balancingAttempts < 20000) {
            balancingAttempts++;
            const tIdx = Math.floor(Math.random() * tripObjects.length);
            if (tIdx === oddAdjustedIdx) continue;
            
            const t = tripObjects[tIdx];
            if (t.type === 'simple') {
                const base = t.base_dist;
                const cur = t.legs[0].dist;
                // STRICT VARIANCE CHECK: No single leg can exceed +/- 2 km from base distance!
                if (diffInt > 0 && cur < base + 2) {
                    t.legs[0].dist += 1;
                    t.legs[1].dist += 1;
                    diffInt -= 2;
                } else if (diffInt < 0 && cur > Math.max(1, base - 2)) {
                    t.legs[0].dist -= 1;
                    t.legs[1].dist -= 1;
                    diffInt += 2;
                }
            } else if (t.type === 'cluster') {
                const base1 = t.base_dists[0];
                const cur1 = t.legs[0].dist;
                if (diffInt > 0 && cur1 < base1 + 2) {
                    t.legs[0].dist += 1;
                    t.legs[2].dist += 1;
                    diffInt -= 2;
                } else if (diffInt < 0 && cur1 > Math.max(1, base1 - 2)) {
                    t.legs[0].dist -= 1;
                    t.legs[2].dist -= 1;
                    diffInt += 2;
                }
            }
        }
    } else {
        // Decimal adjustment
        let balancingAttempts = 0;
        while (Math.abs(diff) > 1e-5 && balancingAttempts < 20000) {
            balancingAttempts++;
            const t = tripObjects[Math.floor(Math.random() * tripObjects.length)];
            const delta = Math.round((diff > 0 ? 0.1 : -0.1) * 10) / 10;
            if (t.type === 'simple') {
                t.legs[0].dist = Math.round((t.legs[0].dist + delta) * 10) / 10;
                t.legs[1].dist = Math.round((t.legs[1].dist + delta) * 10) / 10;
                diff = Math.round((diff - delta * 2) * 10) / 10;
            }
        }
    }

    // Flatten legs for final processing
    const allTrips = [];
    tripObjects.forEach(t => {
        t.legs.forEach(l => {
            allTrips.push({ date: t.date, frm: l.frm, to: l.to, dist: l.dist });
        });
    });

    // Compute Odometer Ledger
    const tripDates = Array.from(new Set(allTrips.map(l => l.date.toISOString().split('T')[0]))).map(s => new Date(s)).sort((a,b) => a-b);
    const gaps = [];
    gaps.push({ days: Math.max(1, Math.floor((tripDates[0] - startDt) / 86400000)) });
    for (let i = 0; i < tripDates.length - 1; i++) {
        gaps.push({ days: Math.max(1, Math.floor((tripDates[i+1] - tripDates[i]) / 86400000)) });
    }
    gaps.push({ days: Math.max(1, Math.floor((endDt - tripDates[tripDates.length-1]) / 86400000)) });

    const totalGapDays = gaps.reduce((sum, g) => sum + g.days, 0);
    const totalPrivKm = (closeOdo - openOdo) - targetBiz;

    let privPerGap = [];
    if (roundOnly) {
        // Distribute private km with high random variance
        privPerGap = gaps.map(g => {
            const base = totalPrivKm * g.days / totalGapDays;
            // High variance: multiply by random factor 0.4 to 1.6
            const factor = 0.4 + Math.random() * 1.2;
            return Math.round(base * factor);
        });

        // Reconcile rounding error randomly across all gaps so they remain integers
        let sumPriv = privPerGap.reduce((a, b) => a + b, 0);
        let err = totalPrivKm - sumPriv;
        let reconAttempts = 0;
        while (err !== 0 && reconAttempts < 5000) {
            reconAttempts++;
            const randIdx = Math.floor(Math.random() * privPerGap.length);
            if (err > 0) {
                privPerGap[randIdx]++;
                err--;
            } else {
                if (privPerGap[randIdx] > 10) {
                    privPerGap[randIdx]--;
                    err++;
                }
            }
        }
    } else {
        // Standard decimal distribution with slight random noise
        privPerGap = gaps.map(g => {
            const base = totalPrivKm * g.days / totalGapDays;
            const factor = 0.8 + Math.random() * 0.4;
            return Math.round(base * factor * 10) / 10;
        });
        const err = Math.round((totalPrivKm - privPerGap.reduce((a,b)=>a+b, 0)) * 10) / 10;
        privPerGap[privPerGap.length - 1] = Math.round((privPerGap[privPerGap.length - 1] + err) * 10) / 10;
    }

    const privBefore = {};
    tripDates.forEach((dt, i) => {
        privBefore[dt.toISOString().split('T')[0]] = privPerGap[i];
    });

    const ledger = [];
    let curOdo = openOdo;
    let lastDtStr = null;

    for (let i = 0; i < allTrips.length; i++) {
        const leg = allTrips[i];
        const dtStr = leg.date.toISOString().split('T')[0];
        if (lastDtStr === null || dtStr !== lastDtStr) {
            curOdo += (privBefore[dtStr] || 0);
        }
        const open = curOdo;
        const close = curOdo + leg.dist;
        ledger.push({
            dateStr: dtStr,
            from: leg.frm,
            to: leg.to,
            openOdo: open,
            closeOdo: close,
            bizKm: leg.dist
        });
        curOdo = close;
        lastDtStr = dtStr;
    }

    return { ledger, allTrips };
}

function exportToXLSX(startStr, endStr, openOdo, closeOdo, targetBiz, roundOnly, ledger, allTrips) {
    const wb = XLSX.utils.book_new();

    // Visit summary
    const visitCounts = {};
    allTrips.forEach(l => {
        if (l.to !== "Work" && l.to !== "Home") visitCounts[l.to] = (visitCounts[l.to] || 0) + 1;
        if (l.frm !== "Work" && l.frm !== "Home") visitCounts[l.frm] = (visitCounts[l.frm] || 0) + 1;
    });

    // Formatting templates
    const fontName = 'Calibri';
    const borderThin = { style: 'thin', color: { rgb: 'D3D3D3' } };
    const borderDouble = { style: 'double', color: { rgb: '336633' } };

    const styleTitle = {
        font: { name: fontName, sz: 18, bold: true, color: { rgb: '1F4E79' } },
        alignment: { horizontal: 'center', vertical: 'center' }
    };

    const styleSubtitle = {
        font: { name: fontName, sz: 12, bold: true, color: { rgb: '4472C4' } },
        alignment: { horizontal: 'center', vertical: 'center' }
    };

    const styleSectionHeader = {
        font: { name: fontName, sz: 11, bold: true, color: { rgb: '000000' } },
        border: { bottom: { style: 'medium', color: { rgb: '000000' } } },
        alignment: { horizontal: 'left', vertical: 'center' }
    };

    const styleLabel = {
        font: { name: fontName, sz: 11 },
        alignment: { horizontal: 'left', vertical: 'center' }
    };

    const styleValue = {
        font: { name: fontName, sz: 11 },
        alignment: { horizontal: 'right', vertical: 'center' }
    };

    const styleHeader = {
        font: { name: fontName, sz: 11, bold: true, color: { rgb: 'FFFFFF' } },
        fill: { fgColor: { rgb: '1F4E79' } },
        alignment: { horizontal: 'center', vertical: 'center' },
        border: { top: borderThin, bottom: borderThin, left: borderThin, right: borderThin }
    };

    // Helper to generate empty cell with style
    const emptyCell = (styleObj) => ({ v: "", t: 's', s: styleObj });

    // 1. COVER SHEET WORKBOOK
    const ws1 = {};
    ws1['!merges'] = [
        { s: { r: 1, c: 1 }, e: { r: 1, c: 2 } }, // B2:C2 Title
        { s: { r: 2, c: 1 }, e: { r: 2, c: 2 } }  // B3:C3 Subtitle
    ];

    ws1['B2'] = { v: "BUSINESS TRAVEL LOGBOOK", t: 's', s: styleTitle };
    ws1['B3'] = { v: `${startStr} – ${endStr}`, t: 's', s: styleSubtitle };

    ws1['B5'] = { v: "Vehicle Summary", t: 's', s: styleSectionHeader };
    ws1['C5'] = emptyCell(styleSectionHeader);
    ws1['B6'] = { v: "Opening Odometer:", t: 's', s: styleLabel };
    ws1['C6'] = { v: openOdo, t: 'n', z: '#,##0" km"', s: styleValue };
    ws1['B7'] = { v: "Closing Odometer:", t: 's', s: styleLabel };
    ws1['C7'] = { v: closeOdo, t: 'n', z: '#,##0" km"', s: styleValue };

    ws1['B9'] = { v: "Kilometre Summary", t: 's', s: styleSectionHeader };
    ws1['C9'] = emptyCell(styleSectionHeader);
    ws1['B10'] = { v: "Total Vehicle km:", t: 's', s: styleLabel };
    ws1['C10'] = { f: "C7-C6", t: 'n', z: '#,##0" km"', s: styleValue };
    ws1['B11'] = { v: "Business km:", t: 's', s: styleLabel };
    ws1['C11'] = { v: targetBiz, t: 'n', z: '#,##0" km"', s: styleValue };
    ws1['B12'] = { v: "Private km:", t: 's', s: styleLabel };
    ws1['C12'] = { f: "C10-C11", t: 'n', z: '#,##0" km"', s: styleValue };

    ws1['B14'] = { v: "Client Visit Summary", t: 's', s: styleSectionHeader };
    ws1['C14'] = emptyCell(styleSectionHeader);

    ws1['B15'] = { v: "Client / Destination", t: 's', s: styleHeader };
    ws1['C15'] = { v: "Visits", t: 's', s: styleHeader };

    let rIdx = 16;
    clients.forEach((c, i) => {
        const rowBg = i % 2 === 0 ? 'D6E4F0' : 'FFFFFF';
        const styleRowLabel = {
            font: { name: fontName, sz: 11 },
            alignment: { horizontal: 'left', vertical: 'center' },
            fill: { fgColor: { rgb: rowBg } },
            border: { top: borderThin, bottom: borderThin, left: borderThin, right: borderThin }
        };
        const styleRowVal = {
            font: { name: fontName, sz: 11 },
            alignment: { horizontal: 'center', vertical: 'center' },
            fill: { fgColor: { rgb: rowBg } },
            border: { top: borderThin, bottom: borderThin, left: borderThin, right: borderThin }
        };

        ws1[`B${rIdx}`] = { v: c.name, t: 's', s: styleRowLabel };
        ws1[`C${rIdx}`] = { v: visitCounts[c.name] || 0, t: 'n', z: '#,##0', s: styleRowVal };
        rIdx++;
    });

    const styleSummary = {
        font: { name: fontName, sz: 11, bold: true },
        fill: { fgColor: { rgb: 'E2EFDA' } },
        alignment: { horizontal: 'center', vertical: 'center' },
        border: { top: borderThin, bottom: borderDouble, left: borderThin, right: borderThin }
    };
    const styleSummaryLabel = {
        font: { name: fontName, sz: 11, bold: true },
        fill: { fgColor: { rgb: 'E2EFDA' } },
        alignment: { horizontal: 'left', vertical: 'center' },
        border: { top: borderThin, bottom: borderDouble, left: borderThin, right: borderThin }
    };

    ws1[`B${rIdx}`] = { v: "TOTAL VISITS", t: 's', s: styleSummaryLabel };
    ws1[`C${rIdx}`] = { f: `SUM(C16:C${rIdx-1})`, t: 'n', z: '#,##0', s: styleSummary };

    ws1['!ref'] = `A1:C${rIdx}`;
    ws1['!cols'] = [{ wch: 5 }, { wch: 32 }, { wch: 20 }];

    XLSX.utils.book_append_sheet(wb, ws1, "Cover Sheet");

    // 2. BUSINESS LOGBOOK WORKBOOK
    const ws2 = {};
    ws2['!merges'] = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: 5 } } // A1:F1 Title
    ];

    ws2['A1'] = { v: `BUSINESS TRAVEL LOGBOOK — ${startStr} to ${endStr}`, t: 's', s: styleTitle };

    const logbookHeaders = ["Date", "From", "To", "Opening Odo", "Closing Odo", "Business km"];
    logbookHeaders.forEach((h, cIdx) => {
        const cellRef = XLSX.utils.encode_cell({ r: 2, c: cIdx });
        ws2[cellRef] = { v: h, t: 's', s: styleHeader };
    });

    const numFmt = roundOnly ? '#,##0' : '#,##0.0';

    let lastSeenDate = "";
    let useFill = false;

    ledger.forEach((r, idx) => {
        const row = 3 + idx;
        
        // Zebra striping by date pairs
        if (r.dateStr !== lastSeenDate) {
            useFill = !useFill;
            lastSeenDate = r.dateStr;
        }
        const rowBg = useFill ? 'D6E4F0' : 'FFFFFF';

        const styleCell = (align) => ({
            font: { name: fontName, sz: 11 },
            alignment: { horizontal: align, vertical: 'center' },
            fill: { fgColor: { rgb: rowBg } },
            border: { top: borderThin, bottom: borderThin, left: borderThin, right: borderThin }
        });

        const parts = r.dateStr.split('-');
        const dateVal = new Date(parts[0], parts[1]-1, parts[2]);

        ws2[`A${row+1}`] = { v: dateVal, t: 'd', z: 'yyyy-mm-dd', s: styleCell('center') };
        ws2[`B${row+1}`] = { v: r.from, t: 's', s: styleCell('left') };
        ws2[`C${row+1}`] = { v: r.to, t: 's', s: styleCell('left') };
        ws2[`D${row+1}`] = { v: r.openOdo, t: 'n', z: numFmt, s: styleCell('right') };
        ws2[`E${row+1}`] = { v: r.closeOdo, t: 'n', z: numFmt, s: styleCell('right') };
        ws2[`F${row+1}`] = { v: r.bizKm, t: 'n', z: numFmt, s: styleCell('right') };
    });

    const totalRow = 3 + ledger.length + 2;
    ws2[`E${totalRow}`] = { v: "TOTAL BUSINESS KM:", t: 's', s: { font: { name: fontName, sz: 11, bold: true }, alignment: { horizontal: 'right', vertical: 'center' } } };
    ws2[`F${totalRow}`] = { f: `SUM(F4:F${totalRow-2})`, t: 'n', z: numFmt, s: styleSummary };

    ws2['!ref'] = `A1:F${totalRow}`;
    ws2['!cols'] = [{ wch: 14 }, { wch: 28 }, { wch: 28 }, { wch: 16 }, { wch: 16 }, { wch: 14 }];

    XLSX.utils.book_append_sheet(wb, ws2, "Business Logbook");

    XLSX.writeFile(wb, `Business_Travel_Logbook_${startStr}_to_${endStr}.xlsx`);
}

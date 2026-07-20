DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>PhishGuard Dashboard</title>
  <style>
    body {
      font-family: -apple-system, Segoe UI, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 20px;
      background: #f7f8fa;
      color: #222;
    }
    h1 { font-size: 24px; }
    .stats { display: flex; gap: 16px; margin-bottom: 24px; }
    .stat-card {
      background: white; border-radius: 8px; padding: 16px 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stat-number { font-size: 28px; font-weight: bold; }
    .stat-label { font-size: 13px; color: #666; }
    table {
      width: 100%; border-collapse: collapse; background: white;
      border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid #eee; font-size: 13px; }
    th { background: #fafafa; }
    .badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .badge-phishing { background: #fdecea; color: #c0392b; }
    .badge-safe { background: #e6f4ea; color: #1e7e34; }
    .url-cell { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  </style>
</head>
<body>
  <h1>PhishGuard Dashboard</h1>
  <div class="stats" id="stats"></div>
  <table>
    <thead><tr><th>URL</th><th>Score</th><th>Verdict</th><th>Scanned At</th></tr></thead>
    <tbody id="scan-rows"></tbody>
  </table>
  <script>
    async function loadHistory() {
      const res = await fetch('/history');
      const data = await res.json();
      document.getElementById('stats').innerHTML = `
        <div class="stat-card"><div class="stat-number">${data.stats.total_scans}</div><div class="stat-label">Total Scans</div></div>
        <div class="stat-card"><div class="stat-number">${data.stats.flagged_count}</div><div class="stat-label">Flagged as Phishing</div></div>
      `;
      const rows = data.scans.map(scan => {
        const badgeClass = scan.verdict === 'phishing' ? 'badge-phishing' : 'badge-safe';
        const time = new Date(scan.scanned_at + 'Z').toLocaleString();
        return `<tr><td class="url-cell" title="${scan.url}">${scan.url}</td><td>${scan.score}</td><td><span class="badge ${badgeClass}">${scan.verdict}</span></td><td>${time}</td></tr>`;
      }).join('');
      document.getElementById('scan-rows').innerHTML = rows;
    }
    loadHistory();
  </script>
</body>
</html>
"""
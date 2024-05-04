<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Drone Control Panel</title>
<style>
  body {
    background-color: #fdb515; /* Set background color to #fdb515 */
    color: #003262; /* Set text color to #003262 */
    font-family: Arial, sans-serif; /* Change font to Arial */
  }
  canvas {
    background-color: #f0f0f0; /* Set grid background color to #f0f0f0 */
    border: 1px solid #003262; /* Set border color to #003262 */
    display: block;
    margin: 20px auto;
  }
  h1 {
    text-align: center; /* Center align the title */
    font-family: Impact, Charcoal, sans-serif; /* Change font family of title */
    font-size: 60px; /* Set font size to 60 pixels */
  }
  p {
    margin-left: 20px; /* Add left margin to paragraphs */
    margin-bottom: 10px; /* Add bottom margin to paragraphs */
  }
  p strong {
    font-weight: bold; /* Make words before ":" bold */
  }
  .button-container {
    text-align: center; /* Center align button container */
    margin-bottom: 20px; /* Add margin at the bottom of button container */
  }
  .button {
    display: inline-block;
    padding: 20px 40px;
    font-size: 24px;
    background-color: #003262; /* Set button background color to dark blue */
    color: #ffffff; /* Set button text color to white */
    border: none;
    cursor: pointer;
    margin: 20px;
    border-radius: 10px;
    text-align: center;
  }
  .gps-info {
    font-size: 28px; /* Set font size to 28 pixels */
  }
  .grid-info {
    display: flex;
    justify-content: space-between; /* Align items with equal space between them */
    margin: 20px; /* Add margin around the grid info */
  }
  .logo-container {
    position: absolute; /* Set logo container position to absolute */
    top: 20px; /* Set top spacing */
    right: 20px; /* Set right spacing */
  }
  .logo {
    width: 100px; /* Set logo width */
    height: auto; /* Maintain aspect ratio */
  }
</style>
</head>
<body>
<div class="logo-container">
  <img src="your_logo.png" alt="Logo" class="logo"> <!-- Replace "your_logo.png" with your logo file path -->
</div>
<h1><span style="font-weight:normal;">Drone</span> Control Panel</h1>
<div class="grid-info">
  <div>
    <p><strong>Distance</strong>: {dist} meters</p>
    <p><strong>Direction</strong>: {direction} degrees from north</p>
    <p><strong>Package Type</strong>: {packs['bcn'][2]}</p>
  </div>
  <div>
    <p class="gps-info"><strong>Beacon GPS</strong>: {bcn_gps}</p>
    <p class="gps-info"><strong>Drone GPS</strong>: {drn_gps}</p>
  </div>
</div>
<div style="text-align: center;"> <!-- Center the grid -->
  <canvas id="gridCanvas" width="500" height="500"></canvas>
  <script>
    const canvas = document.getElementById('gridCanvas');
    const ctx = canvas.getContext('2d');
    const gridSize = 50; // Each grid block represents 20 meters
    const kmRange = 1; // The grid represents 1 km in each direction
    const centerGridX = canvas.width / 2;
    const centerGridY = canvas.height / 2;

    function drawGrid() {
      ctx.fillStyle = '#f0f0f0'; /* Set grid background color to #f0f0f0 */
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      for (let x = 0; x <= canvas.width; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.moveTo(0, x);
        ctx.lineTo(canvas.width, x);
      }
      ctx.strokeStyle = '#003262'; /* Set stroke color to #003262 */
      ctx.stroke();
      ctx.fillText('N  1km', centerGridX - 10, 20);
      ctx.fillText('S  1km', centerGridX - 10, canvas.height - 5);
      ctx.fillText('E  1km', canvas.width - 25, centerGridY + 5);
      ctx.fillText('W  1km', 5, centerGridY + 5);
    }

    function drawPoints() {
      const groundStation = { x: centerGridX, y: centerGridY, color: 'blue', label: 'Ground Station' };
      const dronePosition = { x: centerGridX + ({gnd_gps[1]} - {drn_gps[1]}) * 1000 * 50, y: centerGridY - ({gnd_gps[0]} - {drn_gps[0]}) * 1000 * 50, color: 'red', label: 'Drone' };
      const beaconPosition = { x: centerGridX + ({gnd_gps[1]} - {bcn_gps[1]}) * 1000 * 50, y: centerGridY - ({gnd_gps[0]} - {bcn_gps[0]}) * 1000 * 50, color: 'green', label: 'Beacon' };
      

      [groundStation, dronePosition, beaconPosition].forEach(point => {
        ctx.fillStyle = point.color;
        ctx.beginPath();
        ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillText(point.label, point.x + 10, point.y - 10);
      });
    }

    drawGrid();
    drawPoints();
  </script>
</div>
<div class="button-container">
  <button class="button">Load</button>
  <button class="button">Deploy</button>
</div>
<p><strong>Distance</strong>: {dist} meters</p>
<p><strong>Direction</strong>: {direction} degrees from north</p>
<p><strong>Package Type</strong>: {packs['bcn'][2]}</p>
<p><strong>Uptime</strong>: {uptime_seconds:.2f} seconds</p>
<p><strong>Free Memory</strong>: {free_memory} bytes</p>
</body>
</html>

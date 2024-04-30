def handle_root(client, request):
    last_option = read_last_option()
    uptime_seconds = time.ticks_ms() / 1000
    free_memory = gc.mem_free()
    bcn_gps = [packs['bcn'][0][1], packs['bcn'][0][2]]
    drn_gps = [packs['drn'][0][1], packs['drn'][0][2]]
    dist = haversine(packs['bcn'], packs['drn'])
    direction = calculate_bearing(packs['bcn'], packs['drn'])

    submit_button_html = ""
    if dist <= 5:
        submit_button_html = """
        <form action="/submit" method="post">
            <button type="submit" name="action" value="drop_package">Drop Package</button>
        </form>
        """

    html_content = f"""
    <html>
        <head>
            <title>ESP32 Uptime & Option Select</title>
            <meta http-equiv="refresh" content="5">
        </head>
        <body>
            <h1>Drone Uptime & GPS Info</h1>
            <p>Uptime: {uptime_seconds:.2f} seconds</p>
            <p>Free Memory: {free_memory} bytes</p>
            <canvas id="gpsCanvas" width="300" height="300" style="border:1px solid #000;"></canvas>
            <script>
                var canvas = document.getElementById('gpsCanvas');
                var ctx = canvas.getContext('2d');
                // Scale the positions - you might need to adjust the scaling factor based on actual GPS ranges
                var scale = 50000; // Adjust scale based on expected GPS coordinate ranges
                var centerX = canvas.width / 2;
                var centerY = canvas.height / 2;
                var bcnX = centerX + ({bcn_gps[1]} * scale);
                var bcnY = centerY - ({bcn_gps[0]} * scale);
                var drnX = centerX + ({drn_gps[1]} * scale);
                var drnY = centerY - ({drn_gps[0]} * scale);

                // Draw Beacon
                ctx.fillStyle = 'blue';
                ctx.beginPath();
                ctx.arc(bcnX, bcnY, 5, 0, 2 * Math.PI);
                ctx.fill();

                // Draw Drone
                ctx.fillStyle = 'red';
                ctx.beginPath();
                ctx.arc(drnX, drnY, 5, 0, 2 * Math.PI);
                ctx.fill();
            </script>
            <p>Beacon GPS: {bcn_gps}</p>
            <p>Drone GPS: {drn_gps}</p>
            <p>Distance: {dist} meters</p>
            <p>Direction: {direction} degrees from north</p>
            <p>Blockages: {packs['drn'][3]}</p>
            <p>Altitude: {packs['drn'][4]}</p>
            <p>Package Type: {packs['bcn'][2]}</p>
            {submit_button_html}
        </body>
    </html>
    """
    send_response(client, html_content)

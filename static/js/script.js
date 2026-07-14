// ============================================================
// AttendIQ - Frontend JavaScript
// ============================================================
// This file handles two things on the Teacher Dashboard:
//   1. startAttendance() - Starts the live attendance session
//      and refreshes the QR code every 30 seconds
//   2. verifyWifi()      - Simulates checking if the student
//      is connected to the college Wi-Fi
// ============================================================

// This variable makes sure the timer doesn't start twice
let running = false;

// ============================================================
// HELPER: Build the correct base URL for the QR code
// Uses the LAN IP from the server so phones on same Wi-Fi can open it
// ============================================================
function buildStudentUrl(token) {
    // Use the server-detected LAN IP so the QR works from a phone.
    // If localIp is not defined (e.g., on student page), fall back to current host.
    const ip   = (typeof localIp !== 'undefined' && localIp) ? localIp : window.location.hostname;
    const port = window.location.port;

    // Build origin: include port only if it is non-standard
    const origin = (port && port !== '80' && port !== '443')
        ? `${window.location.protocol}//${ip}:${port}`
        : `${window.location.protocol}//${ip}`;

    return `${origin}/student?token=${token}`;
}

// ============================================================
// HELPER: Generate a fresh QR code image and update the <img> tag
// ============================================================
function refreshQR() {
    // Generate a random token (one-time code) to make each QR unique
    const token = Math.random().toString(36).substring(2, 10);

    // Build the student URL that the QR will encode
    const studentUrl = buildStudentUrl(token);

    // Show the URL under the QR so the teacher can verify it
    const urlDisplay = document.getElementById("qrUrl");
    if (urlDisplay) urlDisplay.textContent = studentUrl;

    // Encode the full URL properly for the QR API data parameter
    const encodedUrl = encodeURIComponent(studentUrl);

    // Update the QR code image
    document.getElementById("qr").src =
        `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodedUrl}`;
}

// ============================================================
// FUNCTION 1: Start Attendance Session
// Called when teacher clicks "Start Attendance" button
//
// STEP 1: Prevent starting again if already running
// STEP 2: Show "Live 🟢" status on screen
// STEP 3: Generate a QR code IMMEDIATELY
// STEP 4: Start a 5-minute countdown timer (300 seconds)
// STEP 5: Refresh the QR code every 30 seconds with a new random token
// ============================================================
function startAttendance() {

    // Step 1: If attendance is already running, do nothing
    if (running) return;
    running = true;

    // Step 2: Update status text to show attendance is live
    document.getElementById("status").innerHTML = "Live 🟢";

    // Step 3: Generate QR code IMMEDIATELY (don't wait for the interval)
    refreshQR();

    // Step 4: Start a 5-minute (300 second) countdown timer
    let seconds = 300;

    setInterval(() => {
        // Calculate minutes and seconds from total seconds
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;

        // Display as MM:SS format (e.g., 04:37)
        document.getElementById("timer").innerHTML =
            `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

        if (seconds > 0) seconds--;  // Decrease by 1 each second
    }, 1000);  // Run every 1000 milliseconds = 1 second

    // Step 5: Refresh QR code every 30 seconds with a new random link
    // (Longer interval is fine; the token is just for uniqueness)
    setInterval(refreshQR, 30000);  // Refresh every 30 seconds
}


// ============================================================
// FUNCTION 2: Verify College Wi-Fi
// Called when student clicks "Verify Wi-Fi" button on student page
//
// STEP 1: Show a "Verifying..." message
// STEP 2: Disable the verify button so it can't be clicked twice
// STEP 3: After 2 seconds, show success message
// STEP 4: Enable the "Mark Attendance" button once verified
//
// NOTE: This is currently a simulation (not a real Wi-Fi check).
//       It always shows success after 2 seconds.
// ============================================================
function verifyWifi() {

    // Get references to the HTML elements we need to update
    const status     = document.getElementById("wifiStatus");
    const verify     = document.getElementById("verifyBtn");
    const attendance = document.getElementById("attendanceBtn");

    // Step 1 & 2: Show verifying message and disable the button
    status.style.display = "block";
    status.innerHTML = "🤖 Verifying College Wi-Fi...";
    verify.disabled = true;

    // Step 3 & 4: After 2 seconds, show success and unlock attendance button
    setTimeout(() => {
        status.innerHTML = `
        <strong>✅ College Wi-Fi Verified</strong><br>
        📍 Connected Network : <b>Campus_WiFi</b><br>
        🏫 Location : <b>SKASC</b><br>
        🔒 Authentication Successful
        `;

        // Unlock the Mark Attendance button
        attendance.disabled = false;

        // Update verify button text to show it's done
        verify.innerHTML = "✅ Verified";
    }, 2000);  // Wait 2 seconds before showing result
}

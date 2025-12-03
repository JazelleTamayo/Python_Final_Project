document.addEventListener("DOMContentLoaded", function () {
    const qrDiv = document.getElementById("qr-reader");
    const resultBox = document.getElementById("scan-result");

    if (!qrDiv) {
        console.error("qr-reader element not found");
        return;
    }

    console.log("Html5Qrcode is:", typeof Html5Qrcode);
    if (typeof Html5Qrcode === "undefined") {
        console.error("Html5Qrcode library NOT loaded.");
        alert("QR library failed to load. Check console for details.");
        return;
    }

    const qrScanner = new Html5Qrcode("qr-reader");

    function isValidURL(text) {
        try {
            const url = new URL(text);
            return true;
        } catch {
            return false;
        }
    }

    function onSuccess(decodedText) {
        console.log("Scanned:", decodedText);

        if (!resultBox) return;

        // If scanned text is a URL → make clickable link
        if (isValidURL(decodedText)) {
            resultBox.innerHTML =
                `<a href="${decodedText}" target="_blank" class="scan-link">${decodedText}</a>`;
        } else {
            // If not a link, show plain text
            resultBox.innerText = decodedText;
        }
    }

    function onError(err) {
        // Normal scan errors; keep silent
    }

    Html5Qrcode.getCameras()
        .then(cameras => {
            if (cameras.length > 0) {
                const id = cameras[0].id;
                qrScanner.start(
                    id,
                    { fps: 10, qrbox: 250 },
                    onSuccess,
                    onError
                ).catch(err => {
                    console.error("Unable to start scanner:", err);
                    alert("Unable to start camera.");
                });
            } else {
                alert("No camera found.");
            }
        })
        .catch(err => {
            console.error("Camera error:", err);
            alert("Error accessing camera.");
        });
});

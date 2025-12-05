document.addEventListener("DOMContentLoaded", function () {

    // ==========================
    // QR SCANNER (index.html)
    // ==========================
    const qrDiv = document.getElementById("qr-reader");
    const resultBox = document.getElementById("scan-result");
    const statusTextEl = document.getElementById("scanner-status-text");
    const statusDotEl = document.querySelector(".status-dot");

    function setStatus(message, mode = "info") {
        if (statusTextEl) {
            statusTextEl.textContent = message;
        }
        if (statusDotEl) {
            statusDotEl.classList.remove("status-success", "status-error");
            if (mode === "success") {
                statusDotEl.classList.add("status-success");
            } else if (mode === "error") {
                statusDotEl.classList.add("status-error");
            }
        }
    }

    if (qrDiv) {
        console.log("Html5Qrcode is:", typeof Html5Qrcode);

        if (typeof Html5Qrcode === "undefined") {
            console.error("Html5Qrcode library NOT loaded.");
            alert("QR library failed to load. Check console for details.");
            setStatus("QR library failed to load.", "error");

        } else {
            setStatus("Initializing camera...");

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

                if (resultBox) {
                    if (isValidURL(decodedText)) {
                        resultBox.innerHTML =
                            `<a href="${decodedText}" target="_blank" class="scan-link">${decodedText}</a>`;
                    } else {
                        resultBox.innerText = decodedText;
                    }
                }

                setStatus("QR code detected!", "success");
                setTimeout(() => {
                    setStatus("Scanning... hold QR code steady.");
                }, 2000);
            }

            function onError(err) {
                // Ignore scan errors
            }

            Html5Qrcode.getCameras()
                .then(cameras => {
                    if (cameras.length > 0) {
                        const id = cameras[0].id;
                        setStatus("Scanning... hold QR code steady.");
                        qrScanner.start(
                            id,
                            { fps: 10, qrbox: 250 },
                            onSuccess,
                            onError
                        ).catch(err => {
                            console.error("Unable to start scanner:", err);
                            alert("Unable to start camera.");
                            setStatus("Unable to start camera.", "error");
                        });
                    } else {
                        alert("No camera found.");
                        setStatus("No camera found.", "error");
                    }
                })
                .catch(err => {
                    console.error("Camera error:", err);
                    alert("Error accessing camera.");
                    setStatus("Error accessing camera.", "error");
                });
        }
    }

    // ==========================
    // LOGIN / REGISTER TABS (login.html)
    // ==========================
    const tabs = document.querySelectorAll(".auth-tab");
    const forms = document.querySelectorAll(".auth-form");

    if (tabs.length > 0 && forms.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener("click", () => {
                const targetSelector = tab.getAttribute("data-target");
                const targetForm = document.querySelector(targetSelector);

                tabs.forEach(t => t.classList.remove("active"));
                tab.classList.add("active");

                forms.forEach(f => f.classList.add("auth-form-hidden"));
                if (targetForm) {
                    targetForm.classList.remove("auth-form-hidden");
                }
            });
        });
    }

    // ==========================
    // PASSWORD TOGGLE (eye icon)
    // ==========================
    const toggleButtons = document.querySelectorAll(".password-toggle-btn");

    toggleButtons.forEach(btn => {
        const targetId = btn.getAttribute("data-password-toggle");
        if (!targetId) return;

        const input = document.getElementById(targetId);
        if (!input) return;

        btn.addEventListener("click", () => {
            if (input.type === "password") {
                input.type = "text";
                btn.textContent = "🙈";
            } else {
                input.type = "password";
                btn.textContent = "👁";
            }
        });
    });

    // ==========================
    // ADMIN INLINE EDIT (admin.html)
    // ==========================
    const adminForm = document.querySelector(".admin-user-form form");

    if (adminForm) {
        const idInput = adminForm.querySelector("#admin-user-id");
        const emailInput = adminForm.querySelector("input[name='email']");
        const passwordInput = adminForm.querySelector("input[name='password']");
        const submitBtn = adminForm.querySelector("#admin-submit-btn");
        const titleEl = document.getElementById("admin-form-title");

        const editButtons = document.querySelectorAll(".edit-user-btn");

        editButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const id = btn.getAttribute("data-id");
                const email = btn.getAttribute("data-email");
                const password = btn.getAttribute("data-password");

                if (idInput) idInput.value = id || "";
                if (emailInput) emailInput.value = email || "";
                if (passwordInput) passwordInput.value = password || "";

                if (submitBtn) submitBtn.textContent = "UPDATE";
                if (titleEl) titleEl.textContent = "EDIT USER";
            });
        });
    }

    // ==========================
    // DELETE CONFIRMATION MODAL
    // ==========================
    const deleteModal = document.getElementById("delete-modal");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const modalConfirmBtn = document.getElementById("modal-confirm-btn");
    const deleteButtons = document.querySelectorAll(".delete-user-btn");

    let pendingDeleteUrl = null;

    if (deleteModal && modalCancelBtn && modalConfirmBtn && deleteButtons.length > 0) {

        deleteButtons.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault(); // Prevent immediate navigation

                pendingDeleteUrl = btn.getAttribute("data-delete-url") || btn.href;

                deleteModal.classList.add("show");
            });
        });

        modalCancelBtn.addEventListener("click", () => {
            deleteModal.classList.remove("show");
            pendingDeleteUrl = null;
        });

        modalConfirmBtn.addEventListener("click", () => {
            if (pendingDeleteUrl) {
                window.location.href = pendingDeleteUrl;
            }
        });

        // Clicking outside closes modal
        deleteModal.addEventListener("click", (e) => {
            if (e.target === deleteModal) {
                deleteModal.classList.remove("show");
                pendingDeleteUrl = null;
            }
        });

        // ESC key closes modal
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && deleteModal.classList.contains("show")) {
                deleteModal.classList.remove("show");
                pendingDeleteUrl = null;
            }
        });
    }

});

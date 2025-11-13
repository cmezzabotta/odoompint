function showQRModal(qrUrl) {
  const overlay = document.createElement("div");
  overlay.id = "qr-overlay";
  overlay.style.position = "fixed";
  overlay.style.top = "0";
  overlay.style.left = "0";
  overlay.style.width = "100vw";
  overlay.style.height = "100vh";
  overlay.style.backgroundColor = "rgba(0,0,0,0.8)";
  overlay.style.display = "flex";
  overlay.style.alignItems = "center";
  overlay.style.justifyContent = "center";
  overlay.style.zIndex = "9999";

  const modal = document.createElement("div");
  modal.style.backgroundColor = "#fff";
  modal.style.padding = "20px";
  modal.style.borderRadius = "12px";
  modal.style.boxShadow = "0 0 20px rgba(0,0,0,0.5)";
  modal.style.position = "relative";
  modal.style.textAlign = "center";
  modal.style.maxWidth = "320px";

  const closeBtn = document.createElement("button");
  closeBtn.textContent = "✕";
  closeBtn.style.position = "absolute";
  closeBtn.style.top = "8px";
  closeBtn.style.right = "8px";
  closeBtn.style.border = "none";
  closeBtn.style.background = "none";
  closeBtn.style.fontSize = "20px";
  closeBtn.style.cursor = "pointer";
  closeBtn.onclick = () => overlay.remove();

  const qrImg = document.createElement("img");
  qrImg.src = qrUrl;
  qrImg.alt = "Código QR";
  qrImg.style.width = "250px";
  qrImg.style.height = "250px";
  qrImg.style.objectFit = "contain";
  qrImg.style.marginTop = "20px";

  const title = document.createElement("h3");
  title.textContent = "Escaneá el QR para pagar";
  title.style.marginTop = "10px";

  modal.appendChild(closeBtn);
  modal.appendChild(title);
  modal.appendChild(qrImg);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
}

window.processPayment = async function (paymentData) {
  const token = "APP_USR-6724179307550211-101517-dea6eb093ed23ae0bc0db56c1cb3a634-442630041";
  const idempotencyKey = crypto.randomUUID();

  const body = {
    type: "qr",
    total_amount: paymentData.amount.toFixed(2),
    description: paymentData.items?.[0]?.name || "Compra",
    external_reference: "ext_ref_" + Math.floor(Math.random() * 999999),
    expiration_time: "PT16M",
    integration_data: { integrator_id: "dev_2970217120" },
    config: {
      qr: { external_pos_id: "POS001", mode: "static" }
    },
    transactions: {
      payments: [{ amount: paymentData.amount.toFixed(2) }]
    },
    items: paymentData.items.map(item => ({
      title: item.name,
      unit_price: item.unit.toFixed(2),
      quantity: item.qty,
      unit_measure: "unit",
      external_code: String(Math.floor(Math.random() * 999999999)),
      external_categories: [{ id: "device" }]
    }))
  };

  try {
    const response = await fetch("http://localhost:3000/crear-orden", {
      method: "POST",
      headers: {
        Accept: "*/*",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-Idempotency-Key": idempotencyKey
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error("Error MercadoPago:", errorData);
      return { ok: false, error: "Error HTTP " + response.status };
    }

    const result = await response.json();

    if (result && result.status === "created" && result.id) {
      const qrUrl = "https://www.mercadopago.com/instore/merchant/qr/120858202/def9c0c87f7349d29b789703af8c8416b5a9120a9a004ca49d181eff79b19c1e.png";
      showQRModal(qrUrl);
    }

    return { ok: true, receipt: result };
  } catch (err) {
    console.error("Error de conexión:", err);
    return { ok: false, error: err.message };
  }
};

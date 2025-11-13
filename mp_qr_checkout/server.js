const express = require("express");
const cors = require("cors");
const crypto = require("crypto");

const app = express();
app.use(express.json());
app.use(cors());

function generarIdempotencyKey() {
  return crypto.randomBytes(16).toString("hex");
}

app.post("/crear-orden", async (req, res) => {
  try {
    const respuesta = await fetch("https://api.mercadopago.com/v1/orders", {
      method: "POST",
      headers: {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": "Bearer APP_USR-6724179307550211-101517-dea6eb093ed23ae0bc0db56c1cb3a634-442630041",
        "X-Idempotency-Key": generarIdempotencyKey()
      },
      body: JSON.stringify(req.body)
    });

    const datos = await respuesta.json();
    res.json(datos);
  } catch (error) {
    console.error("Error al crear orden:", error);
    res.status(500).json({ error: "Error en el servidor" });
  }
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Servidor en http://localhost:${PORT}`));

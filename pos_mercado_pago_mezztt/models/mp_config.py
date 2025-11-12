"""Mercado Pago POS terminal credentials.

This file intentionally keeps the credentials hardcoded because every
physical cash register/terminal has a dedicated set of identifiers in the
Mercado Pago dashboard.  Replace the sample values below with the values
from the Mercado Pago "cajas" configuration before moving the module to
production.
"""

# Access credentials obtained from Mercado Pago for the POS collector.
MP_ACCESS_TOKEN = "APP_USR-xxxxxxxxxxxxxxxxxxxx"
MP_PUBLIC_KEY = "APP_USR-xxxxxxxxxxxxxxxxxxxx"

# Fixed identifiers for the physical cash register/terminal.
COLLECTOR_ID = "123456789"
POS_ID = "POS001"
TERMINAL_ID = "TERMINAL001"
STORE_ID = "STORE001"

# Optional secret used to validate Mercado Pago webhooks.  Leave empty if
# you are not using the feature.
WEBHOOK_SECRET = ""

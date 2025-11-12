# Configuración fija de credenciales para la caja
# ⚠️ Reemplazar por tus valores reales antes de usar

# Estos valores corresponden a la **caja/terminal física** que genera el QR
# dinámico. Mercado Pago los provee en la sección Instore > QR dinámicos del
# panel de desarrolladores. El módulo usará estos datos junto con el Access
# Token y Public Key configurados en Odoo (modelo `payment.provider`).

# Access Token y Public Key de fallback (se recomienda mantenerlos vacíos y
# configurarlos desde Odoo; sólo completar si se quiere forzar valores desde
# código).
MP_ACCESS_TOKEN = ""
MP_PUBLIC_KEY = ""

# Identificadores de la caja / sucursal
COLLECTOR_ID = "000000000"
POS_ID = "POS001"
EXTERNAL_POS_ID = "SUCURSAL1"
TERMINAL_ID = "TERMINAL001"

# URL opcional para notificaciones (webhook). Si se deja vacío se construirá en
# base a la URL pública del sistema Odoo + `/mp/mezztt/webhook`.
NOTIFICATION_URL = ""

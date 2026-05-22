🍽 Restaurante — Sistema de Administración
Sistema de escritorio para la gestión de mesas, pedidos, platos y facturación de un restaurante. Desarrollado en Python con PyQt6 y SQLite.

📸 Características

Tablero de mesas visual con estados en tiempo real (disponible, ocupada, reservada, mantenimiento)
Panel lateral animado para tomar pedidos directamente desde el tablero
Fusión de pedidos — si una mesa ya tiene un pedido activo, los nuevos platos se agregan al mismo
Gestión de platos con búsqueda, disponibilidad y precios
Seguimiento de pedidos con estados: abierto → en preparación → listo → cerrado
Facturación automática con generación de PDF al registrar el pago
Sistema de login con autenticación de usuarios
Interfaz oscura moderna inspirada en el tema Catppuccin Mocha


🗂 Estructura del proyecto
restaurante_app/
├── main.py
├── requirements.txt
├── assets/
│   └── logo.png
├── facturas/
├── backend/
│   ├── database/
│   │   ├── connection.py
│   │   └── schema.sql
│   ├── models/
│   │   ├── mesa.py
│   │   ├── plato.py
│   │   ├── pedido.py
│   │   ├── factura.py
│   │   └── usuario.py
│   └── repositories/
│       ├── mesa_repo.py
│       ├── plato_repo.py
│       ├── pedido_repo.py
│       ├── factura_repo.py
│       └── usuario_repo.py
└── frontend/
    ├── utils/
    │   └── helpers.py
    └── views/
        ├── main_window.py
        ├── login_view.py
        ├── mesas_view.py
        ├── platos_view.py
        ├── pedidos_view.py
        └── pago_view.py

⚙️ Requisitos

Python 3.10 o superior

Dependencias
PyQt6
reportlab

🚀 Instalación
1. Clona el repositorio
bashgit clone https://github.com/tu-usuario/restaurante_app.git
cd restaurante_app
2. Crea y activa el entorno virtual
bashpython -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
3. Instala las dependencias
bashpip install -r requirements.txt
4. Ejecuta la aplicación
bashpython main.py
La base de datos restaurante.db se crea automáticamente en backend/database/ al primer inicio.

📋 Requisitos funcionales
IDDescripciónREQ1Registrar mesa con número, capacidad y estado inicialREQ2Actualizar información y estado de mesasREQ3Consultar pedidos por fecha, mesa o estadoREQ4Crear pedidos asociados a una mesa con platos seleccionadosREQ5Modificar pedidos — agregar o quitar platos, cambiar estadoREQ6Registrar pago y generar factura PDFREQ7Crear y gestionar platos del menú

🛠 Tecnologías
CapaTecnologíaInterfaz gráficaPyQt6Base de datosSQLiteGeneración de PDFReportLabPatrón de diseñoMVC (Model - View - Repository)

👥 Equipo
Desarrollado por JEK Innovation

📄 Licencia
Este proyecto es de uso académico.

Copia esto, crea un archivo README.md en la raíz del proyecto y pégalo. En GitHub se verá formateado automáticamente. Solo cambia tu-usuario en la URL de git por tu usuario real de GitHub. 🚀

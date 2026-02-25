# KrystalOS
KrystalOS es un framework empresarial ultra-modular con estética Glassmorphism. Ofrece un tablero Bento Grid interactivo donde cada widget es un micro-frontend con base de datos propia y comunicación en tiempo real. Incluye Krystal-CLI para automatización, búsqueda semántica con OCR, firmas digitales y accesibilidad personalizable.

// KrystalOS: The Bento-Engine Framework
KrystalOS es un framework de grado empresarial diseñado para centralizar, automatizar y escalar la gestión de procesos de negocio mediante una arquitectura ultra-modular de widgets dinámicos. Inspirado en la estética Glassmorphism de iOS y la flexibilidad de los sistemas operativos modernos, KrystalOS permite a las organizaciones construir un "Sistema Operativo" privado y totalmente personalizado.

// La Visión
A diferencia de los ERPs tradicionales rígidos, KrystalOS ofrece un lienzo vivo (Bento Grid) donde cada funcionalidad es un módulo independiente ("Widget") que se descubre, instala y comunica automáticamente. El objetivo es eliminar la fricción técnica, permitiendo que el software se adapte a la empresa, y no al revés.

//  Características Principales
Arquitectura Plug-and-Play: Sistema de Autodiscovery donde cada carpeta de widget se integra automáticamente al núcleo sin configuración manual de rutas.

// Bento-Grid Dashboard: Interfaz interactiva y persistente con soporte para Drag-and-Drop y redimensionamiento dinámico estilo Canva.

// Estética Krystal: Interfaz de usuario de alta fidelidad basada en Glassmorphism y Neumorphism, con soporte nativo para temas (Light, Dark, Custom) y modo PWA.

// Seguridad de Grado Bancario: Multi-tenancy con aislamiento de base de datos, firmas digitales integradas (PNG overlay) y control de acceso basado en roles (RBAC).

// Inteligencia Operativa: Motor de OCR nativo y búsqueda semántica (RAG) que permite "preguntar" al sistema por información contenida en documentos escaneados.

// Krystal-CLI: Herramienta de línea de comandos potente para la generación de código, gestión de migraciones y despliegue automatizado con Docker.

// Stack Tecnológico
Backend: Python 3.x (FastAPI) + WebSockets.

Database: PostgreSQL (SQLModel) + pgvector.

Frontend: Vanilla JS / TailwindCSS (Offline-first) + CSS Variables.

Infrastructure: Docker & Docker Compose.

Integrations: EasyOCR / Tesseract + ReportLab (Digital Signatures).

// Accesibilidad y Personalización
KrystalOS incluye un Centro de Accesibilidad configurable, permitiendo a cada usuario activar modos de alto contraste, lectura para ciegos, reducción de movimiento y tipografías para dislexia, garantizando que el sistema sea inclusivo para todos.

// Widgets

Los widgets en KrystalOS son unidades de software independientes y autónomas. Funcionan bajo un principio de desacoplamiento total: cada widget posee su propia lógica de negocio, esquema de datos y archivos de interfaz, lo que permite desarrollarlos, probarlos o eliminarlos sin afectar la integridad del núcleo del sistema o de otros módulos.

Funcionamiento de los widgets
El framework utiliza un motor de autodescubrimiento. Al iniciar el servidor, KrystalOS escanea el directorio de widgets y registra automáticamente las rutas de API y los modelos de base de datos encontrados. La comunicación entre ellos se realiza a través de un Bus de Eventos basado en WebSockets, permitiendo que un widget reaccione a cambios en otro sin estar vinculados directamente en el código.

Organización de carpetas y archivos obligatorios
Cada widget debe residir en su propia carpeta dentro del directorio raíz de widgets. La estructura interna obligatoria es la siguiente:

config.json: Contiene los metadatos del widget. Define el nombre técnico, el icono para el menú, los permisos necesarios para ejecutarlo y las dimensiones iniciales (ancho y alto) que ocupará en el bento-grid.

models.py: Define la estructura de la tabla en PostgreSQL utilizando SQLModel o SQLAlchemy. El framework detecta este archivo para ejecutar las migraciones automáticas.

routes.py: Contiene los endpoints de FastAPI específicos del widget. No es necesario registrar estas rutas en un archivo central; el orquestador las monta bajo el prefijo del nombre del widget.

ui.html: El fragmento de interfaz de usuario. Debe seguir las clases CSS de KrystalOS para mantener la estética de cristal y neumorfismo.

script.js: Lógica del lado del cliente. Gestiona la interactividad y la escucha de eventos en tiempo real.

Proceso de creación simplificado
Para crear un widget sin manipular manualmente el framework, se utiliza el Krystal-CLI. El flujo estándar es:

Ejecutar el comando de generación para crear la estructura de carpetas base.

Definir los campos de datos en el archivo de modelos.

Escribir la lógica de la API en el archivo de rutas.

Diseñar la vista en el archivo HTML utilizando los componentes predefinidos del sistema.

Una vez creada la carpeta con estos archivos, el sistema la integra automáticamente en el tablero principal la próxima vez que se inicie el servidor o se actualice el despliegue de Docker.

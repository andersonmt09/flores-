# Jardín en 3D

Un pequeño jardín nocturno en 3D, creado con Three.js.

![Estado](https://img.shields.io/badge/experiencia-interactiva-ffd45a?style=flat-square)

## Abrir el proyecto

Abre `index.html` en un navegador moderno con conexión a Internet. La escena carga Three.js desde CDN.

- **Mirar:** arrastra con el dedo o el ratón; pellizca o usa la rueda para acercarte.
- **Caminar:** en computador usa W A S D o las flechas (Shift para ir más rápido); en el celular, el círculo de abajo a la izquierda.
- **Pausa:** el botón de abajo a la derecha detiene el viento y las luciérnagas.

## Detalles

- Jardín nocturno grande: macizo central de tulipanes, seis parterres de tulipanes y lirios araña con seto, dos anillos de paseo, avenidas en cruz, campos de tulipanes en franjas de colores y praderas de lirios araña.
- Faroles victorianos encendidos a lo largo de los senderos, luna llena con el mapa real de su superficie, bosque de siluetas alrededor, cielo real de una noche de enero en Colombia: 6.300 estrellas del catálogo de Yale en su posición, magnitud y color reales, y la Vía Láctea en su lugar; luna gibosa con relieve. Pocas polillas y libélulas vuelan de flor en flor por todo el jardín y se posan en ellas; luciérnagas entre las flores. En PC con gráficos integrados se usa el modo liviano y la resolución se limita en pantallas grandes.
- Luciérnagas, césped y flores que se mecen con el viento.
- Reproductor: 127 canciones de Penyair, cada una con su audio. Los títulos se leen de la API oEmbed de YouTube (`/api/oembed/{id}` en el servidor, con respaldo directo desde el navegador) y se guardan en el teléfono. Recuerda la última canción, barra arrastrable, búsqueda sin tildes, mantener presionado ⏮/⏭ para retroceder o adelantar, y acceso rápido desde el jardín.
- Rendimiento: el cielo, el dibujo del suelo y la luz de los faroles se precalculan una sola vez; las flores lejanas usan versiones simplificadas y las del centro se dibujan en pocas piezas. En celulares no hay sombras ni luces en tiempo real, y la resolución se ajusta sola según los FPS para que no se trabe en ningún teléfono.
- Respeta `prefers-reduced-motion`.

---

Hecho con un poquito de luz para alguien especial. 🌼

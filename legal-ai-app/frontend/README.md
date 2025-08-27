# Frontend - Legal AI Application

## Descripción

Este es el frontend de la aplicación Legal AI, una interfaz web moderna y responsiva que permite a los usuarios interactuar con todas las funcionalidades del backend de IA legal.

## Características

- **Diseño Responsivo**: Funciona perfectamente en dispositivos móviles y de escritorio
- **Interfaz Moderna**: Utiliza CSS moderno con variables CSS y diseño basado en componentes
- **Navegación Intuitiva**: Menú de navegación fijo con acceso rápido a todas las funcionalidades
- **Autenticación Completa**: Sistema de login/registro con JWT
- **Gestión de Estado**: Manejo de estado de usuario y sesiones
- **Notificaciones**: Sistema de toast notifications para feedback del usuario
- **Loading States**: Indicadores de carga para operaciones asíncronas

## Estructura de Archivos

```
frontend/
├── index.html          # Página principal de la aplicación
├── styles.css          # Estilos CSS con variables y diseño responsivo
├── script.js           # Lógica JavaScript de la aplicación
└── README.md           # Este archivo
```

## Funcionalidades Implementadas

### 1. Análisis Predictivo de Sentencias
- Formulario para ingresar texto del caso
- Selección de tribunal y materia
- Visualización de resultados con predicción y confianza
- Lista de jurisprudencia similar
- Explicación del resultado (XAI)

### 2. Buscador de Jurisprudencia
- Búsqueda por texto libre
- Filtros por tribunal, materia y fechas
- Resultados con ranking de relevancia
- Vista previa del contenido de las sentencias

### 3. Generador de Documentos Legales
- Selección del tipo de documento
- Ingreso de detalles del caso
- Subida opcional de documento base
- Generación automática con IA
- Vista previa y opciones de descarga

### 4. Gestión de Casos
- Creación de nuevos casos
- Visualización de casos existentes
- Estados y prioridades configurables
- Acciones de edición y visualización

### 5. Sistema de Autenticación
- Registro de usuarios
- Login con JWT
- Gestión de perfil de usuario
- Protección de rutas

## Tecnologías Utilizadas

- **HTML5**: Estructura semántica y accesible
- **CSS3**: Variables CSS, Grid, Flexbox, animaciones
- **JavaScript ES6+**: Clases, async/await, módulos
- **Font Awesome**: Iconos vectoriales
- **Google Fonts**: Tipografía Inter para mejor legibilidad

## Configuración

### 1. URL del Backend
Por defecto, el frontend está configurado para conectarse a `http://localhost:8000`. Para cambiar esto:

1. Abre `script.js`
2. Modifica la línea:
   ```javascript
   this.apiBaseUrl = 'http://localhost:8000'; // Cambia esta URL
   ```

### 2. Variables de Entorno
Para producción, asegúrate de configurar:
- `API_BASE_URL`: URL del backend en producción
- `ENABLE_HTTPS`: Si tu backend requiere HTTPS

## Uso

### 1. Desarrollo Local
1. Coloca los archivos en tu servidor web local
2. Asegúrate de que el backend esté corriendo en `http://localhost:8000`
3. Abre `index.html` en tu navegador

### 2. Producción
1. Sube los archivos a tu servidor web
2. Configura la URL del backend en `script.js`
3. Asegúrate de que CORS esté configurado correctamente en el backend

### 3. Integración con Backend
El frontend se comunica con el backend a través de:
- **REST API**: Para operaciones CRUD
- **JWT**: Para autenticación
- **FormData**: Para subida de archivos

## Personalización

### 1. Colores y Temas
Los colores se definen en variables CSS en `styles.css`:
```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --accent-color: #f59e0b;
    /* ... más variables */
}
```

### 2. Tipografía
La fuente principal es Inter de Google Fonts. Para cambiarla:
1. Modifica el import en `index.html`
2. Actualiza `font-family` en `styles.css`

### 3. Iconos
Los iconos usan Font Awesome. Para agregar nuevos:
```html
<i class="fas fa-nombre-del-icono"></i>
```

## Responsive Design

El frontend está optimizado para:
- **Desktop**: 1200px+ (navegación horizontal, grid de 2 columnas)
- **Tablet**: 768px-1199px (navegación colapsable, grid adaptativo)
- **Mobile**: <768px (navegación hamburguesa, layout de 1 columna)

## Accesibilidad

- Navegación por teclado
- Etiquetas ARIA apropiadas
- Contraste de colores adecuado
- Texto alternativo para iconos
- Estructura semántica HTML

## Compatibilidad de Navegadores

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+
- Mobile Safari y Chrome

## Troubleshooting

### 1. CORS Errors
Si ves errores de CORS:
- Verifica que el backend tenga CORS configurado
- Asegúrate de que la URL del backend sea correcta

### 2. API Errors
Si las llamadas a la API fallan:
- Verifica que el backend esté corriendo
- Revisa la consola del navegador para errores
- Verifica que el token JWT sea válido

### 3. Estilos No Aplicados
Si los estilos no se cargan:
- Verifica que `styles.css` esté en la misma carpeta
- Revisa la consola del navegador para errores 404

## Próximas Mejoras

- [ ] Modo oscuro/claro
- [ ] Internacionalización (i18n)
- [ ] PWA (Progressive Web App)
- [ ] Offline support
- [ ] Notificaciones push
- [ ] Dashboard avanzado
- [ ] Exportación de datos
- [ ] Integración con calendario

## Contribución

Para contribuir al frontend:
1. Mantén el código limpio y bien documentado
2. Usa las variables CSS existentes
3. Sigue las convenciones de nomenclatura
4. Prueba en diferentes dispositivos y navegadores

## Licencia

Este frontend es parte del proyecto Legal AI y está sujeto a la misma licencia.
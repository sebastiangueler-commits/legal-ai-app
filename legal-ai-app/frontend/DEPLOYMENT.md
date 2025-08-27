# 🚀 Guía de Despliegue del Frontend

## Opciones de Despliegue

### 1. Despliegue Estático (Recomendado)

#### Netlify
1. Conecta tu repositorio GitHub
2. Configura el directorio de build: `frontend/`
3. Build command: (dejar vacío - no es necesario)
4. Publish directory: `frontend/`
5. Variables de entorno:
   ```
   API_BASE_URL=https://tu-backend.onrender.com
   ```

#### Vercel
1. Conecta tu repositorio GitHub
2. Configura el directorio raíz: `frontend/`
3. Framework preset: Other
4. Build command: (dejar vacío)
5. Output directory: `.`
6. Variables de entorno:
   ```
   API_BASE_URL=https://tu-backend.onrender.com
   ```

#### GitHub Pages
1. Ve a Settings > Pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: `/frontend`
5. Actualiza `script.js` con la URL de producción

### 2. Despliegue en Servidor Web

#### Apache
```apache
# .htaccess
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.html [QSA,L]

# Configurar CORS si es necesario
Header always set Access-Control-Allow-Origin "*"
Header always set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
Header always set Access-Control-Allow-Headers "Content-Type, Authorization"
```

#### Nginx
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    root /var/www/legal-ai-app/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Configurar CORS
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}
```

### 3. Despliegue en CDN

#### Cloudflare Pages
1. Conecta tu repositorio GitHub
2. Framework preset: None
3. Build command: (dejar vacío)
4. Build output directory: `frontend`
5. Variables de entorno:
   ```
   API_BASE_URL=https://tu-backend.onrender.com
   ```

## Configuración para Producción

### 1. Actualizar URL del Backend

En `script.js`, cambia:
```javascript
this.apiBaseUrl = 'http://localhost:8000'; // Cambiar por:
this.apiBaseUrl = 'https://tu-backend.onrender.com';
```

### 2. Configurar CORS en el Backend

Asegúrate de que tu backend permita requests desde tu dominio:
```python
# En main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tu-dominio.com",
        "https://www.tu-dominio.com",
        "http://localhost:3000"  # Para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Variables de Entorno

Crea un archivo `.env.production` en el frontend:
```env
API_BASE_URL=https://tu-backend.onrender.com
ENABLE_HTTPS=true
ENVIRONMENT=production
```

## Optimizaciones para Producción

### 1. Minificación (Opcional)

#### Usando Node.js
```bash
# Instalar herramientas
npm install -g uglify-js clean-css-cli html-minifier

# Minificar JavaScript
uglifyjs script.js -o script.min.js

# Minificar CSS
cleancss -o styles.min.css styles.css

# Minificar HTML
html-minifier --collapse-whitespace --remove-comments index.html -o index.min.html
```

#### Usando herramientas online
- **JavaScript**: [JSCompress](https://jscompress.com/)
- **CSS**: [CSS Minifier](https://cssminifier.com/)
- **HTML**: [HTML Minifier](https://www.minifier.org/)

### 2. Compresión Gzip

#### Apache (.htaccess)
```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>
```

#### Nginx
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

### 3. Cache Headers

#### Apache (.htaccess)
```apache
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/ico "access plus 1 year"
    ExpiresByType image/icon "access plus 1 year"
    ExpiresByType text/plain "access plus 1 month"
    ExpiresByType application/pdf "access plus 1 month"
    ExpiresByType text/html "access plus 1 hour"
</IfModule>
```

#### Nginx
```nginx
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location ~* \.(html)$ {
    expires 1h;
    add_header Cache-Control "public, must-revalidate";
}
```

## Monitoreo y Mantenimiento

### 1. Health Checks

Verifica que tu frontend esté funcionando:
```bash
# Verificar que index.html se sirve correctamente
curl -I https://tu-dominio.com

# Verificar que los assets se cargan
curl -I https://tu-dominio.com/styles.css
curl -I https://tu-dominio.com/script.js
```

### 2. Logs y Analytics

- **Google Analytics**: Para métricas de usuarios
- **Console del navegador**: Para errores JavaScript
- **Network tab**: Para verificar llamadas a la API

### 3. Actualizaciones

Para actualizar el frontend:
1. Haz push a tu repositorio GitHub
2. Tu plataforma de despliegue se actualizará automáticamente
3. Verifica que la nueva versión esté funcionando

## Troubleshooting

### 1. CORS Errors
```
Access to fetch at 'https://tu-backend.com' from origin 'https://tu-frontend.com' has been blocked by CORS policy
```
**Solución**: Configurar CORS en el backend para permitir tu dominio.

### 2. 404 Errors
```
Failed to load resource: the server responded with a status of 404
```
**Solución**: Verificar que todos los archivos estén en el directorio correcto.

### 3. API Connection Errors
```
Failed to fetch
```
**Solución**: Verificar que la URL del backend sea correcta y esté funcionando.

### 4. Styling Issues
Los estilos no se aplican correctamente.
**Solución**: Verificar que `styles.css` esté en la misma carpeta que `index.html`.

## Seguridad

### 1. HTTPS
- Usa siempre HTTPS en producción
- Configura HSTS headers
- Redirige HTTP a HTTPS

### 2. Headers de Seguridad
```apache
# .htaccess
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
```

### 3. Content Security Policy
```html
<!-- En index.html -->
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;">
```

## Recursos Adicionales

- [MDN Web Docs - CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Web.dev - Performance](https://web.dev/performance/)
- [Security Headers](https://securityheaders.com/)
- [Google PageSpeed Insights](https://pagespeed.web.dev/)

---

**¡Tu frontend está listo para producción! 🚀**
# Product Microservice

## Descripción

Microservicio encargado de la gestión de productos. Proporciona endpoints para obtener, crear, actualizar y eliminar productos del catálogo.

## Tecnología

- **Framework**: Flask (Python)
- **Base de datos**: Supabase
- **CORS**: Habilitado para comunicación entre servicios

## Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

## Instalación Local

1. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**
   
   Crear archivo `.env` con las siguientes variables:
   ```
   SUPABASE_URL=tu_supabase_url
   SUPABASE_KEY=tu_supabase_key
   ```

3. **Ejecutar el servicio**
   ```bash
   python app.py
   ```

   El servicio se ejecutará en `http://localhost:5000`

## Endpoints Principales

- `GET /health` - Verificar estado del servicio
- `GET /allproducts` - Obtener todos los productos
- `POST /add` - Crear un nuevo producto
- Consulta `app.py` para ver todos los endpoints disponibles

## Docker

Para ejecutar en contenedor:
```bash
docker build -t product-service .
docker run -p 5000:5000 --env-file .env product-service
```

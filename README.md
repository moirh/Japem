# 🚀 Proyecto JAPEM

Sistema de la **Junta de Asistencia Privada del Estado de México** para la gestión de donantes, donativos, inventario, instituciones (IAPs), distribución y entregas.

Desarrollado en **Django 5.2** con **HTMX**, **Alpine.js** y **Tailwind CSS** (por CDN, sin compilar nada con npm).
A continuación se listan los pasos básicos para instalarlo y ponerlo en marcha en tu entorno local.

---

## 📋 Requisitos previos

- Python >= 3.10 (recomendado 3.13)
- pip
- MySQL 8 (o acceso a la base de datos del proyecto)
- Cliente de MySQL para compilar `mysqlclient`
  - **macOS:** `brew install mysql-client pkg-config`
  - **Ubuntu/Debian:** `sudo apt install pkg-config default-libmysqlclient-dev build-essential`
- Git

---

## ⚙️ Instalación

```bash
git clone git@github.com:moirh/Japem.git
cd Japem
python3 -m venv .venv
source .venv/bin/activate
```

> **Solo en macOS**, antes de instalar las dependencias:
> ```bash
> export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"
> ```

```bash
pip install -r requirements.txt
cp .env.example .env
```

Genera una `SECRET_KEY` y pégala en tu `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Configura la conexión a la base de datos en el `.env`:

```env
DB_CONNECTION=mysql
DB_HOST=tu-servidor-mysql
DB_PORT=3306
DB_DATABASE=nombre_de_la_base
DB_USERNAME=tu_usuario
DB_PASSWORD="tu_contraseña"
```

> Para desarrollo rápido sin MySQL puedes usar `DB_CONNECTION=sqlite`.

---

## 🗄️ Base de datos

**Base de datos nueva** (local o de pruebas):

```bash
python manage.py migrate
```

👉 Esto crea todas las tablas desde cero.

**Base de datos existente** (la que ya usaba el sistema original en Laravel):

```bash
python manage.py migrate --fake-initial
```

👉 Respeta las tablas y los datos que ya existen y solo crea las que faltan.

> ⚠️ Nunca corras `flush` ni borres migraciones sobre la base de producción.

---

## 👥 Usuarios

**Crear un superusuario:**

```bash
python manage.py createsuperuser
```

**Importar los usuarios del sistema original (Laravel)**, con su mismo id y contraseña:

```bash
python manage.py importar_usuarios_laravel            # solo muestra lo que haría
python manage.py importar_usuarios_laravel --aplicar  # guarda los cambios
```

Roles disponibles: `superadmin`, `admin`, `donativos`, `asistencial`, `editor` y `lector`.

---

## 🚀 Servidor local

Levanta el servidor local con:

```bash
python manage.py runserver
```

El proyecto estará disponible en:

👉 http://127.0.0.1:8000

---

## 📦 Archivos estáticos (producción)

No se necesita `npm`: Tailwind, HTMX, Alpine.js y SweetAlert2 se cargan por CDN.

Para producción, junta los archivos estáticos con:

```bash
python manage.py collectstatic
```

---

## 🧩 Módulos

| Módulo | Qué hace |
|---|---|
| **Inicio** | Resumen, Mis Acuerdos, Mis Recordatorios, calendario y Avisos de la Semana |
| **Donantes** | Directorio de donantes, alta/edición e importación por CSV |
| **Entradas** | Registro de donativos con sus productos y precios |
| **Instituciones** | Padrón de IAPs con su ficha técnica e importación por CSV |
| **Distribución** | Sugerencia de IAPs por producto y asignación |
| **Entrega** | Mesa de control de entregas y Vale de Salida en PDF |
| **Inventario** | Stock disponible, semáforo de rotación y caducidad |
| **Configuración** | Perfil y administración de usuarios por rol |

---

## 📚 Documentación técnica

Las decisiones de la migración desde Laravel + React están en
[`docs/MIGRACION.md`](docs/MIGRACION.md).

---

## ✅ Listo

Ya deberías poder usar la aplicación 🚀

Inicia sesión con el superusuario que creaste o con tu usuario del sistema original (misma contraseña).

> 🔒 Nunca subas tu `.env`, respaldos `.sql` ni bases `.sqlite3` al repositorio: ya están en el `.gitignore`.
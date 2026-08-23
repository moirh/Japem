# JAPEM — Backend + Frontend en Python

Reescritura del sistema JAPEM (originalmente Laravel 12 + React/TypeScript) a
**Django**, con vistas server-rendered (Django templates + HTMX + Alpine.js)
en lugar de una SPA separada. Sin build de JavaScript: HTMX/Alpine/Tailwind
se cargan por CDN.

Progreso hasta ahora:

- **Fase 1**: esqueleto del proyecto, autenticación por sesión, y los
  módulos Donantes e Inventario (resumen de stock).
- **Fase 2**: módulo Donativos completo — alta transaccional con productos
  dinámicos, listado, detalle con edición de precios de venta y
  devolución/merma por lote.
- **Fase 3**: módulo Distribución/Entregas — algoritmo de sugerencia de IAPs
  por producto, asignación (sin tocar stock), y mesa de control que confirma
  la entrega física (descuenta `cantidad_actual`, marca la IAP como
  beneficiada). Incluye un modelo `Iap` mínimo (sin CRUD dedicado todavía)
  porque `Asignacion` depende de él.
- **Fase 4**: módulo IAPs completo — CRUD (alta, edición, baja, ficha de
  detalle) con los campos de selección múltiple (clasificación, actividades)
  y de población (fijos/temporales/flotantes) del formulario original, más
  importación masiva por CSV.
- **Fase 5**: Acuerdos, Recordatorios y el panel de inicio real (antes un
  placeholder) — widgets de resumen, calendario mensual interactivo,
  acuerdos compartibles entre usuarios, recordatorios personales, y la
  auto-limpieza de vencidos que tenía el backend original. Esta fase
  reemplaza también la pantalla `home.html` de las Fases 1-4 (que solo
  tenía accesos directos a los módulos) por el dashboard real de Home.tsx +
  DashboardController.
- **Fase 6**: Usuarios y Perfil — cada quien edita su nombre/email y cambia
  su contraseña; el directorio de usuarios (crear/editar/eliminar) queda
  restringido por rol igual que `SettingsModal.tsx`: solo admin/superadmin
  lo ven, y solo superadmin crea o elimina cuentas.
- **Fase 7**: Permisos por rol dentro de cada módulo — Donantes, Donativos y
  Distribución/Entregas quedan de solo lectura para quien no sea
  admin/superadmin/editor/donativos; IAPs queda de solo lectura para quien
  no sea admin/superadmin/editor/asistencial. Igual que el frontend
  original, pero reforzado también del lado del servidor (ver más abajo).

Con esto ya están migrados **todos** los módulos "de negocio" del sistema
original, con los mismos permisos por rol que tenía el frontend React. Lo
que queda pendiente es una suite de tests automatizados y decidir la
estrategia de migración de datos — ver "Próximas fases" al final.

## Requisitos

- Python 3.11+
- PostgreSQL (mismo motor que usaba el backend Laravel) — o SQLite para
  desarrollo rápido sin levantar Postgres.

## Instalación

```bash
cd Japem-Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con tus credenciales de Postgres, o pon `DB_CONNECTION=sqlite`
para usar un archivo `db.sqlite3` local sin configurar nada más.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La aplicación estará disponible en http://127.0.0.1:8000. El panel de
administración de Django (`/admin/`) permite gestionar usuarios, catálogo de
productos, donativos e inventario mientras se completan las pantallas
dedicadas de esos módulos.

## Estructura

```
japem/          Configuración del proyecto (settings, urls raíz, vista home/dashboard)
accounts/       Usuario custom (username + role), login/logout por sesión,
                perfil propio, y CRUD de usuarios restringido por rol
agenda/         Acuerdo (compartible), Recordatorio (personal), auto-limpieza
                de vencidos; alimentan los widgets y el calendario del home
donantes/       Modelo Donante + CRUD completo (HTMX)
donativos/      Donativo, Inventario, CatalogoProducto: alta transaccional,
                listado, detalle, precios de venta, devoluciones y stock
iaps/           Iap: CRUD completo (selección múltiple, población,
                validaciones, importación CSV) + admin
distribucion/   Asignacion, DetalleAsignacion: algoritmo de sugerencia,
                pantalla de asignación y mesa de control de entregas
templates/      Templates Django (base.html con el layout/paleta JAPEM)
static/         CSS propio (Tailwind se sirve por CDN)
```

## Decisiones de la migración

- **Auth**: Laravel usaba Sanctum (tokens Bearer) porque el frontend era una
  SPA en otro origen. Al pasar todo a Django con vistas server-rendered, se
  usa autenticación por **sesión** (`django.contrib.auth`), más simple y
  segura para este caso (no hay CORS ni tokens que gestionar en el cliente).
- **Roles**: el campo `role` del modelo `User` tiene los 6 valores que de
  verdad valida `SettingsController` (`superadmin`, `admin`, `donativos`,
  `asistencial`, `editor`, `lector`) — en la Fase 1 solo se habían migrado 4
  porque `User.php`/`AuthController` no los mencionan; salieron a la luz al
  revisar `SettingsController@createUser` en esta fase. Los permisos por
  rol dentro de cada módulo (Donantes/Donativos/IAPs/Distribución
  distinguían roles de solo-lectura en el frontend original) siguen
  pendientes — ver "Próximas fases". La Fase 6 sí aplica el control de
  acceso propio de Usuarios/Settings (ver más abajo), que no puede esperar
  porque es parte del propio módulo.
- **Nombres de tabla**: los modelos usan `db_table` para conservar los
  nombres de tabla de Laravel (`donantes`, `donativos`, `inventarios`,
  `catalogo_productos`), por si se necesita migrar datos existentes más
  adelante con un script de ETL.
- **Mutadores**: el modelo `Donante` reproduce el `save()` de Eloquent que
  guardaba `razon_social`, `rfc`, `direccion` y `contacto` en mayúsculas.
- **Inventario**: la vista de stock replica la consulta agrupada de
  `InventarioController@index` (suma de `cantidad_actual` y monto deducible
  por producto, filtrando los que ya no tienen stock) usando el ORM de
  Django (`values().annotate()` = `GROUP BY`, `.filter()` posterior = `HAVING`).
- **Alta de donativos**: `donativos.views._guardar_donativo` reproduce
  `DonativoController@store` — crea el `Donativo`, y por cada renglón
  hace `get_or_create` del `CatalogoProducto` (equivalente a `firstOrCreate`,
  no actualiza categoría/unidad si el producto ya existía) y crea el
  `Inventario` con `cantidad_actual = cantidad` inicial, todo dentro de una
  transacción atómica.
- **Filas dinámicas del formulario**: en vez de una lógica React con
  `useState`, se usa un `formset_factory` de Django (`DetalleFormSet`) con
  un patrón estándar de "clonar formulario vacío + reindexar" en ~40 líneas
  de JS plano (sin librería de formularios en el cliente). Probado en
  navegador real con Playwright: agregar filas, quitar filas intermedias y
  que los índices de los campos se reacomoden correctamente.
- **Autocompletado de producto**: el frontend original alternaba entre un
  `<select>` de productos existentes y un input libre. Se simplificó a un
  único input de texto con `<datalist>` (autocompletado nativo del
  navegador) que rellena clave SAT/categoría/unidad al elegir un producto
  ya catalogado — mismo resultado, sin JS de más.
- **Precios de venta y devoluciones**: la pantalla de detalle de un donativo
  reproduce `InventarioController@updatePrices` (edición masiva de precio de
  venta por renglón) y agrega la merma/devolución que en el frontend usaba
  un modal de SweetAlert, aquí con un input de cantidad + confirmación nativa
  del navegador junto a cada renglón.
- **Simplificación pendiente**: el campo "Caducidad" en el formulario de
  alta no se marca como obligatorio dinámicamente según la categoría
  (`needsExpiration` en el frontend original); queda siempre opcional. Se
  puede endurecer en una iteración posterior si se necesita.
- **Algoritmo de sugerencias**: `distribucion.services.sugerir_iaps` es un
  puerto directo de `EntregaController@sugerirAsignacion` (misma matriz de
  reglas por palabra clave, mismas excepciones dinámicas para pañales/ropa,
  mismo sistema de puntaje). Se conserva el criterio original de filtrar
  candidatas por `estatus == "Activa"`.
- **Nota sobre `Activo`/`Activa` (revisada en la Fase 4, ya no es un problema
  real)**: la migración de `iaps` en Laravel pone `"Activo"` como default de
  `estatus` a nivel de columna, pero tanto el `<select>` del formulario de
  alta (`initialForm.estatus = "Activa"`) como el import CSV
  (`$row[1] ?? 'Activa'`) siempre mandan `"Activa"` explícitamente — ninguna
  IAP creada a través de la aplicación termina con `"Activo"` en la
  práctica, así que el algoritmo de sugerencias (que filtra por
  `estatus == "Activa"`) sí las encuentra. El modelo Django usa `"Activa"`
  como default (el valor que la app realmente escribe) en vez de replicar el
  default inerte de la migración; el `<select>` de estatus del formulario de
  IAPs ofrece Activa/Inactiva/Suspendida/En Proceso, igual que el original.
- **Nivel de trabajo: lote en vez de producto agregado**: el frontend
  original operaba la pantalla de Distribución sobre el *resumen* de
  inventario agrupado por producto (mismo endpoint que la pantalla de
  Inventario), cuyo `id` es en realidad el id del `CatalogoProducto` (o un
  id sintético negativo si el lote no tiene catálogo asociado). Pero
  `EntregaController@sugerirAsignacion($inventarioId)` busca ese id
  directamente en la tabla `inventarios` (`Inventario::find`) — es decir,
  trata un id de catálogo como si fuera el id de un lote específico, que
  solo coinciden por casualidad. Para no heredar esa ambigüedad, la pantalla
  de Distribución en Django lista **lotes individuales** (filas reales de
  `Inventario` con `cantidad_actual > 0`, agrupados visualmente por
  categoría), y tanto la sugerencia como la asignación operan sobre el id
  real del lote. Es el nivel al que de todos modos apunta
  `DetalleAsignacion.inventario_id` y al que se le descuenta stock, así que
  el resultado es más correcto que el original, no solo distinto.
- **Columnas muertas omitidas**: `detalle_asignaciones` tiene columnas
  `iap_id` y `producto_nombre` (de una migración posterior) que ningún
  controlador activo lee ni escribe — se omitieron en el modelo Django. Las
  tablas `entregas` / `detalle_entregas` (con sus modelos `Entrega` /
  `DetalleEntrega`) tampoco se migraron: no están referenciadas por ninguna
  ruta en `routes/api.php`, todo el flujo activo de entregas usa
  `asignaciones` / `detalle_asignaciones`.
- **Campos de selección múltiple como texto separado por `|`**: `clasificacion`
  y `actividad_asistencial` no son relaciones normalizadas ni en Laravel ni
  en el frontend original — son un solo `CharField`/`TextField` que guarda
  varios valores unidos por `|` (constante `SEPARATOR` en `IapTable.tsx`).
  Se replicó tal cual con un `PipeMultipleChoiceField` a la medida
  (`iaps/forms.py`): un `MultipleChoiceField` de Django que al leer separa
  el string guardado en la lista de checkboxes marcados, y al guardar vuelve
  a unir la selección con `|`. Se optó por conservar el formato de datos
  original en vez de normalizarlo a una tabla de relación, para no complicar
  una eventual migración de datos desde la base actual.
- **Población (fijos/temporales/flotantes)**: igual que el formulario React,
  `personas_beneficiadas` y `tipo_beneficiario` no se editan directamente:
  se derivan de tres campos auxiliares del formulario (`cantidad_fijos`,
  `cantidad_temporales`, `cantidad_flotantes`) que `IapForm.save()` combina
  en un string tipo `"Fijos: 15|Temporales: 3"` y su suma. Al editar, esos
  tres campos se reconstruyen parseando el string guardado con la misma
  expresión regular que usaba `parsePoblacion` en el frontend.
- **`IapController@sugerirIaps` no se migró (código muerto)**: el frontend
  define `getSugerenciasMatch` (que llamaría a `GET /iaps/sugerencias`) pero
  ningún componente lo importa ni lo usa — las sugerencias reales que sí se
  usan en pantalla vienen de `EntregaController@sugerirAsignacion`, ya
  migrado en la Fase 3. Se dejó fuera junto con las demás rutas sin
  consumidor activo.
- **Acuerdos vs. Recordatorios**: se replicó la diferencia real del backend
  original — un `Acuerdo` se puede compartir con otros usuarios (tabla
  pivote `acuerdo_user`, migrada como modelo `AcuerdoUser` con
  `ManyToManyField(through=...)` para conservar los nombres de columna y los
  timestamps de Laravel) y solo el dueño lo puede editar/eliminar; un
  `Recordatorio` es siempre personal. Marcar cualquiera de los dos como
  "hecho" lo **elimina** de inmediato (no lo oculta) — así se comportaba
  `AcuerdoController@update` y `RecordatorioController@update` con
  `done=true`, y así se replicó.
- **Auto-limpieza de vencidos**: igual que `AcuerdoController@index` y
  `RecordatorioController@index`, cada visita al home borra primero los
  acuerdos/recordatorios *propios* (no los compartidos) cuya fecha ya pasó,
  antes de listar los vigentes. Verificado creando un recordatorio con fecha
  pasada y confirmando que desaparece en la siguiente visita al home.
- **Calendario interactivo sin build de JS**: el `Calendar.tsx` original
  (200 líneas de React con estado de mes/día seleccionado y un tooltip
  flotante) se reescribió como un componente Alpine.js (`calendarWidget()`
  en `templates/agenda/_calendar.html`): los eventos del mes se inyectan una
  sola vez desde Django vía `{{ calendar_events|json_script:"..." }}`, y la
  navegación de mes / selección de día / lista de eventos del día
  seleccionado son cálculos reactivos en el cliente, sin round-trips al
  servidor. Simplificado el tooltip flotante a un panel fijo debajo del
  calendario (mismo contenido, sin la lógica de posicionamiento absoluto).
- **Modal de alta unificado**: igual que el modal único de Home.tsx que
  cambiaba entre "Nuevo Acuerdo" y "Nuevo Recordatorio" según
  `modalType`, el modal en `home.html` usa una sola variable Alpine
  (`x-data="{ open: false, type: 'acuerdo' }"`) para decidir el título, qué
  campos mostrar (descripción y "compartir con" solo para acuerdos, con
  `:required` dinámico en la descripción) y a qué endpoint enviar el POST
  (`:action="type === 'acuerdo' ? ... : ..."`).
- **Verificación con CDNs bloqueados en este sandbox**: el proxy saliente de
  este entorno de desarrollo rechaza `unpkg.com` y `cdn.tailwindcss.com` (no
  están en su lista blanca), así que un navegador real aquí no puede cargar
  Alpine/HTMX/Tailwind por su URL de producción. Para poder probar de verdad
  el modal y el calendario (que si dependen de Alpine, a diferencia de las
  fases anteriores) se descargó Alpine.js desde el registro de npm
  (`registry.npmjs.org`, que sí está permitido) y se sirvió localmente solo
  durante la prueba con Playwright, interceptando la petición a `unpkg.com`.
  Esto **no** es un problema del código ni requiere ningún cambio: en un
  navegador real, con acceso normal a internet, los CDNs cargan sin
  intervención. Se deja documentado por si se repite el mismo síntoma
  (pantalla en blanco de Tailwind, botones que no reaccionan) al probar
  dentro de un entorno con red restringida.
- **Permisos de Usuarios/Settings**: replican exactamente
  `canViewUsers`/`canCreateUser`/`canDeleteUser` de `SettingsModal.tsx` —
  solo admin/superadmin ven el directorio; solo superadmin crea o elimina
  cuentas; cualquiera de los dos puede editar cualquier usuario (así estaba
  en el original: el botón "Editar" no tenía restricción de rol, solo
  "Nuevo Usuario" y "Eliminar"); nadie puede eliminarse a sí mismo. Un
  usuario ya autenticado que intenta entrar a `/accounts/usuarios/` sin
  permiso ve un mensaje de acceso denegado y vuelve al inicio, en vez del
  redirect a `/login/` que da el `user_passes_test` por defecto de Django
  (confuso para alguien que ya inició sesión).
- **Cambiar la propia contraseña no cierra la sesión**: Django invalida la
  sesión activa cuando cambia el hash de contraseña del usuario logueado;
  se llama a `update_session_auth_hash()` después de `set_password()` para
  evitarlo (el original no tenía este problema porque no usaba sesiones).
  Verificado con curl: la sesión sigue respondiendo 200 justo después de
  cambiar la contraseña, y la contraseña nueva funciona en un login
  posterior.
- **Permisos por rol, reforzados en el servidor**: el frontend original
  calculaba `isReadOnly` en cada componente React (`allowedRoles.includes(role)`)
  y con eso ocultaba botones — pero nada impedía llamar al endpoint
  directamente con un rol sin permiso, porque `DonanteController`,
  `DonativoController`, `DistribucionController`, `EntregaController` e
  `IapController` nunca validaban el rol del lado del servidor. Se replicó
  el mismo criterio (`accounts/permissions.py`: `can_edit_donativos` para
  Donantes/Donativos/Distribución/Entregas, `can_edit_iaps` para IAPs) pero
  aplicado en **ambos** lados: los templates ocultan los mismos controles
  que ocultaba React (mismo resultado visual), y las vistas que escriben
  vuelven a comprobar el rol antes de guardar nada, así que ya no basta con
  omitir el botón en el cliente para saltarse la restricción.
- **No-op silencioso vs. mensaje de error**: para las acciones dentro de un
  modal HTMX (crear/editar/eliminar Donante o IAP) un intento sin permiso
  simplemente devuelve la tabla sin cambios, igual que ya hacían esas
  vistas para otros casos límite. Para las páginas completas (alta de
  donativo, actualizar precios, devolución, asignar, confirmar entrega,
  importar IAPs) sí se agrega un mensaje de error visible antes de
  redirigir, porque ahí el usuario espera una respuesta a una navegación
  explícita, no a un botón que ya estaba oculto.

## Verificado

- `python manage.py check` sin errores; migraciones generadas y aplicadas
  limpiamente.
- Fase 1 (Donantes/Inventario) probada con `curl` contra un servidor de
  desarrollo real: login, CRUD completo de donantes (incluyendo el mutador
  de mayúsculas), carga de inventario.
- Fase 2 (Donativos) probada end-to-end: alta de un donativo con dos
  productos (verificado que crea el `CatalogoProducto`, calcula los montos
  deducibles y el total del donativo correctamente), actualización de
  precios de venta, devolución parcial de un lote (resta de
  `cantidad_actual`). Las filas dinámicas del formulario y el
  autocompletado se probaron en un navegador real con Playwright.
- Fase 3 (Distribución/Entregas) probada end-to-end contra un servidor real:
  con una IAP `Activa`/certificada/con donataria/con padrón y un lote de
  ARROZ, el algoritmo la sugirió con las 4 razones esperadas; se creó una
  asignación pendiente, se confirmó la entrega y se verificó en base de
  datos que `cantidad_actual` bajó exactamente lo asignado y
  `iap.veces_donado` subió en 1. También se probaron los rechazos: asignar
  más del stock disponible, y confirmar dos veces la misma entrega.
- Fase 4 (IAPs) probada end-to-end: alta con clasificación múltiple
  (`A1|A2`) y población (`Fijos: 15|Temporales: 3` → 18 personas)
  verificadas en base de datos con el formato exacto del original; edición
  que recalcula esos campos derivados y recarga los checkboxes/inputs
  correctos al reabrir el formulario; eliminación; e importación de un CSV
  de 2 filas verificando estatus, clasificación y los tres booleanos de
  validación de cada institución importada. También se confirmó que la
  pantalla de Distribución (Fase 3) sigue funcionando con IAPs dadas de
  alta desde este módulo nuevo.
- Fase 5 (Acuerdos/Recordatorios/Dashboard) probada end-to-end: creación de
  un acuerdo compartido con otro usuario desde un navegador real (Alpine
  servido localmente, ver nota arriba) confirmando que el modal, el
  show/hide de la descripción y "compartir con", y la navegación del
  calendario a otro mes con clic en un día funcionan correctamente; que el
  segundo usuario ve el acuerdo compartido pero sin botones de
  editar/eliminar; alta, completado (borra el registro) y eliminación de un
  recordatorio por `curl`; y que un recordatorio con fecha pasada desaparece
  solo al volver a visitar el home.
- Fase 6 (Usuarios/Perfil) probada end-to-end contra un servidor real con
  tres cuentas (superadmin, admin, editor): el editor no ve "Usuarios" en el
  menú y un acceso directo lo redirige al inicio con mensaje; el admin sí ve
  el directorio y puede editar usuarios, pero un intento de crear o eliminar
  se bloquea (verificado en base de datos que el usuario "bloqueado" nunca
  se creó y que un usuario existente no se borró); el superadmin sí puede
  crear y eliminar; y el propio editor actualizó su nombre/email y cambió su
  contraseña sin perder la sesión, confirmado con un login posterior usando
  la contraseña nueva.
- Fase 7 (Permisos por rol) probada end-to-end con cuatro cuentas
  (superadmin, `donativos`, `lector`, `asistencial`) sobre datos reales
  (un donante, un donativo con un lote, una IAP): confirmado que `lector`
  no ve ningún control de edición en Donantes/Donativos/IAPs/Distribución y
  que sus intentos directos por POST se bloquean con mensaje sin modificar
  la base de datos (incluida la pantalla de detalle de un donativo, donde
  el input de precio queda `disabled` y la columna "Devolver" desaparece
  por completo); que `asistencial` puede dar de alta una IAP pero un
  intento de crear un donante no se guarda; y, en el sentido contrario,
  que el rol `donativos` puede crear un donante pero un intento de crear
  una IAP no se guarda — confirmando la matriz de permisos completa en
  ambas direcciones, no solo un caso.
- Panel `/admin/` accesible.

## Próximas fases (pendientes)

1. Suite de tests (`pytest-django` o `django.test`) — Laravel tenía Pest;
   no se migró todavía.
2. Decidir estrategia de migración de datos desde la base Postgres actual
   (Laravel) hacia el esquema Django, si se requiere conservar el histórico.

El código original de referencia sigue disponible en `Japem-Backend/` y
`Japem-Frontend/` en la raíz del repositorio mientras dura la migración.

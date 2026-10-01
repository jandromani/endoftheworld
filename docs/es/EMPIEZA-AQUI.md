# 🇪🇸 THE ARK — empezar desde cero

## ¿Qué es esto?

THE ARK convierte un SSD en un **ordenador autónomo** con conocimiento, mapas, IA y herramientas que funcionan sin Internet.

La idea más sencilla:

> Mientras hay Internet, llenamos el Arca. Después la usamos sin Internet.

## No sé informática. ¿Cuál hago?

Empieza por **NANO (64 GB)**.

Necesitas:

- un PC x86-64 con Debian/Ubuntu Linux para construirlo;
- Internet durante la descarga;
- espacio libre en ese PC;
- un SSD/USB de al menos 64 GB que puedas borrar por completo.

## El camino fácil

Abre un terminal:

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld
bash scripts/ark-wizard.sh
```

El asistente te pregunta qué Arca quieres y te explica los pasos.

## ¿Qué hace?

1. **PLAN** — mira qué hay que descargar y cuánto ocupa.
2. **ACQUIRE** — descarga Wikipedia, modelos, mapas, apps, código, contenedores…
3. **VERIFY** — calcula hashes SHA-256.
4. **FREEZE** — deja registrada la versión exacta.
5. **PREPARE** — convierte datos, por ejemplo OSM → PMTiles.
6. **IMAGE** — empaqueta Linux + THE ARK + todo el almacén.
7. **FLASH** — copia la imagen al SSD.
8. **BOOT** — arrancas el PC desde ese SSD.

## ¿Dónde está “la lista de la compra”?

En:

`profiles/nano.yml`

Ese fichero dice qué tiene que llevar NANO.

`manifests/capabilities.yml` no es el producto final: es nuestro **radar** de proyectos interesantes.

## ¿Cómo sé qué se descargó realmente?

Después de adquirir aparece:

`vault/nano/lock/nano.lock.json`

Ese fichero es el **ticket de compra**:

- URL exacta;
- versión/ref;
- tamaño;
- ruta local;
- SHA-256;
- verificación upstream si existía.

Y:

`vault/nano/lock/nano.cdx.json`

es el inventario/BOM.

## ¿Dónde están los archivos grandes?

En:

`vault/nano/`

Git guarda las instrucciones. El vault guarda la carga.

## ¿Cómo lo pruebo antes de borrar un SSD?

```bash
make nano-acquire
make nano-prepare
make nano-verify
make nano-run
```

Abre:

`http://localhost:8080`

## ¿Cómo creo el SSD?

```bash
make nano-image
lsblk -o NAME,SIZE,MODEL,TRAN,MOUNTPOINTS
make nano-flash DEVICE=/dev/sdX
```

⚠️ El último comando borra el disco indicado. No adivines qué dispositivo es.

## ¿Qué pasa al arrancar?

THE ARK levanta una web local con:

- biblioteca;
- IA;
- mapas;
- transcripción;
- apps;
- inventario;
- salud del nodo.

FAMILY añade Syncthing y Forgejo.

NOMAD/CIVILIZATION añaden IDE, Qdrant, IA coder y **Project NOMAD** como centro de mando.

## ¿Qué es Project NOMAD aquí?

Project NOMAD es el **centro de mando de aplicaciones** que vive dentro de los perfiles grandes.

ENDWORLD/THE ARK decide qué se descarga, verifica, congela y mete en la imagen.

Project NOMAD ofrece la experiencia humana para gestionar herramientas y recursos locales.

No dejamos que su actualizador cambie el Arca congelada por su cuenta: las actualizaciones vuelven a pasar por nuestro pipeline.

## ¿Y si se cae Internet mañana?

Si ya construiste y probaste tu Arca, los servicios congelados no necesitan descargar sus piezas principales para arrancar.

Pero una Arca de verdad también necesita:

- hardware probado;
- electricidad;
- copias redundantes;
- procedimientos;
- actualizaciones offline;
- mantenimiento del almacenamiento.

Por eso el proyecto todavía tiene fronteras abiertas.

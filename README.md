# Heli FOB

Heli FOB is a browser-playable, pixel-art helicopter campaign built with Pyxel Web and React Router. Fly eight missions, land gently, cross rough seas, and complete a sea rescue. All missions are selectable from the start for testing. Mission progress and best landing scores are saved in the browser.

## Run locally

Install dependencies once:

```sh
npm install
```

Start the local site:

```sh
npm run dev
```

Open <http://localhost:5173/>. The Python game is loaded as a separate file by Pyxel Web, so serve the page over HTTP instead of opening `public/index.html` directly as a `file://` URL.

## Controls

- **Space**: continue, launch, or take off
- **Up / Down**: increase / decrease collective; use the same keys to move through mission select
- **Left / Right**: cyclic input
- **R**: restart the current mission

## Project layout

- `main.py`: game source
- `public/main.py`: browser-loaded copy of the game source
- `app/routes/home.tsx`: hosted game page
- `public/index.html`: standalone static launch page (requires a local or remote web server)

The two Python files should stay in sync.

## Build and deploy

```sh
npm run build
npm run deploy
```

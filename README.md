# Iron Flight

The first milestone is a detailed, accurately proportioned Iron Man armor model in Blender.

- `blender/references/` holds visual references and proportion studies.
- `blender/source/` holds editable Blender source files.
- `blender/exports/` holds exported models.
- `docs/` holds project documentation.

## Play the prototype

With Node.js installed, run `npm ci` once, then run `npm start` from the repository root.
Open http://localhost:3000 and click **Click to play** to capture the mouse.

| Input | Ground | Flight |
| --- | --- | --- |
| WASD or arrow keys | Move | Move horizontally |
| Shift | Run | Boost |
| Space | Jump | Ascend |
| Ctrl | | Descend |
| F | Take off | Land |
| Mouse / left click | Aim / fire | Aim / fire |
| Esc | Release mouse | Release mouse |

The game loads the V004 export from `blender/exports/iron-man-mark3-v004.glb`.

# Rig AGI-chan in Live2D Cubism (on your Mac)

**File:** `AGI-chan.psd` — 880×1184, 2 layers: `character` (base) + `mask` (the smiley hairclip, on top).

## Steps
1. Install **Live2D Cubism** (free) → https://www.live2d.com/en/cubism/download/ . Open it.
2. **Import:** drag `AGI-chan.psd` into Cubism (or File → Open). Import as a model; keep the PSD layers as materials.
3. **Auto mesh:** select all ArtMeshes → **Modeling → Mesh → Automatic Mesh Generation** (Cubism may offer this on import).
4. **AI rig (deformers):** **Modeling → Deformer → Auto Generation of Deformer** → confirm the dialog. (AI estimates the body/face parts and builds the deformer tree.)
5. **AI facial motion:** run **Auto generation of facial motion** → it creates eye-blink, mouth-open, and head-angle parameters.
6. **Check params** (Parameters panel) and drag-test them. You should see the standard IDs:
   `ParamAngleX/Y/Z`, `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, `ParamMouthForm`, `ParamBrowLY/RY`.
   ⚠️ **Do not rename parameters** — our app drives these exact IDs.
7. **Export:** **File → Export for Runtime → moc3** (embed textures). Save the whole folder (`.model3.json` + `.moc3` + textures + physics).
8. **Send the exported folder back to me** — I wire it into the app (lip-sync → `ParamMouthOpenY`; emotions → `ParamMouthForm`, `ParamEyeL/ROpen`, `ParamBrowLY/RY`, `ParamCheek`). These are Cubism's default IDs, so it should line up automatically.

## Honest note
This PSD has the face merged into the single `character` layer, so the auto-rig will **deform** the face for blink/mouth (basic but real). For crisper blink/lip-sync (separate eye-whites + mouth interior), eyes/mouth want to be their own layers — tell me and I'll attempt that separation and send an upgraded PSD.

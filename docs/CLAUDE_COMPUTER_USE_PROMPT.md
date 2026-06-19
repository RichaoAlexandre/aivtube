# Prompt for a computer-use Claude on your Mac

You are operating my Mac, which has **Live2D Cubism** installed. Goal: turn
`~/Downloads/AGI-chan.psd` into a rigged Live2D model and export it.

Do this:
1. Open Live2D Cubism.
2. Import `~/Downloads/AGI-chan.psd` as a model, keeping the PSD layers as separate materials.
3. Run **Automatic Mesh Generation** on all ArtMeshes.
4. Run **Modeling → Deformer → Auto Generation of Deformer** and accept the default dialog.
5. Run the **Auto generation of facial motion** feature.
6. Open the Parameters panel and confirm these parameters exist (do NOT rename them):
   ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen,
   ParamMouthOpenY, ParamMouthForm. Drag each slider once to confirm it moves the model.
7. **File → Export for Runtime → moc3**, embed textures, and export the bundle to
   `~/Downloads/AGI-chan-model/`.
8. Report the exact export folder path and list the files in it.

If any dialog is ambiguous, describe what you see, choose sensible defaults, and continue.
Keep all parameter IDs at Cubism's standard defaults.

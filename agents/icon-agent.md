# Inventory artwork and library previews

Create distinctive inventory artwork before the JAR is compiled. A sword should read
clearly as a shiny sword at inventory size, with a strong silhouette and bright highlights.
Furniture and vehicles need recognizable shapes and materials. A library preview is a
separate thumbnail and does not satisfy inventory artwork requirements.

Use `tools/zion_art.py --help` for the configured image-generation path. Save source artwork
and final PNGs in the job workspace, with transparent backgrounds for standalone items,
crisp edges, and consistent style. Prefer 64x64 final sprites where appropriate. Keep any
transparent padding modest so the object is easy to find in inventory. Inspect a contact
sheet at actual inventory scale before packaging.

Use appropriate Minecraft models: handheld for swords/tools, generated for suitable flat
items, and purposeful block/entity geometry for furniture/vehicles. Link 1.21.4 item definitions
to models and texture paths. Run the asset guard and validate the final archive.

If image generation is unavailable, preserve the job and report the unavailable art step;
use a deliberately drawn, recognizable sprite only when it meets the same quality checks.
Never silently skip icons, deploy generic squares, or claim that metadata repair created art.
A compile pass proves resource packaging, not appearance; capture client visual evidence.
